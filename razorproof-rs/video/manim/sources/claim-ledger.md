# Film claim-to-source ledger

| Film claim | Evidence class | Source | On-screen boundary |
|---|---|---|---|
| `2.01 × 100` can truncate to `200` in emitted backend paths | dynamically reproduced | `artifacts/expanded/scan.json`, `RP-MCP-GENERATOR-MONEY-UNDERCHARGE` | Small counterexample, not the maximum impact |
| Fixed `×100` maps JPY 295 to 29,500 and KWD 295.990 to 29.599 | dynamic plus Test Mode observed | `RP-MCP-GENERATOR-CURRENCY-EXPONENT` and expanded order contract matrix | Wrong integers were accepted as orders; not paid |
| Browser price is trusted and verification authenticates only the submitted provider tuple | statically confirmed | `RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS` | Paid fulfillment remains inferred |
| Official MCP refund path converts `100.75` to `100` | dynamically reproduced | `RP-MCP-REFUND-TRUNCATION` | Handler/request-path proof |
| Direct Refund API accepted one `100.75` request and persisted `100` | Test Mode observed | `campaign-summary.json` | Inconsistent fail-open; bounded by rejecting control |
| 23 observations, 17 direct defects, 14 dynamic, 4 static, 5 known-public, zero probe errors | executable scan result | expanded scan and claim ledger | Taxonomies shown separately |
| .NET AES-GCM helper deterministically reuses a key-derived nonce | dynamically reproduced | `RP-DOTNET-GCM-NONCE-REUSE` | Critical defect; upstream repair absent |
| .NET/PHP/Java client state violates per-client tenant isolation | dynamically reproduced | three global-state findings | Provider cross-tenant request intentionally not executed |
| 16 non-ASCII signed Test Mode webhooks passed exact UTF-8 and failed the .NET ASCII-equivalent digest | Test Mode observed | `campaign-summary.json` | Reachability proof, redacted bodies |
| Java document upload emits wrong MIME and duplicate file fields | dynamically reproduced | two Java upload findings | Exact local wire body; provider upload unexecuted |
| Six failure chains exist only when every required evidenced node is present | composition rule | `chained-bug-evidence.json` | Unexecuted causal impacts stay labeled inferred |
| RazorProof exposes 113 guarded operations across 20 surfaces and maps 45/45 pinned MCP tools | source-bound implementation | Rust `README.md` and coverage command | Coverage is not dynamic provider execution |
| Current Rust service created a bound 201-subunit Test Mode order and verified four evidence events | Test Mode observed | `artifacts/real-test-mode/e2e.json` | `ORDER CREATED`, not `PAYMENT CAPTURED` |
| Legacy campaign captured two hosted payments and reconciled an 801-subunit fully-refunded fixture | Test Mode observed | `campaign-summary.json` | Separate evidence set |
| Razorpay's dashboard renders the KWD/JPY order pairs, same-receipt duplicates, paid rows, and current bound order | live Test Mode screenshot | `assets/evidence/manifest.json` | Order/payment/customer identifiers are cropped or redacted; amounts and states are untouched |
| Production gates remain | implementation self-assessment | Rust `README.md` | Film names the gates explicitly |
