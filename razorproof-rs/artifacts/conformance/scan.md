# RazorProof conformance report

Scanned `662` files (2683730 bytes) with 23 semantic detectors. Found 23 findings, including 17 direct defects.

| ID | Severity | Classification | Evidence |
|---|---|---|---|
| `RP-DOTNET-GCM-NONCE-REUSE` | `Critical` | `Defect` | razorpay-dot-net/src/Utils.cs:104 |
| `RP-DOTNET-GLOBAL-AUTH-STATE` | `High` | `Defect` | razorpay-dot-net/src/RazorpayClient.cs:15 |
| `RP-JAVA-GLOBAL-PARTNER-HEADERS` | `High` | `Defect` | razorpay-java/src/main/java/com/razorpay/ApiUtils.java:33 |
| `RP-MCP-GENERATOR-CURRENCY-EXPONENT` | `High` | `Defect` | razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go:30 |
| `RP-MCP-GENERATOR-MONEY-UNDERCHARGE` | `High` | `Defect` | razorpay-mcp-server/pkg/razorpay/integrations/backend_go.go:58 |
| `RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS` | `High` | `Defect` | razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go:30 |
| `RP-MCP-MOBILE-DEPENDENCY-CONFUSION` | `High` | `Defect` | razorpay-mcp-server/pkg/razorpay/integrations/mobile.go:843 |
| `RP-MCP-MOBILE-MISSING-SIGNATURE` | `High` | `Defect` | razorpay-mcp-server/pkg/razorpay/integrations/mobile.go:407 |
| `RP-PHP-GLOBAL-AUTH-STATE` | `High` | `Defect` | razorpay-php/src/Api.php:9 |
| `RP-DOTNET-WEBHOOK-ASCII` | `Medium` | `Defect` | razorpay-dot-net/src/Utils.cs:135 |
| `RP-JAVA-UPLOAD-DUPLICATE-FILE-PART` | `Medium` | `Defect` | razorpay-java/src/main/java/com/razorpay/ApiUtils.java:256 |
| `RP-JAVA-UPLOAD-MIME` | `Medium` | `Defect` | razorpay-java/src/main/java/com/razorpay/ApiUtils.java:242 |
| `RP-MCP-EXPAND-COLLAPSE` | `Medium` | `Defect` | razorpay-mcp-server/pkg/razorpay/tools_params.go:265 |
| `RP-MCP-REFUND-IDEMPOTENCY` | `Medium` | `Compatibility` | razorpay-mcp-server/pkg/razorpay/refunds.go:73 |
| `RP-MCP-REFUND-TRUNCATION` | `Medium` | `Defect` | razorpay-mcp-server/pkg/razorpay/refunds.go:64 |
| `RP-PYTHON-WEBHOOK-BYTES` | `Medium` | `KnownPublic` | razorpay-python/razorpay/utility/utility.py:62 |
| `RP-RUBY-PAYLINK-ORDER` | `Medium` | `Defect` | razorpay-ruby/lib/razorpay/utility.rb:20 |
| `RP-DOTNET-SIGNATURE-COMPARE` | `Low` | `KnownPublic` | razorpay-dot-net/src/Utils.cs:72 |
| `RP-JAVA-DEFAULT-CHARSET` | `Low` | `KnownPublic` | razorpay-java/src/main/java/com/razorpay/Utils.java:53 |
| `RP-MCP-GENERATOR-SIGNATURE-LENGTH-500` | `Low` | `Defect` | razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go:69 |
| `RP-MCP-PAYOUT-NAME-DRIFT` | `Low` | `Compatibility` | razorpay-mcp-server/pkg/razorpay/payouts.go:59 |
| `RP-NODE-SIGNATURE-COMPARE` | `Low` | `KnownPublic` | razorpay-node/lib/utils/razorpay-utils.js:102 |
| `RP-PYTHON-PAYLINK-MISSING-FIELD` | `Low` | `Defect` | razorpay-python/razorpay/utility/utility.py:28 |

## Remediations

### RP-DOTNET-GCM-NONCE-REUSE

.NET onboarding encryption derives a reusable AES-GCM nonce from the key

Invariant: An AES-GCM key and nonce pair must never be reused.

Fix: Generate a fresh random 96-bit nonce for every encryption and carry it with the ciphertext.

### RP-DOTNET-GLOBAL-AUTH-STATE

.NET client instances share process-wide credential state

Invariant: Credentials and routing headers must be immutable per client instance.

Fix: Move credentials and headers into immutable instance state and inject them into each request.

### RP-JAVA-GLOBAL-PARTNER-HEADERS

Java clients share one process-wide partner-routing map

Invariant: Submerchant routing must be immutable per client and cannot bleed across tenants.

Fix: Construct request-local headers from immutable client-owned partner context.

### RP-MCP-GENERATOR-CURRENCY-EXPONENT

Generated checkout hard-codes a two-decimal currency exponent

Invariant: Currency exponent and provider quantum are properties of the currency, not a universal constant.

Fix: Resolve exponent and quantum from an audited currency table and reject unsupported precision.

### RP-MCP-GENERATOR-MONEY-UNDERCHARGE

Generated checkout backends convert binary floating point money by truncation

Invariant: Major-to-minor conversion must be decimal-exact and must produce an integer.

Fix: Accept integer subunits or exact decimal strings and convert with a currency-aware decimal type.

### RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS

Generated checkout lets the browser author the order amount

Invariant: The merchant server must derive amount, currency, and cart identity from trusted catalog state.

Fix: Replace browser-authored prices with a short-lived, server-valued quote bound to the provider order.

### RP-MCP-MOBILE-DEPENDENCY-CONFUSION

Generated mobile setup installs a non-official package identity

Invariant: Payment code generators must pin packages controlled and documented by the provider.

Fix: Generate only the official package coordinates and continuously verify their publisher and registry state.

### RP-MCP-MOBILE-MISSING-SIGNATURE

Generated mobile success paths discard the payment signature

Invariant: Every client success callback must pass the payment, order, and signature tuple to server verification.

Fix: Use SDK success objects that contain the full signed tuple and fail closed when any field is absent.

### RP-PHP-GLOBAL-AUTH-STATE

PHP client instances share process-wide credentials and headers

Invariant: Credentials and routing headers must be immutable per client instance.

Fix: Use instance-owned authentication and request headers without static mutation.

### RP-DOTNET-WEBHOOK-ASCII

.NET webhook verifier hashes Unicode payloads as ASCII

Invariant: Webhook HMAC verification must hash the exact UTF-8 bytes received from the network.

Fix: Accept raw bytes; if a string boundary is unavoidable, use strict UTF-8 without reserialization.

### RP-JAVA-UPLOAD-DUPLICATE-FILE-PART

Java document upload emits two conflicting file parts

Invariant: A document multipart request contains exactly one binary file part.

Fix: Remove the file key before serializing scalar form fields and emit one binary part.

### RP-JAVA-UPLOAD-MIME

Java document upload maps image extensions to an invalid PDF MIME

Invariant: Multipart Content-Type must match both the extension and file magic bytes.

Fix: Use value equality and map JPEG, PNG, and PDF magic bytes to the exact allowed MIME.

### RP-MCP-EXPAND-COLLAPSE

Repeated expand query parameters collapse into one value

Invariant: A repeated query parameter must retain every caller-supplied value.

Fix: Represent repeated parameters as a multi-value query and append rather than overwrite.

### RP-MCP-REFUND-IDEMPOTENCY

Refund tool does not expose Razorpay's refund idempotency identity

Invariant: Retryable financial effects need a stable caller-owned identity.

Fix: Expose a required intent identity and send it as X-Refund-Idempotency with immutable request hashing.

### RP-MCP-REFUND-TRUNCATION

Refund MCP tool silently truncates a fractional subunit amount

Invariant: Subunit money is integer-valued and invalid fractions must be rejected, never changed.

Fix: Validate an int64 at the MCP boundary and reject fractional JSON values.

### RP-PYTHON-WEBHOOK-BYTES

Python utility owns a text boundary instead of the raw webhook bytes

Invariant: Webhook verification should preserve exact raw request bytes.

Fix: Add a raw-bytes verifier and retain the text API only as a compatibility wrapper.

### RP-RUBY-PAYLINK-ORDER

Ruby payment-link verification depends on hash insertion order

Invariant: Signature preimages must use named fields in the documented order.

Fix: Construct the preimage from explicitly named fields in a constant documented order.

### RP-DOTNET-SIGNATURE-COMPARE

.NET signature comparison is not constant time

Invariant: Authentication tags should be compared in constant time.

Fix: Decode fixed-length hexadecimal tags and use CryptographicOperations.FixedTimeEquals.

### RP-JAVA-DEFAULT-CHARSET

Java signature utility relies on the process default charset

Invariant: Cryptographic byte encoding must be explicit and portable.

Fix: Use StandardCharsets.UTF_8 explicitly for every signature preimage.

### RP-MCP-GENERATOR-SIGNATURE-LENGTH-500

Generated Node verifier turns malformed signature length into HTTP 500

Invariant: Malformed untrusted signatures must fail as authentication errors, not exceptions.

Fix: Decode strict hex, validate equal fixed length, then compare in constant time and return 400.

### RP-MCP-PAYOUT-NAME-DRIFT

Payout tool name differs between current source and some callers

Invariant: Tool names need a versioned compatibility map.

Fix: Publish the current name and retain an explicit alias for fetch_payout_by_id.

### RP-NODE-SIGNATURE-COMPARE

Node signature utility uses ordinary string equality

Invariant: Authentication tags should be compared in constant time.

Fix: Decode strict fixed-length hexadecimal tags and use timingSafeEqual.

### RP-PYTHON-PAYLINK-MISSING-FIELD

Python payment-link verifier reads an unvalidated required field

Invariant: All signature preimage fields must be validated before access.

Fix: Validate the complete required field set and return a typed validation error.


## Compositional failure chains

### CHAIN-REFUND-MUTATION-RETRY-OBSERVABILITY

A network interruption after acceptance can leave both the sent amount and effect identity uncertain.

Components: `RP-MCP-REFUND-TRUNCATION`, `RP-MCP-REFUND-IDEMPOTENCY`

Demonstration: Intercept the provider request, submit 100.75 twice around a forced disconnect, and compare request bodies and refund IDs.

### CHAIN-CHECKOUT-ECONOMIC-DECOUPLING

A fresh generated checkout can accept a tampered or mis-scaled amount and still produce a validly signed provider payment.

Components: `RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS`, `RP-MCP-GENERATOR-MONEY-UNDERCHARGE`, `RP-MCP-GENERATOR-CURRENCY-EXPONENT`

Demonstration: Generate the integration, change the browser amount, and run INR 2.01, JPY 295, and KWD 295.990 controls against captured outbound orders.

### CHAIN-MOBILE-PAID-BUT-FAILED

The provider can report success while the merchant cannot complete its generated verification path.

Components: `RP-MCP-MOBILE-MISSING-SIGNATURE`

Demonstration: Run each generated success callback and assert that the signed payment tuple reaches the server intact.

### CHAIN-CROSS-TENANT-ROUTING

Creating or mutating one client can change credentials or partner routing used by another client in the same process.

Components: `RP-DOTNET-GLOBAL-AUTH-STATE`, `RP-PHP-GLOBAL-AUTH-STATE`, `RP-JAVA-GLOBAL-PARTNER-HEADERS`

Demonstration: Instantiate tenants A and B, interleave requests through a capture server, and assert every Authorization and X-Razorpay-Account pair.

### CHAIN-JAVA-DOCUMENT-WIRE-CORRUPTION

An otherwise valid JPG or PNG can reach the document endpoint as an ambiguous multipart body.

Components: `RP-JAVA-UPLOAD-MIME`, `RP-JAVA-UPLOAD-DUPLICATE-FILE-PART`

Demonstration: Capture the multipart request and assert one binary file part whose Content-Type matches its magic bytes.

### CHAIN-MOBILE-PACKAGE-IDENTITY

A copy-pasted integration depends on an identity outside Razorpay's documented package boundary.

Components: `RP-MCP-MOBILE-DEPENDENCY-CONFUSION`

Demonstration: Resolve the generated coordinates against the live registries and compare publisher, contents, and official documentation.
