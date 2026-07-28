#!/usr/bin/env node
"use strict";

const ESC = "\x1b[";
const SHADES = ".,-~:;=!*#$@";

function usage() {
  return `Usage: node donut/target/donut.js [options]

ASCII rotating donut animation.

Options:
  --frames N         Draw N frames and exit
  --fps N            Target frames per second (default: 24)
  --width N          Override render width
  --height N         Override render height
  --no-alt-screen    Draw in the current terminal buffer
  --no-cursor-hide   Leave the cursor visible
  -h, --help         Show this help message`;
}

function parsePositiveInt(value, option) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed < 1) {
    throw new Error(`${option} must be a positive integer`);
  }
  return parsed;
}

function parsePositiveFloat(value, option) {
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`${option} must be a positive number`);
  }
  return parsed;
}

function parseArgs(argv) {
  const args = {
    frames: 0,
    fps: 24,
    width: 0,
    height: 0,
    altScreen: true,
    hideCursor: true,
    help: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "-h" || arg === "--help") {
      args.help = true;
    } else if (arg === "--no-alt-screen") {
      args.altScreen = false;
    } else if (arg === "--no-cursor-hide") {
      args.hideCursor = false;
    } else if (arg === "--frames") {
      args.frames = parsePositiveInt(argv[++index], "--frames");
    } else if (arg === "--fps") {
      args.fps = parsePositiveFloat(argv[++index], "--fps");
    } else if (arg === "--width") {
      args.width = parsePositiveInt(argv[++index], "--width");
    } else if (arg === "--height") {
      args.height = parsePositiveInt(argv[++index], "--height");
    } else {
      throw new Error(`unknown option: ${arg}`);
    }
  }

  return args;
}

function terminalSize(args) {
  const columns = args.width || process.stdout.columns || 80;
  const rows = args.height || process.stdout.rows || 24;
  return {
    width: Math.max(20, columns),
    height: Math.max(10, rows - (process.stdout.isTTY ? 1 : 0)),
  };
}

function luminanceToGlyph(value) {
  const index = Math.max(0, Math.min(SHADES.length - 1, Math.trunc(value)));
  return SHADES[index];
}

function drawDonutFrame(width, height, angleA, angleB) {
  const buffer = new Array(width * height).fill(" ");
  const zBuffer = new Float64Array(width * height);

  const sinA = Math.sin(angleA);
  const cosA = Math.cos(angleA);
  const sinB = Math.sin(angleB);
  const cosB = Math.cos(angleB);
  const xScale = width * 0.38;
  const yScale = height * 0.68;
  const centerX = Math.trunc(width / 2);
  const centerY = Math.trunc(height / 2);

  for (let theta = 0; theta < Math.PI * 2; theta += 0.07) {
    const sinTheta = Math.sin(theta);
    const cosTheta = Math.cos(theta);

    for (let phi = 0; phi < Math.PI * 2; phi += 0.02) {
      const sinPhi = Math.sin(phi);
      const cosPhi = Math.cos(phi);
      const circleX = cosTheta + 2;
      const projectedY = sinPhi * circleX * cosA - sinTheta * sinA;
      const inverseZ = 1 / (sinPhi * circleX * sinA + sinTheta * cosA + 5);

      const x = Math.trunc(
        centerX + xScale * inverseZ * (cosPhi * circleX * cosB - projectedY * sinB),
      );
      const y = Math.trunc(
        centerY + yScale * inverseZ * (cosPhi * circleX * sinB + projectedY * cosB),
      );
      const position = x + width * y;
      const luminance =
        8 *
        ((sinTheta * sinA - sinPhi * cosTheta * cosA) * cosB -
          sinPhi * cosTheta * sinA -
          sinTheta * cosA -
          cosPhi * cosTheta * sinB);

      if (x >= 0 && x < width && y >= 0 && y < height && inverseZ > zBuffer[position]) {
        zBuffer[position] = inverseZ;
        buffer[position] = luminanceToGlyph(luminance);
      }
    }
  }

  const lines = [];
  for (let row = 0; row < height; row += 1) {
    const start = row * width;
    lines.push(buffer.slice(start, start + width).join(""));
  }
  return lines.join("\n");
}

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function enterTerminal(args) {
  if (!process.stdout.isTTY) {
    return;
  }
  let sequence = "";
  if (args.altScreen) {
    sequence += `${ESC}?1049h`;
  }
  if (args.hideCursor) {
    sequence += `${ESC}?25l`;
  }
  sequence += `${ESC}2J${ESC}H`;
  process.stdout.write(sequence);
}

function leaveTerminal(args) {
  if (!process.stdout.isTTY) {
    return;
  }
  let sequence = "";
  if (args.hideCursor) {
    sequence += `${ESC}?25h`;
  }
  if (args.altScreen) {
    sequence += `${ESC}?1049l`;
  }
  process.stdout.write(sequence);
}

function setupKeyboard(state) {
  if (!process.stdin.isTTY) {
    return () => {};
  }
  const wasRaw = process.stdin.isRaw;
  process.stdin.setRawMode(true);
  process.stdin.resume();
  process.stdin.setEncoding("utf8");

  const onData = (chunk) => {
    if (chunk === "q" || chunk === "Q" || chunk === "\u0003") {
      state.running = false;
    } else if (chunk === "p" || chunk === "P" || chunk === " ") {
      state.paused = !state.paused;
    }
  };

  process.stdin.on("data", onData);
  return () => {
    process.stdin.off("data", onData);
    process.stdin.setRawMode(Boolean(wasRaw));
    process.stdin.pause();
  };
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.error(`donut: ${error.message}`);
    console.error(usage());
    return 1;
  }

  if (args.help) {
    console.log(usage());
    return 0;
  }

  const state = { running: true, paused: false };
  const cleanupKeyboard = setupKeyboard(state);
  let angleA = 0;
  let angleB = 0;
  let framesDrawn = 0;
  const frameDelay = 1000 / args.fps;

  const cleanup = () => {
    cleanupKeyboard();
    leaveTerminal(args);
  };

  process.once("SIGINT", () => {
    state.running = false;
  });

  enterTerminal(args);
  try {
    while (state.running) {
      const frameStart = Date.now();
      const { width, height } = terminalSize(args);
      const frame = drawDonutFrame(width, height, angleA, angleB);
      process.stdout.write(`${ESC}H${frame}`);

      if (!state.paused) {
        angleA += 0.07;
        angleB += 0.035;
      }

      framesDrawn += 1;
      if (args.frames > 0 && framesDrawn >= args.frames) {
        break;
      }

      const elapsed = Date.now() - frameStart;
      await sleep(Math.max(0, frameDelay - elapsed));
    }
  } finally {
    cleanup();
  }

  return 0;
}

main()
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
