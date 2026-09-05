# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


def verify_signature(raw_body: bytes, signature: str, secret: bytes) -> bool:
    expected = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def ensure_secret(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(secrets.token_urlsafe(32) + "\n", encoding="utf-8")
    path.chmod(0o600)


def _redacted_headers(headers: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in {"authorization", "cookie"}:
            result[key] = "<redacted>"
        else:
            result[key] = value
    return result


class CaptureHandler(BaseHTTPRequestHandler):
    server_version = "RazorProofWebhookCapture/0.1"

    @property
    def output(self) -> Path:
        return self.server.output  # type: ignore[attr-defined]

    @property
    def secret(self) -> bytes:
        return self.server.secret  # type: ignore[attr-defined]

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._write_json(200, {"ready": True})
            return
        self._write_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        signature = self.headers.get("X-Razorpay-Signature", "")
        signature_valid = bool(signature) and verify_signature(
            raw_body, signature, self.secret
        )
        try:
            decoded = raw_body.decode("utf-8")
            body_text: str | None = decoded
            literal_non_ascii = any(ord(character) > 127 for character in decoded)
        except UnicodeDecodeError:
            body_text = None
            literal_non_ascii = False
        now = datetime.now(timezone.utc)
        capture = {
            "captured_at": now.isoformat(),
            "path": self.path,
            "headers": _redacted_headers(self.headers),
            "signature_present": bool(signature),
            "signature_valid": signature_valid,
            "raw_body_base64": base64.b64encode(raw_body).decode(),
            "raw_body_utf8": body_text,
            "raw_body_sha256": hashlib.sha256(raw_body).hexdigest(),
            "literal_non_ascii": literal_non_ascii,
            "json_valid": False,
            "event": None,
        }
        if body_text is not None:
            try:
                parsed = json.loads(body_text)
                capture["json_valid"] = True
                capture["event"] = parsed.get("event") if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                pass
        self.output.mkdir(parents=True, exist_ok=True)
        stamp = now.strftime("%Y%m%dT%H%M%S.%fZ")
        destination = self.output / f"capture-{stamp}.json"
        serialized = json.dumps(capture, indent=2, ensure_ascii=False) + "\n"
        destination.write_text(serialized, encoding="utf-8")
        destination.chmod(0o600)
        latest = self.output / "latest.json"
        latest.write_text(serialized, encoding="utf-8")
        latest.chmod(0o600)
        self._write_json(200, {"received": True})

    def log_message(self, format: str, *args: object) -> None:
        # Do not echo request paths, headers, or provider identifiers to stdout.
        return


def serve(host: str, port: int, output: Path, secret_path: Path) -> None:
    ensure_secret(secret_path)
    secret = secret_path.read_text(encoding="utf-8").strip().encode()
    if not secret:
        raise ValueError("webhook secret must not be empty")
    server = ThreadingHTTPServer((host, port), CaptureHandler)
    server.output = output  # type: ignore[attr-defined]
    server.secret = secret  # type: ignore[attr-defined]
    print(json.dumps({
        "ready": True,
        "bind": f"{host}:{port}",
        "capture_directory": str(output),
        "secret_path": str(secret_path),
    }), flush=True)
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture raw Razorpay Test webhooks")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--secret-file", type=Path, required=True)
    args = parser.parse_args(argv)
    serve(args.host, args.port, args.output, args.secret_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
