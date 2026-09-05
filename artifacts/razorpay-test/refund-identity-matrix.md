# Razorpay Test Control-Plane: Refund Identity Matrix

- Real money: `False`
- Below ₹1.00 rejected: `True`
- Fractional subunit rejected: `False`
- Over-refund rejected: `True`
- Same header with changed body rejected: `True`
- Duplicate receipt prevented: `True`
- Unkeyed retry created two effects: `True`
- Final full-refund retry produced one effect: `False`
- Payment fully refunded: `False`

| Scenario | First HTTP | Retry HTTP | First effect | Retry effect | Interpretation |
|---|---:|---:|---|---|---|
| same header, changed body | `200` | `409` | `06df37b0eebf` | `` | conflicting reuse rejected |
| stable receipt | `200` | `400` | `937ecd5b4c61` | `` | duplicate prevented |
| no operation identity | `200` | `200` | `fe8b2675ffcc` | `c0bb2cdb84bc` | two distinct refund intents |
| same header, full-refund retry | `400` | `400` | `` | `` | one final refund effect |

The fractional boundary request sent `100.75`, returned HTTP `200`, and the provider returned amount `100`. Because the official contract requires an integer, HTTP 200 plus persisted 100 is a silent-coercion defect; it is not a successful boundary rejection.

The unkeyed result is intentional provider behavior: without an operation identity, two requests represent two refund intents. The defect claim belongs only to wrappers or agent tools that hide the available identity mechanisms while encouraging automatic retries.

Provider entity identifiers are represented only by one-way fingerprints.
