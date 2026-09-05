# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class EvidenceLevel(StrEnum):
    DYNAMIC = "confirmed_dynamic"
    STATIC = "confirmed_static"
    KNOWN = "known_public"
    CANDIDATE = "candidate"
    NOT_REPRODUCED = "not_reproduced"
    PASS = "pass"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ClaimKind(StrEnum):
    """What a finding actually claims, independently of evidence strength."""

    DEFECT = "defect"
    COMPATIBILITY = "compatibility_defect"
    SAFETY_GAP = "safety_gap"
    HARDENING = "hardening"
    DOCUMENTATION = "documentation_defect"


@dataclass(frozen=True)
class Evidence:
    kind: str
    summary: str
    detail: str = ""
    command: str = ""
    source_url: str = ""
    path: str = ""
    line: int | None = None


@dataclass
class Finding:
    id: str
    title: str
    repo: str
    surface: str
    invariant: str
    severity: Severity
    level: EvidenceLevel
    confidence: float
    originality: str
    commit: str = ""
    description: str = ""
    impact: str = ""
    counterexample: str = ""
    proposed_fix: str = ""
    known_reference: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    claim_kind: ClaimKind = ClaimKind.DEFECT

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProbeResult:
    probe: str
    findings: list[Finding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0


@dataclass
class RunReport:
    version: str
    started_at: str
    completed_at: str
    repository_commits: dict[str, str]
    results: list[ProbeResult]
    contract_path: str
    environment: dict[str, str]

    @classmethod
    def start(
        cls,
        version: str,
        repository_commits: dict[str, str],
        contract_path: str,
        environment: dict[str, str],
    ) -> "RunReport":
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            version=version,
            started_at=now,
            completed_at="",
            repository_commits=repository_commits,
            results=[],
            contract_path=contract_path,
            environment=environment,
        )

    @property
    def findings(self) -> list[Finding]:
        return [finding for result in self.results for finding in result.findings]

    def finish(self) -> None:
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
