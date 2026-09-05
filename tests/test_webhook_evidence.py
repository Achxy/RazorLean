# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import tempfile
import unittest
from pathlib import Path

from razorproof.webhook_evidence import build_webhook_byte_evidence


class WebhookEvidenceTests(unittest.TestCase):
    def test_proves_ascii_mismatch_without_publishing_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = b"test-secret"
            secret_path = root / "secret"
            secret_path.write_bytes(secret)
            body = '{"event":"payment_link.paid","notes":{"text":"₹ മലയാളം"}}'.encode()
            signature = hmac.new(secret, body, hashlib.sha256).hexdigest()
            capture = {
                "event": "payment_link.paid",
                "headers": {"X-Razorpay-Signature": signature},
                "signature_valid": True,
                "literal_non_ascii": True,
                "raw_body_base64": base64.b64encode(body).decode(),
            }
            (root / "capture-one.json").write_text(json.dumps(capture), encoding="utf-8")

            report = build_webhook_byte_evidence(root, secret_path)

            self.assertTrue(report["checks"]["exact_utf8_verifies_all_literal_non_ascii_deliveries"])
            self.assertTrue(report["checks"]["dotnet_ascii_fails_all_literal_non_ascii_deliveries"])
            serialized = json.dumps(report, ensure_ascii=False)
            self.assertNotIn("മലയാളം", serialized)
            self.assertNotIn(signature, serialized)


if __name__ == "__main__":
    unittest.main()
