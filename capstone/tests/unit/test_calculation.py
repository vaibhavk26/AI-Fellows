from decimal import Decimal

from app.services.calculation import calculate_formula


def test_calculates_arithmetic_formula_with_unit_conversion():
    assert calculate_formula("Q = I * t", {"I": "0.6 A", "t": "4 min"}) == Decimal("144.0")


def test_calculates_fraction_and_power_expression():
    assert calculate_formula("d = v * t", {"v": "1/2 m/s", "t": "10 s"}) == Decimal("5.0")
    assert calculate_formula("A = s ** 2", {"s": "3"}) == Decimal("9")


def test_rejects_unsafe_or_incomplete_formula():
    assert calculate_formula("__import__('os').system('whoami')", {"x": "1"}) is None
    assert calculate_formula("x + missing", {"x": "1"}) is None
    assert calculate_formula("x / 0", {"x": "1"}) is None


def test_rejects_invalid_quantity_values():
    assert calculate_formula("x * y", {"x": "not-a-number", "y": "2"}) is None
