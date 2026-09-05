# Razorpay Test Control-Plane: Reconciled Idempotent Close

- Real money: `False`
- Reconciled remaining amount: `301` subunits
- Both requests accepted: `True`
- One refund effect: `True`
- Payment fully refunded: `True`

| Attempt | HTTP | Refund fingerprint | Amount | Status |
|---|---:|---|---:|---|
| first | `200` | `7676a9d48882` | `301` | `pending` |
| retry | `200` | `7676a9d48882` | `301` | `pending` |

The remaining amount was derived from a fresh provider ledger read. The identical retry used one `X-Refund-Idempotency` value, so both HTTP responses should identify one refund effect.
