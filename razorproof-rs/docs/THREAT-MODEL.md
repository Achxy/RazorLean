# RazorProof threat model

## Scope

Protected assets are financial amount and currency, effect identity, provider credentials, submerchant routing, quote and fulfillment state, webhook authenticity, document integrity, and audit evidence. The current deployment profile is a single-node Razorpay Test Mode service. Live money is explicitly outside scope and rejected by code.

Actors include a malicious browser user, buggy or agent-generated integration code, a replaying network client, a tenant attempting cross-tenant access, a compromised dependency, an operator with filesystem access, and a provider/network failure that creates ambiguity without malicious intent.

## Material threats and controls

| Threat | Consequence | Current control | Residual risk / production gate |
|---|---|---|---|
| Browser tampers with price | Undercharge or catalog mismatch | Server-issued quote computes amount and binds cart hash | Catalog source itself must be trusted and integrated |
| Binary float conversion | Silent minor-unit mutation | Exact decimal parser; provider subunit must be integer | Currency table needs scheduled upstream review |
| Universal two-decimal assumption | JPY/KWD/BHD/OMR errors | Per-currency exponent and quantum | Extend audited table for every enabled currency |
| Fractional subunit input | Truncation changes refund/order | Money JSON pointers reject non-integers | Every new money field must be declared in policy |
| Intent reuse with changed body | Double or wrong effect | Tenant intent binds canonical operation and body hash | Reconciliation tooling is not yet automated |
| Blind retry after accepted write | Duplicate effect | Generic writes attempt once; uncertainty freezes intent | Operator runbook and fetch-by-id adapters needed |
| Cross-tenant credentials or partner header bleed | Wrong merchant charged or paid | Immutable tenant runtime and provider client | Production KMS and tenant lifecycle not implemented |
| SSRF / version smuggling | Credential disclosure | Caller cannot set URL; exact official HTTPS origin; no redirects | DNS and egress policy should independently pin destination |
| Path injection | Endpoint escape or wrong resource | Named placeholders, percent encoding, catalog validation | Add property fuzzing across templates |
| Repeated-query collapse | Incomplete expanded resource | `BTreeMap<String, Vec<String>>` is flattened without overwrite | Contract fixtures should cover every repeated query |
| Checkout signature uses browser order id | Valid signature checked against attacker-selected context | Stored provider order id is the HMAC input | Merchant callback endpoint still requires CSRF/session design |
| Signature timing or malformed length | Oracle or 500 | strict fixed-size hex plus constant-time compare | Network timing analysis has not been performed |
| Forged/re-encoded webhook | False event or verification failure | HMAC over raw bytes before JSON parse | Secret rotation and dual-key window not implemented |
| Webhook replay | Duplicate processing | Tenant-scoped event-id dedup | Retention and provider redelivery window need policy |
| Multipart MIME/part ambiguity | Invalid KYC document | one file part; extension, magic and MIME agree | Antivirus/content disarm is not implemented |
| Audit payload leaks PII/secrets | Secondary data breach | evidence retains hashes/fingerprints and state only | Provider response visible to authenticated caller; add field redaction policy |
| Audit history is edited | False post-incident narrative | per-tenant hash chain and single-successor constraint | Local administrator can rewrite DB and recompute chain; notarize heads externally |
| Dependency compromise | Code execution or policy bypass | Rust lockfile, forbidden unsafe code, constrained dependency surface | Add `cargo-deny`, SBOM, signatures, provenance and review |
| Resource exhaustion | Availability loss | bounded bodies, documents, responses, JSON depth/nodes | Add rate limits, quotas, load shedding and memory profiling |
| Stolen local gateway token | Authenticated misuse | long token requirement, constant-time comparison, session-only UI retention | Prefer workload identity/mTLS and short-lived scoped tokens |

## Security properties deliberately not claimed

- The BLAKE3 evidence chain detects inconsistent history when a trusted head exists; it is not an immutable ledger by itself.
- Test Mode demonstrates the provider protocol but does not prove settlement, banking, or live entitlement behavior.
- Policy coverage means a guarded path and semantic classification exist. It does not mean all 113 provider contracts have been dynamically exercised.
- The source scanner produces reproducible evidence candidates, not automatic vulnerability verdicts. Direct defects, compatibility gaps, and known-public hardening stay separate.
- SQLite durability on one host is not distributed consensus or disaster recovery.

## Production acceptance bar

Before enabling a live credential, require all of the following:

1. Independent security review, misuse cases, fuzzing, and dependency/supply-chain audit.
2. Central identity with least-privilege scopes, mTLS, rotation, revocation, and KMS/HSM custody.
3. Transactional replicated storage, backups, restore drills, retention policy, and independent evidence-head anchoring.
4. Product-specific reconciliation for every ambiguous write and an operator queue with four-eyes resolution.
5. Rate limiting, per-tenant quotas, egress allowlisting, alerting, SLOs, tracing redaction, and incident runbooks.
6. Dynamic Test Mode contract suites for every enabled operation plus limited canary rollout.
7. Legal, PCI, privacy, data-location, and merchant-operations review appropriate to the deployment.
