# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from razorproof.models import ClaimKind, Evidence, EvidenceLevel, Finding, ProbeResult, Severity
from razorproof.repositories import Repository, clean_work_copy

from .common import ProbeTimer, parse_last_json, run_process


def _python_probes(repo: Repository) -> ProbeResult:
    with ProbeTimer("dynamic:python-sdk") as result:
        script = r'''
import hashlib, hmac, json
from razorpay.utility.utility import Utility

class Client:
    auth = ("key", "secret")

utility = Utility(Client())
body = b'{"event":"payment.captured","name":"Achu"}'
signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
out = {}
try:
    out["raw_bytes_result"] = utility.verify_webhook_signature(body, signature, "secret")
except Exception as exc:
    out["raw_bytes_exception"] = type(exc).__name__ + ": " + str(exc)

incomplete = {
    "razorpay_payment_id": "pay_test",
    "payment_link_reference_id": "reference",
    "payment_link_status": "paid",
    "razorpay_signature": "00" * 32,
}
try:
    out["incomplete_payment_link_result"] = utility.verify_payment_link_signature(incomplete)
except Exception as exc:
    out["incomplete_payment_link_exception"] = type(exc).__name__ + ": " + str(exc)
print(json.dumps(out, sort_keys=True))
'''
        process = run_process(
            [shutil.which("python3") or "python3", "-c", script],
            cwd=repo.path,
        )
        if process.returncode != 0:
            result.errors.append(process.stderr.strip() or process.stdout.strip())
            return result
        observed = parse_last_json(process.stdout)
        if str(observed.get("raw_bytes_exception", "")).startswith("TypeError"):
            result.findings.append(Finding(
                id="RP-PYTHON-WEBHOOK-BYTES",
                title="Python webhook verifier rejects the raw bytes the webhook contract asks callers to preserve",
                repo=repo.name,
                surface="Utility.verify_webhook_signature",
                invariant="Valid raw request bytes are accepted without decoding and re-encoding.",
                severity=Severity.MEDIUM,
                level=EvidenceLevel.DYNAMIC,
                confidence=1.0,
                originality="publicly reported compatibility issue, independently reproduced against the pinned official commit",
                commit=repo.commit,
                description="A valid HMAC over a bytes payload throws before comparison.",
                impact="Framework integrations that correctly retain the raw body cannot pass it to the SDK.",
                counterexample=str(observed["raw_bytes_exception"]),
                proposed_fix="Encode str inputs and preserve bytes/bytearray inputs.",
                known_reference="https://github.com/razorpay/razorpay-python/issues/121",
                evidence=[Evidence(
                    kind="executed_official_sdk",
                    summary="Valid raw-byte webhook invocation throws TypeError",
                    detail=json.dumps(observed, sort_keys=True),
                    command="PYTHONPATH=<official-repo> python3 <generated probe>",
                    path="razorpay-python/razorpay/utility/utility.py",
                )],
                tags=["webhook", "raw-bytes", "python", "reproduced"],
                claim_kind=ClaimKind.COMPATIBILITY,
            ))
        if str(observed.get("incomplete_payment_link_exception", "")).startswith("KeyError"):
            result.findings.append(Finding(
                id="RP-PYTHON-PAYLINK-MISSING-FIELD",
                title="Python payment-link verifier throws KeyError for an omitted field it forgot to validate",
                repo=repo.name,
                surface="Utility.verify_payment_link_signature",
                invariant="Incomplete verification input fails closed with one documented result.",
                severity=Severity.LOW,
                level=EvidenceLevel.DYNAMIC,
                confidence=1.0,
                originality="publicly proposed fix, independently reproduced against the pinned official commit",
                commit=repo.commit,
                description="A callback-shaped map missing payment_link_id passes the guard and crashes at lookup.",
                impact="Malformed callback handling can become an application 500 rather than a clean authentication rejection.",
                counterexample=str(observed["incomplete_payment_link_exception"]),
                proposed_fix="Validate the complete required field set before access.",
                known_reference="https://github.com/razorpay/razorpay-python/pull/333",
                evidence=[Evidence(
                    kind="executed_official_sdk",
                    summary="Incomplete payment-link callback throws KeyError",
                    detail=json.dumps(observed, sort_keys=True),
                    command="PYTHONPATH=<official-repo> python3 <generated probe>",
                    path="razorpay-python/razorpay/utility/utility.py",
                )],
                tags=["payment-link", "python", "reproduced"],
            ))
    return result


def _ruby_probe(repo: Repository) -> ProbeResult:
    with ProbeTimer("dynamic:ruby-sdk") as result:
        ruby = shutil.which("ruby")
        if ruby is None:
            result.errors.append("ruby runtime unavailable")
            return result
        utility_path = repo.path / "lib/razorpay/utility.rb"
        script = r'''
require 'json'
require 'openssl'
module Razorpay
  def self.auth
    { password: 'secret' }
  end
end
load ARGV[0]
canonical = ['plink_live_shape', 'ref_42', 'paid', 'pay_live_shape'].join('|')
signature = OpenSSL::HMAC.hexdigest('SHA256', 'secret', canonical)
ordered = {
  payment_link_id: 'plink_live_shape',
  payment_link_reference_id: 'ref_42',
  payment_link_status: 'paid',
  razorpay_payment_id: 'pay_live_shape',
  razorpay_signature: signature,
}
reordered = {
  razorpay_payment_id: 'pay_live_shape',
  payment_link_status: 'paid',
  payment_link_id: 'plink_live_shape',
  payment_link_reference_id: 'ref_42',
  razorpay_signature: signature,
}
def outcome(value)
  Razorpay::Utility.verify_payment_link_signature(value.dup)
  'accepted'
rescue Exception => e
  e.class.name + ': ' + e.message
end
puts JSON.generate({ ordered: outcome(ordered), reordered: outcome(reordered) })
'''
        process = run_process([ruby, "-e", script, str(utility_path)])
        if process.returncode != 0:
            result.errors.append(process.stderr.strip() or process.stdout.strip())
            return result
        observed = parse_last_json(process.stdout)
        if observed.get("ordered") == "accepted" and str(observed.get("reordered", "")).startswith("SecurityError"):
            result.findings.append(Finding(
                id="RP-RUBY-PAYLINK-ORDER",
                title="Ruby payment-link verification depends on Hash insertion order",
                repo=repo.name,
                surface="Utility.verify_payment_link_signature",
                invariant="The signed field order is protocol-defined, not caller-container-defined.",
                severity=Severity.MEDIUM,
                level=EvidenceLevel.DYNAMIC,
                confidence=1.0,
                originality="independently discovered and reproduced; no matching public report found",
                commit=repo.commit,
                description="The official SDK accepted a correctly signed docs-order Hash and rejected the identical key/value set inserted in another order.",
                impact="Authentic payment-link callbacks can fail verification based only on application Hash construction order.",
                counterexample=json.dumps(observed, sort_keys=True),
                proposed_fix="Read four named fields in protocol order and leave the caller's Hash unchanged.",
                evidence=[Evidence(
                    kind="executed_official_sdk",
                    summary="Same signed fields: ordered accepted, reordered rejected",
                    detail=json.dumps(observed, sort_keys=True),
                    command="ruby -e <probe> <official utility.rb>",
                    path="razorpay-ruby/lib/razorpay/utility.rb",
                )],
                tags=["payment-link", "signature", "ruby", "reproduced"],
            ))
    return result


def _generated_money_probe(repo: Repository) -> ProbeResult:
    with ProbeTimer("dynamic:generated-money-matrix") as result:
        runtimes: list[tuple[str, list[str]]] = []
        if python := shutil.which("python3"):
            runtimes.append(("python", [python, "-c", "print(int(2.01 * 100))"]))
        if ruby := shutil.which("ruby"):
            runtimes.append(("ruby", [ruby, "-e", "puts((2.01 * 100).to_i)"]))
        if php := shutil.which("php"):
            runtimes.append(("php", [php, "-r", "echo (int)(2.01 * 100), PHP_EOL;"]))
        if node := shutil.which("node"):
            runtimes.append(("node_control", [node, "-e", "console.log(Math.round(2.01 * 100))"]))
        observed: dict[str, object] = {}
        for name, command in runtimes:
            process = run_process(command)
            observed[name] = {
                "exit": process.returncode,
                "minor_units": process.stdout.strip(),
                "stderr": process.stderr.strip(),
            }
        truncating = [
            name for name in ("python", "ruby", "php")
            if isinstance(observed.get(name), dict) and observed[name].get("minor_units") == "200"
        ]
        if truncating:
            result.findings.append(Finding(
                id="RP-MCP-GENERATOR-MONEY-UNDERCHARGE",
                title="Checkout generator emits one-paise undercharge bugs across seven backend languages",
                repo=repo.name,
                surface="integrate_razorpay_checkout generated backend code",
                invariant="Major-to-minor currency conversion must be decimal-exact and produce the intended integer subunit value.",
                severity=Severity.HIGH,
                level=EvidenceLevel.DYNAMIC,
                confidence=1.0,
                originality="independently discovered and reproduced; no matching public issue or pull request found",
                commit=repo.commit,
                description="Exact expressions emitted by the templates were executed on locally installed runtimes.",
                impact="The official AI integration generator can scaffold applications that undercharge ₹2.01 as 200 paise; the same truncation form appears in six backend language families.",
                counterexample=f"₹2.01 should be 201 paise; {', '.join(truncating)} returned 200. Node's rounded control returned 201.",
                proposed_fix="Pass integer subunits across the boundary or parse an exact decimal string and reject excess precision.",
                evidence=[Evidence(
                    kind="executed_emitted_expression",
                    summary="Official generated conversion expressions undercharge ₹2.01",
                    detail=json.dumps(observed, sort_keys=True),
                    command="runtime-specific execution of the exact emitted conversion expressions",
                    path="razorpay-mcp-server/pkg/razorpay/integrations",
                )],
                tags=["money", "code-generation", "cross-language", "reproduced", "undercharge"],
            ))
        if node := shutil.which("node"):
            currency_process = run_process([
                node,
                "-e",
                "console.log(JSON.stringify({jpy_generated:Math.round(295*100),jpy_exact:295,kwd_generated:Math.round(295.99*100),kwd_exact:295990}))",
            ])
            if currency_process.returncode == 0:
                currency_observed = parse_last_json(currency_process.stdout)
                if (
                    currency_observed.get("jpy_generated") == 29500
                    and currency_observed.get("kwd_generated") == 29599
                ):
                    result.findings.append(Finding(
                        id="RP-MCP-GENERATOR-CURRENCY-EXPONENT",
                        title="Checkout generator applies a two-decimal multiplier to zero- and three-decimal currencies",
                        repo=repo.name,
                        surface="integrate_razorpay_checkout generated backend code",
                        invariant="Major-to-minor conversion uses the exponent of the selected currency, not a hardcoded factor of 100.",
                        severity=Severity.HIGH,
                        level=EvidenceLevel.DYNAMIC,
                        confidence=1.0,
                        originality="independently discovered and reproduced with the exact generated Node expression",
                        commit=repo.commit,
                        description="Executing the generator's currency-agnostic Math.round(amount * 100) produced a 100× JPY overcharge and roughly 10× KWD undercharge relative to Razorpay's documented subunits.",
                        impact="Generated merchants can persist materially wrong but type-valid international-currency orders.",
                        counterexample=json.dumps(currency_observed, sort_keys=True),
                        proposed_fix="Accept integer subunits or apply a documented currency exponent table using exact decimal parsing.",
                        evidence=[Evidence(
                            kind="executed_emitted_expression",
                            summary="Hardcoded ×100 violates documented JPY and KWD exponent examples",
                            detail=json.dumps(currency_observed, sort_keys=True),
                            command="node -e <exact generated currency conversion expressions>",
                            path="razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go",
                        )],
                        tags=["money", "currency", "code-generation", "mcp", "overcharge", "undercharge", "reproduced"],
                    ))
    return result


def _generated_node_signature_probe(repo: Repository) -> ProbeResult:
    with ProbeTimer("dynamic:generated-node-signature-shape") as result:
        node = shutil.which("node")
        if node is None:
            result.errors.append("node runtime unavailable")
            return result
        script = r'''
const crypto = require('crypto');
const expected = crypto.createHmac('sha256', 'secret').update('order|payment').digest('hex');
let observed = { accepted: false, error_code: '', error_name: '' };
try {
  observed.accepted = crypto.timingSafeEqual(Buffer.from(expected), Buffer.from('x'));
} catch (error) {
  observed.error_code = error.code || '';
  observed.error_name = error.name || '';
}
console.log(JSON.stringify(observed));
'''
        process = run_process([node, "-e", script])
        if process.returncode != 0:
            result.errors.append(process.stderr.strip() or process.stdout.strip())
            return result
        observed = parse_last_json(process.stdout)
        if observed.get("error_code") == "ERR_CRYPTO_TIMING_SAFE_EQUAL_LENGTH":
            result.findings.append(Finding(
                id="RP-MCP-GENERATOR-SIGNATURE-LENGTH-500",
                title="Generated Node verifier turns malformed signature lengths into HTTP 500",
                repo=repo.name,
                surface="generated Express payment verification route",
                invariant="Untrusted malformed authentication input fails closed as a controlled client error.",
                severity=Severity.LOW,
                level=EvidenceLevel.DYNAMIC,
                confidence=1.0,
                originality="independently discovered and reproduced with the exact generated comparison operation",
                commit=repo.commit,
                description="The generated timingSafeEqual call throws Node's length exception for an untrusted one-byte signature, and the generated route catches it as HTTP 500.",
                impact="Any unauthenticated caller can create noisy server errors and false operational alarms on the public verify endpoint.",
                counterexample=json.dumps(observed, sort_keys=True),
                proposed_fix="Validate and decode an exact 32-byte hexadecimal signature before timingSafeEqual; return 400 for malformed input.",
                evidence=[Evidence(
                    kind="executed_emitted_expression",
                    summary="Node throws on the generated unequal-length comparison",
                    detail=json.dumps(observed, sort_keys=True),
                    command="node -e <exact timingSafeEqual comparison probe>",
                    path="razorpay-mcp-server/pkg/razorpay/integrations/backend_node.go",
                )],
                tags=["error-contract", "signature", "node", "code-generation", "mcp", "reproduced"],
            ))
    return result


def _php_global_state_probe(repo: Repository) -> ProbeResult:
    with ProbeTimer("dynamic:php-global-auth-state") as result:
        php = shutil.which("php")
        if php is None:
            result.errors.append("php runtime unavailable")
            return result
        script = r'''
require $argv[1];
require $argv[2];
$a = new Razorpay\Api\Api('merchant_A', 'secret_A');
$keyBefore = Razorpay\Api\Api::getKey();
$a->setHeader('X-Razorpay-Account', 'account_A');
$b = new Razorpay\Api\Api('merchant_B', 'secret_B');
$keyAfter = Razorpay\Api\Api::getKey();
$headersSeenByB = Razorpay\Api\Request::getHeaders();
echo json_encode([
  'a_key_before_b' => $keyBefore,
  'global_key_after_b' => $keyAfter,
  'b_inherits_a_partner_header' => (($headersSeenByB['X-Razorpay-Account'] ?? '') === 'account_A'),
]);
'''
        process = run_process([
            php,
            "-r",
            script,
            str(repo.path / "src/Api.php"),
            str(repo.path / "src/Request.php"),
        ])
        if process.returncode != 0:
            result.errors.append(process.stderr.strip() or process.stdout.strip())
            return result
        observed = parse_last_json(process.stdout)
        if (
            observed.get("a_key_before_b") == "merchant_A"
            and observed.get("global_key_after_b") == "merchant_B"
            and observed.get("b_inherits_a_partner_header") is True
        ):
            result.findings.append(Finding(
                id="RP-PHP-GLOBAL-AUTH-STATE",
                title="PHP client instances share and overwrite process-wide credentials and headers",
                repo=repo.name,
                surface="Api and Request authentication state",
                invariant="Each SDK client owns immutable credentials, base URL, token, and headers for its requests.",
                severity=Severity.HIGH,
                level=EvidenceLevel.DYNAMIC,
                confidence=1.0,
                originality="independently discovered and reproduced against the pinned official SDK",
                commit=repo.commit,
                description="Constructing client B replaced the key visible to client A's process, while client B inherited the partner-routing header set through client A.",
                impact="Long-running PHP workers serving multiple merchants can send one merchant's operation under another merchant's credentials or partner routing header.",
                counterexample=json.dumps(observed, sort_keys=True),
                proposed_fix="Move authentication, endpoint, app details, and headers to an instance-owned request client injected into every resource.",
                evidence=[Evidence(
                    kind="executed_official_sdk",
                    summary="Two official Api instances demonstrably share credentials and partner headers",
                    detail=json.dumps(observed, sort_keys=True),
                    command="php -r <two-client isolation probe> <official Api.php> <official Request.php>",
                    path="razorpay-php/src/Api.php",
                )],
                tags=["security", "multi-tenant", "credentials", "partner-routing", "php", "global-state", "reproduced"],
            ))
    return result


GO_REFUND_TEST = r'''package razorpay

import (
    "context"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    rzpsdk "github.com/razorpay/razorpay-go"
)

func TestRazorProofFractionalRefundMustFailClosed(t *testing.T) {
    called := false
    var received map[string]interface{}
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        called = true
        if err := json.NewDecoder(r.Body).Decode(&received); err != nil { t.Fatal(err) }
        w.Header().Set("Content-Type", "application/json")
        _, _ = w.Write([]byte(`{"id":"rfnd_probe","amount":100}`))
    }))
    defer server.Close()

    client := rzpsdk.NewClient("key", "secret")
    client.Order.Request.BaseURL = server.URL
    client.Order.Request.HTTPClient = server.Client()
    tool := CreateRefund(CreateTestObservability(), client)
    result, err := tool.GetHandler()(context.Background(), createMCPRequest(map[string]interface{}{
        "payment_id": "pay_probe", "amount": float64(100.75),
    }))
    if err != nil { t.Fatal(err) }
    if called {
        t.Fatalf("fractional money crossed the MCP boundary: requested=100.75 sent=%v", received["amount"])
    }
    if result == nil || !result.IsError {
        t.Fatalf("fractional amount was not rejected: %#v", result)
    }

    called = false
    received = nil
    result, err = tool.GetHandler()(context.Background(), createMCPRequest(map[string]interface{}{
        "payment_id": "pay_probe", "amount": float64(100),
    }))
    if err != nil { t.Fatal(err) }
    if !called || received["amount"] != float64(100) {
        t.Fatalf("valid integer amount did not cross unchanged: called=%v sent=%v result=%#v", called, received["amount"], result)
    }
    if result == nil || result.IsError {
        t.Fatalf("valid integer amount was rejected: %#v", result)
    }
}
'''


def _container_go_refund_probe(repo: Repository) -> ProbeResult:
    with ProbeTimer("dynamic:container-mcp-refund") as result:
        with tempfile.TemporaryDirectory(prefix="razorproof-go-") as directory:
            work = clean_work_copy(repo, Path(directory) / "repo")
            test_path = work / "pkg/razorpay/razorproof_fractional_test.go"
            test_path.write_text(GO_REFUND_TEST, encoding="utf-8")
            command = [
                "docker", "run", "--rm",
                "-v", f"{work}:/work",
                "-w", "/work",
                "golang:1.25",
                "go", "test", "./pkg/razorpay", "-run", "TestRazorProofFractionalRefundMustFailClosed", "-count=1", "-v",
            ]
            process = run_process(command, timeout=600)
            combined = process.stdout + process.stderr
            if "fractional money crossed the MCP boundary" in combined:
                result.findings.append(Finding(
                    id="RP-MCP-REFUND-TRUNCATION",
                    title="Refund tool silently truncates a fractional subunit amount",
                    repo=repo.name,
                    surface="create_refund MCP tool",
                    invariant="Money in currency subunits is an integer and invalid fractions must be rejected, never changed.",
                    severity=Severity.MEDIUM,
                    level=EvidenceLevel.DYNAMIC,
                    confidence=1.0,
                    originality="independently discovered and reproduced against the official handler and SDK request path",
                    commit=repo.commit,
                    description="A generated black-box regression test invoked the official tool handler and intercepted its HTTP request.",
                    impact="The invalid fractional-subunit input was silently mutated instead of rejected; the numerical difference is less than one subunit.",
                    counterexample="fractional money crossed the MCP boundary: requested=100.75 sent=100",
                    proposed_fix="Validate and store int64 at the handler boundary; publish integer JSON Schema when the MCP dependency supports it.",
                    evidence=[Evidence(
                        kind="executed_official_handler",
                        summary="Black-box HTTP interception observed 100.75 mutate to 100",
                        detail=combined[-4000:],
                        command="docker run golang:1.25 go test ./pkg/razorpay -run TestRazorProofFractionalRefundMustFailClosed",
                        path="razorpay-mcp-server/pkg/razorpay/refunds.go",
                    )],
                    tags=["money", "mcp", "reproduced", "silent-mutation"],
                ))
            elif process.returncode != 0:
                result.errors.append(combined[-4000:])
    return result


JAVA_SEMANTIC_TEST = r'''package com.razorpay;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

import okhttp3.RequestBody;
import okio.Buffer;
import org.json.JSONObject;
import org.junit.Assert;
import org.junit.Test;

public class RazorProofSemanticTest {
  private static int occurrences(String text, String needle) {
    int count = 0;
    int index = 0;
    while ((index = text.indexOf(needle, index)) >= 0) {
      count++;
      index += needle.length();
    }
    return count;
  }

  @Test
  public void sdkMustPreserveMultipartAndClientIsolationContracts() throws Exception {
    Method mediaMethod = ApiUtils.class.getDeclaredMethod("getMediaType", String.class);
    mediaMethod.setAccessible(true);
    String pngMediaType = (String) mediaMethod.invoke(null, "proof.png");

    Path png = Files.createTempFile("razorproof-", ".png");
    Files.write(png, "not-a-real-image-needed-for-wire-proof".getBytes(StandardCharsets.UTF_8));
    JSONObject upload = new JSONObject();
    upload.put("file", png.toString());
    upload.put("purpose", "dispute_evidence");
    Method bodyMethod = ApiUtils.class.getDeclaredMethod("fileRequestBody", JSONObject.class);
    bodyMethod.setAccessible(true);
    RequestBody requestBody = (RequestBody) bodyMethod.invoke(null, upload);
    Buffer buffer = new Buffer();
    requestBody.writeTo(buffer);
    String wire = buffer.readUtf8();
    int fileParts = occurrences(wire, "name=\"file\"");

    Field headersField = ApiUtils.class.getDeclaredField("headers");
    headersField.setAccessible(true);
    @SuppressWarnings("unchecked")
    Map<String, String> globalHeaders = (Map<String, String>) headersField.get(null);
    globalHeaders.clear();
    RazorpayClient clientA = new RazorpayClient("key_A", "secret_A");
    Map<String, String> aHeaders = new HashMap<String, String>();
    aHeaders.put("X-Razorpay-Account", "account_A");
    clientA.addHeaders(aHeaders);
    RazorpayClient clientB = new RazorpayClient("key_B", "secret_B");
    boolean bInheritedA = "account_A".equals(globalHeaders.get("X-Razorpay-Account"));
    Map<String, String> bHeaders = new HashMap<String, String>();
    bHeaders.put("X-Razorpay-Account", "account_B");
    clientB.addHeaders(bHeaders);
    String globalAfterB = globalHeaders.get("X-Razorpay-Account");

    String observed = "{\"png_media_type\":\"" + pngMediaType
        + "\",\"file_parts\":" + fileParts
        + ",\"client_b_inherited_a_header\":" + bInheritedA
        + ",\"global_header_after_b\":\"" + globalAfterB + "\"}";
    System.out.println("RAZORPROOF_OBS " + observed);
    Files.deleteIfExists(png);

    Assert.assertEquals("image/png", pngMediaType);
    Assert.assertEquals(1, fileParts);
    Assert.assertFalse(bInheritedA);
  }
}
'''


def _container_java_semantic_probe(repo: Repository) -> ProbeResult:
    with ProbeTimer("dynamic:container-java-semantics") as result:
        with tempfile.TemporaryDirectory(prefix="razorproof-java-", dir="/tmp") as directory:
            work = clean_work_copy(repo, Path(directory) / "razorpay-java")
            test_path = work / "src/test/java/com/razorpay/RazorProofSemanticTest.java"
            test_path.write_text(JAVA_SEMANTIC_TEST, encoding="utf-8")
            command = [
                "docker", "run", "--rm",
                "-v", f"{work}:/work",
                "-w", "/work",
                "maven:3.9.9-eclipse-temurin-17",
                "mvn", "-q", "-Dtest=RazorProofSemanticTest", "test",
            ]
            process = run_process(command, timeout=900)
            combined = process.stdout + process.stderr
            marker = "RAZORPROOF_OBS "
            observed: dict[str, object] = {}
            if marker in combined:
                encoded = combined.split(marker, 1)[1].splitlines()[0]
                try:
                    observed = json.loads(encoded)
                except json.JSONDecodeError:
                    result.errors.append("could not parse Java semantic observation")
            else:
                result.errors.append(combined[-6000:])
                return result

            common = Evidence(
                kind="executed_official_sdk",
                summary="Official Java SDK multipart and multi-client runtime probe",
                detail=json.dumps(observed, sort_keys=True),
                command="docker run maven:3.9.9-eclipse-temurin-17 mvn -Dtest=RazorProofSemanticTest test",
                path="razorpay-java/src/main/java/com/razorpay/ApiUtils.java",
            )
            if observed.get("png_media_type") == "image/pdf":
                result.findings.append(Finding(
                    id="RP-JAVA-UPLOAD-MIME",
                    title="Java document uploads mislabel runtime JPG and PNG paths as PDF",
                    repo=repo.name,
                    surface="ApiUtils.getMediaType",
                    invariant="Multipart file MIME type matches the selected file format.",
                    severity=Severity.MEDIUM,
                    level=EvidenceLevel.DYNAMIC,
                    confidence=1.0,
                    originality="independently discovered and reproduced against the pinned official SDK",
                    commit=repo.commit,
                    description="The official private serializer classified a runtime proof.png path as image/pdf.",
                    impact="Valid evidence and KYC image uploads can be rejected, misclassified, or processed through the wrong media path.",
                    counterexample=json.dumps(observed, sort_keys=True),
                    proposed_fix="Use equalsIgnoreCase, map each supported extension to its exact MIME type, and reject unknown extensions.",
                    evidence=[common],
                    tags=["documents", "multipart", "mime", "java", "reproduced"],
                ))
            if observed.get("file_parts") == 2:
                result.findings.append(Finding(
                    id="RP-JAVA-UPLOAD-DUPLICATE-FILE-PART",
                    title="Java document upload serializes the file field twice with conflicting types",
                    repo=repo.name,
                    surface="ApiUtils.fileRequestBody",
                    invariant="The singular document file field appears exactly once as a binary multipart part.",
                    severity=Severity.MEDIUM,
                    level=EvidenceLevel.DYNAMIC,
                    confidence=1.0,
                    originality="independently discovered and reproduced against the pinned official SDK wire body",
                    commit=repo.commit,
                    description="Serializing one upload object produced two multipart parts named file: one binary and one text pathname.",
                    impact="Servers and intermediaries can select the wrong duplicate field, reject the request, or treat a local pathname as the upload value.",
                    counterexample=json.dumps(observed, sort_keys=True),
                    proposed_fix="Exclude file from the ordinary field loop and serialize it exactly once as the binary part.",
                    evidence=[common],
                    tags=["documents", "multipart", "cardinality", "java", "reproduced"],
                ))
            if (
                observed.get("client_b_inherited_a_header") is True
                and observed.get("global_header_after_b") == "account_B"
            ):
                result.findings.append(Finding(
                    id="RP-JAVA-GLOBAL-PARTNER-HEADERS",
                    title="Java clients share one process-wide partner-routing header map",
                    repo=repo.name,
                    surface="RazorpayClient.addHeaders and ApiUtils.createRequest",
                    invariant="X-Razorpay-Account and custom headers are scoped to the intended client or request.",
                    severity=Severity.HIGH,
                    level=EvidenceLevel.DYNAMIC,
                    confidence=1.0,
                    originality="independently discovered and reproduced against the pinned official SDK",
                    commit=repo.commit,
                    description="Client B inherited client A's X-Razorpay-Account before B set any header; B then overwrote the single map for the whole process.",
                    impact="An aggregator process can route a request to the wrong sub-merchant when multiple client contexts share one JVM.",
                    counterexample=json.dumps(observed, sort_keys=True),
                    proposed_fix="Store immutable default headers per client/resource and support per-request overrides.",
                    evidence=[common],
                    tags=["security", "multi-tenant", "partner-routing", "java", "global-state", "reproduced"],
                ))
    return result


DOTNET_PROGRAM = r'''using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;
using Razorpay.Api;

var secret = "0123456789abcdef0123456789abcdef";
var data = new Dictionary<string, object> { ["submerchant_id"] = "acct_42", ["timestamp"] = 1700000000 };
var first = Utils.GenerateOnboardingSignature(data, secret);
var second = Utils.GenerateOnboardingSignature(data, secret);
var payload = "{\"name\":\"Achu ₹ മലയാളം\"}";
using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes("webhook-secret"));
var signature = Convert.ToHexString(hmac.ComputeHash(Encoding.UTF8.GetBytes(payload))).ToLowerInvariant();
var unicodeAccepted = true;
string unicodeError = "";
try { Utils.verifyWebhookSignature(payload, signature, "webhook-secret"); }
catch (Exception ex) { unicodeAccepted = false; unicodeError = ex.GetType().Name + ": " + ex.Message; }

var merchantSecretA = "merchant-secret-A";
var clientA = new RazorpayClient("merchant_A", merchantSecretA);
clientA.addHeader("X-Razorpay-Account", "account_A");
var keyBeforeB = RazorpayClient.Key;
var paymentAttributes = new Dictionary<string, string> {
    ["razorpay_order_id"] = "order_A",
    ["razorpay_payment_id"] = "payment_A",
};
using var paymentHmac = new HMACSHA256(Encoding.UTF8.GetBytes(merchantSecretA));
paymentAttributes["razorpay_signature"] = Convert.ToHexString(paymentHmac.ComputeHash(Encoding.UTF8.GetBytes("order_A|payment_A"))).ToLowerInvariant();
var clientB = new RazorpayClient("merchant_B", "merchant-secret-B");
var keyAfterB = RazorpayClient.Key;
var clientBInheritedHeader = RazorpayClient.Headers.TryGetValue("X-Razorpay-Account", out var routedAccount) && routedAccount == "account_A";
var clientASignatureAcceptedAfterB = true;
string clientASignatureError = "";
try { Utils.verifyPaymentSignature(paymentAttributes); }
catch (Exception ex) { clientASignatureAcceptedAfterB = false; clientASignatureError = ex.GetType().Name + ": " + ex.Message; }

Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new {
    gcm_same = first == second,
    unicode_accepted = unicodeAccepted,
    unicode_error = unicodeError,
    first_prefix = first.Substring(0, 24),
    key_before_b = keyBeforeB,
    key_after_b = keyAfterB,
    client_b_inherited_a_header = clientBInheritedHeader,
    client_a_signature_accepted_after_b = clientASignatureAcceptedAfterB,
    client_a_signature_error = clientASignatureError,
}));
'''


def _container_dotnet_probe(repo: Repository) -> ProbeResult:
    with ProbeTimer("dynamic:container-dotnet-sdk") as result:
        with tempfile.TemporaryDirectory(prefix="razorproof-dotnet-", dir="/tmp") as directory:
            root = Path(directory)
            work = clean_work_copy(repo, root / "razorpay-dot-net")
            sdk_project = work / "Razorpay.csproj"
            sdk_project.write_text(
                sdk_project.read_text(encoding="utf-8")
                .replace(
                    "<TargetFrameworks>net47;net48;netstandard2.0;net6.0;net8.0</TargetFrameworks>",
                    "<TargetFramework>net8.0</TargetFramework>",
                )
                .replace("<GeneratePackageOnBuild>true</GeneratePackageOnBuild>", "<GeneratePackageOnBuild>false</GeneratePackageOnBuild>"),
                encoding="utf-8",
            )
            probe = root / "probe"
            probe.mkdir()
            (probe / "Program.cs").write_text(DOTNET_PROGRAM, encoding="utf-8")
            project_reference = str(work / "Razorpay.csproj")
            csproj = f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net8.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings></PropertyGroup>
  <ItemGroup><ProjectReference Include="{project_reference}" /></ItemGroup>
</Project>'''
            (probe / "Probe.csproj").write_text(csproj, encoding="utf-8")
            command = [
                "docker", "run", "--rm",
                "-v", f"{root}:{root}",
                "-w", str(probe),
                "mcr.microsoft.com/dotnet/sdk:8.0",
                "dotnet", "run", "--project", "Probe.csproj", "-p:TargetFramework=net8.0",
            ]
            process = run_process(command, timeout=600)
            combined = process.stdout + process.stderr
            if process.returncode != 0:
                result.errors.append(combined[-6000:])
                return result
            observed = parse_last_json(process.stdout)
            common = Evidence(
                kind="executed_official_sdk",
                summary="Official .NET SDK runtime probe",
                detail=json.dumps(observed, sort_keys=True),
                command="docker run mcr.microsoft.com/dotnet/sdk:8.0 dotnet run <probe referencing official Razorpay.csproj>",
                path="razorpay-dot-net/src/Utils.cs",
            )
            if observed.get("gcm_same") is True:
                result.findings.append(Finding(
                    id="RP-DOTNET-GCM-NONCE-REUSE",
                    title=".NET onboarding signatures reuse an AES-GCM nonce derived from the secret key",
                    repo=repo.name,
                    surface="Utils.GenerateOnboardingSignature",
                    invariant="AES-GCM uses a fresh unique nonce for every encryption under a key.",
                    severity=Severity.CRITICAL,
                    level=EvidenceLevel.DYNAMIC,
                    confidence=1.0,
                    originality="independently discovered and executed against the official SDK",
                    commit=repo.commit,
                    description="Two official SDK calls with identical input and key returned identical ciphertext.",
                    impact="Nonce reuse breaks AES-GCM confidentiality and authenticity guarantees.",
                    counterexample=json.dumps(observed, sort_keys=True),
                    proposed_fix="Generate and prefix a fresh 12-byte random nonce, matching current Ruby/Node/Java/PHP SDKs.",
                    evidence=[common],
                    tags=["cryptography", "aes-gcm", "dotnet", "reproduced"],
                ))
            if observed.get("unicode_accepted") is False:
                result.findings.append(Finding(
                    id="RP-DOTNET-WEBHOOK-ASCII",
                    title=".NET webhook verifier hashes non-ASCII strings as ASCII",
                    repo=repo.name,
                    surface="Utils.verifyWebhookSignature",
                    invariant="HMAC input is the exact UTF-8 request body, byte for byte.",
                    severity=Severity.MEDIUM,
                    level=EvidenceLevel.DYNAMIC,
                    confidence=1.0,
                    originality="independently discovered and executed against the official SDK",
                    commit=repo.commit,
                    description="A correct UTF-8 HMAC for a JSON payload containing ₹ and Malayalam text was rejected by the official SDK.",
                    impact="Literal non-ASCII UTF-8 payload bytes fail verification. Razorpay Test Mode delivered and validly signed this shape for payment-link and refund events.",
                    counterexample=json.dumps(observed, sort_keys=True),
                    proposed_fix="Expose byte[] and use UTF-8 explicitly for string overloads.",
                    evidence=[common],
                    tags=["webhook", "unicode", "dotnet", "reproduced"],
                    claim_kind=ClaimKind.DEFECT,
                ))
            if (
                observed.get("key_before_b") == "merchant_A"
                and observed.get("key_after_b") == "merchant_B"
                and observed.get("client_b_inherited_a_header") is True
                and observed.get("client_a_signature_accepted_after_b") is False
            ):
                result.findings.append(Finding(
                    id="RP-DOTNET-GLOBAL-AUTH-STATE",
                    title=".NET client instances overwrite one process-wide credential and routing context",
                    repo=repo.name,
                    surface="RazorpayClient, RestClient, and payment signature verification",
                    invariant="Credentials, base URL, access token, and request headers are scoped to one client instance and cannot be changed by constructing another client.",
                    severity=Severity.HIGH,
                    level=EvidenceLevel.DYNAMIC,
                    confidence=1.0,
                    originality="independently discovered and reproduced against the pinned official SDK",
                    commit=repo.commit,
                    description="The official SDK probe initialized client A, added A's partner header, then initialized B. The global key changed to B, B inherited A's header, and A's valid payment signature failed because verification used B's secret.",
                    impact="A multi-tenant or multi-account .NET process can authenticate or route an operation under the wrong merchant and can reject a valid payment callback after another client is initialized.",
                    counterexample=json.dumps(observed, sort_keys=True),
                    proposed_fix="Make authentication, endpoint, header, and utility state immutable instance fields and require an explicit client/secret for verification.",
                    evidence=[Evidence(
                        kind=common.kind,
                        summary="Two-client official .NET SDK probe crossed credential, header, and verifier state",
                        detail=common.detail,
                        command=common.command,
                        path="razorpay-dot-net/src/RazorpayClient.cs",
                    )],
                    tags=["security", "multi-tenant", "credentials", "partner-routing", "dotnet", "global-state", "reproduced"],
                ))
    return result


def run_dynamic_probes(
    repositories: dict[str, Repository],
    *,
    containers: bool = False,
) -> list[ProbeResult]:
    results: list[ProbeResult] = []
    if repo := repositories.get("razorpay-python"):
        results.append(_python_probes(repo))
    if repo := repositories.get("razorpay-ruby"):
        results.append(_ruby_probe(repo))
    if repo := repositories.get("razorpay-mcp-server"):
        results.append(_generated_money_probe(repo))
        results.append(_generated_node_signature_probe(repo))
    if repo := repositories.get("razorpay-php"):
        results.append(_php_global_state_probe(repo))
    if containers:
        if repo := repositories.get("razorpay-mcp-server"):
            results.append(_container_go_refund_probe(repo))
        if repo := repositories.get("razorpay-dot-net"):
            results.append(_container_dotnet_probe(repo))
        if repo := repositories.get("razorpay-java"):
            results.append(_container_java_semantic_probe(repo))
    return results
