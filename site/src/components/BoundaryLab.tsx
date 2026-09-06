/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useState } from "react";
import { Reorder, motion, useReducedMotion } from "motion/react";
import { blockNames, inspectProgram } from "./payment-model";
import type { Block } from "./payment-model";
import { useSequence } from "./useSequence";

export function BoundaryLab() {
  const [blocks, setBlocks] = useState<Block[]>([
    "decode",
    "verify",
    "consume",
    "match",
  ]);
  const [attempted, setAttempted] = useState(false);
  const result = inspectProgram(blocks);
  const seq = useSequence(result.stop + 1, 950);
  const reduced = useReducedMotion();
  const reorder = (next: Block[]) => {
    setBlocks(next);
    seq.reset();
    setAttempted(false);
  };
  const move = (index: number, direction: number) => {
    const next = [...blocks];
    [next[index], next[index + direction]] = [
      next[index + direction],
      next[index],
    ];
    reorder(next);
  };
  const done = attempted && seq.step === result.stop + 1;
  return (
    <div className="lab boundary-lab">
      <p className="challenge">
        Your turn: wire a trustworthy webhook handler.
      </p>
      <p>
        Drag the blocks into execution order. The event must be authenticated
        before its representation changes, and matched before it can trigger
        fulfillment.
      </p>
      <div className="program-workspace">
        <Reorder.Group
          axis="y"
          values={blocks}
          onReorder={reorder}
          className="program-blocks"
        >
          {blocks.map((block, i) => (
            <Reorder.Item
              value={block}
              key={block}
              dragListener={!seq.playing}
              layout={reduced ? undefined : true}
              className={`program-block ${attempted && seq.step > i ? (done && !result.ok && i === result.stop ? "block-failed" : "block-passed") : ""}`}
            >
              <span className="block-handle" aria-hidden="true">
                ⠿
              </span>
              <span className="block-position">{i + 1}</span>
              <b>{blockNames[block]}</b>
              <div>
                <button
                  aria-label={`Move ${blockNames[block]} up`}
                  disabled={i === 0 || seq.playing}
                  onClick={() => move(i, -1)}
                >
                  ↑
                </button>
                <button
                  aria-label={`Move ${blockNames[block]} down`}
                  disabled={i === 3 || seq.playing}
                  onClick={() => move(i, 1)}
                >
                  ↓
                </button>
              </div>
            </Reorder.Item>
          ))}
        </Reorder.Group>
        <div className="program-output">
          <small>EVENT → HANDLER</small>
          <motion.div
            className="event-token"
            animate={{ y: reduced ? 0 : Math.min(seq.step, 4) * 8 }}
            transition={{ duration: 0.4 }}
          >
            signed event
          </motion.div>
          <div className={done ? (result.ok ? "good-text" : "bad-text") : ""}>
            {done
              ? result.ok
                ? "Fulfillment permitted"
                : "Execution stopped"
              : attempted
                ? "Following your program…"
                : "Waiting for your program"}
          </div>
        </div>
      </div>
      <div className="transport">
        <button
          className="run"
          onClick={() => {
            setAttempted(true);
            seq.toggle();
          }}
        >
          {seq.playing ? "Pause" : "Run my handler →"}
        </button>
        <button
          onClick={() => {
            setAttempted(true);
            seq.next();
          }}
          disabled={done}
        >
          Step
        </button>
        <button
          onClick={() => {
            seq.reset();
            setAttempted(false);
          }}
        >
          Reset run
        </button>
      </div>
      <p className="lab-caption" aria-live="polite">
        {done
          ? result.message
          : "Two ordering mistakes are hidden in the starting program. Run it, inspect where it stops, and repair the sequence."}
      </p>
    </div>
  );
}
