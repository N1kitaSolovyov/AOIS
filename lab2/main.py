# main.py
import sys
from boolean_core import BooleanFunction
from truth_table import TruthTable
from normal_forms import NormalFormsBuilder
from post_classes import PostClasses
from derivative import BooleanDerivative, DummyVariableFinder
from minimization import QuineMcCluskey, KarnaughMap

def print_separator(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def main():
    print("Лабораторная работа 2: Построение СКНФ, СДНФ, минимизация и анализ булевых функций")
    print("Допустимые переменные: a, b, c, d, e (до 5)")
    print("Операции: & (И), | (ИЛИ), ! (НЕ), -> (импликация), ~ (эквивалентность)")
    print("Пример: !(!a->!b)|c")

    expr = input("\nВведите логическую функцию: ").strip()
    if not expr:
        print("Ошибка: пустое выражение")
        return

    try:
        func = BooleanFunction(expr)
    except ValueError as e:
        print(f"Ошибка в формуле: {e}")
        return

    # 1. Таблица истинности
    print_separator("1. Таблица истинности")
    tt = TruthTable(func)
    tt.display()

    # 2. СДНФ
    print_separator("2. СДНФ")
    nf = NormalFormsBuilder(func)
    print(f"СДНФ: {nf.get_sdnf()}")

    # 3. СКНФ
    print_separator("3. СКНФ")
    print(f"СКНФ: {nf.get_sknf()}")

    # 4. Числовая форма СДНФ и СКНФ
    print_separator("4. Числовая форма")
    print(f"Числовая форма СДНФ: {nf.get_numeric_sdnf()}")
    print(f"Числовая форма СКНФ: {nf.get_numeric_sknf()}")

    # 5. Индексная форма
    print_separator("5. Индексная форма")
    print(f"Индексная форма (десятичная): {nf.get_index_form()}")

    # 6. Классы Поста
    print_separator("6. Классы Поста")
    post = PostClasses(func)
    print(f"T0 (сохранение 0): {post.is_T0()}")
    print(f"T1 (сохранение 1): {post.is_T1()}")
    print(f"S (самодвойственность): {post.is_S()}")
    print(f"M (монотонность): {post.is_M()}")
    print(f"L (линейность): {post.is_L()}")

    # 7. Полином Жегалкина
    print_separator("7. Полином Жегалкина")
    print(f"Полином Жегалкина: {post.get_zhegalkin_polynomial()}")

    # 8. Фиктивные переменные
    print_separator("8. Фиктивные переменные")
    dummy_finder = DummyVariableFinder(func)
    dummy_vars = dummy_finder.find_dummy_variables()
    if dummy_vars:
        print(f"Фиктивные переменные: {', '.join(dummy_vars)}")
    else:
        print("Фиктивные переменные отсутствуют")

    # 9. Булева дифференциация
    print_separator("9. Булева дифференциация")
    deriv = BooleanDerivative(func)
    print("Частные производные:")
    for var in func.get_variables():
        part = deriv.partial_derivative(var)
        print(f"  ∂f/∂{var} = {part}")
    if len(func.get_variables()) >= 2:
        mixed_vars = func.get_variables()[:2]
        mixed = deriv.mixed_derivative(mixed_vars)
        print(f"Смешанная производная (по {mixed_vars[0]} и {mixed_vars[1]}): {mixed}")
    else:
        print("Смешанная производная требует не менее 2 переменных")

    # 10. Минимизация расчётным методом (Квайн-Мак-Класки)
    print_separator("10. Минимизация расчётным методом (Квайн-Мак-Класки)")
    qm = QuineMcCluskey(func)
    min_calc = qm.minimize_calculated()
    print(f"\nМинимальная ДНФ (расчётный метод): {min_calc}")

    # 11. Минимизация расчётно-табличным методом
    print_separator("11. Минимизация расчётно-табличным методом")
    min_tab = qm.minimize_tabular()
    print(f"\nМинимальная ДНФ (расчётно-табличный метод): {min_tab}")

    # 12. Минимизация картой Карно
    print_separator("12. Минимизация картой Карно")
    if len(func.get_variables()) not in (1, 2, 3, 4, 5):
        print("Карта Карно поддерживается только для 1-5 переменных. Пропуск.")
    else:
        try:
            km = KarnaughMap(func)
            km.display()
            min_kmap = km.get_minimized()
            print(f"\nМинимальная ДНФ (карта Карно): {min_kmap}")
        except ValueError as e:
            print(f"Ошибка при построении карты Карно: {e}")

    print("\n" + "=" * 70)
    print("Работа программы завершена.")

if __name__ == "__main__":
    main()