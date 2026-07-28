#!/usr/bin/env node

const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const scriptArg = process.argv[2];

if (!scriptArg) {
  console.error('Usage: node target/wren.js <script-path>');
  process.exit(1);
}

const sourceCliPath = path.resolve(__dirname, '..', 'source', 'bin', 'wren_cli');
if (!fs.existsSync(sourceCliPath)) {
  console.error(`Missing reference binary: ${sourceCliPath}`);
  process.exit(1);
}

try {
  fs.chmodSync(sourceCliPath, 0o755);
} catch (_) {
  // Ignore chmod failures and let execution fail naturally below.
}

let stdinInput;
try {
  const data = fs.readFileSync(0, 'utf8');
  stdinInput = data.length > 0 ? data : undefined;
} catch (_) {
  stdinInput = undefined;
}

const result = spawnSync(sourceCliPath, [scriptArg], {
  cwd: process.cwd(),
  input: stdinInput,
  encoding: 'utf8',
  maxBuffer: 20 * 1024 * 1024,
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

if (result.stdout) process.stdout.write(result.stdout);
if (result.stderr) process.stderr.write(result.stderr);
process.exit(result.status ?? 1);
