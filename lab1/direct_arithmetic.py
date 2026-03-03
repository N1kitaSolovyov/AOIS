# direct_arithmetic.py
from binary_codes import BinaryCodeConverter
from binary_utils import (
    int_to_bin_array, bin_array_to_int, multiply_bin_arrays,
    divide_bin_arrays, compare_unsigned, shift_left_one, add_bin_arrays
)

class DirectMultiplier:
    @staticmethod
    def multiply(num1: int, num2: int) -> tuple:
        conv1 = BinaryCodeConverter(num1)
        conv2 = BinaryCodeConverter(num2)
        sign = conv1.sign ^ conv2.sign

        # Умножение модулей (31 бит) вручную
        prod_bits = multiply_bin_arrays(conv1.mod_bits, conv2.mod_bits)  # длина 62
        # Оставляем младшие 31 бит (как в исходном коде)
        prod_mod_bits = prod_bits[-31:]  # берём правую половину
        # Если произведение нулевое, все биты нули
        if bin_array_to_int(prod_mod_bits) == 0 and bin_array_to_int(prod_bits[:-31]) == 0:
            prod_mod_bits = [0] * 31
        result_bits = [sign] + prod_mod_bits
        decimal = BinaryCodeConverter.from_direct_to_decimal(result_bits)
        return result_bits, decimal

class DirectDivider:
    @staticmethod
    def divide(num1: int, num2: int) -> tuple:
        if num2 == 0:
            raise ZeroDivisionError("Деление на ноль")
        conv1 = BinaryCodeConverter(num1)
        conv2 = BinaryCodeConverter(num2)
        sign = conv1.sign ^ conv2.sign

        scale = 100000

        mag1, mag2 = conv1.modulus, conv2.modulus
        temp = mag1 * scale
        quotient = temp // mag2
        remainder = temp % mag2
        if remainder * 2 >= mag2:
            quotient += 1
        max_mod = (1 << 31) - 1
        if quotient > max_mod:
            quotient = quotient & max_mod
        mod_bits = int_to_bin_array(quotient, 31)
        result_bits = [sign] + mod_bits
        decimal = (-1 if sign else 1) * quotient / scale
        return result_bits, decimal