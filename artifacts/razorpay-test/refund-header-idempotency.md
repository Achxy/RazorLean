# Razorpay Test Control-Plane: Refund Header Idempotency

- Real money: `False`
- Requests accepted: `True`
- One refund effect: `True`
- Amount preserved: `True`
- Payment fingerprint: `68d6a3c27450`

| Attempt | HTTP | Accepted | Refund fingerprint | Amount | Status |
|---:|---:|---|---|---:|---|
| `1` | `200` | `True` | `a7cc768ba08f` | `100` | `pending` |
| `2` | `200` | `True` | `a7cc768ba08f` | `100` | `pending` |

This is a Razorpay Test Mode control-plane result. Repeating the same body with the same `X-Refund-Idempotency` value should return the same refund identity and create one effect. It validates the provider mechanism and supports classifying missing exposure in a wrapper as a safety/discoverability gap rather than a broken Razorpay refund API.

Only one-way entity fingerprints are published. Credentials and raw provider identifiers remain in the private ignored session file.
