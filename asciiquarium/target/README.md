# asciiquarium target

Independent Python implementation of the terminal aquarium animation.

## Requirements

- Python 3.10+
- ANSI-capable terminal

## Run

```bash
python3 asciiquarium/target/asciiquarium.py
```

On Windows PowerShell:

```powershell
python asciiquarium\target\asciiquarium.py
```

## Controls

- `q` quits
- `p` pauses or resumes
- `r` redraws the aquarium

## Smoke test

```bash
python3 asciiquarium/target/asciiquarium.py --frames 3 --no-alt-screen --no-color
```
