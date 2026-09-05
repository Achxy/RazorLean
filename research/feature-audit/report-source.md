# RazorProof feature-versus-bug audit — research source

Audit date: 2026-09-03

## Research question

For each of the 14 observations in the pre-audit RazorProof report, is the behavior a contract violation, a conditional compatibility problem, an expected feature, defensive hardening, or documentation drift? The burden of proof is deliberately asymmetric: a claim remains a product bug only when executable behavior conflicts with an official contract or an official release identifies the same behavior as a bug.

## Decision rules

1. `defect`: observed behavior contradicts an official protocol/API contract or a provider release explicitly identifies the behavior as a bug.
2. `compatibility_defect`: implementation rejects valid contract-shaped input only under a contingent runtime, encoding, or delivery condition.
3. `safety_gap`: the underlying API behavior is intentional, but the tool fails to expose or explain the available safe operating mechanism.
4. `hardening`: current behavior is functionally correct; the proposed change reduces attack surface without a reproduced practical exploit or explicit provider mandate.
5. `documentation_defect`: published interface text and shipped interface disagree, without changing runtime semantics.
6. `rejected`: the original claim depended on an incorrect assumption.

An open GitHub issue or pull request is treated only as a public report. It is not maintainer acceptance unless merged, released, labelled, or otherwise acknowledged by the provider.

## Audit result

The original 14 claims resolve to:

- 7 direct defects;
- 2 conditional compatibility defects;
- 1 safety/discoverability gap;
- 2 defensive-hardening opportunities;
- 1 documentation defect;
- 1 rejected claim.

The production scanner now emits 13 observations because the rejected Go claim was removed. Nine are defect-level behavior; two remain conditional. The separate Test Mode campaign adds `RP-API-REFUND-FRACTIONAL-COERCION`, producing 14 combined observations and 8 direct defects.

## Claim-by-claim disposition

| Original claim | Revised classification | Decision | Decisive reason |
|---|---|---|---|
| RP-DOTNET-GCM-NONCE-REUSE | Direct defect, critical | Keep | The SDK copies key bytes into every AES-GCM nonce. Razorpay's Ruby and PHP releases independently call the same pattern a nonce-reuse vulnerability/bug and ship fresh random nonces. |
| RP-MCP-GENERATOR-MONEY-UNDERCHARGE | Direct defect, high | Keep; downgrade from critical | Razorpay's Order API requires an integer amount in the smallest subunit. Seven emitted backend expressions convert major-unit floats with truncation; each executable expression produced 200 for an intended 201 paise. The per-conversion error is one subunit, so `high` is more defensible than `critical`. |
| RP-MCP-EXPAND-COLLAPSE | Direct defect, medium | Keep | The loop overwrites `expand[]`, while the requested protocol value is a repeated parameter. The linked public PR demonstrates the same last-value-only behavior and a slice-based fix. |
| RP-MCP-REFUND-TRUNCATION | Direct defect, medium | Keep; downgrade from high | The Refund API requires integer subunits. The handler accepts 100.75 and sends 100 instead of rejecting invalid input. The numerical mutation is less than one subunit, so this is input-integrity, not a severe monetary-loss claim. |
| RP-RUBY-PAYLINK-ORDER | Direct defect, medium | Keep; downgrade from high | Razorpay documents a fixed signed-field order. The Ruby SDK derives order from Hash insertion order and includes unrelated extra fields, so identical named fields can verify or fail solely because of container construction. |
| RP-PYTHON-PAYLINK-MISSING-FIELD | Direct robustness defect, low | Keep; downgrade from medium | The function intends to fail incomplete input cleanly but omits two required fields from its guard, then throws `KeyError`. This is real but limited to malformed/incomplete input handling. |
| RP-DOTNET-WEBHOOK-ASCII | Direct defect, medium | Keep; live reachability now confirmed | A correct UTF-8 HMAC over literal non-ASCII JSON bytes is rejected because the SDK hashes ASCII substitutions. Razorpay Test Mode delivered 16 validly signed literal-UTF-8 payment-link and refund bodies; exact bytes verified and the ASCII-equivalent digest failed all 16. |
| RP-JAVA-DEFAULT-CHARSET | Conditional compatibility defect, medium | Keep with runtime caveat; downgrade from high | The SDK compiles for Java 8 and calls `payload.getBytes()` without a charset. That is locale-dependent on older/configured JVMs. Java 18+ standardized UTF-8 as the default, so the defect is not universal. |
| RP-PYTHON-WEBHOOK-BYTES | Conditional compatibility defect, medium | Keep; downgrade from high | Official guidance says preserve the raw body. Python web frameworks commonly expose it as bytes, but the SDK unconditionally applies the two-argument `bytes()` constructor and throws. The contract requires content preservation, not one Python type, so this is API compatibility rather than a protocol/security failure. |
| RP-MCP-REFUND-IDEMPOTENCY | Safety/discoverability gap, medium | Reject the original “no idempotency” framing | Multiple no-key refund requests are distinct requests by design. More importantly, the MCP tool already exposes `receipt`, and Razorpay documents `receipt` as an idempotency key that rejects duplicates. The actual gap is missing header support and a description that hides receipt's retry-safety role. |
| RP-DOTNET-SIGNATURE-COMPARE | Hardening, low | Do not call a bug or vulnerability | Ordinary equality returns the correct result. Fixed-time comparison is good cryptographic hygiene, but no practical remote timing exploit was reproduced and Razorpay's public verification pseudocode does not make constant-time behavior an API contract. |
| RP-NODE-SIGNATURE-COMPARE | Hardening, low | Do not call a bug or vulnerability | Same reasoning as .NET. Node provides `timingSafeEqual`, but availability of a safer primitive does not make strict equality functionally incorrect. The public issue is unreviewed and states no public proof of concept. |
| RP-MCP-PAYOUT-NAME-DRIFT | Documentation defect, low | Keep only as docs/interface drift | README publishes `fetch_payout_by_id`; the registry exposes `fetch_payout_with_id`. An agent following the table fails, but the actual payout implementation is not broken. |
| RP-MCP-GO-VERSION-DRIFT | Rejected | Remove from scanner | Since Go 1.21, the default `GOTOOLCHAIN=auto` can download and run the newer toolchain named by `go.mod`. The failure occurs only under `GOTOOLCHAIN=local` or an offline/restricted environment. The old statement “Go 1.21 cannot load this module” was false as a general claim. |

### Additional provider-control-plane finding

| New claim | Classification | Decision | Decisive reason |
|---|---|---|---|
| RP-API-REFUND-FRACTIONAL-COERCION | Direct defect, medium | Add from real Test Mode evidence | The official API contract types `amount` as integer smallest-unit money. A direct JSON request for `100.75` returned HTTP 200, created a 100-subunit refund, emitted signed lifecycle webhooks, and reached `processed` in the provider ledger. A smaller-balance negative control rejected the same invalid value, so the exact claim is inconsistent fail-open validation and silent coercion. |

## Decisive executable checks

### Generated money matrix

The exact emitted conversions were executed for Python, Ruby, PHP, Go, Java, Rust, and .NET. Every truncating expression returned `200` for `2.01 * 100`; the Node `Math.round` control returned `201`. The checked-in reusable probe sources are under `research/feature-audit/probes/`.

This proves the numerical behavior. The official Order API supplies the missing semantic premise: `amount` is an integer in the smallest currency subunit. It is therefore not a supported “round down by design” feature.

### Go toolchain counterexample to the old claim

- Go 1.23 with `GOTOOLCHAIN=local`: module loading failed because `go.mod` requires Go 1.24.2.
- The same image with the default automatic policy began downloading Go 1.24.2.

This exactly matches the Go toolchain documentation and disproves the unconditional old claim.

### Refund remediation audit

The earlier remediation added a local `WithInteger`, but the MCP adapter mapped both `integer` and `number` back to `mcp.WithNumber`. That did not prove the published schema became integer. The remediation was replaced with handler-level `int64` validation, and the regression test now requires both:

- 100.75 is rejected before the HTTP request;
- 100 is accepted and sent unchanged.

Publishing a true integer schema additionally requires upgrading from `mcp-go` v0.43.2 to a version with native `WithInteger` support (introduced in v0.50.0) and mapping it without downgrading the type.

### Real provider Test Mode checks

- The ₹2.01 generated-code undercharge reached Razorpay's Orders API as 200 subunits; an exact 201 control remained 201.
- Header idempotency returned one refund identity for an identical retry and rejected the same key with a changed body.
- Receipt identity rejected a duplicate; two unkeyed calls created two distinct effects, which is intentional provider behavior.
- A direct fractional refund request `100.75` was accepted, normalized to 100, emitted signed lifecycle webhooks, and settled. This independently reproduces the money-contract failure below the MCP wrapper.
- A 101-subunit-remaining negative control rejected `100.75` and all attempted close forms in that fixture. It disproves universal coercion and the proposed one-paise-dust story; that stronger claim is not made.
- Across 22 captured webhooks, all signatures verified. Sixteen bodies contained literal non-ASCII bytes; exact UTF-8 verification passed and the .NET ASCII-equivalent HMAC failed every one.

## Expected behavior that RazorProof must not flag

- Webhook duplicate delivery is documented and must be deduplicated using the event ID.
- Webhook ordering is not guaranteed.
- A new refund request without `receipt` or `X-Refund-Idempotency` is a new refund intent.
- Sandbox-specific payment outcomes and unsupported real-rail behavior are test-mode limitations, not production bugs.
- Ordinary signature equality is a functional verifier; constant-time comparison is a separate hardening policy.

These negative controls should become regression fixtures so future scanner rules cannot quietly turn platform contracts into “bugs.”

## Source ledger

| Source | Type | Used for | Reliability / limitation |
|---|---|---|---|
| https://razorpay.com/docs/api/orders/create/?preferred-country=IN | Official API documentation | Integer smallest-subunit Order amount | Primary contract source. |
| https://razorpay.com/docs/api/refunds/normal-refunds-idempotent/?preferred-country=IN | Official API documentation | Refund integer amount and header idempotency | Primary contract source. |
| https://razorpay.com/docs/api/refunds/create-normal/?preferred-country=US | Official API documentation | `receipt` is treated as an idempotency key; duplicates rejected | Primary contract source; decisive against the old no-idempotency framing. |
| https://razorpay.com/docs/webhooks/validate-test/?locale=en-US | Official documentation | Raw body, duplicate delivery, event ordering | Primary contract/operations source; literal-Unicode delivery is independently proven by the redacted Test capture bundle. |
| artifacts/razorpay-test/refund-identity-matrix.json | Direct Test Mode observation | Fractional refund coercion and identity matrix | Redacted provider response evidence; private IDs omitted. |
| artifacts/razorpay-test/refund-ledger.json | Direct Test Mode observation | Processed refund effects and exact ledger total | Redacted provider ledger evidence. |
| artifacts/razorpay-test/webhook-byte-evidence.json | Direct Test Mode observation | Literal UTF-8 reachability and signature behavior | Raw bodies, signatures, contact data, IDs, and secret omitted; SHA-256 links to private captures. |
| https://razorpay.com/docs/payments/payment-links/apis/?preferred-country=US | Official documentation | Canonical payment-link signed-field order | Primary protocol source. |
| https://github.com/razorpay/razorpay-ruby/releases/tag/v3.2.4 | Official Razorpay release | Identifies fixed-nonce AES-GCM as nonce reuse vulnerability | Provider-authored release evidence. |
| https://github.com/razorpay/razorpay-php/releases/ | Official Razorpay release list | PHP 2.9.3 calls fresh random nonce a bug fix preventing nonce reuse | Provider-authored corroboration. |
| https://go.dev/doc/toolchain | Official Go documentation | Automatic toolchain switching from Go 1.21 | Primary language-toolchain source. |
| https://github.com/mark3labs/mcp-go/releases | Official dependency release list | Native integer option added in v0.50.0 | Primary dependency source; project is pinned to v0.43.2. |
| https://github.com/razorpay/razorpay-mcp-server/pull/108 | Public PR | `expand[]` collapse reproduction/fix | Public report, not maintainer acceptance. Source behavior is independently visible. |
| https://github.com/razorpay/razorpay-mcp-server/pull/128 | Public PR | Missing refund header support and live test-mode observations | Public report, not maintainer acceptance; its own text acknowledges receipt idempotency. |
| https://github.com/razorpay/razorpay-python/issues/121 | Public issue | Raw bytes integration failure | User report, not maintainer acceptance; independently reproduced. |
| https://github.com/razorpay/razorpay-python/pull/333 | Public PR | Missing payment-link field guard | Public proposal, not maintainer acceptance; independently reproduced. |
| https://github.com/razorpay/razorpay-java/issues/351 | Public issue | Default-charset concern | User report, not maintainer acceptance; source confirmed, environment conditional. |
| https://github.com/razorpay/razorpay-node/issues/479 | Public issue | Timing-safe comparison proposal | User report explicitly without a public PoC; supports hardening only. |
| https://nodejs.org/api/crypto.html#cryptotimingsafeequala-b | Official Node documentation | Availability/purpose of timing-safe equality | Supports best practice, not provider-contract violation. |
| https://learn.microsoft.com/en-us/dotnet/api/system.security.cryptography.cryptographicoperations.fixedtimeequals | Official .NET documentation | Availability/purpose of fixed-time equality | Supports best practice, not provider-contract violation. |

## Conclusion

The audit weakens speculative claims and strengthens the real ones. The scanner no longer depends on classifying every suspicious line as a bug. Its strongest demonstrations now survive hostile review:

1. official generated integrations measurably create the wrong order amount across seven backend languages;
2. the .NET SDK measurably reuses an AES-GCM nonce, and Razorpay's own other-SDK releases identify that exact pattern as a vulnerability;
3. provider-signed literal UTF-8 deliveries measurably fail the .NET ASCII verifier;
4. the Test Refund API measurably accepts and silently coerces a contract-invalid fractional amount on a real control-plane path.

Everything else is now labelled at the level the evidence actually supports.
