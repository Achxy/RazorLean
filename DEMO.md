# RazorProof Demo Script

## The 20-second thesis

Razorpay now has APIs, seven major server SDKs, an MCP server and an AI checkout-code generator. Each surface can be locally correct while disagreeing about money, bytes, retries or cryptographic wire formats. RazorProof compiles those cross-surface semantics into executable conformance tests.

The wedge is measurable on day zero: Razorpay's official MCP generator emits binary-float truncation into seven backend-language templates. Enter ₹2.01 and several emitted constructions create an order for 200 paise, not 201.

## The 3-minute demo

1. Run the full compiler:

   ```bash
   PYTHONPATH=src python3 -m razorproof scan --containers --output artifacts/final
   ```

   Expected repository-scan summary after the feature audit: 13 observations, including 7 direct defects, 2 conditional compatibility defects, and 4 explicitly non-bug safety/hardening/documentation gaps; 0 probe errors. The separate Test Mode campaign adds one provider API defect.

2. Show the generated-code counterexample in `artifacts/final/case-report.md`:

   - Python, Ruby and PHP execute the official emitted expression and return 200 for ₹2.01.
   - Source matches connect the same construction to the Go, Java, Rust and .NET templates.
   - Node's `Math.round` result of 201 acts as the control.

3. Show the shipped-SDK security drift:

   - Official .NET SDK: two onboarding encryptions under one key produce identical AES-GCM output.
   - Official .NET SDK: a correctly signed literal UTF-8 body containing `₹` and Malayalam is rejected because the SDK hashes ASCII substitutions. State clearly that live Razorpay delivery of literal non-ASCII rather than escaped JSON is not yet verified.
   - Official Ruby SDK: identical payment-link fields pass or fail solely based on Hash insertion order.
   - Official Go MCP handler: `100.75` crosses the SDK HTTP boundary as `100`.

4. Run the lost-response lab:

   ```bash
   PYTHONPATH=src python3 -m razorproof fault-lab
   ```

   The server commits an effect and drops the connection. One retry produces two effects without identity and one effect with stable identity. Razorpay's real API already supports that identity through a stable `receipt` as well as `X-Refund-Idempotency`; the MCP gap is header support and poor discovery, not absence of all idempotency.

5. Show that these are fixable, not theatrical:

   ```bash
   PYTHONPATH=src python3 -m razorproof prove-fixes --containers
   ```

   Five remediation proofs go red to green on disposable clean clones: exact money, Python raw bytes, Ruby protocol order, MCP integer rejection, and .NET random nonce plus UTF-8.

## Evidence boundary

- Dynamic probes execute the official pinned source or the exact code emitted by it.
- The fault lab is real loopback HTTP with a deliberate post-commit disconnect; it is not represented as Razorpay production.
- A guarded `live-refund` adapter exists for a user-owned Razorpay test account. It refuses `rzp_live_` keys and refuses to execute without `--execute-test-mode`.
- No merchant credentials were available during this build, so the live adapter was verified only at its fail-closed gate. The public idempotency pull request linked in the report supplies independent live test-mode evidence.

## Why judges should care

This is a compiler and test infrastructure primitive, not another dashboard feature. A conventional linter sees valid syntax in `int(amount * 100)`. A conventional SAST scanner sees that AES-GCM is present. RazorProof understands the deeper contracts: ₹2.01 must remain 201 paise; GCM nonces must be unique per key; raw request bytes must remain byte-identical; a retry must preserve one economic effect; signed field order belongs to the protocol, not the container.
