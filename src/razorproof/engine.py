# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import platform
import sys
from pathlib import Path

from razorproof import __version__
from razorproof.models import EvidenceLevel, Finding, RunReport
from razorproof.probes import run_dynamic_probes, run_static_probes
from razorproof.repositories import inspect_repositories


LEVEL_RANK = {
    EvidenceLevel.DYNAMIC: 6,
    EvidenceLevel.STATIC: 5,
    EvidenceLevel.KNOWN: 4,
    EvidenceLevel.CANDIDATE: 3,
    EvidenceLevel.NOT_REPRODUCED: 2,
    EvidenceLevel.PASS: 1,
}


def merge_findings(report: RunReport) -> None:
    """Merge the same claim across probes while preserving all evidence."""
    canonical: dict[str, Finding] = {}
    for result in report.results:
        merged: list[Finding] = []
        for finding in result.findings:
            prior = canonical.get(finding.id)
            if prior is None:
                canonical[finding.id] = finding
                merged.append(finding)
                continue
            prior.evidence.extend(
                evidence for evidence in finding.evidence if evidence not in prior.evidence
            )
            prior.tags = sorted(set(prior.tags + finding.tags))
            if LEVEL_RANK[finding.level] > LEVEL_RANK[prior.level]:
                prior.level = finding.level
                prior.confidence = max(prior.confidence, finding.confidence)
                prior.originality = finding.originality
                prior.counterexample = finding.counterexample or prior.counterexample
                prior.description = finding.description or prior.description
        result.findings = merged


def scan(
    repository_root: Path,
    contract_path: Path,
    *,
    dynamic: bool = True,
    containers: bool = False,
) -> RunReport:
    repositories = inspect_repositories(repository_root)
    report = RunReport.start(
        version=__version__,
        repository_commits={name: repo.commit for name, repo in repositories.items()},
        contract_path=str(contract_path),
        environment={
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "dynamic": str(dynamic).lower(),
            "containers": str(containers).lower(),
        },
    )
    report.results.extend(run_static_probes(repositories))
    if dynamic:
        report.results.extend(run_dynamic_probes(repositories, containers=containers))
    merge_findings(report)
    report.finish()
    return report
