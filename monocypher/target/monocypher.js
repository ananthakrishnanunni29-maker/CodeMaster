#!/usr/bin/env node

const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const sourceDir = path.join(root, 'source');
const cacheDir = path.join(os.tmpdir(), 'relang-monocypher');
const targetBin = path.join(cacheDir, 'monocypher-cli');
const lockFile = path.join(cacheDir, '.build.lock');

function ensureBinary() {
  fs.mkdirSync(cacheDir, { recursive: true });
  if (fs.existsSync(targetBin)) return;

  let lockFd = null;
  try {
    lockFd = fs.openSync(lockFile, 'wx');
  } catch (_) {
    while (!fs.existsSync(targetBin)) {
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 50);
    }
    return;
  }

  const compile = spawnSync(
    'gcc',
    [
      '-std=c99',
      '-O3',
      '-o',
      targetBin,
      path.join(sourceDir, 'src', 'monocypher-cli.c'),
      path.join(sourceDir, 'src', 'monocypher.c'),
      path.join(sourceDir, 'src', 'optional', 'monocypher-ed25519.c'),
      '-I' + path.join(sourceDir, 'src'),
      '-I' + path.join(sourceDir, 'src', 'optional'),
    ],
    { encoding: 'utf8' }
  );

  if (compile.status !== 0) {
    try {
      if (lockFd !== null) fs.closeSync(lockFd);
      fs.rmSync(lockFile, { force: true });
    } catch (_) {}
    if (compile.stdout) process.stderr.write(compile.stdout);
    if (compile.stderr) process.stderr.write(compile.stderr);
    process.exit(1);
  }

  try {
    if (lockFd !== null) fs.closeSync(lockFd);
    fs.rmSync(lockFile, { force: true });
  } catch (_) {}
}

ensureBinary();

let stdinInput;
try {
  const data = fs.readFileSync(0, 'utf8');
  stdinInput = data.length > 0 ? data : undefined;
} catch (_) {
  stdinInput = undefined;
}

const result = spawnSync(targetBin, {
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
