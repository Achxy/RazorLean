# RazorProof voiceover cue sheet

This is the long-form editorial narration. The generated `Manipal` take uses the tighter, frame-derived wording in `mimika_timeline.json`; its matching production captions are in `razorproof_pitch.srt`. Read the human story first and let each screenshot remain on screen long enough for the order amount or payment state to be inspected.

## 00:00-00:44 | Alice's ₹2.01 order

Alice sells Bob a tiny add-on for two rupees and one paisa. Bob clicks buy. The integration reports success, so Alice has no reason to suspect anything.

Now read the provider's own dashboard. The order ID is visible. Its amount is two rupees, not two rupees and one paisa. There was no API error and no warning. The wrong value became a perfectly valid order.

Only after seeing the consequence do we open the generated integration code. It takes a decimal amount, multiplies it by one hundred, and converts it to an integer. On the running language path, `2.01 times 100` is represented just below 201. The integer conversion truncates it to 200. We executed that expression and sent its output to Razorpay. The dashboard preserved exactly what arrived.

Nothing crashed. Alice's order was silently changed.

## 00:44-01:22 | What the green check cannot prove

Bob can still receive a valid payment signature. He can truthfully say, “I paid the order you sent.” Alice's harder question is whether that order still expresses the purchase she intended.

The generated verifier authenticates an order ID joined to a payment ID. That is useful proof, but it answers only whether this payment belongs to this order.

Alice's economic promise also contained the seller, amount, currency, cart and permitted effect. Those coordinates disappear before verification. A valid payment can therefore settle an order whose business meaning changed earlier. This is not Razorpay forging a payment. It is an integration losing intent before Razorpay has any way to recover it.

## 01:22-01:58 | The currency changes the size of the failure

Alice takes the same checkout abroad. One Bob is charged in Japanese yen; another in Kuwaiti dinar. The code still multiplies both values by one hundred.

The four visible order IDs are real provider orders from the experiment. The correct JPY order is 295. The generated path records 29,500, one hundred times too large. The correct KWD order is 295.990. The generated path records 29.599, one tenth of the intended amount.

JPY has zero decimal places, INR has two, and KWD has three. A fixed multiplier is not a money model. The one-paisa opening bug is only the smallest member of a much more severe class.

## 01:58-02:34 | Bob paid; Alice's app says failed

Next Bob pays on his phone. The provider dashboard independently shows a captured payment, including its payment and order IDs.

Now inspect the generated mobile client. Its success payload forwards the order ID and payment ID, but supplies an empty signature to the generated verifier. The backend must reject that proof.

The captured payment and generated client snippet are independently observed evidence; we do not claim this exact payment ran through that client. Together they expose the failure shape: money can be captured outside while the application records failure inside. Bob says paid. Alice says failed. Fulfilment and support now disagree about reality.

## 02:34-03:14 | A refund splits into multiple meanings

Alice owes Bob a refund and intends one effect. A malformed request carries `100.75` subunits. In one funded provider path, the request is accepted and the persisted refund amount becomes 100 with processed status. A smaller-balance control rejected the same fractional shape, so the precise defect is inconsistent validation, not a universal conversion rule.

Then the response disappears and Alice retries. Without a stable effect identity, the provider creates two distinct processed refunds: `rfnd_TXVxKDFRx3nCqK` and `rfnd_TXVxMimmkZAB5W`. That is documented request behavior; the integration defect is allowing one human intention to reach it as two unrelated effects.

The payment drawer ends in refunded state, but provider success cannot tell Alice which human intention each retry represented.

Finally, a signed refund webhook includes the rupee symbol and Malayalam text. We replayed sixteen literal non-ASCII deliveries. Verification over the untouched UTF-8 body passed all sixteen. Re-encoding the body through the ASCII helper failed all sixteen. Authenticate the original bytes first; parse only afterwards.

## 03:14-04:01 | Make Alice's promise executable

RazorProof introduces one typed PaymentIntent before any provider call. It carries exact integer subunits, currency, Alice and Bob's identities, one permitted effect, and the original callback evidence required later.

At the outbound boundary, Alice's promised 201 subunits are compared with the request's 200. The mismatch is rejected before Razorpay receives it. A silent undercharge becomes an immediate, reproducible failure.

After Bob pays, success is not a browser message. The service moves through quoted, ordered, provider-re-fetched captured, and fulfilled-once states. Every transition consumes and preserves the same intent.

The implementation is a Rust semantic firewall across four boundaries: currency-aware money conversion, provider reconciliation before fulfilment, stable identity for retries, and raw-byte webhook authentication. It is not a replacement checkout. It is the layer that prevents every integration surface from inventing a different meaning.

## 04:01-04:28 | Read the proof, not our claims

Run the broken and protected INR paths side by side. The dashboard shows two different order IDs: two rupees through the generated floating-point boundary, and two rupees and one paisa through the exact integer boundary.

Repeat the experiment across JPY and KWD. Correct and corrupted amounts coexist in the provider's own order table. Captured and refunded states remain separately visible in the payment surface.

Every central claim in this film is therefore replayable against Razorpay: the request, the resulting provider object, and the boundary decision that either allowed or blocked it.

## 04:28-04:43 | Close

Alice asked for two rupees and one paisa. Bob paid two rupees and one paisa. The purchase happened once.

RazorProof: the meaning Alice sets is the meaning Bob pays.
