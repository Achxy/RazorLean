# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import unittest

from razorproof.faultlab import run_fault_lab


class FaultLabTests(unittest.TestCase):
    def test_lost_response_duplicates_without_identity_only(self) -> None:
        try:
            result = run_fault_lab()
        except PermissionError as exc:
            self.skipTest(f"local socket binding blocked by execution sandbox: {exc}")
        self.assertEqual(2, result["without_effect_identity"]["count"])
        self.assertEqual(1, result["with_effect_identity"]["count"])


if __name__ == "__main__":
    unittest.main()
