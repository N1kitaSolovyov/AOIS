from itertools import combinations
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
from boolean_core import BooleanFunction
from truth_table import TruthTable


class QuineMcCluskey:
    """Расчётный и расчётно-табличный методы минимизации."""

    def __init__(self, func: BooleanFunction):
        self.func = func
        self.vars = func.get_variables()
        self.tt = TruthTable(func)
        self.rows = self.tt.get_rows()
        self.one_values = [vals for vals, res in self.rows if res == 1]
        self.ones = [''.join(str(bit) for bit in vals) for vals in self.one_values]
        self.one_numbers = [self._bits_to_int(bits) for bits in self.ones]
        self.is_zero = len(self.ones) == 0
        self.is_one = len(self.ones) == (1 << len(self.vars))

    @staticmethod
    def _bits_to_int(bits: str) -> int:
        normalized = bits.replace('-', '0')
        return int(normalized, 2) if normalized else 0

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
        parts = []
        for var, ch in zip(self.vars, term):
            if ch == '0':
                parts.append(f'!{var}')
            elif ch == '1':
                parts.append(var)
        return '&'.join(parts) if parts else '1'

    def _covers(self, imp: str) -> Set[int]:
        covered: Set[int] = set()
        for num, term in zip(self.one_numbers, self.ones):
            if all(imp[i] == '-' or imp[i] == term[i] for i in range(len(imp))):
                covered.add(num)
        return covered

    def _get_prime_implicants_with_stages(self) -> Tuple[List[str], List[str]]:
        if self.is_zero:
            return [], ['Функция тождественно равна 0, минимизация не требуется.']
        if self.is_one:
            return ['-' * len(self.vars)], ['Функция тождественно равна 1, минимизация не требуется.']

        from collections import defaultdict

        groups: Dict[int, List[str]] = defaultdict(list)
        for term in self.ones:
            groups[self._count_ones(term)].append(term)
        for key in list(groups.keys()):
            groups[key] = sorted(set(groups[key]))

        stages: List[str] = []
        prime_implicants: Set[str] = set()
        stage_num = 1

        while groups:
            lines = [f'Этап {stage_num}:']
            for count in sorted(groups):
                group_terms = ', '.join(groups[count])
                lines.append(f'  Группа {count}: {group_terms}')

            new_groups: Dict[int, Set[str]] = defaultdict(set)
            used_this_pass: Set[str] = set()
            combinations_made: List[str] = []

            sorted_keys = sorted(groups)
            for count in sorted_keys:
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
                                f'  {t1} ({self._term_to_expr(t1)}) + {t2} ({self._term_to_expr(t2)}) -> '
                                f'{new_term} ({self._term_to_expr(new_term)})'
                            )

            if combinations_made:
                lines.append('  Склейки:')
                lines.extend(sorted(set(combinations_made)))
            else:
                lines.append('  Склеек на этом этапе нет.')

            for count, terms in groups.items():
                for term in terms:
                    if term not in used_this_pass:
                        prime_implicants.add(term)

            stages.append('\n'.join(lines))
            groups = {count: sorted(terms) for count, terms in new_groups.items() if terms}
            stage_num += 1

        prime_list = sorted(prime_implicants, key=lambda term: (self._literal_count(term), term))
        return prime_list, stages

    def _select_exact_cover(self, imp_covers: Dict[str, Set[int]]) -> Tuple[List[str], List[str]]:
        all_minterms = set(self.one_numbers)
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
        uncovered = all_minterms - covered

        logs = []
        if essential:
            logs.append('Ядро покрытия: ' + ', '.join(f'{imp} ({self._term_to_expr(imp)})' for imp in essential))
        else:
            logs.append('Ядро покрытия отсутствует.')

        if not uncovered:
            return essential, logs

        candidates = [imp for imp in imp_covers if imp not in essential_set and (imp_covers[imp] & uncovered)]
        best_solution: Optional[List[str]] = None
        best_score: Optional[Tuple[int, int]] = None

        def score(solution: Sequence[str]) -> Tuple[int, int]:
            return (len(solution), sum(self._literal_count(term) for term in solution))

        def backtrack(chosen: List[str], remaining_uncovered: Set[int], available: List[str]):
            nonlocal best_solution, best_score
            if not remaining_uncovered:
                current = essential + chosen
                current_score = score(current)
                if best_score is None or current_score < best_score:
                    best_solution = current[:]
                    best_score = current_score
                return

            if best_score is not None:
                lower_bound_terms = len(essential) + len(chosen)
                if lower_bound_terms > best_score[0]:
                    return

            # Выбираем минтерм с минимальным количеством покрывающих кандидатов
            options_per_minterm = []
            for minterm in remaining_uncovered:
                options = [imp for imp in available if minterm in imp_covers[imp]]
                if not options:
                    return
                options_per_minterm.append((len(options), minterm, options))
            _, pivot, options = min(options_per_minterm, key=lambda item: item[0])

            options = sorted(
                options,
                key=lambda imp: (
                    -len(imp_covers[imp] & remaining_uncovered),
                    self._literal_count(imp),
                    imp,
                ),
            )
            for imp in options:
                new_uncovered = remaining_uncovered - imp_covers[imp]
                new_available = [candidate for candidate in available if candidate > imp]
                chosen.append(imp)
                backtrack(chosen, new_uncovered, new_available)
                chosen.pop()

        backtrack([], uncovered, sorted(candidates))
        if best_solution is None:
            raise ValueError('Не удалось построить точное покрытие для минимизации')

        extras = [imp for imp in best_solution if imp not in essential_set]
        if extras:
            logs.append('Дополнительно выбраны: ' + ', '.join(f'{imp} ({self._term_to_expr(imp)})' for imp in extras))
        return best_solution, logs

    def _format_result(self, chosen: Sequence[str]) -> str:
        if not chosen:
            return '0'
        expressions = [self._term_to_expr(term) for term in chosen]
        return ' | '.join(expressions)

    def minimize_calculated(self) -> str:
        if self.is_zero:
            print('Функция тождественно равна 0')
            return '0'
        if self.is_one:
            print('Функция тождественно равна 1')
            return '1'

        implicants, stages = self._get_prime_implicants_with_stages()
        for stage in stages:
            print(stage)
            print()
        print('Простые импликанты:')
        for imp in implicants:
            print(f'  {imp} -> {self._term_to_expr(imp)}')

        imp_covers = {imp: self._covers(imp) for imp in implicants}
        chosen, logs = self._select_exact_cover(imp_covers)
        print()
        for line in logs:
            print(line)

        result = self._format_result(chosen)
        print('\nРезультат минимизации (расчётный метод):', result)
        return result

    def minimize_tabular(self) -> str:
        if self.is_zero:
            print('Функция тождественно равна 0')
            return '0'
        if self.is_one:
            print('Функция тождественно равна 1')
            return '1'

        implicants, stages = self._get_prime_implicants_with_stages()
        for stage in stages:
            print(stage)
            print()

        imp_covers = {imp: self._covers(imp) for imp in implicants}
        minterms = self.one_numbers
        header = ['Импликанта'] + [f'm{m}' for m in minterms]
        widths = [max(10, len(header[0]))] + [max(3, len(h)) for h in header[1:]]
        print('Таблица покрытия:')
        print(' | '.join(h.ljust(widths[i]) for i, h in enumerate(header)))
        print('-' * (sum(widths) + 3 * (len(widths) - 1)))
        for imp in implicants:
            row = [imp.ljust(widths[0])]
            cover = imp_covers[imp]
            for i, minterm in enumerate(minterms, start=1):
                row.append(('X' if minterm in cover else '.').ljust(widths[i]))
            print(' | '.join(row))

        chosen, logs = self._select_exact_cover(imp_covers)
        print()
        for line in logs:
            print(line)

        result = self._format_result(chosen)
        print('\nРезультат минимизации (расчётно-табличный метод):', result)
        return result


class KarnaughMap:
    """Минимизация картой Карно для 1-5 переменных."""

    def __init__(self, func: BooleanFunction):
        self.func = func
        self.vars = func.get_variables()
        self.tt = TruthTable(func)
        self.rows_tt = self.tt.get_rows()
        self.n = len(self.vars)
        if self.n < 1 or self.n > 5:
            raise ValueError('Карта Карно поддерживается для 1-5 переменных')
        self.map, self.row_labels, self.col_labels, self.row_vars, self.col_vars, self.layer_var = self._build_map()

    @staticmethod
    def _gray_code(bits: int) -> List[str]:
        return [format(i ^ (i >> 1), f'0{bits}b') for i in range(1 << bits)]

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
                row = values[0]
                col = values[1]
                map_data[row][col] = res
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
            target = map0 if values[4] == 0 else map1
            target[row_labels.index(row_str)][col_labels.index(col_str)] = res
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

    def _find_rectangles_2d(self, data, rows, cols, row_labels, col_labels, row_var_names, col_var_names):
        ext_data = [[data[i % rows][j % cols] for j in range(cols * 2)] for i in range(rows * 2)]
        sizes = [(h, w) for h in (1, 2, 4, 8) if h <= rows for w in (1, 2, 4, 8) if w <= cols]
        rectangles = []
        for top in range(rows):
            for left in range(cols):
                for h, w in sizes:
                    ok = True
                    for i in range(top, top + h):
                        for j in range(left, left + w):
                            if ext_data[i][j] != 1:
                                ok = False
                                break
                        if not ok:
                            break
                    if ok:
                        rect_rows = [(top + i) % rows for i in range(h)]
                        rect_cols = [(left + j) % cols for j in range(w)]
                        rectangles.append((rect_rows, rect_cols))

        uniq = {}
        for rect_rows, rect_cols in rectangles:
            key = (tuple(sorted(set(rect_rows))), tuple(sorted(set(rect_cols))))
            uniq[key] = (list(key[0]), list(key[1]))
        rectangles = list(uniq.values())

        def is_subset(r1, r2):
            return set(r1[0]).issubset(r2[0]) and set(r1[1]).issubset(r2[1])

        maximal = []
        for i, rect in enumerate(rectangles):
            if any(i != j and is_subset(rect, other) for j, other in enumerate(rectangles)):
                continue
            maximal.append(rect)

        result = []
        for rect_rows, rect_cols in maximal:
            term_parts = []
            if len(set(rect_rows)) != rows:
                fixed = [None] * len(row_var_names)
                for r in rect_rows:
                    label = row_labels[r]
                    for idx, ch in enumerate(label):
                        if fixed[idx] is None:
                            fixed[idx] = ch
                        elif fixed[idx] != ch:
                            fixed[idx] = '-'
                for idx, var in enumerate(row_var_names):
                    if fixed[idx] != '-':
                        term_parts.append(var if fixed[idx] == '1' else f'!{var}')

            if len(set(rect_cols)) != cols:
                fixed = [None] * len(col_var_names)
                for c in rect_cols:
                    label = col_labels[c]
                    for idx, ch in enumerate(label):
                        if fixed[idx] is None:
                            fixed[idx] = ch
                        elif fixed[idx] != ch:
                            fixed[idx] = '-'
                for idx, var in enumerate(col_var_names):
                    if fixed[idx] != '-':
                        term_parts.append(var if fixed[idx] == '1' else f'!{var}')

            result.append((set(rect_rows), set(rect_cols), '&'.join(term_parts) if term_parts else '1'))
        return result

    @staticmethod
    def _literal_count_expr(term: str) -> int:
        return 0 if term == '1' else term.count('&') + 1

    def _select_exact_cover_terms(self, ones: Set[Tuple], covers: List[Tuple[Set[Tuple], str]]) -> List[str]:
        from collections import Counter

        if not ones:
            return []

        counter = Counter()
        for cover, _ in covers:
            counter.update(cover)

        essential_indices = []
        for idx, (cover, _) in enumerate(covers):
            if any(counter[cell] == 1 for cell in cover):
                essential_indices.append(idx)
        essential_indices = sorted(set(essential_indices))

        chosen_terms = [covers[idx][1] for idx in essential_indices]
        covered = set()
        for idx in essential_indices:
            covered.update(covers[idx][0])
        uncovered = ones - covered

        remaining_indices = [idx for idx in range(len(covers)) if idx not in essential_indices and covers[idx][0] & uncovered]
        best_terms: Optional[List[str]] = None
        best_score: Optional[Tuple[int, int]] = None

        def score(terms: Sequence[str]) -> Tuple[int, int]:
            return (len(terms), sum(self._literal_count_expr(term) for term in terms))

        def backtrack(current_terms: List[str], remaining_uncovered: Set[Tuple], candidate_indices: List[int]):
            nonlocal best_terms, best_score
            if not remaining_uncovered:
                total_terms = chosen_terms + current_terms
                current_score = score(total_terms)
                if best_score is None or current_score < best_score:
                    best_terms = total_terms[:]
                    best_score = current_score
                return
            if best_score is not None and len(chosen_terms) + len(current_terms) > best_score[0]:
                return

            options_per_cell = []
            for cell in remaining_uncovered:
                options = [idx for idx in candidate_indices if cell in covers[idx][0]]
                if not options:
                    return
                options_per_cell.append((len(options), cell, options))
            _, _, options = min(options_per_cell, key=lambda item: item[0])
            options.sort(key=lambda idx: (-len(covers[idx][0] & remaining_uncovered), self._literal_count_expr(covers[idx][1]), covers[idx][1]))

            for idx in options:
                current_terms.append(covers[idx][1])
                new_uncovered = remaining_uncovered - covers[idx][0]
                new_candidates = [other for other in candidate_indices if other > idx]
                backtrack(current_terms, new_uncovered, new_candidates)
                current_terms.pop()

        backtrack([], uncovered, sorted(remaining_indices))
        result = best_terms if best_terms is not None else chosen_terms
        unique = []
        for term in result:
            if term not in unique:
                unique.append(term)
        return unique

    def get_minimized(self) -> str:
        all_ones = all(res == 1 for _, res in self.rows_tt)
        all_zeros = all(res == 0 for _, res in self.rows_tt)
        if all_zeros:
            return '0'
        if all_ones:
            return '1'

        if self.n == 1:
            data = self.map[0]
            if data[0] == 1 and data[1] == 0:
                return f'!{self.col_vars[0]}'
            if data[0] == 0 and data[1] == 1:
                return self.col_vars[0]
            return '1'

        if self.n in (2, 3, 4):
            data = self.map
            rows = len(self.row_labels)
            cols = len(self.col_labels)
            rects = self._find_rectangles_2d(data, rows, cols, self.row_labels, self.col_labels, self.row_vars, self.col_vars)
            ones = {(i, j) for i in range(rows) for j in range(cols) if data[i][j] == 1}
            covers = []
            for row_set, col_set, term in rects:
                cover = {(r, c) for r in row_set for c in col_set if data[r][c] == 1}
                if cover:
                    covers.append((cover, term))
            chosen = self._select_exact_cover_terms(ones, covers)
            return ' | '.join(chosen) if chosen else '0'

        map0, map1 = self.map
        rows = len(self.row_labels)
        cols = len(self.col_labels)
        data3d = [map0, map1]
        ones = {(e, r, c) for e in range(2) for r in range(rows) for c in range(cols) if data3d[e][r][c] == 1}

        rectangles = []
        for e_h in (1, 2):
            for r_h in (1, 2, 4):
                for c_w in (1, 2, 4):
                    for e_start in range(2 - e_h + 1):
                        for r_start in range(rows):
                            for c_start in range(cols):
                                ok = True
                                for de in range(e_h):
                                    for dr in range(r_h):
                                        for dc in range(c_w):
                                            e = e_start + de
                                            r = (r_start + dr) % rows
                                            c = (c_start + dc) % cols
                                            if data3d[e][r][c] != 1:
                                                ok = False
                                                break
                                        if not ok:
                                            break
                                    if not ok:
                                        break
                                if ok:
                                    rectangles.append((
                                        tuple(range(e_start, e_start + e_h)),
                                        tuple((r_start + dr) % rows for dr in range(r_h)),
                                        tuple((c_start + dc) % cols for dc in range(c_w)),
                                    ))

        uniq = {}
        for e_range, r_range, c_range in rectangles:
            key = (tuple(sorted(set(e_range))), tuple(sorted(set(r_range))), tuple(sorted(set(c_range))))
            uniq[key] = key
        rectangles = list(uniq.values())

        def is_subset(r1, r2):
            return set(r1[0]).issubset(r2[0]) and set(r1[1]).issubset(r2[1]) and set(r1[2]).issubset(r2[2])

        maximal = []
        for i, rect in enumerate(rectangles):
            if any(i != j and is_subset(rect, other) for j, other in enumerate(rectangles)):
                continue
            maximal.append(rect)

        covers = []
        for e_range, r_range, c_range in maximal:
            parts = []
            if len(e_range) == 1:
                parts.append(self.layer_var if e_range[0] == 1 else f'!{self.layer_var}')

            if len(set(r_range)) != rows:
                fixed = [None, None]
                for r in r_range:
                    label = self.row_labels[r]
                    for idx, ch in enumerate(label):
                        if fixed[idx] is None:
                            fixed[idx] = ch
                        elif fixed[idx] != ch:
                            fixed[idx] = '-'
                for idx, var in enumerate(self.row_vars):
                    if fixed[idx] != '-':
                        parts.append(var if fixed[idx] == '1' else f'!{var}')

            if len(set(c_range)) != cols:
                fixed = [None, None]
                for c in c_range:
                    label = self.col_labels[c]
                    for idx, ch in enumerate(label):
                        if fixed[idx] is None:
                            fixed[idx] = ch
                        elif fixed[idx] != ch:
                            fixed[idx] = '-'
                for idx, var in enumerate(self.col_vars):
                    if fixed[idx] != '-':
                        parts.append(var if fixed[idx] == '1' else f'!{var}')

            term = '&'.join(parts) if parts else '1'
            cover = {(e, r, c) for e in e_range for r in r_range for c in c_range if data3d[e][r][c] == 1}
            if cover:
                covers.append((cover, term))

        chosen = self._select_exact_cover_terms(ones, covers)
        return ' | '.join(chosen) if chosen else '0'
