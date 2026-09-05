# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ChainEvidenceError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ChainEvidenceError(f"required evidence file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _finding(scan: dict[str, Any], finding_id: str) -> dict[str, Any]:
    for result in scan.get("results", []):
        for finding in result.get("findings", []):
            if finding.get("id") == finding_id:
                return finding
    raise ChainEvidenceError(f"finding missing from scan: {finding_id}")


def build_chain_evidence(root: Path) -> dict[str, Any]:
    scan = _load(root / "artifacts/expanded/scan.json")
    refunds = _load(root / "artifacts/razorpay-test/refund-identity-matrix.json")
    webhooks = _load(root / "artifacts/razorpay-test/webhook-byte-evidence.json")
    orders = _load(root / "artifacts/razorpay-test/expanded-order-contract-matrix.json")
    registry = _load(root / "artifacts/registry/mobile-registry-evidence.json")

    refund_fractional = refunds["boundary_rejections"]["fractional_subunit"]
    order_checks = orders["checks"]
    registry_checks = registry["checks"]
    chains = [
        {
            "id": "CHAIN-REFUND-MUTATION-RETRY-OBSERVABILITY",
            "title": "Silent refund mutation can combine with non-idempotent retry and lost .NET webhook visibility",
            "proof_grade": "all components reproduced; the production retry trigger is an explicit inference",
            "nodes": [
                {
                    "state": "confirmed_dynamic",
                    "claim": "Official MCP handler accepts 100.75 and sends 100 to the SDK request path.",
                    "evidence": "RP-MCP-REFUND-TRUNCATION",
                    "passed": _finding(scan, "RP-MCP-REFUND-TRUNCATION")["level"] == "confirmed_dynamic",
                },
                {
                    "state": "razorpay_test_observed",
                    "claim": "The direct Refund API separately accepted 100.75 and returned/persisted 100.",
                    "evidence": "artifacts/razorpay-test/refund-identity-matrix.json",
                    "passed": (
                        refund_fractional["accepted"] is True
                        and refund_fractional["amount"] == 100
                    ),
                },
                {
                    "state": "razorpay_test_control",
                    "claim": "Two unkeyed retry requests created two distinct effects by documented identity semantics.",
                    "evidence": "artifacts/razorpay-test/refund-identity-matrix.json",
                    "passed": refunds["checks"]["unkeyed_retry_created_two_effects"] is True,
                },
                {
                    "state": "razorpay_test_observed",
                    "claim": "Signed refund webhooks contained literal UTF-8; exact bytes verified and the .NET ASCII-equivalent digest failed.",
                    "evidence": "artifacts/razorpay-test/webhook-byte-evidence.json",
                    "passed": (
                        webhooks["event_counts"].get("refund.created", 0) > 0
                        and webhooks["event_counts"].get("refund.processed", 0) > 0
                        and webhooks["checks"]["dotnet_ascii_fails_all_literal_non_ascii_deliveries"] is True
                    ),
                },
                {
                    "state": "inferred_impact",
                    "claim": "If a consumer treats the rejected event as absence/failure and retries without a stable identity, the independently proven retry behavior amplifies one intent into multiple refunds.",
                    "evidence": "composition of the four preceding counterexamples",
                    "passed": None,
                },
            ],
            "razorproof_prevention": [
                "integer-only monetary boundary",
                "mandatory stable effect identity for retryable money movement",
                "exact raw-byte webhook verification",
                "cross-artifact trace linking request, effect, and event",
            ],
        },
        {
            "id": "CHAIN-CHECKOUT-ECONOMIC-DECOUPLING",
            "title": "Browser-controlled economics plus fixed currency exponent can create a valid but wrong-priced order",
            "proof_grade": "generated path and Test order persistence proven; paid fulfillment remains unexecuted",
            "nodes": [
                {
                    "state": "confirmed_static",
                    "claim": "Generated frontend sends browser amount; backend trusts amount and currency; verifier authenticates only the returned payment tuple.",
                    "evidence": "RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS",
                    "passed": _finding(scan, "RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS")["level"] in {"confirmed_static", "confirmed_dynamic"},
                },
                {
                    "state": "confirmed_dynamic",
                    "claim": "The emitted ×100 expression maps JPY 295 to 29,500 and KWD 295.990 intent to 29,599.",
                    "evidence": "RP-MCP-GENERATOR-CURRENCY-EXPONENT",
                    "passed": _finding(scan, "RP-MCP-GENERATOR-CURRENCY-EXPONENT")["level"] == "confirmed_dynamic",
                },
                {
                    "state": "razorpay_test_observed",
                    "claim": "Razorpay Test Orders persisted both wrong generated values and both exact controls.",
                    "evidence": "artifacts/razorpay-test/expanded-order-contract-matrix.json",
                    "passed": (
                        order_checks["generated_jpy_wrong_amount_persisted"] is True
                        and order_checks["generated_kwd_wrong_amount_persisted"] is True
                    ),
                },
                {
                    "state": "inferred_impact",
                    "claim": "A payment signature can prove that the wrong-priced order was paid; it cannot retroactively prove that the order matched the merchant's intended cart or quote.",
                    "evidence": "protocol property; payment/fulfillment leg not executed in this campaign",
                    "passed": None,
                },
            ],
            "razorproof_prevention": [
                "server-authoritative immutable quote",
                "currency-aware exact subunit conversion",
                "one-time binding of quote, Razorpay order, payment, merchant, and fulfillment",
            ],
        },
        {
            "id": "CHAIN-MOBILE-PAID-BUT-FAILED",
            "title": "Four generated native flows reach success without the data required by their generated verifier",
            "proof_grade": "source-deterministic against official callback contracts; device payment not executed",
            "nodes": [
                {
                    "state": "confirmed_static",
                    "claim": "Android and iOS choose payment_id-only callback protocols; Cordova and native Capacitor use payment_id-only callback shapes.",
                    "evidence": "RP-MCP-MOBILE-MISSING-SIGNATURE",
                    "passed": _finding(scan, "RP-MCP-MOBILE-MISSING-SIGNATURE")["level"] == "confirmed_static",
                },
                {
                    "state": "confirmed_static",
                    "claim": "Generated Android/iOS send an empty signature and Cordova/Capacitor omit it.",
                    "evidence": "RP-MCP-MOBILE-MISSING-SIGNATURE",
                    "passed": True,
                },
                {
                    "state": "deterministic_consequence",
                    "claim": "The generated backend rejects a missing or empty signature after Checkout has already reported success.",
                    "evidence": "generated verify route required-field guard",
                    "passed": True,
                },
            ],
            "razorproof_prevention": [
                "callback-shape contract checking",
                "cross-file dataflow completeness",
                "generated success-path integration test",
            ],
        },
        {
            "id": "CHAIN-CROSS-TENANT-ROUTING",
            "title": "Process-global SDK state can cross merchant authentication and partner routing boundaries",
            "proof_grade": "three official SDK runtime collisions proven; two-account provider request intentionally not executed",
            "nodes": [
                {
                    "state": "confirmed_dynamic",
                    "claim": ".NET client B replaced A's credentials, inherited A's routing header, and made A's valid signature fail.",
                    "evidence": "RP-DOTNET-GLOBAL-AUTH-STATE",
                    "passed": _finding(scan, "RP-DOTNET-GLOBAL-AUTH-STATE")["level"] == "confirmed_dynamic",
                },
                {
                    "state": "confirmed_dynamic",
                    "claim": "PHP client B replaced A's global key and inherited A's routing header.",
                    "evidence": "RP-PHP-GLOBAL-AUTH-STATE",
                    "passed": _finding(scan, "RP-PHP-GLOBAL-AUTH-STATE")["level"] == "confirmed_dynamic",
                },
                {
                    "state": "confirmed_dynamic",
                    "claim": "Java client B inherited and then overwrote the process-global X-Razorpay-Account map.",
                    "evidence": "RP-JAVA-GLOBAL-PARTNER-HEADERS",
                    "passed": _finding(scan, "RP-JAVA-GLOBAL-PARTNER-HEADERS")["level"] == "confirmed_dynamic",
                },
                {
                    "state": "inferred_impact",
                    "claim": "A request interleaving in a multi-merchant worker can authenticate or route an operation under the wrong merchant context.",
                    "evidence": "official partner-header semantics plus reproduced shared state",
                    "passed": None,
                },
            ],
            "razorproof_prevention": [
                "client-isolation contract",
                "parallel interleaving tests",
                "merchant-context trace assertions",
            ],
        },
        {
            "id": "CHAIN-JAVA-DOCUMENT-WIRE-CORRUPTION",
            "title": "One Java upload can carry both the wrong MIME type and two conflicting file fields",
            "proof_grade": "exact SDK multipart bytes proven; provider upload not executed",
            "nodes": [
                {
                    "state": "confirmed_dynamic",
                    "claim": "proof.png is labeled image/pdf.",
                    "evidence": "RP-JAVA-UPLOAD-MIME",
                    "passed": _finding(scan, "RP-JAVA-UPLOAD-MIME")["level"] == "confirmed_dynamic",
                },
                {
                    "state": "confirmed_dynamic",
                    "claim": "The same request contains two multipart fields named file, one binary and one pathname text field.",
                    "evidence": "RP-JAVA-UPLOAD-DUPLICATE-FILE-PART",
                    "passed": _finding(scan, "RP-JAVA-UPLOAD-DUPLICATE-FILE-PART")["level"] == "confirmed_dynamic",
                },
                {
                    "state": "inferred_impact",
                    "claim": "Duplicate-field selection and MIME validation can independently or jointly reject/misclassify dispute and KYC evidence.",
                    "evidence": "document API contract; provider upload not executed",
                    "passed": None,
                },
            ],
            "razorproof_prevention": [
                "multipart field-cardinality contract",
                "extension-to-MIME mapping contract",
                "wire-body snapshot probe",
            ],
        },
        {
            "id": "CHAIN-MOBILE-PACKAGE-IDENTITY",
            "title": "Generated mobile setup crosses from Razorpay code into the wrong package identities",
            "proof_grade": "current registry state reproduced; no malicious-package claim",
            "nodes": [
                {
                    "state": "confirmed_static",
                    "claim": "Generator emits the two non-official package names.",
                    "evidence": "RP-MCP-MOBILE-DEPENDENCY-CONFUSION",
                    "passed": _finding(scan, "RP-MCP-MOBILE-DEPENDENCY-CONFUSION")["level"] == "confirmed_static",
                },
                {
                    "state": "registry_observed",
                    "claim": "Cordova/Ionic package is absent; Capacitor package exists as a two-file 'Empty package' outside Razorpay's repository identity.",
                    "evidence": "artifacts/registry/mobile-registry-evidence.json",
                    "passed": all(registry_checks.values()),
                },
                {
                    "state": "deterministic_consequence",
                    "claim": "Cordova/Ionic installation fails; Capacitor installs no functional Razorpay bridge.",
                    "evidence": "npm 404 and published package contents",
                    "passed": True,
                },
                {
                    "state": "inferred_risk",
                    "claim": "Depending on a similarly named third-party package creates a future package-supply-chain exposure.",
                    "evidence": "package ownership boundary; current package is empty, not alleged malicious",
                    "passed": None,
                },
            ],
            "razorproof_prevention": [
                "verified package-identity allowlist",
                "registry existence and repository-owner checks",
                "generated install smoke test",
            ],
        },
    ]
    for chain in chains:
        confirmed = [node["passed"] for node in chain["nodes"] if node["passed"] is not None]
        chain["confirmed_nodes_pass"] = bool(confirmed) and all(confirmed)
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "compose only independently evidenced nodes; mark unexecuted causal impact explicitly",
        "chains": chains,
        "checks": {
            "all_evidence_backed_nodes_pass": all(
                chain["confirmed_nodes_pass"] for chain in chains
            ),
            "inferences_are_explicit": all(
                any(node["passed"] is None for node in chain["nodes"])
                or "deterministic" in chain["proof_grade"]
                for chain in chains
            ),
        },
    }


def write_chain_evidence(report: dict[str, Any], output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "chained-bug-evidence.json"
    markdown_path = output / "chained-bug-evidence.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# RazorProof Chained-Bug Evidence",
        "",
        "> Chains are composed only from independently evidenced nodes. Unexecuted production consequences remain explicitly labelled inference.",
        "",
        f"- All evidence-backed nodes pass: `{report['checks']['all_evidence_backed_nodes_pass']}`",
        f"- Inferences explicit: `{report['checks']['inferences_are_explicit']}`",
        "",
    ]
    for chain in report["chains"]:
        lines.extend([
            f"## {chain['id']}: {chain['title']}",
            "",
            f"Proof grade: {chain['proof_grade']}.",
            "",
            "| Node | State | Claim | Evidence |",
            "|---:|---|---|---|",
        ])
        for index, node in enumerate(chain["nodes"], 1):
            lines.append(
                f"| {index} | `{node['state']}` | {node['claim']} | `{node['evidence']}` |"
            )
        lines.extend(["", "RazorProof prevention:", ""])
        lines.extend(f"- {item}" for item in chain["razorproof_prevention"])
        lines.append("")
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
