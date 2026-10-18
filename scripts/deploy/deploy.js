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
      } catch (parseErr) {}
    } catch (e) {}
    await new Promise(r => setTimeout(r, intervalMs));
  }
  throw new Error(`Timeout waiting for receipt: ${hash}`);
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
  console.log("Using deployer account:", account.address);

  const client = createClient({
    chain: chains.studionet,
    account: account,
  });

  const contractPath = path.join(__dirname, '../../contracts/AltCheck.py');
  const code = fs.readFileSync(contractPath, 'utf8');
  const sha256 = crypto.createHash('sha256').update(code, 'utf8').digest('hex');
  console.log("AltCheck source SHA-256:", sha256);

  console.log("\n=======================================================");
  console.log("DEPLOYING ALTCHECK CONTRACT ON GENLAYER STUDIONET (PREVIEW)");
  console.log("=======================================================");
  const t0 = Date.now();
  const deployTxHash = await client.deployContract({
    code: code,
    args: [],
  });
  console.log("AltCheck Deploy Tx Hash:", deployTxHash);

  const deployTx = await waitReceiptWithRetry(deployTxHash);
  const elapsed = ((Date.now() - t0) / 1000).toFixed(2);
  console.log(`AltCheck deployed in ${elapsed}s | Status: ${deployTx.status} | Result: ${deployTx.result_name}`);
  const contractAddress = deployTx.recipient;
  console.log("AltCheck Address:", contractAddress);

  if (!contractAddress) {
    throw new Error("No contract address returned for AltCheck");
  }

  const deployments = {
    network: "GenLayer Studionet (Preview)",
    chainId: 61999,
    version: "1.0.1",
    rpc: RPC_URL,
    explorerBase: "https://explorer-studio.genlayer.com",
    deployerAddress: account.address,
    altCheck: {
      contractAddress: contractAddress,
      deployTxHash: deployTxHash,
      deployStatus: deployTx.status,
      consensusResult: deployTx.result_name,
      sourceFile: "contracts/AltCheck.py",
      sourceSha256: sha256,
      explorerUrl: `https://explorer-studio.genlayer.com/address/${contractAddress}`,
      consensus_data: deployTx.consensus_data,
    },
    supersededDeployments: [
      {
        contract: "AltCheck",
        version: "1.0.0",
        address: "0xBA2D886E76b87feD8dCd5be61fccFA2A4e1D388A",
        deployTxHash: "0xf2ec73168cf65d504ddedf4b965bce56d9fa399c86a955ce98f06600e992f9db",
        sourceSha256: "b9c55a75970aca12f11edaf447e16a09a1d9a8a661e068e3ef2a5cddaa00e202",
        reason: "superseded by v1.0.1 (element truncation tracking, partial grade cap, clean non-HTML consensus revert)",
        archivedAt: "2026-10-18T14:45:00Z"
      },
      {
        contract: "Probe",
        version: "0.1.0",
        address: "0xC40bf93bA9c3f1cf9A1088087C4c7156E538FB95",
        deployTxHash: "0xeecc2d204f91eae6ce63444e251f69a2d71463d86edca0f2edf050edfe5593ba",
        sourceSha256: "c7b2966c2ea5dcfa263da0f662f51add37167e490a6ff1bfd2b0d32c075e3520",
        reason: "superseded diagnostic probe for Phase 0 runtime measurements",
        archivedAt: "2026-10-17T16:01:51Z"
      }
    ],
  };

  const outDir = path.join(__dirname);
  const outPath = path.join(outDir, 'deployments.json');
  fs.writeFileSync(outPath, JSON.stringify(deployments, null, 2));
  console.log(`\nDeployment records saved to ${outPath}`);
}

main().catch(err => {
  console.error("Deploy failed:", err);
  process.exit(1);
});
