from itertools import combinations
from boolean_core import BooleanFunction
from truth_table import TruthTable
from normal_forms import NormalFormsBuilder
from post_classes import PostClasses
from derivative import BooleanDerivative, DummyVariableFinder
from minimization import QuineMcCluskey, KarnaughMap


def print_separator(title: str):
    print('\n' + '=' * 80)
    print(f' {title}')
    print('=' * 80)


def main():
    print('Лабораторная работа 2: булевы функции, нормальные формы и минимизация')
    print('Допустимые переменные: a, b, c, d, e (до 5)')
    print('Операции: & (И), | (ИЛИ), ! (НЕ), -> (импликация), ~ (эквивалентность)')
    print('Поддерживаются и Unicode-аналоги: ¬ ∧ ∨ → ↔')
    print('Пример: !(!a->!b)|c   или   ¬(¬a→¬b)∨c')

    expr = input('\nВведите логическую функцию: ').strip()
    if not expr:
        print('Ошибка: пустое выражение')
        return

    try:
        func = BooleanFunction(expr)
    except ValueError as error:
        print(f'Ошибка в формуле: {error}')
        return

    print_separator('1. Таблица истинности')
    tt = TruthTable(func)
    tt.display()

    print_separator('2. СДНФ')
    nf = NormalFormsBuilder(func)
    print(f'СДНФ: {nf.get_sdnf()}')

    print_separator('3. СКНФ')
    print(f'СКНФ: {nf.get_sknf()}')

    print_separator('4. Числовая форма')
    print(f'Числовая форма СДНФ: {nf.get_numeric_sdnf()}')
    print(f'Числовая форма СКНФ: {nf.get_numeric_sknf()}')

    print_separator('5. Индексная форма')
    print(f'Двоичный вектор значений: {nf.get_index_binary()}')
    print(f'Индексная форма (десятичная): {nf.get_index_form()}')

    print_separator('6. Классы Поста')
    post = PostClasses(func)
    print(f'T0 (сохранение 0): {post.is_T0()}')
    print(f'T1 (сохранение 1): {post.is_T1()}')
    print(f'S (самодвойственность): {post.is_S()}')
    print(f'M (монотонность): {post.is_M()}')
    print(f'L (линейность): {post.is_L()}')

    print_separator('7. Полином Жегалкина')
    print(f'Полином Жегалкина: {post.get_zhegalkin_polynomial()}')

    print_separator('8. Фиктивные переменные')
    dummy_finder = DummyVariableFinder(func)
    dummy_vars = dummy_finder.find_dummy_variables()
    print('Фиктивные переменные: ' + (', '.join(dummy_vars) if dummy_vars else 'отсутствуют'))

    print_separator('9. Булева дифференциация')
    if func.get_variables():
        deriv = BooleanDerivative(func)
        max_order = min(4, len(func.get_variables()))
        for order in range(1, max_order + 1):
            title = 'Частные производные' if order == 1 else f'Смешанные производные {order}-го порядка'
            print('\n' + title + ':')
            for vars_group in combinations(func.get_variables(), order):
                print(deriv.format_report(deriv.derivative_report(vars_group)))
                print()
    else:
        print('Для константной функции производные по переменным отсутствуют.')

    print_separator('10. Минимизация расчётным методом')
    qm = QuineMcCluskey(func)
    min_calc = qm.minimize_calculated()
    print(f'\nМинимальная ДНФ (расчётный метод): {min_calc}')

    print_separator('11. Минимизация расчётно-табличным методом')
    min_tab = qm.minimize_tabular()
    print(f'\nМинимальная ДНФ (расчётно-табличный метод): {min_tab}')

    print_separator('12. Минимизация табличным методом (карта Карно)')
    if not func.get_variables():
        print('Для чисто константной функции карта Карно не строится.')
    else:
        try:
            km = KarnaughMap(func)
            km.display()
            min_kmap = km.get_minimized()
            print(f'\nМинимальная ДНФ (карта Карно): {min_kmap}')
        except ValueError as error:
            print(f'Ошибка при построении карты Карно: {error}')

    print('\n' + '=' * 80)
    print('Работа программы завершена.')


if __name__ == '__main__':
    main()
