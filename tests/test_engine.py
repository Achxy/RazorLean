# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import unittest

from razorproof.engine import merge_findings
from razorproof.models import ClaimKind, Evidence, EvidenceLevel, Finding, ProbeResult, RunReport, Severity
from razorproof.report import render_claim_ledger, render_markdown


def finding(level: EvidenceLevel, evidence: str) -> Finding:
    return Finding(
        id="same",
        title="same",
        repo="repo",
        surface="surface",
        invariant="invariant",
        severity=Severity.HIGH,
        level=level,
        confidence=1.0,
        originality="independently reproduced" if level == EvidenceLevel.DYNAMIC else "static",
        evidence=[Evidence(kind=evidence, summary=evidence)],
    )


class MergeTests(unittest.TestCase):
    def test_dynamic_evidence_elevates_static_claim_without_duplicate(self) -> None:
        report = RunReport.start("test", {}, "contract", {})
        report.results = [
            ProbeResult("static", [finding(EvidenceLevel.STATIC, "source")]),
            ProbeResult("dynamic", [finding(EvidenceLevel.DYNAMIC, "runtime")]),
        ]
        merge_findings(report)
        self.assertEqual(1, len(report.findings))
        self.assertEqual(EvidenceLevel.DYNAMIC, report.findings[0].level)
        self.assertEqual({"source", "runtime"}, {e.kind for e in report.findings[0].evidence})

    def test_claim_kind_is_independent_from_evidence_strength(self) -> None:
        item = finding(EvidenceLevel.STATIC, "source")
        item.claim_kind = ClaimKind.HARDENING
        report = RunReport.start("test", {"repo": "commit"}, "contract", {})
        report.results = [ProbeResult("static", [item])]
        report.finish()

        markdown = render_markdown(report)
        ledger = render_claim_ledger(report)
        self.assertIn("`hardening`", markdown)
        self.assertIn("non-bug safety, hardening, or documentation gaps", markdown)
        self.assertIn("| `hardening` | `confirmed_static` |", ledger)
        self.assertNotIn("- Defect:", markdown)


if __name__ == "__main__":
    unittest.main()
