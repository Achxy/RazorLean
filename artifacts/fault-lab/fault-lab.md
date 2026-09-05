# Lost-response retry fault lab

Fault: **first response dropped after server commit**

- Without effect identity: **2 effects** — `['rfnd_faultlab_1', 'rfnd_faultlab_2']`
- With a stable idempotency key: **1 effect** — `['rfnd_faultlab_1']`

This is a real loopback HTTP exchange: the server commits the first effect, closes the socket before returning a response, and the client retries once. It is a deterministic fault-injection environment, not a Razorpay account. The separate `live-refund` adapter runs the idempotent path against a user-owned Razorpay test account and refuses live keys.
