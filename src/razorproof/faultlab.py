# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import http.client
import json
import socket
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


@dataclass
class EffectStore:
    effects: list[str] = field(default_factory=list)
    by_key: dict[str, str] = field(default_factory=dict)
    drop_next_response: bool = True

    def commit(self, key: str) -> str:
        if key and key in self.by_key:
            return self.by_key[key]
        effect = f"rfnd_faultlab_{len(self.effects) + 1}"
        self.effects.append(effect)
        if key:
            self.by_key[key] = effect
        return effect


class FaultLab:
    """Real HTTP retry lab that drops the first response after commit."""

    def __init__(self) -> None:
        self.store = EffectStore()
        store = self.store

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format: str, *_args: object) -> None:
                return

            def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                key = self.headers.get("X-Refund-Idempotency", "")
                effect = store.commit(key)
                if store.drop_next_response:
                    store.drop_next_response = False
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                body = json.dumps({"id": effect}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> "FaultLab":
        self.thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request_with_one_retry(self, key: str = "") -> str:
        headers = {"Content-Type": "application/json"}
        if key:
            headers["X-Refund-Idempotency"] = key
        for attempt in range(2):
            connection = http.client.HTTPConnection(*self.server.server_address, timeout=2)
            try:
                connection.request("POST", "/refund", body='{"amount":100}', headers=headers)
                response = connection.getresponse()
                return str(json.loads(response.read())["id"])
            except (http.client.RemoteDisconnected, ConnectionResetError):
                if attempt == 1:
                    raise
            finally:
                connection.close()
        raise AssertionError("unreachable")


def run_fault_lab() -> dict[str, object]:
    with FaultLab() as unsafe:
        unsafe_id = unsafe.request_with_one_retry()
        unsafe_effects = list(unsafe.store.effects)
    with FaultLab() as safe:
        safe_id = safe.request_with_one_retry("operation-42")
        safe_effects = list(safe.store.effects)
    return {
        "fault": "first response dropped after server commit",
        "without_effect_identity": {"returned_id": unsafe_id, "effects": unsafe_effects, "count": len(unsafe_effects)},
        "with_effect_identity": {"returned_id": safe_id, "effects": safe_effects, "count": len(safe_effects)},
    }


def write_fault_report(report: dict[str, object], output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "fault-lab.json"
    markdown_path = output / "fault-lab.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unsafe = report["without_effect_identity"]
    safe = report["with_effect_identity"]
    markdown_path.write_text(
        "# Lost-response retry fault lab\n\n"
        f"Fault: **{report['fault']}**\n\n"
        f"- Without effect identity: **{unsafe['count']} effects** — `{unsafe['effects']}`\n"
        f"- With a stable idempotency key: **{safe['count']} effect** — `{safe['effects']}`\n\n"
        "This is a real loopback HTTP exchange: the server commits the first effect, closes the socket before returning a response, and the client retries once. It is a deterministic fault-injection environment, not a Razorpay account. The separate `live-refund` adapter runs the idempotent path against a user-owned Razorpay test account and refuses live keys.\n",
        encoding="utf-8",
    )
    return {"json": json_path, "markdown": markdown_path}
