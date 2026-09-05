# RazorProof architecture

## Design objective

RazorProof is a correctness boundary, not another SDK. It converts loosely typed application intent into a durable, tenant-owned, provider-observed state transition. The design favors a visible stop over an economically ambiguous success.

## Trust boundaries

```text
untrusted client                trusted merchant boundary              external provider

cart, strings, headers ──► auth / quote / policy / identity ──► HTTPS api.razorpay.com
webhook bytes          ──► raw-byte signature / event dedup  ◄── Razorpay webhook service
                                │
                                ▼
                         durable local ledger
```

The browser is not trusted to author amount, currency, order identity, or fulfillment state. Razorpay is authoritative for provider object state, but a single network response is not sufficient proof of application fulfillment. The local data store is authoritative for intent identity and state-machine progress. The append-only chain detects later evidence mutation; it is not a substitute for exporting chain heads to an independent timestamp or transparency service.

## Invariants

| Boundary | Invariant | Enforcement |
|---|---|---|
| Money | Provider subunits are positive JSON integers | `MinorAmount`, policy JSON-pointer validation |
| Conversion | Major amounts use decimal exactness and currency exponent | `Money::from_major`; no `f32` or `f64` |
| Currency | Zero and three-decimal currencies obey exponent and provider quantum | audited currency rules; JPY/KWD/BHD/OMR tests |
| Authority | Checkout economics originate from a server-issued quote | immutable quote lines, computed total, cart hash, expiry |
| Effect identity | One tenant intent maps to one operation and canonical request hash | SQLite primary key plus replay/conflict states |
| Retry | Generic writes are not retried after uncertainty | one attempt; failure becomes reconciliation-required |
| Refund retry | Razorpay receives the stable refund identity | `X-Refund-Idempotency` from the durable intent |
| Tenant routing | Credentials and `X-Razorpay-Account` cannot mutate between requests | immutable client-owned configuration |
| Transport | Callers cannot supply an origin or API version | official HTTPS allowlist and catalog-owned v1/v2 |
| Query | Repeated values remain repeated | multi-value query representation |
| Checkout proof | Signature uses the stored order id and state is re-fetched | constant-time HMAC plus order/payment binding |
| Webhook proof | HMAC covers exact network bytes | body extracted as bytes before JSON parsing |
| Webhook replay | Provider event identity is processed once | tenant-scoped hash of `X-Razorpay-Event-Id` |
| Documents | Extension, magic, MIME, size, and part count agree | dedicated validated multipart path |
| Fulfillment | A paid quote fulfills once | optimistic state transition and intent identity |
| Evidence | Each tenant has one verifiable chain | canonical JSON, BLAKE3 links, unique successor index |

## State machines

### Quote and checkout

```text
Issued
  │ create provider order; compare and persist order id
  ▼
OrderBound
  │ verify HMAC; re-fetch order + payment; require captured; compare economics
  ▼
PaymentVerified
  │ durable fulfillment intent
  ▼
Fulfilled
```

Expired quotes and invalid transitions fail. An already bound quote returns its bound order instead of creating a second provider order. Fulfillment with the same reference is idempotent; a different reference conflicts.

### Generic effect

```text
absent ──claim(tenant, intent, operation, body hash)──► pending
  │                                                   ├── 2xx/4xx ─► completed + replayable response
  │                                                   └── transport/5xx ─► failed
  ├── same tuple + completed ─► replay
  ├── same tuple + pending   ─► in-flight conflict
  ├── different tuple       ─► identity reuse conflict
  └── same tuple + failed   ─► reconciliation required
```

A 4xx response is determinate and can be replayed. A transport failure or 5xx after a write is not proof that the provider did nothing, so the effect is frozen until reconciliation. Read operations and refund operations can retry within bounded policy; arbitrary writes cannot.

## Operation compiler

`policies/razorpay-operations.json` is executable policy. Each operation declares:

- canonical name and compatibility aliases;
- product surface and effect class;
- local, ingress, read, or write access;
- API version, method, relative path, and path parameters;
- money and currency pointers, including wildcard nested arrays;
- read-only, gateway-owned, refund-header, or event-id identity;
- whether server quote authorization is mandatory;
- whether it corresponds to a current official MCP source tool.

The catalog rejects duplicate identities, unsupported versions or methods, remote or traversal-like paths, malformed pointers, read/write identity contradictions, and invalid ingress contracts at startup. The coverage command parses production Go source from the official MCP repository and exits non-zero if a current source tool is missing or stale.

The catalog is broader than the official MCP surface but intentionally shallower than generated per-endpoint JSON Schema. Semantic invariants are executable today; schema generation and entitlement-specific contract suites are the next layer, not a hidden claim.

## Persistence and concurrency

The hackathon implementation uses SQLite with WAL, `synchronous=FULL`, foreign keys, bounded connection pools, unique identities, and optimistic quote versions. Evidence append runs inside a transaction and a unique `(tenant_id, previous_hash)` index prevents two successors to the same link.

For horizontally scaled deployment, move effects, quotes, webhook receipts, and evidence into a transactional service that supports row locking or serializable tenant streams. Export chain heads to independent immutable storage. Do not simply put the SQLite file on a shared network filesystem.

## Failure semantics

- API errors use problem-style JSON with a stable machine code and no provider secret.
- Provider bodies are returned to the authenticated caller but evidence stores only fingerprints, hashes, attempts, status, and transitions.
- Provider responses are capped at 2 MiB, request JSON and webhook bodies at 1 MiB, and documents at 50,000 KiB.
- Redirects are disabled; the provider origin is exactly `https://api.razorpay.com`.
- Malformed signatures are authentication failures, not panics or server errors.

## Extension path

1. Generate typed endpoint payload schemas from official OpenAPI or curated fixtures while retaining semantic policy as the authoritative effect layer.
2. Add a reconciliation worker keyed by `(tenant, intent)` and product-specific fetch operations.
3. Add KMS-backed tenant configuration, rotation, workload identity, policy signing, and independent chain-head notarization.
4. Run every entitled operation against isolated Test Mode accounts and record redacted provider receipts.
5. Ship language-neutral sidecars plus Rust, TypeScript, Go, Java, and mobile adapters that never duplicate economic rules.
6. Make the catalog drift check and conformance scanner a required upstream CI gate for MCP and SDK releases.
