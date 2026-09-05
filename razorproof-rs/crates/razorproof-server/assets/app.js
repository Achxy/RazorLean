// Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
// SPDX-License-Identifier: MIT
// Licensed under the MIT License. See LICENSE in the repository root.

const $ = (selector) => document.querySelector(selector);
const factors = { JPY: 1, BHD: 1000, KWD: 1000, OMR: 1000 };
const quantum = { BHD: 10, KWD: 10, OMR: 10 };
let gatewayToken = "";

function exactMinor(input, currency) {
  if (!/^\d+(\.\d+)?$/.test(input)) throw new Error("Use a positive decimal string.");
  const factor = factors[currency] || 100;
  const exponent = Math.log10(factor);
  const [whole, fraction = ""] = input.split(".");
  if (fraction.length > exponent) throw new Error(`${currency} permits ${exponent} decimal places.`);
  const value = BigInt(whole) * BigInt(factor) + BigInt((fraction + "0".repeat(exponent)).slice(0, exponent) || "0");
  if (value <= 0n || (quantum[currency] && value % BigInt(quantum[currency]) !== 0n)) {
    throw new Error(`${currency} amount violates its provider quantum.`);
  }
  return value;
}

$("#run-fault").addEventListener("click", () => {
  const major = $("#major").value.trim();
  const currency = $("#currency").value.trim().toUpperCase();
  const factor = factors[currency] || 100;
  const unsafe = Math.trunc(Number(major) * factor);
  $("#unsafe-expression").textContent = `int(${major} × ${factor})`;
  $("#unsafe-output").textContent = unsafe;
  try {
    const safe = exactMinor(major, currency);
    $("#safe-expression").textContent = `exact(${major}, ${currency})`;
    $("#safe-output").textContent = safe;
    const delta = BigInt(unsafe) - safe;
    $("#unsafe-note").textContent = delta === 0n ? "This input is a control: both paths happen to agree." : `Outbound order changed by ${delta} minor unit${delta === 1n || delta === -1n ? "" : "s"}.`;
    $("#safe-note").textContent = `Validated ${currency} integer. Currency exponent ${Math.log10(factor)}; quantum ${quantum[currency] || 1}.`;
  } catch (error) {
    $("#safe-output").textContent = "BLOCKED";
    $("#safe-note").textContent = error.message;
  }
  for (const lane of document.querySelectorAll(".lane")) {
    lane.classList.remove("ran");
    requestAnimationFrame(() => lane.classList.add("ran"));
  }
});

async function health() {
  try {
    const response = await fetch("/healthz");
    const payload = await response.json();
    $("#operation-count").textContent = payload.operation_count;
    $("#connection-status").textContent = `${payload.status.toUpperCase()} · ${payload.operation_count} operations · ${payload.mode.replace("_", " ")}`;
    $("#connection-status").dataset.tone = "pass";
  } catch {
    $("#connection-status").textContent = "The local service is not reachable.";
    $("#connection-status").dataset.tone = "stop";
  }
}

function auth() {
  return {
    Authorization: `Bearer ${gatewayToken}`,
    "X-RazorProof-Tenant": $("#tenant").value.trim(),
  };
}

function escapeHtml(value) {
  const node = document.createElement("span");
  node.textContent = value;
  return node.innerHTML;
}

async function connect() {
  const [evidence, catalog] = await Promise.all([
    fetch("/v1/evidence", { headers: auth() }),
    fetch("/v1/catalog", { headers: auth() }),
  ]);
  if (!evidence.ok || !catalog.ok) throw new Error("Authentication failed or the service refused the request.");
  const evidencePayload = await evidence.json();
  const catalogPayload = await catalog.json();
  $("#events").innerHTML = evidencePayload.events.length
    ? evidencePayload.events.map((event) => `<div class="event"><time>${new Date(event.occurred_at * 1000).toLocaleTimeString()}</time><span>${escapeHtml(event.operation)} · ${escapeHtml(event.kind)}</span><code>${escapeHtml(event.chain_hash.slice(0, 16))}</code></div>`).join("")
    : '<p class="empty">No effects yet. Issue a quote or run a Test Mode operation to begin the chain.</p>';
  $("#coverage-body").innerHTML = catalogPayload.operations.map((operation) => `<tr><td>${escapeHtml(operation.name)}</td><td>${escapeHtml(operation.surface)}</td><td><span class="pill ${operation.access === "write" ? "write" : ""}">${escapeHtml(operation.access)}</span></td><td>${escapeHtml(operation.effect)}</td><td>${escapeHtml(operation.idempotency)}</td></tr>`).join("");
  $("#connection-status").textContent = `Connected · ${evidencePayload.events.length} evidence events · catalog ${catalogPayload.catalog_version}`;
  $("#connection-status").dataset.tone = "pass";
}

$("#connection-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  gatewayToken = $("#token").value;
  try { await connect(); } catch (error) {
    $("#connection-status").textContent = error.message;
    $("#connection-status").dataset.tone = "stop";
  }
});

$("#forget").addEventListener("click", () => {
  gatewayToken = "";
  $("#token").value = "";
  $("#events").innerHTML = '<p class="empty">Token forgotten. The provider secret was never present here.</p>';
  $("#connection-status").textContent = "Browser session cleared.";
  delete $("#connection-status").dataset.tone;
});

health();
$("#run-fault").click();
