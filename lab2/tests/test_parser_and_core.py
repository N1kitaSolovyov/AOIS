import pytest

from parser import normalize_expression, tokenize, validate, to_rpn, evaluate_rpn
from boolean_core import BooleanFunction
from truth_table import TruthTable


def test_normalize_and_tokenize_unicode_and_constants():
    expr = '¬(a ∧ b) ∨ 1 → c ↔ 0'
    normalized = normalize_expression(expr)
    assert normalized == '!(a & b) | 1 -> c ~ 0'
    assert tokenize(expr) == ['!', '(', 'a', '&', 'b', ')', '|', '1', '->', 'c', '~', '0']


@pytest.mark.parametrize(
    ('expr', 'message'),
    [
        ('', 'Пустое выражение'),
        ('a)', 'Несбалансированные скобки'),
        ('(a', 'Несбалансированные скобки'),
    ],
)
def test_validate_common_errors(expr, message):
    tokens = tokenize(expr) if expr else []
    assert validate(tokens) == message


@pytest.mark.parametrize(
    ('tokens', 'expected'),
    [
        (['a', '(', 'b', ')'], 'Открывающая скобка не может следовать за операндом на позиции 1'),
        ([')'], 'Несбалансированные скобки'),
        (['a', '!'], "Унарный оператор '!' не может следовать за операндом на позиции 1"),
        (['&', 'a'], "Бинарный оператор '&' не имеет левого операнда на позиции 0"),
        (['a', 'b'], "Переменная 'b' не может следовать за операндом без оператора на позиции 1"),
        (['1', '0'], "Константа '0' не может следовать за операндом без оператора на позиции 1"),
        (['a', '&'], 'Выражение заканчивается оператором или пустое'),
        (['?'], "Неизвестный токен '?'"),
        (['(', ')'], 'Закрывающая скобка не может быть на месте операнда на позиции 1'),
    ],
)
def test_validate_specific_error_messages(tokens, expected):
    assert validate(tokens) == expected


@pytest.mark.parametrize(
    ('expr', 'expected'),
    [
        ('a->b->c', ['a', 'b', 'c', '->', '->']),
        ('a~b~c', ['a', 'b', '~', 'c', '~']),
        ('!(a|b)&c', ['a', 'b', '|', '!', 'c', '&']),
    ],
)
def test_to_rpn_precedence_and_associativity(expr, expected):
    assert to_rpn(tokenize(expr)) == expected


def test_to_rpn_rejects_unbalanced_parentheses_left_on_stack():
    with pytest.raises(ValueError, match='Несбалансированные скобки'):
        to_rpn(['('])


def test_to_rpn_rejects_unknown_token_direct_call():
    with pytest.raises(ValueError, match='Неизвестный токен'):
        to_rpn(['a', '?'])


@pytest.mark.parametrize(
    ('rpn', 'assignment', 'expected'),
    [
        (['1'], {}, 1),
        (['0'], {}, 0),
        (['a', '!'], {'a': 0}, 1),
        (['a', 'b', '&'], {'a': 1, 'b': 0}, 0),
        (['a', 'b', '|'], {'a': 1, 'b': 0}, 1),
        (['a', 'b', '->'], {'a': 1, 'b': 0}, 0),
        (['a', 'b', '~'], {'a': 1, 'b': 1}, 1),
    ],
)
def test_evaluate_rpn_operations(rpn, assignment, expected):
    assert evaluate_rpn(rpn, assignment) == expected


@pytest.mark.parametrize(
    ('rpn', 'message'),
    [
        (['!'], 'Недостаточно операндов'),
        (['a', '&'], 'Недостаточно операндов'),
        (['?'], 'Неизвестный токен в RPN'),
        (['1', '1'], 'Некорректная RPN'),
    ],
)
def test_evaluate_rpn_errors(rpn, message):
    with pytest.raises(ValueError, match=message):
        evaluate_rpn(rpn, {'a': 1})


def test_tokenize_invalid_symbol_and_bad_arrow():
    with pytest.raises(ValueError, match="Неверный символ '-' без '>'"):
        tokenize('a-b')
    with pytest.raises(ValueError, match="Недопустимый символ '\$'"):
        tokenize('a$')


def test_boolean_function_evaluation_and_missing_variable_error():
    func = BooleanFunction(' (a & !b) | 1 ')
    assert func.get_variables() == ['a', 'b']
    assert func.evaluate({'a': 0, 'b': 0}) == 1
    with pytest.raises(ValueError, match='Не задано значение переменной b'):
        func.evaluate({'a': 1})


def test_boolean_function_invalid_formula_wraps_error():
    with pytest.raises(ValueError, match='Ошибка в формуле'):
        BooleanFunction('a &')


def test_truth_table_rows_and_display(capsys):
    func = BooleanFunction('a')
    table = TruthTable(func)
    assert table.get_rows() == [((0,), 0), ((1,), 1)]
    table.display()
    out = capsys.readouterr().out
    assert 'a | f' in out
    assert '0 | 0' in out
    assert '1 | 1' in out
