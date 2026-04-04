# normal_forms.py
from typing import List
from boolean_core import BooleanFunction
from truth_table import TruthTable

class NormalFormsBuilder:
    def __init__(self, func: BooleanFunction):
        self.func = func
        self.tt = TruthTable(func)
        self.vars = func.get_variables()
        self.rows = self.tt.get_rows()

    def _build_form(self, target: int, op: str, connective: str) -> str:
        terms = []
        for values, res in self.rows:
            if res == target:
                term_parts = []
                for var, val in zip(self.vars, values):
                    if (target == 1 and val == 0) or (target == 0 and val == 1):
                        term_parts.append(f"!{var}")
                    else:
                        term_parts.append(var)
                terms.append("(" + connective.join(term_parts) + ")")
        return op.join(terms)

    def get_sdnf(self) -> str:
        return self._build_form(1, "|", "&")

    def get_sknf(self) -> str:
        return self._build_form(0, "&", "|")

    def get_numeric_sdnf(self) -> List[int]:
        numbers = []
        n = len(self.vars)
        for values, res in self.rows:
            if res == 1:
                num = 0
                for j, val in enumerate(values):
                    num |= (val << (n - 1 - j))
                numbers.append(num)
        return numbers

    def get_numeric_sknf(self) -> List[int]:
        numbers = []
        n = len(self.vars)
        for values, res in self.rows:
            if res == 0:
                num = 0
                for j, val in enumerate(values):
                    num |= (val << (n - 1 - j))
                numbers.append(num)
        return numbers

    def get_index_form(self) -> int:
        binary = ''.join(str(res) for _, res in self.rows)
        return int(binary, 2)