# RazorProof Chained-Bug Evidence

> Chains are composed only from independently evidenced nodes. Unexecuted production consequences remain explicitly labelled inference.

- All evidence-backed nodes pass: `True`
- Inferences explicit: `True`

## CHAIN-REFUND-MUTATION-RETRY-OBSERVABILITY: Silent refund mutation can combine with non-idempotent retry and lost .NET webhook visibility

Proof grade: all components reproduced; the production retry trigger is an explicit inference.

| Node | State | Claim | Evidence |
|---:|---|---|---|
| 1 | `confirmed_dynamic` | Official MCP handler accepts 100.75 and sends 100 to the SDK request path. | `RP-MCP-REFUND-TRUNCATION` |
| 2 | `razorpay_test_observed` | The direct Refund API separately accepted 100.75 and returned/persisted 100. | `artifacts/razorpay-test/refund-identity-matrix.json` |
| 3 | `razorpay_test_control` | Two unkeyed retry requests created two distinct effects by documented identity semantics. | `artifacts/razorpay-test/refund-identity-matrix.json` |
| 4 | `razorpay_test_observed` | Signed refund webhooks contained literal UTF-8; exact bytes verified and the .NET ASCII-equivalent digest failed. | `artifacts/razorpay-test/webhook-byte-evidence.json` |
| 5 | `inferred_impact` | If a consumer treats the rejected event as absence/failure and retries without a stable identity, the independently proven retry behavior amplifies one intent into multiple refunds. | `composition of the four preceding counterexamples` |

RazorProof prevention:

- integer-only monetary boundary
- mandatory stable effect identity for retryable money movement
- exact raw-byte webhook verification
- cross-artifact trace linking request, effect, and event

## CHAIN-CHECKOUT-ECONOMIC-DECOUPLING: Browser-controlled economics plus fixed currency exponent can create a valid but wrong-priced order

Proof grade: generated path and Test order persistence proven; paid fulfillment remains unexecuted.

| Node | State | Claim | Evidence |
|---:|---|---|---|
| 1 | `confirmed_static` | Generated frontend sends browser amount; backend trusts amount and currency; verifier authenticates only the returned payment tuple. | `RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS` |
| 2 | `confirmed_dynamic` | The emitted ×100 expression maps JPY 295 to 29,500 and KWD 295.990 intent to 29,599. | `RP-MCP-GENERATOR-CURRENCY-EXPONENT` |
| 3 | `razorpay_test_observed` | Razorpay Test Orders persisted both wrong generated values and both exact controls. | `artifacts/razorpay-test/expanded-order-contract-matrix.json` |
| 4 | `inferred_impact` | A payment signature can prove that the wrong-priced order was paid; it cannot retroactively prove that the order matched the merchant's intended cart or quote. | `protocol property; payment/fulfillment leg not executed in this campaign` |

RazorProof prevention:

- server-authoritative immutable quote
- currency-aware exact subunit conversion
- one-time binding of quote, Razorpay order, payment, merchant, and fulfillment

## CHAIN-MOBILE-PAID-BUT-FAILED: Four generated native flows reach success without the data required by their generated verifier

Proof grade: source-deterministic against official callback contracts; device payment not executed.

| Node | State | Claim | Evidence |
|---:|---|---|---|
| 1 | `confirmed_static` | Android and iOS choose payment_id-only callback protocols; Cordova and native Capacitor use payment_id-only callback shapes. | `RP-MCP-MOBILE-MISSING-SIGNATURE` |
| 2 | `confirmed_static` | Generated Android/iOS send an empty signature and Cordova/Capacitor omit it. | `RP-MCP-MOBILE-MISSING-SIGNATURE` |
| 3 | `deterministic_consequence` | The generated backend rejects a missing or empty signature after Checkout has already reported success. | `generated verify route required-field guard` |

RazorProof prevention:

- callback-shape contract checking
- cross-file dataflow completeness
- generated success-path integration test

## CHAIN-CROSS-TENANT-ROUTING: Process-global SDK state can cross merchant authentication and partner routing boundaries

Proof grade: three official SDK runtime collisions proven; two-account provider request intentionally not executed.

| Node | State | Claim | Evidence |
|---:|---|---|---|
| 1 | `confirmed_dynamic` | .NET client B replaced A's credentials, inherited A's routing header, and made A's valid signature fail. | `RP-DOTNET-GLOBAL-AUTH-STATE` |
| 2 | `confirmed_dynamic` | PHP client B replaced A's global key and inherited A's routing header. | `RP-PHP-GLOBAL-AUTH-STATE` |
| 3 | `confirmed_dynamic` | Java client B inherited and then overwrote the process-global X-Razorpay-Account map. | `RP-JAVA-GLOBAL-PARTNER-HEADERS` |
| 4 | `inferred_impact` | A request interleaving in a multi-merchant worker can authenticate or route an operation under the wrong merchant context. | `official partner-header semantics plus reproduced shared state` |

RazorProof prevention:

- client-isolation contract
- parallel interleaving tests
- merchant-context trace assertions

## CHAIN-JAVA-DOCUMENT-WIRE-CORRUPTION: One Java upload can carry both the wrong MIME type and two conflicting file fields

Proof grade: exact SDK multipart bytes proven; provider upload not executed.

| Node | State | Claim | Evidence |
|---:|---|---|---|
| 1 | `confirmed_dynamic` | proof.png is labeled image/pdf. | `RP-JAVA-UPLOAD-MIME` |
| 2 | `confirmed_dynamic` | The same request contains two multipart fields named file, one binary and one pathname text field. | `RP-JAVA-UPLOAD-DUPLICATE-FILE-PART` |
| 3 | `inferred_impact` | Duplicate-field selection and MIME validation can independently or jointly reject/misclassify dispute and KYC evidence. | `document API contract; provider upload not executed` |

RazorProof prevention:

- multipart field-cardinality contract
- extension-to-MIME mapping contract
- wire-body snapshot probe

## CHAIN-MOBILE-PACKAGE-IDENTITY: Generated mobile setup crosses from Razorpay code into the wrong package identities

Proof grade: current registry state reproduced; no malicious-package claim.

| Node | State | Claim | Evidence |
|---:|---|---|---|
| 1 | `confirmed_static` | Generator emits the two non-official package names. | `RP-MCP-MOBILE-DEPENDENCY-CONFUSION` |
| 2 | `registry_observed` | Cordova/Ionic package is absent; Capacitor package exists as a two-file 'Empty package' outside Razorpay's repository identity. | `artifacts/registry/mobile-registry-evidence.json` |
| 3 | `deterministic_consequence` | Cordova/Ionic installation fails; Capacitor installs no functional Razorpay bridge. | `npm 404 and published package contents` |
| 4 | `inferred_risk` | Depending on a similarly named third-party package creates a future package-supply-chain exposure. | `package ownership boundary; current package is empty, not alleged malicious` |

RazorProof prevention:

- verified package-identity allowlist
- registry existence and repository-owner checks
- generated install smoke test
