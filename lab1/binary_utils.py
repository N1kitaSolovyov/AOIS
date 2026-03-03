# binary_utils.py
# Набор функций для работы с двоичными массивами (списки бит, старший слева)

def int_to_bin_array(value: int, bits: int) -> list:
    """Преобразует неотрицательное целое в список битов длины bits (старший слева)."""
    if value == 0:
        return [0] * bits
    binary = []
    while value > 0:
        binary.append(value % 2)
        value //= 2
    while len(binary) < bits:
        binary.append(0)
    return list(reversed(binary))


def bin_array_to_int(bits: list) -> int:
    """Преобразует список битов (старший слева) в беззнаковое целое."""
    result = 0
    for b in bits:
        result = (result << 1) | b
    return result


def add_bin_arrays(a: list, b: list) -> tuple:
    """
    Сложение двух двоичных массивов одинаковой длины.
    Возвращает (результат, перенос).
    """
    n = len(a)
    res = [0] * n
    carry = 0
    for i in range(n - 1, -1, -1):
        total = a[i] + b[i] + carry
        res[i] = total % 2
        carry = total // 2
    return res, carry


def add_one(bits: list) -> list:
    """Прибавляет 1 к массиву бит (перенос отбрасывается)."""
    res = bits[:]
    carry = 1
    for i in range(len(res) - 1, -1, -1):
        total = res[i] + carry
        res[i] = total % 2
        carry = total // 2
    return res


def invert(bits: list) -> list:
    """Инвертирует все биты массива."""
    return [1 - b for b in bits]


def compare_unsigned(a: list, b: list) -> int:
    """
    Сравнивает два массива как беззнаковые числа.
    Возвращает 1, если a > b; 0, если a == b; -1, если a < b.
    """
    for i in range(len(a)):
        if a[i] > b[i]:
            return 1
        if a[i] < b[i]:
            return -1
    return 0


def shift_left_one(bits: list, fill=0) -> list:
    """Сдвиг массива влево на один разряд, в конец вставляется fill."""
    return bits[1:] + [fill]


def multiply_bin_arrays(a: list, b: list) -> list:
    """
    Умножение двух беззнаковых двоичных массивов (одинаковой длины).
    Возвращает результат длиной 2*len (без переполнения).
    """
    n = len(a)
    # Результат будет длины 2n
    res = [0] * (2 * n)
    for i in range(n - 1, -1, -1):
        if b[i] == 1:
            # Прибавляем a, сдвинутое на (n-1-i) влево
            shift = n - 1 - i
            carry = 0
            for j in range(n - 1, -1, -1):
                idx = 2 * n - 1 - (shift + (n - 1 - j))
                total = res[idx] + a[j] + carry
                res[idx] = total % 2
                carry = total // 2
            # Обрабатываем возможный дополнительный перенос
            idx_carry = 2 * n - 1 - (shift + n)
            if idx_carry >= 0:
                total = res[idx_carry] + carry
                res[idx_carry] = total % 2
                carry = total // 2
            # Если остался перенос, игнорируем (переполнение отбрасывается для 2n)
    return res


def divide_bin_arrays(dividend: list, divisor: list) -> tuple:
    """
    Деление беззнаковых двоичных массивов (одинаковой длины).
    Возвращает (частное, остаток) как списки бит длины len(dividend).
    Предполагается, что divisor != 0.
    """
    n = len(dividend)
    if bin_array_to_int(divisor) == 0:
        raise ZeroDivisionError("Division by zero")

    quotient = [0] * n
    remainder = [0] * n  # начинаем с нуля

    for i in range(n):
        # Сдвиг остатка влево и добавление следующего бита делимого
        remainder = shift_left_one(remainder, dividend[i])
        # Если остаток >= делитель
        if compare_unsigned(remainder, divisor) >= 0:
            # вычитаем делитель из остатка
            remainder, _ = add_bin_arrays(remainder, add_one(invert(divisor)))  # remainder - divisor
            quotient[i] = 1  # устанавливаем бит частного
        else:
            quotient[i] = 0
    return quotient, remainder