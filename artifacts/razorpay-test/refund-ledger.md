# Razorpay Test Control-Plane: Redacted Refund Ledger

- Payment status: `refunded`
- Payment amount: `801` subunits
- Provider amount refunded: `801` subunits
- Refund ledger sum: `801` subunits
- All refunds processed: `True`
- Payment fully refunded: `True`
- Fractional request persisted as integer 100: `True`

| Label | Amount | Status | Refund fingerprint | Receipt present |
|---|---:|---|---|---|
| `header-body-mismatch` | `100` | `processed` | `06df37b0eebf` | `False` |
| `receipt-identity` | `100` | `processed` | `937ecd5b4c61` | `True` |
| `reconciled-idempotent-close` | `301` | `processed` | `7676a9d48882` | `False` |
| `refund-fractional-subunit` | `100` | `processed` | `49eb02c30d1c` | `False` |
| `unkeyed-retry-control` | `100` | `processed` | `c0bb2cdb84bc` | `False` |
| `unkeyed-retry-control` | `100` | `processed` | `fe8b2675ffcc` | `False` |

The `refund-fractional-subunit` row is the durable effect of the JSON request amount `100.75` recorded in `refund-identity-matrix.json`: HTTP 200 returned integer amount `100`, and the provider ledger later reached `processed`. Razorpay's current API contract types `amount` as an integer in the currency's smallest unit, so accepting and truncating this value is recorded as a Test control-plane input-validation defect, not as an intentional fractional-currency feature.

Provider identifiers are represented only by one-way fingerprints.
