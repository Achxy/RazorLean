/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
export type PlateKind =
  | "fraction"
  | "float"
  | "currency"
  | "quote"
  | "length"
  | "envelope"
  | "package"
  | "query"
  | "retry"
  | "registry"
  | "encoding"
  | "nonce"
  | "comparison"
  | "permutation"
  | "adapter"
  | "checklist"
  | "charset"
  | "routing"
  | "mime"
  | "multipart";
export type GuideCase = {
  id: string;
  title: string;
  group: "Money" | "Authenticity" | "Identity" | "Integration";
  plate: PlateKind;
  labels: string[];
  story: string;
  mechanism: string;
  consequence: string;
  repair: string;
  scope: string;
  frames: [string, string, string, string];
};
export const guideCases: GuideCase[] = [
  {
    id: "RP-MCP-REFUND-TRUNCATION",
    title: "The fraction that vanished",
    group: "Money",
    plate: "fraction",
    labels: ["100.75 subunits", "100 subunits", "Reject the fraction"],
    story:
      "Bob asks a refund tool to send 100.75 subunits. That is already an invalid money representation: a subunit is indivisible. The useful answer would be a validation error.",
    mechanism:
      "Instead, the tool narrows the number to an integer. The fractional part disappears before the request reaches the API. The API sees a different, otherwise legal amount.",
    consequence:
      "The request changes meaning silently. This is a loss of input integrity, not evidence of a large-value financial loss.",
    repair:
      "Require an integer at the tool schema and validate again at the execution boundary. Do not round or truncate an invalid subunit input.",
    scope:
      "Official handler execution and captured request establish the mutation. The rejected representation should never become a provider write.",
    frames: [
      "An amount enters in subunits, not rupees.",
      "The cast separates the whole number from its fraction.",
      "Only 100 crosses the boundary; .75 is discarded.",
      "A correct boundary returns a validation error and sends nothing.",
    ],
  },
  {
    id: "RP-MCP-GENERATOR-MONEY-UNDERCHARGE",
    title: "A price just below itself",
    group: "Money",
    plate: "float",
    labels: ["2.01 × 100", "200.99999999999997", "201 paise"],
    story:
      "Alice sees ₹2.01. Bob’s generated backend must turn that decimal price into 201 paise. It looks like a multiplication followed by an integer conversion.",
    mechanism:
      "The binary floating-point intermediate is just below 201. Truncation moves it to 200. The enlarged ruler shows the boundary being crossed, not a price chosen by the provider.",
    consequence:
      "Generated merchant code can create an underpriced order while every subsequent API call works as specified. Rounding fixes this example but does not supply a currency contract.",
    repair:
      "Parse decimal strings into integer subunits exactly, with explicit precision and currency rules. Keep binary floats outside the money boundary.",
    scope:
      "Pinned emitted expressions were executed locally. The one-paise counterexample is an integration-generation defect, not a Razorpay ledger rounding claim.",
    frames: [
      "The human price is a decimal: ₹2.01.",
      "Binary multiplication lands infinitesimally below 201.",
      "Truncation chooses the integer on the wrong side.",
      "Exact parsing builds 201 directly; there is no float to round.",
    ],
  },
  {
    id: "RP-MCP-GENERATOR-CURRENCY-EXPONENT",
    title: "One ruler, three currencies",
    group: "Money",
    plate: "currency",
    labels: ["JPY · ×1", "INR · ×100", "KWD · ×1000"],
    story:
      "Bob adds a Japanese and a Kuwaiti price to his store. The generated conversion still multiplies every amount by 100, as if all currencies had two decimal places.",
    mechanism:
      "A yen has no fractional subunit. A Kuwaiti dinar has three decimal places, with additional provider quantum rules. The multiplier is part of the currency’s type, not a universal constant.",
    consequence:
      "JPY 295 becomes 29,500 subunits instead of 295. KWD 295.990 becomes 29,599 instead of 295,990. Both are integer-shaped; that does not make them economically correct.",
    repair:
      "Use an authoritative exponent and quantum table with exact decimal parsing, or accept validated integer subunits from a trusted server quote.",
    scope:
      "Wrong and exact control orders were accepted and persisted in Test Mode. These observations do not establish JPY/KWD capture, settlement, or real customer losses.",
    frames: [
      "Start with the currency’s unit, not the number 100.",
      "The generated ruler assumes two decimal places everywhere.",
      "The JPY and KWD readings diverge from their intended amounts.",
      "Give each currency its own exact scale and quantum check.",
    ],
  },
  {
    id: "RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS",
    title: "Two receipts for one purchase",
    group: "Money",
    plate: "quote",
    labels: ["Bob’s catalogue", "Provider order", "Bind the quote"],
    story:
      "Alice’s cart and the provider order are different records. Bob needs to know that the paid order belongs to this cart at the price his catalogue defines.",
    mechanism:
      "The generated flow carries browser-authored economics into order creation. Its verifier authenticates the provider identifiers, but does not independently bind that tuple to a server-authored cart and price.",
    consequence:
      "A genuine payment result can describe the wrong purchase. Authentication proves origin; fulfillment also needs business authorization and one-time consumption.",
    repair:
      "Build an immutable quote from trusted catalogue data, bind its order, currency, amount and merchant, and consume its fulfillment state once.",
    scope:
      "This is source-bound integration analysis. The illustration is a trust-boundary model, not a live checkout exploitation demonstration.",
    frames: [
      "Bob’s quote records what the purchase means.",
      "The provider order records what was actually requested.",
      "A signature covers the provider tuple, not the missing catalogue relationship.",
      "Match both records before allowing fulfillment.",
    ],
  },
  {
    id: "RP-MCP-GENERATOR-SIGNATURE-LENGTH-500",
    title: "The comparator needs a gate",
    group: "Authenticity",
    plate: "length",
    labels: [
      "Expected · 32 bytes",
      "Received · wrong length",
      "Reject before compare",
    ],
    story:
      "A verification endpoint receives an incomplete signature. It should classify it as invalid input, not report that the server itself broke.",
    mechanism:
      "Node’s timing-safe comparison requires equally sized buffers. The generated route calls it without enforcing that precondition; the thrown length exception becomes an HTTP 500.",
    consequence:
      "Ordinary malformed input creates noisy server errors and misleading operational alarms. This is error handling, not a demonstrated signature bypass.",
    repair:
      "Validate the hex encoding and exact length, decode into fixed-size bytes, then compare. Return a controlled client rejection for malformed input.",
    scope:
      "The generated comparison’s exception path was executed locally. No authentication bypass or remote availability impact is claimed.",
    frames: [
      "A SHA-256 digest has a fixed byte length.",
      "The received representation does not fill the required buffer.",
      "The comparison precondition fails before authentication is decided.",
      "A shape check rejects input before the comparator runs.",
    ],
  },
  {
    id: "RP-MCP-MOBILE-MISSING-SIGNATURE",
    title: "An envelope missing its seal",
    group: "Integration",
    plate: "envelope",
    labels: ["payment_id", "order_id", "signature"],
    story:
      "Alice finishes mobile checkout. The application now has to hand the backend everything it needs to verify the payment result.",
    mechanism:
      "Several generated native flows select callbacks that discard verification data. Android and iOS bodies explicitly send an empty signature; other native paths omit it.",
    consequence:
      "A success callback can reach a backend that must reject it. The missing information is introduced in the integration’s return path, after the UI announces success.",
    repair:
      "Use the supported data-bearing native callbacks and forward the full provider tuple. Verify and reconcile on the server before fulfillment.",
    scope:
      "The omission is visible in pinned generated source. A deployed mobile paid-but-failed incident was not reproduced.",
    frames: [
      "The backend expects a complete verification envelope.",
      "The selected callback preserves only part of the result.",
      "The signature slot arrives empty.",
      "A data-bearing callback preserves the complete tuple.",
    ],
  },
  {
    id: "RP-MCP-MOBILE-DEPENDENCY-CONFUSION",
    title: "A familiar name is not an identity",
    group: "Integration",
    plate: "package",
    labels: ["Generated package", "Registry identity", "Official SDK"],
    story:
      "A developer follows the mobile generator’s installation instructions. The package name looks payment-related, but the name alone does not establish who publishes it.",
    mechanism:
      "The investigated instructions include a missing package and a similarly named package whose captured metadata does not identify Razorpay’s official Cordova SDK.",
    consequence:
      "A generated integration may fail during installation or cross an unexpected third-party dependency boundary before payment code even runs.",
    repair:
      "Use the official package identity and supported instructions. Check registry owner, linked repository and intended version against an explicit allowlist in generator CI.",
    scope:
      "Registry observations are a captured snapshot, not a statement that package ownership can never change. No malicious package behaviour is alleged.",
    frames: [
      "Installation begins with a package identifier.",
      "Resolve the publisher and repository, not just the spelling.",
      "Missing or unrelated identities fail the intended dependency contract.",
      "Accept only the documented official SDK identity.",
    ],
  },
  {
    id: "RP-MCP-EXPAND-COLLAPSE",
    title: "The second value erases the first",
    group: "Integration",
    plate: "query",
    labels: ["payments", "transfers", "expand[]"],
    story:
      "Bob asks for payments and transfers to be expanded in one response. Both requests are legitimate and both need to survive query serialization.",
    mechanism:
      "The serializer writes each expansion into the same single-value map slot. The second assignment replaces the first instead of adding another query occurrence.",
    consequence:
      "The provider receives only the final expansion. Missing response detail looks like a retrieval problem, but information was lost before transmission.",
    repair:
      "Represent query values as a multimap or ordered key-value list. Preserve repeated keys all the way to URL encoding.",
    scope:
      "This is a documented/publicly known serialization defect. The drawing shows map semantics, not a provider ignoring a valid multi-expansion request.",
    frames: [
      "Two requested expansions are separate values.",
      "A single-value map has only one slot for expand[].",
      "The later assignment replaces the earlier one.",
      "A multi-value encoding carries both occurrences.",
    ],
  },
  {
    id: "RP-MCP-REFUND-IDEMPOTENCY",
    title: "A retry needs a name",
    group: "Identity",
    plate: "retry",
    labels: ["First request", "Retry", "One effect identity"],
    story:
      "Bob retries a refund after losing the acknowledgement. Without a stable identity, the second request can look exactly like an intentional second refund.",
    mechanism:
      "The tool omits an explicit idempotency header and under-explains receipt’s existing safety semantics. A stable receipt already provides protection; an omitted identity means something else.",
    consequence:
      "An agent can use the interface incorrectly even though the refund API behaves by design. The missing piece is an explicit, discoverable retry contract.",
    repair:
      "Document stable receipt reuse and expose the refund idempotency header. Preserve identity and body across retries, and reconcile ambiguous writes.",
    scope:
      "Safety/discoverability gap, not a broken refund API. A new identity may intentionally mean a new effect.",
    frames: [
      "There is one human intention to refund.",
      "Two network attempts are not necessarily two intentions.",
      "Without stable identity, the retry can become another effect.",
      "Reuse the documented identity and reconcile the outcome.",
    ],
  },
  {
    id: "RP-MCP-PAYOUT-NAME-DRIFT",
    title: "The directory points to no door",
    group: "Integration",
    plate: "registry",
    labels: [
      "fetch_payout_by_id",
      "fetch_payout_with_id",
      "One registered name",
    ],
    story:
      "An agent reads the published tool directory and chooses the payout lookup it lists. The server’s actual registry has a different name.",
    mechanism:
      "The documentation says fetch_payout_by_id; registration says fetch_payout_with_id. Tool names are exact identifiers, not natural-language suggestions.",
    consequence:
      "An otherwise sensible lookup stops at dispatch. No payout request reaches the provider.",
    repair:
      "Generate interface documentation from registration metadata or test every published tool name against the live registry during CI.",
    scope:
      "Source-bound documentation drift. This is not a payout processing failure or evidence that payouts were altered.",
    frames: [
      "The directory advertises a callable identifier.",
      "Dispatch looks for an exact registry key.",
      "The two names differ at by / with.",
      "Generate both surfaces from one definition.",
    ],
  },
  {
    id: "RP-DOTNET-WEBHOOK-ASCII",
    title: "Three bytes become a question mark",
    group: "Authenticity",
    plate: "encoding",
    labels: ["UTF-8 · E2 82 B9", "ASCII · 3F", "Preserve raw bytes"],
    story:
      "A webhook contains a literal rupee sign or non-English metadata. Its signature was computed over the original UTF-8 body.",
    mechanism:
      "The .NET helper converts the string with ASCIIEncoding. A non-ASCII character becomes a replacement byte, so the verifier authenticates a different message.",
    consequence:
      "A genuine webhook can fail verification. ASCII-only payloads do not expose this particular mismatch, which is why ordinary happy-path tests miss it.",
    repair:
      "Verify the untouched byte array. If a string compatibility overload is necessary, explicitly use UTF-8 without reformatting the body.",
    scope:
      "Locally reproduced and observed with non-ASCII Test Mode webhook payloads. This is conditional on payload representation, not every webhook.",
    frames: [
      "The original character occupies three UTF-8 bytes.",
      "ASCII cannot represent that character.",
      "Replacement changes the bytes before HMAC verification.",
      "Authenticate the original byte sequence without translation.",
    ],
  },
  {
    id: "RP-DOTNET-GCM-NONCE-REUSE",
    title: "The seal number must not repeat",
    group: "Authenticity",
    plate: "nonce",
    labels: ["Message A", "Message B", "Unique nonce / key"],
    story:
      "AES-GCM needs each encryption under one key to use a fresh nonce. Think of it as a seal number that must not be reused for that key.",
    mechanism:
      "The investigated onboarding helper derives the nonce from the secret key. Holding the key constant therefore holds the nonce constant across calls.",
    consequence:
      "This violates a prerequisite of GCM’s confidentiality and authentication guarantees. The diagram demonstrates the uniqueness requirement; it does not demonstrate a forgery.",
    repair:
      "Generate an appropriate fresh nonce for each encryption and carry it alongside ciphertext and tag in the interoperable format. Validate uniqueness and round-trip compatibility.",
    scope:
      "Pinned source and local SDK calls establish the construction. No production plaintext recovery or account compromise was demonstrated.",
    frames: [
      "One key can protect many messages only under the algorithm’s rules.",
      "The helper takes the nonce from key-derived material.",
      "Two calls reuse the same seal number under that key.",
      "Issue fresh nonce material for each encryption.",
    ],
  },
  {
    id: "RP-DOTNET-SIGNATURE-COMPARE",
    title: "Equality has two contracts",
    group: "Authenticity",
    plate: "comparison",
    labels: [".NET · String.Equals", "Equal / not equal", "FixedTimeEquals"],
    story:
      "Bob’s verifier needs the correct equality answer. At a cryptographic boundary, he may also want the comparison work not to depend on matching content.",
    mechanism:
      "Ordinary string equality specifies the result, not a fixed-time comparison contract. A fixed-time byte primitive is designed for that second requirement.",
    consequence:
      "This is a hardening opportunity. Correct equality is not itself a signature-verification failure, and the sketch is not a measured timing trace.",
    repair:
      "Validate and decode the digest into equal-length bytes, then use CryptographicOperations.FixedTimeEquals.",
    scope:
      "Publicly known hardening item. Practical remote timing exploitation was neither reproduced nor claimed.",
    frames: [
      "The two digests have a functional equality question.",
      "String equality does not promise content-independent comparison work.",
      "Do not confuse a missing guarantee with a demonstrated remote exploit.",
      "Use the dedicated fixed-time byte-comparison contract.",
    ],
  },
  {
    id: "RP-RUBY-PAYLINK-ORDER",
    title: "The fields agree; the sentence does not",
    group: "Authenticity",
    plate: "permutation",
    labels: ["link", "reference", "status", "payment"],
    story:
      "Two Ruby Hashes contain the same named callback fields. One was built in the documentation’s order; the other was assembled in a different order.",
    mechanism:
      "The verifier concatenates values in insertion order instead of explicitly reading fields in the protocol-defined order. The same map becomes a different signed sentence.",
    consequence:
      "An authentic callback may be rejected because of how application code constructed its Hash. Extra fields can also contaminate the serialized message.",
    repair:
      "Read the required named fields in canonical order, exclude unrelated fields, and leave the caller’s Hash untouched.",
    scope:
      "Local official-SDK comparison accepted the ordered Hash and rejected the reordered equivalent. No provider signature-generation defect is implied.",
    frames: [
      "Both maps contain the same field/value pairs.",
      "Insertion order changes the concatenated sentence.",
      "Different bytes cannot match the same expected digest.",
      "Serialize named fields in the protocol’s fixed order.",
    ],
  },
  {
    id: "RP-PYTHON-WEBHOOK-BYTES",
    title: "The right input meets the wrong socket",
    group: "Authenticity",
    plate: "adapter",
    labels: ["Framework · bytes", "SDK · string encoder", "Pass bytes through"],
    story:
      "A Python web framework gives Bob the raw request body as bytes. That is precisely the representation a webhook verifier should preserve.",
    mechanism:
      "The helper attempts a string-encoding operation on that bytes object. It throws a type error before comparing the valid signature.",
    consequence:
      "A careful raw-body integration is rejected by an incompatible SDK boundary. Developers may be tempted to add transformations that create new verification mistakes.",
    repair:
      "Accept bytes and bytearray without re-encoding. Encode only string inputs with the explicitly required encoding.",
    scope:
      "Local compatibility failure with a valid bytes payload. This is a type-adapter defect, not proof that every Python integration fails.",
    frames: [
      "The framework preserves the authentic byte sequence.",
      "The SDK socket assumes a string that still needs encoding.",
      "The adapter raises TypeError before authentication.",
      "Pass bytes through; encode only actual strings.",
    ],
  },
  {
    id: "RP-PYTHON-PAYLINK-MISSING-FIELD",
    title: "A checklist skips the field it reads",
    group: "Integration",
    plate: "checklist",
    labels: ["Required fields", "payment_link_id", "Guard before lookup"],
    story:
      "An incomplete callback reaches the verifier. The validation guard should identify every required field before later code reads any of them.",
    mechanism:
      "The guard omits payment_link_id from its complete-required-field check. The later dictionary lookup assumes it exists and raises KeyError.",
    consequence:
      "Malformed input can become an application exception instead of a controlled authentication rejection.",
    repair:
      "Define one complete required-field set and validate it before access. Keep missing, malformed and unauthenticated inputs on intentional rejection paths.",
    scope:
      "Local missing-field exception. The drawing concerns validation coverage, not a bypass of payment authentication.",
    frames: [
      "A checklist stands between the request and dictionary access.",
      "One required field is absent from the checklist.",
      "Lookup reaches the missing field and raises KeyError.",
      "Make the validation set cover every subsequent required access.",
    ],
  },
  {
    id: "RP-NODE-SIGNATURE-COMPARE",
    title: "A boolean is not a timing guarantee",
    group: "Authenticity",
    plate: "comparison",
    labels: ["Node · strict equality", "Equal / not equal", "timingSafeEqual"],
    story:
      "The Node helper compares two hexadecimal strings. The comparison can give the correct boolean while leaving a separate hardening requirement unspecified.",
    mechanism:
      "JavaScript strict equality is not a cryptographic timing contract. A dedicated primitive makes that requirement explicit after format and length validation.",
    consequence:
      "Treat this as defence in depth, not a proven payment exploit. The diagram contrasts contracts rather than plotting invented latency measurements.",
    repair:
      "Validate hex and length, decode the values, and call crypto.timingSafeEqual on equal-length byte buffers.",
    scope:
      "Publicly known hardening item. Remote exploitability has not been established, and ordinary equality remains functionally correct.",
    frames: [
      "Strict equality can answer the boolean question correctly.",
      "That API does not specify a fixed-time cryptographic comparison.",
      "There is no measured remote attack in this evidence set.",
      "Choose timingSafeEqual only after enforcing its input preconditions.",
    ],
  },
  {
    id: "RP-JAVA-DEFAULT-CHARSET",
    title: "The machine becomes part of the message",
    group: "Authenticity",
    plate: "charset",
    labels: ["UTF-8 host", "Other default charset", "Explicit UTF-8"],
    story:
      "The same Java integration is deployed on two differently configured runtimes. Its source is unchanged, but an implicit text encoding can change the bytes it authenticates.",
    mechanism:
      "The payload calls getBytes() without a charset. That delegates the choice to the runtime default instead of the protocol.",
    consequence:
      "Non-ASCII verification can vary on runtimes/configurations whose default is not UTF-8. Java 18+ defaults to UTF-8, so this is not a universal failure claim.",
    repair:
      "Specify StandardCharsets.UTF_8 and offer a raw byte-array verifier. Test with non-ASCII content and an intentionally different default environment.",
    scope:
      "Conditional compatibility issue. The plate distinguishes protocol-required encoding from environment-dependent defaults.",
    frames: [
      "The protocol needs a particular sequence of bytes.",
      "An omitted charset asks the host to choose the encoding.",
      "Different host defaults can produce different sequences.",
      "Name the encoding explicitly or preserve the original bytes.",
    ],
  },
  {
    id: "RP-DOTNET-GLOBAL-AUTH-STATE",
    title: "Two clients, one credential drawer",
    group: "Identity",
    plate: "routing",
    labels: [".NET client A", ".NET client B", "Key + routing state"],
    story:
      "One .NET process creates clients for two merchants. Each client looks like an independent object, so Bob expects its credentials and routing context to stay attached to it.",
    mechanism:
      "The SDK stores relevant context in process-wide state. Constructing B replaces the key visible to A; header state can also carry across client boundaries.",
    consequence:
      "Local verification for A can start using B’s secret, and request identity can diverge from object identity. A valid A signature failed in the recorded interleaving.",
    repair:
      "Keep immutable authentication, endpoints and headers on each request client. Bind every resource and verification operation to that explicit owner.",
    scope:
      "Local official-SDK state interleaving, not a live cross-merchant transfer. Tenant-fixed access protects only operations routed through that boundary.",
    frames: [
      "Client A opens with A’s own context.",
      "Client B writes into the same process-wide drawer.",
      "A later operation through A reads context belonging to B.",
      "Separate the drawers: each client owns an immutable context.",
    ],
  },
  {
    id: "RP-PHP-GLOBAL-AUTH-STATE",
    title: "The worker remembers the wrong merchant",
    group: "Identity",
    plate: "routing",
    labels: ["PHP worker · A", "Next merchant · B", "Credentials + headers"],
    story:
      "A long-running PHP worker serves more than one merchant. Creating a second client should not change the first client’s identity.",
    mechanism:
      "Authentication and header state are shared at process scope. The recorded construction of B replaces the global key while inheriting A’s partner header.",
    consequence:
      "Isolation assumed by application code does not exist in the SDK object model. The problem is especially relevant when a worker survives across merchants.",
    repair:
      "Give each client its own immutable request context and inject it into resources. Do not mutate shared credentials between requests.",
    scope:
      "Local state inspection establishes overwrite and inheritance. No live request under another merchant’s credentials was sent.",
    frames: [
      "The worker handles merchant A with A’s client.",
      "A second client changes process-wide credential state.",
      "The old object and the current identity no longer agree.",
      "Instance-owned context survives interleaving without identity drift.",
    ],
  },
  {
    id: "RP-JAVA-GLOBAL-PARTNER-HEADERS",
    title: "The address label is shared",
    group: "Identity",
    plate: "routing",
    labels: ["Java client A", "Java client B", "Partner header map"],
    story:
      "An aggregator uses separate Java clients to route requests to different sub-merchants. The partner header is the address label on those requests.",
    mechanism:
      "The clients share a static header map. B inherits A’s routing header, and an update through B changes the shared routing context.",
    consequence:
      "A request can retain the wrong destination even if other parts of authentication are independent. This finding is specifically about shared partner routing.",
    repair:
      "Use immutable per-client defaults and explicit per-request overrides. Validate the tenant’s route before dispatch.",
    scope:
      "Local header inheritance and overwrite were observed. Do not generalize this Java finding into a demonstrated global credential overwrite.",
    frames: [
      "A partner header selects the sub-merchant route.",
      "Both clients point at the same mutable address book.",
      "Changing one address changes what the other client reads.",
      "Bind routing headers to the client or to the individual request.",
    ],
  },
  {
    id: "RP-JAVA-UPLOAD-MIME",
    title: "A PNG wearing a PDF label",
    group: "Integration",
    plate: "mime",
    labels: ["proof.png", "image/pdf", "image/png"],
    story:
      "Bob uploads an image as supporting documentation. The binary file and its declared media type need to agree before a downstream processor can interpret it reliably.",
    mechanism:
      "The investigated Java serializer classifies a runtime PNG pathname as image/pdf. The image bytes do not become a PDF; only the label changes.",
    consequence:
      "A valid upload can be rejected, misclassified or sent down the wrong processing path. The defect sits at serialization, not in the image itself.",
    repair:
      "Compare extension values correctly, map supported types explicitly, and validate trusted content metadata where possible. Reject unsupported input deliberately.",
    scope:
      "Local official serializer output established the incorrect MIME label. A real KYC rejection was not demonstrated.",
    frames: [
      "The upload carries an image file.",
      "Serialization assigns the outgoing Content-Type.",
      "The label says image/pdf while the input is PNG.",
      "Preserve the actual media contract: image/png for a valid PNG.",
    ],
  },
  {
    id: "RP-JAVA-UPLOAD-DUPLICATE-FILE-PART",
    title: "One file, two competing parts",
    group: "Integration",
    plate: "multipart",
    labels: ["file · binary", "file · pathname", "One file part"],
    story:
      "Bob supplies a single upload. A multipart request should carry that file once, alongside any ordinary metadata fields.",
    mechanism:
      "The serializer emits a binary file part, then processes the file field again in the ordinary field loop. The wire body contains two parts with the same name but different meanings.",
    consequence:
      "A receiver may reject the duplication or select a different part than the sender intended. A local pathname is not a replacement for uploaded file bytes.",
    repair:
      "Exclude the file key from ordinary field serialization. Test the final wire format for exactly one file part with the expected content type and bytes.",
    scope:
      "Local multipart capture observed two file parts. Different receiver selection behaviours are possible consequences, not universally observed outcomes.",
    frames: [
      "One binary file is added to the multipart body.",
      "The generic field loop reaches the file key again.",
      "The request now contains competing binary and text file parts.",
      "Serialize the binary field once and keep metadata separate.",
    ],
  },
];
