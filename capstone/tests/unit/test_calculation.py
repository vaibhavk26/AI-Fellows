from decimal import Decimal

from app.services.calculation import calculate_formula
from app.services.numerical import parse_numeric_answer


def test_calculates_arithmetic_formula_with_unit_conversion():
    assert calculate_formula("Q = I * t", {"I": "0.6 A", "t": "4 min"}) == Decimal("144.0")


def test_resolves_named_physics_constants_without_requiring_quantities():
    result = calculate_formula("B = mu0*I/(2*pi*r)", {"I": "3.0 A", "r": "0.05 m"})
    assert result is not None
    assert abs(result - Decimal("1.2e-5")) < Decimal("1e-6")


def test_parse_numeric_answer_accepts_compound_unit():
    assert parse_numeric_answer("0.004 N\u00b7m") == (Decimal("0.004"), "n\u00b7m")
    assert parse_numeric_answer("7.5e-4 T\u00b7m\u00b7A") == (Decimal("7.5e-4"), "t\u00b7m\u00b7a")


def test_calculates_fraction_and_power_expression():
    assert calculate_formula("d = v * t", {"v": "1/2 m/s", "t": "10 s"}) == Decimal("5.0")
    assert calculate_formula("A = s ** 2", {"s": "3"}) == Decimal("9")


def test_rejects_unsafe_or_incomplete_formula():
    assert calculate_formula("__import__('os').system('whoami')", {"x": "1"}) is None
    assert calculate_formula("x + missing", {"x": "1"}) is None
    assert calculate_formula("x / 0", {"x": "1"}) is None


def test_rejects_invalid_quantity_values():
    assert calculate_formula("x * y", {"x": "not-a-number", "y": "2"}) is None
