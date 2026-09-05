# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Sequence

from razorproof.models import ProbeResult


def line_number(text: str, needle: str) -> int | None:
    offset = text.find(needle)
    if offset < 0:
        return None
    return text.count("\n", 0, offset) + 1


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_process(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def parse_last_json(output: str) -> dict[str, object]:
    for line in reversed(output.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError(f"process emitted no JSON object: {output[-500:]}")


class ProbeTimer:
    def __init__(self, name: str) -> None:
        self.result = ProbeResult(probe=name)
        self._started = 0.0

    def __enter__(self) -> ProbeResult:
        self._started = time.perf_counter()
        return self.result

    def __exit__(self, exc_type, exc, _traceback) -> bool:
        self.result.duration_ms = round((time.perf_counter() - self._started) * 1000)
        if exc is not None:
            self.result.errors.append(f"{type(exc).__name__}: {exc}")
            return True
        return False
