# Feature or bug? Adversarial audit of RazorProof

> This file preserves the original 14-observation audit. The expanded 24-observation campaign, six chained failures, additional negative controls, and tracker routing are in [research/expanded-bug-audit/report-source.md](research/expanded-bug-audit/report-source.md).

The original report was overclaiming. After checking each behavior against official contracts, provider releases, runtime conventions, and counterexamples, the honest result is:

- **7 direct scanner defects** remain;
- **2 conditional compatibility defects** remain, with explicit runtime caveats;
- **4 observations are not runtime bugs**: one safety/discoverability gap, two hardening opportunities, and one documentation defect;
- **1 original claim was wrong and has been removed**.

That leaves 13 scanner observations, with 9 defect-level claims. A separate real Razorpay Test Mode campaign adds one direct API defect, for **14 total observations and 8 direct defects** across repository and provider evidence.

## The claims that survived

| Class | Claims |
|---|---|
| Direct defects | .NET AES-GCM nonce reuse; seven-language generated undercharge; .NET ASCII webhook hashing; MCP `expand[]` collapse; refund fractional truncation; Ruby payment-link Hash-order dependence; Python missing-field crash |
| Conditional compatibility defects | Java default charset; Python raw-byte webhook input |

The crown-jewel findings now have provider-side proof:

1. Razorpay's official MCP integration generator emits conversions that turn an intended ₹2.01 into 200 paise across seven backend languages. The [Order API contract](https://razorpay.com/docs/api/orders/create/?preferred-country=IN) requires the intended integer smallest-subunit amount, so truncation is not a supported feature.
2. Razorpay's .NET SDK derives its AES-GCM nonce from the key. Razorpay's own [Ruby v3.2.4 release](https://github.com/razorpay/razorpay-ruby/releases/tag/v3.2.4) and [PHP 2.9.3 release](https://github.com/razorpay/razorpay-php/releases/) identify and fix the same nonce-reuse vulnerability.
3. Razorpay Test Mode delivered 16 validly signed webhook bodies containing literal UTF-8 metadata. Exact raw bytes verified; the current .NET SDK's ASCII-equivalent transformation failed all 16. This is now a provider-reachable direct defect, not a hypothetical encoding edge.
4. The direct Refund API accepted JSON `amount: 100.75`, returned 100, emitted signed lifecycle webhooks, and persisted a processed 100-subunit ledger effect even though the official contract requires an integer. A smaller-balance negative control rejected the same invalid input, bounding the claim to inconsistent fail-open validation rather than universal coercion.

## What was not actually a bug

- **Refund idempotency:** The original claim said the MCP tool had no idempotency mechanism. That was wrong. The tool already accepts `receipt`, and Razorpay explicitly documents that [receipt is treated as an idempotency key](https://razorpay.com/docs/api/refunds/create-normal/?preferred-country=US). The real issue is that the description hides this safety property and the tool cannot send the newer header.
- **Go 1.21 setup:** The claim ignored Go's automatic toolchain switching. Since Go 1.21, the default policy can fetch a newer toolchain required by `go.mod`, as documented by [Go's toolchain selection rules](https://go.dev/doc/toolchain). It only fails under local-only or offline policy, so the scanner rule was removed.
- **Node and .NET string equality:** Ordinary equality verifies signatures correctly. Timing-safe comparison is worthwhile defensive hardening, but without a practical exploit or provider mandate it is not honest to call these vulnerabilities.
- **Payout tool naming:** The README-to-registry mismatch is real, but it is a documentation/interface defect, not a payout-processing bug.

## Claims that still carry caveats

- Java's default-charset behavior matters on older or explicitly non-UTF-8 configurations. Java 18+ standardized UTF-8 defaults, so it is conditional.
- Python rejecting a bytes body is a real framework-integration mismatch, but Razorpay's raw-body rule is about preserving content, not mandating Python's `bytes` type.

## Real Test Mode evidence

- [Campaign summary](artifacts/razorpay-test/campaign-summary.md)
- [Order boundary](artifacts/razorpay-test/order-boundary.md)
- [Refund identity matrix](artifacts/razorpay-test/refund-identity-matrix.md)
- [Processed refund ledger](artifacts/razorpay-test/refund-ledger.md)
- [Literal UTF-8 webhook proof](artifacts/razorpay-test/webhook-byte-evidence.md)
- [Fractional dust negative control](artifacts/razorpay-test/refund-fractional-dust.md)

No Live Mode transaction was attempted. Private API credentials, raw webhook bodies, contact data, and provider IDs are excluded from the published artifacts.

## Scanner changes

RazorProof now separates evidence strength from claim type:

```text
Evidence:    confirmed_dynamic | confirmed_static | known_public | candidate
Claim type: defect | compatibility_defect | safety_gap | hardening | documentation_defect
```

The Go claim is gone, public issues and PRs are no longer called maintainer-confirmed defects, and severity was reduced wherever the actual blast radius did not justify the earlier label. The refund fix proof was also repaired: it now proves fractional rejection **and** valid-integer acceptance at the official handler/SDK HTTP boundary.

The complete claim matrix, methodology, executable checks, and source ledger are in [research/feature-audit/report-source.md](research/feature-audit/report-source.md).
