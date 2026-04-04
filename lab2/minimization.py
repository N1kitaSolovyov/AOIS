# minimization.py
from typing import List, Set, Dict, Tuple, Optional
from boolean_core import BooleanFunction
from truth_table import TruthTable


class QuineMcCluskey:
    """Расчётный и расчётно-табличный методы минимизации (пункты 10 и 11)"""

    def __init__(self, func: BooleanFunction):
        self.func = func
        self.vars = func.get_variables()
        self.tt = TruthTable(func)
        self.rows = self.tt.get_rows()
        # Собираем все наборы, где функция = 1, в виде строки битов
        self.ones = [''.join(str(b) for b in vals) for vals, res in self.rows if res == 1]
        # Если функция всюду 0, то минимизация не имеет смысла
        self.is_zero = len(self.ones) == 0
        # Если функция всюду 1, то ДНФ = 1
        self.is_one = len(self.ones) == (1 << len(self.vars))

    # ----------------------------------------------------------------------
    # Вспомогательные методы для этапа склеивания
    # ----------------------------------------------------------------------
    @staticmethod
    def _count_ones(term: str) -> int:
        return term.count('1')

    @staticmethod
    def _is_adjacent(t1: str, t2: str) -> bool:
        diff = 0
        for c1, c2 in zip(t1, t2):
            if c1 != c2:
                diff += 1
                if diff > 1:
                    return False
        return diff == 1

    @staticmethod
    def _combine(t1: str, t2: str) -> str:
        return ''.join(c1 if c1 == c2 else '-' for c1, c2 in zip(t1, t2))

    def _get_prime_implicants_with_stages(self) -> Tuple[List[str], List[str]]:
        """
        Возвращает (список простых импликант, список строк с этапами склеивания).
        Этапы включают группы термов и результаты склеиваний.
        """
        if self.is_zero:
            return [], ["Функция тождественно равна 0, минимизация не требуется."]
        if self.is_one:
            return ["1"], ["Функция тождественно равна 1, минимизация не требуется."]

        # Группировка по количеству единиц
        from collections import defaultdict
        groups = defaultdict(list)
        for term in self.ones:
            groups[self._count_ones(term)].append(term)

        stages = []          # текстовое описание этапов
        prime_implicants = set()
        used = set()         # помечаем термы, которые были склеены
        stage_num = 1

        while groups:
            # Запоминаем текущие группы
            stage_lines = [f"Этап {stage_num}:"]
            for k in sorted(groups.keys()):
                stage_lines.append(f"  {k} единиц: {groups[k]}")
            stages.append("\n".join(stage_lines))

            new_groups = defaultdict(list)
            used_this_pass = set()
            # Склеиваем соседние по количеству единиц
            for k in sorted(groups.keys()):
                if k + 1 not in groups:
                    continue
                for t1 in groups[k]:
                    for t2 in groups[k + 1]:
                        if self._is_adjacent(t1, t2):
                            new_term = self._combine(t1, t2)
                            # Новая импликанта имеет количество единиц = количество единиц в t1 (после замены '-' на 0)
                            cnt = self._count_ones(new_term.replace('-', '0'))
                            new_groups[cnt].append(new_term)
                            used_this_pass.add(t1)
                            used_this_pass.add(t2)
                            # Для отладочного вывода можно добавить пару
                            # stages.append(f"    {t1} + {t2} -> {new_term}")
            # Неиспользованные термы становятся простыми импликантами
            for k in groups:
                for term in groups[k]:
                    if term not in used_this_pass:
                        prime_implicants.add(term)
            used.update(used_this_pass)
            groups = new_groups
            stage_num += 1

        # Убираем лишние импликанты (например, если одна импликанта поглощает другую)
        prime_list = list(prime_implicants)
        # Сортировка для детерминированного вывода
        prime_list.sort(key=lambda x: (len(x.replace('-', '')), x))
        return prime_list, stages

    # ----------------------------------------------------------------------
    # Расчётный метод (пункт 10) – с удалением лишних импликант
    # ----------------------------------------------------------------------
    def minimize_calculated(self) -> str:
        """Расчётный метод: вывод этапов склеивания и минимальная ДНФ."""
        if self.is_zero:
            print("Функция тождественно равна 0")
            return "0"
        if self.is_one:
            print("Функция тождественно равна 1")
            return "1"

        implicants, stages = self._get_prime_implicants_with_stages()
        for s in stages:
            print(s)
        print("\nПростые импликанты:", implicants)

        # Построение покрытия и удаление лишних импликант
        def covers(imp: str) -> Set[int]:
            """Множество индексов конституент, покрываемых импликантой"""
            indices = set()
            for i, term in enumerate(self.ones):
                if all(imp[j] == '-' or imp[j] == term[j] for j in range(len(imp))):
                    indices.add(i)
            return indices

        imp_covers = {imp: covers(imp) for imp in implicants}
        all_indices = set(range(len(self.ones)))

        # Находим ядро (импликанты, покрывающие уникальные конституенты)
        from collections import Counter
        cnt = Counter()
        for cov in imp_covers.values():
            cnt.update(cov)
        essential = set()
        for imp, cov in imp_covers.items():
            if any(cnt[idx] == 1 for idx in cov):
                essential.add(imp)

        # Жадное покрытие остальных
        covered = set()
        for imp in essential:
            covered.update(imp_covers[imp])
        remaining = [imp for imp in implicants if imp not in essential]
        # Сортируем по размеру покрытия (по убыванию)
        remaining.sort(key=lambda x: len(imp_covers[x]), reverse=True)
        chosen = list(essential)
        for imp in remaining:
            if covered.issuperset(all_indices):
                break
            if not imp_covers[imp].issubset(covered):
                chosen.append(imp)
                covered.update(imp_covers[imp])

        # Преобразование в ДНФ
        result_terms = []
        for imp in chosen:
            term_parts = []
            for var, ch in zip(self.vars, imp):
                if ch == '0':
                    term_parts.append(f"!{var}")
                elif ch == '1':
                    term_parts.append(var)
            result_terms.append("&".join(term_parts))
        min_dnf = " | ".join(result_terms)
        print("\nРезультат минимизации (расчётный метод):", min_dnf)
        return min_dnf

    # ----------------------------------------------------------------------
    # Расчётно-табличный метод (пункт 11) – с выводом таблицы покрытия
    # ----------------------------------------------------------------------
    def minimize_tabular(self) -> str:
        """Расчётно-табличный метод: этапы склеивания + таблица покрытия + минимизация."""
        if self.is_zero:
            print("Функция тождественно равна 0")
            return "0"
        if self.is_one:
            print("Функция тождественно равна 1")
            return "1"

        implicants, stages = self._get_prime_implicants_with_stages()
        for s in stages:
            print(s)

        # Построение таблицы покрытия
        def covers(imp: str) -> Set[int]:
            indices = set()
            for i, term in enumerate(self.ones):
                if all(imp[j] == '-' or imp[j] == term[j] for j in range(len(imp))):
                    indices.add(i)
            return indices

        imp_covers = {imp: covers(imp) for imp in implicants}
        term_indices = list(range(len(self.ones)))

        # Вывод таблицы
        print("\nТаблица покрытия (импликанта -> покрываемые конституенты):")
        # Заголовок
        header = "Импликанта | " + " ".join(f"K{i}" for i in term_indices)
        print(header)
        print("-" * len(header))
        for imp in implicants:
            cov = imp_covers[imp]
            row = f"{imp:10} | " + " ".join("X" if i in cov else "." for i in term_indices)
            print(row)

        # Минимизация (ядро + жадный алгоритм, как выше)
        all_indices = set(term_indices)
        from collections import Counter
        cnt = Counter()
        for cov in imp_covers.values():
            cnt.update(cov)
        essential = set()
        for imp, cov in imp_covers.items():
            if any(cnt[idx] == 1 for idx in cov):
                essential.add(imp)

        covered = set()
        for imp in essential:
            covered.update(imp_covers[imp])
        remaining = [imp for imp in implicants if imp not in essential]
        remaining.sort(key=lambda x: len(imp_covers[x]), reverse=True)
        chosen = list(essential)
        for imp in remaining:
            if covered.issuperset(all_indices):
                break
            if not imp_covers[imp].issubset(covered):
                chosen.append(imp)
                covered.update(imp_covers[imp])

        # Преобразование в ДНФ
        result_terms = []
        for imp in chosen:
            term_parts = []
            for var, ch in zip(self.vars, imp):
                if ch == '0':
                    term_parts.append(f"!{var}")
                elif ch == '1':
                    term_parts.append(var)
            result_terms.append("&".join(term_parts))
        min_dnf = " | ".join(result_terms)
        print("\nРезультат минимизации (расчётно-табличный метод):", min_dnf)
        return min_dnf


class KarnaughMap:
    """Минимизация картой Карно для 1-5 переменных"""

    def __init__(self, func: BooleanFunction):
        self.func = func
        self.vars = func.get_variables()
        self.tt = TruthTable(func)
        self.rows_tt = self.tt.get_rows()
        self.n = len(self.vars)
        if self.n < 1 or self.n > 5:
            raise ValueError("Карта Карно поддерживается для 1-5 переменных")
        self.map, self.row_labels, self.col_labels = self._build_map()

    @staticmethod
    def _gray_code(bits: int) -> List[str]:
        res = []
        for i in range(1 << bits):
            gray = i ^ (i >> 1)
            res.append(format(gray, f'0{bits}b'))
        return res

    def _build_map(self):
        # n = 1 : одна переменная a -> карта 1x2 (строка a, столбцы 0 и 1)
        if self.n == 1:
            a_var = self.vars[0]
            row_labels = ['0']  # только одна строка, значение a
            # столбцы: просто 0 и 1, без кода Грея (но можно и Gray, но для 1 бита Gray = 0,1)
            col_labels = ['0', '1']
            map_data = [[0, 0]]
            for values, res in self.rows_tt:
                a_val = values[0]
                map_data[0][a_val] = res
            return map_data, row_labels, col_labels

        # n = 2 : переменные a,b -> карта 2x2, строки a, столбцы b (порядок 0,1)
        if self.n == 2:
            row_labels = ['0', '1']   # a
            col_labels = ['0', '1']   # b
            map_data = [[0, 0], [0, 0]]
            a_idx = self.vars.index('a')
            b_idx = self.vars.index('b')
            for values, res in self.rows_tt:
                a_val = values[a_idx]
                b_val = values[b_idx]
                map_data[a_val][b_val] = res
            return map_data, row_labels, col_labels

        # n = 3 (как было)
        if self.n == 3:
            a_idx = self.vars.index('a')
            bc_vars = [v for v in self.vars if v != 'a']
            bc_vars.sort()
            row_labels = ['0', '1']
            col_labels = self._gray_code(2)
            map_data = [[0]*4 for _ in range(2)]
            for values, res in self.rows_tt:
                a_val = values[a_idx]
                bc_vals = [values[self.vars.index(v)] for v in bc_vars]
                bc_str = ''.join(str(x) for x in bc_vals)
                col = col_labels.index(bc_str)
                map_data[a_val][col] = res
            return map_data, row_labels, col_labels

        # n = 4 (как было)
        if self.n == 4:
            row_vars = self.vars[:2]
            col_vars = self.vars[2:]
            row_labels = self._gray_code(2)
            col_labels = self._gray_code(2)
            map_data = [[0]*4 for _ in range(4)]
            for values, res in self.rows_tt:
                row_vals = [values[self.vars.index(v)] for v in row_vars]
                row_str = ''.join(str(x) for x in row_vals)
                row = row_labels.index(row_str)
                col_vals = [values[self.vars.index(v)] for v in col_vars]
                col_str = ''.join(str(x) for x in col_vals)
                col = col_labels.index(col_str)
                map_data[row][col] = res
            return map_data, row_labels, col_labels

        # n = 5 (как было)
        # n == 5
        row_vars = self.vars[:2]
        col_vars = self.vars[2:4]
        e_var = self.vars[4]
        row_labels = self._gray_code(2)
        col_labels = self._gray_code(2)
        map0 = [[0]*4 for _ in range(4)]
        map1 = [[0]*4 for _ in range(4)]
        for values, res in self.rows_tt:
            e_val = values[self.vars.index(e_var)]
            row_vals = [values[self.vars.index(v)] for v in row_vars]
            row_str = ''.join(str(x) for x in row_vals)
            row = row_labels.index(row_str)
            col_vals = [values[self.vars.index(v)] for v in col_vars]
            col_str = ''.join(str(x) for x in col_vals)
            col = col_labels.index(col_str)
            if e_val == 0:
                map0[row][col] = res
            else:
                map1[row][col] = res
        return (map0, map1), row_labels, col_labels

    def display(self):
        print("\nКарта Карно:")
        if self.n == 1:
            print("   a: 0 1")
            print("    " + " ".join(str(self.map[0][j]) for j in range(2)))
        elif self.n == 2:
            print("   b: 0 1")
            for i in range(2):
                print(f"a={self.row_labels[i]}  {self.map[i][0]} {self.map[i][1]}")
        elif self.n == 3:
            print("   bc: 00 01 11 10")
            for i in range(2):
                print(f"a={self.row_labels[i]}  ", end="")
                for j in range(4):
                    print(f"{self.map[i][j]} ", end="")
                print()
        elif self.n == 4:
            print("   cd: " + " ".join(self.col_labels))
            for i, row_label in enumerate(self.row_labels):
                print(f"ab={row_label} ", end="")
                for j in range(4):
                    print(f"{self.map[i][j]} ", end="")
                print()
        else:  # n == 5
            map0, map1 = self.map
            print("Для e=0:")
            print("   cd: " + " ".join(self.col_labels))
            for i, row_label in enumerate(self.row_labels):
                print(f"ab={row_label} ", end="")
                for j in range(4):
                    print(f"{map0[i][j]} ", end="")
                print()
            print("\nДля e=1:")
            print("   cd: " + " ".join(self.col_labels))
            for i, row_label in enumerate(self.row_labels):
                print(f"ab={row_label} ", end="")
                for j in range(4):
                    print(f"{map1[i][j]} ", end="")
                print()

    # ------------------------------------------------------------------
    # Поиск прямоугольников для 2D карты (с учётом цикличности)
    # ------------------------------------------------------------------
    def _find_rectangles_2d(self, data, rows, cols, row_labels, col_labels,
                            row_var_names, col_var_names):
        """
        Возвращает список кортежей: (множество_строк, множество_столбцов, строка_терма)
        """
        # Расширяем карту для учёта цикличности
        ext_data = [[0]*(cols*2) for _ in range(rows*2)]
        for i in range(rows*2):
            for j in range(cols*2):
                ext_data[i][j] = data[i % rows][j % cols]

        # Все возможные размеры (степени двойки)
        sizes = []
        max_h = 1
        while max_h * 2 <= rows:
            max_h *= 2
        max_w = 1
        while max_w * 2 <= cols:
            max_w *= 2
        for h in (1, 2, 4, 8):
            if h <= rows and h <= max_h:
                for w in (1, 2, 4, 8):
                    if w <= cols and w <= max_w:
                        sizes.append((h, w))

        rectangles = []  # (список строк, список столбцов)
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

        # Удаление дубликатов
        uniq = {}
        for rrows, rcols in rectangles:
            key = (tuple(sorted(rrows)), tuple(sorted(rcols)))
            uniq[key] = (rrows, rcols)
        rectangles = list(uniq.values())

        # Оставляем только максимальные
        def is_subset(r1, r2):
            return set(r1[0]).issubset(set(r2[0])) and set(r1[1]).issubset(set(r2[1]))

        maximal = []
        for i, rect in enumerate(rectangles):
            is_max = True
            for j, other in enumerate(rectangles):
                if i != j and is_subset(rect, other):
                    is_max = False
                    break
            if is_max:
                maximal.append(rect)

        # Преобразуем в термы
        result = []
        for rect_rows, rect_cols in maximal:
            term_parts = []

            # Обработка строк
            row_set = set(rect_rows)
            if len(row_set) == rows:   # занимает все строки → переменные строк выпадают
                pass
            else:
                fixed = [None] * len(row_var_names)
                for r in row_set:
                    label = row_labels[r]
                    for idx, ch in enumerate(label):
                        if fixed[idx] is None:
                            fixed[idx] = ch
                        elif fixed[idx] != ch:
                            fixed[idx] = '-'
                for idx, var in enumerate(row_var_names):
                    if fixed[idx] != '-':
                        term_parts.append(var if fixed[idx] == '1' else f"!{var}")

            # Обработка столбцов
            col_set = set(rect_cols)
            if len(col_set) == cols:   # занимает все столбцы → переменные столбцов выпадают
                pass
            else:
                fixed = [None] * len(col_var_names)
                for c in col_set:
                    label = col_labels[c]
                    for idx, ch in enumerate(label):
                        if fixed[idx] is None:
                            fixed[idx] = ch
                        elif fixed[idx] != ch:
                            fixed[idx] = '-'
                for idx, var in enumerate(col_var_names):
                    if fixed[idx] != '-':
                        term_parts.append(var if fixed[idx] == '1' else f"!{var}")

            term = "&".join(term_parts) if term_parts else "1"
            result.append((set(rect_rows), set(rect_cols), term))

        return result

    # ------------------------------------------------------------------
    # Покрытие единиц (ядро + жадный алгоритм)
    # ------------------------------------------------------------------
    def _cover_ones(self, ones, rect_covers):
        from collections import Counter
        covered = set()
        chosen_terms = []
        rc = [(cover.copy(), term) for cover, term in rect_covers]

        while rc and covered != ones:
            cnt = Counter()
            for cover, _ in rc:
                cnt.update(cover)

            essential = None
            for cover, term in rc:
                for cell in cover:
                    if cnt[cell] == 1:
                        essential = (cover, term)
                        break
                if essential:
                    break

            if essential:
                chosen_terms.append(essential[1])
                covered.update(essential[0])
                new_rc = []
                for cover, term in rc:
                    if cover is essential[0]:
                        continue
                    new_cover = cover - covered
                    if new_cover:
                        new_rc.append((new_cover, term))
                rc = new_rc
            else:
                rc.sort(key=lambda x: len(x[0]), reverse=True)
                best_cover, best_term = rc[0]
                chosen_terms.append(best_term)
                covered.update(best_cover)
                rc = [(cover - covered, term) for cover, term in rc[1:] if cover - covered]

        # Убираем дубликаты
        unique = []
        for t in chosen_terms:
            if t not in unique:
                unique.append(t)
        return unique

    # ------------------------------------------------------------------
    # Главный метод минимизации
    # ------------------------------------------------------------------
    def get_minimized(self) -> str:
        # Проверка на константы
        all_ones = all(res == 1 for _, res in self.rows_tt)
        all_zeros = all(res == 0 for _, res in self.rows_tt)
        if all_zeros:
            return "0"
        if all_ones:
            return "1"

        # Для 1 переменной
        if self.n == 1:
            data = self.map[0]  # список из 2 элементов
            # Просто проверяем возможные импликанты: 1, a, !a
            if data[0] == 1 and data[1] == 1:
                return "1"
            if data[0] == 1 and data[1] == 0:
                return f"!{self.vars[0]}"
            if data[0] == 0 and data[1] == 1:
                return self.vars[0]
            return "0"

        # Для 2 переменных
        if self.n == 2:
            data = self.map
            rows, cols = 2, 2
            row_var_names = [self.vars[0]]
            col_var_names = [self.vars[1]]
            # Используем общий поиск прямоугольников (2x2 с цикличностью)
            rects = self._find_rectangles_2d(data, rows, cols,
                                             self.row_labels, self.col_labels,
                                             row_var_names, col_var_names)
            ones = {(i, j) for i in range(rows) for j in range(cols) if data[i][j] == 1}
            rect_covers = []
            for rset, cset, term in rects:
                cover = {(r, c) for r in rset for c in cset if data[r][c] == 1}
                if cover:
                    rect_covers.append((cover, term))
            chosen = self._cover_ones(ones, rect_covers)
            return " | ".join(chosen) if chosen else "0"

        # Для 3,4 переменных (как было)
        if self.n == 3:
            data = self.map
            rows, cols = 2, 4
            row_var_names = [self.vars[0]]
            col_var_names = [self.vars[1], self.vars[2]]
            rects = self._find_rectangles_2d(data, rows, cols,
                                             self.row_labels, self.col_labels,
                                             row_var_names, col_var_names)
            ones = {(i, j) for i in range(rows) for j in range(cols) if data[i][j] == 1}
            rect_covers = []
            for rset, cset, term in rects:
                cover = {(r, c) for r in rset for c in cset if data[r][c] == 1}
                if cover:
                    rect_covers.append((cover, term))
            chosen = self._cover_ones(ones, rect_covers)
            return " | ".join(chosen) if chosen else "0"

        if self.n == 4:
            data = self.map
            rows, cols = 4, 4
            row_var_names = [self.vars[0], self.vars[1]]
            col_var_names = [self.vars[2], self.vars[3]]
            rects = self._find_rectangles_2d(data, rows, cols,
                                             self.row_labels, self.col_labels,
                                             row_var_names, col_var_names)
            ones = {(i, j) for i in range(rows) for j in range(cols) if data[i][j] == 1}
            rect_covers = []
            for rset, cset, term in rects:
                cover = {(r, c) for r in rset for c in cset if data[r][c] == 1}
                if cover:
                    rect_covers.append((cover, term))
            chosen = self._cover_ones(ones, rect_covers)
            return " | ".join(chosen) if chosen else "0"

        # n == 5
        map0, map1 = self.map
        rows, cols = 4, 4
        row_var_names = [self.vars[0], self.vars[1]]
        col_var_names = [self.vars[2], self.vars[3]]
        e_var = self.vars[4]
        data3d = [map0, map1]

        ones = set()
        for e in range(2):
            for r in range(rows):
                for c in range(cols):
                    if data3d[e][r][c] == 1:
                        ones.add((e, r, c))

        e_sizes = [1, 2]
        r_sizes = [1, 2, 4]
        c_sizes = [1, 2, 4]

        rectangles = []  # (e_range, r_range, c_range)
        for e_h in e_sizes:
            for r_h in r_sizes:
                for c_w in c_sizes:
                    for e_start in range(2 - e_h + 1):
                        for r_start in range(rows):
                            for c_start in range(cols):
                                ok = True
                                for de in range(e_h):
                                    e = e_start + de
                                    for dr in range(r_h):
                                        r = (r_start + dr) % rows
                                        for dc in range(c_w):
                                            c = (c_start + dc) % cols
                                            if data3d[e][r][c] != 1:
                                                ok = False
                                                break
                                        if not ok:
                                            break
                                    if not ok:
                                        break
                                if ok:
                                    e_range = tuple(range(e_start, e_start + e_h))
                                    r_range = tuple((r_start + dr) % rows for dr in range(r_h))
                                    c_range = tuple((c_start + dc) % cols for dc in range(c_w))
                                    rectangles.append((e_range, r_range, c_range))

        uniq = {}
        for e_range, r_range, c_range in rectangles:
            key = (tuple(sorted(e_range)), tuple(sorted(r_range)), tuple(sorted(c_range)))
            uniq[key] = (e_range, r_range, c_range)
        rectangles = list(uniq.values())

        def is_subset5(r1, r2):
            return (set(r1[0]).issubset(set(r2[0])) and
                    set(r1[1]).issubset(set(r2[1])) and
                    set(r1[2]).issubset(set(r2[2])))

        maximal = []
        for i, rect in enumerate(rectangles):
            is_max = True
            for j, other in enumerate(rectangles):
                if i != j and is_subset5(rect, other):
                    is_max = False
                    break
            if is_max:
                maximal.append(rect)

        rect_covers = []
        for e_range, r_range, c_range in maximal:
            term_parts = []
            if len(e_range) == 1:
                e_val = e_range[0]
                term_parts.append(e_var if e_val == 1 else f"!{e_var}")
            # строки
            if len(set(r_range)) == rows:
                pass
            else:
                fixed = [None, None]
                for r in r_range:
                    label = self.row_labels[r]
                    for idx in range(2):
                        if fixed[idx] is None:
                            fixed[idx] = label[idx]
                        elif fixed[idx] != label[idx]:
                            fixed[idx] = '-'
                for idx, var in enumerate(row_var_names):
                    if fixed[idx] != '-':
                        term_parts.append(var if fixed[idx] == '1' else f"!{var}")
            # столбцы
            if len(set(c_range)) == cols:
                pass
            else:
                fixed = [None, None]
                for c in c_range:
                    label = self.col_labels[c]
                    for idx in range(2):
                        if fixed[idx] is None:
                            fixed[idx] = label[idx]
                        elif fixed[idx] != label[idx]:
                            fixed[idx] = '-'
                for idx, var in enumerate(col_var_names):
                    if fixed[idx] != '-':
                        term_parts.append(var if fixed[idx] == '1' else f"!{var}")

            term = "&".join(term_parts) if term_parts else "1"
            cover = set()
            for e in e_range:
                for r in r_range:
                    for c in c_range:
                        if data3d[e][r][c] == 1:
                            cover.add((e, r, c))
            if cover:
                rect_covers.append((cover, term))

        chosen = self._cover_ones(ones, rect_covers)
        return " | ".join(chosen) if chosen else "0"