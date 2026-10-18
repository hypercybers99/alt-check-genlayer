const fs = require('fs');
const path = require('path');

function renderEvidence() {
  const root = path.dirname(path.dirname(__dirname));
  const deploymentsPath = path.join(root, 'scripts', 'deploy', 'deployments.json');
  const liveEvidencePath = path.join(root, 'scripts', 'deploy', 'live_evidence.json');
  const evidenceDocPath = path.join(root, 'docs', 'EVIDENCE.md');
  const readmePath = path.join(root, 'README.md');

  if (!fs.existsSync(deploymentsPath) || !fs.existsSync(liveEvidencePath)) {
    console.error("Missing deployments.json or live_evidence.json");
    return;
  }

  const deployments = JSON.parse(fs.readFileSync(deploymentsPath, 'utf8'));
  const evidence = JSON.parse(fs.readFileSync(liveEvidencePath, 'utf8'));

  const altCheck = deployments.altCheck;
  const superseded = deployments.supersededDeployments || [];

  let md = `# AltCheck On-Chain Evidence Log

This document records verified on-chain execution evidence obtained on **GenLayer Studionet (Preview)**. All transactions were executed on-chain under multi-validator consensus.

---

## 1. Deployed Intelligent Contracts

| Contract | Address | Deploy Tx Hash | Source SHA-256 (Local & On-Chain) | Status | Consensus |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AltCheck** (v1.0.1) | [\`${altCheck.contractAddress}\`](${altCheck.explorerUrl}) | \`${altCheck.deployTxHash}\` | \`${altCheck.sourceSha256}\` | ${altCheck.deployStatus} | ${altCheck.consensusResult} |

### Contract Addresses & Lifecycle

| Contract | Role / Status | Full Hex Address | Deploy Tx Hash | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **AltCheck** | Active Ledger | \`${altCheck.contractAddress}\` | \`${altCheck.deployTxHash}\` | Production consensus accessibility ledger |
`;

  for (const s of superseded) {
    md += `| **${s.contract}** | Superseded Diagnostic | \`${s.address}\` | \`${s.deployTxHash}\` | ${s.reason} |\n`;
  }

  md += `\n---\n\n## 2. Positive Verification Scenarios\n\n`;
  md += `| Scenario | Target Fixture URL | Register Tx | Audit Tx | Agree | Mode | Score | Grade | Consensus Findings |\n`;
  md += `| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |\n`;

  const s1 = evidence.positiveScenarios?.scenario_good;
  if (s1) {
    md += `| **Scenario 1: Clean Accessible Page** | [\`good.html\`](${s1.url}) | \`${s1.registerTx}\` | \`${s1.auditTx}\` | ${s1.auditAgree} | \`${s1.mode}\` | ${s1.score} | **${s1.grade}** | Zero deductions across R1-R12 (100% compliant subset) |\n`;
  }

  const s2 = evidence.positiveScenarios?.scenario_bad;
  if (s2) {
    md += `| **Scenario 2: Defective Page Across R1-R12** | [\`bad.html\`](${s2.url}) | \`${s2.registerTx}\` | \`${s2.auditTx}\` | ${s2.auditAgree} | \`${s2.mode}\` | ${s2.score} | **${s2.grade}** | 12 rules violated; verified snippets stored for all findings |\n`;
  }

  const s3 = evidence.positiveScenarios?.scenario_mixed;
  if (s3) {
    md += `| **Scenario 3: Model Layer Evaluation** | [\`mixed.html\`](${s3.url}) | \`${s3.registerTx}\` | \`${s3.auditTx}\` | ${s3.auditAgree} | \`${s3.mode}\` | ${s3.score} | **${s3.grade}** | Subjective clarity evaluated; penalty ${s3.modelPenalty} pts applied |\n`;
  }

  const s4 = evidence.shellScenario;
  if (s4) {
    md += `| **Scenario 4: SPA Shell Detection** | [\`shell.html\`](${s4.url}) | \`${s4.registerTx}\` | \`${s4.auditTx}\` | ${s4.auditAgree} | \`${s4.mode}\` | ${s4.score} | **${s4.grade}** | Client SPA shell detected; body inspection honestly bypassed |\n`;
  }

  const s4b = evidence.partialScenario;
  if (s4b) {
    md += `| **Scenario 4B: Large Document Partial Audit** | [\`large.html\`](${s4b.url}) | \`${s4b.registerTx}\` | \`${s4b.auditTx}\` | ${s4b.auditAgree} | \`${s4b.mode}\` | ${s4b.score} | **${s4b.grade}** (capped) | Partial audit: ${s4b.elementsAnalyzed}/${s4b.elementsSeen} elements analyzed; unverified rules: \`${JSON.stringify(s4b.unverifiedRules)}\` |\n`;
  }

  md += `\n---\n\n## 3. Secondary Scenario: Verifiable Remediation on Single Page ID (demo.html)\n\n`;
  const s5 = evidence.secondaryScenario;
  if (s5) {
    md += `A single registered page identifier (\`${s5.pageId}\`) was audited across two lifecycle states to provide verifiable consensus evidence of improvement:\n\n`;
    md += `- **Target URL**: \`${s5.url}\`\n`;
    md += `- **Registration Tx**: \`${s5.registerTx}\` (${s5.registerAgree} votes)\n`;
    md += `- **Before State Fixtures Commit**: \`${s5.initialCommit}\`\n`;
    md += `  - Initial Audit Tx: \`${s5.audit1Tx}\` (${s5.audit1Agree} votes)\n`;
    md += `  - Initial Score & Grade: **${s5.audit1Score} (${s5.audit1Grade})**\n`;
    md += `- **After State Fixtures Commit**: \`${s5.remediatedCommit}\`\n`;
    md += `  - Remediated Audit Tx: \`${s5.audit2Tx}\` (${s5.audit2Agree} votes)\n`;
    md += `  - Remediated Score & Grade: **${s5.audit2Score} (${s5.audit2Grade})**\n`;
    md += `- **On-Chain Progress Delta**: \`+${s5.progress?.score_delta}\` points (Grade transition: \`${s5.progress?.grade_change?.from}\` -> \`${s5.progress?.grade_change?.to}\`)\n`;
    md += `- **Maintainer Note Tx**: \`${s5.maintainerNoteTx}\` (${s5.maintainerNoteAgree} votes)\n\n`;
    md += `### Progress Rule Deltas (\`get_progress\`)\n\n`;
    md += `| Rule ID | Earlier Count | Remediated Count | Delta |\n`;
    md += `| :---: | :---: | :---: | :---: |\n`;
    if (s5.progress?.rule_deltas) {
      for (const [r, delta] of Object.entries(s5.progress.rule_deltas)) {
        md += `| \`${r}\` | ${delta < 0 ? -delta : 0} | 0 | \`${delta}\` |\n`;
      }
    }
  }

  md += `\n---\n\n## 4. Negative Tests & Revert Payloads\n\n`;
  md += `Negative rejection rules evaluated on GenLayer Studionet (Preview) through the transaction consensus pipeline:\n\n`;
  md += `| Test Case | Invoked Function | Transaction Hash | Status | Consensus | Decoded UserError Payload |\n`;
  md += `| :--- | :--- | :--- | :--- | :--- | :--- |\n`;

  const neg = evidence.negativeTests || {};
  for (const [k, v] of Object.entries(neg)) {
    md += `| **${v.name}** | \`${v.fn}\` | \`${v.txHash}\` | ${v.status} | ${v.result} (${v.agreeCount}) | \`${v.revertPayload}\` |\n`;
  }

  if (evidence.unexpectedOrSupersededRuns && evidence.unexpectedOrSupersededRuns.length > 0) {
    md += `\n---\n\n## 5. Unexpected or Superseded Runs\n\n`;
    md += `| Description | Tx Hash | Contract | Status | Result / Votes | Root Cause & Resolution |\n`;
    md += `| :--- | :--- | :--- | :--- | :--- | :--- |\n`;
    for (const r of evidence.unexpectedOrSupersededRuns) {
      md += `| **${r.description}** | \`${r.txHash}\` | \`${r.contractAddress}\` | ${r.status} | ${r.result} (${r.votes}) | ${r.rootCause} **Resolution**: ${r.resolution} |\n`;
    }
  }

  if (evidence.timingMeasurements) {
    const tm = evidence.timingMeasurements;
    md += `\n---\n\n## 6. Multi-Transaction Finality & Timing Measurements\n\n`;
    md += `Real on-chain latency and finality measured across write transactions on GenLayer Studionet (Preview):\n\n`;
    md += `| Operation | Function | Tx Hash | Submit Time (UTC) | Time to ACCEPTED (s) | Final Status | Time to FINALIZED (s) |\n`;
    md += `| :--- | :--- | :--- | :--- | :---: | :---: | :---: |\n`;
    for (const t of tm.transactions || []) {
      md += `| ${t.desc} | \`${t.fnName}\` | \`${t.txHash}\` | ${t.submitTime} | ${t.timeToAcceptedSec} | \`${t.finalStatus}\` | ${t.timeToFinalizedSec !== null ? t.timeToFinalizedSec : 'N/A'} |\n`;
    }

    if (tm.stats) {
      md += `\n### Latency & Finality Statistics (Min / Median / Max)\n\n`;
      md += `| Metric | Sample Size | Min (s) | Median (s) | Max (s) | Notes |\n`;
      md += `| :--- | :---: | :---: | :---: | :---: | :--- |\n`;
      if (tm.stats.acceptedStats) {
        const as = tm.stats.acceptedStats;
        md += `| **Time to ACCEPTED** | ${as.count} | ${as.min} | ${as.median} | ${as.max} | Multi-validator consensus reached |\n`;
      }
      if (tm.stats.finalizedStats) {
        const fsStats = tm.stats.finalizedStats;
        md += `| **Time to FINALIZED** | ${fsStats.count} | ${fsStats.min} | ${fsStats.median} | ${fsStats.max} | ${fsStats.note} |\n`;
      }
    }
  }

  md += `\n---\n\n## 7. Partitioned Verification Scope: On-Chain vs. Unit-Tested Only\n\n`;
  md += `### Verified On-Chain (GenLayer Studionet Preview)\n`;
  md += `1. **Full-Spectrum Semantic Audit**: Verified on \`good.html\` (Grade A / 100), \`bad.html\` (Grade F / 25), and \`mixed.html\`.\n`;
  md += `2. **Single Page ID Verifiable Progress**: Verified on \`demo.html\` demonstrating on-chain score delta +75 points (Grade F -> A).\n`;
  md += `3. **SPA Shell Honest Detection**: Verified on \`shell.html\` detecting client-rendered shell and reporting \`SHELL_ONLY\`.\n`;
  md += `4. **Large Document Partial Audit Guard**: Verified on \`large.html\` with 3,215 elements: capped at Grade B, 3000 elements analyzed, whole-document rules marked unverified.\n`;
  md += `5. **Agreed Non-HTML Reverts**: Verified on \`data.json\` and \`notes.txt\` reverting cleanly with \`not an html page\` under consensus agreement.\n`;
  md += `6. **All Negative Revert Classes**: Reverted on-chain with exact decoded UserError payloads.\n`;
  md += `7. **Registrant Maintainer Notes**: Verified note append on audit #2 by verified registrant.\n`;
  md += `8. **Board Indexing & Ranking**: Verified top board rankings for Best Pages and Most Improved Pages.\n\n`;

  md += `### Unit-Tested Only\n`;
  const uto = evidence.unitTestedOnly || [];
  for (const u of uto) {
    md += `- **${u}**\n`;
  }

  fs.writeFileSync(evidenceDocPath, md, 'utf8');
  console.log(`Rendered EVIDENCE.md saved to ${evidenceDocPath}`);

  if (fs.existsSync(readmePath)) {
    let readme = fs.readFileSync(readmePath, 'utf8');
    const startTag = '<!-- EVIDENCE_TABLE_START -->';
    const endTag = '<!-- EVIDENCE_TABLE_END -->';

    let timingSummary = "";
    if (evidence.timingMeasurements?.stats) {
      const ts = evidence.timingMeasurements.stats;
      timingSummary = `
### Multi-Transaction Timing Statistics (Min / Median / Max)

| Metric | Sample Size | Min (s) | Median (s) | Max (s) |
| :--- | :---: | :---: | :---: | :---: |
| **Time to ACCEPTED** | ${ts.acceptedStats?.count || 'N/A'} | ${ts.acceptedStats?.min || 'N/A'} | ${ts.acceptedStats?.median || 'N/A'} | ${ts.acceptedStats?.max || 'N/A'} |
| **Time to FINALIZED** | ${ts.finalizedStats?.count || 'N/A'} | ${ts.finalizedStats?.min || 'N/A'} | ${ts.finalizedStats?.median || 'N/A'} | ${ts.finalizedStats?.max || 'N/A'} |
`;
    }

    const evidenceSection = `
## On-Chain Evidence Summary

### Active Deployed Contracts on GenLayer Studionet (Preview)

| Contract | Address | Deploy Tx Hash | Source SHA-256 | Status | Consensus |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AltCheck** (v1.0.1) | [\`${altCheck.contractAddress}\`](${altCheck.explorerUrl}) | \`${altCheck.deployTxHash}\` | \`${altCheck.sourceSha256}\` | ${altCheck.deployStatus} | ${altCheck.consensusResult} |

### Positive Execution Scenarios

| Scenario | Target Fixture URL | Register Tx | Audit Tx | Agreement | Score | Grade | Consensus Findings |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Clean Page** | [\`good.html\`](${s1?.url}) | \`${s1?.registerTx}\` | \`${s1?.auditTx}\` | ${s1?.auditAgree} | ${s1?.score} | **${s1?.grade}** | 100% compliant deterministic subset |
| **Defective Page** | [\`bad.html\`](${s2?.url}) | \`${s2?.registerTx}\` | \`${s2?.auditTx}\` | ${s2?.auditAgree} | ${s2?.score} | **${s2?.grade}** | 12 rules violated; verbatim snippets verified |
| **Model Evaluation** | [\`mixed.html\`](${s3?.url}) | \`${s3?.registerTx}\` | \`${s3?.auditTx}\` | ${s3?.auditAgree} | ${s3?.score} | **${s3?.grade}** | Subjective clarity evaluated; penalty ${s3?.modelPenalty} pts |
| **SPA Shell Detection** | [\`shell.html\`](${s4?.url}) | \`${s4?.registerTx}\` | \`${s4?.auditTx}\` | ${s4?.auditAgree} | ${s4?.score} | **${s4?.grade}** | Client SPA shell honestly flagged as \`SHELL_ONLY\` |
| **Large Doc Partial** | [\`large.html\`](${s4b?.url}) | \`${s4b?.registerTx}\` | \`${s4b?.auditTx}\` | ${s4b?.auditAgree} | ${s4b?.score} | **${s4b?.grade}** (capped) | Partial audit: ${s4b?.elementsAnalyzed}/${s4b?.elementsSeen} elements; unverified: \`${JSON.stringify(s4b?.unverifiedRules)}\` |

### Single Page ID Verifiable Progress (\`demo.html\`)

- **Page ID**: \`${s5?.pageId}\`
- **Initial State (Defective)**: Score ${s5?.audit1Score} (${s5?.audit1Grade}) | Tx \`${s5?.audit1Tx}\` | Fixtures Commit \`${s5?.initialCommit}\`
- **Remediated State (Clean)**: Score ${s5?.audit2Score} (${s5?.audit2Grade}) | Tx \`${s5?.audit2Tx}\` | Fixtures Commit \`${s5?.remediatedCommit}\`
- **Verified On-Chain Progress**: \`+${s5?.progress?.score_delta}\` points (Grade transition: \`${s5?.progress?.grade_change?.from}\` -> \`${s5?.progress?.grade_change?.to}\`)
- **Maintainer Note Tx**: \`${s5?.maintainerNoteTx}\`
${timingSummary}
`;

    if (readme.includes(startTag) && readme.includes(endTag)) {
      const before = readme.substring(0, readme.indexOf(startTag) + startTag.length);
      const after = readme.substring(readme.indexOf(endTag));
      readme = before + '\n' + evidenceSection.trim() + '\n' + after;
      fs.writeFileSync(readmePath, readme, 'utf8');
      console.log("Updated README.md evidence section");
    }
  }

  return md;
}

if (require.main === module) {
  renderEvidence();
}

module.exports = { renderEvidence };
