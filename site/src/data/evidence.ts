/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */

import scan from "../../../artifacts/expanded/scan.json";
import chainData from "../../../artifacts/chains/chained-bug-evidence.json";

export type Evidence = { kind: string; summary: string; detail: string; source_url: string; path: string; line: number | null };
export type Finding = {
  id: string; title: string; repo: string; surface: string; invariant: string;
  severity: "critical" | "high" | "medium" | "low"; level: string; description: string;
  impact: string; counterexample: string; proposed_fix: string; claim_kind: string;
  tags: string[]; evidence: Evidence[];
};
export type Chain = { id: string; title: string; proof_grade: string; nodes: { state: string; claim: string; evidence: string; passed: boolean | null }[]; razorproof_prevention: string[] };

export const findings = (scan.results as unknown as { findings: Finding[] }[]).flatMap((result) => result.findings);
export const chains = chainData.chains as Chain[];

export const claimLabel: Record<string, string> = {
  defect: "Defect", compatibility_defect: "Compatibility defect", safety_gap: "Safety gap",
  hardening: "Hardening", documentation_defect: "Documentation defect",
};

export const gradeLabel: Record<string, string> = {
  confirmed_dynamic: "Executed", confirmed_static: "Source-bound", known_public: "Publicly known",
  razorpay_test_observed: "Test Mode observed", razorpay_test_control: "Test Mode control", inferred_impact: "Explicit inference",
};

export const currencies = {
  INR: { symbol: "₹", entered: "2.01", intended: "201", generated: "200", factor: "1 paise short", verdict: "REJECTED: binary float at money boundary" },
  JPY: { symbol: "¥", entered: "295", intended: "295", generated: "29,500", factor: "100× overcharge", verdict: "REJECTED: exponent 0, not 2" },
  KWD: { symbol: "KD", entered: "295.990", intended: "295,990", generated: "29,599", factor: "≈10× undercharge", verdict: "REJECTED: exponent 3, not 2" },
} as const;

export const coordinates = [
  ["Value", "Is 295 JPY still 295 subunits?", "Exact decimal parsing + currency exponent"],
  ["Principal", "Which merchant account receives it?", "Tenant-fixed client and route"],
  ["Effect", "Is this retry the same refund?", "Durable idempotency identity"],
  ["Provenance", "Are these the exact signed bytes?", "Raw-byte verification"],
  ["Lifecycle", "Did paid become fulfilled exactly once?", "Provider re-fetch + state machine"],
] as const;
