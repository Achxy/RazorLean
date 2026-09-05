# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import base64
import http.client
import json
import os
import uuid


class LiveGateError(RuntimeError):
    pass


def run_test_mode_refund_idempotency(
    *,
    payment_id: str,
    amount: int,
    execute: bool,
) -> dict[str, object]:
    """Execute one idempotent refund twice against Razorpay test mode.

    This intentionally creates one real test-mode refund. It refuses live keys,
    requires an explicit execution flag, and never returns credential material.
    """
    if not execute:
        raise LiveGateError("refusing mutation without --execute-test-mode")
    key_id = os.environ.get("RAZORPAY_KEY_ID", "")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
    if not key_id.startswith("rzp_test_"):
        raise LiveGateError("RAZORPAY_KEY_ID must be an rzp_test_ key; live keys are refused")
    if not key_secret:
        raise LiveGateError("RAZORPAY_KEY_SECRET is missing")
    if not payment_id.startswith("pay_"):
        raise LiveGateError("payment_id must start with pay_")
    if amount <= 0 or isinstance(amount, bool):
        raise LiveGateError("amount must be a positive integer subunit value")

    operation_key = f"razorproof-{uuid.uuid4()}"
    authorization = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
    body = json.dumps({"amount": amount, "notes": {"razorproof": "idempotency-poc"}})
    ids: list[str] = []
    for _ in range(2):
        connection = http.client.HTTPSConnection("api.razorpay.com", timeout=20)
        try:
            connection.request(
                "POST",
                f"/v1/payments/{payment_id}/refund",
                body=body,
                headers={
                    "Authorization": f"Basic {authorization}",
                    "Content-Type": "application/json",
                    "X-Refund-Idempotency": operation_key,
                },
            )
            response = connection.getresponse()
            payload = json.loads(response.read())
            if response.status >= 300:
                description = payload.get("error", {}).get("description", "Razorpay test request failed")
                raise LiveGateError(f"test-mode API returned {response.status}: {description}")
            ids.append(str(payload["id"]))
        finally:
            connection.close()
    return {
        "mode": "Razorpay test mode",
        "requests": 2,
        "unique_refund_ids": sorted(set(ids)),
        "one_effect": len(set(ids)) == 1,
        "payment_id": payment_id,
        "amount": amount,
    }
