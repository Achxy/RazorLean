# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from razorproof.money import major_to_minor
from razorproof.repositories import Repository, clean_work_copy

from .probes.common import parse_last_json, run_process
from .probes.dynamic import DOTNET_PROGRAM, GO_REFUND_TEST


PYTHON_SCRIPT = r'''
import hashlib, hmac, json
from razorpay.utility.utility import Utility
class Client: auth = ("key", "secret")
body = b'{"event":"payment.captured","name":"Achu"}'
signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
try:
    value = Utility(Client()).verify_webhook_signature(body, signature, "secret")
    print(json.dumps({"accepted": value, "error": ""}))
except Exception as exc:
    print(json.dumps({"accepted": False, "error": type(exc).__name__ + ": " + str(exc)}))
'''


RUBY_SCRIPT = r'''
require 'json'; require 'openssl'
module Razorpay
  def self.auth; { password: 'secret' }; end
end
load ARGV[0]
payload = ['plink_live_shape', 'ref_42', 'paid', 'pay_live_shape'].join('|')
signature = OpenSSL::HMAC.hexdigest('SHA256', 'secret', payload)
value = { razorpay_payment_id: 'pay_live_shape', payment_link_status: 'paid', payment_link_id: 'plink_live_shape', payment_link_reference_id: 'ref_42', razorpay_signature: signature }
begin
  accepted = Razorpay::Utility.verify_payment_link_signature(value)
  puts JSON.generate({ accepted: accepted, error: '', caller_signature_preserved: value.key?(:razorpay_signature) })
rescue Exception => e
  puts JSON.generate({ accepted: false, error: e.class.name + ': ' + e.message, caller_signature_preserved: value.key?(:razorpay_signature) })
end
'''


def _python_fix(repo: Repository) -> dict[str, object]:
    python = shutil.which("python3") or "python3"
    before = parse_last_json(run_process([python, "-c", PYTHON_SCRIPT], cwd=repo.path).stdout)
    with tempfile.TemporaryDirectory(prefix="razorproof-fix-python-") as directory:
        work = clean_work_copy(repo, Path(directory) / "repo")
        path = work / "razorpay/utility/utility.py"
        source = path.read_text(encoding="utf-8")
        old = """            key = bytes(key, 'utf-8')\n            body = bytes(body, 'utf-8')"""
        new = """            if isinstance(key, str):\n                key = key.encode('utf-8')\n            if isinstance(body, str):\n                body = body.encode('utf-8')\n            elif isinstance(body, bytearray):\n                body = bytes(body)\n            elif not isinstance(body, bytes):\n                raise TypeError('body must be str or bytes')"""
        if old not in source:
            raise RuntimeError("Python fix anchor not found")
        path.write_text(source.replace(old, new, 1), encoding="utf-8")
        after = parse_last_json(run_process([python, "-c", PYTHON_SCRIPT], cwd=work).stdout)
    return {
        "id": "RP-PYTHON-WEBHOOK-BYTES",
        "before": before,
        "after": after,
        "fixed": before.get("accepted") is False and after.get("accepted") is True,
        "scope": "disposable clean clone",
    }


def _ruby_fix(repo: Repository) -> dict[str, object]:
    ruby = shutil.which("ruby")
    if ruby is None:
        return {"id": "RP-RUBY-PAYLINK-ORDER", "fixed": False, "error": "ruby unavailable"}
    original_utility = repo.path / "lib/razorpay/utility.rb"
    before = parse_last_json(run_process([ruby, "-e", RUBY_SCRIPT, str(original_utility)]).stdout)
    with tempfile.TemporaryDirectory(prefix="razorproof-fix-ruby-") as directory:
        work = clean_work_copy(repo, Path(directory) / "repo")
        path = work / "lib/razorpay/utility.rb"
        source = path.read_text(encoding="utf-8")
        old = """      signature = attributes.delete(:razorpay_signature)\n      # element of each is the value. These are joined.\n      data = attributes.values.join('|')"""
        new = """      signature = attributes.fetch(:razorpay_signature)\n      data = [\n        attributes.fetch(:payment_link_id),\n        attributes.fetch(:payment_link_reference_id),\n        attributes.fetch(:payment_link_status),\n        attributes.fetch(:razorpay_payment_id)\n      ].join('|')"""
        if old not in source:
            raise RuntimeError("Ruby fix anchor not found")
        path.write_text(source.replace(old, new, 1), encoding="utf-8")
        after = parse_last_json(run_process([ruby, "-e", RUBY_SCRIPT, str(path)]).stdout)
    return {
        "id": "RP-RUBY-PAYLINK-ORDER",
        "before": before,
        "after": after,
        "fixed": before.get("accepted") is False and after.get("accepted") is True and after.get("caller_signature_preserved") is True,
        "scope": "disposable clean clone",
    }


def _money_fix() -> dict[str, object]:
    before = int(2.01 * 100)
    after = major_to_minor("2.01", "INR")
    float_rejected = False
    try:
        major_to_minor(2.01, "INR")  # type: ignore[arg-type]
    except TypeError:
        float_rejected = True
    return {
        "id": "RP-MCP-GENERATOR-MONEY-UNDERCHARGE",
        "before": {"input": 2.01, "minor_units": before},
        "after": {"input": "2.01", "minor_units": after, "binary_float_rejected": float_rejected},
        "fixed": before == 200 and after == 201 and float_rejected,
        "scope": "RazorProof exact-money boundary",
    }


def _run_go_test(work: Path) -> dict[str, object]:
    process = run_process([
        "docker", "run", "--rm", "-v", f"{work}:/work", "-w", "/work",
        "golang:1.25", "go", "test", "./pkg/razorpay",
        "-run", "TestRazorProofFractionalRefundMustFailClosed", "-count=1", "-v",
    ], timeout=600)
    output = process.stdout + process.stderr
    return {"exit": process.returncode, "tail": output[-2500:]}


def _mcp_refund_fix(repo: Repository) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="razorproof-fix-go-", dir="/tmp") as directory:
        work = clean_work_copy(repo, Path(directory) / "repo")
        (work / "pkg/razorpay/razorproof_fractional_test.go").write_text(GO_REFUND_TEST, encoding="utf-8")
        before = _run_go_test(work)

        refund_path = work / "pkg/razorpay/refunds.go"
        refund = refund_path.read_text(encoding="utf-8")
        refund = refund.replace('ValidateAndAddRequiredFloat(payload, "amount")', 'ValidateAndAddRequiredInt(payload, "amount")', 1)
        refund = refund.replace('int(payload["amount"].(float64))', 'int(payload["amount"].(int64))', 1)
        refund_path.write_text(refund, encoding="utf-8")
        after = _run_go_test(work)
    return {
        "id": "RP-MCP-REFUND-TRUNCATION",
        "before": before,
        "after": after,
        "fixed": before["exit"] != 0 and after["exit"] == 0,
        "scope": "disposable clean clone; official handler and SDK HTTP path; proves fractional rejection and valid-integer acceptance",
    }


def _prepare_dotnet_project(work: Path) -> None:
    project = work / "Razorpay.csproj"
    source = project.read_text(encoding="utf-8")
    project.write_text(
        source.replace(
            "<TargetFrameworks>net47;net48;netstandard2.0;net6.0;net8.0</TargetFrameworks>",
            "<TargetFramework>net8.0</TargetFramework>",
        ).replace("<GeneratePackageOnBuild>true</GeneratePackageOnBuild>", "<GeneratePackageOnBuild>false</GeneratePackageOnBuild>"),
        encoding="utf-8",
    )


def _run_dotnet(work: Path, root: Path) -> dict[str, object]:
    probe = root / "probe"
    probe.mkdir()
    (probe / "Program.cs").write_text(DOTNET_PROGRAM, encoding="utf-8")
    (probe / "Probe.csproj").write_text(f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings></PropertyGroup>
  <ItemGroup><ProjectReference Include="{work / 'Razorpay.csproj'}" /></ItemGroup>
</Project>''', encoding="utf-8")
    process = run_process([
        "docker", "run", "--rm", "-v", f"{root}:{root}", "-w", str(probe),
        "mcr.microsoft.com/dotnet/sdk:8.0", "dotnet", "run", "--project", "Probe.csproj",
    ], timeout=600)
    if process.returncode != 0:
        return {"exit": process.returncode, "error": (process.stdout + process.stderr)[-4000:]}
    return {"exit": 0, **parse_last_json(process.stdout)}


def _dotnet_fix(repo: Repository) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="razorproof-fix-dotnet-", dir="/tmp") as directory:
        root = Path(directory)
        work = clean_work_copy(repo, root / "razorpay-dot-net")
        _prepare_dotnet_project(work)
        source_path = work / "src/Utils.cs"
        source = source_path.read_text(encoding="utf-8")
        source = source.replace("Array.Copy(keyBytes, 0, iv, 0, 12);", "RandomNumberGenerator.Fill(iv);", 1)
        source = source.replace(
            "return BytesToHex(encryptedData);",
            "byte[] combined = new byte[iv.Length + encryptedData.Length];\n                Buffer.BlockCopy(iv, 0, combined, 0, iv.Length);\n                Buffer.BlockCopy(encryptedData, 0, combined, iv.Length, encryptedData.Length);\n                return BytesToHex(combined);",
            1,
        )
        source = source.replace("var encoding = new ASCIIEncoding();", "var encoding = new UTF8Encoding(false);", 1)
        source_path.write_text(source, encoding="utf-8")
        after = _run_dotnet(work, root)
    return {
        "id": "RP-DOTNET-GCM-NONCE-REUSE + RP-DOTNET-WEBHOOK-ASCII",
        "before": {"gcm_same": True, "unicode_accepted": False, "source": "successful container scan"},
        "after": after,
        "fixed": after.get("exit") == 0 and after.get("gcm_same") is False and after.get("unicode_accepted") is True,
        "scope": "disposable clean clone; official SDK project",
    }


def prove_fixes(repositories: dict[str, Repository], *, containers: bool = False) -> dict[str, object]:
    proofs: list[dict[str, object]] = [_money_fix()]
    if repo := repositories.get("razorpay-python"):
        proofs.append(_python_fix(repo))
    if repo := repositories.get("razorpay-ruby"):
        proofs.append(_ruby_fix(repo))
    if containers:
        if repo := repositories.get("razorpay-mcp-server"):
            proofs.append(_mcp_refund_fix(repo))
        if repo := repositories.get("razorpay-dot-net"):
            proofs.append(_dotnet_fix(repo))
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "all_fixed": all(bool(proof.get("fixed")) for proof in proofs),
        "proofs": proofs,
    }


def write_fix_report(report: dict[str, object], output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "fix-proof.json"
    markdown_path = output / "fix-proof.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# RazorProof Red to Green Fix Proof", "", f"All proposed fixes passed: **{report['all_fixed']}**", ""]
    for proof in report["proofs"]:
        lines.extend([
            f"## {proof['id']}", "",
            f"- Fixed: `{proof.get('fixed')}`",
            f"- Scope: {proof.get('scope', '')}",
            f"- Before: `{json.dumps(proof.get('before'), sort_keys=True)}`",
            f"- After: `{json.dumps(proof.get('after'), sort_keys=True)}`",
            "",
        ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
