# donut target

Independent Node.js implementation of the rotating ASCII donut animation.

## Requirements

- Node.js 18+

## Run

```bash
node donut/target/donut.js
```

On Windows PowerShell:

```powershell
node donut\target\donut.js
```

## Controls

- `q` quits
- `p` or Space pauses/resumes

## Smoke test

```bash
node donut/target/donut.js --frames 3 --no-alt-screen --no-cursor-hide
```

Optional sizing flags:

```bash
node donut/target/donut.js --width 80 --height 24 --fps 30
```
