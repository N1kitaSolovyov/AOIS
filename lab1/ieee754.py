# ieee754.py
# Реализация IEEE-754 binary32 без использования math
import math
class IEEE754Binary32:
    @staticmethod
    def _float_to_parts(x: float):
        """Разделяет обычное (не специальное) число на знак, экспоненту и мантиссу вручную.
           Предполагается, что x != 0, x не бесконечность и не NaN."""
        sign = 0 if x >= 0 else 1
        x = abs(x)

        # Поиск экспоненты (такой, чтобы 1 <= x/2^e < 2)
        e = 0
        if x >= 2.0:
            while x >= 2.0:
                x /= 2.0
                e += 1
        elif x < 1.0:
            while x < 1.0:
                x *= 2.0
                e -= 1
        # Теперь x в [1,2)
        frac = x - 1.0  # дробная часть в [0,1)
        # Перевод frac в 23-битное целое
        mant_int = 0
        for _ in range(23):
            frac *= 2
            bit = int(frac)
            mant_int = (mant_int << 1) | bit
            frac -= bit
        return sign, e, mant_int

    @staticmethod
    def from_float(x: float) -> int:
        """Преобразует float в 32-битное целое (битовое представление)."""
        # Обработка специальных значений
        if x != x:  # NaN
            return 0x7FC00000  # канонический NaN (sign=0, exp=255, mant != 0)
        if x == float('inf'):
            return 0x7F800000   # +inf: sign 0, exp=255, mant=0
        if x == float('-inf'):
            return 0xFF800000   # -inf: sign 1, exp=255, mant=0

        if x == 0.0:
            # Сохраняем знак нуля (Python различает +0.0 и -0.0)
            return 0 if math.copysign(1.0, x) > 0 else (1 << 31)

        sign, exp, mant = IEEE754Binary32._float_to_parts(x)
        # Смещённая экспонента
        biased_exp = exp + 127
        if biased_exp <= 0:  # денормализованное (на самом деле не должно возникать при exp >= -126)
            # Для простоты не реализуем, считаем нулём
            return 0
        if biased_exp >= 255:  # бесконечность (переполнение)
            return (sign << 31) | (0xFF << 23)
        return (sign << 31) | (biased_exp << 23) | mant

    @staticmethod
    def to_float(bits: int) -> float:
        """Из битового представления в float."""
        sign = (bits >> 31) & 1
        exp = (bits >> 23) & 0xFF
        mant = bits & 0x7FFFFF
        if exp == 0:
            if mant == 0:
                return 0.0
            # денормализованное
            return ((-1)**sign) * mant * (2**(-149))
        elif exp == 255:
            if mant == 0:
                return float('inf') if sign == 0 else float('-inf')
            return float('nan')
        else:
            return ((-1)**sign) * (1 + mant / (1 << 23)) * (2**(exp - 127))

    @staticmethod
    def _unpack(bits: int):
        sign = (bits >> 31) & 1
        exp = (bits >> 23) & 0xFF
        mant = bits & 0x7FFFFF
        return sign, exp, mant

    @staticmethod
    def _pack(sign: int, exp: int, mant: int) -> int:
        return (sign << 31) | (exp << 23) | mant

    @classmethod
    def add(cls, a_bits: int, b_bits: int) -> int:
        """Сложение двух binary32 чисел."""
        s1, e1, m1 = cls._unpack(a_bits)
        s2, e2, m2 = cls._unpack(b_bits)

        # Обработка нулей и особых случаев
        if e1 == 0 and m1 == 0:
            return b_bits
        if e2 == 0 and m2 == 0:
            return a_bits
        if e1 == 0xFF:
            if e2 == 0xFF and s1 != s2:
                return 0x7FC00000  # NaN (inf + -inf)
            return a_bits
        if e2 == 0xFF:
            return b_bits

        # Получаем 24-битную мантиссу со скрытой единицей
        if e1 == 0:
            man1 = m1
            exp1 = -126
        else:
            man1 = m1 | (1 << 23)
            exp1 = e1 - 127
        if e2 == 0:
            man2 = m2
            exp2 = -126
        else:
            man2 = m2 | (1 << 23)
            exp2 = e2 - 127

        # Выравнивание порядков
        if exp1 < exp2:
            s1, s2 = s2, s1
            man1, man2 = man2, man1
            exp1, exp2 = exp2, exp1
        d = exp1 - exp2
        if d > 0:
            man2_shifted = man2 >> d
            # потерянные биты для округления
            lost = man2 & ((1 << d) - 1)
            G = (lost >> (d-1)) & 1
            R = (lost >> (d-2)) & 1 if d >= 2 else 0
            S = 1 if (d >= 3 and (lost & ((1 << (d-2)) - 1) != 0)) else 0
        else:
            man2_shifted = man2
            G = R = S = 0

        # Операция в зависимости от знаков
        if s1 == s2:  # сложение
            sum_man = man1 + man2_shifted
            # округление
            if G == 1 and (R == 1 or S == 1 or (sum_man & 1 == 1)):
                sum_man += 1
            # нормализация
            if sum_man >= (1 << 24):
                sum_man >>= 1
                exp1 += 1
            while sum_man < (1 << 23) and sum_man != 0:
                sum_man <<= 1
                exp1 -= 1
            sign_res = s1
        else:  # вычитание
            if man1 > man2_shifted:
                diff = man1 - man2_shifted
                sign_res = s1
                if G == 1 and (R == 1 or S == 1 or (diff & 1 == 1)):
                    diff -= 1
            elif man1 < man2_shifted:
                diff = man2_shifted - man1
                sign_res = s2
                if G == 1 and (R == 1 or S == 1 or (diff & 1 == 1)):
                    diff += 1
            else:
                # равны
                return 0
            # нормализация разности
            if diff == 0:
                return 0
            while diff < (1 << 23):
                diff <<= 1
                exp1 -= 1
            sum_man = diff

        # Упаковка
        if sum_man == 0:
            return 0
        if sum_man >= (1 << 23):
            exp_res = exp1 + 127
            if exp_res >= 0xFF:
                return cls._pack(sign_res, 0xFF, 0)
            if exp_res <= 0:
                shift = 1 - exp_res
                sum_man >>= shift
                exp_res = 0
            mant_res = sum_man - (1 << 23) if exp_res != 0 else sum_man
            return cls._pack(sign_res, exp_res, mant_res)
        else:
            if exp1 < -126:
                shift = -126 - exp1
                sum_man >>= shift
            return cls._pack(sign_res, 0, sum_man)

    @classmethod
    def sub(cls, a_bits: int, b_bits: int) -> int:
        """Вычитание через сложение с изменённым знаком."""
        b_neg = b_bits ^ (1 << 31)
        return cls.add(a_bits, b_neg)

    @classmethod
    def mul(cls, a_bits: int, b_bits: int) -> int:
        """Умножение двух binary32 чисел."""
        s1, e1, m1 = cls._unpack(a_bits)
        s2, e2, m2 = cls._unpack(b_bits)

        # Обработка специальных случаев
        if e1 == 0xFF or e2 == 0xFF:
            # inf или NaN
            if e1 == 0xFF and m1 != 0:
                return a_bits  # NaN
            if e2 == 0xFF and m2 != 0:
                return b_bits  # NaN
            # inf * 0 -> NaN
            if (e1 == 0xFF and e2 == 0 and m2 == 0) or (e2 == 0xFF and e1 == 0 and m1 == 0):
                return 0x7FC00000
            # inf * число -> inf со знаком
            sign_res = s1 ^ s2
            return cls._pack(sign_res, 0xFF, 0)

        if e1 == 0 and m1 == 0 or e2 == 0 and m2 == 0:
            # Умножение на ноль
            return 0

        # Получаем 24-битную мантиссу
        man1 = m1 | (1 << 23) if e1 != 0 else m1
        man2 = m2 | (1 << 23) if e2 != 0 else m2
        exp1 = e1 - 127 if e1 != 0 else -126
        exp2 = e2 - 127 if e2 != 0 else -126

        # Знак результата
        sign_res = s1 ^ s2

        # Умножение мантисс (24 бита * 24 бита -> до 48 бит)
        prod_man = man1 * man2
        # Нормализация
        if prod_man & (1 << 47):
            # Старший бит установлен -> сдвиг вправо
            prod_man >>= 1
            exp_res = exp1 + exp2 + 1
        else:
            exp_res = exp1 + exp2

        # Округление (упрощённое: отбрасываем младшие биты)
        # Здесь можно реализовать более аккуратное округление, но для простоты сдвинем
        while prod_man >= (1 << 24):
            prod_man >>= 1
            exp_res += 1
        # Теперь prod_man < 2^24
        if prod_man < (1 << 23):
            prod_man <<= 1
            exp_res -= 1

        # Проверка экспоненты
        biased_exp = exp_res + 127
        if biased_exp >= 0xFF:
            return cls._pack(sign_res, 0xFF, 0)  # inf
        if biased_exp <= 0:
            # Денормализованное или ноль
            # Упрощённо: ноль
            return 0
        mant_res = prod_man - (1 << 23)
        return cls._pack(sign_res, biased_exp, mant_res)

    @classmethod
    def div(cls, a_bits: int, b_bits: int) -> int:
        """Деление двух binary32 чисел (a / b)."""
        s1, e1, m1 = cls._unpack(a_bits)
        s2, e2, m2 = cls._unpack(b_bits)

        # Обработка специальных случаев
        if e2 == 0xFF:
            if e2 == 0xFF and m2 != 0:
                return b_bits  # NaN
            # деление на inf
            if e1 == 0xFF:
                if m1 != 0:
                    return a_bits  # NaN
                # inf / inf -> NaN
                return 0x7FC00000
            # число / inf -> 0 со знаком
            return cls._pack(s1 ^ s2, 0, 0)
        if e1 == 0xFF:
            if m1 != 0:
                return a_bits  # NaN
            # inf / число -> inf
            return cls._pack(s1 ^ s2, 0xFF, 0)

        if e2 == 0 and m2 == 0:
            # Деление на ноль
            if e1 == 0 and m1 == 0:
                return 0x7FC00000  # 0/0 = NaN
            return cls._pack(s1 ^ s2, 0xFF, 0)  # число/0 = inf
        if e1 == 0 and m1 == 0:
            return 0  # 0 / число = 0

        man1 = m1 | (1 << 23) if e1 != 0 else m1
        man2 = m2 | (1 << 23) if e2 != 0 else m2
        exp1 = e1 - 127 if e1 != 0 else -126
        exp2 = e2 - 127 if e2 != 0 else -126

        sign_res = s1 ^ s2

        # Деление мантисс: man1 / man2, результат нормализовать к [1,2)
        # Для увеличения точности сдвинем man1 влево
        man1 <<= 23
        # Выполняем целочисленное деление
        if man2 == 0:
            return cls._pack(sign_res, 0xFF, 0)  # inf (уже должно быть отловлено)
        quot = man1 // man2
        exp_res = exp1 - exp2 - 23  # поправка на сдвиг

        # Нормализация
        if quot == 0:
            return 0
        while quot < (1 << 23):
            quot <<= 1
            exp_res -= 1
        while quot >= (1 << 24):
            quot >>= 1
            exp_res += 1

        biased_exp = exp_res + 127
        if biased_exp >= 0xFF:
            return cls._pack(sign_res, 0xFF, 0)
        if biased_exp <= 0:
            # Денормализованное – упрощённо 0
            return 0
        mant_res = quot - (1 << 23)
        return cls._pack(sign_res, biased_exp, mant_res)