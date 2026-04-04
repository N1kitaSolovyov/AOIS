# post_classes.py
from typing import List, Tuple
from boolean_core import BooleanFunction
from truth_table import TruthTable

class PostClasses:
    def __init__(self, func: BooleanFunction):
        self.func = func
        self.tt = TruthTable(func)
        self.vars = func.get_variables()
        self.rows = self.tt.get_rows()
        self.n = len(self.vars)
        self.size = 1 << self.n

    def is_T0(self) -> bool:
        # Находим набор из всех нулей
        zero_tuple = (0,) * self.n
        for vals, res in self.rows:
            if vals == zero_tuple:
                return res == 0
        return False

    def is_T1(self) -> bool:
        one_tuple = (1,) * self.n
        for vals, res in self.rows:
            if vals == one_tuple:
                return res == 1
        return False

    def is_S(self) -> bool:
        # Строим словарь для быстрого доступа
        value_of = {vals: res for vals, res in self.rows}
        half = self.size // 2
        for i in range(half):
            # Набор i (интерпретируем как битовую строку)
            vals = tuple((i >> (self.n - 1 - j)) & 1 for j in range(self.n))
            opp_vals = tuple(1 - v for v in vals)
            if value_of[vals] == value_of[opp_vals]:
                return False
        return True

    def is_M(self) -> bool:
        # Перебираем все пары наборов
        for vals1, res1 in self.rows:
            for vals2, res2 in self.rows:
                # Проверяем, что vals1 <= vals2 покомпонентно
                if all(v1 <= v2 for v1, v2 in zip(vals1, vals2)):
                    if res1 > res2:
                        return False
        return True

    def is_L(self) -> bool:
        # Получаем коэффициенты полинома Жегалкина методом треугольника
        coeffs = self._zhegalkin_coeffs()
        # Если есть ненулевой коэффициент при конъюнкции двух и более переменных -> нелинейна
        for mask, c in enumerate(coeffs):
            if mask != 0 and bin(mask).count('1') >= 2 and c != 0:
                return False
        return True

    def _zhegalkin_coeffs(self) -> List[int]:
        # Строим вектор значений в порядке возрастания номеров наборов (0..size-1)
        f = [0] * self.size
        for vals, res in self.rows:
            # номер набора
            idx = 0
            for j, v in enumerate(vals):
                idx = (idx << 1) | v
            f[idx] = res
        # Преобразование Уолша-Адамара (XOR)
        for bit in range(self.n):
            step = 1 << bit
            for i in range(self.size):
                if i & (1 << bit):
                    f[i] ^= f[i ^ step]
        return f

    def get_zhegalkin_polynomial(self) -> str:
        coeffs = self._zhegalkin_coeffs()
        terms = []
        for mask, c in enumerate(coeffs):
            if c == 0:
                continue
            if mask == 0:
                terms.append("1")
            else:
                var_names = []
                # Биты маски: младший бит соответствует последней переменной
                # Упорядочим переменные в том же порядке, что в self.vars
                # Для единообразия выводим в алфавитном порядке переменных, соответствующих единичным битам
                for j, var in enumerate(self.vars):
                    # Битовая позиция: старший бит маски соответствует первой переменной
                    if mask & (1 << (self.n - 1 - j)):
                        var_names.append(var)
                terms.append("&".join(var_names))
        if not terms:
            return "0"
        return " ⊕ ".join(terms)