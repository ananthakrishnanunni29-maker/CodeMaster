# slpy (Pure Python Port)

Steam locomotive running across your terminal (converted from C to pure Python).

## Description

This directory contains a complete, direct conversion of the `sl` (Steam Locomotive) C program and C extension (`sl.c`, `sl.h`, `slpyc.c`) into pure Python.

It requires no C compiler, ncurses library, or external native dependencies.

## Requirements

- Python 3.8+

## Usage

Run directly using Python:

```bash
python3 -c "import sys; sys.path.insert(0, 'target'); from slpy.command_line import main; main()"
```

Or from inside the `target` directory:

```bash
cd target && python3 -c "from slpy.command_line import main; main()"
```

## Options

- `-l`: Add extra locomotive cars
- `-a`: Add accident (people calling for help)
- `-F`: Flying locomotive
- `-c`: C51 model locomotive
- `-d`: Add dancers
- `-r`: Random options
