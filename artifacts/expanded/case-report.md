# RazorProof Evidence Report

> A semantic conformance compiler for money, cryptographic bytes, effect identity, and cross-SDK protocol behavior.

## Executive result

RazorProof inspected **8 pinned official repositories** and produced **23 evidence-backed observations**: **17 direct defects**, **2 conditional compatibility defects**, and **4 non-bug safety, hardening, or documentation gaps**. It dynamically reproduced **12 independently discovered observations** and links **7 prior public reports** without treating an open issue or pull request as maintainer confirmation.

- Evidence levels: `confirmed_dynamic`=14, `confirmed_static`=4, `known_public`=5
- Claim types: `compatibility_defect`=2, `defect`=17, `documentation_defect`=1, `hardening`=2, `safety_gap`=1
- Severity: `critical`=1, `high`=8, `low`=5, `medium`=9
- Scan window: `2026-09-03T11:03:09.252487+00:00` to `2026-09-03T11:04:26.963271+00:00`
- Contract: `contracts/razorpay.json`

The strongest day-zero case is not hypothetical: the official MCP checkout generator emits binary-float conversion code into new merchant backends. On the executable ₹2.01 counterexample, Python, Ruby and PHP each produced **200 paise instead of 201**. Static matches show the same truncating construction in Go, Java, Rust and .NET templates. The same generator hardcodes a two-decimal exponent for arbitrary currencies: its exact Node expression maps JPY 295 to 29,500 subunits and KWD 295.990 to 29,599 instead of 295,990. Razorpay Test Orders persisted the wrong generated integers because they are valid provider inputs.

The broader failure mode is semantic drift across generated code, provider contracts, SDK state, and wire bytes. Three official SDKs were dynamically shown to leak credentials or partner-routing headers across client instances; four generated mobile success paths discard the signature required by their generated verifier; and the Java document serializer emits the wrong MIME type plus two conflicting `file` fields. These are distinct defects, but RazorProof also compiles them into six explicit failure chains without presenting an unexecuted production consequence as fact.

## Reproducibility boundary

- `confirmed_dynamic` means this run executed the official SDK/handler or the exact emitted expression and observed the counterexample.
- `confirmed_static` means the violation is directly present in pinned official source, but this run did not execute that path.
- `known_public` means a public issue or pull request exists. It is corroboration, not proof of maintainer acceptance and not claimed originality.
- `hardening`, `safety_gap`, and `documentation_defect` are deliberately not represented as runtime product bugs.
- No Live Mode transaction was attempted. Test Mode E2E used a user-owned account; credentials, raw webhook payloads, contact data, and provider IDs remain in ignored private files and never enter the evidence bundle.

## Real Razorpay Test Mode evidence

The repository scan is backed by a separate provider-control-plane campaign. It adds one API-level defect beyond the 23 repository observations: `RP-API-REFUND-FRACTIONAL-COERCION`. Razorpay's documented Refund API types `amount` as integer smallest-subunit money, yet a direct JSON request for `100.75` returned HTTP 200, created a 100-subunit refund, emitted signed `refund.created` and `refund.processed` events, and settled in the provider ledger. A smaller-balance negative control rejected the same invalid input, so the finding is precisely an inconsistent fail-open validation path, not a claim that every fractional request succeeds.

- [Campaign summary](../razorpay-test/campaign-summary.md): headline results, adversarial bounds, and the evidence map.
- [Order boundary and generated undercharge](../razorpay-test/order-boundary.md): the official generated `int(2.01 * 100)` submits and persists 200, while the exact control persists 201.
- [Expanded order contract matrix](../razorpay-test/expanded-order-contract-matrix.md): JPY/KWD exponent counterexamples, duplicate-receipt behavior, and integer-only Orders/Payment Link controls.
- [Refund identity matrix](../razorpay-test/refund-identity-matrix.md): header conflict rejection, receipt duplicate prevention, two distinct unkeyed effects, and the fractional 100.75 to 100 coercion.
- [Final redacted refund ledger](../razorpay-test/refund-ledger.md): all six refunds processed and the 801-subunit payment reached fully refunded with exact ledger equality.
- [Literal UTF-8 webhook proof](../razorpay-test/webhook-byte-evidence.md): 22 signed deliveries across six event types; all signatures valid; all 16 literal-non-ASCII deliveries fail the .NET ASCII-equivalent digest.
- [Negative control](../razorpay-test/refund-fractional-dust.md): the 101-subunit remainder rejected 100.75, disproving the stronger stranded-dust hypothesis and bounding the defect.
- [Chained-bug evidence](../chains/chained-bug-evidence.md): six compositional failures with every inferred consequence labelled.
- [Disclosure ledger](../disclosure/tracker-ledger.md): public correctness issues and private security routing kept separate.

## Findings

### RP-DOTNET-GCM-NONCE-REUSE: .NET onboarding signatures reuse an AES-GCM nonce derived from the secret key

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `critical`; confidence: `100%`
- Originality: independently discovered and executed against the official SDK
- Surface: `razorpay-dot-net` / Utils.GenerateOnboardingSignature
- Invariant: AES-GCM uses a fresh unique nonce for every encryption under a key.
- Assessment: Two official SDK calls with identical input and key returned identical ciphertext.
- Impact: Nonce reuse breaks AES-GCM confidentiality and authentication guarantees; repeated onboarding signatures become deterministic and related plaintexts leak keystream relations.
- Counterexample: `{"client_a_signature_accepted_after_b": false, "client_a_signature_error": "SignatureVerificationError: Invalid signature passed", "client_b_inherited_a_header": true, "first_prefix": "19607e8e4c0d48fb606b168a", "gcm_same": true, "key_after_b": "merchant_B", "key_before_b": "merchant_A", "unicode_accepted": false, "unicode_error": "SignatureVerificationError: Invalid signature passed"}`
- Fix direction: Generate 12 random bytes per call and return nonce || ciphertext || 16-byte tag, matching the other current SDKs.

Evidence:

- `official_source` IV is deterministically copied from the key ([razorpay-dot-net/src/Utils.cs:104](https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/Utils.cs)) — Array.Copy(keyBytes, 0, iv, 0, 12)
- `cross_sdk_release` Ruby release documents the same nonce-reuse defect and fixed wire format ([cross_sdk_release](https://github.com/razorpay/razorpay-ruby/releases/tag/v3.2.4))
- `executed_official_sdk` Official .NET SDK runtime probe (razorpay-dot-net/src/Utils.cs) — {"client_a_signature_accepted_after_b": false, "client_a_signature_error": "SignatureVerificationError: Invalid signature passed", "client_b_inherited_a_header": true, "first_prefix": "19607e8e4c0d48fb606b168a", "gcm_same": true, "key_after_b": "merchant_B", "key_before_b": "merchant_A", "unicode_accepted": false, "unicode_error": "SignatureVerificationError: Invalid signature passed"}

### RP-DOTNET-GLOBAL-AUTH-STATE: .NET client instances overwrite one process-wide credential and routing context

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `high`; confidence: `100%`
- Originality: independently discovered and reproduced against the pinned official SDK
- Surface: `razorpay-dot-net` / RazorpayClient, RestClient, and payment signature verification
- Invariant: Credentials, base URL, access token, and request headers are scoped to one client instance and cannot be changed by constructing another client.
- Assessment: The official SDK probe initialized client A, added A's partner header, then initialized B. The global key changed to B, B inherited A's header, and A's valid payment signature failed because verification used B's secret.
- Impact: A multi-tenant or multi-account .NET process can authenticate client A's request as client B, route it with another account's X-Razorpay-Account header, or reject A's valid payment signature after B is initialized.
- Counterexample: `{"client_a_signature_accepted_after_b": false, "client_a_signature_error": "SignatureVerificationError: Invalid signature passed", "client_b_inherited_a_header": true, "first_prefix": "19607e8e4c0d48fb606b168a", "gcm_same": true, "key_after_b": "merchant_B", "key_before_b": "merchant_A", "unicode_accepted": false, "unicode_error": "SignatureVerificationError: Invalid signature passed"}`
- Fix direction: Make all authentication, endpoint, header, and utility state immutable instance fields; bind resource clients and verification calls to an explicit client or secret.

Evidence:

- `official_source` API key is process-global ([razorpay-dot-net/src/RazorpayClient.cs:15](https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/RazorpayClient.cs)) — private static string key = null;
- `official_source` API secret is process-global ([razorpay-dot-net/src/RazorpayClient.cs:16](https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/RazorpayClient.cs)) — private static string secret = null;
- `official_source` Partner routing and custom headers are process-global ([razorpay-dot-net/src/RazorpayClient.cs:13](https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/RazorpayClient.cs)) — protected static Dictionary<string, string> headers
- `official_source` Every request reads current global credentials ([razorpay-dot-net/src/RestClient.cs:105](https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/RestClient.cs)) — string authString = string.Format("{0}:{1}", RazorpayClient.Key, RazorpayClient.Secret);
- `official_source` Payment verification reads the current global secret ([razorpay-dot-net/src/Utils.cs:23](https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/Utils.cs)) — string secret = RazorpayClient.Secret;
- `executed_official_sdk` Two-client official .NET SDK probe crossed credential, header, and verifier state (razorpay-dot-net/src/RazorpayClient.cs) — {"client_a_signature_accepted_after_b": false, "client_a_signature_error": "SignatureVerificationError: Invalid signature passed", "client_b_inherited_a_header": true, "first_prefix": "19607e8e4c0d48fb606b168a", "gcm_same": true, "key_after_b": "merchant_B", "key_before_b": "merchant_A", "unicode_accepted": false, "unicode_error": "SignatureVerificationError: Invalid signature passed"}

### RP-JAVA-GLOBAL-PARTNER-HEADERS: Java clients share one process-wide partner-routing header map

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `high`; confidence: `100%`
- Originality: independently discovered and reproduced against the pinned official SDK
- Surface: `razorpay-java` / RazorpayClient.addHeaders and ApiUtils.createRequest
- Invariant: X-Razorpay-Account and custom headers are scoped to the intended client or request.
- Assessment: Client B inherited client A's X-Razorpay-Account before B set any header; B then overwrote the single map for the whole process.
- Impact: In an aggregator process, setting X-Razorpay-Account for one sub-merchant can silently route later requests from every other client to that same sub-merchant.
- Counterexample: `{"client_b_inherited_a_header": true, "file_parts": 2, "global_header_after_b": "account_B", "png_media_type": "image/pdf"}`
- Fix direction: Store immutable default headers per RazorpayClient/resource and support per-request overrides; never use a mutable static routing map.

Evidence:

- `official_source` All Java client instances share one header map ([razorpay-java/src/main/java/com/razorpay/ApiUtils.java:33](https://github.com/razorpay/razorpay-java/blob/ad9ab7b6e6f045b782dfd7608da04de9f930ad97/src/main/java/com/razorpay/ApiUtils.java)) — private static Map<String, String> headers
- `official_source` Instance method writes the global header map ([razorpay-java/src/main/java/com/razorpay/RazorpayClient.java:81](https://github.com/razorpay/razorpay-java/blob/ad9ab7b6e6f045b782dfd7608da04de9f930ad97/src/main/java/com/razorpay/RazorpayClient.java)) — ApiUtils.addHeaders(headers);
- `official_source` Every request reads the global header map ([razorpay-java/src/main/java/com/razorpay/ApiUtils.java:198](https://github.com/razorpay/razorpay-java/blob/ad9ab7b6e6f045b782dfd7608da04de9f930ad97/src/main/java/com/razorpay/ApiUtils.java)) — for (Map.Entry<String, String> header : headers.entrySet())
- `provider_contract` Razorpay uses X-Razorpay-Account to select the sub-merchant for partner API calls ([provider_contract](https://razorpay.com/docs/partners/aggregators/partner-auth/?preferred-country=IN))
- `executed_official_sdk` Official Java SDK multipart and multi-client runtime probe (razorpay-java/src/main/java/com/razorpay/ApiUtils.java) — {"client_b_inherited_a_header": true, "file_parts": 2, "global_header_after_b": "account_B", "png_media_type": "image/pdf"}

### RP-MCP-GENERATOR-CURRENCY-EXPONENT: Checkout generator applies a two-decimal multiplier to zero- and three-decimal currencies

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `high`; confidence: `100%`
- Originality: independently discovered and reproduced with the exact generated Node expression
- Surface: `razorpay-mcp-server` / integrate_razorpay_checkout generated backend code
- Invariant: Major-to-minor conversion uses the exponent of the selected currency, not a hardcoded factor of 100.
- Assessment: Executing the generator's currency-agnostic Math.round(amount * 100) produced a 100× JPY overcharge and roughly 10× KWD undercharge relative to Razorpay's documented subunits.
- Impact: Generated merchants can charge JPY orders at 100 times the intended value and KWD/BHD/OMR orders at roughly one tenth of the intended value. The Test API accepts and persists both wrong integer amounts because they are valid provider inputs.
- Counterexample: `{"jpy_exact": 295, "jpy_generated": 29500, "kwd_exact": 295990, "kwd_generated": 29599}`
- Fix direction: Accept integer currency subunits, or use an authoritative currency exponent table plus exact decimal parsing and the documented third-decimal-zero rule.

Evidence:

- `official_source` Generated endpoint accepts arbitrary currency with a major-unit amount ([razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go:30](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_node.go)) — const { amount, currency = 'INR', receipt } = req.body;
- `official_source` Generated endpoint always applies the INR-style ×100 conversion ([razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go:37](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_node.go)) — amount: Math.round(amount * 100)
- `provider_contract` Razorpay documents integer subunits with JPY exponent 0 and KWD/BHD/OMR exponent 3 ([provider_contract](https://razorpay.com/docs/payments/server-integration/nodejs/integration-steps/?preferred-country=IN))
- `executed_emitted_expression` Hardcoded ×100 violates documented JPY and KWD exponent examples (razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go) — {"jpy_exact": 295, "jpy_generated": 29500, "kwd_exact": 295990, "kwd_generated": 29599}

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

### RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS: Checkout generator treats browser price and cart state as the merchant's authoritative order

- Claim type: `defect`; evidence: `confirmed_static`; severity: `high`; confidence: `100%`
- Originality: independently discovered; no matching public issue or pull request found
- Surface: `razorpay-mcp-server` / generated order creation, verification, and checkout wiring
- Invariant: A successful payment is bound server-side to one authoritative merchant quote containing amount, currency, and cart identity.
- Assessment: The generated frontend sends amount from browser state, the backend creates an order directly from that amount/currency, and the verify route checks only the browser-returned Razorpay tuple. The wiring instructions preserve the cart in localStorage rather than creating an authoritative server quote.
- Impact: A buyer can lower the browser-supplied amount, obtain and pay a valid low-value Razorpay order, and still receive a cryptographically valid success response that is not bound to the intended cart or price. Replaying a previously valid tuple is also not rejected by the generated verifier.
- Counterexample: `Tamper checkout total to 1.00, pay the resulting valid order, then present its valid order_id|payment_id signature beside the untouched high-value localStorage cart.`
- Fix direction: Create an immutable server-side quote from trusted SKU/pricing data, store its Razorpay order ID, and consume the paid tuple exactly once only after matching order, amount, currency, merchant, and fulfillment state.

Evidence:

- `official_source` Generated browser sends the price to the order endpoint ([razorpay-mcp-server/pkg/razorpay/integrations/frontend_templates.go:44](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/frontend_templates.go)) — body: JSON.stringify({ amount })
- `official_source` Generated backend trusts browser amount and currency ([razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go:30](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_node.go)) — const { amount, currency = 'INR', receipt } = req.body;
- `official_source` Verifier authenticates only the submitted Razorpay tuple ([razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go:66](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_node.go)) — .update(razorpay_order_id + '|' + razorpay_payment_id)
- `official_source` Generator directs the agent to keep pending order state in browser storage ([razorpay-mcp-server/pkg/razorpay/integrations/helpers.go:177](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/helpers.go)) — localStorage.setItem('pendingOrder', JSON.stringify(pendingOrder));
- `provider_contract` Razorpay says the server-created order ties the payment and secures the request from tampering ([provider_contract](https://razorpay.com/docs/payments/server-integration/nodejs/integration-steps/?preferred-country=IN))

### RP-MCP-MOBILE-DEPENDENCY-CONFUSION: Mobile generator installs nonexistent or unrelated packages instead of Razorpay's official Cordova SDK

- Claim type: `defect`; evidence: `confirmed_static`; severity: `high`; confidence: `100%`
- Originality: independently discovered; no matching public issue or pull request found
- Surface: `razorpay-mcp-server` / Cordova, Ionic, and Capacitor dependency instructions
- Invariant: Generated payment integrations install a currently published dependency controlled by Razorpay's verified package identity.
- Assessment: Cordova and Ionic emit a package name that is absent from npm. Capacitor instructs npm to install cordova-plugin-razorpay, currently an 'Empty package' maintained by a non-Razorpay account, while Razorpay's official package is com.razorpay.cordova.
- Impact: Two generated integrations fail at installation. The Capacitor path crosses a package-identity boundary and can make developers install code from a third party under a payment-SDK-like name.
- Counterexample: `npm view com.nicholaswilliams.nicepay.razorpay returns E404; npm metadata identifies cordova-plugin-razorpay as an empty non-Razorpay package.`
- Fix direction: Emit only the official com.razorpay.cordova package and supported installation instructions, pin an intentional version range, and add registry owner/repository conformance checks in CI.

Evidence:

- `official_source` Cordova and Ionic install a package absent from npm ([razorpay-mcp-server/pkg/razorpay/integrations/mobile.go:843](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/mobile.go)) — cordova plugin add com.nicholaswilliams.nicepay.razorpay
- `official_source` Capacitor installs a similarly named non-Razorpay package ([razorpay-mcp-server/pkg/razorpay/integrations/mobile.go:1222](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/mobile.go)) — npm install cordova-plugin-razorpay
- `official_registry_identity` Razorpay's official Cordova package is com.razorpay.cordova ([official_registry_identity](https://www.npmjs.com/package/com.razorpay.cordova))
- `registry_identity` cordova-plugin-razorpay is described as an empty package and is not maintained by Razorpay ([registry_identity](https://www.npmjs.com/package/cordova-plugin-razorpay))

### RP-MCP-MOBILE-MISSING-SIGNATURE: Generated Android, iOS, Cordova, and native Capacitor success paths discard the payment signature

- Claim type: `defect`; evidence: `confirmed_static`; severity: `high`; confidence: `100%`
- Originality: independently discovered; no matching public issue or pull request found
- Surface: `razorpay-mcp-server` / integrate_razorpay_checkout mobile code generation
- Invariant: A generated Orders API flow preserves order_id, payment_id, and razorpay_signature from Checkout through mandatory server verification.
- Assessment: Android uses PaymentResultListener, which returns only payment_id, and sends an empty signature. iOS likewise chooses the no-data completion protocol and sends an empty signature. Cordova and native Capacitor use a legacy payment_id-only callback and omit the signature.
- Impact: A customer can successfully pay, after which the generated backend must reject the success callback because a mandatory verification field is absent. The merchant sees a paid-but-failed checkout and risks duplicate fulfillment recovery, support incidents, or refund churn.
- Counterexample: `The generated Android and iOS request bodies contain razorpay_signature="" on every successful payment.`
- Fix direction: Use PaymentResultWithDataListener and RazorpayPaymentCompletionProtocolWithData, and use the official Cordova payment.success event/object so all three signed fields reach the backend.

Evidence:

- `official_source` Generated Android verification request always sends an empty signature ([razorpay-mcp-server/pkg/razorpay/integrations/mobile.go:407](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/mobile.go)) — put("razorpay_signature", "")
- `official_source` Generated iOS verification request always sends an empty signature ([razorpay-mcp-server/pkg/razorpay/integrations/mobile.go:623](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/mobile.go)) — "razorpay_signature": ""
- `official_source` Generated native Capacitor request omits razorpay_signature ([razorpay-mcp-server/pkg/razorpay/integrations/mobile.go:785](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/mobile.go)) — razorpay_payment_id: payment_id
- `provider_contract` Android PaymentResultListener returns only payment_id; WithData is required for order_id and signature ([provider_contract](https://razorpay.com/docs/payments/payment-gateway/android-integration/standard/integration-steps/?preferred-country=IN))
- `official_sdk_contract` Official Cordova Orders flow uses payment.success data containing order ID and signature ([official_sdk_contract](https://github.com/razorpay/razorpay-cordova#orders-api-flow))

### RP-PHP-GLOBAL-AUTH-STATE: PHP client instances share and overwrite process-wide credentials and headers

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `high`; confidence: `100%`
- Originality: independently discovered and reproduced against the pinned official SDK
- Surface: `razorpay-php` / Api and Request authentication state
- Invariant: Each SDK client owns immutable credentials, base URL, token, and headers for its requests.
- Assessment: Constructing client B replaced the key visible to client A's process, while client B inherited the partner-routing header set through client A.
- Impact: Long-running PHP workers serving multiple merchants can send one merchant's operation under another merchant's credentials or partner routing header, crossing account and tenant boundaries.
- Counterexample: `{"a_key_before_b": "merchant_A", "b_inherits_a_partner_header": true, "global_key_after_b": "merchant_B"}`
- Fix direction: Move authentication, base URL, app details, and headers to instance-owned request clients, and inject that request client into every resource.

Evidence:

- `official_source` API key is process-global ([razorpay-php/src/Api.php:9](https://github.com/razorpay/razorpay-php/blob/5db430659870e4232040142c6be2820971170fce/src/Api.php)) — protected static $key = null;
- `official_source` Each constructor overwrites the process-global key ([razorpay-php/src/Api.php:29](https://github.com/razorpay/razorpay-php/blob/5db430659870e4232040142c6be2820971170fce/src/Api.php)) — self::$key = $key;
- `official_source` Resources are created without an owning client context ([razorpay-php/src/Api.php:70](https://github.com/razorpay/razorpay-php/blob/5db430659870e4232040142c6be2820971170fce/src/Api.php)) — $entity = new $className();
- `official_source` Requests resolve the latest global credentials at call time ([razorpay-php/src/Request.php:69](https://github.com/razorpay/razorpay-php/blob/5db430659870e4232040142c6be2820971170fce/src/Request.php)) — $options['auth'] = array(Api::getKey(), Api::getSecret());
- `official_source` Request headers are process-global ([razorpay-php/src/Request.php:35](https://github.com/razorpay/razorpay-php/blob/5db430659870e4232040142c6be2820971170fce/src/Request.php)) — protected static $headers = array(
- `executed_official_sdk` Two official Api instances demonstrably share credentials and partner headers (razorpay-php/src/Api.php) — {"a_key_before_b": "merchant_A", "b_inherits_a_partner_header": true, "global_key_after_b": "merchant_B"}

### RP-DOTNET-WEBHOOK-ASCII: .NET webhook verifier hashes non-ASCII strings as ASCII

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `medium`; confidence: `100%`
- Originality: independently discovered and executed against the official SDK
- Surface: `razorpay-dot-net` / Utils.verifyWebhookSignature
- Invariant: HMAC input is the exact UTF-8 request body, byte for byte.
- Assessment: A correct UTF-8 HMAC for a JSON payload containing ₹ and Malayalam text was rejected by the official SDK.
- Impact: A correct UTF-8 signature is rejected for ordinary Razorpay Test Mode payment-link and refund deliveries containing literal non-ASCII metadata.
- Counterexample: `{"client_a_signature_accepted_after_b": false, "client_a_signature_error": "SignatureVerificationError: Invalid signature passed", "client_b_inherited_a_header": true, "first_prefix": "19607e8e4c0d48fb606b168a", "gcm_same": true, "key_after_b": "merchant_B", "key_before_b": "merchant_A", "unicode_accepted": false, "unicode_error": "SignatureVerificationError: Invalid signature passed"}`
- Fix direction: Expose a byte[] webhook API and use UTF-8 explicitly for string compatibility overloads.

Evidence:

- `official_source` All signature strings are encoded as ASCII ([razorpay-dot-net/src/Utils.cs:135](https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/Utils.cs)) — new ASCIIEncoding()
- `executed_official_sdk` Official .NET SDK runtime probe (razorpay-dot-net/src/Utils.cs) — {"client_a_signature_accepted_after_b": false, "client_a_signature_error": "SignatureVerificationError: Invalid signature passed", "client_b_inherited_a_header": true, "first_prefix": "19607e8e4c0d48fb606b168a", "gcm_same": true, "key_after_b": "merchant_B", "key_before_b": "merchant_A", "unicode_accepted": false, "unicode_error": "SignatureVerificationError: Invalid signature passed"}

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

### RP-JAVA-UPLOAD-DUPLICATE-FILE-PART: Java document upload serializes the file field twice with conflicting types

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `medium`; confidence: `100%`
- Originality: independently discovered and reproduced against the pinned official SDK wire body
- Surface: `razorpay-java` / ApiUtils.fileRequestBody
- Invariant: The singular document file field appears exactly once as a binary multipart part.
- Assessment: Serializing one upload object produced two multipart parts named file: one binary and one text pathname.
- Impact: Servers and intermediaries can select the wrong duplicate field, reject the request, or treat a local pathname as the uploaded file value.
- Counterexample: `{"client_b_inherited_a_header": true, "file_parts": 2, "global_header_after_b": "account_B", "png_media_type": "image/pdf"}`
- Fix direction: Remove file from the ordinary field loop and serialize it exactly once as the binary part; add a wire-format cardinality test.

Evidence:

- `official_source` SDK adds the binary file part ([razorpay-java/src/main/java/com/razorpay/ApiUtils.java:256](https://github.com/razorpay/razorpay-java/blob/ad9ab7b6e6f045b782dfd7608da04de9f930ad97/src/main/java/com/razorpay/ApiUtils.java)) — multipartBodyBuilder.addFormDataPart("file",fileName, fileBody);
- `official_source` SDK then iterates all fields including file ([razorpay-java/src/main/java/com/razorpay/ApiUtils.java:258](https://github.com/razorpay/razorpay-java/blob/ad9ab7b6e6f045b782dfd7608da04de9f930ad97/src/main/java/com/razorpay/ApiUtils.java)) — Iterator<?> iterator = requestObject.keys();
- `official_source` SDK adds file path again as a text part ([razorpay-java/src/main/java/com/razorpay/ApiUtils.java:262](https://github.com/razorpay/razorpay-java/blob/ad9ab7b6e6f045b782dfd7608da04de9f930ad97/src/main/java/com/razorpay/ApiUtils.java)) — multipartBodyBuilder.addFormDataPart((String) key, (String) value);
- `executed_official_sdk` Official Java SDK multipart and multi-client runtime probe (razorpay-java/src/main/java/com/razorpay/ApiUtils.java) — {"client_b_inherited_a_header": true, "file_parts": 2, "global_header_after_b": "account_B", "png_media_type": "image/pdf"}

### RP-JAVA-UPLOAD-MIME: Java document uploads mislabel runtime JPG and PNG paths as PDF

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `medium`; confidence: `100%`
- Originality: independently discovered and reproduced against the pinned official SDK
- Surface: `razorpay-java` / ApiUtils.getMediaType
- Invariant: Multipart file MIME type matches the selected file format.
- Assessment: The official private serializer classified a runtime proof.png path as image/pdf.
- Impact: Valid evidence and KYC image uploads can be rejected, misclassified, or processed through the wrong media path.
- Counterexample: `{"client_b_inherited_a_header": true, "file_parts": 2, "global_header_after_b": "account_B", "png_media_type": "image/pdf"}`
- Fix direction: Use equalsIgnoreCase, map each supported extension to its documented MIME type, reject unknown extensions, and preferably inspect trusted content metadata.

Evidence:

- `official_source` Runtime strings are compared with reference equality and non-short-circuit OR ([razorpay-java/src/main/java/com/razorpay/ApiUtils.java:242](https://github.com/razorpay/razorpay-java/blob/ad9ab7b6e6f045b782dfd7608da04de9f930ad97/src/main/java/com/razorpay/ApiUtils.java)) — if(extenionName == "jpg" | extenionName == "jpeg" | extenionName == "png" | extenionName == "jfif")
- `official_source` All failed image comparisons fall through to image/pdf ([razorpay-java/src/main/java/com/razorpay/ApiUtils.java:245](https://github.com/razorpay/razorpay-java/blob/ad9ab7b6e6f045b782dfd7608da04de9f930ad97/src/main/java/com/razorpay/ApiUtils.java)) — return "image/pdf";
- `provider_contract` Document API documents image/jpg, image/jpeg, image/png, and application/pdf ([provider_contract](https://razorpay.com/docs/api/documents/create/?preferred-country=IN))
- `executed_official_sdk` Official Java SDK multipart and multi-client runtime probe (razorpay-java/src/main/java/com/razorpay/ApiUtils.java) — {"client_b_inherited_a_header": true, "file_parts": 2, "global_header_after_b": "account_B", "png_media_type": "image/pdf"}

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
logs are stored in: /tmp/go-build3168719750/b001/logs
    razorproof_fractional_test.go:33: fractional money crossed the MCP boundary: requested=100.75 sent=100
--- FAIL: TestRazorProofFractionalRefundMustFailClosed (0.00s)
FAIL
FAIL	github.com/razorpay/razorpay-mcp-server/pkg/razorpay	0.004s
FAIL
go: downloading github.com/go-test/deep v1.1.1
go: downloading github.com/razorpay/razorpay-go v1.4.0
go: downloading github.com/stretchr/testify v1.10.0
go: downloading github.com/mark3labs/mcp-go v0.43.2
go: downloading github.com/gorilla/mux v1.8.1
go: downloading gopkg.in/yaml.v3 v3.0.1
go: downloading github.com/davecgh/go-spew v1.1.1
go: downloading github.com/pmezard/go-difflib v1.0.0
go: downloading github.com/yosida95/uritemplate/v3 v3.0.2
go: downloading github.com/spf13/cast v1.7.1
go: downloading github.com/invopop/jsonschema v0.13.0
go: downloading github.com/google/uuid v1.6.0
go: downloading github.com/wk8/go-ordered-map/v2 v2.1.8
go: downloading github.com/mailru/easyjson v0.7.7
go: downloading github.com/bahlo/generic-list-go v0.2.0
go: downloading github.com/buger/jsonparser v1.1.1


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

- Claim type: `hardening`; evidence: `known_public`; severity: `low`; confidence: `98%`
- Originality: publicly proposed hardening and independently source-confirmed; no practical remote exploit reproduced
- Surface: `razorpay-dot-net` / Utils.verifySignature
- Invariant: Authentication tags are compared in constant time.
- Assessment: The verifier uses String.Equals rather than a fixed-time byte comparison.
- Impact: Ordinary equality is functionally correct. A fixed-time comparison reduces timing leakage, but practical remote exploitability was not reproduced or claimed.
- Fix direction: Decode hex and call CryptographicOperations.FixedTimeEquals.
- Prior public reference: [https://github.com/razorpay/razorpay-dot-net/pull/153](https://github.com/razorpay/razorpay-dot-net/pull/153)

Evidence:

- `official_source` Non-constant-time comparison ([razorpay-dot-net/src/Utils.cs:72](https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/Utils.cs)) — actualSignature.Equals(expectedSignature)

### RP-MCP-GENERATOR-SIGNATURE-LENGTH-500: Generated Node verifier turns malformed signature lengths into HTTP 500

- Claim type: `defect`; evidence: `confirmed_dynamic`; severity: `low`; confidence: `100%`
- Originality: independently discovered and reproduced with the exact generated comparison operation
- Surface: `razorpay-mcp-server` / generated Express payment verification route
- Invariant: Untrusted malformed authentication input fails closed as a controlled client error.
- Assessment: The generated timingSafeEqual call throws Node's length exception for an untrusted one-byte signature, and the generated route catches it as HTTP 500.
- Impact: Any unauthenticated caller can create noisy server errors and false operational alarms on the public verify endpoint.
- Counterexample: `{"accepted": false, "error_code": "ERR_CRYPTO_TIMING_SAFE_EQUAL_LENGTH", "error_name": "RangeError"}`
- Fix direction: Strictly decode a 64-character lowercase/uppercase hexadecimal signature, reject invalid length/encoding with 400, then compare equal-length bytes.

Evidence:

- `official_source` Generated verifier compares buffers without validating length or hex encoding ([razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go:69](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_node.go)) — crypto.timingSafeEqual(Buffer.from(expectedSignature), Buffer.from(razorpay_signature))
- `official_source` Catch block maps the thrown malformed-input path to HTTP 500 ([razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go:81](https://github.com/razorpay/razorpay-mcp-server/blob/7950d51d118ca164c32b7cf0cfaa14f34f24849f/pkg/razorpay/integrations/backend_node.go)) — res.status(500).json({ success: false, error: 'Payment verification failed' });
- `executed_emitted_expression` Node throws on the generated unequal-length comparison (razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go) — {"accepted": false, "error_code": "ERR_CRYPTO_TIMING_SAFE_EQUAL_LENGTH", "error_name": "RangeError"}

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
