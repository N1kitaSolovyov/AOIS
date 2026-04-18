import pytest

from boolean_core import BooleanFunction
from minimization import QuineMcCluskey, KarnaughMap


def test_quine_mccluskey_helpers_and_stage_generation():
    qm = QuineMcCluskey(BooleanFunction('(a & !b) | c'))
    assert qm._bits_to_int('10-') == 4
    assert qm._count_ones('10-1') == 2
    assert qm._literal_count('10-1') == 3
    assert qm._can_combine('001', '011') is True
    assert qm._can_combine('0-1', '011') is False
    assert qm._can_combine('001', '111') is False
    assert qm._combine('001', '011') == '0-1'
    assert qm._term_to_expr('10-') == 'a&!b'
    assert qm._term_to_expr('---') == '1'
    assert qm._covers('0-1') == {1, 3}

    implicants, stages = qm._get_prime_implicants_with_stages()
    assert implicants == ['--1', '10-']
    assert any('Склейки:' in stage for stage in stages)
    assert 'Этап 1:' in stages[0]


def test_quine_mccluskey_constant_cases_and_exact_cover_branches(capsys):
    qm0 = QuineMcCluskey(BooleanFunction('0'))
    assert qm0.minimize_calculated() == '0'
    assert qm0.minimize_tabular() == '0'

    qm1 = QuineMcCluskey(BooleanFunction('1'))
    assert qm1.minimize_calculated() == '1'
    assert qm1.minimize_tabular() == '1'

    out = capsys.readouterr().out
    assert 'тождественно равна 0' in out
    assert 'тождественно равна 1' in out

    qm = QuineMcCluskey(BooleanFunction('a | b'))
    chosen, logs = qm._select_exact_cover({'0-': {1, 2}, '-0': {2, 3}, '11': {1, 3}})
    assert len(chosen) == 2
    assert logs[0] == 'Ядро покрытия отсутствует.'


def test_quine_mccluskey_minimization_outputs(capsys):
    qm = QuineMcCluskey(BooleanFunction('(a & !b) | c'))
    result_calc = qm.minimize_calculated()
    result_tab = qm.minimize_tabular()
    out = capsys.readouterr().out
    assert result_calc == 'c | a&!b'
    assert result_tab == 'c | a&!b'
    assert 'Таблица покрытия:' in out
    assert 'Ядро покрытия:' in out
    # for this function parser variables sorted from expression tokens a,b,c and minimal form equivalent to c|!a&b? wait ensure via current algorithm
