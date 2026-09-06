/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { microscopeView, type PriceInspection } from "./binary64";

export const RULER_HEIGHT = 360;
const ink = "#363a36",
  muted = "#71766c",
  red = "#a84e3f",
  green = "#37765f";
export type LabelBounds = {
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
};

export function drawRuler(
  ctx: CanvasRenderingContext2D,
  model: PriceInspection,
  zoom: number,
  width: number,
) {
  const view = microscopeView(model, zoom, width);
  const { left, right, center, actualX, gridSpacing, pixelsPerUnit } = view;
  const labels: LabelBounds[] = [];
  const text = (
    value: string,
    x: number,
    y: number,
    size = 13,
    color = muted,
    align: CanvasTextAlign = "left",
  ) => {
    ctx.font = `${size}px "Source Serif 4", Georgia, serif`;
    ctx.fillStyle = color;
    ctx.textAlign = align;
    const metrics = ctx.measureText(value);
    ctx.fillText(value, x, y);
    labels.push({
      text: value,
      x:
        align === "right"
          ? x - metrics.width
          : align === "center"
            ? x - metrics.width / 2
            : x,
      y: y - size,
      width: metrics.width,
      height: size + 3,
    });
  };
  const line = (
    x: number,
    y: number,
    xx: number,
    yy: number,
    color = muted,
    dashed = false,
  ) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.setLineDash(dashed ? [3, 4] : []);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(xx, yy);
    ctx.stroke();
    ctx.setLineDash([]);
  };
  ctx.clearRect(0, 0, width, RULER_HEIGHT);
  ctx.fillStyle = "#f4f3ed";
  ctx.fillRect(0, 0, width, RULER_HEIGHT);
  const face = ctx.createLinearGradient(0, 148, 0, 229);
  face.addColorStop(0, "#e4e6de");
  face.addColorStop(0.13, "#fbfbf6");
  face.addColorStop(1, "#d9dcd2");
  ctx.fillStyle = "#b6bcb0";
  ctx.fillRect(left + 6, 173, right - left, 67);
  ctx.fillStyle = face;
  ctx.fillRect(left, 163, right - left, 64);
  line(left, 163, right, 163, "#bcc2b6");
  line(left, 227, right, 227, "#aeb5a8");
  // The two sides of the integer boundary belong to different truncation bins.
  ctx.fillStyle = "#a84e3f0b";
  ctx.fillRect(left, 163, center - left, 64);
  ctx.fillStyle = "#37765f0b";
  ctx.fillRect(center, 163, right - center, 64);
  const step = Math.pow(10, Math.ceil(Math.log10(50 / pixelsPerUnit)));
  const tickPx = step * pixelsPerUnit;
  for (
    let i = -Math.ceil((right - left) / tickPx);
    i <= Math.ceil((right - left) / tickPx);
    i++
  ) {
    const x = center + i * tickPx;
    if (x < left || x > right) continue;
    line(x, 164, x, 180, "#858d80");
    for (let minor = 1; minor < 5; minor++) {
      const xx = x + (minor * tickPx) / 5;
      if (xx < right) line(xx, 164, xx, 172, "#b7bdb0");
    }
    if (zoom < 0.05)
      text(
        String(Number(model.intended) + i * step),
        x,
        155,
        12,
        muted,
        "center",
      );
  }
  // Draw the actual binary lattice only when individual points can be resolved.
  const latticeAlpha = Math.min(1, Math.max(0, (gridSpacing - 3) / 12));
  if (latticeAlpha > 0) {
    ctx.save();
    ctx.globalAlpha = latticeAlpha;
    // Adjacent floats below powers of two have half the spacing of those above.
    const isPowerOfTwo =
      model.intended > 0n && (model.intended & (model.intended - 1n)) === 0n;
    for (let i = -24; i <= 24; i++) {
      const x = center + i * gridSpacing * (i < 0 && isPowerOfTwo ? 0.5 : 1);
      if (x < left + 2 || x > right - 2) continue;
      ctx.fillStyle = "#8a9486";
      ctx.fillRect(x - 2, 190, 4, 29);
      ctx.fillStyle = "#fcfcf6";
      ctx.fillRect(x - 2, 190, 4, 2);
    }
    ctx.restore();
  }
  const differs = model.error.numerator !== 0n;
  const point = Math.max(left + 7, Math.min(right - 7, actualX));
  line(center, 87, center, 265, green, true);
  ctx.fillStyle = green;
  ctx.beginPath();
  ctx.moveTo(center, 158);
  ctx.lineTo(center - 5, 148);
  ctx.lineTo(center + 5, 148);
  ctx.closePath();
  ctx.fill();
  text(
    `Intended: ${model.intended} paise`,
    left,
    39,
    width < 500 ? 16 : 18,
    green,
  );
  line(left, 51, center, 51, green);
  line(center, 51, center, 82, green);
  text(
    differs ? "Stored product" : "Stored product = intended",
    right,
    82,
    width < 500 ? 15 : 18,
    differs ? red : green,
    "right",
  );
  line(point, 98, right, 98, differs ? red : green);
  line(point, 98, point, 191, differs ? red : green);
  ctx.save();
  ctx.shadowColor = "#242e3540";
  ctx.shadowBlur = 5;
  ctx.shadowOffsetY = 3;
  ctx.fillStyle = differs ? red : green;
  ctx.beginPath();
  ctx.arc(point, 204, 6, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
  ctx.fillStyle = "#ffffff80";
  ctx.beginPath();
  ctx.arc(point - 1.5, 202, 1.6, 0, Math.PI * 2);
  ctx.fill();
  if (Math.abs(center - actualX) > 18) {
    line(point, 251, center, 251, red);
    line(point, 247, point, 255, red);
    line(center, 247, center, 255, red);
  }
  text(
    zoom > 0.92
      ? "Dark notches: representable numbers."
      : "Drag across the ruler to magnify the gap.",
    width / 2,
    292,
    width < 500 ? 12 : 14,
    muted,
    "center",
  );
  text(
    `Just below → ${model.intended - 1n}`,
    left,
    331,
    width < 500 ? 12 : 14,
    red,
  );
  text(
    `At the mark → ${model.intended}`,
    right,
    331,
    width < 500 ? 12 : 14,
    green,
    "right",
  );
  const outside = labels
    .filter(
      (l) =>
        l.x < 0 ||
        l.y < 0 ||
        l.x + l.width > width ||
        l.y + l.height > RULER_HEIGHT,
    )
    .map((l) => l.text);
  const overlaps: string[] = [];
  labels.forEach((a, i) =>
    labels.slice(i + 1).forEach((b) => {
      if (
        a.x < b.x + b.width &&
        a.x + a.width > b.x &&
        a.y < b.y + b.height &&
        a.y + a.height > b.y
      )
        overlaps.push(`${a.text} / ${b.text}`);
    }),
  );
  return { ...view, outside, overlaps };
}
