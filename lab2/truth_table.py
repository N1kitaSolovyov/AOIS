from typing import List, Tuple
from boolean_core import BooleanFunction


class TruthTable:
    def __init__(self, func: BooleanFunction):
        self.func = func
        self.vars = func.get_variables()
        self.n = len(self.vars)
        self.rows = self._build()

    def _build(self) -> List[Tuple[Tuple[int, ...], int]]:
        rows = []
        for i in range(1 << self.n):
            values = tuple((i >> (self.n - 1 - j)) & 1 for j in range(self.n))
            assignment = {var: values[j] for j, var in enumerate(self.vars)}
            res = self.func.evaluate(assignment)
            rows.append((values, res))
        return rows

    def display(self):
        header = ' '.join(self.vars) + ' | f'
        print(header)
        print('-' * len(header))
        for values, res in self.rows:
            print(' '.join(str(v) for v in values) + f' | {res}')

    def get_rows(self) -> List[Tuple[Tuple[int, ...], int]]:
        return self.rows
