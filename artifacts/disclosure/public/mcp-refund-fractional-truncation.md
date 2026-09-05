## Summary

`create_refund` accepts `amount` as a floating-point number and silently casts it to `int` before invoking the Go SDK. An invalid fractional-subunit request is changed rather than rejected.

Affected commit: `7950d51d118ca164c32b7cf0cfaa14f34f24849f`

## Reproduction

The handler currently combines:

- `ValidateAndAddRequiredFloat(payload, "amount")`
- `int(payload["amount"].(float64))`

I ran the official handler and SDK request path against a local HTTP interceptor. The regression test expected a fractional amount to fail before any request; instead it observed:

```text
fractional money crossed the MCP boundary: requested=100.75 sent=100
```

An integer control of `100` crossed unchanged.

Separately, the Razorpay Test Refund API accepted a direct JSON `100.75` request in one sufficiently funded case and returned/persisted `100`, while Orders and Payment Links rejected the same fractional shape. That provider inconsistency increases the importance of failing closed at the MCP boundary, but this report's defect is independently reproducible without provider access.

## Expected

Money represented in currency subunits should be an integer. Fractional input must be rejected before the SDK call, never silently mutated.

## Suggested fix

- Validate and store `amount` as `int64` at the handler boundary.
- Reject `NaN`, infinities, fractions, overflow, and unsafe JSON-number magnitudes.
- Publish an integer JSON schema when the MCP dependency supports it.
- Add a test asserting that `100.75` makes no SDK/HTTP call and that `100` crosses unchanged.

The observed numerical change is less than one subunit, so this is reported as an input-integrity defect, not as a large-value loss claim.
