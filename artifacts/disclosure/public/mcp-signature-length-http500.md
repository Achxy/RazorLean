## Summary

The generated Node payment-verification route passes attacker-controlled signature text directly to `crypto.timingSafeEqual` without first validating decoded length or encoding. Node throws `ERR_CRYPTO_TIMING_SAFE_EQUAL_LENGTH` for unequal-length buffers, and the generated catch block maps this malformed client input to HTTP 500.

Affected commit: `7950d51d118ca164c32b7cf0cfaa14f34f24849f`

## Reproduction

The generated comparison is:

```js
crypto.timingSafeEqual(
  Buffer.from(expectedSignature),
  Buffer.from(razorpay_signature)
)
```

Execute it with a normal 64-character expected HMAC and an untrusted one-character submitted signature. The exact generated operation produces:

```json
{
  "accepted": false,
  "error_name": "RangeError",
  "error_code": "ERR_CRYPTO_TIMING_SAFE_EQUAL_LENGTH"
}
```

The surrounding generated catch block responds with status 500 and `Payment verification failed`.

## Expected

Malformed signature length or encoding should fail closed as a controlled 400 response. It should not throw into the route's internal-error path.

## Suggested fix

- Require exactly 64 hexadecimal characters before comparison.
- Decode both values to equal-length bytes.
- Return 400 for invalid encoding/length and 401/400 for a validly shaped mismatch, according to the project's chosen error contract.
- Add one-character, odd-length, non-hex, empty, correct-length mismatch, and correct-signature fixtures.

This is reported as a low-severity robustness and error-contract defect, not as a denial-of-service vulnerability.
