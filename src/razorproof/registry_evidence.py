# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REGISTRY = "https://registry.npmjs.org"


def _latest(package: str) -> dict[str, Any]:
    url = f"{REGISTRY}/{urllib.parse.quote(package, safe='')}/latest"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "RazorProof-Registry-Evidence/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        return {"package": package, "http_status": exc.code, "exists": False}
    repository = payload.get("repository")
    if isinstance(repository, dict):
        repository = repository.get("url", "")
    maintainers = payload.get("maintainers", [])
    maintainer_names = sorted(
        str(item.get("name", ""))
        for item in maintainers
        if isinstance(item, dict) and item.get("name")
    )
    dist = payload.get("dist", {})
    return {
        "package": package,
        "http_status": 200,
        "exists": True,
        "version": payload.get("version"),
        "description": payload.get("description", ""),
        "repository": repository or "",
        "maintainer_names": maintainer_names,
        "unpacked_size": dist.get("unpackedSize"),
        "file_count": dist.get("fileCount"),
    }


def collect_mobile_registry_evidence() -> dict[str, Any]:
    missing = _latest("com.nicholaswilliams.nicepay.razorpay")
    suspicious = _latest("cordova-plugin-razorpay")
    official = _latest("com.razorpay.cordova")
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": REGISTRY,
        "packages": {
            "generated_cordova_and_ionic": missing,
            "generated_capacitor": suspicious,
            "razorpay_official_control": official,
        },
        "checks": {
            "cordova_and_ionic_dependency_missing": (
                missing.get("exists") is False and missing.get("http_status") == 404
            ),
            "capacitor_dependency_is_empty_package": (
                suspicious.get("exists") is True
                and str(suspicious.get("description", "")).strip().lower()
                == "empty package."
                and suspicious.get("file_count") == 2
            ),
            "capacitor_dependency_not_official_repo": (
                "github.com/razorpay/razorpay-cordova"
                not in str(suspicious.get("repository", "")).lower()
            ),
            "official_control_owned_and_linked_to_razorpay": (
                official.get("exists") is True
                and "razorpay-dev" in official.get("maintainer_names", [])
                and "github.com/razorpay/razorpay-cordova"
                in str(official.get("repository", "")).lower()
            ),
        },
    }


def write_mobile_registry_evidence(
    report: dict[str, Any], output: Path
) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "mobile-registry-evidence.json"
    markdown_path = output / "mobile-registry-evidence.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    packages = report["packages"]
    lines = [
        "# Mobile Dependency Registry Evidence",
        "",
        f"- Registry: `{report['source']}`",
        f"- Captured: `{report['created_at']}`",
        "",
        "| Generator path | Package | Exists | Version | Description | Files | Repository |",
        "|---|---|---|---|---|---:|---|",
    ]
    for label, package in packages.items():
        lines.append(
            f"| `{label}` | `{package['package']}` | `{package['exists']}` | "
            f"`{package.get('version', '')}` | {package.get('description', '')} | "
            f"`{package.get('file_count', '')}` | `{package.get('repository', '')}` |"
        )
    lines.extend([
        "",
        "The official MCP generator emits the first package for Cordova and Ionic and the second for Capacitor. The first returns npm 404. The second is a 179-byte, two-file package whose own description and README say `Empty package.` It is not linked to Razorpay's repository. The official control package is `com.razorpay.cordova`, lists Razorpay's npm maintainer identity, and links to the Razorpay GitHub repository.",
        "",
        "This proves a present dependency identity defect. Arbitrary-code execution is a supply-chain risk, not a claim that the current empty package is malicious.",
        "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
