const dns = require('dns');
dns.setDefaultResultOrder('ipv4first');

const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const RPC_URL = "https://studio.genlayer.com/api";

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
        if (tx && (tx.status === 'ACCEPTED' || tx.status === 'FINALIZED')) {
          return tx;
        }
      } catch (parseErr) {
        // Retry on 502/504
      }
    } catch (e) {
      // Retry on network glitch
    }
    await new Promise(r => setTimeout(r, intervalMs));
  }
  throw new Error(`Timeout waiting for tx receipt: ${hash}`);
}

async function main() {
  let privateKey = null;
  const envPath = path.join(__dirname, '../../.env');
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    const match = envContent.match(/THROWAWAY_PRIVATE_KEY=(0x[0-9a-fA-F]+)/);
    if (match) {
      privateKey = match[1];
    }
  }

  const account = privateKey ? createAccount(privateKey) : createAccount();
  console.log("Using account for probe:", account.address);

  const client = createClient({
    chain: chains.studionet,
    account: account,
  });

  const probePath = path.join(__dirname, '../../contracts/Probe.py');
  const probeCode = fs.readFileSync(probePath, 'utf8');
  const probeSha256 = crypto.createHash('sha256').update(probeCode, 'utf8').digest('hex');
  console.log("Probe contract SHA-256:", probeSha256);

  console.log("\n=======================================================");
  console.log("DEPLOYING PROBE CONTRACT ON GENLAYER STUDIONET (PREVIEW)");
  console.log("=======================================================");
  const t0 = Date.now();
  const deployTxHash = await client.deployContract({
    code: probeCode,
    args: [],
  });
  console.log("Probe Deploy Tx Hash:", deployTxHash);

  const deployTx = await waitReceiptWithRetry(deployTxHash);
  const deployElapsed = ((Date.now() - t0) / 1000).toFixed(2);
  console.log(`Probe deployed in ${deployElapsed}s | Status: ${deployTx.status} | Result: ${deployTx.result_name}`);
  const probeAddress = deployTx.recipient;
  console.log("Probe Address:", probeAddress);

  if (!probeAddress) {
    throw new Error("No contract address returned for Probe");
  }

  const probeRecords = {
    probeAddress,
    deployTxHash,
    deployStatus: deployTx.status,
    consensusResult: deployTx.result_name,
    deployElapsedSeconds: deployElapsed,
    sourceSha256: probeSha256,
    tests: [],
  };

  async function executeWrite(fnName, args, desc) {
    console.log(`\n>>> Probing: ${desc} [${fnName}]`);
    const start = Date.now();
    let txHash = null;
    let receipt = null;
    try {
      txHash = await client.writeContract({
        address: probeAddress,
        functionName: fnName,
        args: args,
      });
      console.log("    Submitted Tx:", txHash);
      receipt = await waitReceiptWithRetry(txHash);
    } catch (err) {
      console.error("    Write error:", err.message);
      return { desc, fnName, args, error: err.message };
    }
    const dur = ((Date.now() - start) / 1000).toFixed(2);
    const votes = receipt?.consensus_data?.votes || {};
    const agree = Object.values(votes).filter(v => v === 'agree').length;
    const total = Object.values(votes).length;
    console.log(`    Status: ${receipt.status} | Result: ${receipt.result_name} | Agree: ${agree}/${total} in ${dur}s`);

    let viewResult = null;
    try {
      viewResult = await client.readContract({
        address: probeAddress,
        functionName: 'get_result',
        args: [],
      });
      console.log("    Contract get_result:", viewResult);
    } catch (ve) {
      console.log("    Read error:", ve.message);
    }

    const record = {
      desc,
      fnName,
      args,
      txHash,
      durationSec: dur,
      status: receipt.status,
      result: receipt.result_name,
      agreeCount: agree,
      totalVotes: total,
      viewResult,
    };
    probeRecords.tests.push(record);
    return record;
  }

  // P1 & P2: Test capabilities with Alan Turing Wikipedia permalink (stable, https)
  await executeWrite(
    'probe_p1_p2_capabilities',
    ["https://en.wikipedia.org/w/index.php?title=Alan_Turing&oldid=1380390650"],
    "P1 & P2 Capabilities Probe (web.get headers/attrs, html.parser, html.unescape)"
  );

  // P3: Latency & size behavior on a ~50KB / ~150KB page
  await executeWrite(
    'probe_fetch_size_and_consistency',
    ["https://en.wikipedia.org/w/index.php?title=Alan_Turing&oldid=1380390650"],
    "P3 & P4 Size & Validator Consistency Probe (Alan Turing oldid 1380390650)"
  );

  // P5: gl.nondet.exec_prompt with a 16-item JSON batch (run 5 times to check latency and validity rate)
  const batch16 = [];
  for (let i = 0; i < 16; i++) {
    batch16.push({ id: i, text: `Item ${i}: Button label or image alt text sample description` });
  }
  const promptText = `You are an accessibility auditor. Return strictly JSON in this exact structure: {"labels":[{"i":0,"label":"CLEAR"}, ...]}. Items:\n${JSON.stringify(batch16)}`;

  for (let run = 1; run <= 5; run++) {
    await executeWrite(
      'probe_prompt_batch',
      [promptText],
      `P5 Batch 16-item Prompt (Run ${run} of 5)`
    );
  }

  // P6: Test redirect behavior (http URL to see how it responds)
  await executeWrite(
    'probe_p1_p2_capabilities',
    ["http://httpbin.org/redirect/1"],
    "P6 Redirect Behavior Probe (http redirect)"
  );

  const outPath = path.join(__dirname, 'probe_results.json');
  fs.writeFileSync(outPath, JSON.stringify(probeRecords, null, 2));
  console.log(`\nProbe results written to ${outPath}`);
}

main().catch(err => {
  console.error("Probe script failed:", err);
  process.exit(1);
});
