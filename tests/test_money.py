# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import unittest

from razorproof.money import major_to_minor


class MoneyTests(unittest.TestCase):
    def test_counterexample_is_exact(self) -> None:
        self.assertEqual(201, major_to_minor("2.01", "INR"))

    def test_float_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            major_to_minor(2.01, "INR")  # type: ignore[arg-type]

    def test_excess_precision_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            major_to_minor("2.001", "INR")


if __name__ == "__main__":
    unittest.main()
