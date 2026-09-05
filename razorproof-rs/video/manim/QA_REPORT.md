# RazorProof film QA report

## Release artifact

- File: `renders/RazorProof_Pitch_Silent_1080p60.mp4`
- SHA-256: `4991f8a75433fd76b543f8bb9ce29dac4e90a008907b9dc40cf8b577ae3ea494`
- Container duration: 282.983333 seconds, or 04:42.983
- Encoded size: 14,410,887 bytes
- Video: H.264, 1920 x 1080, 60 fps
- Audio: intentionally absent; narration and subtitles remain editable
- Full-stream decode: passed with no FFmpeg errors

## Narrated release artifact

- Delivery file: `audio/manipal/RazorProof_Pitch_Manipal_TTS_1080p60.mp4`
- Delivery SHA-256: `97bf4b362fe7008ff74196069dac61ebe9d1679c883205a5535cb036ad79beb3`
- Lossless-sync file: `audio/manipal/RazorProof_Pitch_Manipal_TTS_1080p60.mov`
- Lossless-sync SHA-256: `7e609e8e48211ad037ad4becfef69cadc44d0f49cc9d65524759d4e4ac9ec2bf`
- Voice: MimikaStudio custom clone `Manipal`, generated with Qwen3-TTS 0.6B Base bf16
- Video: the original H.264 stream was copied without re-encoding; its encoded-stream MD5 matches the silent master
- Lossless audio: 24-bit PCM, mono, 48 kHz, 13,583,200 samples
- Shared clock: 16,979 frames at 60 fps and exactly 800 audio samples per frame
- Duration: video and PCM audio both begin at zero and end at 282.983333 seconds
- Cue-boundary drift: zero samples, recorded for all 30 visual panels in `audio/manipal/SYNC_QA.json`
- Ground-up narration: all 30 cues were rewritten to explain the payment model, each observed failure, and RazorProof's intervention in causal order
- Spoken occupancy: 96.20% average and 91.03% minimum after time fitting; the longest measured silence is 0.833 seconds and occurs only at a panel transition
- Natural-speed gate: maximum time correction 1.078369906x; the build rejects any cue above 1.08x
- Loudness: -16.35 LUFS integrated, 3.40 LU range, -1.49 dBFS true peak
- Normalization alignment: cross-correlation peak remains at zero samples, so loudness processing introduces 0.000 ms offset
- Transition safety: all 30 cue slots have at least 120 ms of measured silence at their trailing boundary
- Captions: the 30 frame-derived cues are included as a non-default soft `mov_text` track
- Full-stream decode: passed with no FFmpeg errors

## Scene boundaries

| Scene | Start | End | Duration |
| --- | ---: | ---: | ---: |
| Alice's ₹2.01 order | 00:00.000 | 00:44.000 | 44.000 s |
| What the green check cannot prove | 00:44.000 | 01:22.000 | 38.000 s |
| Currency changes the failure | 01:22.000 | 01:58.000 | 36.000 s |
| Provider paid, application failed | 01:58.000 | 02:34.000 | 36.000 s |
| Refund, retry and webhook chain | 02:34.000 | 03:14.000 | 40.000 s |
| Executable PaymentIntent | 03:14.000 | 04:01.000 | 47.000 s |
| Provider replay | 04:01.000 | 04:28.000 | 27.000 s |
| Close | 04:28.000 | 04:42.983 | 14.983 s |

## Story and evidence checks

- Alice and Bob are the persistent explanatory device across all eight scenes.
- The film begins with a purchase story, then reveals the provider order, and only then opens the generated code.
- The opening accurately shows an accepted order creation, not a captured payment. The dashboard itself shows zero attempts and `Created` status.
- Ten unique cursor-free Razorpay dashboard or pinned-source clips are used. The self-authored RazorProof website is never shown.
- Real order, payment and refund identifiers are retained where they make the experiment replayable. Customer phone, email and other personal fields remain excluded.
- No date, time, decorative digest, random identifier, chapter marker, claim taxonomy or production prompt appears as authored on-screen text.
- The currency order table shows the current exact and generated JPY/KWD pairs with all four order IDs visible.
- The captured payment and generated mobile source are explicitly described as independently observed halves. The film does not claim that the displayed payment executed through that client.
- The fractional refund is bounded as inconsistent validation because the same fractional shape was rejected by a smaller-balance control.
- The two unkeyed retry effects use the actual processed refund IDs from captured provider webhooks.
- The Malayalam webhook example renders with a script-capable font; no missing glyphs remain.

## Mathematical layout checks

- All independent regions are validated against the 16:9 safe area before rendering.
- Pairwise axis-aligned bounds reject overlap or insufficient declared gaps.
- Speech bubbles are sized from measured text bounds and then checked for interior padding.
- The PaymentIntent and mismatch frames are sized from their contents. A second negative-tolerance containment assertion requires visible internal padding, eliminating fixed-box overflow.
- Dense rows also receive component-level collision checks for intent fields, currency rules, request/response values and service capabilities.
- Animated transfer geometry is checked separately from foreground payloads: the opening validates the ₹2.01 card's complete translation envelope, and the refund connector is split with a measured clearance around the coin.
- Screenshot borders follow exact image bounds; the selected crops are pointer-free.
- The production contact sheet was inspected at nine-second intervals. Full-resolution keyframes were separately inspected at 00:15, 01:34, 02:09, 02:51, 03:02, 03:22 and 04:06.
- Stable keyframes contain no clipped titles, overlapping text, orphan strokes or mismatched overlay frames.

## Pacing checks

- Reading time is distributed across the causal story, dashboard evidence and explanation frames instead of being appended as a long final freeze.
- Important evidence frames remain stable for approximately five to nine seconds.
- The subtitle file begins at 00:00.000 and ends at 04:42.983, matching the container to its millisecond timebase.
- Subtitle and narration boundaries are derived from actual Manim panel transitions, not a round-number timing grid.
- Each cue occupies one contiguous visual panel; no narration from a later dashboard, source clip or conclusion begins in an earlier panel.

## Executable verification

- Manim Community 0.21 rendered all eight scene modules at 1080p60 with layout assertions enabled.
- Python compilation passed for the shared primitives, scene modules and master entrypoint.
- `cargo test --workspace --all-targets` passed 26 of 26 Rust tests.
- The fresh expanded-order provider run completed every request and reproduced the exact and generated-wrong JPY/KWD order pairs.
- The evidence manifest is valid JSON and records the source, dimensions, hashes and exclusions for every new dashboard crop.

## Claim boundaries retained

- The provider stores the integer it receives; the INR mismatch is attributed to the generated integration boundary, not provider-side rounding.
- Browser-authority and signature observations are source facts. Paid tampered-cart fulfilment is not claimed.
- JPY and KWD evidence consists of created orders, not paid transactions.
- Mobile paid-but-failed is a bounded composition of an observed captured payment and a statically confirmed generated client path.
- Fractional refund persistence is one inconsistent fail-open observation, not a universal provider rule.
- Unkeyed retry effects are real provider refunds; the missing semantic identity is the integration-layer defect RazorProof prevents.
