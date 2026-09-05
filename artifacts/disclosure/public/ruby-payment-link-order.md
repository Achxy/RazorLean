## Summary

`Utility.verify_payment_link_signature` builds the signed payload from `attributes.values.join('|')` after deleting the signature. Verification therefore depends on Ruby Hash insertion order and also incorporates unrelated extra fields.

Affected commit: `807e80eb25572823ebb1872529747fb9af97282e`

## Reproduction

Using the same four fields and the same correct HMAC:

```text
docs-order hash: accepted
same key/value set inserted in another order: SecurityError
```

The protocol-defined message order is:

```text
payment_link_id|payment_link_reference_id|payment_link_status|razorpay_payment_id
```

The current implementation instead signs every remaining value in caller-container order.

## Expected

Verification should select the four required named fields in protocol order. Hash construction order and unrelated callback fields must not affect authenticity.

## Suggested fix

- Validate the complete required field set.
- Build the message from the four explicit keys in the documented order.
- Do not mutate the caller's Hash.
- Add tests that permute insertion order, include benign extra fields, omit each required field, and alter one signed value.

This report uses locally generated IDs and signatures only; no account access is required.
