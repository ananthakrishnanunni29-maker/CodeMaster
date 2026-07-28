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

const result = spawnSync(sourceCliPath, [scriptArg], {
  cwd: process.cwd(),
  input: process.stdin.read() ?? undefined,
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
