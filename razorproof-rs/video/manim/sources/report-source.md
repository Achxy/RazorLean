# RazorProof Manim film research source

This file is the canonical research record for the rendered film. It separates animation technique from product evidence so that visual polish never upgrades a claim.

## Manim production decisions

- Target Manim Community `0.21.0` on Python `3.13`. PyPI lists `0.21.0` as the current release and requires Python 3.11 or newer: https://pypi.org/project/manim/
- Study the original 3Blue1Brown production repository as the primary reference for explanatory scene construction. Its public source uses evolving mathematical objects, matched transforms, geometric analogies, and short purposeful pauses rather than slide-like UI panels: https://github.com/3b1b/videos
- Use the original Manim example scenes as a primary technique reference for representation changes, path arcs, and matching shapes. The original project explicitly describes Manim as an engine for precise explanatory animation: https://github.com/3b1b/manim/blob/master/example_scenes.py
- Use `TransformMatchingShapes` only when a visual object keeps semantic identity while its representation changes. Official reference: https://docs.manim.community/en/stable/reference/manim.animation.transform_matching_parts.TransformMatchingShapes.html
- Use `LaggedStart` for controlled sequential reveals, with enough lag to keep dense labels readable. Official reference: https://docs.manim.community/en/stable/reference/manim.animation.composition.LaggedStart.html
- Use `MovingCameraScene` only for evidence inspection, not decorative motion. Official reference: https://docs.manim.community/en/stable/reference/manim.scene.moving_camera_scene.MovingCameraScene.html
- Use `ImageMobject` only for real Razorpay dashboard and pinned-source captures. Official reference: https://docs.manim.community/en/stable/reference/manim.mobject.types.image_mobject.ImageMobject.html
- Use `Text` and locally installed fonts instead of LaTeX so the render is deterministic on the target Mac. Official text guide: https://docs.manim.community/en/stable/guides/using_text.html
- Use `ease_in_out_sine` for major translations and camera changes; short evidence reveals use simple eased fades. Official rate-function reference: https://docs.manim.community/en/stable/reference/manim.utils.rate_functions.html

The discarded first visual passes used repeated interface cards, persistent chrome, crowded node graphs, and unexplained counters. The final entrypoint is `master_video_3b1b.py`, with independently editable chapters under `razorproof_video/scenes/`; it replaces that language with one causal value trace, clean projections, exact conversion rows, linear proof sequences, and camera-led evidence inspection.

## Primary product evidence

- `../../../../artifacts/expanded/scan.json`: source-bound scan of eight pinned official repositories.
- `../../../../artifacts/expanded/claim-ledger.md`: finding taxonomy, pinned commits, and evidence counts.
- `../../../../artifacts/chains/chained-bug-evidence.json`: six composed failure chains with each inferred edge explicitly marked.
- `../../../../artifacts/razorpay-test/campaign-summary.json`: redacted Razorpay Test Mode campaign summary.
- `../../../artifacts/real-test-mode/e2e.json`: current Rust service Test Mode order receipt.
- `../../../README.md`: Rust implementation surface, test, scan, and production-gate claims.
- `../assets/evidence/razorpay-orders-currency-pairs.png`: current exact and generated-wrong JPY/KWD orders with real order IDs and no timestamp column.
- `../assets/evidence/razorpay-undercharge-dashboard-unredacted.png`: generated INR undercharge order with its real order ID and provider amount.
- `../assets/evidence/razorpay-exact-dashboard-unredacted.png`: protected INR order with its real order ID and provider amount.
- `../assets/evidence/razorpay-captured-payment-status.png` and `razorpay-captured-payment-ids.png`: captured provider state with the payment and order IDs retained.
- `../assets/evidence/razorpay-refunded-payment-status.png` and `razorpay-refunded-payment-ids.png`: refunded provider state with the payment and order IDs retained.
- `../assets/evidence/manifest.json`: source URL, capture date, dimensions, SHA-256, and exact redactions for every dashboard capture.

Paths above are relative to this `sources` directory.

## Claim boundaries used in the film

- `DYNAMICALLY REPRODUCED`: the official code path or exact generated expression executed and produced the counterexample.
- `STATICALLY CONFIRMED`: the pinned source contains the violation; the path was not executed end-to-end.
- `TEST MODE OBSERVED`: a redacted provider effect was observed in the user's Razorpay Test account.
- `KNOWN PUBLIC`: a public issue or pull request corroborates the concern; it is not maintainer acceptance.
- `INFERRED IMPACT`: the consequence follows from evidenced nodes but was intentionally not executed.
- `PREVENTED`: traffic crossing RazorProof is stopped before the affected boundary.
- `STRUCTURALLY AVOIDED`: RazorProof does not invoke the affected implementation and keeps the relevant state isolated.
- `DETECTION ONLY`: RazorProof reports the issue but does not yet replace every affected client path.

## Non-negotiable corrections

- The protected Rust path proves a provider order for 201 INR subunits was created. It does not prove that this order was paid or captured.
- The separate captured payment is presented as independent lifecycle evidence, not as the current Rust quote-to-capture path.
- The direct Refund API result is an inconsistent fail-open validation case: `100.75` was accepted and persisted as `100` in one funded fixture, while a limited-balance negative control rejected the same fractional request. It is not universal coercion.
- Unkeyed refund retries creating separate refunds is documented identity behavior. The product gap is the agent-facing tool's omission of the stable identity mechanism.
- Cross-merchant provider consequences, paid tampered-cart fulfillment, mobile device checkout, and provider-side document handling remain unexecuted impact boundaries.
