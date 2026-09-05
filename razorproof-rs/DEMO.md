# RazorProof judge demo

This runbook is designed for a seven-minute live demo with a real Razorpay Test Mode surface and no live-money risk.

## Before the room

```bash
cargo build --locked --release
cargo test --workspace --all-targets
cargo run -q -p razorproof-cli -- coverage \
  --source ../.razorproof/current/razorpay-mcp-server
cargo run -q -p razorproof-cli -- scan \
  --repositories ../.razorproof/repos
```

Set `RAZORPROOF_KEY_CSV`, a long random `RAZORPROOF_GATEWAY_TOKEN`, the Test Mode dashboard webhook secret, and an isolated database URL. Start the service bound to loopback. Never project the terminal while credentials are entered.

## 0:00 — Open with the failure, not the architecture

Open the control room and run `2.01 INR` through both lanes.

Expected:

- generated binary-float/truncation path emits `200`;
- RazorProof exact decimal path emits `201`;
- the interface labels the first result an economic mutation, not a rounding preference.

Then run `295 JPY` and `295.990 KWD`. Explain that payment correctness is a type and state problem, not merely an API call problem.

## 1:15 — Prove it is systemic

Connect the control room with the local tenant and gateway token. Show:

- 113 guarded operations across 20 surfaces;
- 45/45 current official MCP tools covered at a pinned upstream commit;
- exact access, effect, identity, API version, and money policy per operation.

Run the source scanner summary. Open two severe findings and one chain:

- browser-authored amount plus floating-point undercharge plus currency exponent;
- global credential or partner-header state causing cross-tenant routing;
- fractional refund mutation plus missing provider idempotency identity.

Keep the taxonomy visible: 17 direct defects is not the same claim as 23 total findings.

## 2:45 — Touch Razorpay for real

Create a server quote for one `201` INR line, then create an order through the quote endpoint using a new UUID intent. Display only the redacted response fields needed for proof:

- Test Mode order id;
- amount `201` and currency `INR`;
- quote id and cart hash in order notes;
- order status;
- evidence chain head.

Repeat the order request, even with a new intent. The quote is already bound, so it must return the same provider order rather than creating another one. Separately, run the generic effect-identity control: replay the same operation and body with one intent to receive the stored response, then reuse that intent with changed input to receive a conflict before Razorpay is contacted.

## 4:15 — Show the paid-state gate

If a Test Mode checkout has been completed, submit its payment id and signature. RazorProof must:

1. ignore any browser-supplied order id;
2. verify HMAC against the stored order id;
3. fetch both payment and order from Razorpay;
4. compare both amounts and currencies to the server quote;
5. require payment status `captured`;
6. transition once to `PaymentVerified`, then fulfill once.

If checkout has not been completed, run the negative control: a fabricated or malformed signature returns an authentication error and state remains `OrderBound`. State clearly that captured-payment verification is implemented and locally tested but not provider-observed until this step succeeds.

## 5:15 — Create network ambiguity on purpose

Run a write against a loopback capture fixture that accepts the request and drops the connection. A generic wrapper is tempted to retry. RazorProof records the intent as failed/ambiguous and refuses reuse until reconciliation.

Contrast that with refunds, where the same durable intent is sent as Razorpay's documented `X-Refund-Idempotency` header and bounded retry is permitted.

## 6:00 — Close with proof

Run:

```bash
cargo run -q -p razorproof-cli -- verify-evidence \
  --database-url sqlite:///absolute/path/to/razorproof.db \
  --tenant hackathon_demo
```

Show the event count and chain head, then alter a copied event fixture and show verification fail. End on the real claim:

> RazorProof is the missing semantic boundary between generated integration code and irreversible financial state. It already prevents the demonstrated failures, produces provider-observed Test Mode proof, and converts future Razorpay surfaces into versioned policy rather than another set of copy-pasted fixes.

## Failure-safe fallback

If network access is unavailable, do not imply a live call. Use `artifacts/real-test-mode/e2e.json` as the prior provider-observed receipt, run `self-test`, run the scanner, and verify the persisted chain locally. The distinction between live, previously observed, source-bound, and simulated evidence is part of the product.
