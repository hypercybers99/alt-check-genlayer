# GenLayer Studionet (Preview) Runtime Probes Report

## 1. Executive Summary & Diagnostic Deployment

To ground the AltCheck intelligent contract architecture in empirical on-chain reality, a throwaway diagnostic `Probe` contract was deployed and executed on GenLayer Studionet (Preview).

- **Network**: GenLayer Studionet (Preview)
- **Chain ID**: 61999
- **RPC Endpoint**: `https://studio.genlayer.com/api`
- **Probe Contract Address**: `0xC40bf93bA9c3f1cf9A1088087C4c7156E538FB95`
- **Deploy Transaction Hash**: `0xeecc2d204f91eae6ce63444e251f69a2d71463d86edca0f2edf050edfe5593ba`
- **Deploy Status**: `ACCEPTED`
- **Consensus Result**: `MAJORITY_AGREE`
- **Deploy Elapsed Time**: 14.78s
- **Probe Source SHA-256**: `c7b2966c2ea5dcfa263da0f662f51add37167e490a6ff1bfd2b0d32c075e3520`

---

## 2. Empirical Probe Findings (P1 - P6)

### P1. Web Fetch Capabilities & Response Object Introspection
- **Transaction Hash**: `0xf3113d3a3469c2d375d667f7518f0311d70343a3391c85f5be712cb0fb03c988`
- **Duration**: 16.51s | **Agreement**: 3 / 5 validator votes (`MAJORITY_AGREE`)
- **Target URL**: `https://en.wikipedia.org/w/index.php?title=Alan_Turing&oldid=1380390650`
- **Response Attributes**: `['body', 'headers', 'status']`
- **Status Code**: Available as integer `200`.
- **Response Headers**: Exposed as a dictionary of `str` to `bytes` or `str`. Key `content-type` yielded `"text/html; charset=UTF-8"`.
- **Destination / Final URL**: `hasattr(resp, 'url')` is `False`. The runtime HTTP response does **not** expose the final destination URL or redirect history.
- **Enforcement Decision**: URL policy must be strictly enforced on the target URL prior to fetch. In addition, the response `content-type` header is inspected, and the fetched body is verified by code to ensure it contains standard HTML root markers (`<html`, `<!doctype html`, `<head`, or `<body`) within the first 2048 bytes; otherwise, execution reverts with `not an html page`.

### P2. Standard Library `html.parser` & `html.unescape` Usability
- Evaluated within the same transaction `0xf3113d3a3469c2d375d667f7518f0311d70343a3391c85f5be712cb0fb03c988`.
- **`html.parser`**: `importable: true`. Custom subclass of `html.parser.HTMLParser` successfully instantiated and tokenized tags, attributes, and nested elements inside GenVM.
- **`html.unescape`**: `importable: true`. Correctly decoded named and numeric entities (e.g., `&lt;`, `&quot;`, `&#169;`).
- **Architecture Decision**: We can use standard library `html.parser` augmented with a strict element tree builder that tracks tag nesting, text content, accessible names, and document order.

### P3. Size & Execution Latency Behavior
- **Transaction Hash**: `0xa5a13df1502049279b68295ec178852ee0d1da778f9d9cf9161953d7ae7e91f4`
- **Duration**: 13.14s | **Agreement**: 3 / 5 validator votes (`MAJORITY_AGREE`)
- **Page Size**: 1,331,304 bytes (~1.33 MB) fetched from Wikipedia permalink.
- **Parsed Structure**: 40 `<img>` tags, 2,839 `<a>` tags, 1 `<h1>` tag parsed within leader and validator sandboxes.
- **Execution Budget Boundary**: While 1.33 MB executed in 13.14s, conservative resource management on Studionet mandates setting `MAX_BODY_BYTES = 300000` (300 KB). Pages exceeding this size are safely truncated at 300,000 bytes with `truncated: true` recorded in the audit log.

### P4. Validator Consistency Across Independent Fetches
- Evaluated in `probe_fetch_size_and_consistency` via `gl.vm.spawn_sandbox` within `validator`:
  - Leader and validator independently fetched the target URL.
  - Both nodes obtained identical parsed counts (`img_count: 40`, `a_count: 2839`, `h1_count: 1`).
  - Consensus agreement: 3 of 5 votes.
- **Consensus Rule**: Validator consensus should compare closed-enumeration mode (`FULL` vs `SHELL_ONLY`), per-rule finding count vectors, and model vague-count buckets, rather than exact raw body byte SHA-256 (which can vary on dynamic or time-stamped pages).

### P5. Model Execution (`gl.nondet.exec_prompt`) with 16-Item Batch
Tested over 5 consecutive on-chain write transactions with a 16-item prompt batch requesting structured JSON:
- **Run 1**: Tx `0x2be176e1c988cee830aaf2b206b18c63a5f908046aca6142b6e1543ee29d1446` | 20.38s | 3/5 votes | Returned all 16 labels (`CLEAR`)
- **Run 2**: Tx `0x03f8c87ad1b330891b175b163a1b4b4d2dcdb6d78f8a91ea015e093f44f93330` | 16.16s | 3/5 votes | Returned all 16 labels (`CLEAR`)
- **Run 3**: Tx `0x4f3f7388da68bcd11645c9bca160928ec8af242330f5d4050bfa1c96c652873c` | 16.05s | 3/5 votes | Returned empty labels list `{"labels": []}`
- **Run 4**: Tx `0x83e6c85b251309afc19b296dfeae16f9632cc5d7d1e887999f9cc1380bc14ff5` | 11.76s | 3/5 votes | Returned all 16 labels (`CLEAR`)
- **Run 5**: Tx `0xc061120742169e888a80f22542d042dcdb395db2f5d741cd6060cddd30da41e4` | 13.36s | 3/5 votes | Returned all 16 labels (`CLEAR`)
- **Summary Metrics**:
  - Validity Rate: 4 / 5 (80.0%) returned fully structured item-level labels; 1 / 5 returned empty schema.
  - Average Latency: 15.54s (Range: 11.76s - 20.38s).
- **Architecture Takeaway**:
  1. The model layer must strictly require exactly one label per requested item. Any discrepancy (such as Run 3's empty list) MUST revert with `raise gl.vm.UserError("model output invalid")` rather than falling back to an unverified default.
  2. The sample size should be bounded to `MODEL_ALT_SAMPLE = 8` and `MODEL_LINK_SAMPLE = 8` (maximum 16 items evaluated per audit).

### P6. HTTP & Redirect Behavior
- **Transaction Hash**: `0x7c1d4dbb7898e8af82f144284a0f52a66af86c38cf28876c3aace207b50c1b1f`
- **Duration**: 10.65s | **Agreement**: 3 / 5 validator votes (`MAJORITY_AGREE`)
- **Target URL**: `http://httpbin.org/redirect/1`
- **Observation**: The underlying HTTP client followed the 302 redirect to `httpbin.org/get` and returned status 200 with JSON payload.
- **Enforcement**: Because the contract receives no final URL or redirect chain from the SDK, AltCheck requires `url` to use HTTPS at registration time, rejects HTTP schemes, and relies on strict content-type and HTML signature verification.

---

## 3. Derived Contract Constants & Design Limits

| Parameter | Calibrated Value | Rationale |
| :--- | :--- | :--- |
| `MAX_BODY_BYTES` | `300000` (300 KB) | Balances inspection depth with predictable block execution time (< 20s). |
| `MAX_ELEMENTS` | `1000` | Prevents excessive memory consumption during DOM tokenization. |
| `MODEL_ALT_SAMPLE` | `8` | Maximum alt texts evaluated subjectively by model. |
| `MODEL_LINK_SAMPLE` | `8` | Maximum link/button names evaluated subjectively by model. |
| `SHELL_TEXT_THRESHOLD` | `200` chars | Minimum visible text before classifying page as `SHELL_ONLY`. |
| `AUDIT_COOLDOWN_SECONDS` | `300` (5 minutes) | Prevents spamming and ensures cache/rate limit compliance. |
| `MAX_AUDITS_PER_PAGE` | `12` | Bounded audit history per registered page. |
| `PAGE_LIMIT_MAX` | `50` | Maximum items returned in paginated view queries. |
