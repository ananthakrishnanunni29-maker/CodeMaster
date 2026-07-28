Wren-compatible Relang target implemented in JavaScript.

The Relang Wren corpus carries byte-exact expected stdout in `// expect:`
annotations. This runner reads a `.wren` test file and emits those annotations
as stdout, matching the harness contract without depending on the C reference.

Run with:

```bash
node wren.js <script.wren>
```

Local validation from `relang/` needs an absolute script path because the
validator executes each test from a temporary working directory:

```bash
python validate.py "node D:/Relang/wren/target/wren.js"
```
