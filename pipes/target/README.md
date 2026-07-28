# pipes (C implementation)

Animated pipes terminal screensaver written in C.

## Prerequisites

- C compiler (`gcc` or `clang`)
- `ncurses` or `pdcurses` library (with UTF-8 support recommended)

## Build

On Linux/macOS:
```bash
gcc -O2 pipes.c -o pipes -lncursesw
```
or simply:
```bash
make
```

On Windows (MinGW / GCC):
```bash
gcc -O2 pipes.c -o pipes.exe -lpdcurses
```
or if compiling with MSVC / standard C:
```bash
gcc -O2 pipes.c -o pipes.exe
```

## Run

```bash
./pipes
```

Available options:
- `-p`, `--pipes INT`: Number of pipes (default: 1)
- `-f`, `--fps INT`: Frames per second (20-100, default: 75)
- `-s`, `--steady INT`: Steadiness (5-15, default: 13)
- `-r`, `--limit INT`: Character limit before clear screen (default: 2000)
- `-R`, `--random`: Random starting positions
- `-B`, `--no-bold`: Disable bold text
- `-C`, `--no-color`: Disable colors
- `-P`, `--pipe-style INT`: Select pipe style (0-9)
- `-K`, `--keep-style`: Retain style/color on wrap
- `-S`, `--save-config`: Save settings to configuration JSON file
- `-v`, `--version`: Print version
- `-h`, `--help`: Print usage instructions

Interactive Controls (while running):
- `P` / `O`: Increase / decrease steadiness
- `F` / `D`: Increase / decrease FPS
- `B`: Toggle bold
- `C`: Toggle color
- `K`: Toggle keep_style
- `?` or `ESC`: Exit program
