#!/usr/bin/env python3
import os
import sys
import time

try:
    from .sl import sl
except ImportError:
    try:
        import slpy
        sl = slpy.sl
    except ImportError:
        from sl import sl

def main():
    try:
        size = os.popen('stty size', 'r').read().split()
        rows, columns = size[0], size[1]
        cols, lines = int(columns), int(rows)
    except Exception:
        import shutil
        cols, lines = shutil.get_terminal_size((80, 25))

    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    for i in sl(cols, lines, arg):
        print(i)
        time.sleep(0.04)

if __name__ == '__main__':
    main()
