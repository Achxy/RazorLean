# Razorpay Test Control-Plane: Fractional Refund Dust

- Fractional `100.75` accepted and persisted as `100`: `False`
- One-subunit residual created: `False`
- Explicit one-subunit refund rejected: `True`
- Header-idempotent omitted amount rejected: `True`
- Receipt-identified omitted amount closed the residual: `False`
- Receipt retry prevented a duplicate: `False`

| Step | Requested amount | HTTP | Returned amount | Result |
|---|---:|---:|---:|---|
| fractional | `100.75` | `400` | `None` | `invalid request sent` |
| explicit residual | `1` | `400` | `` | `The amount must be atleast INR 1.00` |
| header-idempotent omitted amount | omitted | `400` | `None` | `invalid request sent` |
| receipt-identified omitted amount | omitted | `400` | `None` | `invalid request sent` |
| identical receipt retry | omitted | `400` | `` | `invalid request sent` |

On this fixture, only 101 subunits remained. Razorpay rejected the same `100.75` fractional request before creating an effect, so no one-subunit residual was produced. The explicit one-subunit request and both omitted-amount identity forms were also rejected. This negative control disproves the proposed stranded-dust story and shows that the fractional fail-open path is conditional on provider state or validation routing; the broader claim is deliberately not made.

Provider identifiers are represented only by one-way fingerprints.
