# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from razorproof.models import ClaimKind, EvidenceLevel, Finding, RunReport, Severity


SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}


def _link(label: str, url: str) -> str:
    return f"[{label}]({url})" if url else label


def _finding_markdown(finding: Finding) -> str:
    lines = [
        f"### {finding.id}: {finding.title}",
        "",
        f"- Claim type: `{finding.claim_kind.value}`; evidence: `{finding.level.value}`; severity: `{finding.severity.value}`; confidence: `{finding.confidence:.0%}`",
        f"- Originality: {finding.originality}",
        f"- Surface: `{finding.repo}` / {finding.surface}",
        f"- Invariant: {finding.invariant}",
        f"- Assessment: {finding.description}",
        f"- Impact: {finding.impact}",
    ]
    if finding.counterexample:
        lines.append(f"- Counterexample: `{finding.counterexample}`")
    if finding.proposed_fix:
        lines.append(f"- Fix direction: {finding.proposed_fix}")
    if finding.known_reference:
        lines.append(f"- Prior public reference: {_link(finding.known_reference, finding.known_reference)}")
    lines.extend(["", "Evidence:", ""])
    for evidence in finding.evidence:
        location = evidence.path
        if evidence.line is not None:
            location += f":{evidence.line}"
        source = _link(location or evidence.kind, evidence.source_url)
        detail = f" — {evidence.detail}" if evidence.detail else ""
        lines.append(f"- `{evidence.kind}` {evidence.summary} ({source}){detail}")
    lines.append("")
    return "\n".join(lines)


def render_markdown(report: RunReport) -> str:
    findings = sorted(
        report.findings,
        key=lambda item: (SEVERITY_ORDER[item.severity], item.id),
    )
    by_level = Counter(finding.level.value for finding in findings)
    by_severity = Counter(finding.severity.value for finding in findings)
    by_kind = Counter(finding.claim_kind.value for finding in findings)
    original_dynamic = [
        finding for finding in findings
        if finding.level == EvidenceLevel.DYNAMIC
        and "independently" in finding.originality
        and not finding.known_reference
    ]
    public = [finding for finding in findings if finding.known_reference]
    errors = [(result.probe, error) for result in report.results for error in result.errors]

    lines = [
        "# RazorProof Evidence Report",
        "",
        "> A semantic conformance compiler for money, cryptographic bytes, effect identity, and cross-SDK protocol behavior.",
        "",
        "## Executive result",
        "",
        f"RazorProof inspected **{len(report.repository_commits)} pinned official repositories** and produced **{len(findings)} evidence-backed observations**: "
        f"**{by_kind[ClaimKind.DEFECT.value]} direct defects**, **{by_kind[ClaimKind.COMPATIBILITY.value]} conditional compatibility defects**, and **{len(findings) - by_kind[ClaimKind.DEFECT.value] - by_kind[ClaimKind.COMPATIBILITY.value]} non-bug safety, hardening, or documentation gaps**. "
        f"It dynamically reproduced **{len(original_dynamic)} independently discovered observations** and links **{len(public)} prior public reports** without treating an open issue or pull request as maintainer confirmation.",
        "",
        f"- Evidence levels: {', '.join(f'`{key}`={value}' for key, value in sorted(by_level.items()))}",
        f"- Claim types: {', '.join(f'`{key}`={value}' for key, value in sorted(by_kind.items()))}",
        f"- Severity: {', '.join(f'`{key}`={value}' for key, value in sorted(by_severity.items()))}",
        f"- Scan window: `{report.started_at}` to `{report.completed_at}`",
        f"- Contract: `{report.contract_path}`",
        "",
        "The strongest day-zero case is not hypothetical: the official MCP checkout generator emits binary-float conversion code into new merchant backends. On the executable ₹2.01 counterexample, Python, Ruby and PHP each produced **200 paise instead of 201**. Static matches show the same truncating construction in Go, Java, Rust and .NET templates. The same generator hardcodes a two-decimal exponent for arbitrary currencies: its exact Node expression maps JPY 295 to 29,500 subunits and KWD 295.990 to 29,599 instead of 295,990. Razorpay Test Orders persisted the wrong generated integers because they are valid provider inputs.",
        "",
        "The broader failure mode is semantic drift across generated code, provider contracts, SDK state, and wire bytes. Three official SDKs were dynamically shown to leak credentials or partner-routing headers across client instances; four generated mobile success paths discard the signature required by their generated verifier; and the Java document serializer emits the wrong MIME type plus two conflicting `file` fields. These are distinct defects, but RazorProof also compiles them into six explicit failure chains without presenting an unexecuted production consequence as fact.",
        "",
        "## Reproducibility boundary",
        "",
        "- `confirmed_dynamic` means this run executed the official SDK/handler or the exact emitted expression and observed the counterexample.",
        "- `confirmed_static` means the violation is directly present in pinned official source, but this run did not execute that path.",
        "- `known_public` means a public issue or pull request exists. It is corroboration, not proof of maintainer acceptance and not claimed originality.",
        "- `hardening`, `safety_gap`, and `documentation_defect` are deliberately not represented as runtime product bugs.",
        "- No Live Mode transaction was attempted. Test Mode E2E used a user-owned account; credentials, raw webhook payloads, contact data, and provider IDs remain in ignored private files and never enter the evidence bundle.",
        "",
        "## Real Razorpay Test Mode evidence",
        "",
        f"The repository scan is backed by a separate provider-control-plane campaign. It adds one API-level defect beyond the {len(findings)} repository observations: `RP-API-REFUND-FRACTIONAL-COERCION`. Razorpay's documented Refund API types `amount` as integer smallest-subunit money, yet a direct JSON request for `100.75` returned HTTP 200, created a 100-subunit refund, emitted signed `refund.created` and `refund.processed` events, and settled in the provider ledger. A smaller-balance negative control rejected the same invalid input, so the finding is precisely an inconsistent fail-open validation path, not a claim that every fractional request succeeds.",
        "",
        "- [Campaign summary](../razorpay-test/campaign-summary.md): headline results, adversarial bounds, and the evidence map.",
        "- [Order boundary and generated undercharge](../razorpay-test/order-boundary.md): the official generated `int(2.01 * 100)` submits and persists 200, while the exact control persists 201.",
        "- [Expanded order contract matrix](../razorpay-test/expanded-order-contract-matrix.md): JPY/KWD exponent counterexamples, duplicate-receipt behavior, and integer-only Orders/Payment Link controls.",
        "- [Refund identity matrix](../razorpay-test/refund-identity-matrix.md): header conflict rejection, receipt duplicate prevention, two distinct unkeyed effects, and the fractional 100.75 to 100 coercion.",
        "- [Final redacted refund ledger](../razorpay-test/refund-ledger.md): all six refunds processed and the 801-subunit payment reached fully refunded with exact ledger equality.",
        "- [Literal UTF-8 webhook proof](../razorpay-test/webhook-byte-evidence.md): 22 signed deliveries across six event types; all signatures valid; all 16 literal-non-ASCII deliveries fail the .NET ASCII-equivalent digest.",
        "- [Negative control](../razorpay-test/refund-fractional-dust.md): the 101-subunit remainder rejected 100.75, disproving the stronger stranded-dust hypothesis and bounding the defect.",
        "- [Chained-bug evidence](../chains/chained-bug-evidence.md): six compositional failures with every inferred consequence labelled.",
        "- [Disclosure ledger](../disclosure/tracker-ledger.md): public correctness issues and private security routing kept separate.",
        "",
        "## Findings",
        "",
    ]
    for finding in findings:
        lines.append(_finding_markdown(finding))

    lines.extend(["## Repository ledger", "", "| Repository | Commit |", "|---|---|"])
    for name, commit in sorted(report.repository_commits.items()):
        lines.append(f"| `{name}` | `{commit}` |")
    lines.extend(["", "## Probe health", ""])
    if errors:
        lines.append("The following probe errors reduce evidence coverage but do not invalidate successful probes:")
        lines.append("")
        for probe, error in errors:
            lines.append(f"- `{probe}`: `{error[-500:]}`")
    else:
        lines.append("All requested probes completed without harness errors.")
    lines.extend([
        "",
        "## What this POC proves",
        "",
        "RazorProof is not another payment dashboard. It compiles semantic invariants across APIs, MCP schemas, generated integration code and seven SDK languages, then emits executable counterexamples and fix-oriented evidence. A conventional linter sees valid syntax in `int(amount * 100)`; RazorProof knows ₹2.01 must remain 201 paise. A conventional SAST rule sees AES-GCM; RazorProof compares nonce semantics across SDK releases and catches the one lagging implementation.",
        "",
    ])
    return "\n".join(lines)


def render_claim_ledger(report: RunReport) -> str:
    lines = [
        "# Claim Ledger",
        "",
        "| Claim | Type | Evidence | Originality | Evidence count | Commit |",
        "|---|---|---|---|---:|---|",
    ]
    for finding in sorted(report.findings, key=lambda item: item.id):
        lines.append(
            f"| {finding.id}: {finding.title} | `{finding.claim_kind.value}` | `{finding.level.value}` | "
            f"{finding.originality} | {len(finding.evidence)} | `{finding.commit}` |"
        )
    lines.append("")
    return "\n".join(lines)


def write_report(report: RunReport, output_directory: Path) -> dict[str, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": output_directory / "scan.json",
        "markdown": output_directory / "case-report.md",
        "ledger": output_directory / "claim-ledger.md",
    }
    paths["json"].write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    paths["markdown"].write_text(render_markdown(report), encoding="utf-8")
    paths["ledger"].write_text(render_claim_ledger(report), encoding="utf-8")
    return paths
