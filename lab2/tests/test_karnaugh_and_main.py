import builtins
import pytest

from boolean_core import BooleanFunction
from minimization import KarnaughMap
import main as main_module


@pytest.mark.parametrize(
    ('expr', 'expected'),
    [
        ('a', 'a'),
        ('!a', '!a'),
        ('a | b', 'b | a'),
        ('(a & !b) | c', 'c | a&!b'),
        ('(a & !b) | (c & d)', 'a&!b | c&d'),
        ('(a & !b) | (c & d) | e', 'e | a&!b | c&d'),
    ],
)
def test_karnaugh_minimized_for_multiple_dimensions(expr, expected):
    km = KarnaughMap(BooleanFunction(expr))
    result = km.get_minimized()
    assert set(result.split(' | ')) == set(expected.split(' | '))


def test_karnaugh_constant_branches_and_display(capsys):
    km1 = KarnaughMap(BooleanFunction('a'))
    km1.display()
    out1 = capsys.readouterr().out
    assert 'Карта Карно' in out1
    assert 'a: 0 1' in out1

    km2 = KarnaughMap(BooleanFunction('a | b'))
    km2.display()
    out2 = capsys.readouterr().out
    assert 'b: 0 1' in out2

    km3 = KarnaughMap(BooleanFunction('(a & !b) | c'))
    km3.display()
    out3 = capsys.readouterr().out
    assert 'bc:' in out3

    km5 = KarnaughMap(BooleanFunction('(a & !b) | (c & d) | e'))
    km5.display()
    out5 = capsys.readouterr().out
    assert 'Для e=0:' in out5 and 'Для e=1:' in out5

    assert KarnaughMap(BooleanFunction('a | !a')).get_minimized() == '1'
    assert KarnaughMap(BooleanFunction('a & !a')).get_minimized() == '0'
    with pytest.raises(ValueError, match='Карта Карно поддерживается для 1-5 переменных'):
        KarnaughMap(BooleanFunction('1 & 1'))


def test_internal_karnaugh_helpers():
    km = KarnaughMap(BooleanFunction('a | b'))
    assert km._gray_code(2) == ['00', '01', '11', '10']
    rects = km._find_rectangles_2d([[1, 1], [0, 0]], 2, 2, ['0', '1'], ['0', '1'], ['a'], ['b'])
    assert any(term == '!a' for _, _, term in rects)
    assert km._literal_count_expr('1') == 0
    assert km._literal_count_expr('a&!b') == 2
    covers = [({(0, 0)}, 'x'), ({(0, 1)}, 'y')]
    assert km._select_exact_cover_terms({(0, 0), (0, 1)}, covers) == ['x', 'y']


def run_main_with(monkeypatch, capsys, user_input):
    monkeypatch.setattr(builtins, 'input', lambda _: user_input)
    main_module.main()
    return capsys.readouterr().out


def test_main_empty_invalid_constant_and_regular(monkeypatch, capsys):
    out_empty = run_main_with(monkeypatch, capsys, '')
    assert 'Ошибка: пустое выражение' in out_empty

    out_bad = run_main_with(monkeypatch, capsys, 'a &')
    assert 'Ошибка в формуле:' in out_bad

    out_const = run_main_with(monkeypatch, capsys, '1')
    assert 'Для константной функции производные по переменным отсутствуют.' in out_const
    assert 'Для чисто константной функции карта Карно не строится.' in out_const

    out_regular = run_main_with(monkeypatch, capsys, '(a & !b) | c')
    assert '1. Таблица истинности' in out_regular
    assert 'Полином Жегалкина:' in out_regular
    assert 'Минимальная ДНФ (карта Карно):' in out_regular


def test_main_karnaugh_error_branch(monkeypatch, capsys):
    class BrokenKMap:
        def __init__(self, func):
            raise ValueError('boom')

    monkeypatch.setattr(main_module, 'KarnaughMap', BrokenKMap)
    out = run_main_with(monkeypatch, capsys, 'a')
    assert 'Ошибка при построении карты Карно: boom' in out


def test_print_separator(capsys):
    main_module.print_separator('TITLE')
    out = capsys.readouterr().out
    assert 'TITLE' in out and '=' in out
