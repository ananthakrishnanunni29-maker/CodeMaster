# monocypher target (JavaScript)

## Prerequisites

- Node.js 18+
- `gcc` (for building `monocypher-cli` from `source/` on first run)

## Run

```bash
node target/monocypher.js
```

## Validate

From `/home/runner/work/CodeMaster/CodeMaster/monocypher`:

```bash
cd relang && python3 validate.py "node ../target/monocypher.js"
```
