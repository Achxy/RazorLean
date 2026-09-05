# RazorLean

RazorLean is the repository for RazorProof, a Rust payment-boundary service and its Python research tooling.

- [Rust workspace and service documentation](razorproof-rs/README.md)
- [Architecture](razorproof-rs/docs/ARCHITECTURE.md)
- [Threat model](razorproof-rs/docs/THREAT-MODEL.md)
- [Manim video source](razorproof-rs/video/manim/README.md)

The Rust workspace is in `razorproof-rs/`; run Cargo commands from that directory. The Python package is installed from the repository root. Internal crate and command names remain `razorproof`.

Local credentials, private disclosure drafts, raw provider captures, downloaded repositories, virtual environments and generated media are excluded from Git. Sanitized research reports, public disclosure notes, reproducible evidence bundles and the film's curated evidence images are included. Rendering the narrated film still requires the local Manipal voice model.

Licensed under the [MIT License](LICENSE). Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>. Third-party source and captured images retain their original ownership and are not relicensed by this notice.

## Python research tooling

RazorProof is an executable financial semantic-conformance compiler. It checks properties that ordinary API schema validators, linters and SAST tools do not understand:

- an amount in currency subunits stays an integer and is never silently rounded or truncated;
- a retry that preserves a documented effect identity (`receipt` or idempotency header) cannot create a second economic effect;
- a webhook verifier hashes the exact raw bytes; fixed-time comparison is tracked separately as defensive hardening;
- protocol field order is independent of map insertion order;
- AES-GCM nonces are fresh and cross-SDK wire formats do not drift;
- MCP documentation, JSON Schema, handlers, SDK calls and generated code describe the same interface.

The POC scans clean clones of eight official Razorpay repositories pinned by commit. Evidence strength (`confirmed_dynamic`, `confirmed_static`, `known_public`, or `candidate`) is separate from claim type (`defect`, `compatibility_defect`, `safety_gap`, `hardening`, or `documentation_defect`) so recommendations are not inflated into bugs.

For the least-friction path from local evidence to Razorpay-hosted end-to-end evidence, see [ACCOUNT-TESTING.md](ACCOUNT-TESTING.md). It uses only a truthful unregistered-individual account and Test Mode; no company incorporation or KYC is required for the recommended phase.

## Run

Python 3.11+ is the only base dependency.

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/razorproof repos --clone-missing
.venv/bin/razorproof scan
```

For the strongest black-box probes—official MCP handler through its Go SDK HTTP request path and the official .NET project at runtime—Docker is required:

```bash
.venv/bin/razorproof scan --containers
```

Outputs are written to `artifacts/latest/`:

- `scan.json`: machine-readable evidence;
- `case-report.md`: human-readable technical case;
- `claim-ledger.md`: originality/evidence accounting.

Use `--fail-on critical` or `--fail-on high` to make RazorProof a CI policy gate.

Run the E2E lost-response fault lab:

```bash
.venv/bin/razorproof fault-lab
```

It performs real local HTTP requests, commits a refund-like effect, drops the first response, and retries. The no-key path produces two effects; the stable-key path produces one.

An opt-in live adapter can prove the same invariant on a user-owned Razorpay test account. It refuses live keys and does nothing without the explicit execution flag:

```bash
RAZORPAY_KEY_ID=rzp_test_... RAZORPAY_KEY_SECRET=... \
  .venv/bin/razorproof live-refund --payment-id pay_... --amount 100 --execute-test-mode
```

The full hosted-checkout campaign uses a private `key_id,key_secret` CSV, a private session file, and redacted outputs:

```bash
.venv/bin/razorproof live-orders --credentials-csv /path/to/rzp-key.csv --execute-test-mode
.venv/bin/razorproof live-payment-link --credentials-csv /path/to/rzp-key.csv --amount 801 --execute-test-mode
.venv/bin/razorproof live-refresh --credentials-csv /path/to/rzp-key.csv
.venv/bin/razorproof live-refund-matrix --credentials-csv /path/to/rzp-key.csv --execute-test-mode
.venv/bin/razorproof live-refund-ledger --credentials-csv /path/to/rzp-key.csv
.venv/bin/razorproof webhook-evidence --captures .razorproof/webhook-captures --secret-file .razorproof/webhook-secret
```

The captured run proved two provider-reachable failures: a contract-invalid refund amount `100.75` was accepted and persisted as 100 subunits on one real Test control-plane path, and 16 validly signed literal-UTF-8 webhook deliveries all fail the current .NET SDK's ASCII-equivalent digest. The smaller-balance refund control rejected the same fraction, so RazorProof reports inconsistent fail-open validation rather than universal coercion.

Run the expanded Test Mode, registry-identity, and compositional-chain probes:

```bash
.venv/bin/razorproof live-expanded-orders --credentials-csv /path/to/rzp-key.csv --execute-test-mode
.venv/bin/razorproof mobile-registry-evidence
.venv/bin/razorproof build-chains
```

The expanded campaign reports 23 repository observations plus one Test API defect and composes them into six proof-graded chains. See [the expanded audit](research/expanded-bug-audit/report-source.md), [the chain evidence](artifacts/chains/chained-bug-evidence.md), and [the disclosure ledger](artifacts/disclosure/tracker-ledger.md).

Prove the proposed remediations on disposable clean clones:

```bash
.venv/bin/razorproof prove-fixes --containers
```

This produces a red-to-green evidence bundle without modifying the official source inputs.

## Current crown-jewel counterexample

Razorpay's official MCP checkout integration generator emits `int(amount * 100)` or equivalent into multiple backend languages. Binary float `2.01 * 100` is `200.99999999999997` in common runtimes, so the generated Python, Ruby, PHP, Go, Java, Rust and .NET constructions truncate an intended ₹2.01 order to 200 paise. RazorProof executes the emitted expressions and connects them to the exact pinned template lines.

That is the wedge: the failure is created by an official AI integration tool and then copied into downstream merchant applications. RazorProof catches it before generated code can move money.

## Safety boundary

Default probes are read-only and execute only local official source. Container probes use disposable clean clones and local HTTP interceptors. The opt-in E2E commands are restricted to `rzp_test_` credentials and require `--execute-test-mode` for mutations. No Live Mode transaction is attempted, and credentials, raw payloads, signatures, contact data, and provider IDs stay outside the published artifact bundle.
