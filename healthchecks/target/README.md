# healthchecks target

Dependency-free Node.js implementation for the HTTP replay challenge.

## Run

```bash
node server.js
```

The server listens on `PORT` if set, otherwise `8000`.

## Validate

From the repository root, with the server running:

```bash
py -3 healthchecks/relang/validate.py http://localhost:8000
```
