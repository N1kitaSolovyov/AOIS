# parser.py
from typing import List, Dict, Tuple, Optional

# Разрешённые переменные и операторы
VARIABLES = set('abcde')
BINARY_OPS = {'&', '|', '->', '~'}
UNARY_OP = '!'
# Приоритеты операторов (чем выше число, тем выше приоритет)
PRECEDENCE = {
    '!': 4,
    '&': 3,
    '|': 2,
    '->': 1,
    '~': 1,
}

def tokenize(expr: str) -> List[str]:
    """Разбивает выражение на токены (скобки, переменные, операторы)."""
    tokens = []
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch in VARIABLES or ch in '()':
            tokens.append(ch)
            i += 1
        elif ch == '!':
            tokens.append(ch)
            i += 1
        elif ch == '&' or ch == '|':
            tokens.append(ch)
            i += 1
        elif ch == '-':
            if i + 1 < n and expr[i+1] == '>':
                tokens.append('->')
                i += 2
            else:
                raise ValueError(f"Неверный символ '-' без '>' на позиции {i}")
        elif ch == '~':
            tokens.append('~')
            i += 1
        elif ch == ' ':
            i += 1
        else:
            raise ValueError(f"Недопустимый символ '{ch}' на позиции {i}")
    return tokens

def validate(tokens: List[str]) -> Optional[str]:
    """Проверяет корректность последовательности токенов.
    Возвращает None, если ошибок нет, иначе строку с ошибкой."""
    if not tokens:
        return "Пустое выражение"
    # Проверка баланса скобок
    balance = 0
    for tok in tokens:
        if tok == '(':
            balance += 1
        elif tok == ')':
            balance -= 1
            if balance < 0:
                return "Несбалансированные скобки"
    if balance != 0:
        return "Несбалансированные скобки"

    # Проверка структуры: ожидаем операнд или унарный !
    expect_operand = True
    for i, tok in enumerate(tokens):
        if tok == '(':
            if not expect_operand:
                return f"Открывающая скобка не может следовать за операндом на позиции {i}"
            expect_operand = True
        elif tok == ')':
            if expect_operand:
                return f"Закрывающая скобка не может быть на месте операнда на позиции {i}"
            expect_operand = False
        elif tok == UNARY_OP:
            if not expect_operand:
                return f"Унарный оператор '!' не может следовать за операндом на позиции {i}"
            expect_operand = True
        elif tok in BINARY_OPS:
            if expect_operand:
                return f"Бинарный оператор '{tok}' не имеет левого операнда на позиции {i}"
            expect_operand = True
        elif tok in VARIABLES:
            if not expect_operand:
                return f"Переменная '{tok}' не может следовать за операндом без оператора на позиции {i}"
            expect_operand = False
        else:
            return f"Неизвестный токен '{tok}'"
    if expect_operand:
        return "Выражение заканчивается оператором или пустое"
    return None

def to_rpn(tokens: List[str]) -> List[str]:
    """Преобразует инфиксное выражение в обратную польскую нотацию (RPN)."""
    output = []
    stack = []
    for tok in tokens:
        if tok in VARIABLES:
            output.append(tok)
        elif tok == UNARY_OP:
            stack.append(tok)
        elif tok in BINARY_OPS:
            while (stack and stack[-1] != '(' and
                   PRECEDENCE.get(stack[-1], 0) >= PRECEDENCE[tok]):
                output.append(stack.pop())
            stack.append(tok)
        elif tok == '(':
            stack.append(tok)
        elif tok == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
            else:
                raise ValueError("Несбалансированные скобки")
    while stack:
        output.append(stack.pop())
    return output

def evaluate_rpn(rpn: List[str], assignment: Dict[str, int]) -> int:
    """Вычисляет значение выражения в RPN по заданной подстановке."""
    stack = []
    for tok in rpn:
        if tok in VARIABLES:
            stack.append(assignment[tok])
        elif tok == UNARY_OP:
            a = stack.pop()
            stack.append(1 - a)
        elif tok == '&':
            b = stack.pop()
            a = stack.pop()
            stack.append(a & b)
        elif tok == '|':
            b = stack.pop()
            a = stack.pop()
            stack.append(a | b)
        elif tok == '->':
            b = stack.pop()
            a = stack.pop()
            stack.append((1 - a) | b)
        elif tok == '~':
            b = stack.pop()
            a = stack.pop()
            stack.append(1 if a == b else 0)
        else:
            raise ValueError(f"Неизвестный токен в RPN: {tok}")
    return stack[-1]