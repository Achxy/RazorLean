# RazorProof: Real Razorpay Test Mode Campaign

## Result

Two hosted Test Mode checkouts were completed end to end and reconciled against Razorpay's API ledger and signed webhooks. No Live Mode transaction was attempted.

- 2 hosted payments reached `captured`; both Payment Links reached `paid`.
- The ₹8.01 fixture reached `refunded` with `amount = amount_refunded = refund ledger sum = 801`.
- 22 webhook deliveries across 6 event types were captured; every signature verified over the exact raw bytes.
- 16 deliveries contained literal non-ASCII UTF-8 bytes. Exact UTF-8 HMAC verification passed and the current .NET SDK's ASCII-equivalent digest failed all 16.
- A direct Refund API request with JSON `amount: 100.75` returned HTTP 200, created amount 100, emitted signed `refund.created` and `refund.processed` events, and persisted as a processed 100-subunit refund.

## What is now a direct defect

### RP-DOTNET-WEBHOOK-ASCII

The previous reachability caveat is closed. Razorpay itself delivered literal `₹` and Malayalam bytes in ordinary `payment_link.paid`, `refund.created`, and `refund.processed` Test events. The provider signature matches exact UTF-8 bytes; replacing non-ASCII characters as .NET `ASCIIEncoding` does produces a different HMAC every time.

### RP-API-REFUND-FRACTIONAL-COERCION

Razorpay's [Create a Normal Refund contract](https://razorpay.com/docs/api/refunds/create-normal/?preferred-country=IN) types `amount` as an integer in the currency's smallest unit. On the ₹8.01 fixture, the API accepted `100.75` and persisted 100. This is silent monetary-input coercion at the provider boundary, independently of the MCP wrapper's own `float64 → int` defect.

The exact claim is intentionally narrow. With only 101 subunits remaining on the ₹2.01 fixture, the same `100.75` request returned HTTP 400 and created no effect. Therefore RazorProof reports an inconsistent fail-open path, not universal fractional acceptance and not permanently stranded value.

## Provider behavior that is not a bug

- An identical retry with one `X-Refund-Idempotency` value returned one refund identity.
- Reusing that header with a changed body returned HTTP 409.
- A duplicate `receipt` returned HTTP 400.
- Two unkeyed requests produced two refund effects. Those are two intents by design; the wrapper problem is hiding the available identity mechanisms, not Razorpay creating two refunds.
- International Test card failures before the domestic Test card succeeded were an account/payment-method configuration boundary, not a processing defect.

These results match Razorpay's [idempotent-refund contract](https://razorpay.com/docs/api/refunds/normal-refunds-idempotent/?preferred-country=IN) and are retained as negative controls.

## Reconciled sequence

The initial matrix assumed the fractional request would be rejected and therefore proposed a 401-subunit final close. Once Razorpay unexpectedly accepted it as 100, that close correctly failed as an over-refund. RazorProof then fetched the authoritative ledger, calculated the actual 301-subunit remainder, retried it with one header identity, observed one effect, and verified the final 801/801 ledger equality. The harness was changed to reconcile the provider ledger before any future close.

## Evidence map

- [Order and generated-undercharge boundary](order-boundary.md)
- [Refund identity matrix](refund-identity-matrix.md)
- [Reconciled idempotent close](refund-idempotent-close.md)
- [Final processed ledger](refund-ledger.md)
- [Literal UTF-8 byte proof](webhook-byte-evidence.md)
- [Smaller-balance negative control](refund-fractional-dust.md)
- [Machine-readable campaign summary](campaign-summary.json)

Published evidence contains only hashes and one-way entity fingerprints. API credentials, webhook secret, raw bodies, signatures, contact data, and provider IDs remain in ignored mode-600 files.
