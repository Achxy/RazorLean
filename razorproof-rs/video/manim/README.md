# RazorProof Manim film

A story-first, evidence-backed hackathon pitch rendered with Manim Community 0.21. Alice and Bob carry the explanation from the first frame to the last. Code appears only after its human consequence is visible, and every central defect is paired with a real Razorpay dashboard or provider response.

The visual system borrows the explanatory discipline of 3Blue1Brown: persistent semantic colour, simple characters, one causal idea per frame, meaningful transforms, and enough stillness to inspect evidence. It avoids dashboard-card montages, node graphs, decorative hashes, timestamps, chapter chrome, and meta commentary.

## Story structure

1. `opening_proof.py`: Alice creates a ₹2.01 purchase; the accepted order is ₹2.00.
2. `lost_coordinate.py`: Bob's green check proves a payment-to-order relation, not Alice's full economic promise.
3. `invariant_scanner.py`: the same fixed multiplier corrupts JPY and KWD in opposite directions.
4. `boundary_failures.py`: a captured provider payment is contrasted with a generated mobile path that omits its signature.
5. `failure_chains.py`: refund precision, retry identity and raw webhook bytes are shown as one Alice-to-Bob failure chain.
6. `semantic_firewall.py`: one typed PaymentIntent governs request creation, reconciliation, retries and fulfilment.
7. `provider_evidence.py`: broken and protected results are replayed directly on Razorpay surfaces.
8. `final_proof.py`: Alice's meaning reaches Bob unchanged, exactly once.

## Layout guarantees

- STIX Two Text is the editorial voice, Avenir Next handles prose, Menlo handles code, and Arial Unicode MS is used only for the Malayalam webhook example.
- The 16:9 safe area is encoded in `razorproof_video/shared.py`.
- Every independent region is checked with pairwise axis-aligned bounds before rendering.
- Speech bubbles and the PaymentIntent frame are derived from measured content bounds. A second containment check requires actual interior padding, preventing the overflow shown in the rejected draft.
- Screenshot borders are derived from image bounds; all selected public crops are cursor-free.
- Reading time is distributed across causal frames rather than appended as a frozen scene ending.

## Evidence policy

The film uses cursor-free clips from Razorpay's order and payment dashboards plus pinned official source. The current screenshots retain real test order, payment and refund IDs because those IDs are part of the replayable evidence. Customer email, phone and other personal fields remain excluded.

The INR undercharge order was created by executing the generated floating-point expression and submitting its integer result. The film does not say the source generator itself issued that API call. The captured payment and generated mobile code are explicitly presented as independently observed halves, not as one executed mobile transaction. The fractional refund claim remains bounded by its rejecting control.

The self-authored RazorProof website is not used anywhere in the film.

`assets/evidence/manifest.json` records source, dimensions, capture provenance and exclusions for the public evidence images.

## Render

Preview one scene:

```bash
.venv/bin/manim -ql master_video_3b1b.py OpeningProof
```

Render and concatenate the 1080p60 production film:

```bash
./render_master.sh
```

The silent visual master is `renders/RazorProof_Pitch_Silent_1080p60.mp4`.

## MimikaStudio narration

`mimika_timeline.json` binds each narration cue to the exact first and last video frame of its visual panel. At 60 fps and 48 kHz, one frame is exactly 800 audio samples, so every cue boundary is shared by both clocks without rounding drift.

Generate the `Manipal` voice-clone track through the local MimikaStudio service on port 7693:

```bash
python3 tools/build_mimika_tts.py \
  --resume \
  --timeline mimika_timeline.json \
  --video renders/RazorProof_Pitch_Silent_1080p60.mp4 \
  --output-dir audio/manipal
```

The build refuses narration requiring more than 1.08x time compression, pads every panel to its exact sample count, normalizes the completed track to broadcast speech loudness, and creates:

- `audio/manipal/RazorProof_Pitch_Manipal_TTS_1080p60.mp4`, the compact delivery file with soft captions.
- `audio/manipal/RazorProof_Pitch_Manipal_TTS_1080p60.mov`, the H.264 and 24-bit PCM lossless-sync master.
- `audio/manipal/SYNC_QA.json`, the per-cue duration, tempo, frame and sample ledger.

The long-form editorial narration is in `VOICEOVER_CUE_SHEET.md`; the exact generated take is defined in `mimika_timeline.json` and mirrored by the frame-locked `razorproof_pitch.srt`. Verification is recorded in `QA_REPORT.md`.
