# Razorpay Test Control-Plane: Expanded Order Contract Matrix

- Real money: `False`
- Requests completed: `True`
- Generated JPY mismatch persisted: `True`
- Generated KWD mismatch persisted: `True`
- Duplicate receipt created two orders: `True`
- Key fingerprint only: `0bb387c233eb`

| Vector | Currency | Requested subunits | HTTP | Accepted | Persisted subunits |
|---|---|---:|---:|---|---:|
| `duplicate_receipt_first` | `INR` | `100` | `200` | `True` | `100` |
| `duplicate_receipt_second` | `INR` | `100` | `200` | `True` | `100` |
| `generated_jpy_295_times_100` | `JPY` | `29500` | `200` | `True` | `29500` |
| `exact_jpy_295` | `JPY` | `295` | `200` | `True` | `295` |
| `generated_kwd_295_99_times_100` | `KWD` | `29599` | `200` | `True` | `29599` |
| `exact_kwd_295_990` | `KWD` | `295990` | `200` | `True` | `295990` |
| `fractional_order_control` | `INR` | `100.75` | `400` | `False` | `` |
| `fractional_payment_link_control` | `INR` | `100.75` | `400` | `False` | `` |

## Classification

- The currency result is a generator defect, not an Orders API defect. The generated fixed ×100 rule submitted type-valid but economically wrong integers; Razorpay Test Mode persisted them exactly.
- Reusing one receipt produced two distinct orders. This contradicts the current Create Order documentation's uniqueness wording, but it did not cause the hypothesised collision outage, so it is recorded only as contract/documentation drift.
- Orders and Payment Links rejected fractional subunits. This is a negative control that makes the separate Refund API 100.75 to 100 acceptance an inconsistent fail-open path, not normal platform-wide coercion.

Only one-way entity fingerprints are published. Credentials and raw provider identifiers are excluded.
