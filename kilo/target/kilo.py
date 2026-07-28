#!/usr/bin/env python3
"""Kilo -- A very simple editor in less than 1-kilo lines of code (as counted
 *         by "cloc"). Does not depend on libcurses, directly emits VT100
 *         escapes on the terminal.
 *
 * -----------------------------------------------------------------------
 *
 * Copyright (C) 2016 Salvatore Sanfilippo <antirez at gmail dot com>
 *
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 *  *  Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *
 *  *  Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer in the
 *     documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import sys
import os
import time
import signal
import platform
import ctypes
import shutil

KILO_VERSION = "0.0.1"

IS_WINDOWS = platform.system() == "Windows"

if not IS_WINDOWS:
    import termios
    import fcntl
    import struct

# Syntax highlight types
HL_NORMAL = 0
HL_NONPRINT = 1
HL_COMMENT = 2
HL_MLCOMMENT = 3
HL_KEYWORD1 = 4
HL_KEYWORD2 = 5
HL_STRING = 6
HL_NUMBER = 7
HL_MATCH = 8

HL_HIGHLIGHT_STRINGS = 1 << 0
HL_HIGHLIGHT_NUMBERS = 1 << 1

# KEY_ACTION enum
KEY_NULL = 0
CTRL_C = 3
CTRL_D = 4
CTRL_F = 6
CTRL_H = 8
TAB = 9
CTRL_L = 12
ENTER = 13
CTRL_Q = 17
CTRL_S = 19
CTRL_U = 21
ESC = 27
BACKSPACE = 127
ARROW_LEFT = 1000
ARROW_RIGHT = 1001
ARROW_UP = 1002
ARROW_DOWN = 1003
DEL_KEY = 1004
HOME_KEY = 1005
END_KEY = 1006
PAGE_UP = 1007
PAGE_DOWN = 1008
KILO_QUIT_TIMES = 3


class EditorSyntax:
    def __init__(self, filematch, keywords, singleline_comment_start,
                 multiline_comment_start, multiline_comment_end, flags):
        self.filematch = filematch
        self.keywords = keywords
        self.singleline_comment_start = singleline_comment_start
        self.multiline_comment_start = multiline_comment_start
        self.multiline_comment_end = multiline_comment_end
        self.flags = flags


class Erow:
    def __init__(self):
        self.idx = 0
        self.size = 0
        self.rsize = 0
        self.chars = bytearray()
        self.render = bytearray()
        self.hl = []
        self.hl_oc = 0


class Hlcolor:
    def __init__(self, r=0, g=0, b=0):
        self.r = r
        self.g = g
        self.b = b


class EditorConfig:
    def __init__(self):
        self.cx = 0
        self.cy = 0
        self.rowoff = 0
        self.coloff = 0
        self.screenrows = 0
        self.screencols = 0
        self.numrows = 0
        self.rawmode = 0
        self.row = []
        self.dirty = 0
        self.filename = None
        self.statusmsg = ""
        self.statusmsg_time = 0.0
        self.syntax = None
        self.quit_times = KILO_QUIT_TIMES


E = EditorConfig()

# =========================== Syntax highlights DB =========================

C_HL_extensions = [".c", ".h", ".cpp", ".hpp", ".cc"]
C_HL_keywords = [
    "auto", "break", "case", "continue", "default", "do", "else", "enum",
    "extern", "for", "goto", "if", "register", "return", "sizeof", "static",
    "struct", "switch", "typedef", "union", "volatile", "while", "NULL",

    "alignas", "alignof", "and", "and_eq", "asm", "bitand", "bitor", "class",
    "compl", "constexpr", "const_cast", "deltype", "delete", "dynamic_cast",
    "explicit", "export", "false", "friend", "inline", "mutable", "namespace",
    "new", "noexcept", "not", "not_eq", "nullptr", "operator", "or", "or_eq",
    "private", "protected", "public", "reinterpret_cast", "static_assert",
    "static_cast", "template", "this", "thread_local", "throw", "true", "try",
    "typeid", "typename", "virtual", "xor", "xor_eq",

    "int|", "long|", "double|", "float|", "char|", "unsigned|", "signed|",
    "void|", "short|", "auto|", "const|", "bool|",
]

HLDB = [
    EditorSyntax(
        C_HL_extensions,
        C_HL_keywords,
        "//", "/*", "*/",
        HL_HIGHLIGHT_STRINGS | HL_HIGHLIGHT_NUMBERS
    )
]

HLDB_ENTRIES = len(HLDB)

# ======================= Low level terminal handling ======================

orig_termios = None
if IS_WINDOWS:
    orig_console_mode_in = None
    orig_console_mode_out = None

KERNEL32 = None
if IS_WINDOWS:
    KERNEL32 = ctypes.windll.kernel32

    class COORD(ctypes.Structure):
        _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

    class SMALL_RECT(ctypes.Structure):
        _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                    ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]

    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", ctypes.c_ushort),
            ("srWindow", SMALL_RECT),
            ("dwMaximumWindowSize", COORD),
        ]


def disable_raw_mode(fd):
    global E
    if E.rawmode:
        if IS_WINDOWS:
            if orig_console_mode_in is not None:
                KERNEL32.SetConsoleMode(
                    KERNEL32.GetStdHandle(-10), orig_console_mode_in)
            if orig_console_mode_out is not None:
                KERNEL32.SetConsoleMode(
                    KERNEL32.GetStdHandle(-11), orig_console_mode_out)
        else:
            termios.tcsetattr(fd, termios.TCSAFLUSH, orig_termios)
        E.rawmode = 0


def editor_at_exit():
    disable_raw_mode(sys.stdin.fileno())


def enable_raw_mode(fd):
    global E, orig_termios
    if IS_WINDOWS:
        global orig_console_mode_in, orig_console_mode_out
        if E.rawmode:
            return 0
        try:
            stdin_handle = KERNEL32.GetStdHandle(-10)
            stdout_handle = KERNEL32.GetStdHandle(-11)
            mode_in = ctypes.c_uint32()
            mode_out = ctypes.c_uint32()
            if not KERNEL32.GetConsoleMode(stdin_handle, ctypes.byref(mode_in)):
                return -1
            if not KERNEL32.GetConsoleMode(stdout_handle, ctypes.byref(mode_out)):
                return -1
            orig_console_mode_in = mode_in.value
            orig_console_mode_out = mode_out.value
            new_mode_in = mode_in.value
            new_mode_in &= ~(0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020 | 0x0040)
            new_mode_in |= 0x0200
            new_mode_out = mode_out.value | 0x0004
            if not KERNEL32.SetConsoleMode(stdin_handle, new_mode_in):
                return -1
            if not KERNEL32.SetConsoleMode(stdout_handle, new_mode_out):
                return -1
            import atexit
            atexit.register(editor_at_exit)
            E.rawmode = 1
            return 0
        except Exception:
            return -1
    else:
        if E.rawmode:
            return 0
        if not os.isatty(fd):
            return -1
        import atexit
        atexit.register(editor_at_exit)
        try:
            orig_termios = termios.tcgetattr(fd)
        except termios.error:
            return -1
        raw = termios.tcgetattr(fd)
        raw[0] &= ~(termios.BRKINT | termios.ICRNL | termios.INPCK | termios.ISTRIP | termios.IXON)
        raw[1] &= ~(termios.OPOST)
        raw[2] |= termios.CS8
        raw[3] &= ~(termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)
        raw[6][termios.VMIN] = 0
        raw[6][termios.VTIME] = 1
        termios.tcsetattr(fd, termios.TCSAFLUSH, raw)
        E.rawmode = 1
        return 0


def editor_read_key(fd):
    if IS_WINDOWS:
        import msvcrt
        while True:
            c = msvcrt.getch()
            if isinstance(c, bytes):
                c = ord(c)
            else:
                c = ord(c)
            if c == 0x00 or c == 0xE0:
                c2 = msvcrt.getch()
                if isinstance(c2, bytes):
                    c2 = ord(c2)
                else:
                    c2 = ord(c2)
                mapping = {
                    72: ARROW_UP,
                    80: ARROW_DOWN,
                    75: ARROW_LEFT,
                    77: ARROW_RIGHT,
                    73: PAGE_UP,
                    81: PAGE_DOWN,
                    71: HOME_KEY,
                    79: END_KEY,
                    83: DEL_KEY,
                    82: DEL_KEY,
                }
                return mapping.get(c2, ESC)
            elif c == ESC:
                if msvcrt.kbhit():
                    seq1 = msvcrt.getch()
                    if isinstance(seq1, bytes):
                        seq1 = ord(seq1)
                    else:
                        seq1 = ord(seq1)
                    if seq1 == 0x00 or seq1 == 0xE0:
                        seq2 = msvcrt.getch()
                        if isinstance(seq2, bytes):
                            seq2 = ord(seq2)
                        else:
                            seq2 = ord(seq2)
                        mapping = {
                            72: ARROW_UP,
                            80: ARROW_DOWN,
                            75: ARROW_LEFT,
                            77: ARROW_RIGHT,
                            73: PAGE_UP,
                            81: PAGE_DOWN,
                            71: HOME_KEY,
                            79: END_KEY,
                            83: DEL_KEY,
                        }
                        return mapping.get(seq2, ESC)
                    return ESC
                return ESC
            else:
                return c
    else:
        while True:
            buf = os.read(fd, 1)
            if not buf:
                continue
            c = buf[0]
            if c == ESC:
                seq = os.read(fd, 1)
                if not seq:
                    return ESC
                seq1 = seq[0]
                seq = os.read(fd, 1)
                if not seq:
                    return ESC
                seq2 = seq[0]
                if seq1 == ord('['):
                    if ord('0') <= seq2 <= ord('9'):
                        seq = os.read(fd, 1)
                        if not seq:
                            return ESC
                        seq3 = seq[0]
                        if seq3 == ord('~'):
                            if seq2 == ord('3'):
                                return DEL_KEY
                            elif seq2 == ord('5'):
                                return PAGE_UP
                            elif seq2 == ord('6'):
                                return PAGE_DOWN
                    else:
                        if seq2 == ord('A'):
                            return ARROW_UP
                        elif seq2 == ord('B'):
                            return ARROW_DOWN
                        elif seq2 == ord('C'):
                            return ARROW_RIGHT
                        elif seq2 == ord('D'):
                            return ARROW_LEFT
                        elif seq2 == ord('H'):
                            return HOME_KEY
                        elif seq2 == ord('F'):
                            return END_KEY
                elif seq1 == ord('O'):
                    if seq2 == ord('H'):
                        return HOME_KEY
                    elif seq2 == ord('F'):
                        return END_KEY
                return ESC
            else:
                return c


def get_cursor_position(ifd, ofd):
    rows = 0
    cols = 0
    if IS_WINDOWS:
        try:
            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            stdout_handle = KERNEL32.GetStdHandle(-11)
            if KERNEL32.GetConsoleScreenBufferInfo(stdout_handle, ctypes.byref(csbi)):
                rows = csbi.dwCursorPosition.Y + 1
                cols = csbi.dwCursorPosition.X + 1
                return 0, rows, cols
        except Exception:
            pass
        try:
            sz = shutil.get_terminal_size()
            rows = 1
            cols = 1
            return 0, rows, cols
        except Exception:
            pass
        return -1, rows, cols
    else:
        buf = bytearray()
        os.write(ofd, b"\x1b[6n")
        while True:
            b = os.read(ifd, 1)
            if not b:
                break
            buf.append(b[0])
            if b[0] == ord('R'):
                break
        if len(buf) < 2 or buf[0] != ESC or buf[1] != ord('['):
            return -1, rows, cols
        try:
            response = bytes(buf[2:-1]).decode('ascii')
            parts = response.split(';')
            rows = int(parts[0])
            cols = int(parts[1])
        except (ValueError, IndexError):
            return -1, rows, cols
        return 0, rows, cols


def get_window_size(ifd, ofd):
    rows = 0
    cols = 0
    if IS_WINDOWS:
        try:
            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            stdout_handle = KERNEL32.GetStdHandle(-11)
            if KERNEL32.GetConsoleScreenBufferInfo(stdout_handle, ctypes.byref(csbi)):
                cols = csbi.srWindow.Right - csbi.srWindow.Left + 1
                rows = csbi.srWindow.Bottom - csbi.srWindow.Top + 1
                if rows > 0 and cols > 0:
                    return 0, rows, cols
        except Exception:
            pass
        try:
            sz = shutil.get_terminal_size()
            cols = sz.columns
            rows = sz.lines
            return 0, rows, cols
        except Exception:
            pass
        return -1, rows, cols
    else:
        try:
            s = struct.pack('HHHH', 0, 0, 0, 0)
            result = fcntl.ioctl(1, termios.TIOCGWINSZ, s)
            ws_row, ws_col = struct.unpack('HHHH', result)[:2]
            if ws_col != 0:
                cols = ws_col
                rows = ws_row
                return 0, rows, cols
        except (IOError, OSError):
            pass
        try:
            sz = shutil.get_terminal_size()
            cols = sz.columns
            rows = sz.lines
            return 0, rows, cols
        except Exception:
            pass
        ret, orig_row, orig_col = get_cursor_position(ifd, ofd)
        if ret == -1:
            return -1, rows, cols
        os.write(ofd, b"\x1b[999C\x1b[999B")
        ret, rows, cols = get_cursor_position(ifd, ofd)
        if ret == -1:
            return -1, rows, cols
        seq = "\x1b[{};{}H".format(orig_row, orig_col)
        os.write(ofd, seq.encode('ascii'))
        return 0, rows, cols


# ====================== Syntax highlight color scheme ====================


_WHITESPACE_BYTES = set(b' \t\n\r\x0b\x0c')
_SEPARATOR_BYTES = set(b',.()+-/*=~%[];')


def is_separator(c):
    return c == 0 or c in _WHITESPACE_BYTES or c in _SEPARATOR_BYTES


def editor_row_has_open_comment(row):
    if row.hl and row.rsize and row.hl[row.rsize - 1] == HL_MLCOMMENT and \
       (row.rsize < 2 or (row.render[row.rsize - 2] != ord('*') or
                          row.render[row.rsize - 1] != ord('/'))):
        return 1
    return 0


def editor_update_syntax(row):
    row.hl = [HL_NORMAL] * row.rsize
    if E.syntax is None:
        return

    keywords = E.syntax.keywords
    scs = E.syntax.singleline_comment_start
    mcs = E.syntax.multiline_comment_start
    mce = E.syntax.multiline_comment_end
    flags = E.syntax.flags
    highlight_strings = bool(flags & HL_HIGHLIGHT_STRINGS)
    highlight_numbers = bool(flags & HL_HIGHLIGHT_NUMBERS)

    p = row.render
    i = 0
    while i < len(p) and chr(p[i]).isspace():
        i += 1
    prev_sep = 1
    in_string = 0
    in_comment = 0

    if row.idx > 0 and editor_row_has_open_comment(E.row[row.idx - 1]):
        in_comment = 1

    while i < len(p):
        c = p[i]
        # Handle // comments
        if prev_sep and c == ord(scs[0]) and i + 1 < len(p) and p[i + 1] == ord(scs[1]):
            for j in range(i, len(p)):
                row.hl[j] = HL_COMMENT
            return

        # Handle multi line comments
        if in_comment:
            row.hl[i] = HL_MLCOMMENT
            if i + 1 < len(p) and c == ord(mce[0]) and p[i + 1] == ord(mce[1]):
                row.hl[i + 1] = HL_MLCOMMENT
                i += 2
                in_comment = 0
                prev_sep = 1
                continue
            else:
                prev_sep = 0
                i += 1
                continue
        elif i + 1 < len(p) and c == ord(mcs[0]) and p[i + 1] == ord(mcs[1]):
            row.hl[i] = HL_MLCOMMENT
            row.hl[i + 1] = HL_MLCOMMENT
            i += 2
            in_comment = 1
            prev_sep = 0
            continue

        # Handle "" and ''
        if highlight_strings:
            if in_string:
                row.hl[i] = HL_STRING
                if c == ord('\\'):
                    if i + 1 < len(p):
                        row.hl[i + 1] = HL_STRING
                        i += 2
                        prev_sep = 0
                        continue
                if c == in_string:
                    in_string = 0
                i += 1
                continue
            else:
                if c == ord('"') or c == ord("'"):
                    in_string = c
                    row.hl[i] = HL_STRING
                    i += 1
                    prev_sep = 0
                    continue

        # Handle non printable chars
        if not (32 <= c <= 126):
            row.hl[i] = HL_NONPRINT
            i += 1
            prev_sep = 0
            continue

        # Handle numbers
        if highlight_numbers:
            if (chr(c).isdigit() and (prev_sep or (i > 0 and row.hl[i - 1] == HL_NUMBER))) or \
               (c == ord('.') and i > 0 and row.hl[i - 1] == HL_NUMBER):
                row.hl[i] = HL_NUMBER
                i += 1
                prev_sep = 0
                continue

        # Handle keywords and lib calls
        if prev_sep:
            matched = False
            for kw in keywords:
                klen = len(kw)
                kw2 = kw[-1] == '|'
                if kw2:
                    actual_kw = kw[:-1]
                    klen -= 1
                else:
                    actual_kw = kw
                actual_bytes = actual_kw.encode('ascii')
                if i + klen <= len(p) and p[i:i + klen] == actual_bytes and \
                   (i + klen >= len(p) or is_separator(p[i + klen])):
                    for j in range(klen):
                        row.hl[i + j] = HL_KEYWORD2 if kw2 else HL_KEYWORD1
                    i += klen
                    prev_sep = 0
                    matched = True
                    break
            if matched:
                continue

        prev_sep = is_separator(c)
        i += 1

    oc = editor_row_has_open_comment(row)
    if row.hl_oc != oc and row.idx + 1 < E.numrows:
        editor_update_syntax(E.row[row.idx + 1])
    row.hl_oc = oc


def editor_syntax_to_color(hl):
    mapping = {
        HL_COMMENT: 36,
        HL_MLCOMMENT: 36,
        HL_KEYWORD1: 33,
        HL_KEYWORD2: 32,
        HL_STRING: 35,
        HL_NUMBER: 31,
        HL_MATCH: 34,
    }
    return mapping.get(hl, 37)


def editor_select_syntax_highlight(filename):
    for s in HLDB:
        for pat in s.filematch:
            idx = filename.find(pat)
            if idx != -1:
                if pat[0] != '.' or idx + len(pat) == len(filename):
                    E.syntax = s
                    return


# ======================= Editor rows implementation =======================


def editor_update_row(row):
    tabs = sum(1 for c in row.chars if c == TAB)
    nonprint = 0
    render = bytearray()
    for c in row.chars:
        if c == TAB:
            render.append(ord(' '))
            while (len(render) + 1) % 8 != 0:
                render.append(ord(' '))
        else:
            render.append(c)
    row.render = render
    row.rsize = len(render)
    editor_update_syntax(row)


def editor_insert_row(at, s, length):
    global E
    if at > E.numrows:
        return
    new_row = Erow()
    new_row.size = length
    new_row.chars = bytearray(s[:length])
    new_row.hl = []
    new_row.hl_oc = 0
    new_row.render = bytearray()
    new_row.rsize = 0
    new_row.idx = at
    E.row.insert(at, new_row)
    for j in range(at + 1, E.numrows + 1):
        if j < len(E.row):
            E.row[j].idx += 1
    editor_update_row(E.row[at])
    E.numrows += 1
    E.dirty += 1


def editor_free_row(row):
    row.render = None
    row.chars = None
    row.hl = None


def editor_del_row(at):
    global E
    if at >= E.numrows:
        return
    row = E.row[at]
    editor_free_row(row)
    del E.row[at]
    for j in range(at, E.numrows - 1):
        if j < len(E.row):
            E.row[j].idx -= 1
    E.numrows -= 1
    E.dirty += 1


def editor_rows_to_string():
    totlen = sum(row.size + 1 for row in E.row)
    buf = bytearray(totlen)
    offset = 0
    for row in E.row:
        buf[offset:offset + row.size] = row.chars
        offset += row.size
        buf[offset] = ord('\n')
        offset += 1
    return bytes(buf)


def editor_row_insert_char(row, at, c):
    if at > row.size:
        padlen = at - row.size
        row.chars.extend(b' ' * padlen)
        row.chars.append(c)
        row.size += padlen + 1
    else:
        row.chars.insert(at, c)
        row.size += 1
    editor_update_row(row)
    E.dirty += 1


def editor_row_append_string(row, s, length):
    row.chars.extend(s[:length])
    row.size += length
    editor_update_row(row)
    E.dirty += 1


def editor_row_del_char(row, at):
    if row.size <= at:
        return
    del row.chars[at]
    editor_update_row(row)
    row.size -= 1
    E.dirty += 1


def editor_insert_char(c):
    global E
    filerow = E.rowoff + E.cy
    filecol = E.coloff + E.cx
    row = E.row[filerow] if filerow < E.numrows else None
    if row is None:
        while E.numrows <= filerow:
            editor_insert_row(E.numrows, b"", 0)
    row = E.row[filerow]
    editor_row_insert_char(row, filecol, c)
    if E.cx == E.screencols - 1:
        E.coloff += 1
    else:
        E.cx += 1
    E.dirty += 1


def editor_insert_newline():
    global E
    filerow = E.rowoff + E.cy
    filecol = E.coloff + E.cx
    row = E.row[filerow] if filerow < E.numrows else None
    if row is None:
        if filerow == E.numrows:
            editor_insert_row(filerow, b"", 0)
            if E.cy == E.screenrows - 1:
                E.rowoff += 1
            else:
                E.cy += 1
            E.cx = 0
            E.coloff = 0
        return
    if filecol >= row.size:
        filecol = row.size
    if filecol == 0:
        editor_insert_row(filerow, b"", 0)
    else:
        editor_insert_row(filerow + 1, row.chars[filecol:], row.size - filecol)
        row = E.row[filerow]
        row.chars = row.chars[:filecol]
        row.size = filecol
        editor_update_row(row)
    if E.cy == E.screenrows - 1:
        E.rowoff += 1
    else:
        E.cy += 1
    E.cx = 0
    E.coloff = 0


def editor_del_char():
    global E
    filerow = E.rowoff + E.cy
    filecol = E.coloff + E.cx
    row = E.row[filerow] if filerow < E.numrows else None
    if row is None or (filecol == 0 and filerow == 0):
        return
    if filecol == 0:
        filecol = E.row[filerow - 1].size
        editor_row_append_string(E.row[filerow - 1], row.chars, row.size)
        editor_del_row(filerow)
        row = None
        if E.cy == 0:
            E.rowoff -= 1
        else:
            E.cy -= 1
        E.cx = filecol
        if E.cx >= E.screencols:
            shift = (E.screencols - E.cx) + 1
            E.cx -= shift
            E.coloff += shift
    else:
        editor_row_del_char(row, filecol - 1)
        if E.cx == 0 and E.coloff:
            E.coloff -= 1
        else:
            E.cx -= 1
    if row is not None:
        editor_update_row(row)
    E.dirty += 1


def editor_open(filename):
    global E
    E.dirty = 0
    E.filename = filename
    try:
        fp = open(filename, 'rb')
    except FileNotFoundError:
        return 1
    except IOError:
        print("Error opening file", file=sys.stderr)
        sys.exit(1)
    with fp:
        for line in fp:
            if line and line[-1] in (ord('\n'), ord('\r')):
                line = line[:-1]
            if line and line[-1] in (ord('\r'),):
                line = line[:-1]
            editor_insert_row(E.numrows, line, len(line))
    E.dirty = 0
    return 0


def editor_save():
    global E
    buf = editor_rows_to_string()
    length = len(buf)
    try:
        with open(E.filename, 'wb') as f:
            f.write(buf)
    except IOError:
        editor_set_status_message("Can't save! I/O error: {}".format(
            "error saving file"))
        return 1
    E.dirty = 0
    editor_set_status_message("{} bytes written on disk".format(length))
    return 0


# ============================= Terminal update ============================


class Abuf:
    __slots__ = ('b', 'len')

    def __init__(self):
        self.b = bytearray()
        self.len = 0

    def append(self, s, length):
        if isinstance(s, str):
            s = s.encode('ascii')
        self.b.extend(s[:length])
        self.len += length


def abuf_init():
    return Abuf()


def abuf_free(ab):
    ab.b = None
    ab.len = 0


def editor_refresh_screen():
    global E
    ab = Abuf()
    ab.append(b"\x1b[?25l", 6)
    ab.append(b"\x1b[H", 3)
    for y in range(E.screenrows):
        filerow = E.rowoff + y
        if filerow >= E.numrows:
            if E.numrows == 0 and y == E.screenrows // 3:
                welcome = "Kilo editor -- verison {}\x1b[0K\r\n".format(KILO_VERSION)
                welcomelen = len(welcome)
                padding = (E.screencols - welcomelen) // 2
                if padding:
                    ab.append(b"~", 1)
                    padding -= 1
                while padding:
                    ab.append(b" ", 1)
                    padding -= 1
                ab.append(welcome, welcomelen)
            else:
                ab.append(b"~\x1b[0K\r\n", 7)
            continue
        r = E.row[filerow]
        length = r.rsize - E.coloff
        current_color = -1
        if length > 0:
            if length > E.screencols:
                length = E.screencols
            c = r.render[E.coloff:]
            hl = r.hl[E.coloff:]
            for j in range(min(length, len(c))):
                if hl[j] == HL_NONPRINT:
                    ab.append(b"\x1b[7m", 4)
                    cv = c[j]
                    if cv <= 26:
                        sym = ord('@') + cv
                    else:
                        sym = ord('?')
                    ab.append(bytes([sym]), 1)
                    ab.append(b"\x1b[0m", 4)
                elif hl[j] == HL_NORMAL:
                    if current_color != -1:
                        ab.append(b"\x1b[39m", 5)
                        current_color = -1
                    ab.append(bytes([c[j]]), 1)
                else:
                    color = editor_syntax_to_color(hl[j])
                    if color != current_color:
                        buf = "\x1b[{}m".format(color)
                        current_color = color
                        ab.append(buf, len(buf))
                    ab.append(bytes([c[j]]), 1)
        ab.append(b"\x1b[39m", 5)
        ab.append(b"\x1b[0K", 4)
        ab.append(b"\r\n", 2)

    ab.append(b"\x1b[0K", 4)
    ab.append(b"\x1b[7m", 4)
    fname = E.filename if E.filename else "[No Name]"
    status = "{:.20} - {} lines {}".format(
        fname, E.numrows, "(modified)" if E.dirty else "")
    rstatus = "{}/{}".format(E.rowoff + E.cy + 1, E.numrows)
    length = len(status)
    if length > E.screencols:
        length = E.screencols
    ab.append(status[:length], length)
    while length < E.screencols:
        if E.screencols - length == len(rstatus):
            ab.append(rstatus, len(rstatus))
            break
        else:
            ab.append(b" ", 1)
            length += 1
    ab.append(b"\x1b[0m\r\n", 6)

    ab.append(b"\x1b[0K", 4)
    msglen = len(E.statusmsg)
    if msglen and time.time() - E.statusmsg_time < 5:
        display_msg = E.statusmsg[:min(msglen, E.screencols)]
        ab.append(display_msg, len(display_msg))

    cx = 1
    filerow = E.rowoff + E.cy
    row = E.row[filerow] if filerow < E.numrows else None
    if row:
        for j in range(E.coloff, E.cx + E.coloff):
            if j < row.size and row.chars[j] == TAB:
                cx += 7 - ((cx - 1) % 8)
            cx += 1
    buf = "\x1b[{};{}H".format(E.cy + 1, cx)
    ab.append(buf, len(buf))
    ab.append(b"\x1b[?25h", 6)
    sys.stdout.buffer.write(bytes(ab.b))
    sys.stdout.buffer.flush()
    abuf_free(ab)


def editor_set_status_message(fmt, *args):
    global E
    E.statusmsg = fmt.format(*args) if args else fmt
    E.statusmsg_time = time.time()


# =============================== Find mode ================================

KILO_QUERY_LEN = 256


def editor_find(fd):
    global E
    query = bytearray()
    last_match = -1
    find_next = 0
    saved_hl_line = -1
    saved_hl = None

    saved_cx = E.cx
    saved_cy = E.cy
    saved_coloff = E.coloff
    saved_rowoff = E.rowoff

    def find_restore_hl():
        nonlocal saved_hl, saved_hl_line
        if saved_hl is not None and saved_hl_line != -1 and saved_hl_line < len(E.row):
            E.row[saved_hl_line].hl = saved_hl
            saved_hl = None
        saved_hl_line = -1

    while True:
        editor_set_status_message(
            "Search: {} (Use ESC/Arrows/Enter)".format(query.decode('ascii', errors='replace')))
        editor_refresh_screen()

        c = editor_read_key(fd)
        if c in (DEL_KEY, CTRL_H, BACKSPACE):
            if query:
                query.pop()
            last_match = -1
        elif c in (ESC, ENTER):
            if c == ESC:
                E.cx = saved_cx
                E.cy = saved_cy
                E.coloff = saved_coloff
                E.rowoff = saved_rowoff
            find_restore_hl()
            editor_set_status_message("")
            return
        elif c in (ARROW_RIGHT, ARROW_DOWN):
            find_next = 1
        elif c in (ARROW_LEFT, ARROW_UP):
            find_next = -1
        elif 32 <= c <= 126:
            if len(query) < KILO_QUERY_LEN:
                query.append(c)
                last_match = -1

        if last_match == -1:
            find_next = 1
        if find_next:
            match = None
            match_offset = 0
            current = last_match
            for i in range(E.numrows):
                current += find_next
                if current == -1:
                    current = E.numrows - 1
                elif current == E.numrows:
                    current = 0
                idx = E.row[current].render.find(bytes(query))
                if idx != -1:
                    match = current
                    match_offset = idx
                    break
            find_next = 0
            find_restore_hl()
            if match is not None:
                row_obj = E.row[match]
                last_match = match
                if row_obj.hl:
                    saved_hl_line = match
                    saved_hl = list(row_obj.hl)
                    for j in range(len(query)):
                        if match_offset + j < len(row_obj.hl):
                            row_obj.hl[match_offset + j] = HL_MATCH
                E.cy = 0
                E.cx = match_offset
                E.rowoff = match
                E.coloff = 0
                if E.cx > E.screencols:
                    diff = E.cx - E.screencols
                    E.cx -= diff
                    E.coloff += diff


# ========================= Editor events handling ========================


def editor_move_cursor(key):
    global E
    filerow = E.rowoff + E.cy
    filecol = E.coloff + E.cx
    row = E.row[filerow] if filerow < E.numrows else None

    if key == ARROW_LEFT:
        if E.cx == 0:
            if E.coloff:
                E.coloff -= 1
            else:
                if filerow > 0:
                    E.cy -= 1
                    E.cx = E.row[filerow - 1].size
                    if E.cx > E.screencols - 1:
                        E.coloff = E.cx - E.screencols + 1
                        E.cx = E.screencols - 1
        else:
            E.cx -= 1
    elif key == ARROW_RIGHT:
        if row is not None and filecol < row.size:
            if E.cx == E.screencols - 1:
                E.coloff += 1
            else:
                E.cx += 1
        elif row is not None and filecol == row.size:
            E.cx = 0
            E.coloff = 0
            if E.cy == E.screenrows - 1:
                E.rowoff += 1
            else:
                E.cy += 1
    elif key == ARROW_UP:
        if E.cy == 0:
            if E.rowoff:
                E.rowoff -= 1
        else:
            E.cy -= 1
    elif key == ARROW_DOWN:
        if filerow < E.numrows:
            if E.cy == E.screenrows - 1:
                E.rowoff += 1
            else:
                E.cy += 1

    filerow = E.rowoff + E.cy
    filecol = E.coloff + E.cx
    row = E.row[filerow] if filerow < E.numrows else None
    rowlen = row.size if row else 0
    if filecol > rowlen:
        E.cx -= filecol - rowlen
        if E.cx < 0:
            E.coloff += E.cx
            E.cx = 0


def editor_process_keypress(fd):
    global E
    c = editor_read_key(fd)
    if c == ENTER:
        editor_insert_newline()
    elif c == CTRL_C:
        pass
    elif c == CTRL_Q:
        if E.dirty and E.quit_times:
            editor_set_status_message(
                "WARNING!!! File has unsaved changes. "
                "Press Ctrl-Q {} more times to quit.".format(E.quit_times))
            E.quit_times -= 1
            return
        sys.exit(0)
    elif c == CTRL_S:
        editor_save()
    elif c == CTRL_F:
        editor_find(fd)
    elif c in (BACKSPACE, CTRL_H, DEL_KEY):
        editor_del_char()
    elif c in (PAGE_UP, PAGE_DOWN):
        if c == PAGE_UP and E.cy != 0:
            E.cy = 0
        elif c == PAGE_DOWN and E.cy != E.screenrows - 1:
            E.cy = E.screenrows - 1
        times = E.screenrows
        while times:
            editor_move_cursor(ARROW_UP if c == PAGE_UP else ARROW_DOWN)
            times -= 1
    elif c in (ARROW_UP, ARROW_DOWN, ARROW_LEFT, ARROW_RIGHT):
        editor_move_cursor(c)
    elif c == CTRL_L:
        pass
    elif c == ESC:
        pass
    else:
        editor_insert_char(c)
    E.quit_times = KILO_QUIT_TIMES


def editor_file_was_modified():
    return E.dirty


def update_window_size():
    global E
    ret, rows, cols = get_window_size(sys.stdin.fileno(), sys.stdout.fileno())
    if ret == -1:
        print("Unable to query the screen for size (columns / rows)", file=sys.stderr)
        sys.exit(1)
    E.screenrows = rows
    E.screencols = cols
    E.screenrows -= 2


def handle_sig_winch(signum, frame):
    update_window_size()
    if E.cy > E.screenrows:
        E.cy = E.screenrows - 1
    if E.cx > E.screencols:
        E.cx = E.screencols - 1
    editor_refresh_screen()


def init_editor():
    global E
    E.cx = 0
    E.cy = 0
    E.rowoff = 0
    E.coloff = 0
    E.numrows = 0
    E.row = []
    E.dirty = 0
    E.filename = None
    E.syntax = None
    update_window_size()
    if IS_WINDOWS:
        pass
    else:
        signal.signal(signal.SIGWINCH, handle_sig_winch)


def main():
    if len(sys.argv) != 2:
        print("Usage: kilo <filename>", file=sys.stderr)
        sys.exit(1)

    init_editor()
    editor_select_syntax_highlight(sys.argv[1])
    editor_open(sys.argv[1])
    enable_raw_mode(sys.stdin.fileno())
    editor_set_status_message(
        "HELP: Ctrl-S = save | Ctrl-Q = quit | Ctrl-F = find")
    try:
        while True:
            editor_refresh_screen()
            editor_process_keypress(sys.stdin.fileno())
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    main()
