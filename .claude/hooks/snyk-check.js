#!/usr/bin/env node
// Snyk security hook — runs after Write/Edit on backend files.
// - requirements.txt changed → snyk test (dependency CVE audit)
// - any backend .py changed   → snyk code test (SAST, high+ only)

const { execSync } = require('child_process');
const path = require('path');

let raw = '';
process.stdin.on('data', chunk => (raw += chunk));
process.stdin.on('end', () => {
  let payload;
  try { payload = JSON.parse(raw); } catch { process.exit(0); }

  const f = (payload.tool_input?.file_path || '').replace(/\\/g, '/');
  const inBackend = f.includes('/backend/');

  if (!inBackend) process.exit(0);

  const isReqs = f.endsWith('requirements.txt');
  const isPy   = f.endsWith('.py');

  if (!isReqs && !isPy) process.exit(0);

  const backendDir = f.slice(0, f.lastIndexOf('/backend/') + '/backend'.length + 1);

  try {
    if (isReqs) {
      console.log('\n[snyk] Dependency audit on requirements.txt...');
      execSync(`npx snyk test --file="${f}" --severity-threshold=high`, {
        cwd: backendDir,
        stdio: 'inherit',
      });
    } else {
      console.log('\n[snyk] SAST scan on backend (high+ severity)...');
      execSync(`npx snyk code test --severity-threshold=high`, {
        cwd: backendDir,
        stdio: 'inherit',
      });
    }
  } catch {
    // snyk exits non-zero when issues found — that's expected, don't block Claude
  }
});
