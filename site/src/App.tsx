/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode, RefObject } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { chains, claimLabel, coordinates, currencies, findings, gradeLabel } from "./data/evidence";

const asset = (name: string) => `${import.meta.env.BASE_URL}evidence/${name}`;

function ProgressRail({ root }: { root: RefObject<HTMLDivElement | null> }) {
  const [progress, setProgress] = useState(0);
  useEffect(() => {
    const node = root.current;
    if (!node) return;
    const update = () => setProgress(node.scrollTop / Math.max(1, node.scrollHeight - node.clientHeight));
    update(); node.addEventListener("scroll", update, { passive: true });
    return () => node.removeEventListener("scroll", update);
  }, [root]);
  return <div className="progress-rail" aria-hidden="true"><span style={{ transform: `scaleY(${progress})` }} /></div>;
}

function AliceBob() {
  return <svg className="alice-bob" viewBox="0 0 920 210" role="img" aria-label="Alice sends a payment intent through generated integration code to Bob's store">
    <g className="person alice"><circle cx="85" cy="62" r="24"/><path d="M85 86v62M85 105l-38 27M85 105l38 27M85 148l-28 48M85 148l28 48"/><text x="85" y="20">ALICE</text></g>
    <g className="person bob"><circle cx="835" cy="62" r="24"/><path d="M835 86v62M835 105l-38 27M835 105l38 27M835 148l-28 48M835 148l28 48"/><text x="835" y="20">BOB</text></g>
    <path className="intent-line" d="M145 108H775"/><path className="arrow" d="M759 96l18 12-18 12"/>
    <text className="intent" x="460" y="88">one economic intent</text><text className="sub" x="460" y="134">price · currency · cart · merchant · effect</text>
  </svg>;
}

function MoneyExperiment() {
  const [currency, setCurrency] = useState<keyof typeof currencies>("JPY");
  const c = currencies[currency];
  return <div className="experiment money-experiment">
    <div className="experiment-controls" role="group" aria-label="Currency example">
      {(Object.keys(currencies) as (keyof typeof currencies)[]).map((key) => <button key={key} aria-pressed={currency === key} onClick={() => setCurrency(key)}>{key}</button>)}
    </div>
    <div className="equation-line" aria-live="polite">
      <div><i>merchant meant</i><strong>{c.symbol}{c.entered}</strong></div><span>→</span><div><i>generated rule</i><code>round(amount × 100)</code></div><span>→</span><div className="error-value"><i>provider receives</i><strong>{c.generated}</strong></div>
    </div>
    <div className="verdict-line"><span>currency contract: {c.intended} subunits</span><b>{c.factor}</b><span>RazorProof: {c.verdict.toLowerCase()}</span></div>
  </div>;
}

const signedFields = [
  ["razorpay_order_id", true], ["razorpay_payment_id", true], ["provider signature", true],
  ["Bob's catalogue price", false], ["Alice's cart", false], ["currency exponent", false], ["merchant tenant", false],
] as const;

function SignatureExperiment() {
  const [focus, setFocus] = useState(0);
  return <div className="experiment signature-experiment">
    <div className="signed-expression"><span>HMAC</span><b>( order_id | payment_id )</b><span>= valid</span></div>
    <div className="signature-scope">
      <div className="scope-list">{signedFields.map(([name, signed], index) => <button key={name} onClick={() => setFocus(index)} aria-pressed={focus === index}><span>{signed ? "✓" : "×"}</span>{name}</button>)}</div>
      <AnimatePresence mode="wait"><motion.div className={signedFields[focus][1] ? "scope-answer signed" : "scope-answer unsigned"} key={focus} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}><small>{signedFields[focus][1] ? "AUTHENTICATED" : "OUTSIDE THE SIGNATURE"}</small><strong>{signedFields[focus][0]}</strong><p>{signedFields[focus][1] ? "Razorpay can prove this provider field is authentic." : "A valid provider signature says nothing about whether this still matches the merchant's original intent."}</p></motion.div></AnimatePresence>
    </div>
  </div>;
}

function CoordinateExperiment() {
  const [present, setPresent] = useState([true, true, true, true, true]);
  const missing = present.filter((value) => !value).length;
  return <div className="experiment coordinate-experiment">
    <div className="coordinate-switches">{coordinates.map(([name, question], index) => <button key={name} aria-pressed={present[index]} onClick={() => setPresent((old) => old.map((value, i) => i === index ? !value : value))}><span>{present[index] ? "●" : "○"}</span><b>{name}</b><small>{question}</small></button>)}</div>
    <div className={`semantic-state ${missing ? "incomplete" : "complete"}`}><small>SEMANTIC IDENTITY</small><strong>{5 - missing} / 5</strong><p>{missing ? `${missing} coordinate${missing > 1 ? "s are" : " is"} missing. “Paid” is not enough to authorize fulfillment.` : "Complete. This payment can be compared with the original intent."}</p></div>
  </div>;
}

function ChainExperiment() {
  const [selected, setSelected] = useState(1);
  const chain = chains[selected];
  return <div className="chain-experiment">
    <div className="chain-index">{chains.map((item, index) => <button key={item.id} aria-pressed={selected === index} onClick={() => setSelected(index)}><span>0{index + 1}</span>{item.title}</button>)}</div>
    <AnimatePresence mode="wait"><motion.div className="chain-plot" key={chain.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      {chain.nodes.map((node, index) => <div className={node.passed === null ? "inferred" : "observed"} key={`${node.evidence}-${index}`}><span>{index + 1}</span><p>{node.claim}</p><small>{gradeLabel[node.state] ?? node.state}</small></div>)}
      <div className="chain-break"><b>RazorProof breaks this chain at the boundary</b><p>{chain.razorproof_prevention.join(" · ")}</p></div>
    </motion.div></AnimatePresence>
  </div>;
}

function EvidencePair() {
  const [zoomed, setZoomed] = useState<null | string>(null);
  const shots = [
    ["razorpay-orders-fresh-currency-pairs.png", "Razorpay Orders", "Generated JPY and KWD integers persisted beside exact controls."],
    ["github-browser-authored-amount-clip.png", "Generated checkout", "The browser supplies the amount that becomes the provider order."],
    ["github-dotnet-ascii-clip.png", ".NET webhook verifier", "Signed text is re-encoded as ASCII instead of preserving raw UTF-8 bytes."],
    ["github-mobile-empty-signature-clip.png", "Generated mobile verifier", "The success path forwards an empty signature."],
  ];
  return <><div className="evidence-grid">{shots.map(([src, title, note]) => <button key={src} onClick={() => setZoomed(src)}><img src={asset(src)} alt={note}/><span><b>{title}</b>{note}</span></button>)}</div>{zoomed && <div className="lightbox" role="dialog" aria-modal="true" aria-label="Evidence image" onClick={() => setZoomed(null)}><button aria-label="Close evidence">close ×</button><img src={asset(zoomed)} alt="Expanded evidence" /></div>}</>;
}

function CaseIndex() {
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => findings.filter((f) => `${f.title} ${f.repo} ${f.surface} ${f.claim_kind}`.toLowerCase().includes(query.toLowerCase())), [query]);
  return <div className="case-index"><label><span>filter the notebook</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="money, tenant, mobile, webhook…" /></label><p className="result-count">{filtered.length} distinct counterexamples match</p>{filtered.map((finding) => <details key={finding.id}><summary><span className={`sev ${finding.severity}`}>{finding.severity}</span><b>{finding.title}</b><small>{finding.repo} · {claimLabel[finding.claim_kind] ?? finding.claim_kind} · {gradeLabel[finding.level] ?? finding.level}</small></summary><div><p><i>What breaks.</i> {finding.impact}</p><p><i>Counterexample.</i> <code>{finding.counterexample || "Source contract mismatch"}</code></p><p><i>Boundary rule.</i> {finding.proposed_fix}</p>{finding.evidence.filter((e) => e.source_url).slice(0, 3).map((e) => <a key={`${e.source_url}-${e.line}`} href={e.source_url} target="_blank" rel="noreferrer">↗ {e.summary}</a>)}</div></details>)}</div>;
}

function ArticleSection({ number, title, children }: { number: string; title: string; children: ReactNode }) {
  return <section><div className="section-number">{number}</div><h2>{title}</h2>{children}</section>;
}

export function App() {
  const scrollRef = useRef<HTMLDivElement>(null);
  return <div className="document"><header><a href="https://github.com/Achxy/RazorLean">(back to the repository)</a><strong>RazorLean</strong></header><div className="scroll-surface" ref={scrollRef}><ProgressRail root={scrollRef}/><main id="main-content">
    <div className="title-block"><p>AN EXECUTABLE ARGUMENT ABOUT PAYMENT CORRECTNESS</p><h1>How a payment can be<br/><em>valid</em> — and wrong.</h1><div>From one impossible order to the semantic firewall that prevents an entire class of failures.</div></div>
    <ArticleSection number="I" title="Start with Alice, Bob, and one price"><p>Alice wants an item from Bob's store. Bob says it costs ¥295. There is only one economic intent: Alice pays that price, to that merchant, for that cart, once.</p><AliceBob/><p>The payment stack will represent that intent many times: browser state, JSON, SDK types, an API request, an order, a signature, a webhook, and finally a fulfillment decision. Every translation is a chance to preserve the meaning or quietly change it.</p></ArticleSection>
    <ArticleSection number="II" title="The first translation already breaks"><p>The generated integration accepts a major-unit number and applies one rule to every currency. Try the same line against currencies with two, zero, and three decimal places.</p><MoneyExperiment/><p><strong>Nothing inside Razorpay has to malfunction.</strong> The API receives a legal integer and creates the requested order. That is precisely why the defect survives: every local component can report success while the global statement is false.</p><figure className="hero-evidence"><img src={asset("razorpay-orders-fresh-currency-pairs.png")} alt="Razorpay Test Mode order rows showing generated and exact JPY and KWD values"/><figcaption>Actual Razorpay Test Mode orders. Generated values and exact controls were both accepted and persisted.</figcaption></figure></ArticleSection>
    <ArticleSection number="III" title="A signature authenticates bytes, not meaning"><p>Checkout verification commonly computes a digest over the provider order and payment identifiers. That answers an important but narrower question: “Did Razorpay issue this tuple?” It cannot answer “Is this the order Bob intended?”</p><SignatureExperiment/><p>A genuine signature over a wrong-priced order remains genuine. RazorProof therefore verifies the provider tuple <em>and</em> binds it back to a server-authored quote containing the price, currency, cart identity, tenant, and one-time fulfillment state.</p></ArticleSection>
    <ArticleSection number="IV" title="A payment has five coordinates"><p>Think of payment identity as a five-dimensional point. Remove any coordinate below and observe how a reassuring status word stops being sufficient.</p><CoordinateExperiment/></ArticleSection>
    <ArticleSection number="V" title="The dangerous failures are compositions"><p>The one-paise mutation is a useful microscope slide. The severe cases appear when individually plausible behaviours compose across retries, tenants, mobile callbacks, webhooks, and fulfillment.</p><ChainExperiment/></ArticleSection>
    <ArticleSection number="VI" title="Receipts, not rhetoric"><p>These are not recreations of a dashboard. Open any image to inspect the provider surface or the pinned official source that produced the claim.</p><EvidencePair/></ArticleSection>
    <ArticleSection number="VII" title="The entire failure notebook"><p>There is deliberately no aggregate “proof score.” Each entry stands or falls on its own counterexample, claim type, evidence grade, and source.</p><CaseIndex/></ArticleSection>
    <ArticleSection number="VIII" title="RazorProof makes the missing type explicit"><p>Most integrations pass loose JSON between layers. RazorProof instead treats the payment as a value that cannot advance until every coordinate agrees.</p><pre className="type-system"><span>PaymentIntent</span> &lt;Value, Principal, Effect, Provenance, Lifecycle&gt;{"\n"}{"\n"}<i>browser claim</i> ──parse──▶ <b>server quote</b>{"\n"}                           │{"\n"}                     exact money{"\n"}                           │{"\n"}                           ▼{"\n"}<b>provider order</b> ──re-fetch──▶ <b>verified transition</b>{"\n"}                           │{"\n"}                     consume once{"\n"}                           ▼{"\n"}                       Fulfilled</pre><p>The AI can search for counterexamples and compose failure chains. It never decides whether money may move. That authority remains deterministic Rust.</p><div className="closing"><h2>Make the state transition prove what the human meant.</h2><a href="https://github.com/Achxy/RazorLean/tree/main/razorproof-rs">read the Rust boundary →</a></div></ArticleSection>
  </main></div></div>;
}
