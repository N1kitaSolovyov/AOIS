from typing import Dict, List, Optional

# Разрешённые переменные и операторы
VARIABLES = set('abcde')
CONSTANTS = {'0', '1'}
OPERANDS = VARIABLES | CONSTANTS
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

# Ассоциативность: True = правоассоциативный оператор
RIGHT_ASSOC = {
    '!': True,
    '->': True,
    '~': False,
    '&': False,
    '|': False,
}

UNICODE_REPLACEMENTS = {
    '¬': '!',
    '﹁': '!',
    '∧': '&',
    '⋀': '&',
    '∨': '|',
    '⋁': '|',
    '→': '->',
    '⟶': '->',
    '⇒': '->',
    '↔': '~',
    '≡': '~',
    '⇔': '~',
}


def normalize_expression(expr: str) -> str:
    """Нормализует Unicode-символы логики к ASCII-представлению."""
    out: List[str] = []
    for ch in expr:
        out.append(UNICODE_REPLACEMENTS.get(ch, ch))
    return ''.join(out)


def tokenize(expr: str) -> List[str]:
    """Разбивает выражение на токены (скобки, переменные, операторы)."""
    expr = normalize_expression(expr)
    tokens: List[str] = []
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch in OPERANDS or ch in '()':
            tokens.append(ch)
            i += 1
        elif ch == '!':
            tokens.append(ch)
            i += 1
        elif ch in {'&', '|', '~'}:
            tokens.append(ch)
            i += 1
        elif ch == '-':
            if i + 1 < n and expr[i + 1] == '>':
                tokens.append('->')
                i += 2
            else:
                raise ValueError(f"Неверный символ '-' без '>' на позиции {i}")
        elif ch.isspace():
            i += 1
        else:
            raise ValueError(f"Недопустимый символ '{ch}' на позиции {i}")
    return tokens


def validate(tokens: List[str]) -> Optional[str]:
    """Проверяет корректность последовательности токенов."""
    if not tokens:
        return 'Пустое выражение'

    balance = 0
    expect_operand = True
    for i, tok in enumerate(tokens):
        if tok == '(':
            if not expect_operand:
                return f"Открывающая скобка не может следовать за операндом на позиции {i}"
            balance += 1
            expect_operand = True
        elif tok == ')':
            balance -= 1
            if balance < 0:
                return 'Несбалансированные скобки'
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
        elif tok in OPERANDS:
            if not expect_operand:
                kind = 'Константа' if tok in CONSTANTS else 'Переменная'
                return f"{kind} '{tok}' не может следовать за операндом без оператора на позиции {i}"
            expect_operand = False
        else:
            return f"Неизвестный токен '{tok}'"

    if balance != 0:
        return 'Несбалансированные скобки'
    if expect_operand:
        return 'Выражение заканчивается оператором или пустое'
    return None


def to_rpn(tokens: List[str]) -> List[str]:
    """Преобразует инфиксное выражение в обратную польскую нотацию (RPN)."""
    output: List[str] = []
    stack: List[str] = []

    for tok in tokens:
        if tok in OPERANDS:
            output.append(tok)
        elif tok == '(':
            stack.append(tok)
        elif tok == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if not stack:
                raise ValueError('Несбалансированные скобки')
            stack.pop()
        elif tok == UNARY_OP:
            stack.append(tok)
        elif tok in BINARY_OPS:
            while stack and stack[-1] != '(':
                top = stack[-1]
                should_pop = (
                    PRECEDENCE.get(top, 0) > PRECEDENCE[tok]
                    or (
                        PRECEDENCE.get(top, 0) == PRECEDENCE[tok]
                        and not RIGHT_ASSOC.get(tok, False)
                    )
                )
                if not should_pop:
                    break
                output.append(stack.pop())
            stack.append(tok)
        else:
            raise ValueError(f'Неизвестный токен: {tok}')

    while stack:
        tok = stack.pop()
        if tok in {'(', ')'}:
            raise ValueError('Несбалансированные скобки')
        output.append(tok)
    return output


def evaluate_rpn(rpn: List[str], assignment: Dict[str, int]) -> int:
    """Вычисляет значение выражения в RPN по заданной подстановке."""
    stack: List[int] = []
    for tok in rpn:
        if tok in CONSTANTS:
            stack.append(int(tok))
        elif tok in VARIABLES:
            stack.append(int(assignment[tok]))
        elif tok == UNARY_OP:
            if not stack:
                raise ValueError("Недостаточно операндов для '!' в RPN")
            a = stack.pop()
            stack.append(1 - a)
        elif tok in {'&', '|', '->', '~'}:
            if len(stack) < 2:
                raise ValueError(f"Недостаточно операндов для '{tok}' в RPN")
            b = stack.pop()
            a = stack.pop()
            if tok == '&':
                stack.append(a & b)
            elif tok == '|':
                stack.append(a | b)
            elif tok == '->':
                stack.append((1 - a) | b)
            else:  # '~'
                stack.append(1 if a == b else 0)
        else:
            raise ValueError(f'Неизвестный токен в RPN: {tok}')

    if len(stack) != 1:
        raise ValueError('Некорректная RPN: после вычисления остались лишние значения')
    return stack[-1]
