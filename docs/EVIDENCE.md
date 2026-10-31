# AltCheck On-Chain Evidence Log

This document records verified on-chain execution evidence obtained on **GenLayer Studionet (Preview)**. All transactions were executed on-chain under multi-validator consensus.

---

## 1. Deployed Intelligent Contracts

| Contract | Address | Deploy Tx Hash | Source SHA-256 (Local & On-Chain) | Status | Consensus |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AltCheck** (v1.0.1) | [`0x1292C9bf74C2ef2789184Ec9808379d46279dd30`](https://explorer-studio.genlayer.com/address/0x1292C9bf74C2ef2789184Ec9808379d46279dd30) | `0xd171df04a4a959e77f17c8b5c8109d29419baaa273c0df0d58736dbbfbc56cd4` | `9af349d914c6c0e44199a00b0bc4c219a27fc6a9836b3b3a70574c23e4cdc262` | ACCEPTED | MAJORITY_AGREE |

### Contract Addresses & Lifecycle

| Contract | Role / Status | Full Hex Address | Deploy Tx Hash | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **AltCheck** | Active Ledger | `0x1292C9bf74C2ef2789184Ec9808379d46279dd30` | `0xd171df04a4a959e77f17c8b5c8109d29419baaa273c0df0d58736dbbfbc56cd4` | Production consensus accessibility ledger |
| **AltCheck** | Superseded Diagnostic | `0xBA2D886E76b87feD8dCd5be61fccFA2A4e1D388A` | `0xf2ec73168cf65d504ddedf4b965bce56d9fa399c86a955ce98f06600e992f9db` | superseded by v1.0.1 (element truncation tracking, partial grade cap, clean non-HTML consensus revert) |
| **Probe** | Superseded Diagnostic | `0xC40bf93bA9c3f1cf9A1088087C4c7156E538FB95` | `0xeecc2d204f91eae6ce63444e251f69a2d71463d86edca0f2edf050edfe5593ba` | superseded diagnostic probe for Phase 0 runtime measurements |

---

## 2. Positive Verification Scenarios

> [!NOTE]
> All positive verification scenarios below utilize static HTML test fixtures hosted by this project repository at [huzyow155/alt-check-fixtures](https://github.com/huzyow155/alt-check-fixtures) (served over HTTPS via GitHub Pages at `https://huzyow155.github.io/alt-check-fixtures/`).

| Scenario | Target Fixture URL | Register Tx | Audit Tx | Consensus Agreement | Mode | Score | Grade | Consensus Findings |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Scenario 1: Clean Accessible Page** | [`good.html`](https://huzyow155.github.io/alt-check-fixtures/good.html) | `0x5a59ffa105fea05acc3a2484df4f31ce7cae318e23321221e8b0b4f98405a4ca` | `0x0005962924374a3c606671862b2757133733f6af62a7075cbaf655788f0f5302` | Accepted by validators (3/5 agreed) | `FULL` | 100 | **A** | Zero deductions across R1-R12 (100% compliant subset) |
| **Scenario 2: Defective Page Across R1-R12** | [`bad.html`](https://huzyow155.github.io/alt-check-fixtures/bad.html) | `0x98d91239c561e7f1c82a74807d1dbf018b3b149822f5a9335046d57e23388cec` | `0xa788f95121bbdc835ceaf2bf922d804ca9994ffae4dfa2b88f0c0470d35784f0` | Accepted by validators (3/5 agreed) | `FULL` | 25 | **F** | 12 rules violated; verified snippets stored for all findings |
| **Scenario 3: Model Layer Evaluation** | [`mixed.html`](https://huzyow155.github.io/alt-check-fixtures/mixed.html) | `0x670b96340e422e902190af315b580d12978512949870fdb944758158d59e0ecc` | `0xa5cc91061e0ee8f9cbf402fec2bc1943f6407d1d04d2e4ea96fdb88c2fef7b5c` | Accepted by validators (3/5 agreed) | `FULL` | 88 | **B** | Subjective clarity evaluated; penalty 10 pts applied |
| **Scenario 4: SPA Shell Detection** | [`shell.html`](https://huzyow155.github.io/alt-check-fixtures/shell.html) | `0x7195740e4672c08b5efb8f5c512956bdb1568150c503eb0e5c4ba64effd77c8d` | `0x0d7723d22cf4bef8625b7ffcd323bada48fe353fa8fc68c282f04462a6bc0da5` | Accepted by validators (3/5 agreed) | `SHELL_ONLY` | -1 | **N/A** | Client SPA shell detected; body inspection honestly bypassed |
| **Scenario 4B: Large Document Partial Audit** | [`large.html`](https://huzyow155.github.io/alt-check-fixtures/large.html) | `0xe50db6b5170f276a2756d65351688be685972def9f0a4b035214c75d21231525` | `0xf16c3954f12aa8d2ad1ab13ecbd4f68e3374c57d90e525035eadde7c888f9867` | Accepted by validators (3/5 agreed) | `FULL` | 90 | **B** (capped) | Partial audit: 3000/3215 elements analyzed; unverified rules: `["R5","R8","R11"]` |

---

## 3. Secondary Scenario: Verifiable Remediation on Single Page ID (demo.html)

A single registered page identifier (`cf95eac13fb0`) was audited across two lifecycle states to provide verifiable consensus evidence of improvement:

- **Target URL**: `https://huzyow155.github.io/alt-check-fixtures/demo.html`
- **Registration Tx**: `0xe0c866cf543904e36ba17e5ae553b7c96b6361aa565b4a5ed28e680e90b57c29` (3/5 votes)
- **Before State Fixtures Commit**: `dbad5875f2dd61fa2f532092afe75b2e2b23e069`
  - Initial Audit Tx: `0xa6905112adb97abe52e971179f7bfe33f2f3e496dbee7e2fc14fcf681b0a5e21` (3/5 votes)
  - Initial Score & Grade: **25 (F)**
- **After State Fixtures Commit**: `0740db23620926715fdf8e6ae76c6691c4962c0e`
  - Remediated Audit Tx: `0x38a9e4044cb896a24264c3963b23ee0022af2c2b8909f4272ebcf34bdbea4bf6` (3/5 votes)
  - Remediated Score & Grade: **100 (A)**
- **On-Chain Progress Delta**: `+75` points (Grade transition: `F` -> `A`)
- **Maintainer Note Tx**: `0x7151934bb06ce67293eb3cab34bc4f5865a54261f11c41baa97b5a54525e9232` (3/5 votes)

### Progress Rule Deltas (`get_progress`)

| Rule ID | Earlier Count | Remediated Count | Delta |
| :---: | :---: | :---: | :---: |
| `R1` | 3 | 0 | `-3` |
| `R2` | 3 | 0 | `-3` |
| `R3` | 3 | 0 | `-3` |
| `R4` | 4 | 0 | `-4` |
| `R5` | 2 | 0 | `-2` |
| `R6` | 1 | 0 | `-1` |
| `R7` | 1 | 0 | `-1` |
| `R8` | 1 | 0 | `-1` |
| `R9` | 1 | 0 | `-1` |
| `R10` | 2 | 0 | `-2` |
| `R11` | 1 | 0 | `-1` |
| `R12` | 1 | 0 | `-1` |

---

## 4. 15 of 15 Reverts Accepted by Validators with Majority Agreement (3/5 each)

Negative rejection rules evaluated on GenLayer Studionet (Preview) through the transaction consensus pipeline. All 15 cases were accepted by validators with majority agreement (3/5 each) and reverted with the expected UserError payload without modifying state:

| Test Case | Invoked Function | Transaction Hash | Status (Raw Receipt) | Consensus Outcome | Decoded UserError Payload |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Reject HTTP Scheme** | `register_page` | `0x4bb32503f136515fe824efd27b13dc0d7ef90dd57d26c1fc6146cc0de7ab16d2` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `url must use https` |
| **Reject Localhost** | `register_page` | `0x6149c03e97b727c0c23e8ab63c59f0777458f6cbfcf68ff34f1f843d0bf9787b` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `url host not allowed` |
| **Reject IPv4 Literal** | `register_page` | `0x64612dbea46a94744c57f32fbbd7c036fa15e14d64182a39c534438c08443ce5` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `url host not allowed` |
| **Reject Private IP Range** | `register_page` | `0x373123220fe8908aab6220ae0213caa473bd306e2d3bda4d4eb33d16e0509333` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `url host not allowed` |
| **Reject Userinfo Credentials** | `register_page` | `0xb897f5fda7fc819e23e8b66b6bed09a3bcdf24228c7b5dd3e6e2e67fe96eab57` | `FINALIZED` | Accepted by validators (4/5 agreed) - expected revert | `url contains credentials` |
| **Reject Explicit Non-443 Port** | `register_page` | `0xe6525c85717b0b4ecad5bc6d78442d9a92812270809933e619eba6fcd70dcc95` | `FINALIZED` | Accepted by validators (4/5 agreed) - expected revert | `url port not allowed` |
| **Reject Over-Length URL** | `register_page` | `0xe5a093789bb93e5a00068f17198bc3625eff13145a57150d9b9b7c4c496ebc8f` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `url too long` |
| **Reject Non-HTML MIME / Payload (data.json)** | `audit_page` | `0x67b321657fe21b10dd90a399ed27f3d233ae2790e2f03091a6f8ee6a75c3a410` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `not an html page` |
| **Reject Non-HTML MIME / Payload (notes.txt)** | `audit_page` | `0xbfdc5fa402668e0d8bedc5943f35890847f6401243744b66e7322175dcfb09c2` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `not an html page` |
| **Audit Nonexistent Page ID** | `audit_page` | `0xca26c9dc85e211c75530673b6696b7c59893ac59ca54c26cab1852fb0c901d6d` | `FINALIZED` | Accepted by validators (5/5 agreed) - expected revert | `page not found` |
| **Duplicate Page Registration** | `register_page` | `0x19f4ac315b2e103642fc4e450fd73fe12d20bf3099557eb4c106f95934b70e58` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `page already registered` |
| **Audit Cooldown Active** | `audit_page` | `0x932aa3cd6ef05cf33e26394067e0c37bcb33506becfaa39d63499c01c0343936` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `audit cooldown active` |
| **Non-Registrant Maintainer Note Rejection** | `add_maintainer_note` | `0x7c084e32bc56897fdba64d5eb9b5108c94d9a2c61a73d2a185f7a7b2fae17b3d` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `only the registrant can do this` |
| **Maintainer Note Too Short (< 5 chars)** | `add_maintainer_note` | `0x51d35dc589466cd08c4fa7b16c7fa3738a1f6546ef74cffe4438cb5b7bca0779` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `note length out of range` |
| **Non-Registrant Retire Page Rejection** | `retire_page` | `0x10343d90a0312e4047e05126f13353a92767b0a1db0235ca22107cbb698da0b4` | `FINALIZED` | Accepted by validators (3/5 agreed) - expected revert | `only the registrant can do this` |

---

## 5. Unexpected or Superseded Runs

| Description | Tx Hash | Contract | Status | Result / Votes | Root Cause & Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Initial non-HTML audit attempt in v1.0.0 (UNDETERMINED / MAJORITY_DISAGREE 0/5)** | `0xf2c073c96dd2a3ed43f3491910cc1538e5d49d3231fddd227327cfbecc47bab9` | `0xBA2D886E76b87feD8dCd5be61fccFA2A4e1D388A` | UNDETERMINED | MAJORITY_DISAGREE (0/5) | In v1.0.0, leader raised gl.vm.UserError inside run_nondet_unsafe, causing leader execution error and validator_fn Return type-check rejection (0/5 disagree). Fixed in v1.0.1 via FAIL consensus protocol pattern. **Resolution**: Clean agreed revert achieved in v1.0.1 for data.json and notes.txt. |

---

## 6. Multi-Transaction Finality & Timing Measurements

Real on-chain latency and finality measured across write transactions on GenLayer Studionet (Preview):

| Operation | Function | Tx Hash | Submit Time (UTC) | Time to ACCEPTED (s) | Final Status | Time to FINALIZED (s) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| Register good.html | `register_page` | `0x5a59ffa105fea05acc3a2484df4f31ce7cae318e23321221e8b0b4f98405a4ca` | 2026-10-18T07:52:17.106420+00:00 | 6 | `FINALIZED` | 12 |
| Audit good.html (Grade A / 100) | `audit_page` | `0x0005962924374a3c606671862b2757133733f6af62a7075cbaf655788f0f5302` | 2026-10-18T07:52:27.094996+00:00 | 8 | `FINALIZED` | 14 |
| Register bad.html | `register_page` | `0x98d91239c561e7f1c82a74807d1dbf018b3b149822f5a9335046d57e23388cec` | 2026-10-18T07:52:41.758877+00:00 | 6 | `FINALIZED` | 12 |
| Audit bad.html (Grade F / 25) | `audit_page` | `0xa788f95121bbdc835ceaf2bf922d804ca9994ffae4dfa2b88f0c0470d35784f0` | 2026-10-18T07:52:51.608849+00:00 | 11 | `FINALIZED` | 17 |
| Register mixed.html | `register_page` | `0x670b96340e422e902190af315b580d12978512949870fdb944758158d59e0ecc` | 2026-10-18T07:53:09.448799+00:00 | 7 | `FINALIZED` | 13 |
| Audit mixed.html (Model Evaluation) | `audit_page` | `0xa5cc91061e0ee8f9cbf402fec2bc1943f6407d1d04d2e4ea96fdb88c2fef7b5c` | 2026-10-18T07:53:19.418803+00:00 | 14 | `FINALIZED` | 20 |
| Register shell.html | `register_page` | `0x7195740e4672c08b5efb8f5c512956bdb1568150c503eb0e5c4ba64effd77c8d` | 2026-10-18T07:53:39.148801+00:00 | 4 | `FINALIZED` | 10 |
| Audit shell.html (SHELL_ONLY) | `audit_page` | `0x0d7723d22cf4bef8625b7ffcd323bada48fe353fa8fc68c282f04462a6bc0da5` | 2026-10-18T07:53:45.665599+00:00 | 7 | `FINALIZED` | 13 |
| Register large.html | `register_page` | `0xe50db6b5170f276a2756d65351688be685972def9f0a4b035214c75d21231525` | 2026-10-18T07:53:55.401255+00:00 | 3 | `FINALIZED` | 9 |
| Audit large.html (Partial / Grade B Cap) | `audit_page` | `0xf16c3954f12aa8d2ad1ab13ecbd4f68e3374c57d90e525035eadde7c888f9867` | 2026-10-18T07:54:01.947063+00:00 | 14 | `FINALIZED` | 20 |
| Register demo.html | `register_page` | `0xe0c866cf543904e36ba17e5ae553b7c96b6361aa565b4a5ed28e680e90b57c29` | 2026-10-18T08:01:55.678881+00:00 | 15 | `FINALIZED` | 21 |
| Audit 1 demo.html (Before Remediation) | `audit_page` | `0xa6905112adb97abe52e971179f7bfe33f2f3e496dbee7e2fc14fcf681b0a5e21` | 2026-10-18T08:05:55.433232+00:00 | 5 | `FINALIZED` | 11 |
| Audit 2 demo.html (After Remediation) | `audit_page` | `0x38a9e4044cb896a24264c3963b23ee0022af2c2b8909f4272ebcf34bdbea4bf6` | 2026-10-18T08:12:08.860533+00:00 | 9 | `FINALIZED` | 15 |
| Add Maintainer Note demo.html | `add_maintainer_note` | `0x7151934bb06ce67293eb3cab34bc4f5865a54261f11c41baa97b5a54525e9232` | 2026-10-18T08:12:38.302459+00:00 | 4 | `FINALIZED` | 10 |
| Negative: Reject HTTP Scheme | `register_page` | `0x4bb32503f136515fe824efd27b13dc0d7ef90dd57d26c1fc6146cc0de7ab16d2` | 2026-10-18T07:59:27.618794+00:00 | 4 | `FINALIZED` | 10 |
| Negative: Reject Localhost | `register_page` | `0x6149c03e97b727c0c23e8ab63c59f0777458f6cbfcf68ff34f1f843d0bf9787b` | 2026-10-18T08:07:51.940836+00:00 | 5 | `FINALIZED` | 11 |
| Negative: Reject IPv4 Literal | `register_page` | `0x64612dbea46a94744c57f32fbbd7c036fa15e14d64182a39c534438c08443ce5` | 2026-10-18T08:07:53.804213+00:00 | 6 | `FINALIZED` | 12 |
| Negative: Reject Private IP | `register_page` | `0x373123220fe8908aab6220ae0213caa473bd306e2d3bda4d4eb33d16e0509333` | 2026-10-18T08:07:55.772242+00:00 | 8 | `FINALIZED` | 14 |
| Negative: Reject Userinfo | `register_page` | `0xb897f5fda7fc819e23e8b66b6bed09a3bcdf24228c7b5dd3e6e2e67fe96eab57` | 2026-10-18T08:07:57.604992+00:00 | 9 | `FINALIZED` | 15 |
| Negative: Reject Explicit Port 8080 | `register_page` | `0xe6525c85717b0b4ecad5bc6d78442d9a92812270809933e619eba6fcd70dcc95` | 2026-10-18T08:07:59.476760+00:00 | 12 | `FINALIZED` | 18 |
| Negative: Reject Over-Length URL | `register_page` | `0xe5a093789bb93e5a00068f17198bc3625eff13145a57150d9b9b7c4c496ebc8f` | 2026-10-18T08:08:01.363973+00:00 | 14 | `FINALIZED` | 20 |
| Negative: Register data.json | `register_page` | `0xe06587b625f49d6981ade8181b4e08bc18e4f649b3eee4ffff1448dbca9ff2e3` | 2026-10-18T08:08:16.380788+00:00 | 3 | `FINALIZED` | 9 |
| Negative: Audit data.json (Non-HTML) | `audit_page` | `0x67b321657fe21b10dd90a399ed27f3d233ae2790e2f03091a6f8ee6a75c3a410` | 2026-10-18T08:09:23.824613+00:00 | 10 | `FINALIZED` | 16 |
| Negative: Register notes.txt | `register_page` | `0x15ee0705d58bb8bf641ca3c4e7abb9aa3c04da9c43f465b93f4efafe1a5ec1eb` | 2026-10-18T08:08:18.286965+00:00 | 5 | `FINALIZED` | 11 |
| Negative: Audit notes.txt (Non-HTML) | `audit_page` | `0xbfdc5fa402668e0d8bedc5943f35890847f6401243744b66e7322175dcfb09c2` | 2026-10-18T08:09:25.689616+00:00 | 21 | `FINALIZED` | 27 |
| Negative: Audit Nonexistent Page ID | `audit_page` | `0xca26c9dc85e211c75530673b6696b7c59893ac59ca54c26cab1852fb0c901d6d` | 2026-10-18T08:07:15.118796+00:00 | 4 | `FINALIZED` | 10 |
| Negative: Duplicate Registration | `register_page` | `0x19f4ac315b2e103642fc4e450fd73fe12d20bf3099557eb4c106f95934b70e58` | 2026-10-18T08:07:24.038811+00:00 | 4 | `FINALIZED` | 10 |
| Negative: Audit Cooldown Active | `audit_page` | `0x932aa3cd6ef05cf33e26394067e0c37bcb33506becfaa39d63499c01c0343936` | 2026-10-18T08:06:50.148806+00:00 | 4 | `FINALIZED` | 10 |
| Negative: Non-Registrant Note | `add_maintainer_note` | `0x7c084e32bc56897fdba64d5eb9b5108c94d9a2c61a73d2a185f7a7b2fae17b3d` | 2026-10-18T08:07:34.898804+00:00 | 4 | `FINALIZED` | 10 |
| Negative: Note Too Short | `add_maintainer_note` | `0x51d35dc589466cd08c4fa7b16c7fa3738a1f6546ef74cffe4438cb5b7bca0779` | 2026-10-18T08:07:36.898091+00:00 | 5 | `FINALIZED` | 11 |
| Negative: Non-Registrant Retire | `retire_page` | `0x10343d90a0312e4047e05126f13353a92767b0a1db0235ca22107cbb698da0b4` | 2026-10-18T08:07:38.651054+00:00 | 5 | `FINALIZED` | 11 |

### Latency & Finality Statistics (Min / Median / Max)

| Metric | Sample Size | Min (s) | Median (s) | Max (s) | Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Time to ACCEPTED** | 31 | 3 | 6 | 21 | Multi-validator consensus reached |
| **Time to FINALIZED** | 31 | 9 | 12 | 27 | All transactions reached FINALIZED |

---

## 7. Partitioned Verification Scope: On-Chain vs. Unit-Tested Only

### Verified On-Chain (GenLayer Studionet Preview)
1. **Full-Spectrum Semantic Audit**: Verified on `good.html` (Grade A / 100), `bad.html` (Grade F / 25), and `mixed.html`.
2. **Single Page ID Verifiable Progress**: Verified on `demo.html` demonstrating on-chain score delta +75 points (Grade F -> A).
3. **SPA Shell Honest Detection**: Verified on `shell.html` detecting client-rendered shell and reporting `SHELL_ONLY`.
4. **Large Document Partial Audit Guard**: Verified on `large.html` with 3,215 elements: capped at Grade B, 3000 elements analyzed, whole-document rules marked unverified.
5. **Agreed Non-HTML Reverts**: Verified on `data.json` and `notes.txt` reverting cleanly with `not an html page` under consensus agreement.
6. **All Negative Revert Classes**: Reverted on-chain with exact decoded UserError payloads.
7. **Registrant Maintainer Notes**: Verified note append on audit #2 by verified registrant.
8. **Board Indexing & Ranking**: Verified top board rankings for Best Pages and Most Improved Pages.

### Unit-Tested Only
- **Large HTML body truncation at MAX_BODY_BYTES boundary (MAX_BODY_BYTES = 300,000 bytes with partial: true)**
- **Board tie-breaking ranking cases beyond the 8 registered on-chain fixtures (full audits ordered above partial audits at identical scores)**
- **Model layer prompt injection fallback (penalty cap 10 bounds impact)**
- **Maximum audits per page boundary (12 audits cap per registered URL)**
- **Pagination boundary tests (offset < 0, limit > 50, limit < 1)**
