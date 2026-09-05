# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


OFFICIAL_REPOSITORIES = {
    "razorpay-mcp-server": "https://github.com/razorpay/razorpay-mcp-server.git",
    "razorpay-python": "https://github.com/razorpay/razorpay-python.git",
    "razorpay-java": "https://github.com/razorpay/razorpay-java.git",
    "razorpay-node": "https://github.com/razorpay/razorpay-node.git",
    "razorpay-go": "https://github.com/razorpay/razorpay-go.git",
    "razorpay-dot-net": "https://github.com/razorpay/razorpay-dot-net.git",
    "razorpay-php": "https://github.com/razorpay/razorpay-php.git",
    "razorpay-ruby": "https://github.com/razorpay/razorpay-ruby.git",
}


@dataclass(frozen=True)
class Repository:
    name: str
    path: Path
    commit: str
    remote: str


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return process.stdout.strip()


def inspect_repositories(root: Path) -> dict[str, Repository]:
    repositories: dict[str, Repository] = {}
    for name, remote in OFFICIAL_REPOSITORIES.items():
        path = root / name
        if not (path / ".git").exists():
            continue
        commit = _run_git(["rev-parse", "HEAD"], cwd=path)
        repositories[name] = Repository(name, path, commit, remote)
    return repositories


def clone_missing(root: Path, names: list[str] | None = None) -> dict[str, Repository]:
    root.mkdir(parents=True, exist_ok=True)
    selected = names or list(OFFICIAL_REPOSITORIES)
    for name in selected:
        if name not in OFFICIAL_REPOSITORIES:
            raise ValueError(f"unknown official repository: {name}")
        destination = root / name
        if (destination / ".git").exists():
            continue
        _run_git(
            ["clone", "--depth", "1", OFFICIAL_REPOSITORIES[name], str(destination)]
        )
    return inspect_repositories(root)


def snapshot_local(source: Path, root: Path, names: list[str] | None = None) -> dict[str, Repository]:
    """Clone clean HEADs from existing local repositories without copying edits."""
    root.mkdir(parents=True, exist_ok=True)
    selected = names or list(OFFICIAL_REPOSITORIES)
    for name in selected:
        source_repo = source / name
        destination = root / name
        if (destination / ".git").exists():
            continue
        if not (source_repo / ".git").exists():
            continue
        subprocess.run(
            ["git", "clone", "--local", str(source_repo), str(destination)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "clean", "-fdx"],
            cwd=destination,
            check=True,
            capture_output=True,
            text=True,
        )
    return inspect_repositories(root)


def clean_work_copy(repository: Repository, destination: Path) -> Path:
    if destination.exists():
        raise FileExistsError(
            f"refusing to replace existing work-copy destination: {destination}"
        )
    subprocess.run(
        ["git", "clone", "--local", str(repository.path), str(destination)],
        check=True,
        capture_output=True,
        text=True,
    )
    return destination
