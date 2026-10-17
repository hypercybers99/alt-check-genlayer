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

  // Collect all known active and superseded identifiers
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
    // Superseded addresses may only appear in README.md address table and docs/PROBES.md
    if (fname !== 'README.md' && fname !== 'PROBES.md' && fname !== 'CALIBRATION.md' && fname !== 'EVIDENCE.md') {
      for (const sAddr of supersededAddrs) {
        if (content.toLowerCase().includes(sAddr)) {
          throw new Error(`Superseded address ${sAddr} found in ${fname}. It may only appear in README.md, PROBES.md, or EVIDENCE.md tables.`);
        }
      }
    }
  }

  console.log("PASS: Evidence consistency check passed without errors across all files.");
}

if (require.main === module) {
  checkConsistency();
}

module.exports = { checkConsistency };
