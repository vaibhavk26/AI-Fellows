"""Shared parsing for generated and submitted numerical answers."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_NUMBER = r"[-+]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][-+]?\d+)?|[-+]?\d+\s*/\s*\d+"
_NUMERIC_ANSWER = re.compile(
    rf"^(?P<number>{_NUMBER})(?:\s*(?P<unit>%|[A-Za-z][A-Za-z0-9]*(?:/[A-Za-z][A-Za-z0-9]*)?(?:\^[-+]?\d+)?))?$"
)


def parse_numeric_answer(value: str) -> tuple[Decimal, str | None] | None:
    """Return a numeric value and normalized unit, or None for invalid input."""
    match = _NUMERIC_ANSWER.fullmatch(value.strip())
    if not match:
        return None
    number_text = match.group("number").replace(" ", "")
    try:
        if "/" in number_text:
            numerator, denominator = number_text.split("/", 1)
            denominator_value = Decimal(denominator)
            if denominator_value == 0:
                return None
            number = Decimal(numerator) / denominator_value
        else:
            number = Decimal(number_text)
    except InvalidOperation:
        return None
    unit = match.group("unit")
    return number, unit.casefold() if unit else None
