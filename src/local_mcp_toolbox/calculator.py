"""A constrained arithmetic expression evaluator for the calculator tool."""

from __future__ import annotations

import ast
import math
import operator
from typing import Callable

MAX_EXPRESSION_LENGTH = 128
MAX_RESULT_MAGNITUDE = 1_000_000_000_000
MAX_POWER_EXPONENT = 10
MAX_AST_NODES = 64

_BINARY_OPERATORS: dict[type[ast.operator], Callable[[int | float, int | float], int | float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[int | float], int | float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalculatorError(ValueError):
    """Raised when an arithmetic expression is invalid or unsafe."""


def _checked_number(value: object) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CalculatorError("Only numeric values are allowed.")
    if isinstance(value, int):
        if abs(value) > MAX_RESULT_MAGNITUDE:
            raise CalculatorError("The calculation exceeds the supported numeric range.")
    elif not math.isfinite(value) or abs(value) > MAX_RESULT_MAGNITUDE:
        raise CalculatorError("The calculation exceeds the supported numeric range.")
    return value


def _evaluate(node: ast.AST, depth: int = 0) -> int | float:
    if depth > 16:
        raise CalculatorError("The expression is nested too deeply.")

    if isinstance(node, ast.Constant):
        return _checked_number(node.value)

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate(node.left, depth + 1)
        right = _evaluate(node.right, depth + 1)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_POWER_EXPONENT:
            raise CalculatorError(
                f"Exponent magnitude must not exceed {MAX_POWER_EXPONENT}."
            )
        try:
            result = _BINARY_OPERATORS[type(node.op)](left, right)
        except ZeroDivisionError as exc:
            raise CalculatorError("Division by zero is not allowed.") from exc
        except (OverflowError, ValueError) as exc:
            raise CalculatorError("The calculation could not be completed.") from exc
        return _checked_number(result)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _checked_number(
            _UNARY_OPERATORS[type(node.op)](_evaluate(node.operand, depth + 1))
        )

    raise CalculatorError(
        "Unsupported expression. Use numbers, parentheses, and +, -, *, /, //, %, **."
    )


def evaluate_expression(expression: str) -> dict[str, object]:
    """Safely evaluate basic arithmetic without using Python eval()."""

    candidate = expression.strip()
    if not candidate:
        return {
            "ok": False,
            "expression": expression,
            "error": "Expression cannot be empty.",
        }
    if len(candidate) > MAX_EXPRESSION_LENGTH:
        return {
            "ok": False,
            "expression": expression,
            "error": "Expression is too long.",
        }

    try:
        parsed = ast.parse(candidate, mode="eval")
        if sum(1 for _ in ast.walk(parsed)) > MAX_AST_NODES:
            raise CalculatorError("Expression is too complex.")
        result = _evaluate(parsed.body)
        return {"ok": True, "expression": candidate, "result": result}
    except (SyntaxError, CalculatorError) as exc:
        return {"ok": False, "expression": candidate, "error": str(exc)}


__all__ = ["CalculatorError", "evaluate_expression"]
