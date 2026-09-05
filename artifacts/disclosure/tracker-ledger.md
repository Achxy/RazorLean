# RazorProof disclosure and issue-tracker ledger

Audit date: 2026-09-03

This ledger separates public correctness defects from security-sensitive reports. Razorpay's repository `SECURITY.md` directs security vulnerabilities to HackerOne and forbids public disclosure. Public issue titles and bodies contain no credentials, provider IDs, webhook payloads, signatures, or customer data.

## Public correctness reports

| Finding | Repository | Tracker record | Status |
|---|---|---|---|
| Java document multipart MIME and duplicate `file` field | `razorpay-java` | https://github.com/razorpay/razorpay-java/issues/365 | Opened |
| Generated mobile callbacks omit mandatory signature | `razorpay-mcp-server` | https://github.com/razorpay/razorpay-mcp-server/issues/133 | Opened |
| Refund tool silently truncates fractional subunits | `razorpay-mcp-server` | https://github.com/razorpay/razorpay-mcp-server/issues/134 | Opened |
| Generated Node verifier maps malformed signature length to HTTP 500 | `razorpay-mcp-server` | https://github.com/razorpay/razorpay-mcp-server/issues/135 | Opened |
| .NET webhook verifier hashes UTF-8 bodies as ASCII | `razorpay-dot-net` | https://github.com/razorpay/razorpay-dot-net/issues/156 | Opened |
| Ruby Payment Link verification depends on Hash order | `razorpay-ruby` | https://github.com/razorpay/razorpay-ruby/issues/276 | Opened |

## Private security-sensitive reports

| Finding / chain | Destination | Local report | Status |
|---|---|---|---|
| .NET process-global credential, routing, and verifier state | Razorpay HackerOne | `private/dotnet-global-client-state.md` | Ready; not yet transmitted |
| PHP process-global credentials and headers | Razorpay HackerOne | `private/php-global-client-state.md` | Ready; not yet transmitted |
| Java process-global partner-routing header | Razorpay HackerOne | `private/java-global-partner-header.md` | Ready; not yet transmitted |
| .NET AES-GCM nonce reuse | Razorpay HackerOne | `private/dotnet-aes-gcm-nonce-reuse.md` | Ready; not yet transmitted |
| MCP mobile dependency identity boundary | Razorpay HackerOne | `private/mcp-mobile-dependency-identity.md` | Ready; not yet transmitted |
| MCP checkout economic/quote binding and currency chain | Razorpay HackerOne | `private/mcp-checkout-economic-binding.md` | Ready; not yet transmitted; bounty eligibility not claimed |

## Intentionally not reported as security vulnerabilities

- Node malformed-signature length produces HTTP 500: recorded only as a low-impact correctness issue, not a security/denial-of-service report.
- Node and .NET ordinary signature equality: defensive hardening, not a demonstrated functional or security failure.
- Missing refund idempotency-header exposure: safety/discoverability gap; receipt identity already exists and Test Mode controls behaved as documented.
- Duplicate order receipts: accepted platform behavior/documentation drift, not presented as an outage or security defect.
- The current third-party mobile package is empty; no malicious-package allegation is made.
