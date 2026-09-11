"""Restricted deterministic calculation for generated numerical questions."""

from __future__ import annotations

import ast
import operator
from decimal import Decimal, InvalidOperation

from app.services.numerical import parse_numeric_answer

_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_UNIT_FACTORS = {
    "ms": Decimal("0.001"),
    "s": Decimal("1"),
    "sec": Decimal("1"),
    "secs": Decimal("1"),
    "second": Decimal("1"),
    "seconds": Decimal("1"),
    "min": Decimal("60"),
    "mins": Decimal("60"),
    "minute": Decimal("60"),
    "minutes": Decimal("60"),
    "h": Decimal("3600"),
    "hr": Decimal("3600"),
    "hour": Decimal("3600"),
    "hours": Decimal("3600"),
}


def _evaluate(node: ast.AST, values: dict[str, Decimal]) -> Decimal:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, values)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Decimal(str(node.value))
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate(node.operand, values)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate(node.left, values)
        right = _evaluate(node.right, values)
        if isinstance(node.op, ast.Pow) and right != right.to_integral_value():
            raise ValueError("exponent must be an integer")
        return _BINARY_OPERATORS[type(node.op)](left, right)
    raise ValueError("formula contains an unsupported expression")


def calculate_formula(formula: str, quantities: dict[str, str]) -> Decimal | None:
    """Evaluate a supplied arithmetic formula using only supplied quantities."""
    expression = formula.split("=", 1)[-1].strip()
    try:
        values: dict[str, Decimal] = {}
        for name, raw_value in quantities.items():
            parsed = parse_numeric_answer(str(raw_value))
            if not parsed:
                return None
            value, unit = parsed
            values[name] = value * _UNIT_FACTORS.get(unit or "", Decimal("1"))
        tree = ast.parse(expression, mode="eval")
        return _evaluate(tree, values)
    except (SyntaxError, InvalidOperation, ValueError, ZeroDivisionError, OverflowError):
        return None
