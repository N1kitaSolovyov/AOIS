# bcd.py
from abc import ABC, abstractmethod

class BCDCode(ABC):
    @abstractmethod
    def encode(self, digit: int) -> int:
        pass

    @abstractmethod
    def decode(self, tetrad: int) -> int:
        pass

class BCD8421(BCDCode):
    def encode(self, digit: int) -> int:
        return digit
    def decode(self, tetrad: int) -> int:
        return tetrad if 0 <= tetrad <= 9 else None

class BCD2421(BCDCode):
    _encode = [0b0000, 0b0001, 0b0010, 0b0011, 0b0100, 0b1011, 0b1100, 0b1101, 0b1110, 0b1111]
    _decode = {v: k for k, v in enumerate(_encode)}
    def encode(self, digit: int) -> int:
        return self._encode[digit]
    def decode(self, tetrad: int) -> int:
        return self._decode.get(tetrad)

class BCD5421(BCDCode):
    _encode = [0b0000, 0b0001, 0b0010, 0b0011, 0b0100, 0b1000, 0b1001, 0b1010, 0b1011, 0b1100]
    _decode = {v: k for k, v in enumerate(_encode)}
    def encode(self, digit: int) -> int:
        return self._encode[digit]
    def decode(self, tetrad: int) -> int:
        return self._decode.get(tetrad)

class Excess3(BCDCode):
    def encode(self, digit: int) -> int:
        return digit + 3
    def decode(self, tetrad: int) -> int:
        d = tetrad - 3
        return d if 0 <= d <= 9 else None

class GrayBCD(BCDCode):
    def encode(self, digit: int) -> int:
        g = digit ^ (digit >> 1)
        return g & 0xF
    def decode(self, tetrad: int) -> int:
        b = tetrad
        mask = b >> 1
        while mask:
            b ^= mask
            mask >>= 1
        return b if 0 <= b <= 9 else None

class BCDAdder:
    def __init__(self, code: BCDCode):
        self.code = code

    def _dec_to_tetrads(self, num: int) -> list:
        digits = [int(d) for d in str(num)]
        digits = [0] * (8 - len(digits)) + digits
        return [self.code.encode(d) for d in digits]

    def _tetrads_to_dec(self, tetrads: list) -> int:
        digits = []
        for t in tetrads:
            d = self.code.decode(t)
            if d is None:
                raise ValueError("Некорректная тетрада")
            digits.append(d)
        num = 0
        for d in digits:
            num = num * 10 + d
        return num

    def add(self, num1: int, num2: int) -> tuple:
        tet1 = self._dec_to_tetrads(num1)
        tet2 = self._dec_to_tetrads(num2)
        result = [0] * 8
        carry = 0
        for i in range(7, -1, -1):
            a = self.code.decode(tet1[i])
            b = self.code.decode(tet2[i])
            s = a + b + carry
            carry = 1 if s >= 10 else 0
            d = s % 10
            result[i] = self.code.encode(d)
        return result, self._tetrads_to_dec(result)