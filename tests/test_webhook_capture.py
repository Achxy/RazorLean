# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import hashlib
import hmac
import tempfile
import unittest
from pathlib import Path

from razorproof.webhook_capture import ensure_secret, verify_signature


class WebhookCaptureTests(unittest.TestCase):
    def test_verifies_exact_raw_utf8_bytes(self) -> None:
        secret = b"test-secret"
        body = '{"notes":{"text":"₹ മലയാളം"}}'.encode()
        signature = hmac.new(secret, body, hashlib.sha256).hexdigest()
        self.assertTrue(verify_signature(body, signature, secret))
        self.assertFalse(verify_signature(body + b"\n", signature, secret))

    def test_secret_is_created_once_with_private_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "secret"
            ensure_secret(path)
            first = path.read_text()
            ensure_secret(path)
            self.assertEqual(path.read_text(), first)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
