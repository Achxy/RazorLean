#![doc = "Source, generated-code, registry, and chain conformance engine."]
// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

use std::{
    collections::{BTreeMap, BTreeSet},
    fmt::Write as _,
    fs,
    path::Path,
};

use serde::{Deserialize, Serialize};
use thiserror::Error;
use time::OffsetDateTime;
use walkdir::WalkDir;

const MAX_SOURCE_BYTES: u64 = 4 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Severity {
    Low,
    Medium,
    High,
    Critical,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ClaimKind {
    Defect,
    Compatibility,
    KnownPublic,
    Observation,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct SourceEvidence {
    pub path: String,
    pub line: usize,
    pub matched: String,
    pub source_hash: String,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct Finding {
    pub id: String,
    pub title: String,
    pub repository: String,
    pub invariant: String,
    pub severity: Severity,
    pub claim_kind: ClaimKind,
    pub evidence: Vec<SourceEvidence>,
    pub remediation: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ScanReport {
    #[serde(with = "time::serde::timestamp")]
    pub generated_at: OffsetDateTime,
    pub root: String,
    pub files_scanned: usize,
    pub bytes_scanned: u64,
    pub findings: Vec<Finding>,
    pub findings_by_severity: BTreeMap<String, usize>,
    pub direct_defects: usize,
    pub detector_count: usize,
    pub chains: Vec<FailureChain>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct FailureChain {
    pub id: String,
    pub title: String,
    pub component_findings: Vec<String>,
    pub consequence: String,
    pub demonstration: String,
}

impl ScanReport {
    #[must_use]
    pub fn to_markdown(&self) -> String {
        let mut output = format!(
            "# RazorProof conformance report\n\nScanned `{}` files ({} bytes) with {} semantic detectors. Found {} findings, including {} direct defects.\n\n",
            self.files_scanned,
            self.bytes_scanned,
            self.detector_count,
            self.findings.len(),
            self.direct_defects
        );
        output.push_str("| ID | Severity | Classification | Evidence |\n|---|---|---|---|\n");
        for finding in &self.findings {
            let location = finding
                .evidence
                .first()
                .map_or("no source location".to_owned(), |item| {
                    format!("{}:{}", item.path, item.line)
                });
            let _ = writeln!(
                output,
                "| `{}` | `{:?}` | `{:?}` | {} |",
                finding.id, finding.severity, finding.claim_kind, location
            );
        }
        output.push_str("\n## Remediations\n\n");
        for finding in &self.findings {
            let _ = write!(
                output,
                "### {}\n\n{}\n\nInvariant: {}\n\nFix: {}\n\n",
                finding.id, finding.title, finding.invariant, finding.remediation
            );
        }
        output.push_str("\n## Compositional failure chains\n\n");
        for chain in &self.chains {
            let _ = write!(
                output,
                "### {}\n\n{}\n\nComponents: `{}`\n\nDemonstration: {}\n\n",
                chain.id,
                chain.consequence,
                chain.component_findings.join("`, `"),
                chain.demonstration
            );
        }
        output
    }
}

#[derive(Clone, Copy)]
struct Probe {
    path_suffix: &'static str,
    needle: &'static str,
}

struct Detector {
    id: &'static str,
    title: &'static str,
    repository: &'static str,
    invariant: &'static str,
    severity: Severity,
    claim_kind: ClaimKind,
    requirements: Vec<Vec<Probe>>,
    remediation: &'static str,
}

#[derive(Clone)]
struct SourceFile {
    relative_path: String,
    contents: String,
    hash: String,
}

pub fn scan_repositories(root: impl AsRef<Path>) -> Result<ScanReport, EngineError> {
    let root = root.as_ref();
    let mut files = Vec::new();
    let mut bytes_scanned = 0_u64;
    for entry in WalkDir::new(root).follow_links(false) {
        let entry = entry?;
        if !entry.file_type().is_file() || is_ignored(entry.path()) {
            continue;
        }
        let metadata = entry.metadata()?;
        if metadata.len() > MAX_SOURCE_BYTES || !is_source(entry.path()) {
            continue;
        }
        let bytes = fs::read(entry.path())?;
        let Ok(contents) = String::from_utf8(bytes) else {
            continue;
        };
        bytes_scanned = bytes_scanned.saturating_add(metadata.len());
        let relative_path = entry
            .path()
            .strip_prefix(root)
            .unwrap_or(entry.path())
            .to_string_lossy()
            .replace('\\', "/");
        files.push(SourceFile {
            relative_path,
            hash: blake3::hash(contents.as_bytes()).to_hex().to_string(),
            contents,
        });
    }

    let detectors = detectors();
    let mut findings = Vec::new();
    for detector in &detectors {
        let mut evidence = Vec::new();
        let mut satisfied = true;
        for alternatives in &detector.requirements {
            let mut group_evidence = Vec::new();
            for probe in alternatives {
                group_evidence.extend(find_probe(&files, *probe));
            }
            if group_evidence.is_empty() {
                satisfied = false;
                break;
            }
            evidence.extend(group_evidence);
        }
        if satisfied {
            evidence.sort_by(|left, right| {
                (&left.path, left.line, &left.matched).cmp(&(
                    &right.path,
                    right.line,
                    &right.matched,
                ))
            });
            evidence.dedup_by(|left, right| {
                left.path == right.path && left.line == right.line && left.matched == right.matched
            });
            findings.push(Finding {
                id: detector.id.to_owned(),
                title: detector.title.to_owned(),
                repository: detector.repository.to_owned(),
                invariant: detector.invariant.to_owned(),
                severity: detector.severity,
                claim_kind: detector.claim_kind,
                evidence,
                remediation: detector.remediation.to_owned(),
            });
        }
    }
    findings.sort_by(|left, right| {
        right
            .severity
            .cmp(&left.severity)
            .then_with(|| left.id.cmp(&right.id))
    });
    let direct_defects = findings
        .iter()
        .filter(|finding| finding.claim_kind == ClaimKind::Defect)
        .count();
    let mut findings_by_severity = BTreeMap::new();
    for finding in &findings {
        *findings_by_severity
            .entry(format!("{:?}", finding.severity).to_ascii_lowercase())
            .or_insert(0) += 1;
    }
    let chains = compile_chains(&findings);
    Ok(ScanReport {
        generated_at: OffsetDateTime::now_utc(),
        root: root.to_string_lossy().into_owned(),
        files_scanned: files.len(),
        bytes_scanned,
        findings,
        findings_by_severity,
        direct_defects,
        detector_count: detectors.len(),
        chains,
    })
}

fn compile_chains(findings: &[Finding]) -> Vec<FailureChain> {
    let present = findings
        .iter()
        .map(|finding| finding.id.as_str())
        .collect::<BTreeSet<_>>();
    let definitions = [
        (
            "CHAIN-REFUND-MUTATION-RETRY-OBSERVABILITY",
            "A malformed refund is silently changed, then lacks a stable retry identity",
            &["RP-MCP-REFUND-TRUNCATION", "RP-MCP-REFUND-IDEMPOTENCY"][..],
            "A network interruption after acceptance can leave both the sent amount and effect identity uncertain.",
            "Intercept the provider request, submit 100.75 twice around a forced disconnect, and compare request bodies and refund IDs.",
        ),
        (
            "CHAIN-CHECKOUT-ECONOMIC-DECOUPLING",
            "Browser authority, binary floats, and a fixed exponent decouple charge from catalog price",
            &[
                "RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS",
                "RP-MCP-GENERATOR-MONEY-UNDERCHARGE",
                "RP-MCP-GENERATOR-CURRENCY-EXPONENT",
            ][..],
            "A fresh generated checkout can accept a tampered or mis-scaled amount and still produce a validly signed provider payment.",
            "Generate the integration, change the browser amount, and run INR 2.01, JPY 295, and KWD 295.990 controls against captured outbound orders.",
        ),
        (
            "CHAIN-MOBILE-PAID-BUT-FAILED",
            "Mobile success loses the signature required by the generated server verifier",
            &["RP-MCP-MOBILE-MISSING-SIGNATURE"][..],
            "The provider can report success while the merchant cannot complete its generated verification path.",
            "Run each generated success callback and assert that the signed payment tuple reaches the server intact.",
        ),
        (
            "CHAIN-CROSS-TENANT-ROUTING",
            "Process-wide SDK state can redirect concurrent tenant traffic",
            &[
                "RP-DOTNET-GLOBAL-AUTH-STATE",
                "RP-PHP-GLOBAL-AUTH-STATE",
                "RP-JAVA-GLOBAL-PARTNER-HEADERS",
            ][..],
            "Creating or mutating one client can change credentials or partner routing used by another client in the same process.",
            "Instantiate tenants A and B, interleave requests through a capture server, and assert every Authorization and X-Razorpay-Account pair.",
        ),
        (
            "CHAIN-JAVA-DOCUMENT-WIRE-CORRUPTION",
            "Java document serialization combines a wrong MIME with duplicate file parts",
            &["RP-JAVA-UPLOAD-MIME", "RP-JAVA-UPLOAD-DUPLICATE-FILE-PART"][..],
            "An otherwise valid JPG or PNG can reach the document endpoint as an ambiguous multipart body.",
            "Capture the multipart request and assert one binary file part whose Content-Type matches its magic bytes.",
        ),
        (
            "CHAIN-MOBILE-PACKAGE-IDENTITY",
            "Generated payment code crosses into an unrelated package namespace",
            &["RP-MCP-MOBILE-DEPENDENCY-CONFUSION"][..],
            "A copy-pasted integration depends on an identity outside Razorpay's documented package boundary.",
            "Resolve the generated coordinates against the live registries and compare publisher, contents, and official documentation.",
        ),
    ];
    definitions
        .into_iter()
        .filter(|(_, _, components, _, _)| {
            components
                .iter()
                .all(|component| present.contains(component))
        })
        .map(
            |(id, title, component_findings, consequence, demonstration)| FailureChain {
                id: id.to_owned(),
                title: title.to_owned(),
                component_findings: component_findings
                    .iter()
                    .map(|value| (*value).to_owned())
                    .collect(),
                consequence: consequence.to_owned(),
                demonstration: demonstration.to_owned(),
            },
        )
        .collect()
}

fn find_probe(files: &[SourceFile], probe: Probe) -> Vec<SourceEvidence> {
    let mut matches = Vec::new();
    for file in files
        .iter()
        .filter(|file| file.relative_path.ends_with(probe.path_suffix))
    {
        for (index, line) in file.contents.lines().enumerate() {
            if line.contains(probe.needle) {
                matches.push(SourceEvidence {
                    path: file.relative_path.clone(),
                    line: index + 1,
                    matched: line.trim().chars().take(240).collect(),
                    source_hash: file.hash.clone(),
                });
            }
        }
    }
    matches
}

fn is_ignored(path: &Path) -> bool {
    path.components().any(|component| {
        matches!(
            component.as_os_str().to_str(),
            Some(".git" | "target" | "node_modules" | "vendor" | "dist" | "build")
        )
    })
}

fn is_source(path: &Path) -> bool {
    let extensions = BTreeSet::from([
        "cs", "go", "java", "js", "kt", "m", "php", "py", "rb", "rs", "swift", "ts",
    ]);
    path.extension()
        .and_then(|value| value.to_str())
        .is_some_and(|extension| extensions.contains(extension))
}

fn p(path_suffix: &'static str, needle: &'static str) -> Probe {
    Probe {
        path_suffix,
        needle,
    }
}

fn one(probe: Probe) -> Vec<Vec<Probe>> {
    vec![vec![probe]]
}

// Keeping the detector registry declarative makes every source-bound rule auditable in one place.
#[allow(clippy::too_many_lines)]
fn detectors() -> Vec<Detector> {
    let mut rules = vec![
        Detector {
            id: "RP-DOTNET-GCM-NONCE-REUSE",
            title: ".NET onboarding encryption derives a reusable AES-GCM nonce from the key",
            repository: "razorpay-dot-net",
            invariant: "An AES-GCM key and nonce pair must never be reused.",
            severity: Severity::Critical,
            claim_kind: ClaimKind::Defect,
            requirements: one(p(
                "razorpay-dot-net/src/Utils.cs",
                "Array.Copy(keyBytes, 0, iv, 0, 12)",
            )),
            remediation: "Generate a fresh random 96-bit nonce for every encryption and carry it with the ciphertext.",
        },
        Detector {
            id: "RP-MCP-GENERATOR-MONEY-UNDERCHARGE",
            title: "Generated checkout backends convert binary floating point money by truncation",
            repository: "razorpay-mcp-server",
            invariant: "Major-to-minor conversion must be decimal-exact and must produce an integer.",
            severity: Severity::High,
            claim_kind: ClaimKind::Defect,
            requirements: vec![vec![
                p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/backend_python.go",
                    "int(amount * 100)",
                ),
                p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/backend_go.go",
                    "int(req.Amount * 100)",
                ),
                p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/backend_java.go",
                    "(int) (amount * 100)",
                ),
                p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/backend_other.go",
                    "(amount * 100).to_i",
                ),
            ]],
            remediation: "Accept integer subunits or exact decimal strings and convert with a currency-aware decimal type.",
        },
        Detector {
            id: "RP-MCP-GENERATOR-CURRENCY-EXPONENT",
            title: "Generated checkout hard-codes a two-decimal currency exponent",
            repository: "razorpay-mcp-server",
            invariant: "Currency exponent and provider quantum are properties of the currency, not a universal constant.",
            severity: Severity::High,
            claim_kind: ClaimKind::Defect,
            requirements: vec![
                vec![p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go",
                    "currency = 'INR'",
                )],
                vec![p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go",
                    "Math.round(amount * 100)",
                )],
            ],
            remediation: "Resolve exponent and quantum from an audited currency table and reject unsupported precision.",
        },
        Detector {
            id: "RP-MCP-GENERATOR-UNTRUSTED-ECONOMICS",
            title: "Generated checkout lets the browser author the order amount",
            repository: "razorpay-mcp-server",
            invariant: "The merchant server must derive amount, currency, and cart identity from trusted catalog state.",
            severity: Severity::High,
            claim_kind: ClaimKind::Defect,
            requirements: vec![
                vec![p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/frontend_templates.go",
                    "JSON.stringify({ amount })",
                )],
                vec![p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go",
                    "const { amount, currency",
                )],
            ],
            remediation: "Replace browser-authored prices with a short-lived, server-valued quote bound to the provider order.",
        },
        Detector {
            id: "RP-MCP-MOBILE-MISSING-SIGNATURE",
            title: "Generated mobile success paths discard the payment signature",
            repository: "razorpay-mcp-server",
            invariant: "Every client success callback must pass the payment, order, and signature tuple to server verification.",
            severity: Severity::High,
            claim_kind: ClaimKind::Defect,
            requirements: vec![vec![
                p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/mobile.go",
                    "put(\"razorpay_signature\", \"\")",
                ),
                p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/mobile.go",
                    "\"razorpay_signature\": \"\"",
                ),
            ]],
            remediation: "Use SDK success objects that contain the full signed tuple and fail closed when any field is absent.",
        },
        Detector {
            id: "RP-MCP-MOBILE-DEPENDENCY-CONFUSION",
            title: "Generated mobile setup installs a non-official package identity",
            repository: "razorpay-mcp-server",
            invariant: "Payment code generators must pin packages controlled and documented by the provider.",
            severity: Severity::High,
            claim_kind: ClaimKind::Defect,
            requirements: vec![vec![
                p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/mobile.go",
                    "com.nicholaswilliams.nicepay.razorpay",
                ),
                p(
                    "razorpay-mcp-server/pkg/razorpay/integrations/mobile.go",
                    "cordova-plugin-razorpay",
                ),
            ]],
            remediation: "Generate only the official package coordinates and continuously verify their publisher and registry state.",
        },
        Detector {
            id: "RP-DOTNET-GLOBAL-AUTH-STATE",
            title: ".NET client instances share process-wide credential state",
            repository: "razorpay-dot-net",
            invariant: "Credentials and routing headers must be immutable per client instance.",
            severity: Severity::High,
            claim_kind: ClaimKind::Defect,
            requirements: vec![
                vec![p(
                    "razorpay-dot-net/src/RazorpayClient.cs",
                    "private static string key",
                )],
                vec![p(
                    "razorpay-dot-net/src/RestClient.cs",
                    "RazorpayClient.Key",
                )],
            ],
            remediation: "Move credentials and headers into immutable instance state and inject them into each request.",
        },
        Detector {
            id: "RP-PHP-GLOBAL-AUTH-STATE",
            title: "PHP client instances share process-wide credentials and headers",
            repository: "razorpay-php",
            invariant: "Credentials and routing headers must be immutable per client instance.",
            severity: Severity::High,
            claim_kind: ClaimKind::Defect,
            requirements: vec![
                vec![p("razorpay-php/src/Api.php", "protected static $key")],
                vec![p("razorpay-php/src/Request.php", "Api::getKey()")],
            ],
            remediation: "Use instance-owned authentication and request headers without static mutation.",
        },
        Detector {
            id: "RP-JAVA-GLOBAL-PARTNER-HEADERS",
            title: "Java clients share one process-wide partner-routing map",
            repository: "razorpay-java",
            invariant: "Submerchant routing must be immutable per client and cannot bleed across tenants.",
            severity: Severity::High,
            claim_kind: ClaimKind::Defect,
            requirements: vec![
                vec![p(
                    "razorpay-java/src/main/java/com/razorpay/ApiUtils.java",
                    "static Map<String, String> headers",
                )],
                vec![p(
                    "razorpay-java/src/main/java/com/razorpay/RazorpayClient.java",
                    "ApiUtils.addHeaders(headers)",
                )],
            ],
            remediation: "Construct request-local headers from immutable client-owned partner context.",
        },
        Detector {
            id: "RP-MCP-REFUND-TRUNCATION",
            title: "Refund MCP tool silently truncates a fractional subunit amount",
            repository: "razorpay-mcp-server",
            invariant: "Subunit money is integer-valued and invalid fractions must be rejected, never changed.",
            severity: Severity::Medium,
            claim_kind: ClaimKind::Defect,
            requirements: vec![
                vec![p(
                    "razorpay-mcp-server/pkg/razorpay/refunds.go",
                    "ValidateAndAddRequiredFloat",
                )],
                vec![p(
                    "razorpay-mcp-server/pkg/razorpay/refunds.go",
                    "int(payload[\"amount\"].(float64))",
                )],
            ],
            remediation: "Validate an int64 at the MCP boundary and reject fractional JSON values.",
        },
        Detector {
            id: "RP-MCP-EXPAND-COLLAPSE",
            title: "Repeated expand query parameters collapse into one value",
            repository: "razorpay-mcp-server",
            invariant: "A repeated query parameter must retain every caller-supplied value.",
            severity: Severity::Medium,
            claim_kind: ClaimKind::Defect,
            requirements: one(p(
                "razorpay-mcp-server/pkg/razorpay/tools_params.go",
                "params[\"expand[]\"] = val",
            )),
            remediation: "Represent repeated parameters as a multi-value query and append rather than overwrite.",
        },
        Detector {
            id: "RP-DOTNET-WEBHOOK-ASCII",
            title: ".NET webhook verifier hashes Unicode payloads as ASCII",
            repository: "razorpay-dot-net",
            invariant: "Webhook HMAC verification must hash the exact UTF-8 bytes received from the network.",
            severity: Severity::Medium,
            claim_kind: ClaimKind::Defect,
            requirements: one(p("razorpay-dot-net/src/Utils.cs", "new ASCIIEncoding()")),
            remediation: "Accept raw bytes; if a string boundary is unavoidable, use strict UTF-8 without reserialization.",
        },
        Detector {
            id: "RP-RUBY-PAYLINK-ORDER",
            title: "Ruby payment-link verification depends on hash insertion order",
            repository: "razorpay-ruby",
            invariant: "Signature preimages must use named fields in the documented order.",
            severity: Severity::Medium,
            claim_kind: ClaimKind::Defect,
            requirements: one(p(
                "razorpay-ruby/lib/razorpay/utility.rb",
                "attributes.values.join('|')",
            )),
            remediation: "Construct the preimage from explicitly named fields in a constant documented order.",
        },
        Detector {
            id: "RP-JAVA-UPLOAD-MIME",
            title: "Java document upload maps image extensions to an invalid PDF MIME",
            repository: "razorpay-java",
            invariant: "Multipart Content-Type must match both the extension and file magic bytes.",
            severity: Severity::Medium,
            claim_kind: ClaimKind::Defect,
            requirements: vec![
                vec![p(
                    "razorpay-java/src/main/java/com/razorpay/ApiUtils.java",
                    "extenionName == \"jpg\"",
                )],
                vec![p(
                    "razorpay-java/src/main/java/com/razorpay/ApiUtils.java",
                    "return \"image/pdf\"",
                )],
            ],
            remediation: "Use value equality and map JPEG, PNG, and PDF magic bytes to the exact allowed MIME.",
        },
        Detector {
            id: "RP-JAVA-UPLOAD-DUPLICATE-FILE-PART",
            title: "Java document upload emits two conflicting file parts",
            repository: "razorpay-java",
            invariant: "A document multipart request contains exactly one binary file part.",
            severity: Severity::Medium,
            claim_kind: ClaimKind::Defect,
            requirements: vec![
                vec![p(
                    "razorpay-java/src/main/java/com/razorpay/ApiUtils.java",
                    "addFormDataPart(\"file\",fileName, fileBody)",
                )],
                vec![p(
                    "razorpay-java/src/main/java/com/razorpay/ApiUtils.java",
                    "requestObject.keys()",
                )],
            ],
            remediation: "Remove the file key before serializing scalar form fields and emit one binary part.",
        },
        Detector {
            id: "RP-MCP-GENERATOR-SIGNATURE-LENGTH-500",
            title: "Generated Node verifier turns malformed signature length into HTTP 500",
            repository: "razorpay-mcp-server",
            invariant: "Malformed untrusted signatures must fail as authentication errors, not exceptions.",
            severity: Severity::Low,
            claim_kind: ClaimKind::Defect,
            requirements: one(p(
                "razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go",
                "crypto.timingSafeEqual",
            )),
            remediation: "Decode strict hex, validate equal fixed length, then compare in constant time and return 400.",
        },
        Detector {
            id: "RP-PYTHON-PAYLINK-MISSING-FIELD",
            title: "Python payment-link verifier reads an unvalidated required field",
            repository: "razorpay-python",
            invariant: "All signature preimage fields must be validated before access.",
            severity: Severity::Low,
            claim_kind: ClaimKind::Defect,
            requirements: one(p(
                "razorpay-python/razorpay/utility/utility.py",
                "parameters['payment_link_id']",
            )),
            remediation: "Validate the complete required field set and return a typed validation error.",
        },
        Detector {
            id: "RP-MCP-REFUND-IDEMPOTENCY",
            title: "Refund tool does not expose Razorpay's refund idempotency identity",
            repository: "razorpay-mcp-server",
            invariant: "Retryable financial effects need a stable caller-owned identity.",
            severity: Severity::Medium,
            claim_kind: ClaimKind::Compatibility,
            requirements: one(p(
                "razorpay-mcp-server/pkg/razorpay/refunds.go",
                "client.Payment.Refund(",
            )),
            remediation: "Expose a required intent identity and send it as X-Refund-Idempotency with immutable request hashing.",
        },
        Detector {
            id: "RP-MCP-PAYOUT-NAME-DRIFT",
            title: "Payout tool name differs between current source and some callers",
            repository: "razorpay-mcp-server",
            invariant: "Tool names need a versioned compatibility map.",
            severity: Severity::Low,
            claim_kind: ClaimKind::Compatibility,
            requirements: one(p(
                "razorpay-mcp-server/pkg/razorpay/payouts.go",
                "fetch_payout_with_id",
            )),
            remediation: "Publish the current name and retain an explicit alias for fetch_payout_by_id.",
        },
        Detector {
            id: "RP-PYTHON-WEBHOOK-BYTES",
            title: "Python utility owns a text boundary instead of the raw webhook bytes",
            repository: "razorpay-python",
            invariant: "Webhook verification should preserve exact raw request bytes.",
            severity: Severity::Medium,
            claim_kind: ClaimKind::KnownPublic,
            requirements: one(p(
                "razorpay-python/razorpay/utility/utility.py",
                "body = bytes(body, 'utf-8')",
            )),
            remediation: "Add a raw-bytes verifier and retain the text API only as a compatibility wrapper.",
        },
        Detector {
            id: "RP-DOTNET-SIGNATURE-COMPARE",
            title: ".NET signature comparison is not constant time",
            repository: "razorpay-dot-net",
            invariant: "Authentication tags should be compared in constant time.",
            severity: Severity::Low,
            claim_kind: ClaimKind::KnownPublic,
            requirements: one(p(
                "razorpay-dot-net/src/Utils.cs",
                ".Equals(expectedSignature)",
            )),
            remediation: "Decode fixed-length hexadecimal tags and use CryptographicOperations.FixedTimeEquals.",
        },
        Detector {
            id: "RP-NODE-SIGNATURE-COMPARE",
            title: "Node signature utility uses ordinary string equality",
            repository: "razorpay-node",
            invariant: "Authentication tags should be compared in constant time.",
            severity: Severity::Low,
            claim_kind: ClaimKind::KnownPublic,
            requirements: one(p(
                "razorpay-node/lib/utils/razorpay-utils.js",
                "expectedSignature === signature",
            )),
            remediation: "Decode strict fixed-length hexadecimal tags and use timingSafeEqual.",
        },
        Detector {
            id: "RP-JAVA-DEFAULT-CHARSET",
            title: "Java signature utility relies on the process default charset",
            repository: "razorpay-java",
            invariant: "Cryptographic byte encoding must be explicit and portable.",
            severity: Severity::Low,
            claim_kind: ClaimKind::KnownPublic,
            requirements: one(p(
                "razorpay-java/src/main/java/com/razorpay/Utils.java",
                ".getBytes()",
            )),
            remediation: "Use StandardCharsets.UTF_8 explicitly for every signature preimage.",
        },
    ];
    rules.sort_by(|left, right| left.id.cmp(right.id));
    rules
}

#[derive(Debug, Error)]
pub enum EngineError {
    #[error(transparent)]
    Io(#[from] std::io::Error),
    #[error(transparent)]
    Walk(#[from] walkdir::Error),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detector_set_preserves_claim_taxonomy() {
        let rules = detectors();
        assert_eq!(rules.len(), 23);
        assert_eq!(
            rules
                .iter()
                .filter(|rule| rule.claim_kind == ClaimKind::Defect)
                .count(),
            17
        );
    }

    #[test]
    fn ignored_and_source_boundaries_are_explicit() {
        assert!(is_ignored(Path::new("repo/.git/config")));
        assert!(is_source(Path::new("main.rs")));
        assert!(!is_source(Path::new("proof.png")));
    }
}
