from typing import List
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
        zero_tuple = (0,) * self.n
        return next((res == 0 for vals, res in self.rows if vals == zero_tuple), False)

    def is_T1(self) -> bool:
        one_tuple = (1,) * self.n
        return next((res == 1 for vals, res in self.rows if vals == one_tuple), False)

    def is_S(self) -> bool:
        if self.n == 0:
            return False
        value_of = {vals: res for vals, res in self.rows}
        for i in range(self.size // 2):
            vals = tuple((i >> (self.n - 1 - j)) & 1 for j in range(self.n))
            opp_vals = tuple(1 - v for v in vals)
            if value_of[vals] == value_of[opp_vals]:
                return False
        return True

    def is_M(self) -> bool:
        for vals1, res1 in self.rows:
            for vals2, res2 in self.rows:
                if all(v1 <= v2 for v1, v2 in zip(vals1, vals2)) and res1 > res2:
                    return False
        return True

    def is_L(self) -> bool:
        coeffs = self._zhegalkin_coeffs()
        for mask, coeff in enumerate(coeffs):
            if coeff and bin(mask).count('1') >= 2:
                return False
        return True

    def _zhegalkin_coeffs(self) -> List[int]:
        f = [0] * self.size
        for vals, res in self.rows:
            idx = 0
            for v in vals:
                idx = (idx << 1) | v
            f[idx] = res

        for bit in range(self.n):
            step = 1 << bit
            for i in range(self.size):
                if i & step:
                    f[i] ^= f[i ^ step]
        return f

    def get_zhegalkin_polynomial(self) -> str:
        coeffs = self._zhegalkin_coeffs()
        terms = []
        for mask, coeff in enumerate(coeffs):
            if coeff == 0:
                continue
            if mask == 0:
                terms.append('1')
                continue
            var_names = []
            for j, var in enumerate(self.vars):
                if mask & (1 << (self.n - 1 - j)):
                    var_names.append(var)
            terms.append('&'.join(var_names))
        return ' ⊕ '.join(terms) if terms else '0'
