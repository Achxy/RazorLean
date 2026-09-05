## Summary

The .NET SDK computes webhook HMACs through a shared `ASCIIEncoding` helper. Razorpay signs the exact raw UTF-8 request body, so a valid webhook containing literal non-ASCII data is rejected by `Utils.verifyWebhookSignature`.

Affected commit: `2cd38a155ec56ea47e879a573a3acb19334c152e`

## Minimal reproduction

1. Use payload `{"name":"Achu ₹ മലയാളം"}`.
2. Compute HMAC-SHA256 with UTF-8 payload bytes and any test secret.
3. Call `Utils.verifyWebhookSignature(payload, signature, secret)`.
4. The official SDK throws `SignatureVerificationError` because `StringEncode` replaces non-ASCII characters before hashing.

Relevant source: `src/Utils.cs`, where `StringEncode` constructs `new ASCIIEncoding()` and is used by `getActualSignature`.

## Provider reachability evidence

I also captured 22 Razorpay Test Mode deliveries over HTTPS across payment, payment-link, and refund event types. Sixteen bodies contained literal non-ASCII metadata. For every one of those 16:

- the webhook header matched HMAC-SHA256 over the exact raw body bytes;
- a UTF-8 string round-trip produced the same digest;
- the .NET SDK's ASCII-equivalent byte transformation produced a different digest.

This closes the usual caveat that JSON might always escape Unicode: current Test Mode deliveries can contain literal UTF-8 values in ordinary notes and descriptions.

## Expected

Valid Razorpay webhook bodies should verify byte-for-byte regardless of the scripts or symbols present in metadata.

## Suggested fix

- Add a `byte[]`/`ReadOnlySpan<byte>` verification API for raw request bodies.
- Make the string compatibility overload use `Encoding.UTF8` explicitly.
- Add literal `₹`, Malayalam, and emoji fixtures, plus a one-byte mutation negative control.

No raw webhook body, signature, secret, contact data, or provider entity ID is included in this report.
