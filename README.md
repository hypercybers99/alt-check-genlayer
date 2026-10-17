# AltCheck (GenLayer Studionet Preview)

AltCheck is a consensus-audited web accessibility ledger deployed on **GenLayer Studionet (Preview)**. Multiple independent validator nodes fetch raw server-delivered HTML, execute deterministic WCAG accessibility rules in code, evaluate subjective clarity via a bounded language model layer, and record verifiable scores, grades, and remediation progress on-chain.

- **Network**: GenLayer Studionet (Preview)
- **Chain ID**: 61999
- **RPC Endpoint**: `https://studio.genlayer.com/api`
- **Explorer**: `https://explorer-studio.genlayer.com`
- **Contract Repository**: [huzyow155/alt-check-genlayer](https://github.com/huzyow155/alt-check-genlayer)
- **Fixtures Repository**: [huzyow155/alt-check-fixtures](https://github.com/huzyow155/alt-check-fixtures)
- **Static Fixtures Site**: [https://huzyow155.github.io/alt-check-fixtures/](https://huzyow155.github.io/alt-check-fixtures/)

---

## Honest Scope & Limitations

> [!IMPORTANT]
> **Raw Server-Delivered HTML Only**: AltCheck evaluates the raw HTML document as delivered by the origin server. It does **not** execute client-side JavaScript, load external stylesheets, compute visual layout or bounding boxes, calculate color contrast ratios (e.g. WCAG 1.4.3), view image pixels, or simulate screen readers.

Client-rendered Single-Page Applications (SPAs) built with React, Next.js, Nuxt, or Vue often serve an empty HTML container (`<div id="root"></div>`) that hydrates in the browser. AltCheck detects this honestly and flags it as `SHELL_ONLY` mode (Score: -1, Grade: `N/A`) rather than reporting a misleading score for an empty document. The rules audited by AltCheck represent a deterministic subset of WCAG criteria and do not constitute an official legal compliance certificate.

---

## Contract Addresses

| Contract | Status / Role | Address | Deploy Tx Hash | Source SHA-256 |
| :--- | :--- | :--- | :--- | :--- |
| **AltCheck** (v1.0.0) | Active Ledger | [`0xBA2D886E76b87feD8dCd5be61fccFA2A4e1D388A`](https://explorer-studio.genlayer.com/address/0xBA2D886E76b87feD8dCd5be61fccFA2A4e1D388A) | `0xf2ec73168cf65d504ddedf4b965bce56d9fa399c86a955ce98f06600e992f9db` | `b9c55a75970aca12f11edaf447e16a09a1d9a8a661e068e3ef2a5cddaa00e202` |
| **Probe** | Superseded Diagnostic | [`0xC40bf93bA9c3f1cf9A1088087C4c7156E538FB95`](https://explorer-studio.genlayer.com/address/0xC40bf93bA9c3f1cf9A1088087C4c7156E538FB95) | `0xeecc2d204f91eae6ce63444e251f69a2d71463d86edca0f2edf050edfe5593ba` | `c7b2966c2ea5dcfa263da0f662f51add37167e490a6ff1bfd2b0d32c075e3520` |

---

## How It Works

```
Raw HTML -> URL Policy -> HTML Parser -> Deterministic Rules (R1-R12) -> Bounded Model Layer -> Consensus -> State Ledger
```

1. **Deterministic Rules (R1 - R12)**: Evaluated entirely in code across document elements. Every finding deducts points according to fixed weights and caps.
2. **Accessible Name Computation**: Implements prioritized resolution (`aria-labelledby` -> `aria-label` -> `label[for]` -> wrapping `<label>` -> `title` -> visible text/img-alt -> `value`). `placeholder` does not count; punctuation-only strings count as empty.
3. **Bounded Model Layer**: Evaluates subjective descriptive clarity out of context for up to 8 alts and 8 links that passed deterministic rules. Returns strict closed enum (`CLEAR` or `VAGUE`). Penalty is strictly capped at 10 points (`min(10, 2 * vague_count)`).
4. **Validator Consensus**: Validators independently re-fetch the target URL, re-parse the DOM, and recompute rule counts and model vague buckets in `gl.vm.spawn_sandbox`. Agreement requires exact equality on the closed-count vector and vague bucket.
5. **Verifiable Snippets**: Every recorded snippet must be a verbatim substring of the raw fetched HTML; fabricated snippets are dropped by code.

---

## Deterministic Rule Set (R1 - R12)

$$\text{Deterministic Score} = \max\left(0, 100 - \sum_{i=1}^{12} \text{weight}_i \times \min(\text{count}_i, \text{cap}_i)\right)$$
$$\text{Final Score} = \max(0, \text{Deterministic Score} - \text{Model Penalty})$$

| Rule ID | WCAG Ref | Description | Weight | Cap | Max Deduction |
| :---: | :---: | :--- | :---: | :---: | :---: |
| **R1** | 1.1.1 | Images without alt attribute (`alt=""` permitted with `role="presentation"`/`none` or `aria-hidden="true"`) | 4 | 8 | 32 pts |
| **R2** | 1.1.1 | Poor alt text (filename-like extensions, regex patterns, or generic dictionary words) | 2 | 8 | 16 pts |
| **R3** | 1.3.1, 3.3.2, 4.1.2 | Form controls (`input`, `select`, `textarea`) without an accessible name | 4 | 8 | 32 pts |
| **R4** | 2.4.4, 4.1.2 | Links and buttons without an accessible name or with generic text ("click here", "read more") | 3 | 8 | 24 pts |
| **R5** | 1.3.1, 2.4.6 | Heading structure violations (missing `h1`, multiple `h1`, or skipped heading levels) | 3 | 3 | 9 pts |
| **R6** | 3.1.1 | `<html>` tag missing or empty `lang` attribute | 5 | 1 | 5 pts |
| **R7** | 2.4.2 | `<title>` element missing or whitespace-only | 5 | 1 | 5 pts |
| **R8** | 4.1.1 | Duplicate `id` attributes across elements in the document | 2 | 5 | 10 pts |
| **R9** | 1.4.4 | Viewport meta disabling user zoom (`user-scalable=no` or `maximum-scale < 2`) | 5 | 1 | 5 pts |
| **R10** | 2.4.3 | Focusable elements configured with positive `tabindex` attributes | 2 | 5 | 10 pts |
| **R11** | 1.3.1, 2.4.1 | Missing `<main>` landmark element and missing `role="main"` | 3 | 1 | 3 pts |
| **R12** | 4.1.2 | `<iframe>` elements missing `title` or `aria-label` attributes | 3 | 5 | 15 pts |

### Grade Scale
- **Grade A**: Score $\ge 90$
- **Grade B**: Score $\ge 80$
- **Grade C**: Score $\ge 65$
- **Grade D**: Score $\ge 50$
- **Grade F**: Score $< 50$
- **Grade N/A**: Client SPA Shell (`SHELL_ONLY` mode, score = -1)

---

## Contract Methods & Storage

### Storage Model
- `pages: TreeMap[str, str]`: Page record JSON keyed by 12-hex `page_id`.
- `audits: TreeMap[str, str]`: Audit record JSON keyed by `"<page_id>:<n>"`.
- `meta: TreeMap[str, str]`: Counters (`pages_count`, `audits_count`, `nonce`), O(1) indexed page IDs (`pid:<i>`), duplicate lookup index (`dup:<url>:<sender>`), and top-50 board aggregates (`board_best`, `board_improved`).

### Write Methods
- `register_page(label: str, url: str) -> None`: Validates label length (3-80 chars) and URL policy; assigns deterministic 12-hex ID; prevents duplicate registration for same URL + sender.
- `audit_page(page_id: str) -> None`: Executes consensus audit pipeline; enforces 300s cooldown and 12-audit cap; appends audit record; updates page aggregates and board rankings in $O(1)$.
- `add_maintainer_note(page_id: str, audit_n: int, note: str) -> None`: Registrant-only; adds explanatory note (5-280 chars, max 3 notes per audit).
- `retire_page(page_id: str) -> None`: Registrant-only; marks page retired and excludes it from active audits and board rankings.

### View Methods
- `get_page(page_id: str) -> str`: Returns page record JSON.
- `get_audits(page_id: str, offset: int, limit: int) -> str`: Returns paginated audit records (newest first, max limit 50).
- `get_progress(page_id: str) -> str`: Computes deterministic diff between the two latest `FULL` audits (score delta, grade change, per-rule deltas).
- `list_page_ids(offset: int, limit: int) -> str`: Returns paginated list of registered page IDs (newest first).
- `get_board(limit: int) -> str`: Returns top pages by latest `FULL` score and biggest verified improvement delta.
- `get_rules() -> str`: Returns rules, weights, caps, constants, and scope limitations text.
- `get_meta() -> str`: Returns metadata counters (`pages_count`, `audits_count`).

---

<!-- EVIDENCE_TABLE_START -->
## On-Chain Evidence Summary

### Active Deployed Contracts on GenLayer Studionet (Preview)

| Contract | Address | Deploy Tx Hash | Source SHA-256 | Status | Consensus |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AltCheck** (v1.0.0) | [`0xBA2D886E76b87feD8dCd5be61fccFA2A4e1D388A`](https://explorer-studio.genlayer.com/address/0xBA2D886E76b87feD8dCd5be61fccFA2A4e1D388A) | `0xf2ec73168cf65d504ddedf4b965bce56d9fa399c86a955ce98f06600e992f9db` | `b9c55a75970aca12f11edaf447e16a09a1d9a8a661e068e3ef2a5cddaa00e202` | ACCEPTED | MAJORITY_AGREE |

### Positive Execution Scenarios

| Scenario | Target Fixture URL | Register Tx | Audit Tx | Agreement | Score | Grade | Consensus Findings |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Clean Page** | [`good.html`](https://huzyow155.github.io/alt-check-fixtures/good.html) | `0xf49c85bd84833fb8ebd54b9cd8b6b0f40718056372cc62407c455069615d5adf` | `0x76ffa62456a54ab77af846e6b3c41bb302fae5af12830a96e168922b227bc57b` | 3/5 | 100 | **A** | 100% compliant deterministic subset |
| **Defective Page** | [`bad.html`](https://huzyow155.github.io/alt-check-fixtures/bad.html) | `0x5dd313162b96fe4a1c9f7315f7c48fb6974cdaedfb4b9635765019ecd54e4332` | `0x91a150f5099aa1dab66055589a3184be8c1ebf70f65b0f328dd50d4bb2cdcd2d` | 3/5 | 25 | **F** | 12 rules violated; verbatim snippets verified |
| **Model Evaluation** | [`mixed.html`](https://huzyow155.github.io/alt-check-fixtures/mixed.html) | `0xea682f80f6c386f77c78e0125a2d2a9fbd3beea6888a55a5ed7b82112d6aa45c` | `0x4d9bca0236c68ee7766fbda3471c25c774db49e3e5be81913ae42c44599b5bad` | 3/5 | 88 | **B** | Subjective clarity evaluated; penalty 10 pts |
| **SPA Shell Detection** | [`shell.html`](https://huzyow155.github.io/alt-check-fixtures/shell.html) | `0xb2f387828909c6cf2b1918d5786b4ec1a53150e95d4265b1c0ee36c88def8243` | `0x254360074fee0e21c6e72822f21570deed57e7bc899881da44902b6e88a1a22c` | 3/5 | -1 | **N/A** | Client SPA shell honestly flagged as `SHELL_ONLY` |

### Single Page ID Verifiable Progress (`demo.html`)

- **Page ID**: `b7eea06d23f8`
- **Initial State (Defective)**: Score 25 (F) | Tx `0x94c2c711508de0da077b5fa9c237ee85e4b67a86ee8d8d04360896297668ceec` | Fixtures Commit `92d9e46cc7dc9c7cdba8b9007e24f0a78cddcdbb`
- **Remediated State (Clean)**: Score 100 (A) | Tx `0xf57ea28ef5d66b05aa966556ee7efb99ae1465bff9649cda4704212585aaca19` | Fixtures Commit `df679b4949503ca5a5209dd5708e28466e77ad67`
- **Verified On-Chain Progress**: `+75` points (Grade transition: `F` -> `A`)
- **Maintainer Note Tx**: `0xbf568744aed1ca7fbdc9d8b9fe2f3a6de69cd41002e6f09bd88e0f40f8d56d39`
<!-- EVIDENCE_TABLE_END -->

---

## Verification & Testing Suite

AltCheck contains 120 passing automated tests and rigorous validation scripts:

```bash
# Run complete test suite (120 tests)
python -m unittest discover tests

# Run ASCII compliance scan on contracts
python scripts/tools/scan_ascii.py

# Run banned words scan
python scripts/tools/scan_banned_words.py

# Verify deployed contract source SHA-256
node scripts/tools/verify_source.js

# Check evidence cross-document consistency
node scripts/tools/check_evidence_consistency.js
```

---

## Known Limitations

1. **Raw HTML Only**: Does not execute JavaScript or wait for client-side AJAX requests. Client-rendered single-page apps will be detected as `SHELL_ONLY`.
2. **No CSS or Color Contrast**: Cannot measure font sizes, text visibility, or color contrast ratios.
3. **No Image Vision**: Cannot inspect image pixels; alt texts are judged for semantic clarity out of context only.
4. **Page Churn & Consensus Disagreement**: If a target web page alters between the leader's fetch and a validator's fetch, rule counts will differ and validators will disagree. This is an intentional protocol defense against non-reproducible states.
5. **Subset of WCAG**: Evaluates 12 deterministic criteria; does not represent a full WCAG 2.1 AAA accessibility audit.
6. **Bounded Model Impact**: Subjective model penalty is capped at 10 points to prevent prompt non-determinism from dominating the audit.
7. **Body Size Truncation**: Documents exceeding `MAX_BODY_BYTES` (300 KB) are truncated at 300,000 bytes with `truncated: true` recorded in state.
8. **Consensus Agreement**: Typically achieves 3 of 5 validator votes on GenLayer Studionet (Preview).
