# binary_codes.py
from binary_utils import int_to_bin_array, invert, add_one, bin_array_to_int


class BinaryCodeConverter:
    """Представление числа в трёх двоичных кодах (32 бита)."""

    def __init__(self, decimal: int):
        self.decimal = decimal
        self.sign = 0 if decimal >= 0 else 1
        self.modulus = abs(decimal)
        self.mod_bits = int_to_bin_array(self.modulus, 31)

    def direct_code(self) -> list:
        return [self.sign] + self.mod_bits

    def inverse_code(self) -> list:
        if self.sign == 0:
            return self.direct_code()
        inv_mod = invert(self.mod_bits)
        return [self.sign] + inv_mod

    def additional_code(self) -> list:
        if self.sign == 0:
            return self.direct_code()
        inv = self.inverse_code()
        return add_one(inv)

    @staticmethod
    def from_direct_to_decimal(bits: list) -> int:
        sign = bits[0]
        magnitude = bin_array_to_int(bits[1:])
        return -magnitude if sign else magnitude

    @staticmethod
    def from_inverse_to_decimal(bits: list) -> int:
        sign = bits[0]
        if sign == 0:
            return bin_array_to_int(bits[1:])
        magnitude = bin_array_to_int(invert(bits[1:]))
        return -magnitude

    @staticmethod
    def from_additional_to_decimal(bits: list) -> int:
        unsigned = bin_array_to_int(bits)
        if bits[0] == 1:
            unsigned -= (1 << 32)
        return unsigned