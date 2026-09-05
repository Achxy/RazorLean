# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

from decimal import Decimal, InvalidOperation


CURRENCY_EXPONENTS = {
    "INR": 2,
    "USD": 2,
    "EUR": 2,
    "JPY": 0,
}


def major_to_minor(value: str, currency: str = "INR") -> int:
    """Convert an exact decimal string to integer currency subunits.

    Floats are deliberately rejected: once a decimal amount has crossed a binary
    float boundary, its original decimal intent may no longer be recoverable.
    """
    if not isinstance(value, str):
        raise TypeError("money must enter as an exact decimal string")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid decimal money value: {value!r}") from exc
    if not amount.is_finite():
        raise ValueError("money must be finite")
    exponent = CURRENCY_EXPONENTS.get(currency.upper())
    if exponent is None:
        raise ValueError(f"unknown currency exponent: {currency}")
    scale = Decimal(10) ** exponent
    minor = amount * scale
    if minor != minor.to_integral_value():
        raise ValueError(f"{value} has more precision than {currency} supports")
    if minor <= 0:
        raise ValueError("money must be positive")
    return int(minor)
