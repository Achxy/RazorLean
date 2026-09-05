# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

"""Crop and redact live Test Mode screenshots for the public pitch render.

Raw browser captures stay in /private/tmp. Only the deliberately redacted,
presentation-ready crops are written into the project.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "evidence"


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def redact(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], label: str = "REDACTED") -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=5, fill="#17191f")
    face = font(max(10, int((y1 - y0) * 0.42)))
    bounds = draw.textbbox((0, 0), label, font=face)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    draw.text(
        ((x0 + x1 - width) / 2, (y0 + y1 - height) / 2 - 1),
        label,
        fill="#d8dce7",
        font=face,
    )


def save_dashboard() -> dict[str, object]:
    source = Path("/private/tmp/razorpay-dashboard-live.png")
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((550, 108, 1140, 175), fill="#fbfbfc")
    redact(draw, (1390, 8, 1434, 48), "")
    result = image.crop((0, 0, 1440, 755))
    path = OUT / "razorpay-dashboard-test-mode.png"
    result.save(path, optimize=True)
    return record(path, "https://dashboard.razorpay.com/app/dashboard", ["display name", "avatar initials"])


def save_orders() -> dict[str, object]:
    source = Path("/private/tmp/razorpay-orders-anomalies-live.png")
    image = Image.open(source).convert("RGB")
    # The crop excludes the order-id column while retaining the provider-rendered
    # amounts, receipts, timestamps, status pills, and the global TEST indicator.
    result = image.crop((500, 48, 1415, 670))
    path = OUT / "razorpay-orders-anomaly-matrix.png"
    result.save(path, optimize=True)
    return record(path, "https://dashboard.razorpay.com/app/orders", ["order ids excluded by crop"])


def save_order_detail() -> dict[str, object]:
    source = Path("/private/tmp/razorpay-order-detail-live.png")
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image)
    redact(draw, (1030, 66, 1355, 101), "ORDER ID")
    redact(draw, (1170, 398, 1438, 426), "HASH")
    result = image.crop((935, 54, 1438, 470))
    path = OUT / "razorpay-order-detail-bindings.png"
    result.save(path, optimize=True)
    return record(path, "https://dashboard.razorpay.com/app/orders/<redacted>", ["order id", "cart hash value"])


def save_payments() -> dict[str, object]:
    source = Path("/private/tmp/razorpay-payment-rows-live.png")
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image)
    rows = [(499, 531), (546, 579), (594, 627), (642, 675)]
    for y0, y1 in rows:
        redact(draw, (301, y0, 480, y1), "PAYMENT ID")
        redact(draw, (586, y0, 785, y1), "CUSTOMER")
    redact(draw, (1390, 8, 1434, 48), "")
    result = image.crop((282, 235, 1418, 700))
    path = OUT / "razorpay-payment-status-matrix.png"
    result.save(path, optimize=True)
    return record(path, "https://dashboard.razorpay.com/app/payments", ["payment ids", "customer phone", "customer email"])


def save_undercharge_order() -> dict[str, object]:
    source = Path("/private/tmp/razorpay-film-order-table.png")
    image = Image.open(source).convert("RGB")
    # Amount, attempts, receipt, timestamp, and provider state only. The opaque
    # order-id column and the account chrome are excluded by construction.
    result = image.crop((480, 630, 1410, 716))
    path = OUT / "razorpay-undercharge-order-row.png"
    result.save(path, optimize=True)
    return record(
        path,
        "https://dashboard.razorpay.com/app/orders",
        ["order ids excluded by crop", "account chrome excluded by crop"],
    )


def save_undercharge_detail() -> dict[str, object]:
    source = Path("/private/tmp/razorpay-film-undercharge-detail.png")
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image)
    redact(draw, (1005, 63, 1328, 101), "ORDER ID")
    # Stop before the third notes column, which is clipped by the dashboard
    # drawer itself. The evidence frame therefore contains only complete fields:
    # provider amount, currency, status, and the two causal notes we rely on.
    result = image.crop((940, 55, 1365, 468))
    path = OUT / "razorpay-undercharge-order-detail.png"
    result.save(path, optimize=True)
    return record(path, "https://dashboard.razorpay.com/app/orders/<redacted>", ["order id"])


def save_github_capture(
    source_name: str,
    output_name: str,
    source_url: str,
    crop: tuple[int, int, int, int],
) -> dict[str, object]:
    image = Image.open(Path("/private/tmp") / source_name).convert("RGB")
    result = image.crop(crop)
    path = OUT / output_name
    result.save(path, optimize=True)
    return record(
        path,
        source_url,
        ["GitHub account controls and symbols sidebar excluded by crop"],
        mode="Pinned official source",
    )


def record(path: Path, url: str, redactions: list[str], mode: str = "Razorpay Test Mode") -> dict[str, object]:
    payload = path.read_bytes()
    with Image.open(path) as image:
        dimensions = list(image.size)
    return {
        "file": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "dimensions": dimensions,
        "source_url": url,
        "captured_at": "2026-09-04 Asia/Kolkata",
        "mode": mode,
        "redactions": redactions,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    captures = [
        save_dashboard(),
        save_orders(),
        save_order_detail(),
        save_payments(),
        save_undercharge_order(),
        save_undercharge_detail(),
        save_github_capture(
            "razorpay-github-money.png",
            "github-generated-money.png",
            "https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_python.go#L24-L31",
            (8, 0, 930, 505),
        ),
        save_github_capture(
            "razorpay-github-money.png",
            "github-generated-money-clip.png",
            "https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_python.go#L24-L31",
            (48, 260, 918, 458),
        ),
        save_github_capture(
            "razorpay-github-browser-amount.png",
            "github-browser-authored-amount.png",
            "https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/frontend_templates.go#L38-L47",
            (8, 0, 930, 610),
        ),
        save_github_capture(
            "razorpay-github-browser-amount.png",
            "github-browser-authored-amount-clip.png",
            "https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/frontend_templates.go#L38-L47",
            (48, 310, 918, 470),
        ),
        save_github_capture(
            "razorpay-github-refund.png",
            "github-fractional-refund.png",
            "https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/refunds.go#L60-L77",
            (8, 0, 930, 640),
        ),
        save_github_capture(
            "razorpay-github-refund.png",
            "github-fractional-refund-clip.png",
            "https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/refunds.go#L60-L77",
            (48, 245, 918, 606),
        ),
        save_github_capture(
            "razorpay-github-dotnet.png",
            "github-dotnet-gcm-nonce.png",
            "https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/Utils.cs#L98-L107",
            (8, 0, 930, 640),
        ),
        save_github_capture(
            "razorpay-github-dotnet.png",
            "github-dotnet-gcm-nonce-clip.png",
            "https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/Utils.cs#L98-L107",
            (48, 255, 918, 500),
        ),
        save_github_capture(
            "razorpay-github-mobile.png",
            "github-mobile-empty-signature.png",
            "https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/mobile.go#L397-L412",
            (8, 0, 930, 630),
        ),
        save_github_capture(
            "razorpay-github-mobile.png",
            "github-mobile-empty-signature-clip.png",
            "https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/mobile.go#L397-L412",
            (48, 255, 918, 595),
        ),
        save_github_capture(
            "razorpay-github-verifier.png",
            "github-verifier-clip.png",
            "https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_node.go#L55-L70",
            (48, 245, 918, 535),
        ),
        save_github_capture(
            "razorpay-github-dotnet-ascii.png",
            "github-dotnet-ascii-clip.png",
            "https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/Utils.cs#L133-L136",
            (48, 365, 918, 515),
        ),
    ]
    (OUT / "manifest.json").write_text(json.dumps({"captures": captures}, indent=2) + "\n")


if __name__ == "__main__":
    main()
