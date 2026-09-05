# RazorProof video storyboard

## Visual grammar

- **Camera:** human stakes and conviction.
- **Notebook:** concepts that should feel discovered rather than advertised.
- **Manim:** invisible financial state, identity, and causal chains.
- **Screen recording:** executable proof.
- **Source macro shots:** forensic credibility, never filler montage.
- **Sound:** one restrained success tone, pencil/marker texture, quiet mechanical ticks for state transitions. No generic corporate music swell.

Use the control-room palette throughout: warm paper `#F2EEE5`, ink `#15130F`, Razorpay blue `#2F63F5`, stopped-defect vermilion `#DC4C36`, and evidence gold `#D6A53A`.

## Edit timeline

| Time | Chapter | Picture | Narration purpose | Required capture |
|---|---|---|---|---|
| 0:00–0:04 | Cold open | Black; success tone; green `PAYMENT CAPTURED` appears | Establish apparent success | Manim `ValidButWrong` opening |
| 0:04–0:12 | Cold open | Order card: signature ✓, order ✓, amount `200` | Reveal contradiction | Manim |
| 0:12–0:22 | Discovery | Medium camera shot; notebook already open | Put a human behind the investigation | A-roll take 1 |
| 0:22–0:32 | Discovery | Overhead notebook: `₹2.01 → 200` | Make the failure tactile | Notebook shot N1 |
| 0:32–0:42 | Escalation | JPY explodes 100×; KWD collapses 10× | Show this is economically material | Manim `CurrencyExponent` |
| 0:42–0:52 | Rabbit hole | Repository names assemble as eight pinned cards | Establish breadth | Screen/source montage S1 |
| 0:52–1:08 | Rabbit hole | Exact source lines: static credentials, fixed nonce, ASCII | Escalate severity | Source shots S2–S4 |
| 1:08–1:24 | Rabbit hole | Three concise counters: `23`, `17`, `6` | Quantify without overwhelming | Motion typography |
| 1:24–1:47 | Missing layer | Overhead notebook draws Intent → Provider → Fulfillment | Teach the thesis | Notebook shot N2 |
| 1:47–2:02 | Missing layer | Signature shield surrounds only provider tuple; cart remains outside | Explain why valid can still be wrong | Manim `ProofGap` |
| 2:02–2:10 | Product reveal | Hard cut/title lockup | Name the solution after the problem is understood | Manim title |
| 2:10–2:37 | Product | Quote state machine assembles | Explain authoritative economic state | Manim `QuoteStateMachine` |
| 2:37–2:52 | Product | Merchant A/B lanes collide, then separate through firewall | Explain tenant isolation | Manim `TenantIsolation` |
| 2:52–3:08 | Product | Intent key stops duplicate; raw webhook verified; document becomes one part | Show breadth quickly | Manim `EffectIdentity` + icon inserts |
| 3:08–3:22 | Demo | Control room full screen; run INR fault lab | Immediate executable proof | Screen recording D1 |
| 3:22–3:42 | Demo | Create/show real Test Mode order and bound notes | Prove provider contact | Screen recording D2 |
| 3:42–3:55 | Demo | Replay returns same order; mutation returns conflict | Prove effect identity | Screen recording D3 |
| 3:55–4:10 | Demo | Open cross-tenant finding and evidence class | Prove claim discipline | Screen recording D4 |
| 4:10–4:20 | Demo | Catalog scroll stops at `113 / 20 / 45 of 45` | Prove surface breadth | Screen recording D5 |
| 4:20–4:43 | Close | Camera, closer crop than opening; completed notebook diagram visible | State honest scope | A-roll take 2 |
| 4:43–4:57 | Close | `RIGHT MERCHANT × RIGHT AMOUNT × ONCE` resolves into logo | Memorable final line | Manim `FinalLockup` |
| 4:57–5:00 | End | Project, one-line description, public repository URL | Submission identification | End card |

## Notebook pages

Prepare these before recording in thick black marker. Draw arrows live; pre-write only the numbers.

### N1 — A valid payment can be wrong

```text
INTENDED                 CREATED
₹2.01        ───────▶    200 paise
                           ✓ order
                           ✓ signature
                           ✕ intent
```

Circle `✕ intent` only after saying “one paisa is not the story.”

### N2 — The missing proof

```text
MERCHANT INTENT          PROVIDER FACT          FULFILLMENT
SKU + PRICE + CART  →    ORDER + PAYMENT   →    SHIP / ACCESS
       q                     p                      f

                 proof = H(q || p || f || tenant || effect)
```

Do not claim the displayed hash formula is the literal implementation. It is a conceptual drawing; say “bound together,” not “this exact hash.”

### N3 — Exactly once is an identity problem

```text
intent_7 + body_A → effect_1
intent_7 + body_A → replay effect_1
intent_7 + body_B → STOP
```

## Screen-recording sequence

Record one uninterrupted clean master, then repeat each interaction as an isolated pickup.

1. Load the control room and confirm the page contains no credentials or personal data.
2. Run `2.01 INR`; pause on `200` versus `201` for three seconds.
3. Show the authenticated evidence panel.
4. Show the redacted real Test Mode order receipt.
5. Demonstrate same-order replay.
6. Demonstrate changed-body intent conflict.
7. Open one cross-tenant finding, including `confirmed_dynamic`.
8. Open the chain view and point to the inference label.
9. End on `113 operations`, `20 surfaces`, `45/45 MCP tools`.

If provider networking fails during recording, use the durable receipt and explicitly label it **previously observed Test Mode evidence**. Never imply that a prerecorded receipt is a live request.

## Webcam placement

- Use webcam only for the first two seconds of a screen-recording transition and during one explanation pause.
- Place it bottom-right unless it covers evidence controls; then use top-left.
- Keep it at 18–20% of frame width with a square crop and no glowing border.
- Never leave the webcam over code or numbers merely to prove presence.

## Overlay copy

Use no more than seven words per overlay:

- `VALID PAYMENT. WRONG INTENT.`
- `ONE CLIENT CHANGED ANOTHER.`
- `CRYPTOGRAPHY PROVED THE WRONG THING.`
- `INTENT → PROVIDER → FULFILLMENT`
- `DETECTED` / `PREVENTED` / `INFERRED`
- `RIGHT MERCHANT × RIGHT AMOUNT × ONCE`

Avoid “bank-grade,” “unhackable,” “zero fraud,” “production-ready,” or “fixed Razorpay.”
