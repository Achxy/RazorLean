# Razorpay Test Control-Plane: Reconciled Idempotent Close

- Real money: `False`
- Identity mechanism: `header`
- Reconciled remaining amount: `101` subunits
- First request accepted: `False`
- Retry safely identified: `False`
- One refund effect: `False`
- Payment fully refunded: `False`

| Attempt | HTTP | Refund fingerprint | Amount | Status |
|---|---:|---|---:|---|
| first | `400` | `` | `` | `` |
| retry | `400` | `` | `` | `` |

The remaining amount was derived from a fresh provider ledger read. The identical retry used one stable operation identity. Header identity should return the same effect; receipt identity should reject the duplicate. Either behavior must leave exactly one new refund in the ledger.
