const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function verifySource() {
  const root = path.dirname(path.dirname(__dirname));
  const contractPath = path.join(root, 'contracts', 'AltCheck.py');
  const deploymentsPath = path.join(root, 'scripts', 'deploy', 'deployments.json');

  const contractCode = fs.readFileSync(contractPath, 'utf8');
  const computedSha = crypto.createHash('sha256').update(contractCode, 'utf8').digest('hex');

  const deployments = JSON.parse(fs.readFileSync(deploymentsPath, 'utf8'));
  const recordedSha = deployments.altCheck.sourceSha256;

  console.log("Local AltCheck.py SHA-256:    ", computedSha);
  console.log("Deployments record SHA-256:   ", recordedSha);

  if (computedSha.toLowerCase() !== recordedSha.toLowerCase()) {
    console.error("FAIL: Source SHA-256 mismatch!");
    process.exit(1);
  }
  console.log("PASS: Local file exactly matches deployed source SHA-256.");
}

verifySource();
