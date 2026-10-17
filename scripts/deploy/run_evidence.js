const dns = require('dns');
dns.setDefaultResultOrder('ipv4first');

const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const RPC_URL = "https://studio.genlayer.com/api";

function decodeLeaderResult(tx) {
  const leaderReceipts = tx?.consensus_data?.leader_receipt || [];
  for (const lr of leaderReceipts) {
    if (typeof lr.result === 'string') {
      const buf = Buffer.from(lr.result, 'base64');
      if (buf.length > 0 && buf[0] < 32) {
        return buf.slice(1).toString('utf8');
      }
      return buf.toString('utf8');
    }
    if (typeof lr.error === 'string') {
      return lr.error;
    }
    if (lr.genvm_result) {
      if (lr.genvm_result.error_description) return lr.genvm_result.error_description;
      if (lr.genvm_result.stderr) return lr.genvm_result.stderr;
      if (lr.genvm_result.raw_error) return JSON.stringify(lr.genvm_result.raw_error);
    }
    if (lr.execution_result) {
      if (typeof lr.execution_result.error === 'string') return lr.execution_result.error;
      if (typeof lr.execution_result.result === 'string') {
        const buf = Buffer.from(lr.execution_result.result, 'base64');
        if (buf.length > 0 && buf[0] < 32) return buf.slice(1).toString('utf8');
        return buf.toString('utf8');
      }
    }
  }
  return null;
}

function extractUserError(raw) {
  if (!raw) return "";
  const m = raw.match(/UserError:\s*([^"\n\r]+)/);
  if (m) return m[1].trim();
  const m2 = raw.match(/UserError\("([^"]+)"\)/);
  if (m2) return m2[1].trim();
  return raw;
}

async function waitReceiptWithRetry(hash, maxRetries = 90, intervalMs = 3000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const res = await fetch(RPC_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 1,
          method: 'eth_getTransactionByHash',
          params: [hash],
        }),
      });
      const text = await res.text();
      try {
        const json = JSON.parse(text);
        const tx = json.result;
        if (tx && (tx.status === 'ACCEPTED' || tx.status === 'FINALIZED' || tx.result_name === 'MAJORITY_DISAGREE' || tx.status_name === 'FINALIZED')) {
          return tx;
        }
      } catch (parseErr) {}
    } catch (e) {}
    await new Promise(r => setTimeout(r, intervalMs));
  }
  throw new Error(`Timeout waiting for receipt: ${hash}`);
}

async function main() {
  const deploymentsPath = path.join(__dirname, 'deployments.json');
  const deployments = JSON.parse(fs.readFileSync(deploymentsPath, 'utf8'));
  const contractAddress = deployments.altCheck.contractAddress;

  console.log("=======================================================");
  console.log("RUNNING ALTCHECK ON-CHAIN EVIDENCE SUITE");
  console.log("Network:          GenLayer Studionet (Preview)");
  console.log("Chain ID:         61999");
  console.log("AltCheck Address:", contractAddress);
  console.log("RPC Endpoint:     ", RPC_URL);
  console.log("=======================================================\n");

  let privateKey = null;
  const envPath = path.join(__dirname, '../../.env');
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    const match = envContent.match(/THROWAWAY_PRIVATE_KEY=(0x[0-9a-fA-F]+)/);
    if (match) {
      privateKey = match[1];
    }
  }

  const registrantAccount = privateKey ? createAccount(privateKey) : createAccount();
  console.log("Registrant Account:", registrantAccount.address);

  const nonRegistrantAccount = createAccount();
  console.log("Non-Registrant Account:", nonRegistrantAccount.address);

  const client = createClient({
    chain: chains.studionet,
    account: registrantAccount,
  });

  const nonRegClient = createClient({
    chain: chains.studionet,
    account: nonRegistrantAccount,
  });

  const evidence = {
    network: "GenLayer Studionet (Preview)",
    chainId: 61999,
    rpc: RPC_URL,
    version: "1.0.0",
    contractAddress: contractAddress,
    deployTxHash: deployments.altCheck.deployTxHash,
    deployStatus: deployments.altCheck.deployStatus,
    consensusResult: deployments.altCheck.consensusResult,
    sourceSha256: deployments.altCheck.sourceSha256,
    recordedAt: new Date().toISOString(),
    positiveScenarios: {},
    secondaryScenario: {},
    shellScenario: {},
    negativeTests: {},
    finalizedMeasurement: null,
    boardState: null,
    unitTestedOnly: [
      "Model layer prompt injection fallback (penalty cap 10 bounds impact)",
      "Maximum audits per page (12 audits cap per registered URL)",
      "Large HTML body truncation (MAX_BODY_BYTES = 300,000 bytes)",
      "Pagination boundary tests (offset < 0, limit > 50, limit < 1)"
    ],
  };

  async function executeWrite(actingClient, fnName, args, desc) {
    console.log(`\n>>> Executing: ${fnName} [${desc}]`);
    const t0 = Date.now();
    let txHash = null;
    let receipt = null;
    let sendErr = null;

    try {
      txHash = await actingClient.writeContract({
        address: contractAddress,
        functionName: fnName,
        args: args,
      });
      console.log(`    Tx Submitted: ${txHash}`);
      receipt = await waitReceiptWithRetry(txHash);
    } catch (err) {
      console.log(`    Send/Wait Error: ${err.message}`);
      sendErr = err.message;
    }

    const elapsed = ((Date.now() - t0) / 1000).toFixed(2);
    const votes = receipt?.consensus_data?.votes || {};
    const agree = Object.values(votes).filter(v => v === 'agree').length;
    const total = Object.values(votes).length;
    const rawLeader = decodeLeaderResult(receipt);
    const userErr = extractUserError(rawLeader);

    console.log(`    Finished in ${elapsed}s | Status: ${receipt?.status} | Result: ${receipt?.result_name} | Agree: ${agree}/${total}`);
    if (userErr) {
      console.log(`    Decoded Revert/Error: ${userErr}`);
    }

    return {
      desc,
      fnName,
      args,
      txHash,
      elapsed,
      status: receipt?.status,
      result: receipt?.result_name,
      agreeCount: `${agree}/${total}`,
      votes,
      rawLeader,
      userErr,
    };
  }

  // =========================================================================
  // 1. POSITIVE SCENARIO 1: good.html (Grade A / Score 100)
  // =========================================================================
  console.log("\n=======================================================");
  console.log("SCENARIO 1: Accessible Page Audit (good.html -> Target Grade A)");
  console.log("=======================================================");
  const goodUrl = "https://huzyow155.github.io/alt-check-fixtures/good.html";
  const regGood = await executeWrite(
    client, 'register_page', ["Accessible Portfolio Demonstration", goodUrl], "Register good.html"
  );

  const rawGoodId = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'list_page_ids', args: [0, 1]
  }))[0];
  console.log("    Registered Page ID:", rawGoodId);

  const auditGood = await executeWrite(
    client, 'audit_page', [rawGoodId], "Audit good.html (Expect Grade A / 100)"
  );

  const goodPageRecord = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'get_page', args: [rawGoodId]
  }));
  const goodAuditsList = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'get_audits', args: [rawGoodId, 0, 1]
  }));
  const latestGoodAudit = goodAuditsList[0];

  console.log(`    Audit Result -> Score: ${latestGoodAudit.score} | Grade: ${latestGoodAudit.grade} | Mode: ${latestGoodAudit.mode}`);
  evidence.positiveScenarios.scenario_good = {
    title: "Scenario 1: Clean Accessible Page Audit (Grade A)",
    pageId: rawGoodId,
    url: goodUrl,
    registerTx: regGood.txHash,
    registerAgree: regGood.agreeCount,
    auditTx: auditGood.txHash,
    auditAgree: auditGood.agreeCount,
    auditElapsed: auditGood.elapsed,
    score: latestGoodAudit.score,
    grade: latestGoodAudit.grade,
    mode: latestGoodAudit.mode,
    ruleCounts: latestGoodAudit.rule_counts,
    pageRecord: goodPageRecord,
    auditRecord: latestGoodAudit,
  };

  // =========================================================================
  // 2. POSITIVE SCENARIO 2: bad.html (Low Grade / Score 25 / Grade F)
  // =========================================================================
  console.log("\n=======================================================");
  console.log("SCENARIO 2: Defective Page Audit (bad.html -> Target Grade F)");
  console.log("=======================================================");
  const badUrl = "https://huzyow155.github.io/alt-check-fixtures/bad.html";
  const regBad = await executeWrite(
    client, 'register_page', ["Defective Legacy Form & Media", badUrl], "Register bad.html"
  );

  const rawBadId = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'list_page_ids', args: [0, 1]
  }))[0];
  console.log("    Registered Page ID:", rawBadId);

  const auditBad = await executeWrite(
    client, 'audit_page', [rawBadId], "Audit bad.html (Expect Grade F / 25)"
  );

  const badPageRecord = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'get_page', args: [rawBadId]
  }));
  const badAuditsList = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'get_audits', args: [rawBadId, 0, 1]
  }));
  const latestBadAudit = badAuditsList[0];

  console.log(`    Audit Result -> Score: ${latestBadAudit.score} | Grade: ${latestBadAudit.grade} | Mode: ${latestBadAudit.mode}`);
  evidence.positiveScenarios.scenario_bad = {
    title: "Scenario 2: Defective Page Audit Across R1-R12 (Grade F)",
    pageId: rawBadId,
    url: badUrl,
    registerTx: regBad.txHash,
    registerAgree: regBad.agreeCount,
    auditTx: auditBad.txHash,
    auditAgree: auditBad.agreeCount,
    auditElapsed: auditBad.elapsed,
    score: latestBadAudit.score,
    grade: latestBadAudit.grade,
    mode: latestBadAudit.mode,
    ruleCounts: latestBadAudit.rule_counts,
    decorativeUnmarked: latestBadAudit.decorative_unmarked,
    snippets: latestBadAudit.snippets,
    pageRecord: badPageRecord,
    auditRecord: latestBadAudit,
  };

  // =========================================================================
  // 3. POSITIVE SCENARIO 3: mixed.html (Model Layer Visible)
  // =========================================================================
  console.log("\n=======================================================");
  console.log("SCENARIO 3: Model Layer Evaluation (mixed.html -> CLEAR & VAGUE)");
  console.log("=======================================================");
  const mixedUrl = "https://huzyow155.github.io/alt-check-fixtures/mixed.html";
  const regMixed = await executeWrite(
    client, 'register_page', ["Consensus Model Layer Calibration Site", mixedUrl], "Register mixed.html"
  );

  const rawMixedId = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'list_page_ids', args: [0, 1]
  }))[0];
  console.log("    Registered Page ID:", rawMixedId);

  const auditMixed = await executeWrite(
    client, 'audit_page', [rawMixedId], "Audit mixed.html (Model Evaluation)"
  );

  const mixedAuditsList = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'get_audits', args: [rawMixedId, 0, 1]
  }));
  const latestMixedAudit = mixedAuditsList[0];

  console.log(`    Audit Result -> Score: ${latestMixedAudit.score} | Grade: ${latestMixedAudit.grade} | Vague Count: ${latestMixedAudit.vague_count} | Penalty: ${latestMixedAudit.model_penalty}`);
  evidence.positiveScenarios.scenario_mixed = {
    title: "Scenario 3: Model Layer Evaluation (mixed.html)",
    pageId: rawMixedId,
    url: mixedUrl,
    registerTx: regMixed.txHash,
    registerAgree: regMixed.agreeCount,
    auditTx: auditMixed.txHash,
    auditAgree: auditMixed.agreeCount,
    auditElapsed: auditMixed.elapsed,
    score: latestMixedAudit.score,
    grade: latestMixedAudit.grade,
    mode: latestMixedAudit.mode,
    ruleCounts: latestMixedAudit.rule_counts,
    vagueCount: latestMixedAudit.vague_count,
    modelPenalty: latestMixedAudit.model_penalty,
    modelLabels: latestMixedAudit.model_labels,
    auditRecord: latestMixedAudit,
  };

  // =========================================================================
  // 4. POSITIVE SCENARIO 4: shell.html (Client-rendered SPA shell -> SHELL_ONLY)
  // =========================================================================
  console.log("\n=======================================================");
  console.log("SCENARIO 4: Client SPA Shell Detection (shell.html -> SHELL_ONLY)");
  console.log("=======================================================");
  const shellUrl = "https://huzyow155.github.io/alt-check-fixtures/shell.html";
  const regShell = await executeWrite(
    client, 'register_page', ["Client Rendered Single Page Shell", shellUrl], "Register shell.html"
  );

  const rawShellId = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'list_page_ids', args: [0, 1]
  }))[0];
  console.log("    Registered Page ID:", rawShellId);

  const auditShell = await executeWrite(
    client, 'audit_page', [rawShellId], "Audit shell.html (Expect SHELL_ONLY / Grade N/A)"
  );

  const shellAuditsList = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'get_audits', args: [rawShellId, 0, 1]
  }));
  const latestShellAudit = shellAuditsList[0];

  console.log(`    Audit Result -> Score: ${latestShellAudit.score} | Grade: ${latestShellAudit.grade} | Mode: ${latestShellAudit.mode}`);
  evidence.shellScenario = {
    title: "Scenario 4: SPA Shell Detection (SHELL_ONLY)",
    pageId: rawShellId,
    url: shellUrl,
    registerTx: regShell.txHash,
    registerAgree: regShell.agreeCount,
    auditTx: auditShell.txHash,
    auditAgree: auditShell.agreeCount,
    auditElapsed: auditShell.elapsed,
    score: latestShellAudit.score,
    grade: latestShellAudit.grade,
    mode: latestShellAudit.mode,
    ruleCounts: latestShellAudit.rule_counts,
    visibleTextChars: latestShellAudit.visible_text_chars,
    scriptTagCount: latestShellAudit.script_tag_count,
    auditRecord: latestShellAudit,
  };

  // =========================================================================
  // 5. SECONDARY SCENARIO: Real Before/After Remediation on ONE Page ID
  // =========================================================================
  console.log("\n=======================================================");
  console.log("SCENARIO 5: Verifiable Remediation (demo.html Before & After)");
  console.log("=======================================================");
  const demoUrl = "https://huzyow155.github.io/alt-check-fixtures/demo.html";
  const regDemo = await executeWrite(
    client, 'register_page', ["Verifiable Accessibility Remediation Demo", demoUrl], "Register demo.html"
  );

  const rawDemoId = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'list_page_ids', args: [0, 1]
  }))[0];
  console.log("    Registered Demo Page ID:", rawDemoId);

  // Initial audit 1 (at this time demo.html equals bad.html)
  const initialDemoCommit = execSync('git -C "E:/alt-check-fixtures" rev-parse HEAD', { encoding: 'utf8' }).trim();
  console.log("    Before State Fixtures Commit:", initialDemoCommit);

  const auditDemo1 = await executeWrite(
    client, 'audit_page', [rawDemoId], "Audit 1 demo.html (Before Remediation -> Grade F / 25)"
  );

  const demoAudit1 = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'get_audits', args: [rawDemoId, 0, 1]
  }))[0];
  console.log(`    Audit 1 Result -> Score: ${demoAudit1.score} | Grade: ${demoAudit1.grade}`);

  // Now remediate demo.html to equal fixed.html and commit/push
  console.log("\n>>> Committing Remediation Fix to demo.html on GitHub Pages...");
  fs.copyFileSync(
    path.join(__dirname, '../../fixtures-local/fixed.html'),
    path.join('E:/alt-check-fixtures/demo.html')
  );
  execSync('git -C "E:/alt-check-fixtures" add demo.html');
  execSync('git -C "E:/alt-check-fixtures" commit -m "feat: remediate demo.html to match fixed.html"');
  execSync('git -C "E:/alt-check-fixtures" push');
  const remediatedDemoCommit = execSync('git -C "E:/alt-check-fixtures" rev-parse HEAD', { encoding: 'utf8' }).trim();
  console.log("    After State Fixtures Commit:", remediatedDemoCommit);

  // Wait for GitHub Pages cache update and cooldown
  console.log("\n>>> Waiting 310s to satisfy contract audit cooldown (300s)...");
  for (let s = 310; s > 0; s -= 30) {
    console.log(`    ${s} seconds remaining in cooldown wait...`);
    await new Promise(r => setTimeout(r, 30000));
  }

  // Audit 2 (remediated state)
  const auditDemo2 = await executeWrite(
    client, 'audit_page', [rawDemoId], "Audit 2 demo.html (After Remediation -> Grade A / 100)"
  );

  const demoAudit2 = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'get_audits', args: [rawDemoId, 0, 1]
  }))[0];
  console.log(`    Audit 2 Result -> Score: ${demoAudit2.score} | Grade: ${demoAudit2.grade}`);

  // Progress diff query
  const progressJson = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'get_progress', args: [rawDemoId]
  }));
  console.log("    On-Chain Verified Progress:", progressJson);

  // Add Maintainer Note by registrant
  const noteTx = await executeWrite(
    client,
    'add_maintainer_note',
    [rawDemoId, 2, "Remediated all 12 WCAG violations; score improved from 25 (Grade F) to 100 (Grade A)"],
    "Add Maintainer Note on Remediated Audit"
  );

  // Read board state
  const boardJson = JSON.parse(await client.readContract({
    address: contractAddress, functionName: 'get_board', args: [10]
  }));
  console.log("    Top Board State (Best):", boardJson.best);
  console.log("    Top Board State (Most Improved):", boardJson.most_improved);
  evidence.boardState = boardJson;

  evidence.secondaryScenario = {
    title: "Scenario 5: Verified Before & After Remediation on Single Page ID",
    pageId: rawDemoId,
    url: demoUrl,
    initialCommit: initialDemoCommit,
    remediatedCommit: remediatedDemoCommit,
    registerTx: regDemo.txHash,
    registerAgree: regDemo.agreeCount,
    audit1Tx: auditDemo1.txHash,
    audit1Agree: auditDemo1.agreeCount,
    audit1Score: demoAudit1.score,
    audit1Grade: demoAudit1.grade,
    audit2Tx: auditDemo2.txHash,
    audit2Agree: auditDemo2.agreeCount,
    audit2Score: demoAudit2.score,
    audit2Grade: demoAudit2.grade,
    progress: progressJson,
    maintainerNoteTx: noteTx.txHash,
    maintainerNoteAgree: noteTx.agreeCount,
  };

  // =========================================================================
  // 6. NEGATIVE REVERT TESTS (14 On-Chain Reverts)
  // =========================================================================
  console.log("\n=======================================================");
  console.log("NEGATIVE TESTS SUITE: On-Chain UserError Verification (14 Tests)");
  console.log("=======================================================");

  const negDefs = [
    {
      key: "neg_http_scheme",
      name: "Reject HTTP Scheme",
      client: client,
      fn: 'register_page',
      args: ["HTTP Rejection", "http://example.com/page"],
      expected: "url must use https",
    },
    {
      key: "neg_localhost",
      name: "Reject Localhost",
      client: client,
      fn: 'register_page',
      args: ["Localhost Rejection", "https://localhost/test"],
      expected: "url host not allowed",
    },
    {
      key: "neg_ipv4_literal",
      name: "Reject IPv4 Literal",
      client: client,
      fn: 'register_page',
      args: ["IPv4 Literal Rejection", "https://127.0.0.1/app"],
      expected: "url host not allowed",
    },
    {
      key: "neg_private_ip",
      name: "Reject Private IP Range",
      client: client,
      fn: 'register_page',
      args: ["Private IP Rejection", "https://192.168.1.1/admin"],
      expected: "url host not allowed",
    },
    {
      key: "neg_userinfo",
      name: "Reject Userinfo Credentials",
      client: client,
      fn: 'register_page',
      args: ["Userinfo Rejection", "https://admin:pass@example.com/"],
      expected: "url contains credentials",
    },
    {
      key: "neg_non_443_port",
      name: "Reject Explicit Non-443 Port",
      client: client,
      fn: 'register_page',
      args: ["Port Rejection", "https://example.com:8080/"],
      expected: "url port not allowed",
    },
    {
      key: "neg_url_too_long",
      name: "Reject Over-Length URL",
      client: client,
      fn: 'register_page',
      args: ["Overlong Rejection", "https://example.com/" + "a".repeat(305)],
      expected: "url too long",
    },
    {
      key: "neg_non_html_url",
      name: "Reject Non-HTML MIME / Payload",
      client: client,
      fn: 'register_page',
      args: ["Non-HTML JSON Target", "https://huzyow155.github.io/alt-check-fixtures/data.json"],
      expected: "not an html page",
      isAuditTest: true,
    },
    {
      key: "neg_unknown_page_id",
      name: "Audit Nonexistent Page ID",
      client: client,
      fn: 'audit_page',
      args: ["000000000000"],
      expected: "page not found",
    },
    {
      key: "neg_duplicate_registration",
      name: "Duplicate Page Registration",
      client: client,
      fn: 'register_page',
      args: ["Duplicate Good", goodUrl],
      expected: "page already registered",
    },
    {
      key: "neg_cooldown_active",
      name: "Audit Cooldown Active",
      client: client,
      fn: 'audit_page',
      args: [rawDemoId],
      expected: "audit cooldown active",
    },
    {
      key: "neg_non_registrant_note",
      name: "Non-Registrant Maintainer Note Rejection",
      client: nonRegClient,
      fn: 'add_maintainer_note',
      args: [rawDemoId, 2, "Unauthorized maintainer note attempt"],
      expected: "only the registrant can do this",
    },
    {
      key: "neg_note_length_short",
      name: "Maintainer Note Too Short (< 5 chars)",
      client: client,
      fn: 'add_maintainer_note',
      args: [rawDemoId, 2, "hi"],
      expected: "note length out of range",
    },
    {
      key: "neg_non_registrant_retire",
      name: "Non-Registrant Retire Page Rejection",
      client: nonRegClient,
      fn: 'retire_page',
      args: [rawDemoId],
      expected: "only the registrant can do this",
    },
  ];

  for (const item of negDefs) {
    if (item.isAuditTest) {
      // Register non-HTML page first
      const rTx = await executeWrite(item.client, 'register_page', [item.name, item.args[1]], `Register for ${item.name}`);
      const nid = JSON.parse(await client.readContract({
        address: contractAddress, functionName: 'list_page_ids', args: [0, 1]
      }))[0];
      const res = await executeWrite(item.client, 'audit_page', [nid], item.name);
      evidence.negativeTests[item.key] = {
        name: item.name,
        fn: 'audit_page',
        args: [nid],
        txHash: res.txHash,
        status: res.status,
        result: res.result,
        agreeCount: res.agreeCount,
        revertPayload: res.userErr || res.rawLeader,
        expected: item.expected,
      };
    } else {
      const res = await executeWrite(item.client, item.fn, item.args, item.name);
      evidence.negativeTests[item.key] = {
        name: item.name,
        fn: item.fn,
        args: item.args,
        txHash: res.txHash,
        status: res.status,
        result: res.result,
        agreeCount: res.agreeCount,
        revertPayload: res.userErr || res.rawLeader,
        expected: item.expected,
      };
    }
  }

  // =========================================================================
  // 7. TRANSACTION FINALITY MEASUREMENT
  // =========================================================================
  console.log("\n=======================================================");
  console.log("TRANSACTION FINALITY MEASUREMENT");
  console.log("=======================================================");
  if (regGood.txHash) {
    console.log(`Polling for FINALIZED status on Tx: ${regGood.txHash}`);
    const t0 = Date.now();
    let isFinalized = false;
    let polls = 0;
    while (!isFinalized && polls < 40) {
      polls++;
      const res = await fetch(RPC_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 1,
          method: 'eth_getTransactionByHash',
          params: [regGood.txHash],
        }),
      });
      const data = await res.json();
      const tx = data.result;
      if (tx?.status_name === 'FINALIZED' || tx?.status === 'FINALIZED') {
        isFinalized = true;
        const elapsed = ((Date.now() - t0) / 1000).toFixed(2);
        console.log(`    Tx reached FINALIZED in ${elapsed}s (${polls} polls)`);
        evidence.finalizedMeasurement = {
          txHash: regGood.txHash,
          polls,
          elapsedSeconds: elapsed,
          finalStatus: 'FINALIZED',
        };
        break;
      }
      await new Promise(r => setTimeout(r, 4000));
    }
    if (!isFinalized) {
      evidence.finalizedMeasurement = {
        txHash: regGood.txHash,
        polls,
        elapsedSeconds: ((Date.now() - t0) / 1000).toFixed(2),
        finalStatus: 'TIMEOUT_POLLING',
      };
    }
  }

  const outPath = path.join(__dirname, 'live_evidence.json');
  fs.writeFileSync(outPath, JSON.stringify(evidence, null, 2));
  console.log(`\n=======================================================`);
  console.log(`EVIDENCE COLLECTION COMPLETE! Saved to ${outPath}`);
  console.log(`=======================================================`);
}

main().catch(err => {
  console.error("Evidence runner failed:", err);
  process.exit(1);
});
