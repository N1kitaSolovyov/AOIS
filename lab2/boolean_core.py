# boolean_core.py
from typing import List, Dict
from parser import tokenize, validate, to_rpn, evaluate_rpn

class BooleanFunction:
    def __init__(self, expression: str):
        expr_clean = ''.join(expression.split())
        tokens = tokenize(expr_clean)
        err = validate(tokens)
        if err:
            raise ValueError(f"Ошибка в формуле: {err}")
        self.original = expression
        self.tokens = tokens
        self.rpn = to_rpn(tokens)
        self.variables = sorted(set(t for t in tokens if t in 'abcde'))
        if len(self.variables) > 5:
            raise ValueError("Допустимо не более 5 переменных (a,b,c,d,e)")

    def evaluate(self, assignment: Dict[str, int]) -> int:
        # Проверка, что все переменные функции присутствуют в назначении
        for v in self.variables:
            if v not in assignment:
                raise ValueError(f"Не задано значение переменной {v}")
        return evaluate_rpn(self.rpn, assignment)

    def get_variables(self) -> List[str]:
        return self.variables.copy()