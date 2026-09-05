# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _non_ascii_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            paths.extend(_non_ascii_paths(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_non_ascii_paths(child, f"{path}[{index}]"))
    elif isinstance(value, str) and any(ord(character) > 127 for character in value):
        paths.append(path)
    return paths


def build_webhook_byte_evidence(capture_directory: Path, secret_path: Path) -> dict[str, Any]:
    """Build publishable proof without copying payloads, IDs, PII, or signatures."""
    secret = secret_path.read_text(encoding="utf-8").strip().encode()
    if not secret:
        raise ValueError("webhook secret must not be empty")

    observations: list[dict[str, Any]] = []
    event_counts: Counter[str] = Counter()
    all_signatures_valid = True
    for path in sorted(capture_directory.glob("capture-*.json")):
        capture = json.loads(path.read_text(encoding="utf-8"))
        event = str(capture.get("event") or "unknown")
        event_counts[event] += 1
        signature_valid_at_capture = capture.get("signature_valid") is True
        all_signatures_valid = all_signatures_valid and signature_valid_at_capture
        if capture.get("literal_non_ascii") is not True:
            continue

        raw = base64.b64decode(capture["raw_body_base64"], validate=True)
        text = raw.decode("utf-8")
        parsed = json.loads(text)
        signature = str(capture.get("headers", {}).get("X-Razorpay-Signature", ""))
        exact_digest = hmac.new(secret, raw, hashlib.sha256).hexdigest()
        utf8_roundtrip = text.encode("utf-8")
        ascii_substituted = text.encode("ascii", errors="replace")
        ascii_digest = hmac.new(secret, ascii_substituted, hashlib.sha256).hexdigest()
        codepoints = sorted({f"U+{ord(character):04X}" for character in text if ord(character) > 127})
        observations.append({
            "event": event,
            "raw_body_sha256": hashlib.sha256(raw).hexdigest(),
            "raw_body_bytes": len(raw),
            "signature_valid_at_capture": signature_valid_at_capture,
            "exact_raw_bytes_match_provider_signature": hmac.compare_digest(exact_digest, signature),
            "utf8_roundtrip_matches_provider_signature": hmac.compare_digest(
                hmac.new(secret, utf8_roundtrip, hashlib.sha256).hexdigest(), signature
            ),
            "dotnet_ascii_substitution_matches_provider_signature": hmac.compare_digest(
                ascii_digest, signature
            ),
            "ascii_substitution_changes_bytes": ascii_substituted != raw,
            "non_ascii_json_paths": sorted(_non_ascii_paths(parsed)),
            "non_ascii_codepoints": codepoints,
        })

    checks = {
        "captures_present": sum(event_counts.values()) > 0,
        "all_capture_signatures_valid": all_signatures_valid,
        "literal_non_ascii_provider_deliveries_present": bool(observations),
        "exact_utf8_verifies_all_literal_non_ascii_deliveries": bool(observations) and all(
            item["exact_raw_bytes_match_provider_signature"]
            and item["utf8_roundtrip_matches_provider_signature"]
            for item in observations
        ),
        "dotnet_ascii_fails_all_literal_non_ascii_deliveries": bool(observations) and all(
            item["ascii_substitution_changes_bytes"]
            and not item["dotnet_ascii_substitution_matches_provider_signature"]
            for item in observations
        ),
    }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_scope": "razorpay-test-mode-signed-webhooks",
        "real_money": False,
        "redaction": "raw bodies, signatures, headers, provider IDs, contact data, and secret omitted",
        "event_counts": dict(sorted(event_counts.items())),
        "literal_non_ascii_observations": observations,
        "checks": checks,
    }


def write_webhook_byte_evidence(report: dict[str, Any], output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "webhook-byte-evidence.json"
    markdown_path = output / "webhook-byte-evidence.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    checks = report["checks"]
    lines = [
        "# Razorpay Test Mode: Literal UTF-8 Webhook Evidence",
        "",
        f"- Captured signed deliveries: `{sum(report['event_counts'].values())}`",
        f"- Literal non-ASCII deliveries: `{len(report['literal_non_ascii_observations'])}`",
        f"- All capture signatures valid: `{checks['all_capture_signatures_valid']}`",
        f"- Exact UTF-8 bytes verify: `{checks['exact_utf8_verifies_all_literal_non_ascii_deliveries']}`",
        f"- .NET ASCII substitution fails verification: `{checks['dotnet_ascii_fails_all_literal_non_ascii_deliveries']}`",
        "",
        "## Event coverage",
        "",
        "| Event | Deliveries |",
        "|---|---:|",
    ]
    for event, count in report["event_counts"].items():
        lines.append(f"| `{event}` | `{count}` |")
    lines.extend([
        "",
        "## Literal-byte observations",
        "",
        "| Event | Bytes | Raw SHA-256 | Exact UTF-8 | .NET ASCII | Non-ASCII paths |",
        "|---|---:|---|---|---|---|",
    ])
    for item in report["literal_non_ascii_observations"]:
        paths = ", ".join(f"`{path}`" for path in item["non_ascii_json_paths"])
        lines.append(
            f"| `{item['event']}` | `{item['raw_body_bytes']}` | `{item['raw_body_sha256']}` | "
            f"`{item['exact_raw_bytes_match_provider_signature']}` | "
            f"`{item['dotnet_ascii_substitution_matches_provider_signature']}` | {paths} |"
        )
    lines.extend([
        "",
        "Razorpay signed the exact raw UTF-8 bytes delivered to the Test Mode endpoint. Re-encoding "
        "the same payload text with ASCII replacement changes those bytes and produces a different HMAC. "
        "This closes the former reachability caveat for the current .NET SDK's shared ASCII encoder: "
        "ordinary provider-generated payment-link and refund webhooks can contain literal non-ASCII bytes.",
        "",
        "This artifact intentionally omits raw payloads, signatures, headers, entity IDs, contact data, "
        "and the signing secret. SHA-256 values identify the private captures without disclosing them.",
        "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
