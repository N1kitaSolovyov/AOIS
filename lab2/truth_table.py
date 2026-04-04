# truth_table.py
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
        n = self.n
        vars_list = self.vars
        for i in range(1 << n):
            # Построение набора значений: старший бит – первая переменная
            values = tuple((i >> (n - 1 - j)) & 1 for j in range(n))
            assignment = {var: values[j] for j, var in enumerate(vars_list)}
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