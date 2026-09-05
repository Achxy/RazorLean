# RazorProof research and claim ledger

Research refreshed 2026-09-04. Primary sources are preferred. Endpoint counts describe the RazorProof policy catalog, not a claim that every product is enabled on this Test Mode account.

## Provider contracts used as invariants

| Source | Contract used by RazorProof |
|---|---|
| [Razorpay API reference](https://razorpay.com/docs/api/) | Most payment APIs use `/v1`; partner onboarding includes `/v2` resources. API errors and rate-limit behavior need explicit handling. |
| [Orders API](https://razorpay.com/docs/api/orders/) | An order carries integer subunit amount, currency, receipt, notes, amount-paid/due, and status. |
| [Standard Checkout integration](https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/integration-steps/) | Server creates the order and verifies `order_id|payment_id` using the server's order id, not an untrusted checkout echo. |
| [Build your own integration](https://razorpay.com/docs/payments/payment-gateway/ecommerce-plugins/build-your-own/) | Amount is sent in currency subunits; currencies differ in supported decimal representation. |
| [Idempotent refunds](https://razorpay.com/docs/api/refunds/normal-refunds-idempotent/) | A stable `X-Refund-Idempotency` identity makes refund retries safe. |
| [Validate and test webhooks](https://razorpay.com/docs/webhooks/validate-test/) | Signature verification uses the raw webhook request body; webhook event ids support duplicate defense. |
| [Partner authentication](https://razorpay.com/docs/partners/aggregators/partner-auth/) | Partner requests can include `X-Razorpay-Account`, making immutable tenant routing material to correctness. |
| [Documents API](https://razorpay.com/docs/api/documents/create/) | Documents use multipart upload with a purpose and file; safe serialization needs a dedicated path. |
| [Subscriptions API](https://razorpay.com/docs/api/payments/subscriptions/) | Plans, subscriptions, add-ons, updates, pause/resume, cancellation, and offers extend the recurring effect surface. |
| [Invoices API](https://razorpay.com/docs/api/payments/invoices/) | Invoice creation/update/issue/cancel/notify adds nested line-item monetary fields and lifecycle effects. |
| [Customers API](https://razorpay.com/docs/api/customers/) | Customer state, tokens, bank accounts, and eligibility are identity-bearing operations beyond checkout. |
| [Route API](https://razorpay.com/docs/api/payments/route/) | Transfers and reversals create multi-party financial effects requiring exact amounts and intent identity. |
| [Disputes API](https://razorpay.com/docs/api/disputes/) | Accepting or contesting a dispute is an irreversible state transition, not a generic metadata call. |
| [Partner accounts](https://razorpay.com/docs/api/partners/account-onboarding/) | Partner account onboarding uses v2 account resources. |
| [Partner stakeholders](https://razorpay.com/docs/api/partners/stakeholder/) | Stakeholders use v2 nested resources and legitimate non-money decimals such as ownership percentages. |
| [Partner product configuration](https://razorpay.com/docs/api/partners/product-configuration/) | Product requests and configuration add another v2 state machine. |
| [Official Razorpay MCP server](https://github.com/razorpay/razorpay-mcp-server) | Source of the current 45-tool baseline and generated integration code audited by the conformance engine. |

## Claims and exact evidence class

| Claim | Class | Reproduction |
|---|---|---|
| 113 operations / 20 surfaces | Static executable policy | Load catalog; validation is mandatory at startup |
| 45/45 current MCP tools | Pinned source comparison | `razorproof coverage --source ...` exits non-zero on drift |
| 23 findings / 17 direct defects / 6 chains | Pinned source scan | `razorproof scan --repositories ...`; line, detector, taxonomy retained |
| Exact-money invariant | Unit and property controls | INR/JPY/KWD controls and fractional-subunit rejection |
| Query expansion preserved | Wire-construction unit test | repeated query vector flattens to repeated pairs |
| Multipart unambiguous | Serialization boundary unit test | one binary part; extension/magic/MIME validation |
| Test credentials accepted | Provider-observed read | real Test Mode order-list API HTTP 200, redacted fingerprint only |
| ₹2.01 order is 201 INR | Provider-observed write | real Test Mode order receipt and local four-event evidence chain |
| Captured payment can be verified | Implemented and locally tested | provider-observed completion pending a Test Mode Checkout payment |
| Live money is protected | Negative executable control | `rzp_live_` credentials are rejected in `TestOnly` mode |

## What the research changed

The product began as a fix for one floating-point undercharge. Cross-SDK and generator evidence showed that the deeper common failure is missing semantic ownership: money, tenant routing, effect identity, signature preimage, retry, documents, and fulfillment are independently handled at weak boundaries. RazorProof therefore enforces one protocol with five gates—value, authority, identity, provider observation, and proof—rather than patching 23 symptoms.

The broader API review also changed two technical assumptions:

1. Razorpay is not one uniform v1 surface; partner onboarding requires catalog-owned v2 routing.
2. Not every decimal is money. Stakeholder ownership can legitimately be fractional, so exact-integer rejection must apply only to declared money pointers, including nested wildcard arrays.

## Open research and invalidation tests

- Exercise every entitled operation in Test Mode and compare actual response/error contracts to the policy.
- Complete Standard Checkout to turn payment verification from local-contract proof into provider-observed proof.
- Determine product-specific reconciliation keys for generic writes that return transport failure or 5xx.
- Validate all supported currency quantum rules against the current provider contract; fail closed for unreviewed currencies in a live edition.
- Test webhook duplicate and secret-rotation behavior against dashboard delivery rather than only signed local fixtures.
- Re-run the MCP source diff whenever its pinned commit changes and reclassify findings after upstream fixes.
- Treat evidence against a detector as a reason to downgrade or remove it; compatibility and known-public findings must never be counted as undisclosed vulnerabilities.
