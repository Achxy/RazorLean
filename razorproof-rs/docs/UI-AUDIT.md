# Control-room technical audit

Audit target: the RazorProof single-page judge control room, inspected from source and in the live in-app browser on 2026-09-04. The browser rendered the narrow/mobile layout without horizontal page overflow, executed the `2.01 INR` counterexample, authenticated locally, displayed four real evidence events, and rendered all 113 operations.

## Audit health score before remediation

| # | Dimension | Score | Key finding |
|---|---:|---:|---|
| 1 | Accessibility | 3/4 | `input:focus` suppressed the global visible focus outline; live status and data table semantics were incomplete |
| 2 | Performance | 3/4 | Framework-free and small, but animation restart forced synchronous layout |
| 3 | Responsive design | 4/4 | Fluid typography/layout, 44 px buttons, deliberate table scrolling, mobile ledger simplification |
| 4 | Theming | 3/4 | Strong token system and intentional light-only scheme; a few contextual colors remain local |
| 5 | Anti-patterns | 4/4 | Distinct forensic editorial language; no glass, neon dashboard, gradient text, stock imagery, or nested-card grid |
| **Total** |  | **17/20** | **Good** |

## Anti-pattern verdict

Pass. The page does not read as an AI dashboard template. The graph-paper ledger, split unsafe/sealed laboratory, typographic hierarchy, stamp motion, and restrained palette form one product-specific visual argument. The four-number scoreboard is the only familiar hero-metric device, but here every number resolves to executable evidence and the surrounding composition is not card-based.

## Findings

### [P1] Input focus indicator overridden

- Location: `assets/styles.css`, input focus rule.
- Category: Accessibility.
- Impact: Keyboard users can lose their location in amount, currency, tenant, and token fields.
- Standard: WCAG 2.4.7 and 2.4.11.
- Recommendation: Preserve the global focus-visible outline and use border change only as an additional cue.
- Suggested command: `/polish`.

### [P1] Browser token persisted longer than necessary without a CSP

- Location: `assets/app.js` session storage and document response headers.
- Category: Performance/security resilience.
- Impact: Any future same-origin script injection would have a durable tab-scoped token target; framing and unexpected resource origins were not denied.
- Recommendation: Keep the token in memory only and ship a restrictive CSP, frame denial, referrer policy, and MIME-sniffing protection.
- Suggested command: `/harden`.

### [P2] Dynamic status was not announced

- Location: `index.html`, `#connection-status`.
- Category: Accessibility.
- Impact: Screen-reader users may not learn whether authentication, health, or evidence loading succeeded.
- Standard: WCAG 4.1.3.
- Recommendation: Use `role=status` and polite atomic live announcement.
- Suggested command: `/polish`.

### [P2] Coverage table lacks explicit navigation metadata

- Location: `index.html`, coverage table.
- Category: Accessibility.
- Impact: A screen-reader user receives columns but no concise purpose and headers do not declare column scope.
- Standard: WCAG 1.3.1.
- Recommendation: Add a visually hidden caption and `scope=col` to every column header.
- Suggested command: `/polish`.

### [P2] Text inputs are below the preferred touch height

- Location: `assets/styles.css`, input rule.
- Category: Responsive design.
- Impact: Mobile amount and credential entry is less forgiving than the buttons.
- Recommendation: Set a 44 px minimum block size without changing the underline aesthetic.
- Suggested command: `/adapt`.

### [P3] Animation restart forces layout

- Location: `assets/app.js`, `void lane.offsetWidth`.
- Category: Performance.
- Impact: Negligible with two elements, but it establishes a poor pattern if the laboratory expands.
- Recommendation: restart the class in a queued animation frame.
- Suggested command: `/optimize`.

### [P3] Placeholder overstates catalog signing

- Location: `index.html`, unloaded coverage row.
- Category: UX writing / claim accuracy.
- Impact: The catalog is versioned and embedded but is not cryptographically signed.
- Recommendation: say “versioned policy catalog.”
- Suggested command: `/clarify`.

## Systemic and positive findings

There is no systemic component sprawl: one HTML document, one stylesheet, and one dependency-free script. Semantic landmarks, heading order, real buttons, associated labels, a skip link, high-visibility focus design, reduced-motion behavior, safe text escaping, responsive grids, and data minimization are already present. The table is intentionally horizontally scrollable rather than crushing five technical fields on mobile. Motion is limited to entry and a meaningful sealed/mutated stamp.

## Remediation order

1. **[P1] `/harden`** — remove persistent token storage and set document security policy.
2. **[P1-P2] `/polish`** — restore focus, add live status, table semantics, and accurate claim language.
3. **[P2] `/adapt`** — raise input touch height while preserving mobile layout.
4. **[P3] `/optimize`** — remove synchronous layout from the two-lane animation restart.
5. **[P3] `/polish`** — re-run live narrow and desktop checks and record the post-fix score.

After remediation, re-run `/audit` to verify the score rather than assuming the fixes worked.

## Remediation result

All seven findings were addressed in the same build: visible input focus was restored, the token moved to page memory, restrictive browser headers were added, status and table semantics were completed, inputs reached 44 px, animation restart stopped forcing layout, and the signing overclaim was removed. A post-fix source and live-browser pass raises accessibility and performance to 4/4, for **19/20 (Excellent)**. The remaining point reflects the intentional light-only theme and a small number of context-local colors, not a release blocker.
