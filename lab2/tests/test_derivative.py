import pytest

from boolean_core import BooleanFunction
from derivative import BooleanDerivative, DummyVariableFinder


def test_partial_and_mixed_derivatives_for_reference_function():
    deriv = BooleanDerivative(BooleanFunction('(a & !b) | c'))
    assert deriv.partial_derivative('a') == [((0, 0), 1), ((0, 1), 0), ((1, 0), 0), ((1, 1), 0)]
    assert deriv.partial_derivative('b') == [((0, 0), 0), ((0, 1), 0), ((1, 0), 1), ((1, 1), 0)]
    assert deriv.partial_derivative('c') == [((0, 0), 1), ((0, 1), 1), ((1, 0), 0), ((1, 1), 1)]
    assert deriv.mixed_derivative(['a', 'b']) == [((0,), 1), ((1,), 0)]
    assert deriv.mixed_derivative(['a', 'b', 'c']) == [((), 1)]


def test_derivative_reports_all_orders_and_formatting():
    deriv = BooleanDerivative(BooleanFunction('(a & !b) | c'))
    reports = deriv.all_reports()
    assert len(reports) == 7  # 3 choose 1 + 3 choose 2 + 3 choose 3

    report = deriv.derivative_report(['a', 'b', 'c'])
    assert report['vector'] == '1'
    assert report['numeric'] == [0]
    assert report['sdnf'] == '1'
    text = deriv.format_report(report)
    assert '∂^3f/∂a∂b∂c' in text
    assert 'Константа: 1' in text
    assert 'СДНФ производной: 1' in text

    report2 = deriv.derivative_report(['a'])
    text2 = deriv.format_report(report2)
    assert 'Оставшиеся переменные: b, c' in text2
    assert 'Вектор значений: 1000' in text2


@pytest.mark.parametrize(
    ('var_list', 'message'),
    [
        ([], 'Список переменных для производной пуст'),
        (['a', 'a'], 'не должны повторяться'),
        (['z'], 'не входит в функцию'),
        (['a', 'b', 'c', 'd', 'e'], 'не выше 4-го порядка'),
    ],
)
def test_mixed_derivative_error_cases(var_list, message):
    expr = '(a & !b) | c' if var_list != ['a', 'b', 'c', 'd', 'e'] else '(a & b) | (c & d) | e'
    deriv = BooleanDerivative(BooleanFunction(expr))
    with pytest.raises(ValueError, match=message):
        deriv.mixed_derivative(var_list)


def test_rows_to_sdnf_edge_cases_and_dummy_variables():
    assert BooleanDerivative._rows_to_sdnf([((0,), 0), ((1,), 0)], ['x']) == '0'
    assert BooleanDerivative._rows_to_sdnf([((), 1)], []) == '1'

    finder_dummy = DummyVariableFinder(BooleanFunction('a'))
    assert finder_dummy.find_dummy_variables() == []

    finder = DummyVariableFinder(BooleanFunction('a | (b & !b)'))
    assert finder.find_dummy_variables() == ['b']
