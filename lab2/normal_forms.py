from typing import List, Tuple
from boolean_core import BooleanFunction
from truth_table import TruthTable


class NormalFormsBuilder:
    def __init__(self, func: BooleanFunction):
        self.func = func
        self.tt = TruthTable(func)
        self.vars = func.get_variables()
        self.rows = self.tt.get_rows()

    def _build_form(self, target: int, op: str, connective: str) -> str:
        if not self.vars:
            value = self.rows[0][1] if self.rows else 0
            return str(value)
        terms = []
        for values, res in self.rows:
            if res != target:
                continue
            term_parts = []
            for var, val in zip(self.vars, values):
                if target == 1:
                    term_parts.append(var if val == 1 else f'!{var}')
                else:
                    term_parts.append(var if val == 0 else f'!{var}')
            terms.append('(' + connective.join(term_parts) + ')')

        if terms:
            return op.join(terms)
        return '0' if target == 1 else '1'

    def get_sdnf(self) -> str:
        return self._build_form(1, '|', '&')

    def get_sknf(self) -> str:
        return self._build_form(0, '&', '|')

    def get_numeric_sdnf(self) -> List[int]:
        return [self._row_to_number(values) for values, res in self.rows if res == 1]

    def get_numeric_sknf(self) -> List[int]:
        return [self._row_to_number(values) for values, res in self.rows if res == 0]

    def _row_to_number(self, values: Tuple[int, ...]) -> int:
        num = 0
        for val in values:
            num = (num << 1) | val
        return num

    def get_index_form(self) -> int:
        return int(self.get_index_binary(), 2)

    def get_index_binary(self) -> str:
        return ''.join(str(res) for _, res in self.rows)
