# derivative.py
from typing import List, Tuple
from boolean_core import BooleanFunction
from truth_table import TruthTable

class BooleanDerivative:
    def __init__(self, func: BooleanFunction):#Конструктор сохраняет функцию, таблицу истинности и строки таблицы
        self.func = func
        self.tt = TruthTable(func)
        self.vars = func.get_variables()
        self.rows = self.tt.get_rows()

    def partial_derivative(self, var: str) -> List[Tuple[Tuple[int, ...], int]]:
        if var not in self.vars:
            raise ValueError(f"Переменная {var} не входит в функцию")
        idx = self.vars.index(var)
        groups = {}
        for values, res in self.rows:
            rest = values[:idx] + values[idx+1:]
            key = rest
            if key not in groups:
                groups[key] = {}
            groups[key][values[idx]] = res
        result = []
        for rest, d in groups.items():
            val0 = d.get(0, 0)
            val1 = d.get(1, 0)
            result.append((rest, val0 ^ val1))
        # Сортировка по числовому значению остатка
        result.sort(key=lambda x: int(''.join(map(str, x[0])), 2) if x[0] else 0)
        return result

    def mixed_derivative(self, var_list: List[str]) -> List[Tuple[Tuple[int, ...], int]]:
        idxs = [self.vars.index(v) for v in var_list]
        groups = {}
        for values, res in self.rows:
            rest = tuple(values[i] for i in range(len(values)) if i not in idxs)
            key = rest
            if key not in groups:
                groups[key] = []
            groups[key].append(res)
        result = []
        for rest, lst in groups.items():
            xor_val = 0
            for r in lst:
                xor_val ^= r
            result.append((rest, xor_val))
        result.sort(key=lambda x: int(''.join(map(str, x[0])), 2) if x[0] else 0)
        return result

class DummyVariableFinder:
    def __init__(self, func: BooleanFunction):
        self.func = func
        self.tt = TruthTable(func)
        self.vars = func.get_variables()
        self.rows = self.tt.get_rows()

    def find_dummy_variables(self) -> List[str]:
        dummy = []
        for idx, var in enumerate(self.vars):
            if self._is_dummy(idx):
                dummy.append(var)
        return dummy

    def _is_dummy(self, idx: int) -> bool:
        groups = {}
        for values, res in self.rows:
            rest = tuple(values[i] for i in range(len(values)) if i != idx)
            key = rest
            if key not in groups:
                groups[key] = set()
            groups[key].add(res)
        # Переменная фиктивная, если для каждого остатка значение функции не зависит от переменной
        for s in groups.values():
            if len(s) > 1:
                return False
        return True