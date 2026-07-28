# img2ascii (Pure Python Port)

JPEG/PNG image to ASCII art converter (converted from C to pure Python).

## Description

This directory contains a complete, direct conversion of the `img2ascii` C application (`main.c`, `args.h`, `utils.h`, `ascii_art.h`) into Python (`img2ascii.py`).

It converts image files (PNG, JPEG, etc.) into ASCII art rendered in full 24-bit ANSI color or monochrome grayscale, with support for custom width, custom character sets, character string reversal, and saving output directly to text files.

## Requirements

- Python 3.8+
- Pillow (`pip install Pillow`)

## Build

No build step required for Python.

## Usage

Run directly using Python:

```bash
# Print 24-bit ANSI color ASCII art (width = 40)
python target/img2ascii.py -i source/images/c.png -w 40 -p

# Print monochrome grayscale ASCII art
python target/img2ascii.py -i source/images/c.png -w 40 -g

# Save ASCII art to an output file
python target/img2ascii.py -i source/images/c.png -w 40 -o output.txt
```

## Command-Line Options

| Option | Long Option | Description |
|--------|-------------|-------------|
| `-i <FILE>` | `--input <FILE>` | Path of the input image file (required) |
| `-o <FILE>` | `--output <FILE>` | Path of the output file |
| `-w <NUMBER>` | `--width <NUMBER>` | Desired width of the ASCII output |
| `-c <STRING>` | `--chars <STRING>` | Character set used for ASCII conversion |
| `-g` | `--grayscale` | Render in monochrome grayscale mode |
| `-p` | `--print` | Print the ASCII output to standard output |
| `-r` | `--reverse` | Reverse the character ramp sequence |
| `-d` | `--debug` | Output diagnostic information (input, output, resolution, character set) |
| `-h` | `--help` | Show usage instructions |
