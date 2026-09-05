# RazorProof Evidence Report

> A semantic conformance compiler for money, cryptographic bytes, effect identity, and cross-SDK protocol behavior.

## Executive result

RazorProof inspected **8 pinned official repositories** and produced **13 evidence-backed observations**: **7 direct defects**, **2 conditional compatibility defects**, and **4 non-bug safety, hardening, or documentation gaps**. It dynamically reproduced **5 independently discovered observations** and links **6 prior public reports** without treating an open issue or pull request as maintainer confirmation.

- Evidence levels: `confirmed_dynamic`=7, `confirmed_static`=2, `known_public`=4
- Claim types: `compatibility_defect`=2, `defect`=7, `documentation_defect`=1, `hardening`=2, `safety_gap`=1
- Severity: `critical`=1, `high`=1, `low`=4, `medium`=7
- Scan window: `2026-09-03T09:40:40.367704+00:00` to `2026-09-03T09:41:10.413755+00:00`
- Contract: `contracts/razorpay.json`

The strongest day-zero case is not hypothetical: the official MCP checkout generator emits binary-float conversion code into new merchant backends. On the executable ₹2.01 counterexample, Python, Ruby and PHP each produced **200 paise instead of 201**. Static matches show the same truncating construction in Go, Java, Rust and .NET templates. This is an AI tool creating a financial bug in downstream applications, precisely the class of failure RazorProof prevents at generation time.

The second strongest case is a cross-SDK security regression: the current .NET SDK derives an AES-GCM IV from the key while current Ruby, Node, Java and PHP SDKs contain the fresh-random-nonce fix. A real Razorpay Test Mode campaign also closed the .NET webhook reachability caveat: 16 signed deliveries contained literal UTF-8 metadata, exact bytes verified, and the SDK's ASCII transformation failed every one.

## Reproducibility boundary

- `confirmed_dynamic` means this run executed the official SDK/handler or the exact emitted expression and observed the counterexample.
- `confirmed_static` means the violation is directly present in pinned official source, but this run did not execute that path.
- `known_public` means a public issue or pull request exists. It is corroboration, not proof of maintainer acceptance and not claimed originality.
- `hardening`, `safety_gap`, and `documentation_defect` are deliberately not represented as runtime product bugs.
- No Live Mode transaction was attempted. Test Mode E2E used a user-owned account; credentials, raw webhook payloads, contact data, and provider IDs remain in ignored private files and never enter the evidence bundle.

## Real Razorpay Test Mode evidence

The repository scan is backed by a separate provider-control-plane campaign. It adds one API-level defect beyond the 13 repository observations: `RP-API-REFUND-FRACTIONAL-COERCION`. Razorpay's documented Refund API types `amount` as integer smallest-subunit money, yet a direct JSON request for `100.75` returned HTTP 200, created a 100-subunit refund, emitted signed `refund.created` and `refund.processed` events, and settled in the provider ledger. A smaller-balance negative control rejected the same invalid input, so the finding is precisely an inconsistent fail-open validation path, not a claim that every fractional request succeeds.

- [Campaign summary](../razorpay-test/campaign-summary.md): headline results, adversarial bounds, and the evidence map.
- [Order boundary and generated undercharge](../razorpay-test/order-boundary.md): the official generated `int(2.01 * 100)` submits and persists 200, while the exact control persists 201.
- [Refund identity matrix](../razorpay-test/refund-identity-matrix.md): header conflict rejection, receipt duplicate prevention, two distinct unkeyed effects, and the fractional 100.75 to 100 coercion.
- [Final redacted refund ledger](../razorpay-test/refund-ledger.md): all six refunds processed and the 801-subunit payment reached fully refunded with exact ledger equality.
- [Literal UTF-8 webhook proof](../razorpay-test/webhook-byte-evidence.md): 22 signed deliveries across six event types; all signatures valid; all 16 literal-non-ASCII deliveries fail the .NET ASCII-equivalent digest.
- [Negative control](../razorpay-test/refund-fractional-dust.md): the 101-subunit remainder rejected 100.75, disproving the stronger stranded-dust hypothesis and bounding the defect.

## Findings

### RP-DOTNET-GCM-NONCE-REUSE: .NET onboarding signatures reuse an AES-GCM nonce derived from the secret key

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `critical`; confidence: `100%`
- Originality: independently discovered and executed against the official SDK
- Surface: `razorpay-dot-net` / Utils.GenerateOnboardingSignature
- Invariant: AES-GCM uses a fresh unique nonce for every encryption under a key.
- Assessment: Two official SDK calls with identical input and key returned identical ciphertext.
- Impact: Nonce reuse breaks AES-GCM confidentiality and authentication guarantees; repeated onboarding signatures become deterministic and related plaintexts leak keystream relations.
- Counterexample: `{"first_prefix": "19607e8e4c0d48fb606b168a", "gcm_same": true, "unicode_accepted": false, "unicode_error": "SignatureVerificationError: Invalid signature passed"}`
- Fix direction: Generate 12 random bytes per call and return nonce || ciphertext || 16-byte tag, matching the other current SDKs.

Evidence:

- `official_source` IV is deterministically copied from the key ([razorpay-dot-net/src/Utils.cs:104](https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/Utils.cs)) — Array.Copy(keyBytes, 0, iv, 0, 12)
- `cross_sdk_release` Ruby release documents the same nonce-reuse defect and fixed wire format ([cross_sdk_release](https://github.com/razorpay/razorpay-ruby/releases/tag/v3.2.4))
- `executed_official_sdk` Official .NET SDK runtime probe (razorpay-dot-net/src/Utils.cs) — {"first_prefix": "19607e8e4c0d48fb606b168a", "gcm_same": true, "unicode_accepted": false, "unicode_error": "SignatureVerificationError: Invalid signature passed"}

### RP-MCP-GENERATOR-MONEY-UNDERCHARGE: Checkout generator emits one-paise undercharge bugs across seven backend languages

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `high`; confidence: `100%`
- Originality: independently discovered and reproduced; no matching public issue or pull request found
- Surface: `razorpay-mcp-server` / integrate_razorpay_checkout generated backend code
- Invariant: Major-to-minor currency conversion must be decimal-exact and produce the intended integer subunit value.
- Assessment: Exact expressions emitted by the templates were executed on locally installed runtimes.
- Impact: Fresh projects generated by Razorpay's official AI tool can create orders for less than the user-entered price. The defect is copied into merchant code, multiplying its blast radius.
- Counterexample: `₹2.01 should be 201 paise; python, ruby, php returned 200. Node's rounded control returned 201.`
- Fix direction: Make the generated boundary accept integer subunits or exact decimal strings; reject excess precision and convert with a decimal type.

Evidence:

- `official_source` Generated backend uses binary float then truncates ([razorpay-mcp-server/pkg/razorpay/integrations/backend_python.go:28](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_python.go)) — int(amount * 100)
- `official_source` Generated backend uses binary float then truncates ([razorpay-mcp-server/pkg/razorpay/integrations/backend_go.go:58](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_go.go)) — int(req.Amount * 100)
- `official_source` Generated backend uses binary float then truncates ([razorpay-mcp-server/pkg/razorpay/integrations/backend_java.go:48](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_java.go)) — (int) (amount * 100)
- `official_source` Generated backend uses binary float then truncates ([razorpay-mcp-server/pkg/razorpay/integrations/backend_other.go:154](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_other.go)) — (amount * 100).to_i
- `official_source` Generated backend uses binary float then truncates ([razorpay-mcp-server/pkg/razorpay/integrations/backend_other.go:300](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_other.go)) — (req.amount * 100.0) as i64
- `official_source` Generated backend uses binary float then truncates ([razorpay-mcp-server/pkg/razorpay/integrations/backend_other.go:447](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_other.go)) — (int)(request.Amount * 100)
- `executed_emitted_expression` Official generated conversion expressions undercharge ₹2.01 (razorpay-mcp-server/pkg/razorpay/integrations) — {"node_control": {"exit": 0, "minor_units": "201", "stderr": ""}, "php": {"exit": 0, "minor_units": "200", "stderr": ""}, "python": {"exit": 0, "minor_units": "200", "stderr": ""}, "ruby": {"exit": 0, "minor_units": "200", "stderr": ""}}

### RP-DOTNET-WEBHOOK-ASCII: .NET webhook verifier hashes non-ASCII strings as ASCII

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `medium`; confidence: `100%`
- Originality: independently discovered and executed against the official SDK
- Surface: `razorpay-dot-net` / Utils.verifyWebhookSignature
- Invariant: HMAC input is the exact UTF-8 request body, byte for byte.
- Assessment: A correct UTF-8 HMAC for a JSON payload containing ₹ and Malayalam text was rejected by the official SDK.
- Impact: A correct UTF-8 signature is rejected for ordinary Razorpay Test Mode payment-link and refund deliveries containing literal non-ASCII metadata.
- Counterexample: `{"first_prefix": "19607e8e4c0d48fb606b168a", "gcm_same": true, "unicode_accepted": false, "unicode_error": "SignatureVerificationError: Invalid signature passed"}`
- Fix direction: Expose a byte[] webhook API and use UTF-8 explicitly for string compatibility overloads.

Evidence:

- `official_source` All signature strings are encoded as ASCII ([razorpay-dot-net/src/Utils.cs:135](https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/Utils.cs)) — new ASCIIEncoding()
- `executed_official_sdk` Official .NET SDK runtime probe (razorpay-dot-net/src/Utils.cs) — {"first_prefix": "19607e8e4c0d48fb606b168a", "gcm_same": true, "unicode_accepted": false, "unicode_error": "SignatureVerificationError: Invalid signature passed"}

### RP-JAVA-DEFAULT-CHARSET: Java webhook HMAC payload uses the process default charset

- Claim type: `compatibility_defect`; evidence: `known_public`; severity: `medium`; confidence: `100%`
- Originality: publicly reported compatibility issue and independently source-confirmed; not maintainer-confirmed
- Surface: `razorpay-java` / Utils.getHash
- Invariant: String compatibility APIs encode exact UTF-8 deterministically.
- Assessment: The secret is explicitly UTF-8 but the payload calls getBytes() with no charset.
- Impact: Unicode verification can depend on host locale on Java versions/configurations with a non-UTF-8 default. Java 18+ defaults to UTF-8, so this is conditional rather than universal.
- Fix direction: Use StandardCharsets.UTF_8 and add a byte[] verifier.
- Prior public reference: [https://github.com/razorpay/razorpay-java/issues/351](https://github.com/razorpay/razorpay-java/issues/351)

Evidence:

- `official_source` Default-charset payload encoding ([razorpay-java/src/main/java/com/razorpay/Utils.java:108](https://github.com/razorpay/razorpay-java/blob/ad9ab7b6e6f045b782dfd7608da04de9f930ad97/src/main/java/com/razorpay/Utils.java)) — sha256_HMAC.doFinal(payload.getBytes())

### RP-MCP-EXPAND-COLLAPSE: Repeated expand[] values collapse to the last value

- Claim type: `defect`; evidence: `known_public`; severity: `medium`; confidence: `100%`
- Originality: publicly reported and source-confirmed; the linked pull request is not maintainer acceptance
- Surface: `razorpay-mcp-server` / collection query builder
- Invariant: Repeated query parameters preserve multiplicity and order.
- Assessment: The loop overwrites one map key for every requested expansion.
- Impact: Callers asking for multiple expansions receive only the final expansion.
- Counterexample: `expand=[payments, transfers] -> expand[]=transfers`
- Fix direction: Represent repeated query values as a list and encode every occurrence.
- Prior public reference: [https://github.com/razorpay/razorpay-mcp-server/pull/108](https://github.com/razorpay/razorpay-mcp-server/pull/108)

Evidence:

- `official_source` Each loop iteration overwrites the same key ([razorpay-mcp-server/pkg/razorpay/tools_params.go:265](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/tools_params.go)) — params["expand[]"] = val

### RP-MCP-REFUND-IDEMPOTENCY: Refund tool omits header idempotency and hides receipt safety semantics

- Claim type: `safety_gap`; evidence: `known_public`; severity: `medium`; confidence: `100%`
- Originality: publicly reported safety gap; the linked pull request is not maintainer acceptance
- Surface: `razorpay-mcp-server` / create_refund MCP tool
- Invariant: A retryable money-moving action exposes and preserves effect identity.
- Assessment: The tool cannot send X-Refund-Idempotency and describes receipt only as an internal reference, even though Razorpay documents a stable receipt as an idempotency key.
- Impact: A caller that omits receipt can create another refund on retry by design. A caller that reuses a stable receipt already has duplicate protection, so this is a safety/discoverability gap rather than a broken refund API.
- Counterexample: `No identity is intentionally a new refund; stable receipt or X-Refund-Idempotency identifies one effect.`
- Fix direction: Document receipt as the existing idempotency mechanism and also expose X-Refund-Idempotency for explicit retry identity.
- Prior public reference: [https://github.com/razorpay/razorpay-mcp-server/pull/128](https://github.com/razorpay/razorpay-mcp-server/pull/128)

Evidence:

- `official_source` Tool exposes receipt but describes it only as internal reference ([razorpay-mcp-server/pkg/razorpay/refunds.go:42](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/refunds.go)) — mcpgo.WithString(
			"receipt",
- `official_source` Refund SDK call passes nil headers ([razorpay-mcp-server/pkg/razorpay/refunds.go:75](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/refunds.go)) — int(payload["amount"].(float64)), data, nil)

### RP-MCP-REFUND-TRUNCATION: Refund tool silently truncates a fractional subunit amount

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `medium`; confidence: `100%`
- Originality: independently discovered and reproduced against the official handler and SDK request path
- Surface: `razorpay-mcp-server` / create_refund MCP tool
- Invariant: Money in currency subunits is an integer and invalid fractions must be rejected, never changed.
- Assessment: A generated black-box regression test invoked the official tool handler and intercepted its HTTP request.
- Impact: An invalid fractional-subunit request reaches the API with a different value instead of failing closed. The mutation is less than one subunit, so this is an input-integrity defect rather than a large-value loss claim.
- Counterexample: `fractional money crossed the MCP boundary: requested=100.75 sent=100`
- Fix direction: Validate and store an int64 before invoking the SDK; upgrade the MCP dependency and publish an integer schema when supported.

Evidence:

- `official_source` Amount is accepted as binary float ([razorpay-mcp-server/pkg/razorpay/refunds.go:64](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/refunds.go)) — ValidateAndAddRequiredFloat(payload, "amount")
- `official_source` Float is silently cast to integer ([razorpay-mcp-server/pkg/razorpay/refunds.go:75](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/refunds.go)) — int(payload["amount"].(float64))
- `executed_official_handler` Black-box HTTP interception observed 100.75 mutate to 100 (razorpay-mcp-server/pkg/razorpay/refunds.go) — === RUN   TestRazorProofFractionalRefundMustFailClosed
logs are stored in: /tmp/go-build20183757/b001/logs
    razorproof_fractional_test.go:33: fractional money crossed the MCP boundary: requested=100.75 sent=100
--- FAIL: TestRazorProofFractionalRefundMustFailClosed (0.02s)
FAIL
FAIL	github.com/razorpay/razorpay-mcp-server/pkg/razorpay	0.025s
FAIL
go: downloading github.com/razorpay/razorpay-go v1.4.0
go: downloading github.com/go-test/deep v1.1.1
go: downloading github.com/stretchr/testify v1.10.0
go: downloading github.com/mark3labs/mcp-go v0.43.2
go: downloading github.com/gorilla/mux v1.8.1
go: downloading github.com/davecgh/go-spew v1.1.1
go: downloading gopkg.in/yaml.v3 v3.0.1
go: downloading github.com/pmezard/go-difflib v1.0.0
go: downloading github.com/yosida95/uritemplate/v3 v3.0.2
go: downloading github.com/invopop/jsonschema v0.13.0
go: downloading github.com/spf13/cast v1.7.1
go: downloading github.com/google/uuid v1.6.0
go: downloading github.com/wk8/go-ordered-map/v2 v2.1.8
go: downloading github.com/mailru/easyjson v0.7.7
go: downloading github.com/buger/jsonparser v1.1.1
go: downloading github.com/bahlo/generic-list-go v0.2.0


### RP-PYTHON-WEBHOOK-BYTES: Python webhook verifier rejects the raw bytes the webhook contract asks callers to preserve

- Claim type: `compatibility_defect`; evidence: `confirmed_dynamic`; severity: `medium`; confidence: `100%`
- Originality: publicly reported compatibility issue, independently reproduced against the pinned official commit
- Surface: `razorpay-python` / Utility.verify_webhook_signature
- Invariant: Valid raw request bytes are accepted without decoding and re-encoding.
- Assessment: A valid HMAC over a bytes payload throws before comparison.
- Impact: Framework integrations that correctly retain the raw body cannot pass it to the SDK.
- Counterexample: `TypeError: encoding without a string argument`
- Fix direction: Encode str inputs and preserve bytes/bytearray inputs.
- Prior public reference: [https://github.com/razorpay/razorpay-python/issues/121](https://github.com/razorpay/razorpay-python/issues/121)

Evidence:

- `official_source` Unconditional str-to-bytes constructor ([razorpay-python/razorpay/utility/utility.py:62](https://github.com/razorpay/razorpay-python/blob/8960507a29854c8a484d130139179c2429c2f45c/razorpay/utility/utility.py)) — body = bytes(body, 'utf-8')
- `executed_official_sdk` Valid raw-byte webhook invocation throws TypeError (razorpay-python/razorpay/utility/utility.py) — {"incomplete_payment_link_exception": "KeyError: 'payment_link_id'", "raw_bytes_exception": "TypeError: encoding without a string argument"}

### RP-RUBY-PAYLINK-ORDER: Ruby payment-link verification depends on Hash insertion order

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `medium`; confidence: `100%`
- Originality: independently discovered and reproduced; no matching public report found
- Surface: `razorpay-ruby` / Utility.verify_payment_link_signature
- Invariant: The signed field order is protocol-defined, not caller-container-defined.
- Assessment: The official SDK accepted a correctly signed docs-order Hash and rejected the identical key/value set inserted in another order.
- Impact: An authentic callback fails verification when the application builds the same field set in a different order; extra fields also contaminate the signature payload.
- Counterexample: `{"ordered": "accepted", "reordered": "SecurityError: Signature verification failed"}`
- Fix direction: Read the four named fields explicitly in the protocol-defined order and do not mutate the caller's Hash.

Evidence:

- `official_source` Signature payload follows Hash insertion order ([razorpay-ruby/lib/razorpay/utility.rb:20](https://github.com/razorpay/razorpay-ruby/blob/807e80eb25572823ebb1872529747fb9af97282e/lib/razorpay/utility.rb)) — attributes.values.join('|')
- `executed_official_sdk` Same signed fields: ordered accepted, reordered rejected (razorpay-ruby/lib/razorpay/utility.rb) — {"ordered": "accepted", "reordered": "SecurityError: Signature verification failed"}

### RP-DOTNET-SIGNATURE-COMPARE: .NET signature verification uses ordinary string equality

- Claim type: `hardening`; evidence: `confirmed_static`; severity: `low`; confidence: `98%`
- Originality: independently discovered hardening opportunity; no practical remote exploit reproduced
- Surface: `razorpay-dot-net` / Utils.verifySignature
- Invariant: Authentication tags are compared in constant time.
- Assessment: The verifier uses String.Equals rather than a fixed-time byte comparison.
- Impact: Ordinary equality is functionally correct. A fixed-time comparison reduces timing leakage, but practical remote exploitability was not reproduced or claimed.
- Fix direction: Decode hex and call CryptographicOperations.FixedTimeEquals.

Evidence:

- `official_source` Non-constant-time comparison ([razorpay-dot-net/src/Utils.cs:72](https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/Utils.cs)) — actualSignature.Equals(expectedSignature)

### RP-MCP-PAYOUT-NAME-DRIFT: Published payout tool name does not exist

- Claim type: `documentation_defect`; evidence: `confirmed_static`; severity: `low`; confidence: `100%`
- Originality: independently discovered
- Surface: `razorpay-mcp-server` / MCP README/tool registry
- Invariant: Published tool identifiers match the registered interface exactly.
- Assessment: README advertises fetch_payout_by_id while the server registers fetch_payout_with_id.
- Impact: An agent following the official interface table calls a nonexistent tool.
- Fix direction: Rename the registered tool or update the table and add a docs-to-registry conformance test.

Evidence:

- `official_source` Published name ([razorpay-mcp-server/README.md:56](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/README.md)) — fetch_payout_by_id
- `official_source` Registered name ([razorpay-mcp-server/pkg/razorpay/payouts.go:59](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/payouts.go)) — "fetch_payout_with_id"

### RP-NODE-SIGNATURE-COMPARE: Node webhook verifier uses ordinary string equality

- Claim type: `hardening`; evidence: `known_public`; severity: `low`; confidence: `98%`
- Originality: publicly reported hardening concern; no maintainer confirmation or practical exploit reproduction
- Surface: `razorpay-node` / validateWebhookSignature
- Invariant: Authentication tags are compared in constant time.
- Assessment: The SDK compares hex HMACs with JavaScript strict equality.
- Impact: Strict equality is functionally correct. A timing-safe comparison is defensive hardening; practical remote exploitability was not reproduced or claimed.
- Fix direction: Use crypto.timingSafeEqual after strict length and hex validation.
- Prior public reference: [https://github.com/razorpay/razorpay-node/issues/479](https://github.com/razorpay/razorpay-node/issues/479)

Evidence:

- `official_source` Non-constant-time comparison ([razorpay-node/lib/utils/razorpay-utils.js:102](https://github.com/razorpay/razorpay-node/blob/b9e8527225a7322ba2671a3bc0b848fd019d2d8c/lib/utils/razorpay-utils.js)) — expectedSignature === signature

### RP-PYTHON-PAYLINK-MISSING-FIELD: Python payment-link verifier throws KeyError for an omitted field it forgot to validate

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `low`; confidence: `100%`
- Originality: publicly proposed fix, independently reproduced against the pinned official commit
- Surface: `razorpay-python` / Utility.verify_payment_link_signature
- Invariant: Incomplete verification input fails closed with one documented result.
- Assessment: A callback-shaped map missing payment_link_id passes the guard and crashes at lookup.
- Impact: Malformed callback handling can become an application 500 rather than a clean authentication rejection.
- Counterexample: `KeyError: 'payment_link_id'`
- Fix direction: Validate the complete required field set before access.
- Prior public reference: [https://github.com/razorpay/razorpay-python/pull/333](https://github.com/razorpay/razorpay-python/pull/333)

Evidence:

- `official_source` Unchecked required field access ([razorpay-python/razorpay/utility/utility.py:28](https://github.com/razorpay/razorpay-python/blob/8960507a29854c8a484d130139179c2429c2f45c/razorpay/utility/utility.py)) — payment_link_id = str(parameters['payment_link_id'])
- `executed_official_sdk` Incomplete payment-link callback throws KeyError (razorpay-python/razorpay/utility/utility.py) — {"incomplete_payment_link_exception": "KeyError: 'payment_link_id'", "raw_bytes_exception": "TypeError: encoding without a string argument"}

## Repository ledger

| Repository | Commit |
|---|---|
| `razorpay-dot-net` | `2cd38a155ec56ea47e879a573a3acb19334c152e` |
| `razorpay-go` | `23677d8c4eb27673b2eeff06317cd12f7a7cf6ad` |
| `razorpay-java` | `ad9ab7b6e6f045b782dfd7608da04de9f930ad97` |
| `razorpay-mcp-server` | `7950d51d118ca164c32b7cf0cfaa14f34f24849f` |
| `razorpay-node` | `b9e8527225a7322ba2671a3bc0b848fd019d2d8c` |
| `razorpay-php` | `5db430659870e4232040142c6be2820971170fce` |
| `razorpay-python` | `8960507a29854c8a484d130139179c2429c2f45c` |
| `razorpay-ruby` | `807e80eb25572823ebb1872529747fb9af97282e` |

## Probe health

All requested probes completed without harness errors.

## What this POC proves

RazorProof is not another payment dashboard. It compiles semantic invariants across APIs, MCP schemas, generated integration code and seven SDK languages, then emits executable counterexamples and fix-oriented evidence. A conventional linter sees valid syntax in `int(amount * 100)`; RazorProof knows ₹2.01 must remain 201 paise. A conventional SAST rule sees AES-GCM; RazorProof compares nonce semantics across SDK releases and catches the one lagging implementation.
