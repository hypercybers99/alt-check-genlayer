const fs = require('fs');
const path = require('path');

function checkConsistency() {
  const root = path.dirname(path.dirname(__dirname));
  const deploymentsPath = path.join(root, 'scripts', 'deploy', 'deployments.json');
  const liveEvidencePath = path.join(root, 'scripts', 'deploy', 'live_evidence.json');
  const readmePath = path.join(root, 'README.md');
  const docsDir = path.join(root, 'docs');

  if (!fs.existsSync(deploymentsPath)) {
    throw new Error("Missing deployments.json");
  }
  if (!fs.existsSync(liveEvidencePath)) {
    throw new Error("Missing live_evidence.json");
  }

  const deployments = JSON.parse(fs.readFileSync(deploymentsPath, 'utf8'));
  const liveEvidence = JSON.parse(fs.readFileSync(liveEvidencePath, 'utf8'));

  const expectedContract = deployments.altCheck.contractAddress.toLowerCase();
  const actualContract = liveEvidence.contractAddress.toLowerCase();
  if (expectedContract !== actualContract) {
    throw new Error(`Contract address mismatch: ${expectedContract} vs ${actualContract}`);
  }

  // Collect all known active and superseded identifiers from json sources
  const knownHashes = new Set();
  const knownAddrs = new Set();

  function collect(obj) {
    if (!obj) return;
    if (typeof obj === 'string') {
      if (obj.startsWith('0x') && obj.length === 66) knownHashes.add(obj.toLowerCase());
      if (obj.startsWith('0x') && obj.length === 42) knownAddrs.add(obj.toLowerCase());
    } else if (Array.isArray(obj)) {
      obj.forEach(collect);
    } else if (typeof obj === 'object') {
      Object.values(obj).forEach(collect);
    }
  }

  collect(deployments);
  collect(liveEvidence);

  // Check superseded addresses
  const supersededAddrs = (deployments.supersededDeployments || []).map(s => s.address.toLowerCase());

  const filesToCheck = [];
  if (fs.existsSync(readmePath)) filesToCheck.push(readmePath);
  if (fs.existsSync(docsDir)) {
    for (const f of fs.readdirSync(docsDir)) {
      if (f.endsWith('.md')) filesToCheck.push(path.join(docsDir, f));
    }
  }

  const truncatedPattern = /0x[a-fA-F0-9]{4,16}\.\.\.[a-fA-F0-9]{4,16}/g;
  const txHashPattern = /0x[a-fA-F0-9]{64}/g;

  for (const fpath of filesToCheck) {
    const fname = path.basename(fpath);
    const content = fs.readFileSync(fpath, 'utf8');

    // 1. Truncated hashes check
    const truncMatches = content.match(truncatedPattern);
    if (truncMatches && truncMatches.length > 0) {
      throw new Error(`Truncated hash found in ${fname}: ${truncMatches.join(', ')}`);
    }

    // 2. Check for forbidden undefined
    const lines = content.split('\n');
    lines.forEach((line, idx) => {
      if (line.includes('|')) {
        if (line.toLowerCase().includes('undefined')) {
          throw new Error(`'undefined' found in markdown table in ${fname}:${idx + 1}: ${line}`);
        }
      }
    });

    // 3. Superseded addresses check
    // Superseded addresses may only appear in README.md, PROBES.md, CALIBRATION.md, or EVIDENCE.md tables
    if (fname !== 'README.md' && fname !== 'PROBES.md' && fname !== 'CALIBRATION.md' && fname !== 'EVIDENCE.md') {
      for (const sAddr of supersededAddrs) {
        if (content.toLowerCase().includes(sAddr)) {
          throw new Error(`Superseded address ${sAddr} found in ${fname}. It may only appear in README.md, PROBES.md, CALIBRATION.md, or EVIDENCE.md tables.`);
        }
      }
    }

    // 4. Verification that every tx hash in rendered markdown tables exists in JSON sources
    if (fname === 'README.md' || fname === 'EVIDENCE.md') {
      const tableLines = lines.filter(l => l.includes('|'));
      for (const tline of tableLines) {
        const rowHashes = tline.match(txHashPattern) || [];
        for (const h of rowHashes) {
          if (!knownHashes.has(h.toLowerCase())) {
            throw new Error(`Hash ${h} in ${fname} table does not exist in deployments.json or live_evidence.json`);
          }
        }
      }
    }
  }

  // 5. Operation Distinctness Check: No duplicate hashes across distinct operations
  // Scenario registration and audit hashes must be mutually distinct
  const scenarioHashes = new Map();

  function recordOp(name, hash) {
    if (!hash) return;
    const lower = hash.toLowerCase();
    if (scenarioHashes.has(lower)) {
      const prev = scenarioHashes.get(lower);
      throw new Error(`Discrepancy detected: Tx hash ${hash} is reused for two distinct operations: '${prev}' and '${name}'`);
    }
    scenarioHashes.set(lower, name);
  }

  const sGood = liveEvidence.positiveScenarios?.scenario_good;
  if (sGood) {
    recordOp("register good.html", sGood.registerTx);
    recordOp("audit good.html", sGood.auditTx);
  }

  const sBad = liveEvidence.positiveScenarios?.scenario_bad;
  if (sBad) {
    recordOp("register bad.html", sBad.registerTx);
    recordOp("audit bad.html", sBad.auditTx);
  }

  const sMixed = liveEvidence.positiveScenarios?.scenario_mixed;
  if (sMixed) {
    recordOp("register mixed.html", sMixed.registerTx);
    recordOp("audit mixed.html", sMixed.auditTx);
  }

  const sShell = liveEvidence.shellScenario;
  if (sShell) {
    recordOp("register shell.html", sShell.registerTx);
    recordOp("audit shell.html", sShell.auditTx);
  }

  const sPartial = liveEvidence.partialScenario;
  if (sPartial) {
    recordOp("register large.html", sPartial.registerTx);
    recordOp("audit large.html", sPartial.auditTx);
  }

  const sDemo = liveEvidence.secondaryScenario;
  if (sDemo) {
    recordOp("register demo.html", sDemo.registerTx);
    recordOp("audit 1 demo.html", sDemo.audit1Tx);
    recordOp("audit 2 demo.html", sDemo.audit2Tx);
    recordOp("maintainer note demo.html", sDemo.maintainerNoteTx);
  }

  // Negative tests audit hashes must also be distinct
  const neg = liveEvidence.negativeTests || {};
  for (const [k, v] of Object.entries(neg)) {
    if (v.txHash) {
      recordOp(`negative test: ${v.name}`, v.txHash);
    }
  }

  console.log(`PASS: Evidence consistency check passed without errors (${scenarioHashes.size} distinct operations verified).`);
}

if (require.main === module) {
  checkConsistency();
}

module.exports = { checkConsistency };
