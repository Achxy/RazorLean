# RazorProof five-minute pitch script

Target runtime: **4:50 to 5:00** at 138 to 145 spoken words per minute.

The story is a reconstruction of the actual investigation. Do not say that a merchant lost money or that a production incident occurred. The generated expressions, SDK runtime failures, Test Mode orders, captured Test Mode payments, and signed webhooks are evidenced; downstream production consequences are not.

## Chapter 1 — The payment that succeeded wrong — 0:00–0:42

**[Black screen. A single payment-success sound. Provider order card appears.]**

> The payment succeeded. The signature verified. Razorpay created the order. Everything was valid — except the amount.

**[Cut to camera. Hold a notebook showing `₹2.01 → 200 paise`. Do not explain yet.]**

> While stress-testing the exact code emitted by an official AI integration generator, I entered two rupees and one paisa. In Python, Ruby, and PHP, the generated conversion sent two hundred paise instead of two hundred and one.
>
> One paisa is not the story. The story is that every green checkmark still passed. Cryptography proved that Razorpay processed the order. It did not prove that the order represented what the merchant intended.

**[Manim: the one-paisa split expands into JPY and KWD.]**

> Then I changed the currency. Two hundred and ninety-five yen became twenty-nine thousand five hundred yen. Two hundred and ninety-five dinar became twenty-nine. This was not a rounding bug. It was a missing layer in the payment stack.

## Chapter 2 — The rabbit hole — 0:42–1:24

**[Fast montage: eight repository names, terminals, highlighted source lines. Keep code legible, not decorative.]**

> So I cloned eight official Razorpay repositories and defined the rules a payment system must never violate: exact money, isolated merchant identity, byte-exact webhooks, one retry identity, and every payment bound to its cart.
>
> The deeper we looked, the less this resembled one bug. In three SDKs, client B overwrote or inherited client A's credentials or partner routing. The .NET SDK reused an AES-GCM nonce derived from the key. Real non-ASCII Test Mode webhooks failed its ASCII digest.

**[Overlay, one line at a time.]**

> Across the corpus: twenty-three findings. Seventeen direct defects. Fourteen dynamically reproduced. And six ways individually small failures can combine into a financial incident.

## Chapter 3 — What was actually missing — 1:24–2:02

**[Overhead notebook shot. Draw three boxes: `INTENT`, `PROVIDER`, `FULFILLMENT`.]**

> Here is the real problem. APIs validate request shape. SDKs make the call. Signatures prove what the provider processed. But none of those automatically prove what should have happened.

**[Draw arrows: SKU and price into Intent; order and payment into Provider; shipment into Fulfillment.]**

> A payment needs an economic identity: merchant, cart, exact amount, intended effect, and fulfillment. Lose one link and a valid API response can certify the wrong transaction.
>
> We built the missing boundary.

## Chapter 4 — RazorProof — 2:02–3:08

**[Title card: `RAZORPROOF / A SEMANTIC PAYMENT FIREWALL`.]**

> RazorProof sits between applications, AI agents, and Razorpay. It is written in Rust and makes invalid financial states difficult to represent.

**[Manim state machine appears while the corresponding words are spoken.]**

> First, the server issues an immutable quote from trusted SKU data. Money is stored as integer subunits with currency-specific rules — zero decimals for yen, three for dinar, and no binary floating point anywhere.
>
> That quote becomes exactly one Razorpay order. A payment is accepted only if its signature, fetched provider state, captured status, amount, currency, tenant, and quote agree. Only then can fulfillment happen, once.

**[Animation changes to two isolated merchant lanes.]**

> Each tenant gets immutable credentials and routing. Every write gets a durable intent identity. Same identity and input: same result. Changed input: stopped. Ambiguous failures freeze for reconciliation instead of being blindly retried.

**[Raw bytes flow through HMAC before JSON; then one multipart file.]**

> Webhooks are verified over raw bytes before parsing. Documents are checked by extension, MIME and file signature, then emitted as one part. Every transition produces tamper-evident evidence without retaining credentials or customer payloads.

## Chapter 5 — Proof, not slides — 3:08–4:20

**[Full-screen control room recording. Webcam moves to lower-right only after the UI is readable.]**

> Let me show you.

**[Enter `2.01 INR` in the fault lab.]**

> The unsafe generated path produces two hundred. RazorProof produces two hundred and one.

**[Switch to the authenticated evidence view.]**

> This is not a mock gateway. RazorProof created a real Razorpay Test Mode order for exactly two hundred and one paise. The provider returned the order, and the quote and cart hash are bound into its notes.

**[Replay order creation; show the same provider order ID.]**

> Repeat the same economic intent and no second order appears. Change the body under the same intent and RazorProof stops it before Razorpay is called.

**[Open one cross-tenant finding and the evidence chain.]**

> The scanner checks eight official repositories, while the interface separates executed defects, inferred consequences, and controls enforced here. No inflated zero-day counter.

**[Show operation catalog metrics.]**

> The current policy covers one hundred and thirteen operations across twenty Razorpay surfaces, including all forty-five tools in the pinned official MCP server.

## Chapter 6 — The way out — 4:20–4:57

**[Return to camera. Notebook now shows the completed chain.]**

> We started with one missing paisa. We ended with a new correctness boundary for agent-generated payments.
>
> RazorProof does not repair every SDK on every machine. It detects ecosystem defects, prevents those failure classes for traffic crossing its boundary, and proves the right financial intent happened exactly once.

**[Final Manim lockup: `RIGHT MERCHANT × RIGHT AMOUNT × ONCE`.]**

> APIs can tell us whether a request was valid. RazorProof proves it was the right request, for the right merchant, for the right amount — once.

**[End card for three seconds: project name, one-sentence description, repository URL.]**

## Optional ten-second cut if the edit runs long

Remove this paragraph from Chapter 4:

> Webhooks are verified over raw bytes before parsing. Documents are checked by extension, MIME and file signature, and emitted as exactly one part.

Do not accelerate the narration to fit. Silence before the opening sentence and after the closing sentence makes the film feel controlled rather than rushed.
