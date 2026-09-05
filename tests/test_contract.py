# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import json
import unittest
from pathlib import Path


class ContractTests(unittest.TestCase):
    def test_contract_ids_are_unique_and_core_invariants_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "contracts/razorpay.json").read_text())
        ids = [item["id"] for item in data["contracts"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("refund.create", ids)
        self.assertIn("checkout.generated-order", ids)
        self.assertIn("checkout.currency-exponent", ids)
        self.assertIn("checkout.quote-binding", ids)
        self.assertIn("sdk.client-isolation", ids)
        self.assertIn("partner.header-isolation", ids)
        self.assertIn("document.multipart", ids)
        self.assertIn("onboarding-signature.encrypt", ids)

        refund = next(item for item in data["contracts"] if item["id"] == "refund.create")
        self.assertEqual(
            "each request is a distinct refund intent",
            refund["effect"]["without_identity"],
        )
        self.assertIn("stable receipt field", refund["effect"]["identity_mechanisms"])

        webhook = next(item for item in data["contracts"] if item["id"] == "webhook.verify")
        self.assertIn("hardening", webhook["cryptography"]["comparison_policy"])

        exponent = next(item for item in data["contracts"] if item["id"] == "checkout.currency-exponent")
        self.assertEqual(295, exponent["money"]["examples"]["JPY_295"])
        self.assertEqual(295990, exponent["money"]["examples"]["KWD_295_990"])


if __name__ == "__main__":
    unittest.main()
