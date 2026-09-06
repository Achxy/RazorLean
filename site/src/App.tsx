/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import type { ReactNode } from "react";
import { MotionConfig } from "motion/react";
import { chains, gradeLabel } from "./data/evidence";
import { FieldGuide } from "./field-guide/FieldGuide";
import { MoneyChapter } from "./microscope/MoneyChapter";
import { RetryLab } from "./components/RetryLab";
import { BoundaryLab } from "./components/BoundaryLab";
import { BytesLab } from "./components/BytesLab";
import { GitHubSnippet } from "./components/GitHubSnippet";
import "./labs.css";

const asset = (name: string) => `${import.meta.env.BASE_URL}evidence/${name}`;

function EvidencePair() {
  return (
    <div className="source-embeds">
      <GitHubSnippet source="checkout" />
      <GitHubSnippet source="mobile" />
    </div>
  );
}

function Section({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section id={id}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export function App() {
  return (
    <MotionConfig
      reducedMotion="user"
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      <div className="document">
        <header>
          <a href="https://github.com/Achxy/RazorLean">
            (back to the repository)
          </a>
          <strong>RazorLean</strong>
        </header>
        <div className="scroll-surface">
          <main id="main-content">
            <MoneyChapter />
            <details className="evidence-inline">
              <summary>
                Compare the model with the recorded Razorpay orders
              </summary>
              <figure>
                <img
                  src={asset("razorpay-orders-fresh-currency-pairs.png")}
                  alt="Recorded Razorpay Test Mode order rows comparing generated and exact JPY and KWD values"
                />
                <figcaption>
                  These Test Mode orders were accepted and persisted. This
                  establishes order creation, not JPY or KWD capture,
                  settlement, or a real customer being charged.
                </figcaption>
              </figure>
            </details>
            <nav className="essay-nav" aria-label="Experiments">
              <a href="#retry">Lose a response ↓</a>
              <a href="#bytes">Inspect the bytes ↓</a>
              <a href="#boundary">Build the handler ↓</a>
              <a href="#notebook">Inspect the findings ↓</a>
            </nav>
            <Section id="retry" title="Now lose the response, not the money.">
              <p>
                Bob sends Alice a refund. The provider processes it, but the
                network drops the acknowledgement. Bob sees a timeout. Should he
                retry?
              </p>
              <p>
                The problem is that a timeout describes Bob’s knowledge, not the
                provider’s state. Run the sequence once, then preserve the
                effect identity and replay it.
              </p>
              <RetryLab />
              <p>
                RazorProof’s durable intent record distinguishes a new operation
                from a replay or a conflicting payload. An ambiguous external
                write still needs reconciliation with the provider before
                another write is safe.
              </p>
            </Section>
            <Section
              id="bytes"
              title="The same-looking text can be different bytes."
            >
              <p>
                Razorpay signs a webhook’s payload bytes. The verifier must
                authenticate those same bytes. A text conversion between
                receiving and verifying the event can change the message without
                changing what the developer thinks it says.
              </p>
              <BytesLab />
              <GitHubSnippet source="ascii" />
            </Section>
            <Section
              id="boundary"
              title="A valid event still needs permission to act."
            >
              <p>
                Checkout’s signature binds the order and payment identifiers. It
                does not independently certify Bob’s catalogue price, Alice’s
                cart, or whether an earlier event already fulfilled the
                purchase.
              </p>
              <p>
                A webhook handler has to preserve both authenticity and business
                intent. Here is a deliberately misordered program. You can fix
                it.
              </p>
              <BoundaryLab />
              <p>
                The Rust boundary supplies exact money, quote binding,
                tenant-scoped provider access, and durable effect state. This
                little program illustrates the sequencing requirement; it is not
                a browser port of the Rust runtime or a proof of complete API
                coverage.
              </p>
            </Section>
            <Section
              id="compositions"
              title="Where the small failures join up."
            >
              <p>
                The interesting unit is often a chain: a value is changed, a
                later component accepts it, and an application interprets that
                acceptance too broadly. Each recorded chain below separates
                observations from inferred consequences.
              </p>
              <div className="chain-notes">
                {chains.map((chain) => (
                  <details key={chain.id}>
                    <summary>{chain.title}</summary>
                    <ol>
                      {chain.nodes.map((node, i) => (
                        <li key={i}>
                          <p>{node.claim}</p>
                          <small>{gradeLabel[node.state] ?? node.state}</small>
                        </li>
                      ))}
                    </ol>
                    <p>
                      <i>Mitigation path:</i>{" "}
                      {chain.razorproof_prevention.join(" · ")}
                    </p>
                  </details>
                ))}
              </div>
            </Section>
            <Section id="sources" title="Look at the original surface.">
              <p>
                These excerpts load directly from Razorpay’s official GitHub
                repositories. Click any line number to inspect it in context.
                Each excerpt is pinned to the commit used by the investigation.
              </p>
              <EvidencePair />
            </Section>
            <Section
              id="notebook"
              title="An illustrated field guide to the failures"
            >
              <p>
                Each plate follows one mechanism from intention to failure to
                correction. Choose a case, play its sequence, then inspect the
                source and the limits of the evidence. The drawings explain the
                contracts; they do not send requests or simulate an exploit.
              </p>
              <FieldGuide />
            </Section>
            <Section
              id="implementation"
              title="What the product actually owns."
            >
              <p>
                RazorLean contains RazorProof, a Rust payment boundary and
                evidence tooling. The boundary can reject an invalid
                representation, bind an operation to the intended merchant and
                quote, and keep a durable record of effects. It cannot repair an
                upstream SDK merely by reporting a defect.
              </p>
              <p>
                The experiments here are browser-local teaching models. The
                screenshots and linked artifacts are recorded observations. The
                Rust implementation and its tests are the place to inspect
                enforcement.
              </p>
              <a href="https://github.com/Achxy/RazorLean/tree/main/razorproof-rs">
                Read the Rust implementation →
              </a>
              <p className="design-credit">
                Interaction references:{" "}
                <a href="https://www.redblobgames.com/making-of/little-things/">
                  Red Blob’s linked diagrams
                </a>{" "}
                and <a href="https://motion.dev/docs/react-animation">Motion</a>
                .
              </p>
            </Section>
          </main>
        </div>
      </div>
    </MotionConfig>
  );
}
