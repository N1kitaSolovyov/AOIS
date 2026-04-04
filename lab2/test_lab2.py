import unittest
from boolean_core import BooleanFunction
from truth_table import TruthTable
from normal_forms import NormalFormsBuilder
from post_classes import PostClasses
from derivative import BooleanDerivative, DummyVariableFinder
from minimization import QuineMcCluskey, KarnaughMap
from parser import tokenize, validate, to_rpn, evaluate_rpn

class TestParser(unittest.TestCase):
    def test_tokenize_simple(self):
        self.assertEqual(tokenize("a&b"), ['a', '&', 'b'])
        self.assertEqual(tokenize("!a|b"), ['!', 'a', '|', 'b'])
        self.assertEqual(tokenize("a->b"), ['a', '->', 'b'])
        self.assertEqual(tokenize("a~b"), ['a', '~', 'b'])
        self.assertEqual(tokenize("(a&b)"), ['(', 'a', '&', 'b', ')'])

    def test_tokenize_with_spaces(self):
        self.assertEqual(tokenize(" a & b "), ['a', '&', 'b'])
        self.assertEqual(tokenize("! a | b"), ['!', 'a', '|', 'b'])

    def test_tokenize_error(self):
        with self.assertRaises(ValueError):
            tokenize("a@b")
        with self.assertRaises(ValueError):
            tokenize("a-")  # некорректная импликация

    def test_validate_balanced(self):
        self.assertIsNone(validate(['(', 'a', ')']))
        self.assertIsNotNone(validate(['(', 'a']))
        self.assertIsNotNone(validate(['a', ')']))

    def test_validate_operands(self):
        self.assertIsNotNone(validate(['a', 'b']))          # два операнда подряд
        self.assertIsNotNone(validate(['&', 'a']))          # оператор без левого
        self.assertIsNone(validate(['!', 'a']))             # унарный норм
        self.assertIsNotNone(validate([]))                  # пустое
        self.assertIsNotNone(validate(['a', '&']))          # кончается оператором

    def test_to_rpn(self):
        self.assertEqual(to_rpn(['a', '&', 'b']), ['a', 'b', '&'])
        self.assertEqual(to_rpn(['!', 'a', '|', 'b']), ['a', '!', 'b', '|'])
        self.assertEqual(to_rpn(['a', '->', 'b']), ['a', 'b', '->'])
        self.assertEqual(to_rpn(['a', '~', 'b']), ['a', 'b', '~'])
        self.assertEqual(to_rpn(['(', 'a', '&', 'b', ')', '|', 'c']), ['a', 'b', '&', 'c', '|'])

    def test_evaluate_rpn(self):
        # AND
        rpn = ['a', 'b', '&']
        self.assertEqual(evaluate_rpn(rpn, {'a':1,'b':1}), 1)
        self.assertEqual(evaluate_rpn(rpn, {'a':1,'b':0}), 0)
        # NOT
        rpn = ['a', '!']
        self.assertEqual(evaluate_rpn(rpn, {'a':1}), 0)
        self.assertEqual(evaluate_rpn(rpn, {'a':0}), 1)
        # IMPLICATION
        rpn = ['a', 'b', '->']
        self.assertEqual(evaluate_rpn(rpn, {'a':1,'b':0}), 0)
        self.assertEqual(evaluate_rpn(rpn, {'a':1,'b':1}), 1)
        self.assertEqual(evaluate_rpn(rpn, {'a':0,'b':0}), 1)
        # EQUIVALENCE
        rpn = ['a', 'b', '~']
        self.assertEqual(evaluate_rpn(rpn, {'a':1,'b':0}), 0)
        self.assertEqual(evaluate_rpn(rpn, {'a':1,'b':1}), 1)

class TestBooleanFunction(unittest.TestCase):
    def test_create_valid(self):
        func = BooleanFunction("a&b")
        self.assertEqual(func.variables, ['a','b'])
        func = BooleanFunction("!a|b->c")
        self.assertEqual(func.variables, ['a','b','c'])
        func = BooleanFunction("a~b")
        self.assertEqual(func.variables, ['a','b'])

    def test_create_too_many_vars(self):
        with self.assertRaises(ValueError):
            BooleanFunction("a&b&c&d&e&f")  # f недопустима

    def test_evaluate(self):
        func = BooleanFunction("a&b")
        self.assertEqual(func.evaluate({'a':1,'b':1}), 1)
        self.assertEqual(func.evaluate({'a':1,'b':0}), 0)
        with self.assertRaises(ValueError):
            func.evaluate({'a':1})   # нет b

    def test_get_variables(self):
        func = BooleanFunction("a|b")
        self.assertEqual(func.get_variables(), ['a','b'])

class TestTruthTable(unittest.TestCase):
    def test_truth_table_2vars(self):
        func = BooleanFunction("a&b")
        tt = TruthTable(func)
        rows = tt.get_rows()
        # порядок наборов: (0,0),(0,1),(1,0),(1,1)
        expected = [
            ((0,0),0), ((0,1),0), ((1,0),0), ((1,1),1)
        ]
        self.assertEqual(rows, expected)

    def test_truth_table_3vars(self):
        func = BooleanFunction("a&b&c")
        tt = TruthTable(func)
        rows = tt.get_rows()
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[-1][1], 1)  # (1,1,1) -> 1

class TestNormalForms(unittest.TestCase):
    def test_sdnf_sknf(self):
        func = BooleanFunction("a&b")
        nf = NormalFormsBuilder(func)
        sdnf = nf.get_sdnf()
        sknf = nf.get_sknf()
        # СДНФ: только (a&b)
        self.assertEqual(sdnf, "(a&b)")
        # СКНФ: (a|b)&(a|!b)&(!a|b) – порядок может быть другим, проверим через множество
        # разбиваем по '&' и убираем скобки
        terms = [t.strip('()') for t in sknf.split('&')]
        self.assertEqual(set(terms), {"a|b", "a|!b", "!a|b"})

    def test_numeric_forms(self):
        func = BooleanFunction("a|b")
        nf = NormalFormsBuilder(func)
        # СДНФ: наборы (0,1),(1,0),(1,1) -> номера 1,2,3
        self.assertEqual(set(nf.get_numeric_sdnf()), {1,2,3})
        # СКНФ: набор (0,0) -> номер 0
        self.assertEqual(nf.get_numeric_sknf(), [0])

    def test_index_form(self):
        func = BooleanFunction("a&b")
        nf = NormalFormsBuilder(func)
        # таблица 2 переменных: 0,0,0,1 -> двоичное 0001 = 1
        self.assertEqual(nf.get_index_form(), 1)
        func2 = BooleanFunction("a|b")
        nf2 = NormalFormsBuilder(func2)
        # 0,1,1,1 -> 0111 = 7
        self.assertEqual(nf2.get_index_form(), 7)

class TestPostClasses(unittest.TestCase):
    def test_T0_T1(self):
        # константа 0: T0 да, T1 нет
        func0 = BooleanFunction("a&!a")
        post0 = PostClasses(func0)
        self.assertTrue(post0.is_T0())
        self.assertFalse(post0.is_T1())
        # константа 1: T0 нет, T1 да
        func1 = BooleanFunction("a|!a")
        post1 = PostClasses(func1)
        self.assertFalse(post1.is_T0())
        self.assertTrue(post1.is_T1())
        # a&b: T0 да, T1 да
        func_and = BooleanFunction("a&b")
        post_and = PostClasses(func_and)
        self.assertTrue(post_and.is_T0())
        self.assertTrue(post_and.is_T1())

    def test_S(self):
        # a – самодвойственна
        func_a = BooleanFunction("a")
        post_a = PostClasses(func_a)
        self.assertTrue(post_a.is_S())
        # a&b – не самодвойственна
        func_and = BooleanFunction("a&b")
        post_and = PostClasses(func_and)
        self.assertFalse(post_and.is_S())

    def test_M(self):
        # a&b – монотонна
        func_and = BooleanFunction("a&b")
        post_and = PostClasses(func_and)
        self.assertTrue(post_and.is_M())
        # !a – не монотонна
        func_not = BooleanFunction("!a")
        post_not = PostClasses(func_not)
        self.assertFalse(post_not.is_M())

    def test_L(self):
        # a~b – линейна (эквивалентность)
        func_eq = BooleanFunction("a~b")
        post_eq = PostClasses(func_eq)
        self.assertTrue(post_eq.is_L())
        # a&b – не линейна
        func_and = BooleanFunction("a&b")
        post_and = PostClasses(func_and)
        self.assertFalse(post_and.is_L())

    def test_zhegalkin(self):
        # a&b -> полином "a&b"
        func_and = BooleanFunction("a&b")
        post_and = PostClasses(func_and)
        self.assertEqual(post_and.get_zhegalkin_polynomial(), "a&b")
        # a~b -> 1 ⊕ a ⊕ b
        func_eq = BooleanFunction("a~b")
        post_eq = PostClasses(func_eq)
        poly = post_eq.get_zhegalkin_polynomial()
        terms = set(poly.split(" ⊕ "))
        self.assertEqual(terms, {"1", "a", "b"})

class TestBooleanDerivative(unittest.TestCase):
    def test_partial_derivative(self):
        func = BooleanFunction("a&b")
        deriv = BooleanDerivative(func)
        # ∂f/∂a = b
        part_a = deriv.partial_derivative('a')
        # формат: список ((остаток,), значение)
        expected = [((0,),0), ((1,),1)]
        self.assertEqual(part_a, expected)
        # ∂f/∂b = a
        part_b = deriv.partial_derivative('b')
        self.assertEqual(part_b, expected)

    def test_mixed_derivative(self):
        func = BooleanFunction("a&b")
        deriv = BooleanDerivative(func)
        mixed = deriv.mixed_derivative(['a','b'])
        # ∂²f/∂a∂b = 1
        self.assertEqual(mixed, [((),1)])

class TestDummyVariableFinder(unittest.TestCase):
    def test_no_dummy(self):
        func = BooleanFunction("a&b")
        finder = DummyVariableFinder(func)
        self.assertEqual(finder.find_dummy_variables(), [])

    def test_dummy(self):
        # a&b | a&!b = a
        func = BooleanFunction("a&b|a&!b")
        finder = DummyVariableFinder(func)
        self.assertEqual(finder.find_dummy_variables(), ['b'])
        # константа 1 – все переменные фиктивны
        func_one = BooleanFunction("a|!a")
        finder_one = DummyVariableFinder(func_one)
        self.assertEqual(set(finder_one.find_dummy_variables()), {'a'})

class TestQuineMcCluskey(unittest.TestCase):
    def test_minimize_calculated(self):
        # a&b|a&!b = a
        func = BooleanFunction("a&b|a&!b")
        qm = QuineMcCluskey(func)
        min_dnf = qm.minimize_calculated()
        self.assertEqual(min_dnf, "a")

        # Пример из лабораторной: !(!a->!b)|c = (!a&b)|c
        func2 = BooleanFunction("!(!a->!b)|c")
        qm2 = QuineMcCluskey(func2)
        min2 = qm2.minimize_calculated()
        # результат может быть "c | !a&b" или "!a&b | c"
        self.assertIn("c", min2)
        self.assertIn("!a&b", min2)

    def test_minimize_tabular(self):
        func = BooleanFunction("a&b|a&!b")
        qm = QuineMcCluskey(func)
        min_dnf = qm.minimize_tabular()
        self.assertEqual(min_dnf, "a")

class TestKarnaughMap(unittest.TestCase):

    def test_4vars(self):
        # a&b&c&d | a&b&c&!d | a&b&!c&d | a&b&!c&!d = a&b
        func = BooleanFunction("a&b&c&d | a&b&c&!d | a&b&!c&d | a&b&!c&!d")
        km = KarnaughMap(func)
        min_dnf = km.get_minimized()
        self.assertEqual(min_dnf, "a&b")

    def test_1var(self):
        # f = a
        func = BooleanFunction("a")
        km = KarnaughMap(func)
        self.assertEqual(km.get_minimized(), "a")
        # f = !a
        func = BooleanFunction("!a")
        km = KarnaughMap(func)
        self.assertEqual(km.get_minimized(), "!a")
        # f = 1
        func = BooleanFunction("a|!a")
        km = KarnaughMap(func)
        self.assertEqual(km.get_minimized(), "1")
        # f = 0
        func = BooleanFunction("a&!a")
        km = KarnaughMap(func)
        self.assertEqual(km.get_minimized(), "0")



    def test_3vars(self):
        # уже был пример (a&b)|(!a&c)
        func = BooleanFunction("(a&b)|(!a&c)")
        km = KarnaughMap(func)
        min_dnf = km.get_minimized()
        self.assertIn("a&b", min_dnf)
        self.assertIn("!a&c", min_dnf)
        # склейка по краю: (!a&!c) | (a&c)
        func = BooleanFunction("(!a&!b&!c)|(!a&b&!c)|(a&!b&c)|(a&b&c)")
        km = KarnaughMap(func)
        min_dnf = km.get_minimized()
        # возможные варианты: "!a&!c | a&c" или "a&c | !a&!c"
        self.assertTrue(("!a&!c" in min_dnf and "a&c" in min_dnf))

    def test_4vars(self):
        # a&b
        func = BooleanFunction("a&b&c&d | a&b&c&!d | a&b&!c&d | a&b&!c&!d")
        km = KarnaughMap(func)
        self.assertEqual(km.get_minimized(), "a&b")
        # функция большинства (3 из 4) – не требует упрощения
        expr = "(a&b&c)|(a&b&d)|(a&c&d)|(b&c&d)"
        func = BooleanFunction(expr)
        km = KarnaughMap(func)
        min_dnf = km.get_minimized()
        # ожидается, что все 4 конъюнкции останутся (они не склеиваются в более простые)
        self.assertIn("a&b&c", min_dnf)
        self.assertIn("a&b&d", min_dnf)
        self.assertIn("a&c&d", min_dnf)
        self.assertIn("b&c&d", min_dnf)

    def test_2vars(self):
        # a & b
        func = BooleanFunction("a&b")
        km = KarnaughMap(func)
        self.assertEqual(km.get_minimized(), "a&b")

        # a | b
        func = BooleanFunction("a|b")
        km = KarnaughMap(func)
        min_dnf = km.get_minimized()
        # удаляем пробелы и сравниваем с допустимыми вариантами
        norm = min_dnf.replace(" ", "")
        self.assertIn(norm, {"a|b", "b|a"})

        # a xor b = (!a&b)|(a&!b)
        func = BooleanFunction("(a&!b)|(!a&b)")
        km = KarnaughMap(func)
        min_dnf = km.get_minimized()
        terms = [t.strip() for t in min_dnf.replace(" ", "").split("|")]
        self.assertIn("!a&b", terms)
        self.assertIn("a&!b", terms)

        # функция от 2 переменных, где одна фиктивна: f = a
        func = BooleanFunction("(a&b)|(a&!b)")
        km = KarnaughMap(func)
        self.assertEqual(km.get_minimized().replace(" ", ""), "a")

    def test_5vars(self):
        # (e&a&b) | (!e&a&b) = a&b
        func = BooleanFunction("(e&a&b)|(!e&a&b)")
        km = KarnaughMap(func)
        self.assertEqual(km.get_minimized().replace(" ", ""), "a&b")

        # функция, зависящая от всех пяти
        expr = "(a&b&c&d&e)|(a&b&c&d&!e)"
        func = BooleanFunction(expr)
        km = KarnaughMap(func)
        self.assertEqual(km.get_minimized().replace(" ", ""), "a&b&c&d")

        # сложная функция: (a&b) | (!a&c&d&e)
        func = BooleanFunction("(a&b)|(!a&c&d&e)")
        km = KarnaughMap(func)
        min_dnf = km.get_minimized()
        # разбиваем на термы (без пробелов)
        terms = [t.strip() for t in min_dnf.replace(" ", "").split("|")]
        # проверяем, что есть терм a&b
        self.assertTrue(any(set(t.split("&")) == {"a", "b"} for t in terms))
        # и терм, содержащий !a, c, d, e (порядок любой)
        self.assertTrue(any("!a" in t and "c" in t and "d" in t and "e" in t for t in terms))

        # функция-константа 1
        func = BooleanFunction("a|!a")
        km = KarnaughMap(func)
        self.assertEqual(km.get_minimized().replace(" ", ""), "1")

        # константа 0
        func = BooleanFunction("a&!a")
        km = KarnaughMap(func)
        self.assertEqual(km.get_minimized().replace(" ", ""), "0")



if __name__ == '__main__':
    unittest.main()