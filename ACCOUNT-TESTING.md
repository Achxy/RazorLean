# RazorProof account-testing strategy

Research date: 2 September 2026

## Decision

Create one ordinary Razorpay account with truthful personal details and use **Payments Test Mode**. If the onboarding flow asks for a business type, choose **Unregistered → Individual** and use the closest truthful software/developer-tools category. Do not invent a company, GSTIN, turnover, customers, or business documents. Do not activate Live Mode yet.

Then sign in to **RazorpayX with the same credentials** and enable its Test Mode if it is offered on the account. Razorpay documents both Payments Test Mode and RazorpayX Test Mode as usable before KYC, with no real money involved.

This is the least-friction legitimate setup with the largest useful test surface. A Partner/Technology Partner account and Live Mode add lead time but very little evidence for the POC's current core claim.

## Why this is legitimate

Razorpay explicitly supports `Individual/Unregistered Businesses`. Its onboarding documentation says an unregistered individual uses a personal PAN if they later continue into activation. Payments Test Mode is available immediately after sign-up, can be used indefinitely, and does not require a website or KYC. RazorpayX's quickstart likewise says Test Mode can be started without KYC.

The important distinction is:

- **Sign-up and sandbox testing:** email or phone verification, no company incorporation and no KYC completion required.
- **Live activation:** personal identity/KYC, bank details, and usually website/app review are required.
- **Technology Partner access:** a separate program and approval path; it is not part of the minimum setup.

Sources: [Payments Quickstart](https://razorpay.com/docs/payments/quickstart/), [Test and Live Modes](https://razorpay.com/docs/payments/dashboard/test-live-modes/?preferred-country=IN), [account setup and unregistered individuals](https://razorpay.com/docs/payments/set-up/?preferred-country=IN), [API keys](https://razorpay.com/docs/payments/dashboard/account-settings/api-keys/), and [RazorpayX Quickstart](https://razorpay.com/docs/x/quickstart/?preferred-country=IN).

## What one Payments Test account unlocks

| Probe | Real Razorpay control plane? | Real money? | Demonstration value |
|---|---:|---:|---|
| Create orders with integer subunits | Yes | No | Establishes the server's accepted monetary contract. |
| Run Checkout with test cards, netbanking, wallets and UPI success/failure IDs | Yes | No | Produces payment entities and visible success/failure flows. |
| Feed the MCP-generated `2.01` case into Checkout | Yes | No | Shows the official generated code displaying/charging `2.00`, not merely a local arithmetic example. |
| Capture and fetch payments | Yes | No | Verifies end-to-end entity and amount propagation. |
| Create full and partial refunds | Yes | No | Makes refund truncation and amount-contract failures observable in Razorpay's own response. |
| Retry a refund with one `X-Refund-Idempotency` key | Yes | No | Two requests should resolve to one refund effect. |
| Retry the same economic intent without a key | Yes | No | On disposable test payments, demonstrates duplicate effects and quantifies the architectural need. |
| Reuse a key with a changed payload and test concurrent requests | Yes | No | Verifies rejection/409 semantics and the protocol's exact boundary. |
| Receive signed payment/refund webhooks | Yes | No | Uses real Razorpay delivery, signature headers, event IDs and retry behavior. |
| Replay duplicate and out-of-order webhook events | Partly | No | Tests exact-byte verification, deduplication and ordering locally against genuine payloads. |
| Create Standard Payment Links and complete success/failure checkout | Yes | No | Exercises hosted checkout, callbacks, signatures and reference-ID uniqueness. |
| Run official SDKs and MCP handlers against one account | Yes | No | Converts SDK and generator discrepancies into cross-language, server-observed evidence. |

Razorpay labels its refund endpoint with Test API keys and explicitly documents `X-Refund-Idempotency`, identical-body retries, changed-payload rejection, and `409 Conflict` for overlapping requests: [idempotent normal refunds](https://razorpay.com/docs/api/refunds/normal-refunds-idempotent/?preferred-country=IN). Standard Payment Links are also available with Test API keys, with a limit of 30 per business: [Standard Payment Link API](https://razorpay.com/docs/api/payments/payment-links/create-standard/?preferred-country=IN).

## What RazorpayX Test Mode adds

If RazorpayX is available under the login, its sandbox adds:

- a dummy balance;
- contacts and bank/VPA fund accounts using dummy data;
- payout creation and payout state transitions;
- payout and transaction webhooks;
- an additional money-moving API family on which to test amount, idempotency, state-machine and retry contracts.

It does **not** reproduce the approval workflow in Test Mode, so `pending` and `rejected` approval states are unavailable. Treat RazorpayX as a high-value second sandbox, not a prerequisite for the Payments proof. Source: [RazorpayX Test Mode](https://razorpay.com/docs/x/dashboard/test-mode/).

## Hard boundaries of Test Mode

The following cannot be honestly claimed as end-to-end real-rail validation from this setup:

- actual card/UPI/bank network behavior, settlement, reconciliation and bank-side timing;
- UPI cancellation behavior: Razorpay warns that cancellation in Test Mode can appear successful;
- scannable QR and UPI Intent flows, which require Live Mode;
- UPI-only Payment Links, which are rejected in Test Mode;
- RazorpayX approval-workflow `pending` and `rejected` states;
- disputes, chargebacks, real fraud/risk decisions and production outages;
- sub-merchant onboarding APIs unless a Partner application is available.

Sources: [UPI test details](https://razorpay.com/docs/payments/payments/test-upi-details/), [QR creation limitations](https://razorpay.com/docs/payments/qr-codes/create/?preferred-country=IN), [Checkout integration limits](https://razorpay.com/docs/payments/payment-gateway/quick-integration/integration-steps/?preferred-country=IN), and [UPI Payment Link API](https://razorpay.com/docs/api/payments/payment-links/create-upi/).

## Five-minute account handoff

1. Sign up at Razorpay using an email address or Indian mobile number you control.
2. Use your real name and contact details. If asked, select `Unregistered` and then `Individual`.
3. Stop before Live Mode activation/KYC; select **Test Mode** in the Dashboard.
4. Go to **Account & Settings → API Keys → Generate Key**.
5. Confirm the key ID starts with `rzp_test_`. Never generate or share a live key for this POC.
6. In this project, copy `.env.example` to `.env.local`, paste the test credentials there, and set file mode `600`. Do not paste the secret into chat or commit it.
7. Optionally open RazorpayX with the same login, select Test Mode, generate its test keys, and add an arbitrary dummy balance. If RazorpayX is not exposed, record that as an access boundary and continue with Payments.

The key secret is visible only when generated. Razorpay also states that Test API keys can be created without a website. Source: [API key documentation](https://razorpay.com/docs/payments/dashboard/account-settings/api-keys/).

## Credential file

```bash
cp .env.example .env.local
chmod 600 .env.local
```

Populate `.env.local` locally:

```dotenv
RAZORPAY_KEY_ID=rzp_test_replace_me
RAZORPAY_KEY_SECRET=replace_me_locally
```

RazorProof refuses any key ID that does not begin with `rzp_test_`. Before any mutation, it also requires an explicit `--execute-test-mode` flag.

## Test sequence after the key exists

1. Read-only authentication and capability inventory.
2. Create boundary-value orders: `1`, `99`, `100`, `101`, `200`, `201`, and selected large safe integers.
3. Complete test Checkout for `201` paise and capture the genuine payment/webhook evidence.
4. Execute the official MCP-generated `2.01` path and compare intended amount, outgoing API payload, order entity and rendered Checkout amount.
5. Run idempotent refund duplicate, changed-payload and overlap tests on disposable captured payments.
6. Run a controlled no-key duplicate-refund test on a separate test payment.
7. Validate signatures using exact raw webhook bytes, including Unicode; replay identical event IDs and reverse event order.
8. Exercise Standard Payment Links and callback signatures.
9. Run the same vectors through each relevant official SDK and the MCP handler, recording request/response pairs with secrets redacted.
10. If available, repeat the semantic contract suite against RazorpayX contacts, fund accounts and payouts.

All mutations remain in Razorpay's sandbox. The resulting evidence bundle should record merchant/account IDs only in redacted form and must never store API secrets.

## Why not activate or join Partners now

Live activation adds PAN/CKYC or Video KYC, bank details, and a reviewed website/app for live API keys. An unregistered individual may use a personal bank account, but that step should be taken only for a truthful live commercial use—not to manufacture hackathon evidence. See [account activation support](https://razorpay.com/docs/payments/account-activation-support/?preferred-country=IN) and [website requirements](https://razorpay.com/docs/payments/dashboard/account-settings/business-website-details/?preferred-country=IN).

The general Partner program accepts individuals and students, but Technology Partner status requires a use-case review and can take roughly two to three weeks. It also expects a website and a product that manages payments for sub-merchants. That makes it a later expansion path, not the least-friction test account. Sources: [Partner eligibility](https://razorpay.com/docs/partners/?preferred-country=IN) and [Technology Partner switch](https://razorpay.com/docs/partners/technology-partners/become-technology-partner/).

## Evidence standard

The sandbox is a real Razorpay-operated control plane and produces genuine API entities, hosted Checkout screens, signatures, event IDs and state transitions. It is therefore stronger than a local simulation for protocol and application semantics. It is not proof of bank-rail behavior. Every report must label evidence as one of:

- `local-runtime`: executed in an official SDK/tool locally;
- `razorpay-test-control-plane`: observed against Razorpay Test Mode;
- `live-rail`: observed with real money or an external payment rail;
- `not-tested`: inaccessible or intentionally deferred.

This label prevents a spectacular demo from turning into an inflated claim.
