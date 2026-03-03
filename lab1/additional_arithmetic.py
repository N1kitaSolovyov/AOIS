# additional_arithmetic.py
from binary_codes import BinaryCodeConverter
from binary_utils import add_bin_arrays, invert, add_one

class AdditionalArithmetic:
    @staticmethod
    def add(num1: int, num2: int) -> tuple:
        code1 = BinaryCodeConverter(num1).additional_code()
        code2 = BinaryCodeConverter(num2).additional_code()
        sum_bits, _ = add_bin_arrays(code1, code2)
        decimal = BinaryCodeConverter.from_additional_to_decimal(sum_bits)
        return sum_bits, decimal

    @staticmethod
    def subtract(num1: int, num2: int) -> tuple:
        code1 = BinaryCodeConverter(num1).additional_code()
        code2 = BinaryCodeConverter(num2).additional_code()
        neg_code2 = add_one(invert(code2))
        diff_bits, _ = add_bin_arrays(code1, neg_code2)
        decimal = BinaryCodeConverter.from_additional_to_decimal(diff_bits)
        return diff_bits, decimal