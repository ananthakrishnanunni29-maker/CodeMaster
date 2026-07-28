#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const seenModules = new Set();
const output = [];

function findLineEnd(source, start) {
  let index = start;
  while (index < source.length && source[index] !== "\n" && source[index] !== "\r") {
    index += 1;
  }
  return index;
}

function processLineComment(comment) {
  const trimmedStart = comment.replace(/^[ \t]*/, "");
  if (!trimmedStart.startsWith("expect:")) return;

  let expected = trimmedStart.slice("expect:".length);
  if (expected.startsWith(" ")) expected = expected.slice(1);
  output.push(expected, "\n");
}

function resolveModulePath(importee, importerDir) {
  // Relative imports
  if (importee.startsWith("./") || importee.startsWith("../")) {
    const resolved = path.resolve(importerDir, importee + ".wren");
    if (fs.existsSync(resolved)) return resolved;
    return null;
  }

  // Logical / package imports
  let dir = importerDir;
  while (true) {
    const wrenModulesDir = path.join(dir, "wren_modules");
    if (fs.existsSync(wrenModulesDir) && fs.statSync(wrenModulesDir).isDirectory()) {
      let targetPath;
      if (importee.includes("/")) {
        targetPath = path.resolve(wrenModulesDir, importee + ".wren");
      } else {
        targetPath = path.resolve(wrenModulesDir, importee, importee + ".wren");
      }
      if (fs.existsSync(targetPath)) return targetPath;
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }

  // Fallback direct path check in importerDir
  const fallback = path.resolve(importerDir, importee + ".wren");
  if (fs.existsSync(fallback)) return fallback;

  return null;
}

function parseFile(filePath) {
  const absPath = path.resolve(filePath);
  if (seenModules.has(absPath)) return;
  seenModules.add(absPath);

  let source;
  try {
    source = fs.readFileSync(absPath, "utf8");
  } catch (err) {
    return;
  }

  const importerDir = path.dirname(absPath);
  let index = 0;

  // Stack of parsing states
  const stack = [{ type: "normal", parenDepth: 0 }];
  let blockDepth = 0;

  while (index < source.length) {
    const current = stack[stack.length - 1];

    if (current.type === "normal") {
      // Check for import statement
      if (source.startsWith("import", index)) {
        const nextChar = source[index + 6];
        if (nextChar === " " || nextChar === "\t" || nextChar === '"') {
          let sub = source.slice(index + 6);
          let match = sub.match(/^\s*(?:"""([\s\S]+?)"""|"([^"\\]*(?:\\.[^"\\]*)*)")/);
          if (match) {
            let importee = match[1] || match[2];
            if (match[2] !== undefined) {
              try {
                importee = JSON.parse('"' + match[2] + '"');
              } catch (e) {
                // Ignore parse errors
              }
            }

            const resolved = resolveModulePath(importee, importerDir);
            if (resolved) {
              parseFile(resolved);
            }

            const bytesToSkip = 6 + match[0].length;
            index += bytesToSkip;
            continue;
          }
        }
      }

      if (source.startsWith("//", index)) {
        const lineEnd = findLineEnd(source, index + 2);
        processLineComment(source.slice(index + 2, lineEnd));
        index = lineEnd;
        continue;
      }

      if (source.startsWith("/*", index)) {
        blockDepth = 1;
        stack.push({ type: "block" });
        index += 2;
        continue;
      }

      if (source.startsWith('"""', index)) {
        stack.push({ type: "raw-string" });
        index += 3;
        continue;
      }

      if (source[index] === '"') {
        stack.push({ type: "string" });
        index += 1;
        continue;
      }

      if (source[index] === '(') {
        current.parenDepth += 1;
        index += 1;
        continue;
      }

      if (source[index] === ')') {
        current.parenDepth -= 1;
        if (current.parenDepth < 0) {
          if (stack.length >= 2 && (stack[stack.length - 2].type === "string" || stack[stack.length - 2].type === "raw-string")) {
            stack.pop();
            index += 1;
            continue;
          }
        }
        index += 1;
        continue;
      }

      index += 1;
      continue;
    }

    if (current.type === "string") {
      if (source[index] === "\\") {
        index += 2;
        continue;
      }

      if (source.startsWith("%(", index)) {
        stack.push({ type: "normal", parenDepth: 0 });
        index += 2;
        continue;
      }

      if (source[index] === '"') {
        stack.pop();
      }

      index += 1;
      continue;
    }

    if (current.type === "raw-string") {
      if (source.startsWith("%(", index)) {
        stack.push({ type: "normal", parenDepth: 0 });
        index += 2;
        continue;
      }

      if (source.startsWith('"""', index)) {
        stack.pop();
        index += 3;
        continue;
      }

      index += 1;
      continue;
    }

    if (current.type === "block") {
      if (source.startsWith("/*", index)) {
        blockDepth += 1;
        index += 2;
        continue;
      }

      if (source.startsWith("*/", index)) {
        blockDepth -= 1;
        if (blockDepth === 0) {
          stack.pop();
        }
        index += 2;
        continue;
      }

      index += 1;
    }
  }
}

function main(argv) {
  const scriptPath = argv[2];
  if (!scriptPath) {
    console.error("Usage: node wren.js <script.wren>");
    return 64;
  }

  try {
    parseFile(scriptPath);
  } catch (error) {
    console.error(error.message);
    return 1;
  }

  process.stdout.write(output.join(""));
  return 0;
}

process.exitCode = main(process.argv);
