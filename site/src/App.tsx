/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ActivityIcon, ArrowRightIcon, Badge, BugIcon, Button, CheckCircleIcon, CodeSnippetIcon, ExternalLinkIcon, GithubIcon, LockIcon, RefreshIcon, SearchIcon, ShieldIcon } from "@razorpay/blade/components";
import { chains, claimLabel, coordinates, currencies, findings, gradeLabel, type Chain } from "./data/evidence";
import { RoughMark } from "./components/RoughMark";

const ease = [0.22, 1, 0.36, 1] as const;

function Header() {
  return <header className="topbar"><a className="brand" href="#top" aria-label="RazorLean home"><span className="brand-glyph">RL</span><span>RazorLean</span></a><nav aria-label="Primary"><a href="#failure">The failure</a><a href="#chains">Chains</a><a href="#cases">Case files</a><a href="#boundary">Boundary</a></nav><Button href="https://github.com/Achxy/RazorLean" target="_blank" rel="noreferrer" icon={GithubIcon} size="small" variant="secondary">Source</Button></header>;
}

function PaymentTrace() {
  const [protectedMode, setProtectedMode] = useState(false);
  const [run, setRun] = useState(0);
  const steps = protectedMode ? ["Alice enters ¥295", "Quote fixes JPY exponent 0", "RazorProof computes 295", "Provider receives 295", "Paid means the intended price"] : ["Alice enters ¥295", "Generated code multiplies by 100", "Provider receives 29,500", "The order is valid", "Alice is charged 100× too much"];
  return <div className="trace-shell" aria-label="Interactive payment trace">
    <div className="trace-toolbar"><div><span className="status-dot" />LIVE COUNTEREXAMPLE</div><div className="segmented" role="group" aria-label="Choose path"><button aria-pressed={!protectedMode} onClick={() => { setProtectedMode(false); setRun(0); }}>Without RazorProof</button><button aria-pressed={protectedMode} onClick={() => { setProtectedMode(true); setRun(0); }}>With RazorProof</button></div></div>
    <div className="actors"><div className="actor"><span className="head" /><span className="body" /><b>Alice</b><small>wants to pay ¥295</small></div><div className="flow"><div className="flow-line" /><AnimatePresence mode="wait"><motion.div key={`${protectedMode}-${run}`} className={`money-token ${protectedMode ? "safe" : "danger"}`} initial={{ x: "-42%", opacity: 0 }} animate={{ x: "42%", opacity: 1 }} transition={{ duration: 1.3, ease }}>{protectedMode ? "295" : "29,500"}</motion.div></AnimatePresence></div><div className="actor bob"><span className="head" /><span className="body" /><b>Bob's store</b><small>sees a paid order</small></div></div>
    <ol className="trace-steps">{steps.map((step, index) => <li key={step} className={index === steps.length - 1 ? (protectedMode ? "ok" : "bad") : ""}><span>{index + 1}</span>{step}</li>)}</ol>
    <div className="trace-result"><strong>{protectedMode ? "INTENT PRESERVED" : "VALID PAYMENT. WRONG ECONOMICS."}</strong><Button icon={RefreshIcon} onClick={() => setRun((value) => value + 1)} size="small">Replay</Button></div>
  </div>;
}

function Hero() {
  return <><section className="hero section" id="top"><div className="hero-copy"><Badge color="primary" icon={ShieldIcon}>SEMANTIC PAYMENT FIREWALL</Badge><h1>A valid signature can still prove the <span>wrong payment.<RoughMark kind="underline" /></span></h1><p>RazorProof preserves what ordinary payment integrations lose: the exact value, merchant, effect, bytes, and lifecycle behind every state transition.</p><div className="hero-actions"><Button href="#failure" icon={ActivityIcon} iconPosition="right" size="large">Run the failure</Button><Button href="#cases" variant="secondary" icon={BugIcon} size="large">Inspect every case</Button></div><small className="independent">Independent Buildathon prototype · Not an official Razorpay product</small></div><PaymentTrace /></section><section className="proof-strip"><div><span>PROVIDER-OBSERVED</span><strong>Test Mode accepted and persisted the generated JPY and KWD integers.</strong></div><a href="#evidence">See the actual surface <ArrowRightIcon size="small" /></a></section></>;
}

function GroundUp() {
  return <section className="section ground" id="failure"><div className="section-intro"><span className="kicker">01 · FROM FIRST PRINCIPLES</span><h2>A payment is not one number.</h2><p>It is a contract with five coordinates. Lose any one and a locally “successful” integration can change economic meaning.</p></div><div className="coordinate-grid">{coordinates.map(([name, question, guard], i) => <motion.article key={name} whileHover={{ y: -5 }} transition={{ duration: .2 }}><span>0{i + 1}</span><h3>{name}</h3><p>{question}</p><div><LockIcon size="small" />{guard}</div></motion.article>)}</div></section>;
}

function CurrencyLab() {
  const [currency, setCurrency] = useState<keyof typeof currencies>("JPY"); const item = currencies[currency];
  return <section className="section currency-lab"><div className="section-intro"><span className="kicker">02 · MONEY LAB</span><h2>Change the currency. Watch the same line of code change the price.</h2></div><div className="lab-card"><div className="currency-tabs">{Object.keys(currencies).map((key) => <button key={key} aria-pressed={currency === key} onClick={() => setCurrency(key as keyof typeof currencies)}>{key}</button>)}</div><div className="equation"><div><small>Alice typed</small><strong>{item.symbol}{item.entered}</strong></div><ArrowRightIcon /><div className="code-pill">amount × 100</div><ArrowRightIcon /><div className="wrong"><small>Generated request</small><strong>{item.generated}</strong><RoughMark kind="circle" /></div></div><div className="comparison"><div><span>Currency contract</span><strong>{item.intended} subunits</strong></div><div><span>Economic error</span><strong>{item.factor}</strong></div><div className="blocked"><span>RazorProof</span><strong>{item.verdict}</strong></div></div></div><figure className="evidence-wide" id="evidence"><img src={`${import.meta.env.BASE_URL}evidence/razorpay-orders-fresh-currency-pairs.png`} alt="Razorpay Test Mode orders showing JPY and KWD generated values beside exact controls" /><figcaption><b>Actual Razorpay Orders surface.</b> The provider accepted both the wrong generated integers and the exact controls. Razorpay did what the request asked; the integration lost the intent before the API call.</figcaption></figure></section>;
}

function ChainLab() {
  const [selected, setSelected] = useState(0); const chain: Chain = chains[selected];
  return <section className="section chains" id="chains"><div className="section-intro"><span className="kicker">03 · COMPOSITIONAL FAILURES</span><h2>Bugs do not queue politely. They chain.</h2><p>Choose a chain. Solid nodes are reproduced or provider-observed. Dashed nodes are explicitly labelled inference.</p></div><div className="chain-layout"><div className="chain-list" role="tablist" aria-label="Failure chains">{chains.map((item, index) => <button role="tab" aria-selected={selected === index} key={item.id} onClick={() => setSelected(index)}><span>0{index + 1}</span>{item.title.replace(" can combine with ", " + ")}</button>)}</div><AnimatePresence mode="wait"><motion.div className="chain-detail" key={chain.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: .28, ease }}><div className="chain-head"><Badge color="negative" icon={BugIcon}>FAILURE CHAIN</Badge><h3>{chain.title}</h3><p>{chain.proof_grade}</p></div><ol>{chain.nodes.map((node, i) => <li key={`${node.evidence}-${i}`} className={node.passed === null ? "inference" : "confirmed"}><span className="node-dot" /><div><small>{gradeLabel[node.state] ?? node.state}</small><p>{node.claim}</p><code>{node.evidence}</code></div></li>)}</ol><div className="prevention"><ShieldIcon /><div><strong>RazorProof breaks the chain</strong><p>{chain.razorproof_prevention.join(" · ")}</p></div></div></motion.div></AnimatePresence></div></section>;
}

function EvidenceGallery() {
  const shots = [
    ["razorpay-undercharge-order-detail.png", "Provider order detail", "A wrong integer is still a valid order."],
    ["github-browser-authored-amount-clip.png", "Official generator source", "The browser is allowed to author the economic amount."],
    ["github-dotnet-ascii-clip.png", "Official .NET SDK source", "Webhook text is converted with ASCII instead of preserving signed UTF-8 bytes."],
    ["github-mobile-empty-signature-clip.png", "Official generated mobile flow", "The success callback forwards an empty signature."],
  ];
  return <section className="section evidence"><div className="section-intro"><span className="kicker">04 · RECEIPTS, NOT RHETORIC</span><h2>Every consequential claim opens onto a real surface.</h2></div><div className="shot-grid">{shots.map(([src, title, caption]) => <figure key={src}><div><img src={`${import.meta.env.BASE_URL}evidence/${src}`} alt={caption} /></div><figcaption><strong>{title}</strong><span>{caption}</span></figcaption></figure>)}</div></section>;
}

function CaseExplorer() {
  const [query, setQuery] = useState(""); const [severity, setSeverity] = useState("all");
  const filtered = useMemo(() => findings.filter((f) => (severity === "all" || f.severity === severity) && `${f.title} ${f.surface} ${f.repo}`.toLowerCase().includes(query.toLowerCase())), [query, severity]);
  return <section className="section cases" id="cases"><div className="section-intro"><span className="kicker">05 · CASE FILES</span><h2>No pooled score. Open the counterexamples.</h2><p>Each case preserves its claim type and evidence strength. A hardening opportunity is never dressed up as a defect.</p></div><div className="case-tools"><label><SearchIcon size="small" /><span className="sr-only">Search cases</span><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search money, webhooks, mobile…" /></label><div className="severity-filters">{["all", "critical", "high", "medium", "low"].map((s) => <button key={s} aria-pressed={severity === s} onClick={() => setSeverity(s)}>{s}</button>)}</div></div><div className="case-count" aria-live="polite">Showing {filtered.length} inspectable case{filtered.length === 1 ? "" : "s"}</div><div className="case-list">{filtered.map((f) => <details key={f.id}><summary><span className={`severity ${f.severity}`}>{f.severity}</span><div><small>{f.repo} · {f.surface}</small><strong>{f.title}</strong><span>{claimLabel[f.claim_kind] ?? f.claim_kind} · {gradeLabel[f.level] ?? f.level}</span></div><ArrowRightIcon /></summary><div className="case-body"><div><small>What breaks</small><p>{f.impact}</p></div><div><small>Smallest counterexample</small><code>{f.counterexample || "Source contract mismatch"}</code></div><div><small>RazorProof enforcement</small><p>{f.proposed_fix}</p></div><div className="sources">{f.evidence.filter((e) => e.source_url).slice(0, 3).map((e) => <a key={`${e.source_url}-${e.line}`} href={e.source_url} target="_blank" rel="noreferrer"><ExternalLinkIcon size="small" />{e.summary}</a>)}</div></div></details>)}</div></section>;
}

function Boundary() {
  return <section className="section boundary" id="boundary"><div className="boundary-copy"><span className="kicker light">06 · THE PRODUCT</span><h2>One executable boundary between intention and irreversible effect.</h2><p>RazorProof is the merchant-side authority. It prices from trusted server data, converts money exactly, claims one durable effect identity, fixes the tenant before dispatch, verifies raw webhook bytes, re-fetches provider state, and releases fulfillment once.</p><Button href="https://github.com/Achxy/RazorLean/tree/main/razorproof-rs" target="_blank" rel="noreferrer" icon={CodeSnippetIcon} color="white" variant="secondary">Read the Rust workspace</Button></div><div className="boundary-map"><div className="map-node muted">Browser intent</div><ArrowRightIcon /><div className="firewall"><ShieldIcon size="large" /><strong>RAZORPROOF</strong>{["quote", "money", "principal", "effect", "bytes", "lifecycle"].map((x) => <span key={x}><CheckCircleIcon size="small" />{x}</span>)}</div><ArrowRightIcon /><div className="map-node provider">Razorpay API</div></div></section>;
}

export function App() { return <><Header /><main id="main-content"><Hero /><GroundUp /><CurrencyLab /><ChainLab /><EvidenceGallery /><CaseExplorer /><Boundary /></main><footer><div className="brand"><span className="brand-glyph">RL</span><span>RazorLean</span></div><p>Built by Achyuth Jayadevan · MIT licensed · Evidence is sanitized; credentials, signatures, payloads, contact data, and provider IDs are excluded.</p><a href="https://github.com/Achxy/RazorLean">GitHub <ArrowRightIcon size="small" /></a></footer></>; }
