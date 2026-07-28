# qrterminal (Pure Python Port)

QR code generator for the terminal (converted from Go to pure Python).

## Description

This directory contains a complete, direct conversion of the `qrterminal` Go application (`qrterminal.go` and `cmd/qrterminal/main.go`) into pure Python.

It requires no external Python packages or native dependencies — it includes a self-contained pure-Python QR Code encoder and terminal renderer matching the original Go implementation.

## Requirements

- Python 3.8+

## Build

No build step required for Python.

## Usage

Run directly using Python:

```bash
# Standard output
python target/qrterminal.py "https://example.com"

# Half-block mode (recommmended for phone camera scanning)
python target/qrterminal.py -m "https://example.com"
```

Or piped via stdin:

```bash
echo "https://example.com" | python target/qrterminal.py
```

## Options

- `-v`: Output debugging information
- `-l`: Error correction level (`L`, `M`, `H`; default: `L`)
- `-q`: Size of quietzone border (default: `2`)
- `-s`: Disable sixel format for output
- `-m`: Half-block mode (renders compact Unicode blocks `█`, `▀`, `▄` for instant scanning on any terminal/phone camera)
