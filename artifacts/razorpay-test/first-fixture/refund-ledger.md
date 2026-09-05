# Razorpay Test Control-Plane: Redacted Refund Ledger

- Payment status: `captured`
- Payment amount: `201` subunits
- Provider amount refunded: `100` subunits
- Refund ledger sum: `100` subunits
- All refunds processed: `True`
- Payment fully refunded: `False`
- Fractional request persisted as integer 100: `False`

| Label | Amount | Status | Refund fingerprint | Receipt present |
|---|---:|---|---|---|
| `header-idempotency-e2e` | `100` | `processed` | `a7cc768ba08f` | `False` |

The `refund-fractional-subunit` row is the durable effect of the JSON request amount `100.75` recorded in `refund-identity-matrix.json`: HTTP 200 returned integer amount `100`, and the provider ledger later reached `processed`. Razorpay's current API contract types `amount` as an integer in the currency's smallest unit, so accepting and truncating this value is recorded as a Test control-plane input-validation defect, not as an intentional fractional-currency feature.

Provider identifiers are represented only by one-way fingerprints.
