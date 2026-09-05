# RazorProof expanded defect and chain audit

Audit date: 2026-09-03

## Executive result

The expanded campaign now contains **24 evidence-backed observations**: 23 findings from eight pinned official Razorpay repositories plus one independently observed Razorpay Test Mode API defect. The repository set contains 17 direct defects, 2 conditional compatibility defects, 1 safety gap, 2 hardening observations, and 1 documentation defect. Fourteen repository findings were dynamically reproduced; four were confirmed directly from pinned source and official contracts; five are retained as known-public corroboration rather than claimed originality.

This is not a count-maximization exercise. Suspicions that matched documented behavior, depended on a runtime caveat, or lacked a violated contract were downgraded or rejected. The useful result is a set of **six compositional failure chains** that a schema linter, ordinary SAST tool, and single-SDK test suite do not see.

## What expanded beyond the original audit

| New finding | Evidence | Classification | Decisive counterexample |
|---|---|---|---|
| MCP arbitrary-currency exponent | Dynamic expression + Razorpay Test Orders | Direct defect, high | JPY 295 becomes 29,500; KWD 295.990 becomes 29,599 rather than 295,990. |
| MCP browser-authoritative economics | Pinned source + official order-security contract | Direct defect, high/security-sensitive | Generated backend creates an order from browser amount/currency and never binds the signed tuple to a server quote. |
| MCP generated Node signature length | Exact generated runtime expression | Direct robustness defect, low | Unequal-length malformed signature throws and reaches generic HTTP 500 handling. |
| MCP mobile success payloads | Pinned Android/iOS/Cordova/Capacitor templates + official callback contracts | Direct defect, high | Four generated success paths omit or blank the signature their generated backend requires. |
| MCP mobile dependency identities | Pinned templates + live npm metadata/tarball controls | Direct defect, high/security-sensitive | Two names do not resolve to a working official SDK; Capacitor selects a 179-byte third-party `Empty package`. |
| .NET client isolation | Executed official SDK | Direct defect, high/security-sensitive | Client B overwrites A's credentials, inherits A's partner header, and causes A's valid signature to fail. |
| PHP client isolation | Executed official SDK | Direct defect, high/security-sensitive | Client B overwrites A's global key and inherits A's partner header. |
| Java partner-header isolation | Executed official SDK | Direct defect, high/security-sensitive | Client B inherits A's `X-Razorpay-Account` and can overwrite the map for all clients. |
| Java upload MIME | Executed official serializer bytes | Direct defect, medium | Runtime `proof.png` becomes `image/pdf`; PDF uses non-standard `image/pdf`. |
| Java duplicate multipart file | Executed official serializer bytes | Direct defect, medium | One request contains two `file` parts: binary content and pathname text. |

The separate provider-control-plane finding remains `RP-API-REFUND-FRACTIONAL-COERCION`: direct JSON `100.75` was accepted and persisted as a processed 100-subunit refund in one sufficiently funded Test Mode case, despite the integer contract. A smaller-balance negative control rejected the same shape, so the exact defect is inconsistent fail-open validation and silent coercion.

## The six chains

### 1. Silent refund mutation → ambiguous retry → missed .NET event

The MCP wrapper accepts 100.75 and transmits 100. The Test Refund API independently accepted and persisted the same mutation. Two unkeyed retry requests created two distinct refund effects as documented. Signed literal-UTF-8 refund events then fail the .NET SDK's ASCII-equivalent digest. A production consumer deciding to retry because it did not accept the event is an inference, but every technical precondition is independently reproduced.

RazorProof stops this chain by compiling integer-only money, stable effect identity, exact raw-byte HMAC, and request/effect/event traceability into one contract.

### 2. Browser price trust → wrong currency conversion → valid wrong order

The generator trusts browser amount/currency, applies one hardcoded multiplier, and authenticates only the Razorpay tuple. Test Orders persisted both the generated JPY/KWD values and exact controls. Payment signature verification cannot reconstruct an absent merchant quote. A completed paid/fulfilled exploit was not attempted.

RazorProof requires a server-authoritative immutable quote bound once to order, payment, merchant, amount, currency, cart, and fulfillment.

### 3. Mobile payment success → missing signature → deterministic application failure

Android and iOS intentionally choose payment-ID-only callback protocols, while Cordova/Capacitor use payment-ID-only callback shapes. The generated clients then send an empty or absent signature to a backend that requires it. This is source-deterministic against official callback contracts; a device payment was not needed to establish the incompatible payload shapes.

### 4. Multi-client SDK use → shared auth/routing state → wrong merchant context

.NET, PHP, and Java were tested separately and all violated client isolation. .NET and PHP cross credential state; all three cross partner/custom header state. The two-account provider consequence was intentionally not executed, so it remains an inferred impact based on Razorpay's official `X-Razorpay-Account` routing semantics.

### 5. Java document upload → wrong MIME + duplicate `file` parts

The exact serialized multipart body labels PNG as `image/pdf` and emits `file` twice with conflicting types. Either defect can cause rejection or misclassification; together they make provider behavior dependent on duplicate-field selection. Provider upload was not executed because the complete wire defect is already observable locally.

### 6. Generated package name → missing/unrelated registry identity → broken mobile build

Registry evidence proves one emitted identity is absent and another is an empty non-Razorpay package, while `com.razorpay.cordova` is the working official control. Installation failure/non-functionality is current; future malicious-package takeover is explicitly only a risk.

The machine-readable and rendered chain proof is in `artifacts/chains/chained-bug-evidence.{json,md}`.

## Feature-versus-defect controls

The following suspicious behaviors are **not** promoted to defects or vulnerabilities:

- Duplicate Order `receipt` values were accepted twice. Current Orders behavior and documentation do not establish receipt as a uniqueness guarantee, so this is recorded as documentation/control-plane drift, not an outage bug.
- Orders and Payment Links rejected fractional subunits, showing those boundaries fail closed. This isolates the Refund API/MCP inconsistency rather than supporting a claim that Razorpay universally accepts fractional money.
- Two unkeyed refund calls created two effects by design. Stable header identity returned one effect and a changed body with the same key returned 409. Duplicate refund `receipt` returned 400.
- Webhook duplicate delivery and out-of-order delivery are documented operating conditions, not Razorpay defects.
- Java default charset is a compatibility defect only on older or explicitly non-UTF-8 runtimes; Java 18+ defaults to UTF-8.
- Node and .NET ordinary string equality are functionally correct verification. Fixed-time equality is tracked as hardening absent a demonstrated practical timing exploit.
- `Go 1.21 cannot load the module` was rejected because automatic toolchain selection can download the required version.
- The currently observed third-party Cordova-like package is empty, not alleged malicious.
- The malformed-signature HTTP 500 is low-impact robustness. Denial-of-service-only claims are excluded from HackerOne reporting.

## Evidence boundary

| State | What it means |
|---|---|
| `confirmed_dynamic` | The official SDK/handler or exact generated expression executed and produced the counterexample. |
| `confirmed_static` | Pinned official source deterministically violates an official callback or protocol contract; the device/provider leg was not executed. |
| `razorpay_test_observed` | A redacted request/effect was observed in the user-owned Test Mode control plane. |
| `known_public` | An issue or PR exists; it is corroboration, not maintainer acceptance. |
| `inferred_impact` | A consequence follows from proven nodes but was intentionally not executed and is never presented as observed fact. |

No Live Mode transaction was attempted. Credentials, webhook secrets, raw signed bodies, contact details, and provider entity IDs remain in ignored private files. Published provider artifacts use hashes and one-way entity fingerprints.

## Tracker routing

Six non-security correctness defects were deduplicated and recorded publicly:

- https://github.com/razorpay/razorpay-java/issues/365
- https://github.com/razorpay/razorpay-mcp-server/issues/133
- https://github.com/razorpay/razorpay-mcp-server/issues/134
- https://github.com/razorpay/razorpay-mcp-server/issues/135
- https://github.com/razorpay/razorpay-dot-net/issues/156
- https://github.com/razorpay/razorpay-ruby/issues/276

Six security-sensitive reports are drafted separately for private HackerOne routing, in accordance with Razorpay's repository security policy. They are listed in `artifacts/disclosure/tracker-ledger.md`; no public GitHub issue contains their proof details.

## Decisive sources and artifacts

- Razorpay order/currency contract: https://razorpay.com/docs/payments/server-integration/nodejs/integration-steps/?preferred-country=IN
- Razorpay partner routing contract: https://razorpay.com/docs/partners/aggregators/partner-auth/?preferred-country=IN
- Razorpay document upload contract: https://razorpay.com/docs/api/documents/create/?preferred-country=IN
- Razorpay Android callback contract: https://razorpay.com/docs/payments/payment-gateway/android-integration/standard/integration-steps/?preferred-country=SG
- Razorpay iOS callback contract: https://razorpay.com/docs/payments/payment-gateway/ios-integration/standard/test-integration/?preferred-country=US
- Official Cordova SDK: https://github.com/razorpay/razorpay-cordova
- Expanded scanner report: `artifacts/expanded/case-report.md`
- Test currency/integer/receipt matrix: `artifacts/razorpay-test/expanded-order-contract-matrix.md`
- Registry identity evidence: `artifacts/registry/mobile-registry-evidence.md`
- Chained-bug proof: `artifacts/chains/chained-bug-evidence.md`
- Disclosure ledger: `artifacts/disclosure/tracker-ledger.md`

## Why the architecture is the actual product

The bugs are deliberately heterogeneous: money exponent, binary-float conversion, browser trust, callback shape, package ownership, static SDK state, HMAC bytes, AEAD nonce semantics, and multipart cardinality. A patch-specific linter needs a separate rule for every file. RazorProof instead compiles a small set of economic and protocol invariants across generation inputs, SDK implementations, provider contracts, runtime requests, effects, and signed events.

That is the hard differentiator: the demo does not merely show that six bugs exist. It shows one executable architecture finding them before money moves, proving the violated invariant, generating a minimal counterexample, and demonstrating the remediation boundary.
