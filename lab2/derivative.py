from itertools import combinations
from typing import Dict, List, Sequence, Tuple
from boolean_core import BooleanFunction
from truth_table import TruthTable


def _tuple_to_number(values: Tuple[int, ...]) -> int:
    num = 0
    for v in values:
        num = (num << 1) | v
    return num


class BooleanDerivative:
    def __init__(self, func: BooleanFunction):
        self.func = func
        self.tt = TruthTable(func)
        self.vars = func.get_variables()
        self.rows = self.tt.get_rows()

    def partial_derivative(self, var: str) -> List[Tuple[Tuple[int, ...], int]]:
        return self.mixed_derivative([var])

    def mixed_derivative(self, var_list: Sequence[str]) -> List[Tuple[Tuple[int, ...], int]]:
        if not var_list:
            raise ValueError('Список переменных для производной пуст')
        if len(set(var_list)) != len(var_list):
            raise ValueError('В смешанной производной переменные не должны повторяться')
        for var in var_list:
            if var not in self.vars:
                raise ValueError(f'Переменная {var} не входит в функцию')
        if len(var_list) > min(4, len(self.vars)):
            raise ValueError('Поддерживаются производные не выше 4-го порядка и не выше числа переменных функции')

        idxs = [self.vars.index(v) for v in var_list]
        groups: Dict[Tuple[int, ...], List[int]] = {}
        for values, res in self.rows:
            rest = tuple(values[i] for i in range(len(values)) if i not in idxs)
            groups.setdefault(rest, []).append(res)

        result = []
        expected_group_size = 1 << len(var_list)
        for rest, vals in groups.items():
            if len(vals) != expected_group_size:
                raise ValueError('Таблица истинности неполная: не хватает строк для вычисления производной')
            xor_val = 0
            for val in vals:
                xor_val ^= val
            result.append((rest, xor_val))
        result.sort(key=lambda item: _tuple_to_number(item[0]) if item[0] else 0)
        return result

    def derivative_report(self, var_list: Sequence[str]) -> Dict[str, object]:
        rows = self.mixed_derivative(var_list)
        remaining_vars = [v for v in self.vars if v not in var_list]
        binary_vector = ''.join(str(val) for _, val in rows) or '0'
        ones = [_tuple_to_number(values) for values, val in rows if val == 1]
        return {
            'diff_vars': list(var_list),
            'order': len(var_list),
            'remaining_vars': remaining_vars,
            'rows': rows,
            'vector': binary_vector,
            'numeric': ones,
            'sdnf': self._rows_to_sdnf(rows, remaining_vars),
        }

    def all_reports(self, max_order: int = 4) -> List[Dict[str, object]]:
        max_order = min(max_order, len(self.vars), 4)
        reports: List[Dict[str, object]] = []
        for order in range(1, max_order + 1):
            for var_list in combinations(self.vars, order):
                reports.append(self.derivative_report(var_list))
        return reports

    def format_report(self, report: Dict[str, object]) -> str:
        diff_vars: List[str] = report['diff_vars']  # type: ignore[assignment]
        remaining_vars: List[str] = report['remaining_vars']  # type: ignore[assignment]
        rows: List[Tuple[Tuple[int, ...], int]] = report['rows']  # type: ignore[assignment]
        numeric: List[int] = report['numeric']  # type: ignore[assignment]
        vector: str = report['vector']  # type: ignore[assignment]
        sdnf: str = report['sdnf']  # type: ignore[assignment]

        order = len(diff_vars)
        numerator = '∂f' if order == 1 else f'∂^{order}f'
        denominator = ''.join(f'∂{v}' for v in diff_vars)
        title = f'{numerator}/{denominator}'

        lines = [title]
        if remaining_vars:
            lines.append('  Оставшиеся переменные: ' + ', '.join(remaining_vars))
            header = '  ' + ' '.join(remaining_vars) + ' | D'
            lines.append(header)
            lines.append('  ' + '-' * (len(header) - 2))
            for values, val in rows:
                lines.append('  ' + ' '.join(str(v) for v in values) + f' | {val}')
        else:
            const_val = rows[0][1] if rows else 0
            lines.append(f'  Константа: {const_val}')
        lines.append(f'  Вектор значений: {vector}')
        lines.append(f'  Числовая форма: {numeric}')
        lines.append(f'  СДНФ производной: {sdnf}')
        return '\n'.join(lines)

    @staticmethod
    def _rows_to_sdnf(rows: List[Tuple[Tuple[int, ...], int]], vars_list: List[str]) -> str:
        ones = [(values, val) for values, val in rows if val == 1]
        if not ones:
            return '0'
        if not vars_list:
            return '1'
        terms = []
        for values, _ in ones:
            parts = [var if val == 1 else f'!{var}' for var, val in zip(vars_list, values)]
            terms.append('(' + '&'.join(parts) + ')')
        return '|'.join(terms)


class DummyVariableFinder:
    def __init__(self, func: BooleanFunction):
        self.func = func
        self.tt = TruthTable(func)
        self.vars = func.get_variables()
        self.rows = self.tt.get_rows()

    def find_dummy_variables(self) -> List[str]:
        return [var for idx, var in enumerate(self.vars) if self._is_dummy(idx)]

    def _is_dummy(self, idx: int) -> bool:
        groups: Dict[Tuple[int, ...], set] = {}
        for values, res in self.rows:
            rest = tuple(values[i] for i in range(len(values)) if i != idx)
            groups.setdefault(rest, set()).add(res)
        return all(len(results) == 1 for results in groups.values())
