# RazorProof maximum-density master script

This is the uncut source script. It deliberately contains more material than a five-minute edit can hold. Preserve the argument and select lines during editing; do not weaken precise evidence language merely to make a shorter claim.

## Evidence language used on screen

- **DYNAMICALLY REPRODUCED:** official SDK code, an official handler, or the exact generated expression executed and produced the counterexample.
- **STATICALLY CONFIRMED:** the pinned source directly contains the contract violation, but that path was not executed end to end.
- **TEST MODE OBSERVED:** a redacted effect was observed in the user-owned Razorpay Test environment.
- **KNOWN PUBLIC:** a public issue or pull request corroborates the concern; this is not maintainer acceptance.
- **INFERRED IMPACT:** the consequence follows from proven components but was intentionally not executed.
- **PREVENTED:** RazorProof enforces a control for traffic crossing its boundary.
- **STRUCTURALLY AVOIDED:** RazorProof does not invoke the affected SDK implementation.
- **DETECTION ONLY:** RazorProof reports the defect but does not yet replace the affected client path.

---

## Prologue — A transaction can be valid and still be wrong

**[Black screen. One restrained payment-success tone. A green status appears: `PAYMENT CAPTURED`.]**

> The most dangerous payment failure is not always a declined card. Sometimes the order exists. The signature verifies. The API returns success. The ledger is internally consistent. And the transaction is still wrong.

**[Three green checks appear: `ORDER`, `SIGNATURE`, `STATUS`. A fourth field appears in vermilion: `INTENT`.]**

> We found exactly that while stress-testing the code emitted by an official Razorpay AI integration generator. We entered two rupees and one paisa. The generated Python, Ruby, and PHP conversion paths sent two hundred paise instead of two hundred and one.

**[Camera. Hold the notebook page: `₹2.01 → 200 paise`.]**

> But one paisa is not the story. One paisa is the smallest counterexample that proves the system has lost the merchant's economic intent. If the same mistake scales across currencies, retries, tenants, callbacks, and fulfillment, a green payment result can certify the wrong thing with complete cryptographic confidence.

**[Manim: `₹2.01 → ₹2.00` shrinks to the corner. `JPY 295 → JPY 29,500` fills the frame. Then `KWD 295.990 → KWD 29.599`.]**

> So we changed the currency. Two hundred and ninety-five yen became twenty-nine thousand five hundred yen: a hundred-times overcharge. Two hundred and ninety-five Kuwaiti dinar became twenty-nine dinar and five hundred ninety-nine fils: roughly a ten-times undercharge. Razorpay Test Mode accepted and persisted those wrong values because they were valid integers. The API could validate their shape. It had no way to know what the merchant meant.

> That question became RazorProof: can we prove not only that a payment happened, but that the right financial intent happened, under the right merchant, for the right amount, exactly once?

---

## Chapter 1 — How we investigated

**[Fast but readable source montage: eight repository names and their pinned commit hashes.]**

> We cloned eight official repositories: the Razorpay MCP server and the official Python, Java, Node, Go, .NET, PHP, and Ruby SDKs. Every observation was tied to a pinned commit. We started from payment invariants, not generic code smells.

**[Notebook. Write each invariant as a separate line.]**

> Money in provider subunits must be an exact integer. Currency exponent is a property of the currency, not a universal constant. Credentials and partner routing belong to one client and one tenant. HMAC authenticates the exact bytes received. An authenticated callback must preserve every field in its protocol-defined order. A retryable financial action needs a stable effect identity. A document upload contains one real file with one correct media type. A customer-facing success path cannot discard the data required by server verification.

**[Screen recording: static evidence line, then container probe, then Test Mode receipt.]**

> For every candidate, RazorProof looked for a counterexample. Static source established the suspect operation. Runtime probes executed official SDK code in clean work copies and disposable language containers. Local capture servers inspected the exact outgoing HTTP or multipart bytes. Test Mode was used only where provider behavior mattered. Public issues were treated as corroboration, never as proof of maintainer acceptance. Consequences we did not execute remained labelled inference.

> The result was twenty-three findings: seventeen direct defects, two compatibility defects, one safety gap, two hardening findings, and one documentation defect. Fourteen were dynamically reproduced. Four were statically confirmed. Five had known-public corroboration. The scanner found zero probe errors in the complete container run.

---

## Chapter 2 — Case files: money, price, and effect identity

### Case 1 — Binary floating-point undercharge

**[Source macro: `int(amount * 100)`, `(amount * 100).to_i`, `(int)(amount * 100)`.]**

> The checkout generator emits binary floating-point money followed by truncation across multiple backend language templates. In binary, two point zero one multiplied by one hundred can be represented just below two hundred and one. Python `int`, Ruby `to_i`, and PHP integer casts returned two hundred. Node's rounded control returned two hundred and one.

**[Lower third: `RP-MCP-GENERATOR-MONEY-UNDERCHARGE · HIGH · DYNAMICALLY REPRODUCED`.]**

> The defect is not that one language has unusual floating-point behavior. The generator copies the unsafe representation into fresh merchant applications. One source template multiplies the blast radius across languages and projects.

**[Control overlay: `PREVENTED`.]**

> RazorProof prevents this class by accepting integer subunits at the payment boundary and using exact decimal parsing only when converting a human major-unit string. There is no binary floating-point money type in the Rust core.

### Case 2 — Universal two-decimal currency assumption

**[Manim: currency cards with exponent values: `JPY 0`, `INR 2`, `KWD/BHD/OMR 3`.]**

> The generated checkout accepts a caller-selected currency but applies a fixed multiplier of one hundred. That happens to match INR. It does not match zero-decimal yen or three-decimal dinar, Bahraini dinar, and Omani rial. The exact generated expression produced JPY twenty-nine thousand five hundred instead of two hundred ninety-five, and KWD twenty-nine point five nine nine instead of two hundred ninety-five point nine nine zero.

**[Lower third: `RP-MCP-GENERATOR-CURRENCY-EXPONENT · HIGH · DYNAMIC + TEST MODE`.]**

> Both wrong integers were valid provider inputs and were persisted as Test Mode orders. The gateway cannot reconstruct the intended major-unit value after the integration has already converted it incorrectly.

**[Control overlay: `PREVENTED`.]**

> RazorProof applies a currency rule before provider contact: exponent zero for JPY, exponent three with Razorpay's documented quantum for KWD, BHD, and OMR, and exponent two for the enabled two-decimal currencies. Excess precision is rejected rather than rounded into a new economic value.

### Case 3 — The browser authors the economics

**[Split screen: frontend sends `{ amount }`; backend destructures `amount, currency`; verifier hashes only `order_id|payment_id`.]**

> The most consequential checkout finding is not floating point. The generated frontend sends the amount from browser state. The generated backend trusts that amount and currency when creating the order. Pending cart state is placed in local storage. The verification route authenticates the Razorpay order and payment tuple, but does not bind that tuple back to a trusted server-side cart and price.

**[Lower third: `RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS · HIGH · STATICALLY CONFIRMED`.]**

> The counterexample is conceptually simple: alter the browser amount, create and pay the lower-value provider order, then present its valid signature beside the untouched high-value browser cart. The signature can prove the lower-value order was paid. It cannot prove that order represented the merchant's catalog. We did not execute paid fulfillment for this exploit path, so downstream loss remains an explicit inference.

**[Control overlay: `PREVENTED`.]**

> RazorProof moves authority behind an authenticated merchant boundary. It constructs an expiring quote from merchant-server-supplied SKU lines, computes the cart hash and total, creates one provider order from that quote, stores the provider order ID, re-fetches the order and payment, requires captured status, compares both amounts and currencies, verifies the signature against the stored order ID, and allows one fulfillment transition only after every value agrees. The current POC authenticates the quote issuer and enforces the lifecycle; a production deployment must connect quote issuance to the merchant's authoritative catalog and must never expose the gateway credential to a shopper's browser.

### Case 4 — Fractional refund mutation

**[Source: `ValidateAndAddRequiredFloat`; next line: `int(payload["amount"].(float64))`.]**

> Razorpay's MCP refund tool accepts the amount as a floating-point number and later casts it to an integer. We inserted a black-box regression test into a clean copy of the official handler, redirected its SDK to a local HTTP capture server, and submitted one hundred point seven five subunits. The official handler sent one hundred.

**[Lower third: `RP-MCP-REFUND-TRUNCATION · MEDIUM · DYNAMICALLY REPRODUCED`.]**

> The amount did not merely fail validation. It crossed the boundary as a different financial instruction.

**[Test Mode ledger appears.]**

> A separate direct API experiment found a narrower provider-side issue. On a funded eight-rupee-one-paisa fixture, the Refund API accepted JSON amount one hundred point seven five, returned HTTP two hundred, persisted a processed refund of one hundred, and emitted signed refund events. With only one hundred and one subunits remaining on a different fixture, the same input returned HTTP four hundred. The accurate claim is inconsistent fail-open validation, not universal truncation.

**[Control overlay: `PREVENTED BEFORE PROVIDER`.]**

> RazorProof declares every monetary JSON path in its operation policy and rejects non-integer subunits before the request can reach either the MCP handler or Razorpay.

### Case 5 — Refund identity exists, but the tool hides it

**[Manim: response drops after provider commit; client retries; two refund IDs appear.]**

> A money-moving retry needs to answer one question: is this the same intent or a new intent? Razorpay supports stable refund identity through receipt behavior and the `X-Refund-Idempotency` header. The MCP tool does not expose the header and describes receipt only as an internal reference.

**[Lower third: `RP-MCP-REFUND-IDEMPOTENCY · MEDIUM · SAFETY GAP · KNOWN PUBLIC`.]**

> Two unkeyed refund requests creating two refunds is documented behavior, not a Razorpay bug. The safety gap is that an agent-facing tool makes it easy to retry without carrying the identity mechanism that distinguishes one effect from two.

**[Fault lab: first response dropped after commit.]**

> In the fault lab, the server committed the first effect and dropped the response. An unkeyed retry produced two effects. The same experiment with one stable identity produced one. In Test Mode, repeating the same idempotency header and body returned one refund identity; changing the body under that header returned HTTP four hundred nine.

**[Control overlay: `PREVENTED`.]**

> RazorProof requires a caller-owned intent for every write, binds it to the canonical operation and body hash, forwards refund intent through `X-Refund-Idempotency`, returns the stored result for an exact replay, rejects mutation, and freezes ambiguous failures for reconciliation instead of guessing.

---

## Chapter 3 — Case files: merchant isolation and cryptography

### Case 6 — .NET process-wide credentials and routing

**[Two clients labelled A and B. A's key changes to B; A's account header flows into B.]**

> In the .NET SDK, credentials and headers live in process-wide static state. The runtime probe created client A with merchant A, added account A's partner-routing header, then created client B with merchant B. The global key changed from A to B. Client B inherited A's `X-Razorpay-Account` header. A valid payment signature created under A's secret then failed because the verification path read B's secret.

**[Lower third: `RP-DOTNET-GLOBAL-AUTH-STATE · HIGH · DYNAMICALLY REPRODUCED`.]**

> This proves the isolation failure inside the official SDK. We did not send a two-account provider request, so an actual cross-merchant charge remains inferred. But in a long-running multi-merchant process, the state required for that boundary crossing is demonstrably shared.

**[Control overlay: `STRUCTURALLY AVOIDED`.]**

> RazorProof never uses that SDK. Each tenant runtime owns one immutable Rust credential object, one immutable optional partner account, and one provider client. A caller cannot supply or mutate the account-routing header per request.

### Case 7 — PHP process-wide credentials and headers

**[Repeat the A/B visualization with a PHP worker queue behind it.]**

> The PHP SDK reproduced the same class independently. Constructing client B replaced the key visible in the process, while B inherited the partner-routing header previously set through A. That is especially relevant to long-running workers that serve multiple merchants without restarting the process between jobs.

**[Lower third: `RP-PHP-GLOBAL-AUTH-STATE · HIGH · DYNAMICALLY REPRODUCED`.]**

> RazorProof structurally avoids it through tenant-owned immutable clients and explicit authentication at the firewall boundary. Applications that bypass RazorProof and continue using the affected PHP SDK remain outside this protection.

### Case 8 — Java process-wide partner headers

**[One static map in the centre; every Java client points to it.]**

> The Java SDK stores partner headers in one static map. Client B inherited client A's `X-Razorpay-Account` before B set any header, and B then overwrote the same global map with account B. In an aggregator process, the sub-merchant route is therefore not owned by the client that appears to set it.

**[Lower third: `RP-JAVA-GLOBAL-PARTNER-HEADERS · HIGH · DYNAMICALLY REPRODUCED`.]**

> RazorProof binds partner account configuration when the tenant runtime is constructed. It validates the provider account identifier and injects the header from immutable service state, not user payload or a shared global map.

### Case 9 — AES-GCM nonce reuse in .NET onboarding

**[Manim: one key produces the same twelve-byte nonce for several messages. Warning pulse.]**

> This was the most technically severe defect. The .NET onboarding-signature utility derives its twelve-byte AES-GCM nonce by copying bytes from the secret key. AES-GCM requires a unique nonce for every encryption under one key. Deriving it deterministically from the key guarantees reuse.

**[Two calls. Identical plaintext and key produce identical ciphertext.]**

> The official SDK was executed twice with the same key and input. It returned identical ciphertext. The source and runtime result establish deterministic nonce reuse. Reusing a GCM nonce destroys the security assumptions behind confidentiality and authentication and creates keystream relationships between related plaintexts.

**[Lower third: `RP-DOTNET-GCM-NONCE-REUSE · CRITICAL · DYNAMICALLY REPRODUCED`.]**

> RazorProof detects this defect and avoids invoking the .NET utility. It does not patch every installed .NET SDK and it does not yet provide a replacement onboarding-encryption endpoint. The complete upstream fix is a fresh random ninety-six-bit nonce per call, carried alongside ciphertext and tag.

---

## Chapter 4 — Case files: webhooks, callbacks, and signatures

### Case 10 — .NET hashes webhook text as ASCII

**[Raw UTF-8 byte sequence for `₹` and Malayalam; ASCII path replaces bytes.]**

> A webhook signature authenticates bytes, not an abstract JSON object. The .NET SDK converts webhook text with ASCII encoding. We computed a correct HMAC over UTF-8 JSON containing the rupee symbol and Malayalam text. The official SDK rejected it.

**[Real campaign counter: `16 NON-ASCII DELIVERIES · 16 UTF-8 PASS · 16 ASCII FAIL`.]**

> Test Mode closed the reachability question. Of twenty-two signed deliveries across six event types, sixteen contained literal non-ASCII bytes. Exact UTF-8 HMAC verification passed all sixteen. The .NET ASCII-equivalent digest failed all sixteen.

**[Lower third: `RP-DOTNET-WEBHOOK-ASCII · MEDIUM · DYNAMIC + TEST MODE`.]**

> RazorProof terminates the webhook over its untouched request body, verifies HMAC before JSON parsing, fingerprints the event ID, and deduplicates delivery per tenant.

### Case 11 — Python rejects the raw bytes callers are told to preserve

**[Python call receives `bytes`; utility attempts `bytes(body, 'utf-8')`; TypeError.]**

> The Python webhook utility has the opposite compatibility problem. Framework guidance says to preserve the raw request body. But when the caller supplies valid raw bytes, the utility unconditionally invokes the string-to-bytes constructor and throws `TypeError: encoding without a string argument`.

**[Lower third: `RP-PYTHON-WEBHOOK-BYTES · MEDIUM · COMPATIBILITY DEFECT · DYNAMIC`.]**

> RazorProof owns a byte-native webhook boundary, so no decode-and-re-encode round trip exists. Direct users of the Python SDK still need its compatibility fix: preserve bytes and encode only string inputs.

### Case 12 — Java relies on the process default charset

**[Code: secret uses UTF-8; payload uses bare `.getBytes()`.]**

> The Java signature utility explicitly encodes the secret as UTF-8 but encodes the payload with the process default charset. On Java eighteen and newer, UTF-8 is the normal default. On older or explicitly configured environments, identical text can become different bytes and therefore a different HMAC.

**[Lower third: `RP-JAVA-DEFAULT-CHARSET · MEDIUM · COMPATIBILITY DEFECT · KNOWN PUBLIC`.]**

> This is conditional, not universal. RazorProof avoids the ambiguity by accepting raw bytes and using explicit encodings wherever text conversion is unavoidable.

### Case 13 — Ruby signature verification depends on hash insertion order

**[Two Ruby hashes contain identical key/value pairs in different insertion orders.]**

> The Ruby payment-link verifier constructs its signature payload by joining `attributes.values`. That means the caller's hash insertion order becomes part of the protocol. The official SDK accepted a correctly signed hash inserted in documentation order and rejected the identical field set inserted in another order with `SecurityError: Signature verification failed`.

**[Lower third: `RP-RUBY-PAYLINK-ORDER · MEDIUM · DYNAMICALLY REPRODUCED`.]**

> Protocol order should come from named fields, never container history. RazorProof detects this. Its current checkout and webhook verification paths avoid caller-container order, but it does not yet expose a dedicated replacement for every payment-link signature helper. That exact helper remains detection-only unless the integration moves to RazorProof's provider-state and webhook path.

### Case 14 — .NET ordinary string equality for signatures

**[Code: `actualSignature.Equals(expectedSignature)`; badge: `FUNCTIONALLY CORRECT / NOT CONSTANT TIME`.]**

> The .NET verifier compares authentication tags with ordinary string equality. This is functionally correct. A fixed-time comparison is stronger defensive practice, but we did not reproduce a practical remote timing exploit.

**[Lower third: `RP-DOTNET-SIGNATURE-COMPARE · LOW · HARDENING · KNOWN PUBLIC`.]**

> RazorProof strictly decodes fixed-length hexadecimal tags and compares the resulting bytes in constant time.

### Case 15 — Node ordinary string equality for webhook signatures

**[Code: `expectedSignature === signature`; same badge.]**

> The Node SDK uses JavaScript strict equality for webhook HMAC strings. Again, this is a hardening issue, not a claim that signature verification is functionally broken or remotely exploitable.

**[Lower third: `RP-NODE-SIGNATURE-COMPARE · LOW · HARDENING · KNOWN PUBLIC`.]**

> RazorProof applies the same strict-length, strict-hexadecimal, constant-time comparison at its boundary.

### Case 16 — Generated Node verifier turns malformed input into HTTP 500

**[A one-character signature enters `timingSafeEqual`; RangeError exits.]**

> The generated Node payment verifier does call `timingSafeEqual`, but it does so before validating length. Node requires equal-length buffers and throws `ERR_CRYPTO_TIMING_SAFE_EQUAL_LENGTH` for a one-byte attacker-supplied signature. The generated catch block converts that expected malformed-input path into HTTP five hundred.

**[Lower third: `RP-MCP-GENERATOR-SIGNATURE-LENGTH-500 · LOW · DYNAMICALLY REPRODUCED`.]**

> Any unauthenticated caller can manufacture noisy internal-server errors on the public verification route. RazorProof rejects malformed length and encoding as a controlled authentication failure before comparison.

### Case 17 — Python forgets to validate one required payment-link field

**[Input map lacks `payment_link_id`; guard passes; lookup throws KeyError.]**

> The Python payment-link verifier checks an incomplete required-field set, then reads `payment_link_id` unconditionally. A callback-shaped map missing that field passes the guard and crashes with `KeyError` instead of returning a documented authentication rejection.

**[Lower third: `RP-PYTHON-PAYLINK-MISSING-FIELD · LOW · DYNAMICALLY REPRODUCED`.]**

> RazorProof detects the defect. Its typed routes reject missing fields cleanly, but it does not yet offer an exact drop-in replacement for the Python payment-link helper. Direct SDK callers remain outside the firewall.

---

## Chapter 5 — Case files: generated mobile code, wire formats, and interface drift

### Case 18 — Generated mobile success paths discard the signature

**[Four columns: Android, iOS, Cordova, Capacitor. Each success callback loses `razorpay_signature`.]**

> The generated Android code selects `PaymentResultListener`, which returns only a payment ID, then sends an empty signature to the server. The generated iOS code selects the no-data completion protocol and also sends an empty signature. Cordova and native Capacitor use payment-ID-only callback shapes and omit the signature.

**[Lower third: `RP-MCP-MOBILE-MISSING-SIGNATURE · HIGH · STATICALLY CONFIRMED`.]**

> The customer can pay successfully, but the generated backend must reject the callback because mandatory verification data has already been discarded. That creates a paid-but-failed state with support, recovery, duplicate-fulfillment, and refund risk.

**[Control overlay: `PARTIALLY CONTROLLED`.]**

> RazorProof refuses to mark the payment verified or fulfill without the complete signed tuple and matching provider state. That prevents false fulfillment, but it cannot recreate a signature the mobile client discarded. Completing this fix requires RazorProof mobile adapters that use the data-bearing Android and iOS protocols and the official Cordova success object.

### Case 19 — Generated mobile setup crosses package identity boundaries

**[Terminal: one package returns npm E404; another resolves to an empty third-party package; official package shown beside them.]**

> The Cordova and Ionic generator instructions emit `com.nicholaswilliams.nicepay.razorpay`, which was absent from npm. The Capacitor instructions emit `cordova-plugin-razorpay`, which resolved to an empty package outside Razorpay's repository and publisher identity. Razorpay's official package is `com.razorpay.cordova`.

**[Lower third: `RP-MCP-MOBILE-DEPENDENCY-CONFUSION · HIGH · STATIC + REGISTRY OBSERVED`.]**

> Two paths fail installation. The third crosses into an unrelated payment-SDK-like package identity. We found no evidence that the current empty package is malicious, so the supply-chain consequence is a future exposure, not an allegation.

**[Control overlay: `DETECTION ONLY`.]**

> RazorProof currently detects and reports the package mismatch. It does not yet generate mobile projects or enforce a registry-owner allowlist. That is an explicit remaining feature.

### Case 20 — Java labels PNG and JPG uploads as PDF

**[Actual serializer output: filename `proof.png`; Content-Type `image/pdf`.]**

> The Java document helper's media-type logic classified a runtime PNG path as `image/pdf`. The result was reproduced by compiling the official SDK in a container and invoking the actual private serializer.

**[Lower third: `RP-JAVA-UPLOAD-MIME · MEDIUM · DYNAMICALLY REPRODUCED`.]**

> Valid KYC or dispute evidence can be rejected, misclassified, or processed through the wrong media path. RazorProof's document endpoint checks extension against magic bytes, accepts only PDF, PNG, or JPEG, assigns the corresponding MIME, and rejects disagreement.

### Case 21 — Java emits the file twice

**[Wire-level multipart body. Highlight two `name="file"` boundaries.]**

> The same Java serializer emitted two multipart fields named `file`: one binary part and one ordinary text part containing the local pathname. Duplicate multipart fields are ambiguous; servers and intermediaries can reject the request or select the wrong value.

**[Lower third: `RP-JAVA-UPLOAD-DUPLICATE-FILE-PART · MEDIUM · DYNAMICALLY REPRODUCED`.]**

> RazorProof constructs the multipart form itself and emits exactly one binary file part plus the allowed scalar purpose field.

### Case 22 — Repeated expand parameters collapse

**[Input: `expand=[payments, transfers]`; map assignment overwrites; output only `transfers`.]**

> The MCP query builder stores repeated `expand[]` values in a single-value map. Every loop iteration overwrites the same key, so callers requesting payments and transfers receive only the last expansion.

**[Lower third: `RP-MCP-EXPAND-COLLAPSE · MEDIUM · DIRECT DEFECT · KNOWN PUBLIC`.]**

> RazorProof represents each query name as a vector of values and flattens every occurrence without overwriting multiplicity.

### Case 23 — Published payout tool name does not exist

**[README name and registered tool name appear side by side.]**

> The official MCP interface table advertised `fetch_payout_by_id`, while the server registered `fetch_payout_with_id`. An agent following the published interface calls a nonexistent tool.

**[Lower third: `RP-MCP-PAYOUT-NAME-DRIFT · LOW · DOCUMENTATION DEFECT · STATIC`.]**

> RazorProof's versioned operation catalog publishes the current name and preserves the older form as an explicit alias. Its MCP coverage command compares the catalog against production source and fails on future drift.

---

## Chapter 6 — Six bugs become six failure chains

**[Notebook. Individual red evidence cards connect only when every required node is present.]**

> Individual bugs matter. Their composition matters more. RazorProof emits a chain only when every required component finding exists. Executed nodes remain separate from the final consequence.

### Chain 1 — Refund mutation, retry ambiguity, and lost webhook visibility

> First, a fractional refund enters the MCP handler as one hundred point seven five and leaves as one hundred. Second, the provider independently accepts that malformed shape in one funded Test Mode case and persists one hundred. Third, an unkeyed retry is a new refund by design. Fourth, non-ASCII refund webhooks can fail the .NET ASCII verifier. If a merchant interprets the lost or rejected evidence as failure and retries without a stable identity, one intended refund can become multiple uncertain effects. The trigger is inferred; every supporting mechanism was independently demonstrated.

**[RazorProof lane closes each edge.]**

> RazorProof rejects fractional money, requires intent identity, carries refund idempotency, verifies raw webhook bytes, and links request, effect, and event fingerprints.

### Chain 2 — Browser authority plus currency corruption

> The browser authors the price. The backend trusts it. The generator applies binary floating point and a fixed currency exponent. Razorpay correctly signs and persists the resulting provider order. The signature is authentic, but it authenticates a value that was never bound to a trusted cart. RazorProof replaces the entire chain with a server-issued quote and a one-time quote-to-order-to-payment-to-fulfillment state machine.

### Chain 3 — Mobile paid but merchant cannot verify

> The generated mobile client selects a callback that cannot deliver the complete signed tuple. It sends an empty or missing signature. Checkout can report success before the generated backend rejects verification. RazorProof fails closed, which prevents unverified fulfillment, but the complete customer-experience fix requires client adapters that preserve the tuple before it reaches the server.

### Chain 4 — Cross-tenant merchant routing

> .NET shares credentials and headers. PHP shares credentials and headers. Java shares partner-routing headers. Three language ecosystems independently violate the same tenant-isolation invariant. A multi-merchant worker can therefore construct local state in which one request is authenticated or routed using another merchant's context. We proved the collisions but intentionally did not execute the two-account provider consequence. RazorProof eliminates the shared state by construction.

### Chain 5 — Java document wire corruption

> One upload combines two independent wire defects: the image is labelled as PDF, and the multipart body contains two conflicting file parts. Even if a server tolerates one defect, the other can still reject or misclassify KYC or dispute evidence. RazorProof validates content and emits one unambiguous part.

### Chain 6 — Generated mobile package identity

> The generator emits a nonexistent Cordova package and an unrelated empty Capacitor package. Installation failure is directly observed. The current packages were not shown to be malicious. The security lesson is that generated payment code must treat package publisher and repository identity as part of its protocol, not as an arbitrary string copied into a shell command. RazorProof detects this boundary today; registry enforcement remains to be built.

---

## Chapter 7 — The missing layer: economic intent

**[Overhead notebook. Three large boxes: `INTENT`, `PROVIDER FACT`, `FULFILLMENT`.]**

> These twenty-three findings look unrelated because they occur in different languages and products. Underneath, they violate five shared properties.

**[Property one appears.]**

> Value integrity: the amount and currency crossing the API must equal the merchant's intended value exactly.

**[Property two.]**

> Principal integrity: credentials, tenant, partner account, customer, order, and payment must remain attached to the same principal.

**[Property three.]**

> Effect integrity: a retry must identify whether it repeats one financial action or requests another.

**[Property four.]**

> Evidence integrity: signatures must authenticate the exact protocol bytes and every required field must survive from client to server.

**[Property five.]**

> Lifecycle integrity: provider success is not fulfillment authority until the server has reconciled the payment with the original merchant intent.

> Traditional SDKs answer, “How do I call this endpoint?” RazorProof answers, “What economic state transition is this caller allowed to make, and what evidence proves it happened once?”

---

## Chapter 8 — How RazorProof enforces the answer

**[Architecture animation builds one layer at a time.]**

> RazorProof is a Rust semantic payment firewall between applications or AI agents and Razorpay. It contains seven correctness domains.

> The core defines exact money, safe identifiers, cryptographic verification, canonical hashing, and the quote state machine. Amounts remain positive bounded integers in provider subunits. Human decimal conversion uses an exact decimal type. Currency exponent and quantum are explicit.

> The policy compiler defines one hundred and thirteen operations across twenty surfaces: payments, orders, refunds, settlements, payouts, payment links, QR codes, tokens, customers, subscriptions, invoices, items, virtual accounts, Route transfers, disputes, partner onboarding, documents, webhooks, registration links, and generated-code controls. Every operation owns its HTTP method, API version, path template, access class, economic effect, money fields, currency field, quote requirement, and idempotency strategy.

> The provider adapter accepts only an exact official Razorpay HTTPS origin in service mode. Redirects are disabled. Callers cannot provide arbitrary URLs or API versions. Path parameters are validated and encoded. Repeated query values are preserved. Responses, requests, webhook bodies, and documents are bounded.

> Each tenant owns immutable credentials and an immutable partner account. Live credentials are rejected by the current build. Provider writes require an intent. Generic writes are attempted once because retrying after an uncertain response can duplicate an effect. Read operations and explicitly idempotent refunds receive bounded retries. Refund intent becomes `X-Refund-Idempotency`.

> The store records a canonical body hash under tenant, intent, and operation. An exact completed replay returns the stored response. A changed body is a conflict. An in-flight duplicate is stopped. A failed or ambiguous intent cannot be silently reused. Quote transitions use optimistic version checks, so concurrent callers cannot advance the same financial state twice.

> The checkout lifecycle has four authorized states: issued quote, bound provider order, verified captured payment, and fulfilled. Quote issuance is an authenticated merchant-server operation; the production catalog adapter remains an explicit deployment gate. The server never trusts a browser-supplied order ID during verification. It uses the stored order ID in the signature preimage, fetches both provider objects, and compares order ID, payment order ID, amount, currency, captured status, tenant, and quote before advancing state.

> The webhook endpoint authenticates the raw body before JSON parsing, requires the provider event ID, and records tenant-scoped deduplication. The document endpoint validates filename, extension, size, magic bytes, and MIME, then constructs one multipart file part.

> Every accepted request, provider result, webhook, and state transition creates a canonical payload hash and a per-tenant BLAKE3 chain. The ledger stores fingerprints and proof metadata rather than credentials or full customer payloads. It is tamper-evident when a trusted chain head exists; it is not distributed consensus and a local administrator could rewrite both database and head. Production deployment therefore requires external head anchoring.

---

## Chapter 9 — Real-world proof

**[Dashboard recording. Keep the browser full-screen and the webcam absent until the numbers are legible.]**

> The control room begins with the smallest counterexample. Unsafe generated arithmetic maps two point zero one INR to two hundred. RazorProof maps it to two hundred and one. JPY and KWD controls demonstrate that the same policy understands currency-specific subunits.

**[Show the current Rust receipt.]**

> The Rust service authenticated to Razorpay Test Mode and created a real provider order for exactly two hundred and one INR subunits. The server quote ID and cart hash were bound into the provider notes. The local evidence chain independently verified four events at its recorded head.

**[Show the older campaign summary, clearly labelled `TEST MODE CAMPAIGN` rather than current Rust checkout.]**

> The broader Test Mode campaign completed two hosted checkouts. Both payments reached captured state and both Payment Links reached paid. The eight-rupee-one-paisa fixture was reconciled to a fully refunded ledger where payment amount, amount refunded, and refund sum all equalled eight hundred and one. Twenty-two signed webhook deliveries across six event types were captured and verified over their exact bytes. Sixteen contained literal non-ASCII UTF-8. Every exact-byte signature passed, and every .NET ASCII-equivalent digest failed.

> The current Rust state machine implements captured-payment verification and tests it locally, but that specific Rust quote-to-captured-payment path has not yet been completed against Test Mode. The legacy campaign and current Rust order proof are separate evidence sets and should be shown as such.

**[Show source scanner counters.]**

> The conformance engine scanned six hundred sixty-two files and two million six hundred eighty-three thousand seven hundred thirty bytes using twenty-three semantic detectors. It reproduced the full twenty-three-finding result and built six chains. The MCP drift check separately discovered forty-five current production tools and proved that all forty-five are represented in the one-hundred-thirteen-operation policy catalog.

---

## Chapter 10 — What is solved, what is contained, and what remains

**[Three columns: `PREVENTED`, `AVOIDED`, `DETECTION ONLY`.]**

> RazorProof directly prevents browser-authored order values, binary-float money, currency-exponent corruption, fractional subunits, mutated intent reuse, blind write retries, raw-webhook re-encoding, webhook replay, malformed signature exceptions, repeated-query collapse, and ambiguous multipart documents.

> It structurally avoids the .NET, PHP, and Java global-client defects because it does not use those SDKs and keeps tenant clients immutable. It also avoids their string-encoding and signature-comparison implementations at its own boundary.

> It detects but does not globally repair the .NET AES-GCM utility. Existing applications calling the SDK directly remain affected until an upstream patch or replacement adapter is deployed.

> Mobile signature loss is partially controlled: RazorProof prevents unverified fulfillment, but only a corrected client adapter can preserve data already discarded on the phone.

> Mobile package identity remains detection-only. Dedicated replacement helpers for the exact Ruby and Python payment-link verifier APIs are also not present. Applications bypassing the firewall remain outside its guarantees.

> Policy coverage is not the same as dynamic provider coverage. Some of the one hundred thirteen operations require products, balances, partner permissions, or entitlements this Test account does not have. The current service is deliberately locked to Test Mode. Production still requires KMS or HSM credential custody, replicated transactional storage, automatic reconciliation workers, rate limits, workload identity, egress policy, fuzzing, load and chaos testing, product-specific acceptance suites, external evidence-head notarization, and independent security review.

---

## Finale — What broke, and how we got out

**[Return to the original notebook page. Add four boxes around the initial `₹2.01 → 200`: `VALUE`, `PRINCIPAL`, `EFFECT`, `EVIDENCE`.]**

> We thought we had found a rounding error. What broke was much larger: payment integrations had no single boundary responsible for preserving economic intent across generated code, SDK state, provider effects, callbacks, and fulfillment.

> We got out by refusing to treat payment correctness as a collection of endpoint calls. We made money exact. We made merchant context immutable. We gave every write an identity. We verified original bytes. We bound the cart to one order, one captured payment, and one fulfillment. And we made every transition produce inspectable evidence.

**[Final lockup: `RIGHT MERCHANT × RIGHT AMOUNT × RIGHT EFFECT × ONCE`.]**

> RazorProof is not another wrapper around Razorpay. It is a compiler and enforcement boundary for financial intent. It finds where integrations violate payment invariants, blocks the corresponding failure classes for traffic that crosses the firewall, and shows exactly which claims were executed, observed, inferred, prevented, or still outside scope.

> An API can tell us whether a request was valid. A signature can tell us whether a provider processed it. RazorProof answers the question that decides whether software should move money or fulfill value: was this the right request, for the right merchant, for the right amount, under one intended effect, exactly once?

---

## Coverage audit: all 23 findings in this script

| # | Finding ID | Script case | Evidence | RazorProof relationship |
|---:|---|---:|---|---|
| 1 | `RP-MCP-GENERATOR-MONEY-UNDERCHARGE` | 1 | Dynamically reproduced | Prevented |
| 2 | `RP-MCP-GENERATOR-CURRENCY-EXPONENT` | 2 | Dynamic plus Test Mode order persistence | Prevented |
| 3 | `RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS` | 3 | Statically confirmed; downstream fulfillment inferred | Prevented when quote issuance stays behind a trusted merchant boundary; catalog adapter is a production gate |
| 4 | `RP-MCP-REFUND-TRUNCATION` | 4 | Dynamically reproduced | Prevented |
| 5 | `RP-MCP-REFUND-IDEMPOTENCY` | 5 | Known-public safety gap plus fault/Test controls | Prevented through intent identity |
| 6 | `RP-DOTNET-GLOBAL-AUTH-STATE` | 6 | Dynamically reproduced | Structurally avoided |
| 7 | `RP-PHP-GLOBAL-AUTH-STATE` | 7 | Dynamically reproduced | Structurally avoided |
| 8 | `RP-JAVA-GLOBAL-PARTNER-HEADERS` | 8 | Dynamically reproduced | Structurally avoided |
| 9 | `RP-DOTNET-GCM-NONCE-REUSE` | 9 | Dynamically reproduced | Detected and avoided; upstream repair absent |
| 10 | `RP-DOTNET-WEBHOOK-ASCII` | 10 | Dynamic plus Test Mode reachability | Prevented at raw-byte ingress |
| 11 | `RP-PYTHON-WEBHOOK-BYTES` | 11 | Dynamically reproduced compatibility defect | Structurally avoided at ingress |
| 12 | `RP-JAVA-DEFAULT-CHARSET` | 12 | Known-public conditional compatibility defect | Structurally avoided at ingress |
| 13 | `RP-RUBY-PAYLINK-ORDER` | 13 | Dynamically reproduced | Detection-only for exact helper |
| 14 | `RP-DOTNET-SIGNATURE-COMPARE` | 14 | Known-public hardening | Hardened in RazorProof |
| 15 | `RP-NODE-SIGNATURE-COMPARE` | 15 | Known-public hardening | Hardened in RazorProof |
| 16 | `RP-MCP-GENERATOR-SIGNATURE-LENGTH-500` | 16 | Dynamically reproduced | Prevented |
| 17 | `RP-PYTHON-PAYLINK-MISSING-FIELD` | 17 | Dynamically reproduced | Detection-only for exact helper |
| 18 | `RP-MCP-MOBILE-MISSING-SIGNATURE` | 18 | Statically confirmed | Partial: fail-closed server; client adapter absent |
| 19 | `RP-MCP-MOBILE-DEPENDENCY-CONFUSION` | 19 | Static plus registry observed | Detection-only |
| 20 | `RP-JAVA-UPLOAD-MIME` | 20 | Dynamically reproduced | Prevented by dedicated uploader |
| 21 | `RP-JAVA-UPLOAD-DUPLICATE-FILE-PART` | 21 | Dynamically reproduced | Prevented by dedicated uploader |
| 22 | `RP-MCP-EXPAND-COLLAPSE` | 22 | Known-public direct defect | Prevented |
| 23 | `RP-MCP-PAYOUT-NAME-DRIFT` | 23 | Statically confirmed documentation defect | Catalog alias plus drift detection |

## Coverage audit: all six chains in this script

| # | Chain | Included | Remaining unexecuted boundary |
|---:|---|---:|---|
| 1 | Refund mutation, retry, and webhook observability | Yes | Real production retry trigger |
| 2 | Checkout economic decoupling | Yes | Paid fulfillment of a tampered cart |
| 3 | Mobile paid-but-failed | Yes | Device checkout using generated flow |
| 4 | Cross-tenant routing | Yes | Two-account provider request |
| 5 | Java document wire corruption | Yes | Provider-side document handling |
| 6 | Mobile package identity | Yes | No malicious-package claim; current registry risk only |
