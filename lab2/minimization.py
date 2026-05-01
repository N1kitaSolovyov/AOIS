from itertools import combinations, product
from typing import Dict, List, Optional, Sequence, Set, Tuple

from boolean_core import BooleanFunction
from truth_table import TruthTable


class QuineMcCluskey:
    """Расчётный и расчётно-табличный методы минимизации для ДНФ и КНФ."""

    def __init__(self, func: BooleanFunction):
        self.func = func
        self.vars = func.get_variables()
        self.tt = TruthTable(func)
        self.rows = self.tt.get_rows()
        self.one_values = [vals for vals, res in self.rows if res == 1]
        self.zero_values = [vals for vals, res in self.rows if res == 0]
        self.ones = [''.join(str(bit) for bit in vals) for vals in self.one_values]
        self.zeros = [''.join(str(bit) for bit in vals) for vals in self.zero_values]
        self.one_numbers = [self._bits_to_int(bits) for bits in self.ones]
        self.zero_numbers = [self._bits_to_int(bits) for bits in self.zeros]
        self.is_zero = len(self.ones) == 0
        self.is_one = len(self.ones) == (1 << len(self.vars))

    @staticmethod
    def _bits_to_int(bits: str) -> int:
        clean = bits.replace('-', '0')
        return int(clean, 2) if clean else 0

    @staticmethod
    def _count_ones(term: str) -> int:
        return term.count('1')

    @staticmethod
    def _literal_count(term: str) -> int:
        return sum(ch != '-' for ch in term)

    @staticmethod
    def _can_combine(t1: str, t2: str) -> bool:
        diff = 0
        for c1, c2 in zip(t1, t2):
            if c1 == c2:
                continue
            if c1 == '-' or c2 == '-':
                return False
            diff += 1
            if diff > 1:
                return False
        return diff == 1

    @staticmethod
    def _combine(t1: str, t2: str) -> str:
        return ''.join(c1 if c1 == c2 else '-' for c1, c2 in zip(t1, t2))

    def _term_to_expr(self, term: str) -> str:
        return self._pattern_to_expr(term, form='dnf')

    def _clause_to_expr(self, term: str) -> str:
        return self._pattern_to_expr(term, form='cnf')

    def _pattern_to_expr(self, term: str, form: str) -> str:
        parts = []

        for var, ch in zip(self.vars, term):
            if ch == '-':
                continue

            if form == 'dnf':
                parts.append(f'!{var}' if ch == '0' else var)
            else:
                parts.append(var if ch == '0' else f'!{var}')

        if not parts:
            return '1' if form == 'dnf' else '0'

        joiner = '&' if form == 'dnf' else '|'
        expr = joiner.join(parts)

        return expr if form == 'dnf' or len(parts) == 1 else f'({expr})'

    def _covers(self, imp: str) -> Set[int]:
        return self._covers_generic(imp, self.ones, self.one_numbers)

    def _covers_zero(self, imp: str) -> Set[int]:
        return self._covers_generic(imp, self.zeros, self.zero_numbers)

    @staticmethod
    def _covers_generic(
        imp: str,
        source_bits: Sequence[str],
        source_numbers: Sequence[int],
    ) -> Set[int]:
        covered: Set[int] = set()

        for num, term in zip(source_numbers, source_bits):
            if all(imp[i] == '-' or imp[i] == term[i] for i in range(len(imp))):
                covered.add(num)

        return covered

    def _get_prime_patterns_with_stages(
        self,
        patterns: Sequence[str],
        form: str,
    ) -> Tuple[List[str], List[str]]:
        if not patterns:
            return [], ['Минимизация не требуется: выбранное множество наборов пусто.']

        if len(patterns) == (1 << len(self.vars)):
            full = '-' * len(self.vars)
            kind = '1' if form == 'dnf' else '0'
            return [full], [f'Функция тождественно равна {kind}, минимизация не требуется.']

        from collections import defaultdict

        formatter = self._term_to_expr if form == 'dnf' else self._clause_to_expr

        groups: Dict[int, List[str]] = defaultdict(list)
        for term in patterns:
            groups[self._count_ones(term)].append(term)

        for key in list(groups.keys()):
            groups[key] = sorted(set(groups[key]))

        stages: List[str] = []
        prime_patterns: Set[str] = set()
        stage_num = 1

        while groups:
            lines = [f'Этап {stage_num}:']

            for count in sorted(groups):
                group_terms = ', '.join(groups[count])
                lines.append(f'  Группа {count}: {group_terms}')

            new_groups: Dict[int, Set[str]] = defaultdict(set)
            used_this_pass: Set[str] = set()
            combinations_made: List[str] = []

            for count in sorted(groups):
                if count + 1 not in groups:
                    continue

                for t1 in groups[count]:
                    for t2 in groups[count + 1]:
                        if self._can_combine(t1, t2):
                            new_term = self._combine(t1, t2)
                            new_groups[self._count_ones(new_term)].add(new_term)
                            used_this_pass.add(t1)
                            used_this_pass.add(t2)

                            combinations_made.append(
                                f'  {t1} ({formatter(t1)}) + {t2} ({formatter(t2)}) -> '
                                f'{new_term} ({formatter(new_term)})'
                            )

            if combinations_made:
                lines.append('  Склейки:')
                lines.extend(sorted(set(combinations_made)))
            else:
                lines.append('  Склеек на этом этапе нет.')

            for count, terms in groups.items():
                for term in terms:
                    if term not in used_this_pass:
                        prime_patterns.add(term)

            stages.append('\n'.join(lines))
            groups = {count: sorted(terms) for count, terms in new_groups.items() if terms}
            stage_num += 1

        prime_list = sorted(prime_patterns, key=lambda term: (self._literal_count(term), term))
        return prime_list, stages

    def _get_prime_implicants_with_stages(self) -> Tuple[List[str], List[str]]:
        if self.is_zero:
            return [], ['Функция тождественно равна 0, минимизация не требуется.']

        if self.is_one:
            return ['-' * len(self.vars)], ['Функция тождественно равна 1, минимизация не требуется.']

        return self._get_prime_patterns_with_stages(self.ones, form='dnf')

    def _select_exact_cover(
        self,
        imp_covers: Dict[str, Set[int]],
        target_numbers: Optional[Sequence[int]] = None,
        form: str = 'dnf',
    ) -> Tuple[List[str], List[str]]:
        targets = set(self.one_numbers if target_numbers is None else target_numbers)
        formatter = self._term_to_expr if form == 'dnf' else self._clause_to_expr
        item_name = 'Ядро покрытия'

        from collections import Counter

        counter = Counter()
        for cover in imp_covers.values():
            counter.update(cover)

        essential = sorted(
            [imp for imp, cover in imp_covers.items() if any(counter[m] == 1 for m in cover)],
            key=lambda term: (self._literal_count(term), term),
        )

        essential_set = set(essential)

        covered = set()
        for imp in essential:
            covered.update(imp_covers[imp])

        uncovered = targets - covered

        logs = []
        if essential:
            logs.append(item_name + ': ' + ', '.join(f'{imp} ({formatter(imp)})' for imp in essential))
        else:
            logs.append(item_name + ' отсутствует.')

        if not uncovered:
            return essential, logs

        candidates = [
            imp
            for imp in imp_covers
            if imp not in essential_set and (imp_covers[imp] & uncovered)
        ]

        best_solution: Optional[List[str]] = None
        best_score: Optional[Tuple[int, int]] = None

        def score(solution: Sequence[str]) -> Tuple[int, int]:
            return len(solution), sum(self._literal_count(term) for term in solution)

        def backtrack(
            chosen: List[str],
            remaining_uncovered: Set[int],
            available: List[str],
        ):
            nonlocal best_solution, best_score

            if not remaining_uncovered:
                current = essential + chosen
                current_score = score(current)

                if best_score is None or current_score < best_score:
                    best_solution = current[:]
                    best_score = current_score

                return

            if best_score is not None and len(essential) + len(chosen) > best_score[0]:
                return

            options_per_target = []

            for target in remaining_uncovered:
                options = [imp for imp in available if target in imp_covers[imp]]

                if not options:
                    return

                options_per_target.append((len(options), target, options))

            _, _, options = min(options_per_target, key=lambda item: item[0])

            options = sorted(
                options,
                key=lambda imp: (
                    -len(imp_covers[imp] & remaining_uncovered),
                    self._literal_count(imp),
                    imp,
                ),
            )

            for imp in options:
                chosen.append(imp)

                new_uncovered = remaining_uncovered - imp_covers[imp]
                new_available = [candidate for candidate in available if candidate > imp]

                backtrack(chosen, new_uncovered, new_available)

                chosen.pop()

        backtrack([], uncovered, sorted(candidates))

        if best_solution is None:
            raise ValueError('Не удалось построить точное покрытие для минимизации')

        extras = [imp for imp in best_solution if imp not in essential_set]

        if extras:
            logs.append('Дополнительно выбраны: ' + ', '.join(f'{imp} ({formatter(imp)})' for imp in extras))

        return best_solution, logs

    def _format_result(self, chosen: Sequence[str], form: str = 'dnf') -> str:
        if not chosen:
            return '0' if form == 'dnf' else '1'

        formatter = self._term_to_expr if form == 'dnf' else self._clause_to_expr
        expressions = [formatter(term) for term in chosen]
        joiner = ' | ' if form == 'dnf' else ' & '

        return joiner.join(expressions)

    def _minimize(self, form: str, tabular: bool) -> str:
        if form == 'dnf':
            if self.is_zero:
                print('Функция тождественно равна 0')
                return '0'

            if self.is_one:
                print('Функция тождественно равна 1')
                return '1'

            patterns = self.ones
            numbers = self.one_numbers
            label = 'импликанты'
        else:
            if self.is_zero:
                print('Функция тождественно равна 0')
                return '0'

            if self.is_one:
                print('Функция тождественно равна 1')
                return '1'

            patterns = self.zeros
            numbers = self.zero_numbers
            label = 'макстермы'

        primes, stages = self._get_prime_patterns_with_stages(patterns, form=form)
        formatter = self._term_to_expr if form == 'dnf' else self._clause_to_expr
        covers_fn = self._covers if form == 'dnf' else self._covers_zero

        for stage in stages:
            print(stage)
            print()

        if tabular:
            imp_covers = {imp: covers_fn(imp) for imp in primes}

            header = ['Импликанта' if form == 'dnf' else 'Клауза'] + [
                f'm{m}' if form == 'dnf' else f'M{m}'
                for m in numbers
            ]

            widths = [max(10, len(header[0]))] + [max(3, len(h)) for h in header[1:]]

            print('Таблица покрытия:')
            print(' | '.join(h.ljust(widths[i]) for i, h in enumerate(header)))
            print('-' * (sum(widths) + 3 * (len(widths) - 1)))

            for imp in primes:
                row = [imp.ljust(widths[0])]
                cover = imp_covers[imp]

                for i, number in enumerate(numbers, start=1):
                    row.append(('X' if number in cover else '.').ljust(widths[i]))

                print(' | '.join(row))
        else:
            print('Простые ' + label + ':')

            for imp in primes:
                print(f'  {imp} -> {formatter(imp)}')

            imp_covers = {imp: covers_fn(imp) for imp in primes}

        chosen, logs = self._select_exact_cover(
            imp_covers,
            target_numbers=numbers,
            form=form,
        )

        print()

        for line in logs:
            print(line)

        result = self._format_result(chosen, form=form)
        form_name = 'ДНФ' if form == 'dnf' else 'КНФ'
        method_name = 'расчётно-табличный метод' if tabular else 'расчётный метод'

        print(f'\nРезультат минимизации ({method_name}, {form_name}): {result}')

        return result

    def minimize_calculated(self) -> str:
        return self._minimize(form='dnf', tabular=False)

    def minimize_calculated_cnf(self) -> str:
        return self._minimize(form='cnf', tabular=False)

    def minimize_tabular(self) -> str:
        return self._minimize(form='dnf', tabular=True)

    def minimize_tabular_cnf(self) -> str:
        return self._minimize(form='cnf', tabular=True)


class KarnaughMap:
    """Минимизация картой Карно для 1-5 переменных: ДНФ и КНФ."""

    def __init__(self, func: BooleanFunction):
        self.func = func
        self.vars = func.get_variables()
        self.tt = TruthTable(func)
        self.rows_tt = self.tt.get_rows()
        self.n = len(self.vars)

        if self.n < 1 or self.n > 5:
            raise ValueError('Карта Карно поддерживается для 1-5 переменных')

        (
            self.map,
            self.row_labels,
            self.col_labels,
            self.row_vars,
            self.col_vars,
            self.layer_var,
        ) = self._build_map()

    @staticmethod
    def _gray_code(bits: int) -> List[str]:
        return [format(i ^ (i >> 1), f'0{bits}b') for i in range(1 << bits)]

    @staticmethod
    def _literal_count_expr(term: str) -> int:
        return 0 if term in {'0', '1'} else term.count('&') + term.count('|') + 1

    def _pattern_to_expr(self, pattern: str, form: str) -> str:
        parts = []

        for var, ch in zip(self.vars, pattern):
            if ch == '-':
                continue

            if form == 'dnf':
                parts.append(f'!{var}' if ch == '0' else var)
            else:
                parts.append(var if ch == '0' else f'!{var}')

        if not parts:
            return '1' if form == 'dnf' else '0'

        joiner = '&' if form == 'dnf' else '|'
        expr = joiner.join(parts)

        return expr if form == 'dnf' or len(parts) == 1 else f'({expr})'

    def _build_map(self):
        if self.n == 1:
            row_labels = ['0']
            col_labels = ['0', '1']
            map_data = [[0, 0]]

            for values, res in self.rows_tt:
                map_data[0][values[0]] = res

            return map_data, row_labels, col_labels, [], [self.vars[0]], None

        if self.n == 2:
            row_vars = [self.vars[0]]
            col_vars = [self.vars[1]]
            row_labels = ['0', '1']
            col_labels = ['0', '1']
            map_data = [[0, 0], [0, 0]]

            for values, res in self.rows_tt:
                map_data[values[0]][values[1]] = res

            return map_data, row_labels, col_labels, row_vars, col_vars, None

        if self.n == 3:
            row_vars = [self.vars[0]]
            col_vars = self.vars[1:]
            row_labels = ['0', '1']
            col_labels = self._gray_code(2)
            map_data = [[0] * 4 for _ in range(2)]

            for values, res in self.rows_tt:
                row_str = str(values[0])
                col_str = ''.join(str(v) for v in values[1:])

                map_data[row_labels.index(row_str)][col_labels.index(col_str)] = res

            return map_data, row_labels, col_labels, row_vars, col_vars, None

        if self.n == 4:
            row_vars = self.vars[:2]
            col_vars = self.vars[2:]
            row_labels = self._gray_code(2)
            col_labels = self._gray_code(2)
            map_data = [[0] * 4 for _ in range(4)]

            for values, res in self.rows_tt:
                row_str = ''.join(str(v) for v in values[:2])
                col_str = ''.join(str(v) for v in values[2:])

                map_data[row_labels.index(row_str)][col_labels.index(col_str)] = res

            return map_data, row_labels, col_labels, row_vars, col_vars, None

        row_vars = self.vars[:2]
        col_vars = self.vars[2:4]
        layer_var = self.vars[4]
        row_labels = self._gray_code(2)
        col_labels = self._gray_code(2)

        map0 = [[0] * 4 for _ in range(4)]
        map1 = [[0] * 4 for _ in range(4)]

        for values, res in self.rows_tt:
            row_str = ''.join(str(v) for v in values[:2])
            col_str = ''.join(str(v) for v in values[2:4])

            target_map = map0 if values[4] == 0 else map1
            target_map[row_labels.index(row_str)][col_labels.index(col_str)] = res

        return (map0, map1), row_labels, col_labels, row_vars, col_vars, layer_var

    def display(self):
        print('\nКарта Карно:')

        if self.n == 1:
            print(f"   {self.col_vars[0]}: 0 1")
            print('   ' + ' '.join(str(self.map[0][j]) for j in range(2)))

        elif self.n == 2:
            print(f"   {self.col_vars[0]}: 0 1")

            for i, row_label in enumerate(self.row_labels):
                print(f"{self.row_vars[0]}={row_label}  {self.map[i][0]} {self.map[i][1]}")

        elif self.n in (3, 4):
            print(f"   {''.join(self.col_vars)}: " + ' '.join(self.col_labels))

            for i, row_label in enumerate(self.row_labels):
                row_name = ''.join(self.row_vars) if self.row_vars else '•'
                print(f"{row_name}={row_label} " + ' '.join(str(x) for x in self.map[i]))

        else:
            map0, map1 = self.map

            print(f'Для {self.layer_var}=0:')
            print(f"   {''.join(self.col_vars)}: " + ' '.join(self.col_labels))

            for i, row_label in enumerate(self.row_labels):
                print(f"{''.join(self.row_vars)}={row_label} " + ' '.join(str(x) for x in map0[i]))

            print(f'\nДля {self.layer_var}=1:')
            print(f"   {''.join(self.col_vars)}: " + ' '.join(self.col_labels))

            for i, row_label in enumerate(self.row_labels):
                print(f"{''.join(self.row_vars)}={row_label} " + ' '.join(str(x) for x in map1[i]))

    def _pattern_from_row_col_sets(
        self,
        rect_rows,
        rect_cols,
        row_labels,
        col_labels,
        row_var_names,
        col_var_names,
    ) -> str:
        bits_by_var = {var: '-' for var in self.vars}

        if row_var_names and len(set(rect_rows)) != len(row_labels):
            fixed = [None] * len(row_var_names)

            for r in rect_rows:
                label = row_labels[r]

                for idx, ch in enumerate(label):
                    if fixed[idx] is None:
                        fixed[idx] = ch
                    elif fixed[idx] != ch:
                        fixed[idx] = '-'

            for idx, var in enumerate(row_var_names):
                bits_by_var[var] = fixed[idx] if fixed[idx] is not None else '-'

        if col_var_names and len(set(rect_cols)) != len(col_labels):
            fixed = [None] * len(col_var_names)

            for c in rect_cols:
                label = col_labels[c]

                for idx, ch in enumerate(label):
                    if fixed[idx] is None:
                        fixed[idx] = ch
                    elif fixed[idx] != ch:
                        fixed[idx] = '-'

            for idx, var in enumerate(col_var_names):
                bits_by_var[var] = fixed[idx] if fixed[idx] is not None else '-'

        return ''.join(bits_by_var[var] for var in self.vars)

    def _find_rectangles_2d_generic(
        self,
        data,
        rows,
        cols,
        row_labels,
        col_labels,
        row_var_names,
        col_var_names,
        target: int,
        form: str,
    ):
        ext_data = [
            [data[i % rows][j % cols] for j in range(cols * 2)]
            for i in range(rows * 2)
        ]

        sizes = [
            (height, width)
            for height in (1, 2, 4, 8)
            if height <= rows
            for width in (1, 2, 4, 8)
            if width <= cols
        ]

        rectangles = []

        for top in range(rows):
            for left in range(cols):
                for height, width in sizes:
                    ok = True

                    for i in range(top, top + height):
                        for j in range(left, left + width):
                            if ext_data[i][j] != target:
                                ok = False
                                break

                        if not ok:
                            break

                    if ok:
                        rect_rows = [(top + i) % rows for i in range(height)]
                        rect_cols = [(left + j) % cols for j in range(width)]
                        rectangles.append((rect_rows, rect_cols))

        unique_rectangles = {}

        for rect_rows, rect_cols in rectangles:
            key = (
                tuple(sorted(set(rect_rows))),
                tuple(sorted(set(rect_cols))),
            )

            unique_rectangles[key] = (list(key[0]), list(key[1]))

        rectangles = list(unique_rectangles.values())

        def is_subset(rect1, rect2):
            return set(rect1[0]).issubset(rect2[0]) and set(rect1[1]).issubset(rect2[1])

        maximal = []

        for i, rect in enumerate(rectangles):
            if any(i != j and is_subset(rect, other) for j, other in enumerate(rectangles)):
                continue

            maximal.append(rect)

        result = []

        for rect_rows, rect_cols in maximal:
            pattern = self._pattern_from_row_col_sets(
                rect_rows,
                rect_cols,
                row_labels,
                col_labels,
                row_var_names,
                col_var_names,
            )

            result.append(
                (
                    set(rect_rows),
                    set(rect_cols),
                    self._pattern_to_expr(pattern, form=form),
                )
            )

        return result

    def _find_rectangles_2d(
        self,
        data,
        rows,
        cols,
        row_labels,
        col_labels,
        row_var_names,
        col_var_names,
    ):
        return self._find_rectangles_2d_generic(
            data,
            rows,
            cols,
            row_labels,
            col_labels,
            row_var_names,
            col_var_names,
            target=1,
            form='dnf',
        )

    @staticmethod
    def _axis_group_sizes(axis_size: int) -> Tuple[int, ...]:
        sizes = []
        size = 1

        while size <= axis_size:
            sizes.append(size)
            size *= 2

        return tuple(sizes)

    @staticmethod
    def _cyclic_range(start: int, length: int, limit: int) -> Tuple[int, ...]:
        return tuple((start + offset) % limit for offset in range(length))

    @staticmethod
    def _normalize_3d_rectangle(rectangle):
        return tuple(tuple(sorted(set(axis))) for axis in rectangle)

    @staticmethod
    def _is_3d_subset(inner, outer) -> bool:
        return all(
            set(inner_axis).issubset(set(outer_axis))
            for inner_axis, outer_axis in zip(inner, outer)
        )

    @staticmethod
    def _target_cells_3d(
        data3d,
        rows: int,
        cols: int,
        target: int,
    ) -> Set[Tuple[int, int, int]]:
        return {
            (layer, row, col)
            for layer, row, col in product(range(2), range(rows), range(cols))
            if data3d[layer][row][col] == target
        }

    def _iter_3d_rectangles(self, rows: int, cols: int):
        layer_sizes = (1, 2)
        row_sizes = self._axis_group_sizes(rows)
        col_sizes = self._axis_group_sizes(cols)

        for layer_size, row_size, col_size in product(layer_sizes, row_sizes, col_sizes):
            for layer_start in range(2 - layer_size + 1):
                layer_range = tuple(range(layer_start, layer_start + layer_size))

                for row_start, col_start in product(range(rows), range(cols)):
                    row_range = self._cyclic_range(row_start, row_size, rows)
                    col_range = self._cyclic_range(col_start, col_size, cols)

                    yield layer_range, row_range, col_range

    @staticmethod
    def _is_target_rectangle_3d(data3d, rectangle, target: int) -> bool:
        layer_range, row_range, col_range = rectangle

        return all(
            data3d[layer][row][col] == target
            for layer, row, col in product(layer_range, row_range, col_range)
        )

    def _get_maximal_3d_rectangles(self, rectangles):
        unique_rectangles = []
        seen = set()

        for rectangle in rectangles:
            normalized = self._normalize_3d_rectangle(rectangle)

            if normalized not in seen:
                seen.add(normalized)
                unique_rectangles.append(normalized)

        maximal = []

        for i, rectangle in enumerate(unique_rectangles):
            is_inside_bigger = any(
                i != j and self._is_3d_subset(rectangle, other)
                for j, other in enumerate(unique_rectangles)
            )

            if not is_inside_bigger:
                maximal.append(rectangle)

        return maximal

    def _term_from_3d_rectangle(
        self,
        layer_range,
        row_range,
        col_range,
        form: str,
    ) -> str:
        if self.layer_var is None:
            raise ValueError('Для карты Карно из 5 переменных не задана переменная слоя')

        bits_by_var = {var: '-' for var in self.vars}

        if len(layer_range) == 1:
            bits_by_var[self.layer_var] = str(layer_range[0])

        row_col_pattern = self._pattern_from_row_col_sets(
            row_range,
            col_range,
            self.row_labels,
            self.col_labels,
            self.row_vars,
            self.col_vars,
        )

        for var, ch in zip(self.vars, row_col_pattern):
            if ch != '-':
                bits_by_var[var] = ch

        pattern = ''.join(bits_by_var[var] for var in self.vars)

        return self._pattern_to_expr(pattern, form=form)

    def _find_rectangles_3d_generic(
        self,
        data3d,
        rows: int,
        cols: int,
        target: int,
        form: str,
    ) -> List[Tuple[Set[Tuple[int, int, int]], str]]:
        valid_rectangles = [
            rectangle
            for rectangle in self._iter_3d_rectangles(rows, cols)
            if self._is_target_rectangle_3d(data3d, rectangle, target)
        ]

        maximal_rectangles = self._get_maximal_3d_rectangles(valid_rectangles)

        covers = []

        for layer_range, row_range, col_range in maximal_rectangles:
            cover = set(product(layer_range, row_range, col_range))
            term = self._term_from_3d_rectangle(
                layer_range,
                row_range,
                col_range,
                form,
            )

            covers.append((cover, term))

        return covers

    def _select_exact_cover_indices(
        self,
        cells: Set[Tuple],
        covers: List[Tuple[Set[Tuple], str]],
    ) -> List[int]:
        from collections import Counter

        if not cells:
            return []

        counter = Counter()

        for cover, _ in covers:
            counter.update(cover)

        essential_indices = []

        for idx, (cover, _) in enumerate(covers):
            if any(counter[cell] == 1 for cell in cover):
                essential_indices.append(idx)

        essential_indices = sorted(set(essential_indices))

        covered = set()

        for idx in essential_indices:
            covered.update(covers[idx][0])

        uncovered = cells - covered

        remaining_indices = [
            idx
            for idx in range(len(covers))
            if idx not in essential_indices and covers[idx][0] & uncovered
        ]

        best_indices: Optional[List[int]] = None
        best_score: Optional[Tuple[int, int]] = None

        def score(indices: Sequence[int]) -> Tuple[int, int]:
            terms = [covers[idx][1] for idx in indices]
            return len(indices), sum(self._literal_count_expr(term) for term in terms)

        def backtrack(
            current_indices: List[int],
            remaining_uncovered: Set[Tuple],
            candidate_indices: List[int],
        ):
            nonlocal best_indices, best_score

            if not remaining_uncovered:
                total_indices = essential_indices + current_indices
                current_score = score(total_indices)

                if best_score is None or current_score < best_score:
                    best_indices = total_indices[:]
                    best_score = current_score

                return

            if best_score is not None and len(essential_indices) + len(current_indices) > best_score[0]:
                return

            options_per_cell = []

            for cell in remaining_uncovered:
                options = [idx for idx in candidate_indices if cell in covers[idx][0]]

                if not options:
                    return

                options_per_cell.append((len(options), cell, options))

            _, _, options = min(options_per_cell, key=lambda item: item[0])

            options.sort(
                key=lambda idx: (
                    -len(covers[idx][0] & remaining_uncovered),
                    self._literal_count_expr(covers[idx][1]),
                    covers[idx][1],
                )
            )

            for idx in options:
                current_indices.append(idx)

                new_uncovered = remaining_uncovered - covers[idx][0]
                new_candidates = [other for other in candidate_indices if other > idx]

                backtrack(current_indices, new_uncovered, new_candidates)

                current_indices.pop()

        backtrack([], uncovered, sorted(remaining_indices))

        result = best_indices if best_indices is not None else essential_indices

        unique = []
        seen = set()

        for idx in result:
            if idx not in seen:
                unique.append(idx)
                seen.add(idx)

        return unique

    def _select_exact_cover_terms(
        self,
        cells: Set[Tuple],
        covers: List[Tuple[Set[Tuple], str]],
    ) -> List[str]:
        return [covers[idx][1] for idx in self._select_exact_cover_indices(cells, covers)]

    def _get_extremes(self) -> Tuple[bool, bool]:
        all_ones = all(res == 1 for _, res in self.rows_tt)
        all_zeros = all(res == 0 for _, res in self.rows_tt)

        return all_ones, all_zeros

    def _describe_cover_cells(self, cover: Set[Tuple], form: str) -> str:
        target_name = 'единиц' if form == 'dnf' else 'нулей'

        if not cover:
            return f'без {target_name}'

        ordered = sorted(cover)
        cell_strings = []

        for cell in ordered:
            if len(cell) == 2:
                cell_strings.append(f'({cell[0]},{cell[1]})')
            else:
                cell_strings.append(f'({cell[0]},{cell[1]},{cell[2]})')

        return ', '.join(cell_strings)

    def _build_kmap_solution(self, form: str):
        all_ones, all_zeros = self._get_extremes()

        if all_zeros:
            return '0', []

        if all_ones:
            return '1', []

        target = 1 if form == 'dnf' else 0
        group_word = 'Область единиц' if form == 'dnf' else 'Область нулей'
        label_word = 'импликанта' if form == 'dnf' else 'клауза'

        def finalize(covers):
            if not covers:
                return ('0' if form == 'dnf' else '1'), []

            chosen_indices = self._select_exact_cover_indices(cells, covers)
            chosen_terms = [covers[idx][1] for idx in chosen_indices]

            lines = []

            for number, idx in enumerate(chosen_indices, start=1):
                cover, term = covers[idx]

                lines.append(
                    f'{group_word} {number}: '
                    f'{self._describe_cover_cells(cover, form)} -> '
                    f'{label_word} {term}'
                )

            joiner = ' | ' if form == 'dnf' else ' & '
            result = joiner.join(chosen_terms) if chosen_terms else ('0' if form == 'dnf' else '1')

            return result, lines

        if self.n == 1:
            data = self.map[0]
            covers = []

            if form == 'dnf':
                if data[0] == 1 and data[1] == 0:
                    covers = [({(0, 0)}, f'!{self.col_vars[0]}')]
                elif data[0] == 0 and data[1] == 1:
                    covers = [({(0, 1)}, self.col_vars[0])]
                else:
                    return '1', [f'{group_word} 1: (0,0), (0,1) -> {label_word} 1']
            else:
                if data[0] == 0 and data[1] == 1:
                    covers = [({(0, 0)}, self.col_vars[0])]
                elif data[0] == 1 and data[1] == 0:
                    covers = [({(0, 1)}, f'!{self.col_vars[0]}')]
                else:
                    return '0', [f'{group_word} 1: (0,0), (0,1) -> {label_word} 0']

            cells = {cell for cover, _ in covers for cell in cover}

            return finalize(covers)

        if self.n in (2, 3, 4):
            data = self.map
            rows = len(self.row_labels)
            cols = len(self.col_labels)

            rects = self._find_rectangles_2d_generic(
                data,
                rows,
                cols,
                self.row_labels,
                self.col_labels,
                self.row_vars,
                self.col_vars,
                target=target,
                form=form,
            )

            cells = {
                (i, j)
                for i in range(rows)
                for j in range(cols)
                if data[i][j] == target
            }

            covers = []

            for row_set, col_set, term in rects:
                cover = {
                    (row, col)
                    for row in row_set
                    for col in col_set
                    if data[row][col] == target
                }

                if cover:
                    covers.append((cover, term))

            return finalize(covers)

        map0, map1 = self.map
        rows = len(self.row_labels)
        cols = len(self.col_labels)
        data3d = [map0, map1]

        cells = self._target_cells_3d(data3d, rows, cols, target)
        covers = self._find_rectangles_3d_generic(data3d, rows, cols, target, form)

        return finalize(covers)

    def print_minimization_report(self, form: str):
        result, lines = self._build_kmap_solution(form)
        form_name = 'ДНФ' if form == 'dnf' else 'КНФ'

        if lines:
            print(f'Построение минимальной {form_name} по карте Карно:')

            for line in lines:
                print(f'  {line}')
        else:
            print(f'Построение минимальной {form_name} по карте Карно: функция константна.')

        print(f'Результат минимизации (карта Карно, {form_name}): {result}')

        return result

    def _get_minimized_generic(self, form: str) -> str:
        result, _ = self._build_kmap_solution(form)

        return result

    def get_minimized(self) -> str:
        return self._get_minimized_generic('dnf')

    def get_minimized_cnf(self) -> str:
        return self._get_minimized_generic('cnf')