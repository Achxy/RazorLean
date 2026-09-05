## Summary

The generated Android, iOS, Cordova, and native Capacitor Orders API flows do not preserve `razorpay_signature`, but send their success result to a generated backend endpoint that requires the signature. A customer can complete payment and then deterministically reach the generated application's verification failure path.

Affected commit: `7950d51d118ca164c32b7cf0cfaa14f34f24849f`

## Reproduction from generated source

1. Generate the Android integration. It implements `PaymentResultListener`, whose success callback supplies only `payment_id`, then builds the verification body with `put("razorpay_signature", "")`.
2. Generate the iOS integration. It implements `RazorpayPaymentCompletionProtocol`, whose success callback supplies only `payment_id`, then sends `"razorpay_signature": ""`.
3. Generate Cordova or Capacitor-native. Their legacy success callbacks preserve only `payment_id` (and the locally remembered order ID), omitting `razorpay_signature`.
4. Send any of those generated bodies to any generated backend `/verify` route. The route rejects because `razorpay_signature` is missing or empty.

Relevant source:

- `pkg/razorpay/integrations/mobile.go`: Android empty signature near the generated `verifyPayment` body.
- `pkg/razorpay/integrations/mobile.go`: iOS empty signature near the generated `verifyPayment` body.
- `pkg/razorpay/integrations/mobile.go`: Cordova and Capacitor native callback shapes omit the signature.
- `pkg/razorpay/integrations/backend_node.go`: generated verification route requires all three fields.

The Razorpay Android documentation distinguishes `PaymentResultListener` (payment ID only) from `PaymentResultWithDataListener` (order ID, payment ID, signature, and other data). The official Cordova Orders API flow likewise uses the `payment.success` object containing the signed fields.

## Expected

Every generated Orders API success path should preserve and submit `razorpay_order_id`, `razorpay_payment_id`, and `razorpay_signature`, so mandatory backend verification can succeed.

## Suggested fix

- Android: use `PaymentResultWithDataListener` and `PaymentData`.
- iOS: use `RazorpayPaymentCompletionProtocolWithData`.
- Cordova/Capacitor: use the official Orders-flow `payment.success` event/object rather than the payment-ID-only legacy callback.
- Add generated-fixture tests asserting that every mobile success payload contains all three non-empty signed fields.

This is a functional correctness report. It does not include or depend on any live credentials or payment data.
