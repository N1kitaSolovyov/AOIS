from boolean_core import BooleanFunction
from normal_forms import NormalFormsBuilder
from post_classes import PostClasses


def test_normal_forms_for_nontrivial_function():
    func = BooleanFunction('(a & !b) | c')
    nf = NormalFormsBuilder(func)
    assert nf.get_sdnf() == '(!a&!b&c)|(!a&b&c)|(a&!b&!c)|(a&!b&c)|(a&b&c)'
    assert nf.get_sknf() == '(a|b|c)&(a|!b|c)&(!a|!b|c)'
    assert nf.get_numeric_sdnf() == [1, 3, 4, 5, 7]
    assert nf.get_numeric_sknf() == [0, 2, 6]
    assert nf.get_index_binary() == '01011101'
    assert nf.get_index_form() == 93


def test_normal_forms_for_constant_zero_and_one():
    nf0 = NormalFormsBuilder(BooleanFunction('0'))
    assert nf0.get_sdnf() == '0'
    assert nf0.get_sknf() == '0'
    assert nf0.get_numeric_sdnf() == []
    assert nf0.get_numeric_sknf() == [0]
    assert nf0.get_index_binary() == '0'
    assert nf0.get_index_form() == 0

    nf1 = NormalFormsBuilder(BooleanFunction('1'))
    assert nf1.get_sdnf() == '1'
    assert nf1.get_sknf() == '1'
    assert nf1.get_numeric_sdnf() == [0]
    assert nf1.get_numeric_sknf() == []
    assert nf1.get_index_binary() == '1'
    assert nf1.get_index_form() == 1


def test_post_classes_for_various_functions():
    linear = PostClasses(BooleanFunction('!(a ~ b)'))  # XOR
    assert linear.is_T0() is True
    assert linear.is_T1() is False
    assert linear.is_S() is False
    assert linear.is_M() is False
    assert linear.is_L() is True
    assert linear.get_zhegalkin_polynomial() == 'b ⊕ a'

    identity = PostClasses(BooleanFunction('a'))
    assert identity.is_S() is True
    assert identity.get_zhegalkin_polynomial() == 'a'

    monotone = PostClasses(BooleanFunction('a | b'))
    assert monotone.is_M() is True
    assert monotone.is_L() is False

    const_one = PostClasses(BooleanFunction('1'))
    assert const_one.is_T0() is False
    assert const_one.is_T1() is True
    assert const_one.is_S() is False
    assert const_one.is_M() is True
    assert const_one.is_L() is True
    assert const_one.get_zhegalkin_polynomial() == '1'

    const_zero = PostClasses(BooleanFunction('0'))
    assert const_zero.get_zhegalkin_polynomial() == '0'
