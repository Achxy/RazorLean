# Account test strategy — source report

Research date: 2026-09-02

## Research question

What is the least-friction legitimate Razorpay account configuration for an individual without a registered business that unlocks the maximum useful, demonstrable RazorProof test surface?

## Decision

Use a standard Razorpay Payments account in Test Mode. When business classification is requested, select Unregistered → Individual and supply only truthful data. Do not complete KYC or Live Mode activation for the current POC. Attempt RazorpayX Test Mode with the same credentials as a second sandbox. Defer Partner/Technology Partner enrollment and all live-rail testing.

## Evidence ledger

| Question | Finding | Confidence | Primary source |
|---|---|---:|---|
| Is Test Mode available without KYC? | Yes; immediately after sign-up and usable indefinitely. | High | https://razorpay.com/docs/payments/dashboard/test-live-modes/?preferred-country=IN |
| Is a website required for test keys? | No. It is required for Live Mode API keys. | High | https://razorpay.com/docs/payments/dashboard/account-settings/api-keys/ |
| Is a registered company required? | No; Individual/Unregistered Business is supported. | High | https://razorpay.com/docs/payments/set-up/?preferred-country=IN |
| Can an unregistered person later activate? | The documented flow uses personal PAN; personal bank details may be supplied when unregistered. Further review can still be required. | High | https://razorpay.com/docs/payments/set-up/?preferred-country=IN and https://razorpay.com/docs/payments/account-activation-support/?preferred-country=IN |
| Can refunds and idempotency be tested? | Yes; refund API is labelled for Test API keys and documents the idempotency header and conflict semantics. | High | https://razorpay.com/docs/api/refunds/normal-refunds-idempotent/?preferred-country=IN |
| Are test webhooks representative? | Payload structure is the same in Test and Live Modes; genuine test transactions trigger events. | High | https://razorpay.com/docs/webhooks/validate-test/?locale=en-US |
| Can local webhooks be received directly? | No; a public URL is required. Many common tunnels are blocked; Razorpay recommends zrok. | High | https://razorpay.com/docs/webhooks/validate-test/?locale=en-US |
| Can Standard Payment Links be tested? | Yes, up to 30 per business in Test Mode. | High | https://razorpay.com/docs/api/payments/payment-links/create-standard/?preferred-country=IN |
| Can UPI-only Payment Links be tested? | No; the API rejects them in Test Mode. | High | https://razorpay.com/docs/api/payments/payment-links/create-upi/ |
| Can QR/UPI Intent be tested end to end? | QR can be created but only Live Mode QR codes can be scanned; integration docs reserve UPI Intent/QR for Live Mode. | High | https://razorpay.com/docs/payments/qr-codes/create/?preferred-country=IN and https://razorpay.com/docs/payments/payment-gateway/quick-integration/integration-steps/?preferred-country=IN |
| Is UPI cancellation realistic in Test Mode? | No; cancellation can result in a successful test payment. | High | https://razorpay.com/docs/payments/payments/test-upi-details/ |
| Is RazorpayX Test Mode available without KYC? | RazorpayX Quickstart says Test Mode starts without KYC; sandbox docs cover dummy balances, contacts, fund accounts and payouts. Actual product visibility remains account-dependent. | Medium-high | https://razorpay.com/docs/x/quickstart/?preferred-country=IN and https://razorpay.com/docs/x/dashboard/test-mode/ |
| Is RazorpayX approval workflow testable? | No; pending and rejected approval states are unavailable in Test Mode. | High | https://razorpay.com/docs/x/dashboard/test-mode/ |
| Is Technology Partner the easiest route? | No; it requires a product/use-case review, website, and a requested type switch that can take 2–3 weeks. | High | https://razorpay.com/docs/partners/technology-partners/become-technology-partner/ |
| Can an individual join Partners eventually? | Yes; documentation lists individuals and students, but this is not the same as immediate Technology Partner API access. | High | https://razorpay.com/docs/partners/?preferred-country=IN |

## Alternative comparison

| Setup | Initial friction | Useful POC coverage | Main exclusions | Decision |
|---|---:|---:|---|---|
| No account | None | Official source/runtime probes only | No Razorpay-hosted entities or webhooks | Already completed; retain as reproducible baseline. |
| Payments Test Mode, unregistered individual | Very low | Highest current value: orders, Checkout, payments, captures, refunds, webhooks, Payment Links, SDK/MCP E2E | Real rails, QR scan, UPI Intent/cancel, settlement | Recommended primary setup. |
| RazorpayX Test Mode under same login | Low if exposed | Contacts, fund accounts, payouts, payout states/webhooks | Approval workflow and live bank behavior | Recommended optional second sandbox. |
| Live unregistered-individual activation | Medium/high | Real payments, QR, UPI Intent/cancel, settlement | Still no Partner APIs; introduces real-money/compliance risk | Defer until a legitimate live use exists. |
| Partner/Technology Partner | High and time-dependent | OAuth and sub-merchant onboarding surfaces | Approval, website, KYC, multi-week lead time | Defer; not critical path. |

## Unknowns and stop rules

- RazorpayX product visibility may vary by account. Treat absence as an access result, not a reason to misstate business details.
- Payment methods may require per-account approval even in the integration journey.
- Test Mode validates Razorpay application/control-plane semantics, not NPCI/card-network/bank behavior.
- Never use live keys, real customer data, fake KYC, or production money for the POC without a separately reviewed protocol and explicit user authorization.
- Never store or render API secrets in logs, reports, screenshots or source control.

## Recommended next gate

The account owner creates the account and test keys privately. RazorProof first performs a read-only capability inventory, then creates disposable Test Mode entities under explicit mutation flags. Each result is tagged `razorpay-test-control-plane`; inaccessible live-rail cases remain explicitly `not-tested`.
