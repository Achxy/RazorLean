/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useEffect, useRef, useState } from "react";

export function BytesLab() {
  const [text, setText] = useState("Hello ₹");
  const [selected, setSelected] = useState(6);
  const canvas = useRef<HTMLCanvasElement>(null);
  const characters = Array.from(text);
  const character = characters[selected] || "";
  const utf8 = Array.from(new TextEncoder().encode(character));
  const ascii = character
    ? character.codePointAt(0)! > 127
      ? [63]
      : [character.charCodeAt(0)]
    : [];
  const equal =
    utf8.length === ascii.length && utf8.every((byte, i) => byte === ascii[i]);
  useEffect(() => {
    const el = canvas.current;
    if (!el) return;
    const ctx = el.getContext("2d");
    if (!ctx) return;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    el.width = 760 * ratio;
    el.height = 190 * ratio;
    ctx.scale(ratio, ratio);
    ctx.clearRect(0, 0, 760, 190);
    const drawRow = (
      bytes: number[],
      y: number,
      color: string,
      label: string,
    ) => {
      ctx.font = "16px 'Source Serif 4', serif";
      ctx.fillStyle = "#bbb8ae";
      ctx.fillText(label, 20, y + 23);
      bytes.forEach((byte, i) => {
        const x = 195 + i * 118;
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, 100, 40);
        ctx.fillStyle = color;
        ctx.font = "16px 'JetBrains Mono', monospace";
        ctx.fillText(
          byte.toString(16).toUpperCase().padStart(2, "0"),
          x + 37,
          y + 25,
        );
      });
    };
    drawRow(utf8, 20, "#81a981", "Original UTF-8");
    drawRow(ascii, 125, equal ? "#81a981" : "#dd745f", "Re-encoded ASCII");
    ctx.strokeStyle = "#55554a";
    ctx.setLineDash([3, 5]);
    utf8.forEach((_, i) => {
      ctx.beginPath();
      ctx.moveTo(245 + i * 118, 65);
      ctx.lineTo(245, 119);
      ctx.stroke();
    });
    ctx.setLineDash([]);
    ctx.fillStyle = "#bbb8ae";
    ctx.font = "15px 'Source Serif 4', serif";
    ctx.fillText(equal ? "same byte" : "replacement character: ?", 430, 151);
  }, [character, equal, utf8.join(","), ascii.join(",")]);
  return (
    <div className="lab bytes-lab">
      <label className="byte-input">
        A small piece of the payload
        <input
          aria-label="Payload text"
          value={text}
          maxLength={24}
          onChange={(e) => {
            setText(e.target.value);
            setSelected(0);
          }}
        />
      </label>
      <div
        className="character-strip"
        role="group"
        aria-label="Select a character"
      >
        {characters.map((ch, i) => (
          <button
            key={i}
            onClick={() => setSelected(i)}
            aria-pressed={selected === i}
            aria-label={`Character ${i + 1}: ${ch === " " ? "space" : ch}`}
          >
            {ch === " " ? "␠" : ch}
          </button>
        ))}
      </div>
      <div className="diagram-scroll">
        <canvas
          ref={canvas}
          className="bytes-canvas"
          role="img"
          aria-label={`Selected ${character}. UTF-8 bytes ${utf8.join(", ")}; ASCII bytes ${ascii.join(", ")}. ${equal ? "Same bytes" : "Different bytes"}.`}
        />
      </div>
      <p
        className={`lab-caption ${equal ? "good-text" : "bad-text"}`}
        aria-live="polite"
      >
        {!character
          ? "Type a short payload above, then select a character to inspect its bytes."
          : equal
            ? "This character survives ASCII encoding. Now select ₹ or type a non-ASCII character."
            : `“${character}” becomes “?” under ASCII replacement. The verifier would authenticate a different byte sequence from the original message.`}
      </p>
      <p className="try-note">
        Click a character to trace its bytes. Each box contains one hexadecimal
        byte. The safe boundary verifies the untouched request body before
        decoding it.
      </p>
    </div>
  );
}
