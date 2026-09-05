# Real Razorpay Test Mode receipt

Observed 2026-09-04 through the Rust RazorProof boundary. No live credential or live-money effect was used. Secrets and provider payloads are excluded.

| Field | Observed value |
|---|---|
| Mode | Razorpay Test Mode |
| Local quote | `quote_01a06ad09fbe7f31a5e48aae3165adf0` |
| Exact amount | `201 INR` (₹2.01) |
| Cart hash | `072c2bc636cb80f9b784036e76659dc36cded4f1fc0bd64abdec6e552626030b` |
| Provider order | `order_TXq3ismYFdisza` |
| Provider status | `created` |
| Provider binding | quote id and cart hash present in order notes |
| Evidence events | `4` |
| Verified chain head | `cae406c83021d5e39bea0d778f1af05e3d7af4326f7f139f2fb2354a0288372f` |

This proves Test Mode authentication, a real provider write, exact outbound amount/currency, quote-to-order binding, durable local state, and independent evidence-chain verification. It does **not** prove payment capture, refund movement, settlement, live banking behavior, or all 113 policy operations.

The current local SQLite evidence database is `/private/tmp/razorproof-e2e.db`. It contains fingerprints, hashes, and state transitions rather than the Razorpay key secret. Because `/private/tmp` is ephemeral, the JSON and Markdown receipt in this directory are the durable hackathon artifacts. While the database remains present, verify it with:

```bash
cargo run -q -p razorproof-cli -- verify-evidence \
  --database-url sqlite:///private/tmp/razorproof-e2e.db \
  --tenant hackathon_demo
```
