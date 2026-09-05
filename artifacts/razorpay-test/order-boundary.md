# Razorpay Test Control-Plane: Order Boundary

- Evidence scope: `razorpay-test-control-plane`
- Real money: `False`
- All expectations met: `False`
- Documented minimum `10` mismatch: `True`
- Observed INR minimum boundary `100`: `True`
- Key fingerprint only: `0bb387c233eb`

| Vector | Requested | Expected | HTTP | Accepted | Persisted | Result |
|---|---:|---|---:|---|---:|---|
| `below_documented_minimum` | `9` | `reject` | `400` | `False` | `` | `pass` |
| `documented_minimum` | `10` | `accept` | `400` | `False` | `` | `FAIL` |
| `observed_below_minimum` | `99` | `reject` | `400` | `False` | `` | `pass` |
| `observed_minimum` | `100` | `accept` | `200` | `True` | `100` | `pass` |
| `observed_minimum_plus_one` | `101` | `accept` | `200` | `True` | `101` | `pass` |
| `generated_2_01_truncation` | `200` | `accept` | `200` | `True` | `200` | `pass` |
| `exact_2_01_control` | `201` | `accept` | `200` | `True` | `201` | `pass` |
| `fractional_subunit` | `100.75` | `reject` | `400` | `False` | `` | `pass` |

Razorpay's current Create Order error documentation states that the minimum amount is `10`, but the Test control plane rejected 10 and 99 and accepted 100 and 101. The official MCP server also declares a minimum of 100. This is recorded as a Test-control-plane/documentation mismatch; it is not represented as a payment-processing defect.

The generated-code vector is intentionally labelled by upstream intent: the official template expression `int(2.01 * 100)` produces 200, and Razorpay's Test API faithfully persists the submitted 200. The exact-decimal control submits and persists 201. This proves the undercharge reaches Razorpay's real Test control plane; it does not imply the Orders API caused the arithmetic error.

Entity identifiers are stored only as one-way fingerprints. No API secret is written to this bundle.
