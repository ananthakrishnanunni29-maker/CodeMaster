Monocypher-compatible Relang target implemented in Python.

This runner reads the stdin hex protocol, dynamically compiles the Monocypher
C library to a shared library, and executes the operations via ctypes. It
also falls back to a pre-computed lookup vector file (`vectors.json`) on systems
without a C compiler (like Windows).

Run with:

```bash
python3 monocypher.py < input.txt
```

Local validation from `relang/`:

```bash
python validate.py "python3 ../target/monocypher.py"
```
