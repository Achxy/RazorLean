# RazorProof

RazorProof is a semantic payment firewall for Razorpay. It sits between application or agent-generated code and Razorpay, then turns a payment request into a constrained state transition with a durable economic identity.

This is a production-oriented hackathon build, not a claim of production certification. The code is deliberately locked to Razorpay **Test Mode** until deployment controls, operational reconciliation, key management, and a formal security review are completed.

## What is different

Most payment wrappers answer “how do I call this endpoint?” RazorProof answers the harder questions first:

- Who was allowed to choose the amount and currency?
- Does `2.01 INR` become exactly `201`, without binary floating point?
- Is this effect new, a replay of the same effect, or reuse of an identity with different input?
- Which tenant and partner account owns the request?
- If the connection failed after Razorpay accepted a write, why was it not silently retried?
- Does checkout success still match the server quote, the Razorpay order, the captured payment, and the signature?
- Can an auditor prove the sequence without retaining customer or credential payloads?

The current build has a versioned policy for **113 operations across 20 surfaces**, including all **45 source tools** in Razorpay's official MCP server at pinned commit `7950d51d118ca164c32b7cf0cfaa14f34f24849f`. The broader catalog covers v1 and v2 routes for payments, orders, refunds, settlements, payouts, payment links, QR codes, tokens, customers, subscriptions, invoices, items, virtual accounts, Route transfers, disputes, partner onboarding, documents, webhooks, and local code-generation controls.

## What has been proved

| Claim | Evidence level | Result |
|---|---|---|
| Rust workspace builds and tests | Local executable | 26 unit/integration tests pass |
| Exact INR, JPY, KWD conversion | Local executable | Pass; invalid three-decimal quantum rejected |
| Fractional subunit rejection | Local executable | `100.75` never crosses the boundary |
| Current official MCP tool coverage | Source-bound executable | 45/45 tools mapped; drift fails the command |
| Official SDK and generator audit | Source-bound executable | 662 files, 2,683,730 bytes, 23 findings, 17 direct defects, 6 chains |
| Razorpay Test Mode authentication | Provider-observed | Read-only API returned HTTP 200 |
| Real order creation through firewall | Provider-observed | ₹2.01 became a real Test Mode order for 201 INR |
| Durable evidence verification | Local executable | Four-event chain independently verified |
| Captured payment and fulfillment | Not yet exercised | Needs a Test Mode checkout completion |
| All 113 endpoint families | Policy-covered, not all exercised | Some need product entitlements or partner access |

See [the real Test Mode receipt](artifacts/real-test-mode/e2e.md), [the conformance report](artifacts/conformance/scan.md), and [the claim ledger](research/report-source.md).

## Architecture

```text
browser / backend / agent
           │  tenant + bearer token + intent id
           ▼
┌───────────────────────────────────────────────────────┐
│ RazorProof                                             │
│ auth → policy → exact money → quote → effect identity │
│      → tenant-fixed provider client → reconciliation  │
└───────────────┬──────────────────────┬────────────────┘
                │                      │
                ▼                      ▼
       Razorpay Test Mode       SQLite WAL/FULL
       v1 + v2 allowlist        quotes/effects/webhooks
                                hash-chained evidence
```

The seven-crate workspace keeps correctness domains separate:

- `razorproof-core`: money, identities, quotes, signatures, canonical evidence.
- `razorproof-policy`: versioned operations, monetary JSON paths, effects, access, API version, idempotency.
- `razorproof-provider`: official-origin-only HTTP, immutable auth/routing, bounded responses, safe retry rules, multipart validation.
- `razorproof-store`: optimistic quote transitions, durable effect claims, webhook deduplication, append-only evidence.
- `razorproof-engine`: reproducible semantic detectors and compositional failure chains across official source.
- `razorproof-server`: authenticated REST boundary, specialized checkout lifecycle, generic guarded operations, webhook ingress, judge UI.
- `razorproof-cli`: self-test, source coverage, scanner, Test Mode probe, evidence verification, service runner.

Read [Architecture](docs/ARCHITECTURE.md) and [Threat model](docs/THREAT-MODEL.md) for the actual guarantees and remaining production work.

## Run it

Requirements: Rust 1.90 or newer, the Razorpay dashboard Test Mode CSV, and no Live Mode key.

```bash
cargo test --workspace --all-targets
cargo run -p razorproof-cli -- self-test
cargo run -p razorproof-cli -- coverage \
  --source ../.razorproof/current/razorpay-mcp-server
cargo run -p razorproof-cli -- scan \
  --repositories ../.razorproof/repos
cargo run -p razorproof-cli -- probe-test-mode \
  --key-csv /absolute/path/to/rzp-key.csv
```

To start the firewall, supply long random local secrets through the environment or a secret manager. Do not put Razorpay secrets in arguments, source, browser storage, or logs.

```bash
export RAZORPROOF_KEY_CSV=/absolute/path/to/rzp-key.csv
export RAZORPROOF_GATEWAY_TOKEN='replace-with-at-least-24-random-characters'
export RAZORPROOF_WEBHOOK_SECRET='replace-with-dashboard-test-webhook-secret'
cargo run -p razorproof-cli -- serve
```

Then open `http://127.0.0.1:8787`. The control room never receives the Razorpay key secret. Its gateway token is retained only in page memory, disappears on reload, and can be forgotten from the UI.

## Core API flow

1. `POST /v1/quotes` computes total and cart hash on the server.
2. `POST /v1/quotes/{id}/order` requires `X-RazorProof-Intent`, creates one Razorpay Test Mode order, and binds it to that quote.
3. Checkout returns `payment_id` and signature to the merchant server.
4. `POST /v1/quotes/{id}/verify` uses the server-bound order id in the HMAC preimage, re-fetches both objects from Razorpay, requires a captured payment, and compares order, payment, amount, and currency.
5. `POST /v1/quotes/{id}/fulfill` advances once; a different fulfillment reference is rejected.

Every state change emits a content hash and a chained event hash. Sensitive provider payloads are not copied into the evidence ledger.

The complete request contract is in [OpenAPI](openapi.yaml). A timed judge sequence is in [Demo runbook](DEMO.md).

## Deliberate production gates

RazorProof refuses `rzp_live_` credentials. Before a live-mode edition should exist, it needs:

- KMS or HSM-backed tenant credentials with rotation and least privilege;
- PostgreSQL or another transactional store with serializable per-tenant evidence append;
- a reconciliation worker for deliberately ambiguous writes;
- rate limits, workload identity or mTLS, network policy, and centralized audit export;
- generated schemas for each request/response beyond the current semantic policy;
- chaos, load, fuzz, dependency, license, and independent security testing;
- product-specific acceptance tests for every enabled Razorpay entitlement.

The absence of those items is explicit. The hackathon claim is stronger and measurable: this build already prevents or exposes the demonstrated semantic failures at one executable boundary, and it touches a real Razorpay Test Mode surface today.

## Security and disclosure

The conformance scanner separates direct defects, compatibility gaps, and known-public hardening so counts cannot be inflated. Reports about third-party code remain drafts unless their owner authorizes disclosure. Do not include credentials, customer data, or live financial effects in a report.

MIT licensed.
