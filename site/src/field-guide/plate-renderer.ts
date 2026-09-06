/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import type { GuideCase } from "./cases";

export const PLATE_WIDTH = 760;
export const PLATE_HEIGHT = 430;
const ink = "#302f2a",
  muted = "#706a5a",
  red = "#a83f32",
  green = "#416d58",
  blue = "#3c617e",
  paper = "#e9e2cf";
type Bounds = {
  x: number;
  y: number;
  width: number;
  height: number;
  text: string;
};
export type PlateReport = { overlaps: string[]; outside: string[] };

class Pen {
  ctx: CanvasRenderingContext2D;
  bounds: Bounds[] = [];
  constructor(ctx: CanvasRenderingContext2D) {
    this.ctx = ctx;
  }
  text(
    value: string,
    x: number,
    y: number,
    width = 660,
    size = 15,
    color = ink,
    serif = false,
  ) {
    const c = this.ctx;
    c.fillStyle = color;
    const font = serif
      ? '"Source Serif 4", Georgia, serif'
      : '"Inter", sans-serif';
    let actual = size;
    c.font = `${actual}px ${font}`;
    while (c.measureText(value).width > width && actual > 10) {
      actual -= 0.5;
      c.font = `${actual}px ${font}`;
    }
    const measure = c.measureText(value);
    c.fillText(value, x, y);
    this.bounds.push({
      x,
      y: y - actual,
      width: measure.width,
      height: actual + 2,
      text: value,
    });
  }
  line(
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    color = muted,
    dash = false,
  ) {
    const c = this.ctx;
    c.strokeStyle = color;
    c.lineWidth = 1;
    c.setLineDash(dash ? [4, 5] : []);
    c.beginPath();
    c.moveTo(x1, y1);
    c.lineTo(x2, y2);
    c.stroke();
    c.setLineDash([]);
  }
  rect(
    x: number,
    y: number,
    w: number,
    h: number,
    color = muted,
    hatch = false,
  ) {
    const c = this.ctx;
    c.fillStyle = paper;
    c.fillRect(x, y, w, h);
    c.strokeStyle = color;
    c.lineWidth = 1;
    c.strokeRect(x, y, w, h);
    if (hatch) {
      c.save();
      c.beginPath();
      c.rect(x, y, w, h);
      c.clip();
      c.globalAlpha = 0.12;
      for (let n = -h; n < w; n += 6)
        this.line(x + n, y + h, x + n + h, y, color);
      c.restore();
    }
  }
  circle(x: number, y: number, r: number, color = ink, fill = false) {
    const c = this.ctx;
    c.beginPath();
    c.arc(x, y, r, 0, Math.PI * 2);
    c.strokeStyle = color;
    c.lineWidth = 1.5;
    c.stroke();
    if (fill) {
      c.fillStyle = color;
      c.fill();
    }
  }
  arrow(
    x: number,
    y: number,
    endX: number,
    endY: number,
    color = muted,
    progress = 1,
  ) {
    this.line(x, y, endX, endY, color, true);
    const px = x + (endX - x) * progress,
      py = y + (endY - y) * progress;
    this.circle(px, py, 3, color, true);
    const a = Math.atan2(endY - y, endX - x);
    this.line(
      endX,
      endY,
      endX - 8 * Math.cos(a - 0.45),
      endY - 8 * Math.sin(a - 0.45),
      color,
    );
    this.line(
      endX,
      endY,
      endX - 8 * Math.cos(a + 0.45),
      endY - 8 * Math.sin(a + 0.45),
      color,
    );
  }
  ticket(
    x: number,
    y: number,
    w: number,
    h: number,
    title: string,
    color = ink,
  ) {
    this.rect(x, y, w, h, color);
    this.text(title, x + 14, y + 28, w - 28, 15, color, true);
    this.line(x + 10, y + 42, x + w - 10, y + 42, color, true);
    for (let n = 10; n < w - 8; n += 13)
      this.line(x + n, y + h - 4, x + n + 5, y + h, color);
  }
  stamp(label: string, x: number, y: number, color = red, width = 170) {
    this.rect(x, y, width, 34, color, true);
    this.text(label, x + 10, y + 23, width - 20, 13, color);
  }
  report(): PlateReport {
    const outside = this.bounds
      .filter(
        (b) =>
          b.x < 0 ||
          b.y < 0 ||
          b.x + b.width > PLATE_WIDTH ||
          b.y + b.height > PLATE_HEIGHT,
      )
      .map((b) => b.text);
    const overlaps: string[] = [];
    this.bounds.forEach((a, i) =>
      this.bounds.slice(i + 1).forEach((b) => {
        if (
          a.x < b.x + b.width &&
          a.x + a.width > b.x &&
          a.y < b.y + b.height &&
          a.y + a.height > b.y
        )
          overlaps.push(`${a.text} / ${b.text}`);
      }),
    );
    return { outside, overlaps };
  }
}

function grain(ctx: CanvasRenderingContext2D) {
  ctx.fillStyle = paper;
  ctx.fillRect(0, 0, PLATE_WIDTH, PLATE_HEIGHT);
  let state = 9317;
  const random = () => {
    state = (state * 16807) % 2147483647;
    return state / 2147483647;
  };
  ctx.fillStyle = "#403927";
  for (let i = 0; i < 6500; i++) {
    ctx.globalAlpha = random() * 0.055;
    ctx.fillRect(
      random() * PLATE_WIDTH,
      random() * PLATE_HEIGHT,
      random() * 1.5 + 0.3,
      0.6,
    );
  }
  ctx.globalAlpha = 1;
}

export function paintPlate(
  ctx: CanvasRenderingContext2D,
  item: GuideCase,
  step: number,
  travel = 1,
): PlateReport {
  grain(ctx);
  const p = new Pen(ctx),
    broken = step >= 2 && step < 3,
    fixed = step === 3;
  p.text(item.group.toUpperCase(), 28, 30, 300, 11, muted);
  p.text("ILLUSTRATED MECHANISM · NOT A LIVE REQUEST", 382, 30, 350, 10, muted);
  p.line(28, 43, 732, 43, "#c2b8a1");
  const mode = fixed
    ? "CORRECTED CONTRACT"
    : broken
      ? "WHERE MEANING CHANGES"
      : "FOLLOW THE REPRESENTATION";
  p.text(mode, 28, 402, 700, 11, fixed ? green : broken ? red : muted);

  switch (item.plate) {
    case "fraction": {
      p.text(
        "The input arrives in indivisible subunits",
        50,
        85,
        640,
        22,
        ink,
        true,
      );
      p.ticket(50, 112, 275, 205, "Refund instruction");
      p.text("100", 75, 228, 150, 62, ink, true);
      p.text(".75", 209, 228, 90, 48, broken ? red : muted, true);
      p.line(198, 168, 198, 289, red, true);
      p.text("integer", 77, 283, 110, 12, muted);
      p.text("fraction", 217, 283, 90, 12, red);
      p.arrow(347, 218, 411, 218, fixed ? green : red, travel);
      p.ticket(
        435,
        112,
        275,
        205,
        fixed ? "Validation boundary" : "Outgoing request",
      );
      p.text(
        fixed ? "No write" : broken ? "100" : "?",
        461,
        228,
        220,
        48,
        fixed ? green : red,
        true,
      );
      p.text(
        fixed ? "Fractional input rejected" : "The cast cannot preserve .75",
        457,
        283,
        230,
        12,
        muted,
      );
      break;
    }
    case "float": {
      p.text(
        "A microscope on the integer boundary",
        45,
        84,
        680,
        22,
        ink,
        true,
      );
      p.text("₹2.01", 50, 141, 210, 38, ink, true);
      p.text("× 100", 247, 140, 130, 27, muted, true);
      p.text(
        fixed ? "exact integer: 201" : "200.99999999999997",
        425,
        140,
        285,
        24,
        fixed ? green : red,
        true,
      );
      p.rect(45, 181, 670, 100, muted, true);
      for (let i = 0; i <= 20; i++)
        p.line(65 + i * 31.5, 255, 65 + i * 31.5, i % 5 ? 245 : 232, muted);
      p.line(65, 255, 695, 255, ink);
      p.line(655, 194, 655, 267, green);
      p.circle(fixed ? 655 : 642, 212, 5, fixed ? green : red, true);
      p.text(
        fixed ? "on the mark" : "just below",
        521,
        206,
        105,
        12,
        fixed ? green : red,
      );
      p.text("201", 649, 309, 60, 25, green, true);
      p.text(
        fixed ? "decimal → integer subunits" : "200  ←  truncation",
        62,
        309,
        440,
        24,
        fixed ? green : broken ? red : muted,
        true,
      );
      p.text(
        "Schematic magnification; distance is not to scale.",
        50,
        351,
        660,
        12,
        muted,
      );
      break;
    }
    case "currency": {
      p.text("The unit determines the scale", 45, 85, 665, 22, ink, true);
      const rows = [
        ["JPY 295", "295", "29,500", 1],
        ["INR 2.01", "201", "201 (rounded)", 2],
        ["KWD 295.990", "295,990", "29,599", 3],
      ];
      rows.forEach((r, i) => {
        const y = 115 + i * 81;
        p.text(String(r[0]), 45, y + 25, 160, 17, ink, true);
        p.rect(219, y, 239, 40, muted, true);
        p.text(
          fixed ? ["×1", "×100", "×1000"][i] : "×100",
          234,
          y + 27,
          85,
          20,
          fixed ? green : muted,
          true,
        );
        p.text(
          fixed
            ? ["0 decimal places", "2 decimal places", "3 decimal places"][i]
            : "2 decimal places",
          327,
          y + 25,
          120,
          11,
          fixed ? green : muted,
        );
        p.text(
          fixed ? String(r[1]) : step >= 1 ? String(r[2]) : "—",
          495,
          y + 29,
          215,
          25,
          fixed ? green : i === 1 ? muted : red,
          true,
        );
      });
      p.text(
        "Three currencies. Three unit contracts. One invalid universal rule.",
        45,
        367,
        670,
        12,
        muted,
      );
      break;
    }
    case "quote": {
      p.ticket(50, 90, 275, 238, "Bob’s server quote", blue);
      p.ticket(435, 90, 275, 238, "Provider order", green);
      ["catalogue price", "cart identity", "merchant", "consume once"].forEach(
        (s, i) => p.text(s, 72, 161 + i * 31, 230, 15),
      );
      ["order identifier", "payment identifier", "provider signature"].forEach(
        (s, i) => p.text(s, 457, 161 + i * 31, 230, 15),
      );
      p.stamp("AUTHENTIC TUPLE", 457, 267, green, 220);
      p.arrow(329, 196, 429, 196, fixed ? green : red, travel);
      p.text(
        fixed ? "MATCH" : "UNBOUND",
        339,
        230,
        83,
        11,
        fixed ? green : red,
      );
      p.text(
        fixed
          ? "Only the matched, unconsumed quote authorizes fulfillment."
          : "Authenticity of the right-hand record does not establish the left-hand record.",
        50,
        363,
        660,
        13,
        fixed ? green : muted,
      );
      break;
    }
    case "length": {
      p.text("Validate the shape before comparing", 45, 85, 660, 22, ink, true);
      [0, 1].forEach((row) => {
        const y = 137 + row * 103;
        p.text(row ? "RECEIVED" : "EXPECTED", 45, y - 16, 660, 11, muted);
        for (let i = 0; i < 32; i++)
          p.rect(
            45 + i * 20.8,
            y,
            17,
            38,
            row && i > 0 ? "#c9bfab" : row ? red : blue,
            row === 0,
          );
        p.text(
          row ? "wrong length" : "32 decoded bytes",
          45,
          y + 62,
          660,
          13,
          row ? red : blue,
        );
      });
      p.stamp(
        fixed
          ? "CONTROLLED REJECTION"
          : broken
            ? "LENGTH EXCEPTION"
            : "PRECONDITION REQUIRED",
        415,
        330,
        fixed ? green : red,
        290,
      );
      break;
    }
    case "envelope": {
      p.text("The callback is a data envelope", 45, 85, 665, 22, ink, true);
      p.rect(115, 115, 530, 216, muted, true);
      p.line(115, 115, 380, 216);
      p.line(645, 115, 380, 216);
      item.labels.forEach((label, i) => {
        const x = 147 + i * 157;
        p.rect(x, 178, 147, 116, i === 2 && !fixed && step > 0 ? red : green);
        p.text(label, x + 11, 208, 125, 13);
        p.text(
          step === 0 ? "required" : i === 2 && !fixed ? "EMPTY" : "present",
          x + 11,
          259,
          125,
          17,
          i === 2 && !fixed && step > 0 ? red : green,
          true,
        );
      });
      p.text(
        fixed
          ? "Use the data-bearing callback; preserve all required fields."
          : "A success notification is not necessarily a complete verification result.",
        45,
        367,
        665,
        13,
        muted,
      );
      break;
    }
    case "package": {
      p.text("Follow the package’s provenance", 45, 85, 665, 22, ink, true);
      const labels = ["Package name", "Publisher", "Linked repository"];
      labels.forEach((label, i) => {
        const x = 45 + i * 232;
        p.ticket(x, 121, 207, 191, label, fixed ? green : muted);
        p.text(
          i === 0
            ? "SDK-like name"
            : i === 1
              ? fixed
                ? "official owner"
                : "verify owner"
              : fixed
                ? "official source"
                : "verify source",
          x + 15,
          210,
          177,
          18,
          fixed ? green : red,
          true,
        );
        p.text(
          i === 0
            ? "spelling ≠ ownership"
            : i === 1
              ? "registry metadata"
              : "repository identity",
          x + 15,
          272,
          177,
          11,
          muted,
        );
      });
      p.text(
        "The official package identity in this investigation: com.razorpay.cordova",
        45,
        356,
        665,
        14,
        green,
      );
      break;
    }
    case "query": {
      p.text(
        "A list cannot fit in a single-value slot",
        45,
        85,
        665,
        22,
        ink,
        true,
      );
      p.ticket(45, 125, 230, 180, "Requested expansion");
      p.text("payments", 64, 205, 180, 20, blue, true);
      p.text("transfers", 64, 254, 180, 20, green, true);
      p.arrow(295, 220, 386, 220, muted, travel);
      p.ticket(
        405,
        125,
        310,
        180,
        fixed ? "Multi-value query" : "Single map slot",
      );
      p.text("expand[]", 424, 201, 120, 16, muted);
      p.text(
        fixed ? "payments" : step >= 1 ? "transfers" : "payments",
        554,
        201,
        142,
        17,
        fixed ? blue : red,
        true,
      );
      if (fixed) {
        p.text("expand[]", 424, 253, 120, 16, muted);
        p.text("transfers", 554, 253, 142, 17, green, true);
      }
      p.text(
        fixed
          ? "Both occurrences survive URL encoding."
          : "Assignment replaces the old value; it does not append another occurrence.",
        45,
        356,
        670,
        13,
        muted,
      );
      break;
    }
    case "retry": {
      p.text(
        "Count intentions separately from attempts",
        45,
        85,
        665,
        22,
        ink,
        true,
      );
      p.ticket(45, 117, 212, 206, "Bob’s refund intent");
      p.text("ONE REFUND", 63, 226, 176, 20, blue, true);
      p.arrow(278, 176, 468, 176, muted, travel);
      p.text("first attempt", 304, 152, 155, 13);
      p.arrow(278, 270, 468, 270, muted, travel);
      p.text("retry", 337, 248, 125, 13);
      p.stamp("effect 1", 492, 152, green, 200);
      p.stamp(
        fixed ? "same result" : "effect 2 possible",
        492,
        246,
        fixed ? green : red,
        200,
      );
      p.text(
        fixed
          ? "A stable receipt already identifies one effect in the documented API."
          : "With no stable identity, the next request can intentionally mean a new refund.",
        45,
        365,
        670,
        13,
        muted,
      );
      break;
    }
    case "registry": {
      p.text(
        "The interface directory and the registry",
        45,
        85,
        665,
        22,
        ink,
        true,
      );
      p.ticket(45, 123, 670, 90, "Published tool name");
      p.text(
        fixed ? item.labels[1] : item.labels[0],
        66,
        194,
        620,
        20,
        fixed ? green : red,
        true,
      );
      p.ticket(45, 240, 670, 90, "Registered tool name");
      p.text(item.labels[1], 66, 311, 620, 20, green, true);
      p.text(
        fixed
          ? "One definition supplies both surfaces."
          : "Exact identifiers must agree before any API request can be dispatched.",
        45,
        367,
        665,
        13,
        muted,
      );
      break;
    }
    case "encoding": {
      p.text(
        "The character changes representation",
        45,
        85,
        665,
        22,
        ink,
        true,
      );
      p.text("₹", 65, 220, 160, 100, blue, true);
      ["E2", "82", "B9"].forEach((s, i) => {
        p.rect(253 + i * 146, 117, 115, 66, blue, true);
        p.text(s, 280 + i * 146, 160, 70, 23, blue, true);
      });
      p.text("original UTF-8 bytes", 253, 215, 430, 14, blue);
      ["E2", "82", "B9"]
        .slice(0, step === 0 ? 0 : fixed ? 3 : 1)
        .forEach((s, i) => {
          p.rect(253 + i * 146, 256, 115, 66, fixed ? green : red, true);
          p.text(
            fixed ? s : "3F",
            280 + i * 146,
            299,
            70,
            23,
            fixed ? green : red,
            true,
          );
        });
      p.text(
        step === 0
          ? "These are the bytes the signature authenticates."
          : fixed
            ? "original bytes preserved"
            : "ASCII replacement: ?",
        253,
        354,
        435,
        14,
        fixed ? green : red,
      );
      break;
    }
    case "nonce": {
      p.text(
        "GCM’s per-key uniqueness requirement",
        45,
        85,
        665,
        22,
        ink,
        true,
      );
      [0, 1].forEach((i) => {
        p.ticket(55 + i * 365, 117, 285, 211, item.labels[i]);
        p.text("same encryption key", 74 + i * 365, 191, 247, 14, muted);
        p.circle(130 + i * 365, 251, 29, fixed ? green : red);
        p.text(
          step === 0 && i ? "?" : fixed ? (i ? "B" : "A") : "A",
          120 + i * 365,
          260,
          32,
          24,
          fixed ? green : red,
          true,
        );
        p.text("nonce", 178 + i * 365, 256, 130, 16);
      });
      p.text(
        step === 0
          ? "The next invocation needs a different nonce under this key."
          : fixed
            ? "Different seal numbers under one key. Letters are illustrative identities."
            : "Same seal number under one key. This violates the prerequisite, not just formatting.",
        45,
        365,
        670,
        13,
        fixed ? green : red,
      );
      break;
    }
    case "comparison": {
      p.text(item.labels[0], 45, 85, 665, 22, ink, true);
      [0, 1].forEach((row) => {
        p.text(
          row ? "TIMING CONTRACT" : "BOOLEAN CONTRACT",
          45,
          136 + row * 106,
          665,
          11,
          muted,
        );
        for (let i = 0; i < 24; i++) {
          p.rect(
            45 + i * 28,
            151 + row * 106,
            22,
            38,
            row && !fixed ? muted : green,
            row === 0 || fixed,
          );
        }
      });
      p.text("Correct equality result", 45, 214, 670, 13, green);
      p.text(
        fixed
          ? `Use ${item.labels[2]} after validating input shape.`
          : "Not specified by ordinary equality; these cells are not measured timings.",
        45,
        330,
        670,
        13,
        fixed ? green : muted,
      );
      break;
    }
    case "permutation": {
      p.text(
        "Named fields need a canonical sentence",
        45,
        85,
        665,
        22,
        ink,
        true,
      );
      const order = fixed || step === 0 ? [0, 1, 2, 3] : [3, 0, 1, 2];
      [0, 1].forEach((row) => {
        p.text(
          row ? "SERIALIZED ORDER" : "PROTOCOL ORDER",
          45,
          127 + row * 131,
          665,
          11,
          muted,
        );
        (row ? order : [0, 1, 2, 3]).forEach((n, i) => {
          p.rect(
            45 + i * 173,
            147 + row * 131,
            151,
            49,
            row && n !== i ? red : blue,
            true,
          );
          p.text(
            item.labels[n],
            57 + i * 173,
            177 + row * 131,
            126,
            15,
            row && n !== i ? red : blue,
          );
        });
      });
      p.text(
        fixed
          ? "Read by field name in fixed order, regardless of Hash insertion order."
          : "The same values move to different positions in the authenticated message.",
        45,
        365,
        670,
        13,
        muted,
      );
      break;
    }
    case "adapter": {
      p.text(
        "Preserving bytes should not require an adapter",
        45,
        85,
        665,
        22,
        ink,
        true,
      );
      p.ticket(45, 125, 255, 193, "Framework request body", blue);
      p.text("bytes", 65, 244, 210, 49, blue, true);
      p.arrow(323, 220, 429, 220, fixed ? green : red, travel);
      p.ticket(450, 125, 265, 193, "Verifier input", fixed ? green : red);
      p.text(
        fixed ? "bytes" : "str only",
        470,
        244,
        225,
        43,
        fixed ? green : red,
        true,
      );
      p.text(
        fixed
          ? "The byte sequence passes through unchanged."
          : "Re-encoding a bytes object raises before comparison.",
        45,
        365,
        665,
        13,
        fixed ? green : red,
      );
      break;
    }
    case "checklist": {
      p.text(
        "Every required access needs a matching guard",
        45,
        85,
        665,
        22,
        ink,
        true,
      );
      p.ticket(45, 112, 670, 223, "Required callback fields");
      [
        "payment identifier",
        "payment status",
        "payment-link reference",
        "payment_link_id",
      ].forEach((s, i) => {
        const y = 176 + i * 38;
        p.rect(
          66,
          y - 17,
          19,
          19,
          i === 3 && !fixed ? red : green,
          i < 3 || fixed,
        );
        p.text(s, 105, y, 380, 16);
        p.text(
          i === 3 && !fixed ? "unguarded lookup" : "checked",
          488,
          y,
          195,
          13,
          i === 3 && !fixed ? red : green,
        );
      });
      p.text(
        fixed
          ? "Reject the missing field before touching the map."
          : "The absent guard lets a missing key become an exception.",
        45,
        367,
        665,
        13,
        muted,
      );
      break;
    }
    case "charset": {
      p.text(
        "Do not delegate the protocol to the host",
        45,
        85,
        665,
        22,
        ink,
        true,
      );
      [0, 1].forEach((i) => {
        const x = 45 + i * 353;
        p.rect(x, 118, 317, 206, i ? red : blue, true);
        p.rect(x + 17, 139, 283, 112, muted);
        p.text(item.labels[i], x + 32, 168, 253, 17, ink, true);
        p.text(
          fixed ? "UTF-8 explicitly" : "getBytes()",
          x + 32,
          216,
          250,
          20,
          fixed ? green : muted,
          true,
        );
        p.text(
          fixed
            ? "same protocol bytes"
            : i
              ? "default may differ"
              : "UTF-8 bytes",
          x + 22,
          294,
          270,
          15,
          fixed ? green : i ? red : blue,
        );
      });
      p.text(
        "Conditional on runtime/configuration. Java 18+ defaults to UTF-8.",
        45,
        365,
        670,
        13,
        muted,
      );
      break;
    }
    case "routing": {
      p.text(item.labels[2], 45, 85, 665, 22, ink, true);
      p.ticket(45, 114, 229, 97, item.labels[0], blue);
      p.text("operation A", 63, 186, 195, 17, blue, true);
      p.ticket(45, 242, 229, 97, item.labels[1], green);
      p.text("operation B", 63, 314, 195, 17, green, true);
      if (fixed) {
        [0, 1].forEach((i) => {
          const y = 114 + i * 128;
          p.rect(458, y, 258, 97, i ? green : blue, true);
          p.text(
            i ? "B’s own context" : "A’s own context",
            480,
            y + 55,
            213,
            19,
            i ? green : blue,
            true,
          );
          p.arrow(293, y + 49, 439, y + 49, i ? green : blue, travel);
        });
      } else {
        p.rect(458, 146, 258, 160, red, true);
        p.text("PROCESS-WIDE", 479, 176, 217, 12, muted);
        p.text(
          step >= 1 ? "context B" : "context A",
          479,
          226,
          217,
          29,
          step >= 1 ? red : blue,
          true,
        );
        p.text("one mutable drawer", 479, 273, 217, 13, muted);
        p.arrow(293, 160, 439, 207, blue, travel);
        p.arrow(293, 290, 439, 245, green, travel);
      }
      p.text(
        fixed
          ? "Ownership follows the client, even when requests interleave."
          : "An object boundary does not isolate state stored outside that object.",
        45,
        373,
        670,
        13,
        muted,
      );
      break;
    }
    case "mime": {
      p.text(
        "The contents and the label must agree",
        45,
        85,
        665,
        22,
        ink,
        true,
      );
      p.ticket(65, 117, 280, 222, "proof.png", blue);
      p.rect(87, 179, 233, 109, blue, true);
      p.circle(275, 205, 12, blue);
      p.line(100, 271, 165, 212, blue);
      p.line(165, 212, 216, 260, blue);
      p.line(216, 260, 256, 231, blue);
      p.line(256, 231, 309, 278, blue);
      p.arrow(366, 221, 422, 221, fixed ? green : red, travel);
      p.ticket(445, 117, 270, 222, "Content-Type");
      p.text(
        fixed ? "image/png" : "image/pdf",
        465,
        238,
        230,
        27,
        fixed ? green : red,
        true,
      );
      p.text("header ≠ file conversion", 465, 304, 230, 12, muted);
      break;
    }
    case "multipart": {
      p.text(
        "A cutaway of the outgoing multipart body",
        45,
        85,
        665,
        22,
        ink,
        true,
      );
      p.rect(65, 113, 630, 232, muted);
      p.text("— multipart boundary —", 83, 138, 590, 12, muted);
      p.rect(84, 153, 592, 66, blue, true);
      p.text('name="file" · binary image bytes', 104, 191, 550, 17, blue, true);
      p.text("— multipart boundary —", 83, 243, 590, 12, muted);
      p.rect(
        84,
        258,
        592,
        66,
        step === 0 ? muted : fixed ? green : red,
        step > 0 && !fixed,
      );
      p.text(
        step === 0
          ? "metadata loop has not run yet"
          : fixed
            ? "ordinary metadata only · file excluded from this loop"
            : 'name="file" · text pathname',
        104,
        296,
        550,
        17,
        step === 0 ? muted : fixed ? green : red,
        true,
      );
      p.text(
        step === 0
          ? "One file part so far. Next, the serializer walks the remaining fields."
          : fixed
            ? "Exactly one binary file part."
            : "The duplicate name makes receiver interpretation ambiguous.",
        65,
        372,
        630,
        13,
        fixed ? green : red,
      );
      break;
    }
  }
  return p.report();
}
