# main.py
from binary_codes import BinaryCodeConverter
from additional_arithmetic import AdditionalArithmetic
from direct_arithmetic import DirectMultiplier, DirectDivider
from ieee754 import IEEE754Binary32
from bcd import (
     BCD2421, BCDAdder
)

def print_bits(bits: list, title: str = ""):
    if title:
        print(title)
    # разбиваем по 8 бит для читаемости
    s = ''
    for i in range(0, len(bits), 8):
        s += ' ' + ''.join(str(b) for b in bits[i:i+8])
    print(s.strip())

def main():
    print("=" * 50)
    print("Лабораторная работа №1 (исправленная версия)")
    print("=" * 50)
    while True:
        print("\nВыберите пункт:")
        print("1 - Перевод в прямой/обратный/дополнительный код")
        print("2 - Сложение в дополнительном коде")
        print("3 - Вычитание в дополнительном коде")
        print("4 - Умножение в прямом коде")
        print("5 - Деление в прямом коде (точность 5 знаков)")
        print("6 - Операции IEEE-754 binary32 (+, -, *, /)")
        print("7 - Сложение в BCD-коде")
        print("0 - Выход")
        choice = input("Ваш выбор: ").strip()

        if choice == '0':
            break

        elif choice == '1':
            try:
                num = int(input("Введите целое число: "))
            except:
                print("Ошибка ввода")
                continue
            conv = BinaryCodeConverter(num)
            print("\nПрямой код:")
            print_bits(conv.direct_code())
            print("Десятичное (из прямого):", conv.from_direct_to_decimal(conv.direct_code()))
            print("Обратный код:")
            print_bits(conv.inverse_code())
            print("Десятичное (из обратного):", conv.from_inverse_to_decimal(conv.inverse_code()))
            print("Дополнительный код:")
            print_bits(conv.additional_code())
            print("Десятичное (из дополнительного):", conv.from_additional_to_decimal(conv.additional_code()))

        elif choice == '2':
            try:
                a = int(input("Введите первое число: "))
                b = int(input("Введите второе число: "))
            except:
                print("Ошибка ввода")
                continue
            bits, dec = AdditionalArithmetic.add(a, b)
            print("\nРезультат сложения в дополнительном коде:")
            print_bits(bits)
            print("Десятичное значение:", dec)

        elif choice == '3':
            try:
                a = int(input("Введите уменьшаемое: "))
                b = int(input("Введите вычитаемое: "))
            except:
                print("Ошибка ввода")
                continue
            bits, dec = AdditionalArithmetic.subtract(a, b)
            print("\nРезультат вычитания в дополнительном коде:")
            print_bits(bits)
            print("Десятичное значение:", dec)

        elif choice == '4':
            try:
                a = int(input("Введите первый множитель: "))
                b = int(input("Введите второй множитель: "))
            except:
                print("Ошибка ввода")
                continue
            bits, dec = DirectMultiplier.multiply(a, b)
            print("\nРезультат умножения в прямом коде:")
            print_bits(bits)
            print("Десятичное значение:", dec)

        elif choice == '5':
            try:
                a = int(input("Введите делимое: "))
                b = int(input("Введите делитель: "))
            except:
                print("Ошибка ввода")
                continue
            try:
                bits, dec = DirectDivider.divide(a, b)
            except ZeroDivisionError as e:
                print(e)
                continue
            print("\nРезультат деления в прямом коде:")
            print_bits(bits)
            print(f"Десятичное значение: {dec:.5f}")

        elif choice == '6':
            try:
                x = float(input("Введите первое число (десятичное): "))
                y = float(input("Введите второе число (десятичное): "))
                op = input("Операция (+, -, *, /): ").strip()
            except:
                print("Ошибка ввода")
                continue
            a_bits = IEEE754Binary32.from_float(x)
            b_bits = IEEE754Binary32.from_float(y)
            if op == '+':
                res_bits = IEEE754Binary32.add(a_bits, b_bits)
            elif op == '-':
                res_bits = IEEE754Binary32.sub(a_bits, b_bits)
            elif op == '*':
                res_bits = IEEE754Binary32.mul(a_bits, b_bits)
            elif op == '/':
                try:
                    res_bits = IEEE754Binary32.div(a_bits, b_bits)
                except ZeroDivisionError as e:
                    print(e)
                    continue
            else:
                print("Неизвестная операция")
                continue
            print("\nРезультат в binary32:")
            # вывод битов
            bits_str = ''.join(str((res_bits >> i) & 1) for i in range(31, -1, -1))
            print("  биты:", ' '.join(bits_str[i:i+8] for i in range(0,32,8)))
            print("  десятичное значение:", IEEE754Binary32.to_float(res_bits))

        elif choice == '7':
            from bcd import BCD2421, BCDAdder
            try:
                num1 = int(input("Введите первое число (целое неотрицательное): "))
                num2 = int(input("Введите второе число: "))
                if num1 < 0 or num2 < 0:
                    print("Числа должны быть неотрицательными")
                    continue
            except:
                print("Ошибка ввода")
                continue
            adder = BCDAdder(BCD2421())
            tetrads, dec = adder.add(num1, num2)
            # Преобразуем список тетрад (8 чисел) в 32-битный список битов
            bits = []
            for t in tetrads:
                # Каждая тетрада – это 4 бита (от старшего к младшему)
                for shift in range(3, -1, -1):
                    bits.append((t >> shift) & 1)
            print("\nРезультат сложения в коде 2421 (32 бита):")
            print_bits(bits)
            print("Десятичное значение:", dec)
        else:
            print("Неверный пункт, попробуйте снова.")

if __name__ == "__main__":
    main()
