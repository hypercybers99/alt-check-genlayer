# AltCheck Calibration Report

## 1. Executive Summary

This document presents empirical calibration results for **AltCheck** on **GenLayer Studionet (Preview)** across four dimensions:
1. **Deterministic Parity (a)**: Cross-verification of the local reference auditor (`scripts/tools/local_audit.py`) against the smart contract rule functions across all shared fixtures.
2. **Real-World Pages (b)**: Neutral raw-HTML accessibility measurements of three public static web pages.
3. **Model Layer Calibration (c)**: Empirical evaluation of 20 alt and link text descriptions across 3 independent on-chain runs on GenLayer Studionet (Preview) through the deployed `Probe` diagnostic contract (`0xC40bf93bA9c3f1cf9A1088087C4c7156E538FB95`).
4. **Validator Consensus & Churn Check (d)**: Independent multi-node verification behavior under static and evolving page conditions.

---

## 2. Deterministic Parity (a)

The local reference auditor (`scripts/tools/local_audit.py`) and the contract rule evaluator (`contracts/AltCheck.py`) were evaluated across all shared static fixtures in `fixtures-local/`. The per-rule counts, detection modes, and scores matched with 100% mathematical precision:

| Fixture | Mode | Expected Score | Local Reference Score | On-Chain Contract Score | Per-Rule Counts Parity |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `good.html` | `FULL` | 100 (A) | 100 (A) | 100 (A) | **Exact Match**: All R1-R12 counts = 0 |
| `bad.html` | `FULL` | 25 (F) | 25 (F) | 25 (F) | **Exact Match**: R1:3, R2:3, R3:3, R4:4, R5:2, R6:1, R7:1, R8:1, R9:1, R10:2, R11:1, R12:1 |
| `demo.html` (initial) | `FULL` | 25 (F) | 25 (F) | 25 (F) | **Exact Match**: R1:3, R2:3, R3:3, R4:4, R5:2, R6:1, R7:1, R8:1, R9:1, R10:2, R11:1, R12:1 |
| `fixed.html` | `FULL` | 100 (A) | 100 (A) | 100 (A) | **Exact Match**: All R1-R12 counts = 0 (+75 point improvement) |
| `mixed.html` | `FULL` | 98 (A)* | 98 (A) | 98 (A) | **Exact Match**: R10:1 (Deterministic base score 98 before model penalty) |
| `shell.html` | `SHELL_ONLY` | -1 (N/A) | -1 (N/A) | -1 (N/A) | **Exact Match**: Head rules clean, body rules bypassed |

*\*Note: `mixed.html` score represents deterministic rules baseline before model penalty.*

---

## 3. Real-World Public Pages (b)

Three public static URLs were inspected using raw-HTML consensus rules. Measurements are reported neutrally:

| Target Page URL | Raw Byte Size | Detection Mode | Truncated? | Measured Score | Grade | Detected Findings |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `https://example.com/` | 577 bytes | `SHELL_ONLY` | No | -1 | `N/A` | Visible text < 200 chars in lone container; client shell detected. |
| `https://httpbin.org/html` | 3,739 bytes | `FULL` | No | 87 | `B` | `R6:1` (no `<html lang>`), `R7:1` (no `<title>`), `R11:1` (no `<main>` landmark). |
| `https://en.wikipedia.org/w/index.php?title=Alan_Turing&oldid=1380390650` | 1,326,241 bytes | `FULL` | Yes (`MAX_BODY_BYTES`) | 100 | `A` | Clean semantic structure; truncated at 300,000 bytes. |

---

## 4. Model Layer Calibration (c)

Twenty alt-text and link-text descriptions (10 CLEAR, 10 VAGUE) spanning English, Vietnamese, and Spanish were submitted across 3 independent write transactions on GenLayer Studionet (Preview) through `Probe.probe_prompt_batch`:

- **Run 1**: Tx `0xbc21e0b50c93881d9b25dfe1e703f65d938d1730eb2c45a11b2ceb2ec4d2dd55` (13.4s, 20/20 labels, `ACCEPTED`)
- **Run 2**: Tx `0x432c4c6b9dd1ff9251844711466c999eb9205c31ae9d6b5cc8e4d2e91a942518` (12.0s, 20/20 labels, `ACCEPTED`)
- **Run 3**: Tx `0x93f0a76ec7ead186e92593598619a573879f7c1f44c9a33e90d723aa57763717` (22.1s, 20/20 labels, `ACCEPTED`)

### Item-by-Item Stability Matrix

| ID | Kind | Language | Evaluated Text | Expected | Run 1 | Run 2 | Run 3 | Stability | Result |
| :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 0 | alt | EN | "Bar chart of monthly signups, 2025" | CLEAR | CLEAR | CLEAR | CLEAR | 100.0% | **STABLE** |
| 1 | alt | EN | "Diagram showing three-tier client-server architecture with API gateway" | CLEAR | CLEAR | CLEAR | CLEAR | 100.0% | **STABLE** |
| 2 | alt | EN | "Photograph of Alan Turing standing next to the Bombe machine at Bletchley Park" | CLEAR | CLEAR | CLEAR | CLEAR | 100.0% | **STABLE** |
| 3 | link | EN | "Download the complete 2025 accessibility audit report in PDF format" | CLEAR | CLEAR | CLEAR | CLEAR | 100.0% | **STABLE** |
| 4 | link | EN | "View real-time validator node uptime and consensus voting distribution" | CLEAR | CLEAR | CLEAR | CLEAR | 100.0% | **STABLE** |
| 5 | alt | VI | "Bieu do hien thi so luong nguoi dung dang ky hang thang nam 2025" | CLEAR | CLEAR | CLEAR | CLEAR | 100.0% | **STABLE** |
| 6 | link | VI | "Tai xuong tai lieu huong dan su dung he thong dong thuan" | CLEAR | CLEAR | CLEAR | CLEAR | 100.0% | **STABLE** |
| 7 | alt | ES | "Grafico de barras que muestra las transacciones mensuales de 2025" | CLEAR | CLEAR | CLEAR | CLEAR | 100.0% | **STABLE** |
| 8 | link | ES | "Descargue el informe anual completo de accesibilidad web" | CLEAR | CLEAR | CLEAR | CLEAR | 100.0% | **STABLE** |
| 9 | alt | EN | "Logo of the World Wide Web Consortium displaying the letters W3C in blue" | CLEAR | CLEAR | CLEAR | CLEAR | 100.0% | **STABLE** |
| 10 | alt | EN | "the thing we made last week" | VAGUE | VAGUE | VAGUE | VAGUE | 100.0% | **STABLE** |
| 11 | alt | EN | "what happened earlier today" | VAGUE | VAGUE | VAGUE | VAGUE | 100.0% | **STABLE** |
| 12 | alt | EN | "some interesting items" | VAGUE | VAGUE | VAGUE | VAGUE | 100.0% | **STABLE** |
| 13 | alt | EN | "stuff and other content" | VAGUE | VAGUE | VAGUE | VAGUE | 100.0% | **STABLE** |
| 14 | link | EN | "check out that update" | VAGUE | VAGUE | VAGUE | VAGUE | 100.0% | **STABLE** |
| 15 | link | EN | "see our thoughts on it" | VAGUE | VAGUE | VAGUE | VAGUE | 100.0% | **STABLE** |
| 16 | alt | VI | "cai nay chung toi lam tuan truoc" | VAGUE | VAGUE | VAGUE | VAGUE | 100.0% | **STABLE** |
| 17 | link | VI | "xem cai nay" | VAGUE | VAGUE | VAGUE | VAGUE | 100.0% | **STABLE** |
| 18 | alt | ES | "la cosa que hicimos ayer" | VAGUE | VAGUE | VAGUE | VAGUE | 100.0% | **STABLE** |
| 19 | link | ES | "haga clic para mas info sobre eso" | VAGUE | VAGUE | VAGUE | VAGUE | 100.0% | **STABLE** |

**Summary**: 20 of 20 items (100.0%) achieved strict classification stability across all runs.

---

## 5. Churn Check & Multi-Account Consistency (d)

Auditing the static `good.html` fixture twice across distinct transactions and timestamps demonstrated consistent agreement:
- Both executions yielded `rule_counts` = all zeros.
- Both executions reached majority agreement (3 of 5 validator votes).
- Consensus validates identical closed-count vectors and VAGUE buckets, ensuring stability against minor transport-level jitter while strictly rejecting genuine page churn.
