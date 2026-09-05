# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import argparse
import json
from pathlib import Path

from razorproof.engine import scan
from razorproof.chains import ChainEvidenceError, build_chain_evidence, write_chain_evidence
from razorproof.faultlab import run_fault_lab, write_fault_report
from razorproof.fixes import prove_fixes, write_fix_report
from razorproof.live import LiveGateError, run_test_mode_refund_idempotency
from razorproof.registry_evidence import (
    collect_mobile_registry_evidence,
    write_mobile_registry_evidence,
)
from razorproof.live_e2e import (
    TestControlPlaneError,
    create_payment_link_fixture,
    fetch_redacted_refund_ledger,
    refresh_payment_session,
    run_expanded_order_contract_matrix,
    run_order_boundary_matrix,
    run_refund_header_idempotency,
    run_refund_idempotent_close,
    run_refund_identity_matrix,
    run_refund_fractional_dust_probe,
    write_expanded_order_contract_matrix,
    write_order_boundary_report,
    write_refund_report,
    write_refund_idempotent_close,
    write_refund_identity_matrix,
    write_refund_fractional_dust_probe,
    write_refund_ledger,
)
from razorproof.report import write_report
from razorproof.repositories import OFFICIAL_REPOSITORIES, clone_missing, inspect_repositories
from razorproof.webhook_evidence import (
    build_webhook_byte_evidence,
    write_webhook_byte_evidence,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    root = _project_root()
    parser = argparse.ArgumentParser(
        prog="razorproof",
        description="Compile financial semantic contracts against Razorpay interfaces.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    repos = subparsers.add_parser("repos", help="inspect or clone pinned official source inputs")
    repos.add_argument("--root", type=Path, default=root / ".razorproof/repos")
    repos.add_argument("--clone-missing", action="store_true")

    scanner = subparsers.add_parser("scan", help="run semantic conformance probes")
    scanner.add_argument("--repos", type=Path, default=root / ".razorproof/repos")
    scanner.add_argument("--contract", type=Path, default=root / "contracts/razorpay.json")
    scanner.add_argument("--output", type=Path, default=root / "artifacts/latest")
    scanner.add_argument("--static-only", action="store_true")
    scanner.add_argument("--containers", action="store_true", help="execute official Go/.NET paths in disposable containers")
    scanner.add_argument("--fail-on", choices=["none", "critical", "high"], default="none")

    fault = subparsers.add_parser("fault-lab", help="run a real local HTTP lost-response/idempotency demonstration")
    fault.add_argument("--output", type=Path, default=root / "artifacts/fault-lab")

    live = subparsers.add_parser("live-refund", help="run the idempotency proof against a user-owned Razorpay test account")
    live.add_argument("--payment-id", required=True)
    live.add_argument("--amount", required=True, type=int, help="integer currency subunits")
    live.add_argument("--execute-test-mode", action="store_true")

    live_orders = subparsers.add_parser(
        "live-orders",
        help="run the redacted order-boundary matrix against Razorpay Test Mode",
    )
    live_orders.add_argument("--credentials-csv", required=True, type=Path)
    live_orders.add_argument("--execute-test-mode", action="store_true")
    live_orders.add_argument("--output", type=Path, default=root / "artifacts/razorpay-test")

    expanded_orders = subparsers.add_parser(
        "live-expanded-orders",
        help="run redacted currency, receipt, and integer controls against Razorpay Test Mode",
    )
    expanded_orders.add_argument("--credentials-csv", required=True, type=Path)
    expanded_orders.add_argument("--execute-test-mode", action="store_true")
    expanded_orders.add_argument(
        "--output", type=Path, default=root / "artifacts/razorpay-test"
    )

    live_link = subparsers.add_parser(
        "live-payment-link",
        help="create one hosted ₹2.01 fixture in Razorpay Test Mode",
    )
    live_link.add_argument("--credentials-csv", required=True, type=Path)
    live_link.add_argument("--amount", type=int, default=201)
    live_link.add_argument("--execute-test-mode", action="store_true")
    live_link.add_argument(
        "--session",
        type=Path,
        default=root / ".razorproof/test-session.json",
    )

    live_refresh = subparsers.add_parser(
        "live-refresh",
        help="resolve a hosted-link Test payment into the private session",
    )
    live_refresh.add_argument("--credentials-csv", required=True, type=Path)
    live_refresh.add_argument(
        "--session", type=Path, default=root / ".razorproof/test-session.json"
    )

    live_refund_e2e = subparsers.add_parser(
        "live-refund-e2e",
        help="prove explicit refund-header idempotency in Razorpay Test Mode",
    )
    live_refund_e2e.add_argument("--credentials-csv", required=True, type=Path)
    live_refund_e2e.add_argument("--amount", required=True, type=int)
    live_refund_e2e.add_argument("--execute-test-mode", action="store_true")
    live_refund_e2e.add_argument(
        "--session", type=Path, default=root / ".razorproof/test-session.json"
    )
    live_refund_e2e.add_argument(
        "--output", type=Path, default=root / "artifacts/razorpay-test"
    )

    live_refund_matrix = subparsers.add_parser(
        "live-refund-matrix",
        help="compare header, receipt, and unkeyed retry identity in Razorpay Test Mode",
    )
    live_refund_matrix.add_argument("--credentials-csv", required=True, type=Path)
    live_refund_matrix.add_argument("--execute-test-mode", action="store_true")
    live_refund_matrix.add_argument(
        "--session", type=Path, default=root / ".razorproof/test-session.json"
    )
    live_refund_matrix.add_argument(
        "--output", type=Path, default=root / "artifacts/razorpay-test"
    )

    live_refund_close = subparsers.add_parser(
        "live-refund-close",
        help="reconcile and idempotently close a partially refunded Test payment",
    )
    live_refund_close.add_argument("--credentials-csv", required=True, type=Path)
    live_refund_close.add_argument("--execute-test-mode", action="store_true")
    live_refund_close.add_argument(
        "--identity", choices=["header", "receipt"], default="header"
    )
    live_refund_close.add_argument(
        "--session", type=Path, default=root / ".razorproof/test-session.json"
    )
    live_refund_close.add_argument(
        "--output", type=Path, default=root / "artifacts/razorpay-test"
    )

    webhook_evidence = subparsers.add_parser(
        "webhook-evidence",
        help="redact captured Test webhooks and prove UTF-8 versus ASCII signature behavior",
    )
    webhook_evidence.add_argument("--captures", required=True, type=Path)
    webhook_evidence.add_argument("--secret-file", required=True, type=Path)
    webhook_evidence.add_argument(
        "--output", type=Path, default=root / "artifacts/razorpay-test"
    )

    refund_ledger = subparsers.add_parser(
        "live-refund-ledger",
        help="fetch a redacted Test payment and refund ledger",
    )
    refund_ledger.add_argument("--credentials-csv", required=True, type=Path)
    refund_ledger.add_argument(
        "--session", type=Path, default=root / ".razorproof/test-session.json"
    )
    refund_ledger.add_argument(
        "--output", type=Path, default=root / "artifacts/razorpay-test"
    )

    refund_dust = subparsers.add_parser(
        "live-refund-dust",
        help="prove fractional coercion and characterize a one-subunit Test refund residual",
    )
    refund_dust.add_argument("--credentials-csv", required=True, type=Path)
    refund_dust.add_argument("--execute-test-mode", action="store_true")
    refund_dust.add_argument(
        "--session", type=Path, default=root / ".razorproof/test-session.json"
    )
    refund_dust.add_argument(
        "--output", type=Path, default=root / "artifacts/razorpay-test"
    )

    fixes = subparsers.add_parser("prove-fixes", help="apply proposed remediations to disposable clean clones and rerun counterexamples")
    fixes.add_argument("--repos", type=Path, default=root / ".razorproof/repos")
    fixes.add_argument("--output", type=Path, default=root / "artifacts/fixes")
    fixes.add_argument("--containers", action="store_true")

    registry = subparsers.add_parser(
        "mobile-registry-evidence",
        help="capture current npm identity evidence for generated mobile dependencies",
    )
    registry.add_argument(
        "--output", type=Path, default=root / "artifacts/registry"
    )

    chains = subparsers.add_parser(
        "build-chains",
        help="compose strict chained-bug evidence from existing scan and Test Mode artifacts",
    )
    chains.add_argument(
        "--output", type=Path, default=root / "artifacts/chains"
    )
    return parser


def _repos(args: argparse.Namespace) -> int:
    repositories = clone_missing(args.root) if args.clone_missing else inspect_repositories(args.root)
    print(json.dumps({
        "found": {name: repo.commit for name, repo in sorted(repositories.items())},
        "missing": sorted(set(OFFICIAL_REPOSITORIES) - set(repositories)),
    }, indent=2))
    return 0 if len(repositories) == len(OFFICIAL_REPOSITORIES) else 2


def _scan(args: argparse.Namespace) -> int:
    report = scan(
        args.repos,
        args.contract,
        dynamic=not args.static_only,
        containers=args.containers,
    )
    paths = write_report(report, args.output)
    counts: dict[str, int] = {}
    for finding in report.findings:
        counts[finding.level.value] = counts.get(finding.level.value, 0) + 1
    print(json.dumps({
        "findings": len(report.findings),
        "by_level": counts,
        "reports": {name: str(path) for name, path in paths.items()},
        "probe_errors": sum(len(result.errors) for result in report.results),
    }, indent=2))
    if args.fail_on == "critical" and any(f.severity.value == "critical" for f in report.findings):
        return 1
    if args.fail_on == "high" and any(f.severity.value in {"critical", "high"} for f in report.findings):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "repos":
        return _repos(args)
    if args.command == "scan":
        return _scan(args)
    if args.command == "fault-lab":
        result = run_fault_lab()
        paths = write_fault_report(result, args.output)
        print(json.dumps({**result, "reports": {key: str(value) for key, value in paths.items()}}, indent=2))
        return 0
    if args.command == "live-refund":
        try:
            result = run_test_mode_refund_idempotency(
                payment_id=args.payment_id,
                amount=args.amount,
                execute=args.execute_test_mode,
            )
        except LiveGateError as exc:
            print(json.dumps({"executed": False, "reason": str(exc)}, indent=2))
            return 2
        print(json.dumps(result, indent=2))
        return 0 if result["one_effect"] else 1
    if args.command == "live-orders":
        try:
            report = run_order_boundary_matrix(
                args.credentials_csv,
                execute=args.execute_test_mode,
            )
        except TestControlPlaneError as exc:
            print(json.dumps({"executed": False, "reason": str(exc)}, indent=2))
            return 2
        paths = write_order_boundary_report(report, args.output)
        print(json.dumps({
            "executed": True,
            "all_expectations_met": report["checks"]["all_expectations_met"],
            "reports": {key: str(value) for key, value in paths.items()},
        }, indent=2))
        return 0 if report["checks"]["run_completed"] else 1
    if args.command == "live-expanded-orders":
        try:
            report = run_expanded_order_contract_matrix(
                args.credentials_csv,
                execute=args.execute_test_mode,
            )
        except TestControlPlaneError as exc:
            print(json.dumps({"executed": False, "reason": str(exc)}, indent=2))
            return 2
        paths = write_expanded_order_contract_matrix(report, args.output)
        print(json.dumps({
            "executed": True,
            **report["checks"],
            "reports": {key: str(value) for key, value in paths.items()},
        }, indent=2))
        return 0 if report["checks"]["all_requests_completed"] else 1
    if args.command == "live-payment-link":
        try:
            report = create_payment_link_fixture(
                args.credentials_csv,
                args.session,
                amount=args.amount,
                execute=args.execute_test_mode,
            )
        except TestControlPlaneError as exc:
            print(json.dumps({"executed": False, "reason": str(exc)}, indent=2))
            return 2
        print(json.dumps({"executed": True, **report}, indent=2))
        return 0
    if args.command == "live-refresh":
        try:
            report = refresh_payment_session(args.credentials_csv, args.session)
        except TestControlPlaneError as exc:
            print(json.dumps({"executed": False, "reason": str(exc)}, indent=2))
            return 2
        print(json.dumps(report, indent=2))
        return 0 if report["payment_found"] else 1
    if args.command == "live-refund-e2e":
        try:
            report = run_refund_header_idempotency(
                args.credentials_csv,
                args.session,
                amount=args.amount,
                execute=args.execute_test_mode,
            )
        except TestControlPlaneError as exc:
            print(json.dumps({"executed": False, "reason": str(exc)}, indent=2))
            return 2
        paths = write_refund_report(report, args.output)
        print(json.dumps({
            "executed": True,
            "one_refund_effect": report["checks"]["one_refund_effect"],
            "reports": {key: str(value) for key, value in paths.items()},
        }, indent=2))
        return 0 if report["checks"]["one_refund_effect"] else 1
    if args.command == "live-refund-matrix":
        try:
            report = run_refund_identity_matrix(
                args.credentials_csv,
                args.session,
                mechanism=args.identity,
                execute=args.execute_test_mode,
            )
        except TestControlPlaneError as exc:
            print(json.dumps({"executed": False, "reason": str(exc)}, indent=2))
            return 2
        paths = write_refund_identity_matrix(report, args.output)
        print(json.dumps({
            "executed": True,
            **report["checks"],
            "reports": {key: str(value) for key, value in paths.items()},
        }, indent=2))
        return 0 if all(report["checks"].values()) else 1
    if args.command == "live-refund-close":
        try:
            report = run_refund_idempotent_close(
                args.credentials_csv,
                args.session,
                execute=args.execute_test_mode,
            )
        except TestControlPlaneError as exc:
            print(json.dumps({"executed": False, "reason": str(exc)}, indent=2))
            return 2
        paths = write_refund_idempotent_close(report, args.output)
        print(json.dumps({
            "executed": True,
            **report["checks"],
            "reports": {key: str(value) for key, value in paths.items()},
        }, indent=2))
        return 0 if all(report["checks"].values()) else 1
    if args.command == "webhook-evidence":
        report = build_webhook_byte_evidence(args.captures, args.secret_file)
        paths = write_webhook_byte_evidence(report, args.output)
        print(json.dumps({
            **report["checks"],
            "event_counts": report["event_counts"],
            "literal_non_ascii_deliveries": len(report["literal_non_ascii_observations"]),
            "reports": {key: str(value) for key, value in paths.items()},
        }, indent=2))
        return 0 if all(report["checks"].values()) else 1
    if args.command == "live-refund-ledger":
        try:
            report = fetch_redacted_refund_ledger(
                args.credentials_csv,
                args.session,
            )
        except TestControlPlaneError as exc:
            print(json.dumps({"executed": False, "reason": str(exc)}, indent=2))
            return 2
        paths = write_refund_ledger(report, args.output)
        print(json.dumps({
            **report["checks"],
            "refund_count": report["refund_count"],
            "refunded_total": report["refunded_total"],
            "reports": {key: str(value) for key, value in paths.items()},
        }, indent=2))
        return 0 if all(report["checks"].values()) else 1
    if args.command == "live-refund-dust":
        try:
            report = run_refund_fractional_dust_probe(
                args.credentials_csv,
                args.session,
                execute=args.execute_test_mode,
            )
        except TestControlPlaneError as exc:
            print(json.dumps({"executed": False, "reason": str(exc)}, indent=2))
            return 2
        paths = write_refund_fractional_dust_probe(report, args.output)
        print(json.dumps({
            "executed": True,
            **report["checks"],
            "reports": {key: str(value) for key, value in paths.items()},
        }, indent=2))
        return 0 if all(report["checks"].values()) else 1
    if args.command == "prove-fixes":
        report = prove_fixes(inspect_repositories(args.repos), containers=args.containers)
        paths = write_fix_report(report, args.output)
        print(json.dumps({"all_fixed": report["all_fixed"], "reports": {key: str(value) for key, value in paths.items()}}, indent=2))
        return 0 if report["all_fixed"] else 1
    if args.command == "mobile-registry-evidence":
        report = collect_mobile_registry_evidence()
        paths = write_mobile_registry_evidence(report, args.output)
        print(json.dumps({
            **report["checks"],
            "reports": {key: str(value) for key, value in paths.items()},
        }, indent=2))
        return 0 if all(report["checks"].values()) else 1
    if args.command == "build-chains":
        try:
            report = build_chain_evidence(_project_root())
        except ChainEvidenceError as exc:
            print(json.dumps({"built": False, "reason": str(exc)}, indent=2))
            return 2
        paths = write_chain_evidence(report, args.output)
        print(json.dumps({
            **report["checks"],
            "chain_count": len(report["chains"]),
            "reports": {key: str(value) for key, value in paths.items()},
        }, indent=2))
        return 0 if all(report["checks"].values()) else 1
    raise AssertionError(args.command)
