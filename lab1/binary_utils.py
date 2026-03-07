def int_to_bin_array(value: int, bits: int) -> list:
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
    result = 0
    for b in bits:
        result = (result << 1) | b
    return result


def add_bin_arrays(a: list, b: list) -> tuple:
    n = len(a)
    res = [0] * n
    carry = 0
    for i in range(n - 1, -1, -1):
        total = a[i] + b[i] + carry
        res[i] = total % 2
        carry = total // 2
    return res, carry


def add_one(bits: list) -> list:
    res = bits[:]
    carry = 1
    for i in range(len(res) - 1, -1, -1):
        total = res[i] + carry
        res[i] = total % 2
        carry = total // 2
    return res


def invert(bits: list) -> list:
    return [1 - b for b in bits]


def compare_unsigned(a: list, b: list) -> int:
    for i in range(len(a)):
        if a[i] > b[i]:
            return 1
        if a[i] < b[i]:
            return -1
    return 0


def shift_left_one(bits: list, fill=0) -> list:
    return bits[1:] + [fill]


def multiply_bin_arrays(a: list, b: list) -> list:
    n = len(a)
    res = [0] * (2 * n)
    for i in range(n - 1, -1, -1):
        if b[i] == 1:
            shift = n - 1 - i
            carry = 0
            for j in range(n - 1, -1, -1):
                idx = 2 * n - 1 - (shift + (n - 1 - j))
                total = res[idx] + a[j] + carry
                res[idx] = total % 2
                carry = total // 2
            idx_carry = 2 * n - 1 - (shift + n)
            if idx_carry >= 0:
                total = res[idx_carry] + carry
                res[idx_carry] = total % 2
                carry = total // 2
    return res


def divide_bin_arrays(dividend: list, divisor: list) -> tuple:
    n = len(dividend)
    if bin_array_to_int(divisor) == 0:
        raise ZeroDivisionError("Division by zero")

    quotient = [0] * n
    remainder = [0] * n

    for i in range(n):
        remainder = shift_left_one(remainder, dividend[i])
        if compare_unsigned(remainder, divisor) >= 0:
            remainder, _ = add_bin_arrays(remainder, add_one(invert(divisor)))
            quotient[i] = 1
        else:
            quotient[i] = 0
    return quotient, remainder