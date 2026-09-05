# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import base64
import csv
import hashlib
import http.client
import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TestControlPlaneError(RuntimeError):
    pass


@dataclass(frozen=True)
class TestCredentials:
    key_id: str
    key_secret: str


def load_test_credentials_csv(path: Path) -> TestCredentials:
    """Load one Razorpay Test key pair without returning it in reports."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1 or set(rows[0]) != {"key_id", "key_secret"}:
        raise TestControlPlaneError("credential CSV must contain one key_id,key_secret row")
    key_id = rows[0]["key_id"].strip()
    key_secret = rows[0]["key_secret"].strip()
    if not key_id.startswith("rzp_test_"):
        raise TestControlPlaneError("only rzp_test_ credentials are accepted; live keys are refused")
    if not key_secret:
        raise TestControlPlaneError("test key secret is empty")
    return TestCredentials(key_id, key_secret)


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


class RazorpayTestClient:
    def __init__(self, credentials: TestCredentials) -> None:
        self._authorization = base64.b64encode(
            f"{credentials.key_id}:{credentials.key_secret}".encode()
        ).decode()

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        body = None if payload is None else json.dumps(payload, separators=(",", ":"))
        connection = http.client.HTTPSConnection("api.razorpay.com", timeout=30)
        try:
            headers = {
                "Authorization": f"Basic {self._authorization}",
                "Content-Type": "application/json",
                "User-Agent": "RazorProof-Test-Control-Plane/0.1",
            }
            if extra_headers:
                headers.update(extra_headers)
            connection.request(
                method,
                path,
                body=body,
                headers=headers,
            )
            response = connection.getresponse()
            raw = response.read()
            decoded = json.loads(raw) if raw else {}
            return response.status, decoded
        finally:
            connection.close()


def _description(payload: dict[str, Any]) -> str:
    return str(payload.get("error", {}).get("description", ""))


def _sum_refund_amounts(items: list[dict[str, Any]]) -> int:
    """Sum provider-returned subunits without silently coercing fractions."""
    total = 0
    for item in items:
        amount = item.get("amount")
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TestControlPlaneError(
                f"refund ledger returned a non-integer amount: {amount!r}"
            )
        total += amount
    return total


def run_order_boundary_matrix(credentials_path: Path, *, execute: bool) -> dict[str, Any]:
    """Create disposable Test-mode orders and record only redacted evidence."""
    if not execute:
        raise TestControlPlaneError("refusing Test control-plane mutations without --execute-test-mode")
    credentials = load_test_credentials_csv(credentials_path)
    client = RazorpayTestClient(credentials)
    run_id = uuid.uuid4().hex[:10]
    vectors: list[dict[str, Any]] = [
        {"name": "below_documented_minimum", "amount": 9, "expect": "reject"},
        {"name": "documented_minimum", "amount": 10, "expect": "accept"},
        {"name": "observed_below_minimum", "amount": 99, "expect": "reject"},
        {"name": "observed_minimum", "amount": 100, "expect": "accept"},
        {"name": "observed_minimum_plus_one", "amount": 101, "expect": "accept"},
        {
            "name": "generated_2_01_truncation",
            "amount": int(2.01 * 100),
            "intended_amount": 201,
            "expect": "accept",
        },
        {"name": "exact_2_01_control", "amount": 201, "expect": "accept"},
        {"name": "fractional_subunit", "amount": 100.75, "expect": "reject"},
    ]
    observations: list[dict[str, Any]] = []
    for index, vector in enumerate(vectors):
        request_payload = {
            "amount": vector["amount"],
            "currency": "INR",
            "receipt": f"rp-{run_id}-{index}",
            "notes": {"razorproof_vector": vector["name"]},
        }
        status, response = client.request("POST", "/v1/orders", request_payload)
        accepted = 200 <= status < 300
        expected_accept = vector["expect"] == "accept"
        observations.append({
            **vector,
            "http_status": status,
            "accepted": accepted,
            "expectation_met": accepted == expected_accept,
            "persisted_amount": response.get("amount") if accepted else None,
            "persisted_currency": response.get("currency") if accepted else None,
            "entity_status": response.get("status") if accepted else None,
            "entity_id_fingerprint": _fingerprint(str(response.get("id", ""))) if accepted else None,
            "error_description": _description(response) if not accepted else "",
        })
    by_name = {item["name"]: item for item in observations}
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_scope": "razorpay-test-control-plane",
        "real_money": False,
        "credential_mode": "rzp_test_ CSV; secret not persisted in evidence",
        "key_id_fingerprint": _fingerprint(credentials.key_id),
        "observations": observations,
        "checks": {
            "run_completed": all(item["http_status"] > 0 for item in observations),
            "all_expectations_met": all(item["expectation_met"] for item in observations),
            "documented_minimum_10_mismatch": not by_name["documented_minimum"]["accepted"],
            "observed_minimum_boundary_100": (
                not by_name["observed_below_minimum"]["accepted"]
                and by_name["observed_minimum"]["persisted_amount"] == 100
                and by_name["observed_minimum_plus_one"]["persisted_amount"] == 101
            ),
            "fractional_subunit_rejected": not by_name["fractional_subunit"]["accepted"],
            "below_minimum_rejected": not by_name["below_documented_minimum"]["accepted"],
            "generated_200_reached_server": by_name["generated_2_01_truncation"]["persisted_amount"] == 200,
            "exact_201_control_reached_server": by_name["exact_2_01_control"]["persisted_amount"] == 201,
        },
    }


def write_order_boundary_report(report: dict[str, Any], output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "order-boundary.json"
    markdown_path = output / "order-boundary.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Razorpay Test Control-Plane: Order Boundary",
        "",
        f"- Evidence scope: `{report['evidence_scope']}`",
        f"- Real money: `{report['real_money']}`",
        f"- All expectations met: `{report['checks']['all_expectations_met']}`",
        f"- Documented minimum `10` mismatch: `{report['checks']['documented_minimum_10_mismatch']}`",
        f"- Observed INR minimum boundary `100`: `{report['checks']['observed_minimum_boundary_100']}`",
        f"- Key fingerprint only: `{report['key_id_fingerprint']}`",
        "",
        "| Vector | Requested | Expected | HTTP | Accepted | Persisted | Result |",
        "|---|---:|---|---:|---|---:|---|",
    ]
    for item in report["observations"]:
        persisted = "" if item["persisted_amount"] is None else str(item["persisted_amount"])
        lines.append(
            f"| `{item['name']}` | `{item['amount']}` | `{item['expect']}` | "
            f"`{item['http_status']}` | `{item['accepted']}` | `{persisted}` | "
            f"`{'pass' if item['expectation_met'] else 'FAIL'}` |"
        )
    lines.extend([
        "",
        "Razorpay's current Create Order error documentation states that the minimum amount is `10`, but "
        "the Test control plane rejected 10 and 99 and accepted 100 and 101. The official MCP server also "
        "declares a minimum of 100. This is recorded as a Test-control-plane/documentation mismatch; it is "
        "not represented as a payment-processing defect.",
        "",
        "The generated-code vector is intentionally labelled by upstream intent: the official template expression "
        "`int(2.01 * 100)` produces 200, and Razorpay's Test API faithfully persists the submitted 200. "
        "The exact-decimal control submits and persists 201. This proves the undercharge reaches Razorpay's "
        "real Test control plane; it does not imply the Orders API caused the arithmetic error.",
        "",
        "Entity identifiers are stored only as one-way fingerprints. No API secret is written to this bundle.",
        "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def run_expanded_order_contract_matrix(
    credentials_path: Path,
    *,
    execute: bool,
) -> dict[str, Any]:
    """Exercise currency exponent, receipt, and integer boundaries in Test Mode."""
    if not execute:
        raise TestControlPlaneError(
            "refusing Test control-plane mutations without --execute-test-mode"
        )
    credentials = load_test_credentials_csv(credentials_path)
    client = RazorpayTestClient(credentials)
    run_id = uuid.uuid4().hex[:12]

    def create_order(name: str, amount: int | float, currency: str, receipt: str) -> dict[str, Any]:
        status, response = client.request("POST", "/v1/orders", {
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "notes": {"razorproof_vector": name},
        })
        accepted = 200 <= status < 300
        return {
            "name": name,
            "requested_amount": amount,
            "currency": currency,
            "http_status": status,
            "accepted": accepted,
            "persisted_amount": response.get("amount") if accepted else None,
            "persisted_currency": response.get("currency") if accepted else None,
            "entity_id_fingerprint": (
                _fingerprint(str(response.get("id", ""))) if accepted else None
            ),
            "error_description": _description(response) if not accepted else "",
        }

    receipt = f"rp-contract-{run_id}"
    receipt_first = create_order("duplicate_receipt_first", 100, "INR", receipt)
    receipt_second = create_order("duplicate_receipt_second", 100, "INR", receipt)
    jpy_generated = create_order(
        "generated_jpy_295_times_100", 29500, "JPY", f"rp-jg-{run_id}"
    )
    jpy_exact = create_order(
        "exact_jpy_295", 295, "JPY", f"rp-je-{run_id}"
    )
    kwd_generated = create_order(
        "generated_kwd_295_99_times_100", 29599, "KWD", f"rp-kg-{run_id}"
    )
    kwd_exact = create_order(
        "exact_kwd_295_990", 295990, "KWD", f"rp-ke-{run_id}"
    )
    fractional_order = create_order(
        "fractional_order_control", 100.75, "INR", f"rp-of-{run_id}"
    )

    link_status, link_response = client.request("POST", "/v1/payment_links", {
        "amount": 100.75,
        "currency": "INR",
        "accept_partial": False,
        "reference_id": f"rp-link-{run_id}",
        "description": "RazorProof fractional integer-boundary control",
        "notify": {"sms": False, "email": False},
        "reminder_enable": False,
    })
    fractional_link = {
        "name": "fractional_payment_link_control",
        "requested_amount": 100.75,
        "currency": "INR",
        "http_status": link_status,
        "accepted": 200 <= link_status < 300,
        "entity_id_fingerprint": (
            _fingerprint(str(link_response.get("id", "")))
            if 200 <= link_status < 300 else None
        ),
        "error_description": (
            _description(link_response) if not 200 <= link_status < 300 else ""
        ),
    }

    same_receipt_ids = {
        item["entity_id_fingerprint"]
        for item in (receipt_first, receipt_second)
        if item["entity_id_fingerprint"] is not None
    }
    observations = [
        receipt_first,
        receipt_second,
        jpy_generated,
        jpy_exact,
        kwd_generated,
        kwd_exact,
        fractional_order,
        fractional_link,
    ]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_scope": "razorpay-test-control-plane",
        "real_money": False,
        "credential_mode": "rzp_test_ CSV; secret not persisted in evidence",
        "key_id_fingerprint": _fingerprint(credentials.key_id),
        "observations": observations,
        "checks": {
            "duplicate_receipt_accepted_as_two_orders": (
                receipt_first["accepted"]
                and receipt_second["accepted"]
                and len(same_receipt_ids) == 2
            ),
            "generated_jpy_wrong_amount_persisted": (
                jpy_generated["persisted_amount"] == 29500
                and jpy_exact["persisted_amount"] == 295
            ),
            "generated_kwd_wrong_amount_persisted": (
                kwd_generated["persisted_amount"] == 29599
                and kwd_exact["persisted_amount"] == 295990
            ),
            "orders_reject_fractional_subunits": not fractional_order["accepted"],
            "payment_links_reject_fractional_subunits": not fractional_link["accepted"],
            "all_requests_completed": all(item["http_status"] > 0 for item in observations),
        },
        "classifications": {
            "currency_exponent": "generated-code defect; Orders API faithfully persists the wrong integer",
            "duplicate_receipt": "documentation/control-plane contradiction; not treated as a uniqueness outage",
            "fractional_controls": "negative controls showing correct rejection outside the Refund API fail-open path",
        },
    }


def write_expanded_order_contract_matrix(
    report: dict[str, Any], output: Path
) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "expanded-order-contract-matrix.json"
    markdown_path = output / "expanded-order-contract-matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Razorpay Test Control-Plane: Expanded Order Contract Matrix",
        "",
        f"- Real money: `{report['real_money']}`",
        f"- Requests completed: `{report['checks']['all_requests_completed']}`",
        f"- Generated JPY mismatch persisted: `{report['checks']['generated_jpy_wrong_amount_persisted']}`",
        f"- Generated KWD mismatch persisted: `{report['checks']['generated_kwd_wrong_amount_persisted']}`",
        f"- Duplicate receipt created two orders: `{report['checks']['duplicate_receipt_accepted_as_two_orders']}`",
        f"- Key fingerprint only: `{report['key_id_fingerprint']}`",
        "",
        "| Vector | Currency | Requested subunits | HTTP | Accepted | Persisted subunits |",
        "|---|---|---:|---:|---|---:|",
    ]
    for item in report["observations"]:
        persisted = item.get("persisted_amount")
        lines.append(
            f"| `{item['name']}` | `{item['currency']}` | `{item['requested_amount']}` | "
            f"`{item['http_status']}` | `{item['accepted']}` | "
            f"`{'' if persisted is None else persisted}` |"
        )
    lines.extend([
        "",
        "## Classification",
        "",
        "- The currency result is a generator defect, not an Orders API defect. The generated fixed ×100 rule submitted type-valid but economically wrong integers; Razorpay Test Mode persisted them exactly.",
        "- Reusing one receipt produced two distinct orders. This contradicts the current Create Order documentation's uniqueness wording, but it did not cause the hypothesised collision outage, so it is recorded only as contract/documentation drift.",
        "- Orders and Payment Links rejected fractional subunits. This is a negative control that makes the separate Refund API 100.75 to 100 acceptance an inconsistent fail-open path, not normal platform-wide coercion.",
        "",
        "Only one-way entity fingerprints are published. Credentials and raw provider identifiers are excluded.",
        "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def create_payment_link_fixture(
    credentials_path: Path,
    session_path: Path,
    *,
    amount: int = 201,
    execute: bool,
) -> dict[str, Any]:
    """Create one hosted Test-mode link with Unicode metadata."""
    if not execute:
        raise TestControlPlaneError("refusing Test control-plane mutation without --execute-test-mode")
    if isinstance(amount, bool) or amount < 100:
        raise TestControlPlaneError("payment-link amount must be an integer of at least 100 subunits")
    credentials = load_test_credentials_csv(credentials_path)
    client = RazorpayTestClient(credentials)
    reference = f"rp-{uuid.uuid4().hex[:18]}"
    status, response = client.request("POST", "/v1/payment_links", {
        "amount": amount,
        "currency": "INR",
        "accept_partial": False,
        "reference_id": reference,
        "description": f"RazorProof exact ₹{amount / 100:.2f} മലയാളം delivery probe",
        "notify": {"sms": False, "email": False},
        "reminder_enable": False,
        "notes": {
            "razorproof": "e2e-payment-link",
            "unicode_probe": "₹ മലയാളം",
        },
    })
    if not 200 <= status < 300:
        raise TestControlPlaneError(
            f"payment-link creation returned {status}: {_description(response)}"
        )
    session = {
        "mode": "razorpay-test-control-plane",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "payment_link_id": response["id"],
        "short_url": response["short_url"],
        "reference_id": reference,
        "amount": response["amount"],
        "currency": response["currency"],
        "status": response["status"],
    }
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    session_path.chmod(0o600)
    return {
        "mode": session["mode"],
        "real_money": False,
        "amount": session["amount"],
        "currency": session["currency"],
        "status": session["status"],
        "payment_link_id_fingerprint": _fingerprint(session["payment_link_id"]),
        "short_url": session["short_url"],
        "session_path": str(session_path),
    }


def refresh_payment_session(
    credentials_path: Path,
    session_path: Path,
) -> dict[str, Any]:
    """Resolve the captured payment for a private Test-mode session."""
    credentials = load_test_credentials_csv(credentials_path)
    client = RazorpayTestClient(credentials)
    session = json.loads(session_path.read_text(encoding="utf-8"))
    link_id = str(session.get("payment_link_id", ""))
    if not link_id.startswith("plink_"):
        raise TestControlPlaneError("private session has no valid payment_link_id")

    status, link = client.request("GET", f"/v1/payment_links/{link_id}")
    if not 200 <= status < 300:
        raise TestControlPlaneError(
            f"payment-link fetch returned {status}: {_description(link)}"
        )

    candidates: list[dict[str, Any]] = []
    embedded = link.get("payments")
    if isinstance(embedded, list):
        candidates.extend(item for item in embedded if isinstance(item, dict))

    created_at = session.get("created_at")
    if isinstance(created_at, str):
        lower_bound = int(datetime.fromisoformat(created_at).timestamp()) - 60
    else:
        lower_bound = int(time.time()) - 86400
    payment_status, payments = client.request(
        "GET", f"/v1/payments?from={lower_bound}&count=100"
    )
    if 200 <= payment_status < 300:
        items = payments.get("items", [])
        if isinstance(items, list):
            candidates.extend(item for item in items if isinstance(item, dict))

    seen: set[str] = set()
    matching: list[dict[str, Any]] = []
    for payment in candidates:
        payment_id = str(payment.get("id", ""))
        if not payment_id.startswith("pay_") or payment_id in seen:
            continue
        seen.add(payment_id)
        notes = payment.get("notes")
        belongs_to_fixture = (
            payment.get("payment_link_id") == link_id
            or (isinstance(notes, dict) and notes.get("razorproof") == "e2e-payment-link")
        )
        if belongs_to_fixture:
            matching.append(payment)

    if not matching:
        return {
            "payment_found": False,
            "payment_link_status": link.get("status"),
            "payment_link_id_fingerprint": _fingerprint(link_id),
        }

    matching.sort(key=lambda item: int(item.get("created_at", 0)), reverse=True)
    payment = matching[0]
    session.update({
        "payment_id": payment["id"],
        "payment_status": payment.get("status"),
        "payment_amount": payment.get("amount"),
        "payment_currency": payment.get("currency"),
        "payment_captured": payment.get("captured"),
        "payment_link_status": link.get("status"),
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    })
    session_path.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    session_path.chmod(0o600)
    return {
        "payment_found": True,
        "payment_id_fingerprint": _fingerprint(str(payment["id"])),
        "status": payment.get("status"),
        "captured": payment.get("captured"),
        "amount": payment.get("amount"),
        "currency": payment.get("currency"),
        "payment_link_status": link.get("status"),
    }


def run_refund_header_idempotency(
    credentials_path: Path,
    session_path: Path,
    *,
    amount: int,
    execute: bool,
) -> dict[str, Any]:
    """Send the same Test refund twice with one explicit operation identity."""
    if not execute:
        raise TestControlPlaneError("refusing Test refund mutation without --execute-test-mode")
    if isinstance(amount, bool) or amount <= 0:
        raise TestControlPlaneError("refund amount must be a positive integer")
    credentials = load_test_credentials_csv(credentials_path)
    client = RazorpayTestClient(credentials)
    session = json.loads(session_path.read_text(encoding="utf-8"))
    payment_id = str(session.get("payment_id", ""))
    if not payment_id.startswith("pay_"):
        raise TestControlPlaneError("refresh the private session after a captured Test payment first")
    if session.get("payment_status") != "captured" and session.get("payment_captured") is not True:
        raise TestControlPlaneError("refund proof requires a captured Test payment")

    operation_key = f"razorproof_{uuid.uuid4().hex}"
    payload = {
        "amount": amount,
        "notes": {"razorproof": "header-idempotency-e2e"},
    }
    observations: list[dict[str, Any]] = []
    for attempt in range(1, 3):
        status, response = client.request(
            "POST",
            f"/v1/payments/{payment_id}/refund",
            payload,
            {"X-Refund-Idempotency": operation_key},
        )
        accepted = 200 <= status < 300
        observations.append({
            "attempt": attempt,
            "http_status": status,
            "accepted": accepted,
            "refund_id_fingerprint": (
                _fingerprint(str(response.get("id", ""))) if accepted else None
            ),
            "amount": response.get("amount") if accepted else None,
            "status": response.get("status") if accepted else None,
            "error_description": _description(response) if not accepted else "",
        })
    fingerprints = {
        item["refund_id_fingerprint"]
        for item in observations
        if item["refund_id_fingerprint"] is not None
    }
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_scope": "razorpay-test-control-plane",
        "real_money": False,
        "mechanism": "X-Refund-Idempotency",
        "payment_id_fingerprint": _fingerprint(payment_id),
        "requested_amount": amount,
        "observations": observations,
        "checks": {
            "both_requests_accepted": all(item["accepted"] for item in observations),
            "one_refund_effect": len(fingerprints) == 1,
            "amount_preserved": all(
                item["amount"] == amount for item in observations if item["accepted"]
            ),
        },
    }
    session["refund_header_probe"] = {
        "executed_at": report["created_at"],
        "amount": amount,
        "one_refund_effect": report["checks"]["one_refund_effect"],
    }
    session_path.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    session_path.chmod(0o600)
    return report


def write_refund_report(report: dict[str, Any], output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "refund-header-idempotency.json"
    markdown_path = output / "refund-header-idempotency.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Razorpay Test Control-Plane: Refund Header Idempotency",
        "",
        f"- Real money: `{report['real_money']}`",
        f"- Requests accepted: `{report['checks']['both_requests_accepted']}`",
        f"- One refund effect: `{report['checks']['one_refund_effect']}`",
        f"- Amount preserved: `{report['checks']['amount_preserved']}`",
        f"- Payment fingerprint: `{report['payment_id_fingerprint']}`",
        "",
        "| Attempt | HTTP | Accepted | Refund fingerprint | Amount | Status |",
        "|---:|---:|---|---|---:|---|",
    ]
    for item in report["observations"]:
        lines.append(
            f"| `{item['attempt']}` | `{item['http_status']}` | `{item['accepted']}` | "
            f"`{item['refund_id_fingerprint'] or ''}` | `{item['amount'] or ''}` | "
            f"`{item['status'] or ''}` |"
        )
    lines.extend([
        "",
        "This is a Razorpay Test Mode control-plane result. Repeating the same body with the same "
        "`X-Refund-Idempotency` value should return the same refund identity and create one effect. "
        "It validates the provider mechanism and supports classifying missing exposure in a wrapper as a "
        "safety/discoverability gap rather than a broken Razorpay refund API.",
        "",
        "Only one-way entity fingerprints are published. Credentials and raw provider identifiers remain "
        "in the private ignored session file.",
        "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def run_refund_identity_matrix(
    credentials_path: Path,
    session_path: Path,
    *,
    execute: bool,
) -> dict[str, Any]:
    """Exercise refund boundaries and identities, then close the payment."""
    if not execute:
        raise TestControlPlaneError("refusing Test refund mutation without --execute-test-mode")
    credentials = load_test_credentials_csv(credentials_path)
    client = RazorpayTestClient(credentials)
    session = json.loads(session_path.read_text(encoding="utf-8"))
    payment_id = str(session.get("payment_id", ""))
    if not payment_id.startswith("pay_"):
        raise TestControlPlaneError("private session has no captured Test payment")

    before_status, before_payload = client.request(
        "GET", f"/v1/payments/{payment_id}/refunds"
    )
    if not 200 <= before_status < 300:
        raise TestControlPlaneError(
            f"refund preflight returned {before_status}: {_description(before_payload)}"
        )
    before = before_payload.get("items", [])
    before_total = _sum_refund_amounts(before)
    payment_amount = int(session.get("payment_amount", 0))
    available = payment_amount - before_total
    if available < 500:
        raise TestControlPlaneError(
            f"identity matrix requires at least 500 refundable subunits; observed {available}"
        )

    def post(
        payload: dict[str, Any], headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        status, response = client.request(
            "POST", f"/v1/payments/{payment_id}/refund", payload, headers
        )
        accepted = 200 <= status < 300
        return {
            "http_status": status,
            "accepted": accepted,
            "refund_id_fingerprint": (
                _fingerprint(str(response.get("id", ""))) if accepted else None
            ),
            "amount": response.get("amount") if accepted else None,
            "status": response.get("status") if accepted else None,
            "error_description": _description(response) if not accepted else "",
        }

    below_minimum = post({
        "amount": 99,
        "notes": {"razorproof": "refund-below-minimum"},
    })
    fractional = post({
        "amount": 100.75,
        "notes": {"razorproof": "refund-fractional-subunit"},
    })
    over_refund = post({
        "amount": available + 1,
        "notes": {"razorproof": "refund-over-payment"},
    })

    header_key = f"razorproof_{uuid.uuid4().hex}"
    header_first = post(
        {"amount": 100, "notes": {"razorproof": "header-body-mismatch"}},
        {"X-Refund-Idempotency": header_key},
    )
    header_changed = post(
        {"amount": 200, "notes": {"razorproof": "header-body-mismatch"}},
        {"X-Refund-Idempotency": header_key},
    )

    receipt = f"rp_{uuid.uuid4().hex}"
    receipt_body = {
        "amount": 100,
        "receipt": receipt,
        "notes": {"razorproof": "receipt-identity"},
    }
    receipt_first = post(receipt_body)
    receipt_retry = post(receipt_body)

    unkeyed_body = {
        "amount": 100,
        "notes": {"razorproof": "unkeyed-retry-control"},
    }
    unkeyed_first = post(unkeyed_body)
    unkeyed_retry = post(unkeyed_body)

    mid_status, mid_payload = client.request(
        "GET", f"/v1/payments/{payment_id}/refunds"
    )
    if not 200 <= mid_status < 300:
        raise TestControlPlaneError(
            f"refund reconciliation returned {mid_status}: {_description(mid_payload)}"
        )
    mid = mid_payload.get("items", [])
    mid_total = _sum_refund_amounts(mid)
    final_amount = payment_amount - mid_total
    if final_amount < 100:
        raise TestControlPlaneError(
            f"matrix left {final_amount} refundable subunits, below the observed minimum"
        )
    final_key = f"razorproof_{uuid.uuid4().hex}"
    final_body = {
        "amount": final_amount,
        "notes": {"razorproof": "full-refund-idempotent-close"},
    }
    final_first = post(final_body, {"X-Refund-Idempotency": final_key})
    final_retry = post(final_body, {"X-Refund-Idempotency": final_key})

    after_status, after_payload = client.request(
        "GET", f"/v1/payments/{payment_id}/refunds"
    )
    after = after_payload.get("items", []) if 200 <= after_status < 300 else []
    after_total = _sum_refund_amounts(after)
    after_fingerprints = sorted(
        _fingerprint(str(item.get("id", ""))) for item in after
    )
    unkeyed_ids = {
        item["refund_id_fingerprint"]
        for item in (unkeyed_first, unkeyed_retry)
        if item["refund_id_fingerprint"] is not None
    }
    final_ids = {
        item["refund_id_fingerprint"]
        for item in (final_first, final_retry)
        if item["refund_id_fingerprint"] is not None
    }
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_scope": "razorpay-test-control-plane",
        "real_money": False,
        "payment_id_fingerprint": _fingerprint(payment_id),
        "before": {
            "refund_count": len(before),
            "refunded_amount": before_total,
        },
        "boundary_rejections": {
            "below_minimum": below_minimum,
            "fractional_subunit": fractional,
            "over_refund": over_refund,
        },
        "header_same_key_changed_body": {
            "first": header_first,
            "changed_body_retry": header_changed,
            "changed_body_rejected": (
                header_first["accepted"] and not header_changed["accepted"]
            ),
        },
        "receipt_retry": {
            "first": receipt_first,
            "retry": receipt_retry,
            "duplicate_prevented": (
                receipt_first["accepted"] and not receipt_retry["accepted"]
            ),
        },
        "unkeyed_retry": {
            "first": unkeyed_first,
            "retry": unkeyed_retry,
            "two_distinct_effects": (
                unkeyed_first["accepted"]
                and unkeyed_retry["accepted"]
                and len(unkeyed_ids) == 2
            ),
        },
        "idempotent_full_refund": {
            "amount": final_amount,
            "first": final_first,
            "retry": final_retry,
            "one_effect": (
                final_first["accepted"]
                and final_retry["accepted"]
                and len(final_ids) == 1
            ),
        },
        "mid_reconciliation": {
            "http_status": mid_status,
            "refund_count": len(mid),
            "refunded_amount": mid_total,
            "remaining_amount": final_amount,
        },
        "after": {
            "http_status": after_status,
            "refund_count": len(after),
            "refunded_amount": after_total,
            "refund_id_fingerprints": after_fingerprints,
        },
    }
    report["checks"] = {
        "below_minimum_rejected": not below_minimum["accepted"],
        "fractional_subunit_rejected": not fractional["accepted"],
        "over_refund_rejected": not over_refund["accepted"],
        "header_changed_body_rejected": report["header_same_key_changed_body"]["changed_body_rejected"],
        "receipt_duplicate_prevented": report["receipt_retry"]["duplicate_prevented"],
        "unkeyed_retry_created_two_effects": report["unkeyed_retry"]["two_distinct_effects"],
        "idempotent_full_refund_one_effect": report["idempotent_full_refund"]["one_effect"],
        "payment_fully_refunded": after_total == payment_amount,
    }
    session["refund_identity_matrix"] = {
        "executed_at": report["created_at"],
        **report["checks"],
    }
    session_path.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    session_path.chmod(0o600)
    return report


def run_refund_idempotent_close(
    credentials_path: Path,
    session_path: Path,
    *,
    mechanism: str = "header",
    execute: bool,
) -> dict[str, Any]:
    """Reconcile a partially refunded Test payment, then close it exactly once."""
    if not execute:
        raise TestControlPlaneError("refusing Test refund mutation without --execute-test-mode")
    if mechanism not in {"header", "receipt"}:
        raise TestControlPlaneError("close mechanism must be header or receipt")
    credentials = load_test_credentials_csv(credentials_path)
    client = RazorpayTestClient(credentials)
    session = json.loads(session_path.read_text(encoding="utf-8"))
    payment_id = str(session.get("payment_id", ""))
    if not payment_id.startswith("pay_"):
        raise TestControlPlaneError("private session has no captured Test payment")
    payment_amount = session.get("payment_amount")
    if isinstance(payment_amount, bool) or not isinstance(payment_amount, int):
        raise TestControlPlaneError("private session has no integer payment amount")

    before_status, before_payload = client.request(
        "GET", f"/v1/payments/{payment_id}/refunds"
    )
    if not 200 <= before_status < 300:
        raise TestControlPlaneError(
            f"refund preflight returned {before_status}: {_description(before_payload)}"
        )
    before = before_payload.get("items", [])
    before_total = _sum_refund_amounts(before)
    remaining = payment_amount - before_total
    if remaining < 100:
        raise TestControlPlaneError(
            f"idempotent close requires at least 100 refundable subunits; observed {remaining}"
        )

    operation_key = f"razorproof_{uuid.uuid4().hex}"
    body = {
        "amount": remaining,
        "notes": {"razorproof": "reconciled-idempotent-close"},
    }
    headers: dict[str, str] | None = None
    if mechanism == "header":
        headers = {"X-Refund-Idempotency": operation_key}
    else:
        body["receipt"] = operation_key

    def post() -> dict[str, Any]:
        status, response = client.request(
            "POST",
            f"/v1/payments/{payment_id}/refund",
            body,
            headers,
        )
        accepted = 200 <= status < 300
        return {
            "http_status": status,
            "accepted": accepted,
            "refund_id_fingerprint": (
                _fingerprint(str(response.get("id", ""))) if accepted else None
            ),
            "amount": response.get("amount") if accepted else None,
            "status": response.get("status") if accepted else None,
            "error_description": _description(response) if not accepted else "",
        }

    first = post()
    retry = post()
    after_status, after_payload = client.request(
        "GET", f"/v1/payments/{payment_id}/refunds"
    )
    if not 200 <= after_status < 300:
        raise TestControlPlaneError(
            f"refund postflight returned {after_status}: {_description(after_payload)}"
        )
    after = after_payload.get("items", [])
    after_total = _sum_refund_amounts(after)
    effect_ids = {
        item["refund_id_fingerprint"]
        for item in (first, retry)
        if item["refund_id_fingerprint"] is not None
    }
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_scope": "razorpay-test-control-plane",
        "real_money": False,
        "mechanism": mechanism,
        "payment_id_fingerprint": _fingerprint(payment_id),
        "before": {
            "refund_count": len(before),
            "refunded_amount": before_total,
            "remaining_amount": remaining,
        },
        "requests": {"first": first, "retry": retry},
        "after": {
            "refund_count": len(after),
            "refunded_amount": after_total,
        },
        "checks": {
            "first_request_accepted": first["accepted"],
            "retry_safely_identified": (
                first["accepted"]
                and (
                    (mechanism == "header" and retry["accepted"] and len(effect_ids) == 1)
                    or (mechanism == "receipt" and not retry["accepted"])
                )
            ),
            "one_refund_effect": (
                first["accepted"]
                and len(after) == len(before) + 1
            ),
            "remaining_amount_preserved": (
                first["amount"] == remaining
                and (not retry["accepted"] or retry["amount"] == remaining)
            ),
            "payment_fully_refunded": after_total == payment_amount,
        },
    }
    session["refund_idempotent_close"] = {
        "executed_at": report["created_at"],
        **report["checks"],
    }
    session_path.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    session_path.chmod(0o600)
    return report


def write_refund_idempotent_close(
    report: dict[str, Any], output: Path
) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "refund-idempotent-close.json"
    markdown_path = output / "refund-idempotent-close.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    first = report["requests"]["first"]
    retry = report["requests"]["retry"]
    lines = [
        "# Razorpay Test Control-Plane: Reconciled Idempotent Close",
        "",
        f"- Real money: `{report['real_money']}`",
        f"- Identity mechanism: `{report['mechanism']}`",
        f"- Reconciled remaining amount: `{report['before']['remaining_amount']}` subunits",
        f"- First request accepted: `{report['checks']['first_request_accepted']}`",
        f"- Retry safely identified: `{report['checks']['retry_safely_identified']}`",
        f"- One refund effect: `{report['checks']['one_refund_effect']}`",
        f"- Payment fully refunded: `{report['checks']['payment_fully_refunded']}`",
        "",
        "| Attempt | HTTP | Refund fingerprint | Amount | Status |",
        "|---|---:|---|---:|---|",
        f"| first | `{first['http_status']}` | `{first['refund_id_fingerprint'] or ''}` | `{first['amount'] or ''}` | `{first['status'] or ''}` |",
        f"| retry | `{retry['http_status']}` | `{retry['refund_id_fingerprint'] or ''}` | `{retry['amount'] or ''}` | `{retry['status'] or ''}` |",
        "",
        "The remaining amount was derived from a fresh provider ledger read. The identical retry used "
        "one stable operation identity. Header identity should return the same effect; receipt identity "
        "should reject the duplicate. Either behavior must leave exactly one new refund in the ledger.",
        "",
    ]
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def fetch_redacted_refund_ledger(
    credentials_path: Path,
    session_path: Path,
) -> dict[str, Any]:
    """Fetch a private Test payment and publish only labelled, fingerprinted refund state."""
    credentials = load_test_credentials_csv(credentials_path)
    client = RazorpayTestClient(credentials)
    session = json.loads(session_path.read_text(encoding="utf-8"))
    payment_id = str(session.get("payment_id", ""))
    if not payment_id.startswith("pay_"):
        raise TestControlPlaneError("private session has no captured Test payment")

    payment_status, payment = client.request("GET", f"/v1/payments/{payment_id}")
    if not 200 <= payment_status < 300:
        raise TestControlPlaneError(
            f"payment fetch returned {payment_status}: {_description(payment)}"
        )
    refunds_status, refunds_payload = client.request(
        "GET", f"/v1/payments/{payment_id}/refunds"
    )
    if not 200 <= refunds_status < 300:
        raise TestControlPlaneError(
            f"refund ledger returned {refunds_status}: {_description(refunds_payload)}"
        )
    refunds = refunds_payload.get("items", [])
    refunded_total = _sum_refund_amounts(refunds)
    entries: list[dict[str, Any]] = []
    for item in refunds:
        notes = item.get("notes")
        label = notes.get("razorproof") if isinstance(notes, dict) else None
        entries.append({
            "refund_id_fingerprint": _fingerprint(str(item.get("id", ""))),
            "label": label,
            "amount": item.get("amount"),
            "status": item.get("status"),
            "speed_requested": item.get("speed_requested"),
            "speed_processed": item.get("speed_processed"),
            "receipt_present": bool(item.get("receipt")),
        })
    entries.sort(key=lambda item: (str(item["label"]), item["refund_id_fingerprint"]))
    payment_amount = payment.get("amount")
    fractional_entries = [
        item for item in entries if item["label"] == "refund-fractional-subunit"
    ]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_scope": "razorpay-test-control-plane",
        "real_money": False,
        "payment_id_fingerprint": _fingerprint(payment_id),
        "payment": {
            "status": payment.get("status"),
            "amount": payment_amount,
            "amount_refunded": payment.get("amount_refunded"),
        },
        "refund_count": len(entries),
        "refunded_total": refunded_total,
        "refunds": entries,
        "checks": {
            "all_refunds_processed": bool(entries) and all(
                item["status"] == "processed" for item in entries
            ),
            "payment_fully_refunded": (
                isinstance(payment_amount, int)
                and refunded_total == payment_amount
                and payment.get("amount_refunded") == payment_amount
                and payment.get("status") == "refunded"
            ),
            "fractional_request_persisted_as_integer_100": (
                len(fractional_entries) == 1
                and fractional_entries[0]["amount"] == 100
                and fractional_entries[0]["status"] == "processed"
            ),
        },
    }


def write_refund_ledger(report: dict[str, Any], output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "refund-ledger.json"
    markdown_path = output / "refund-ledger.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Razorpay Test Control-Plane: Redacted Refund Ledger",
        "",
        f"- Payment status: `{report['payment']['status']}`",
        f"- Payment amount: `{report['payment']['amount']}` subunits",
        f"- Provider amount refunded: `{report['payment']['amount_refunded']}` subunits",
        f"- Refund ledger sum: `{report['refunded_total']}` subunits",
        f"- All refunds processed: `{report['checks']['all_refunds_processed']}`",
        f"- Payment fully refunded: `{report['checks']['payment_fully_refunded']}`",
        f"- Fractional request persisted as integer 100: `{report['checks']['fractional_request_persisted_as_integer_100']}`",
        "",
        "| Label | Amount | Status | Refund fingerprint | Receipt present |",
        "|---|---:|---|---|---|",
    ]
    for item in report["refunds"]:
        lines.append(
            f"| `{item['label'] or ''}` | `{item['amount']}` | `{item['status']}` | "
            f"`{item['refund_id_fingerprint']}` | `{item['receipt_present']}` |"
        )
    lines.extend([
        "",
        "The `refund-fractional-subunit` row is the durable effect of the JSON request amount `100.75` "
        "recorded in `refund-identity-matrix.json`: HTTP 200 returned integer amount `100`, and the "
        "provider ledger later reached `processed`. Razorpay's current API contract types `amount` as "
        "an integer in the currency's smallest unit, so accepting and truncating this value is recorded "
        "as a Test control-plane input-validation defect, not as an intentional fractional-currency feature.",
        "",
        "Provider identifiers are represented only by one-way fingerprints.",
        "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def run_refund_fractional_dust_probe(
    credentials_path: Path,
    session_path: Path,
    *,
    execute: bool,
) -> dict[str, Any]:
    """Characterize fractional coercion and the resulting one-subunit remainder."""
    if not execute:
        raise TestControlPlaneError("refusing Test refund mutation without --execute-test-mode")
    credentials = load_test_credentials_csv(credentials_path)
    client = RazorpayTestClient(credentials)
    session = json.loads(session_path.read_text(encoding="utf-8"))
    payment_id = str(session.get("payment_id", ""))
    if not payment_id.startswith("pay_"):
        raise TestControlPlaneError("private session has no captured Test payment")
    payment_amount = session.get("payment_amount")
    if isinstance(payment_amount, bool) or not isinstance(payment_amount, int):
        raise TestControlPlaneError("private session has no integer payment amount")

    def fetch_state() -> tuple[dict[str, Any], list[dict[str, Any]], int]:
        status, payment = client.request("GET", f"/v1/payments/{payment_id}")
        if not 200 <= status < 300:
            raise TestControlPlaneError(
                f"payment fetch returned {status}: {_description(payment)}"
            )
        refunds_status, payload = client.request(
            "GET", f"/v1/payments/{payment_id}/refunds"
        )
        if not 200 <= refunds_status < 300:
            raise TestControlPlaneError(
                f"refund ledger returned {refunds_status}: {_description(payload)}"
            )
        refunds = payload.get("items", [])
        return payment, refunds, _sum_refund_amounts(refunds)

    def post(
        payload: dict[str, Any], operation_key: str | None = None
    ) -> dict[str, Any]:
        headers = (
            {"X-Refund-Idempotency": operation_key}
            if operation_key is not None
            else None
        )
        status, response = client.request(
            "POST",
            f"/v1/payments/{payment_id}/refund",
            payload,
            headers,
        )
        accepted = 200 <= status < 300
        return {
            "http_status": status,
            "accepted": accepted,
            "refund_id_fingerprint": (
                _fingerprint(str(response.get("id", ""))) if accepted else None
            ),
            "amount": response.get("amount") if accepted else None,
            "status": response.get("status") if accepted else None,
            "error_description": _description(response) if not accepted else "",
        }

    before_payment, before_refunds, before_total = fetch_state()
    available = payment_amount - before_total
    if available != 101:
        raise TestControlPlaneError(
            f"dust probe requires exactly 101 refundable subunits; observed {available}"
        )

    fractional = post(
        {
            "amount": 100.75,
            "notes": {"razorproof": "fractional-dust-coercion"},
        }
    )
    mid_payment, mid_refunds, mid_total = fetch_state()
    explicit_dust = post(
        {
            "amount": 1,
            "notes": {"razorproof": "explicit-one-subunit-remainder"},
        }
    )
    header_close_key = f"razorproof_{uuid.uuid4().hex}"
    header_close_body = {
        "notes": {"razorproof": "header-omitted-amount-dust-close"}
    }
    header_close_first = post(header_close_body, header_close_key)
    header_close_retry = post(header_close_body, header_close_key)
    receipt = f"rp_{uuid.uuid4().hex}"
    receipt_close_body = {
        "receipt": receipt,
        "notes": {"razorproof": "receipt-omitted-amount-dust-close"},
    }
    receipt_close_first = post(receipt_close_body)
    receipt_close_retry = post(receipt_close_body)
    final_payment, final_refunds, final_total = fetch_state()
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_scope": "razorpay-test-control-plane",
        "real_money": False,
        "payment_id_fingerprint": _fingerprint(payment_id),
        "before": {
            "payment_status": before_payment.get("status"),
            "refund_count": len(before_refunds),
            "refunded_amount": before_total,
            "remaining_amount": available,
        },
        "fractional_request": {
            "requested_amount": 100.75,
            "response": fractional,
        },
        "after_fractional": {
            "payment_status": mid_payment.get("status"),
            "provider_amount_refunded": mid_payment.get("amount_refunded"),
            "refund_count": len(mid_refunds),
            "ledger_total": mid_total,
            "remaining_amount": payment_amount - mid_total,
        },
        "explicit_one_subunit_request": explicit_dust,
        "header_omitted_amount_close": {
            "first": header_close_first,
            "retry": header_close_retry,
        },
        "receipt_omitted_amount_close": {
            "first": receipt_close_first,
            "retry": receipt_close_retry,
        },
        "final": {
            "payment_status": final_payment.get("status"),
            "provider_amount_refunded": final_payment.get("amount_refunded"),
            "refund_count": len(final_refunds),
            "ledger_total": final_total,
        },
    }
    report["checks"] = {
        "fractional_request_accepted_and_truncated": (
            fractional["accepted"] and fractional["amount"] == 100
        ),
        "one_subunit_residual_created": (
            mid_total == before_total + 100
            and payment_amount - mid_total == 1
            and mid_payment.get("status") == "captured"
        ),
        "explicit_one_subunit_refund_rejected": not explicit_dust["accepted"],
        "header_omitted_amount_rejected": (
            not header_close_first["accepted"]
            and not header_close_retry["accepted"]
        ),
        "receipt_omitted_amount_closed_residual": (
            receipt_close_first["accepted"]
            and receipt_close_first["amount"] == 1
            and final_total == payment_amount
            and final_payment.get("status") == "refunded"
        ),
        "receipt_retry_duplicate_prevented": (
            receipt_close_first["accepted"]
            and not receipt_close_retry["accepted"]
        ),
    }
    session["refund_fractional_dust_probe"] = {
        "executed_at": report["created_at"],
        **report["checks"],
    }
    session_path.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    session_path.chmod(0o600)
    return report


def write_refund_fractional_dust_probe(
    report: dict[str, Any], output: Path
) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "refund-fractional-dust.json"
    markdown_path = output / "refund-fractional-dust.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    fractional = report["fractional_request"]["response"]
    explicit = report["explicit_one_subunit_request"]
    header_close = report["header_omitted_amount_close"]
    receipt_close = report["receipt_omitted_amount_close"]
    fractional_result = (
        "accepted after coercion"
        if fractional["accepted"]
        else fractional["error_description"]
    )
    receipt_result = (
        "full remaining amount"
        if receipt_close["first"]["accepted"]
        else receipt_close["first"]["error_description"]
    )
    lines = [
        "# Razorpay Test Control-Plane: Fractional Refund Dust",
        "",
        f"- Fractional `100.75` accepted and persisted as `100`: `{report['checks']['fractional_request_accepted_and_truncated']}`",
        f"- One-subunit residual created: `{report['checks']['one_subunit_residual_created']}`",
        f"- Explicit one-subunit refund rejected: `{report['checks']['explicit_one_subunit_refund_rejected']}`",
        f"- Header-idempotent omitted amount rejected: `{report['checks']['header_omitted_amount_rejected']}`",
        f"- Receipt-identified omitted amount closed the residual: `{report['checks']['receipt_omitted_amount_closed_residual']}`",
        f"- Receipt retry prevented a duplicate: `{report['checks']['receipt_retry_duplicate_prevented']}`",
        "",
        "| Step | Requested amount | HTTP | Returned amount | Result |",
        "|---|---:|---:|---:|---|",
        f"| fractional | `100.75` | `{fractional['http_status']}` | `{fractional['amount']}` | `{fractional_result}` |",
        f"| explicit residual | `1` | `{explicit['http_status']}` | `` | `{explicit['error_description']}` |",
        f"| header-idempotent omitted amount | omitted | `{header_close['first']['http_status']}` | `{header_close['first']['amount']}` | `{header_close['first']['error_description']}` |",
        f"| receipt-identified omitted amount | omitted | `{receipt_close['first']['http_status']}` | `{receipt_close['first']['amount']}` | `{receipt_result}` |",
        f"| identical receipt retry | omitted | `{receipt_close['retry']['http_status']}` | `` | `{receipt_close['retry']['error_description']}` |",
        "",
        "On this fixture, only 101 subunits remained. Razorpay rejected the same `100.75` fractional "
        "request before creating an effect, so no one-subunit residual was produced. The explicit one-subunit "
        "request and both omitted-amount identity forms were also rejected. This negative control disproves "
        "the proposed stranded-dust story and shows that the fractional fail-open path is conditional on "
        "provider state or validation routing; the broader claim is deliberately not made.",
        "",
        "Provider identifiers are represented only by one-way fingerprints.",
        "",
    ]
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def write_refund_identity_matrix(report: dict[str, Any], output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "refund-identity-matrix.json"
    markdown_path = output / "refund-identity-matrix.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Razorpay Test Control-Plane: Refund Identity Matrix",
        "",
        f"- Real money: `{report['real_money']}`",
        f"- Below ₹1.00 rejected: `{report['checks']['below_minimum_rejected']}`",
        f"- Fractional subunit rejected: `{report['checks']['fractional_subunit_rejected']}`",
        f"- Over-refund rejected: `{report['checks']['over_refund_rejected']}`",
        f"- Same header with changed body rejected: `{report['checks']['header_changed_body_rejected']}`",
        f"- Duplicate receipt prevented: `{report['checks']['receipt_duplicate_prevented']}`",
        f"- Unkeyed retry created two effects: `{report['checks']['unkeyed_retry_created_two_effects']}`",
        f"- Final full-refund retry produced one effect: `{report['checks']['idempotent_full_refund_one_effect']}`",
        f"- Payment fully refunded: `{report['checks']['payment_fully_refunded']}`",
        "",
        "| Scenario | First HTTP | Retry HTTP | First effect | Retry effect | Interpretation |",
        "|---|---:|---:|---|---|---|",
    ]
    scenarios = [
        (
            "same header, changed body",
            report["header_same_key_changed_body"]["first"],
            report["header_same_key_changed_body"]["changed_body_retry"],
            "conflicting reuse rejected",
        ),
        (
            "stable receipt",
            report["receipt_retry"]["first"],
            report["receipt_retry"]["retry"],
            "duplicate prevented",
        ),
        (
            "no operation identity",
            report["unkeyed_retry"]["first"],
            report["unkeyed_retry"]["retry"],
            "two distinct refund intents",
        ),
        (
            "same header, full-refund retry",
            report["idempotent_full_refund"]["first"],
            report["idempotent_full_refund"]["retry"],
            "one final refund effect",
        ),
    ]
    for name, first, retry, interpretation in scenarios:
        lines.append(
            f"| {name} | `{first['http_status']}` | `{retry['http_status']}` | "
            f"`{first['refund_id_fingerprint'] or ''}` | `{retry['refund_id_fingerprint'] or ''}` | "
            f"{interpretation} |"
        )
    lines.extend([
        "",
        f"The fractional boundary request sent `100.75`, returned HTTP "
        f"`{report['boundary_rejections']['fractional_subunit']['http_status']}`, and the provider "
        f"returned amount `{report['boundary_rejections']['fractional_subunit']['amount']}`. "
        "Because the official contract requires an integer, HTTP 200 plus persisted 100 is a "
        "silent-coercion defect; it is not a successful boundary rejection.",
        "",
        "The unkeyed result is intentional provider behavior: without an operation identity, two requests "
        "represent two refund intents. The defect claim belongs only to wrappers or agent tools that hide "
        "the available identity mechanisms while encouraging automatic retries.",
        "",
        "Provider entity identifiers are represented only by one-way fingerprints.",
        "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
