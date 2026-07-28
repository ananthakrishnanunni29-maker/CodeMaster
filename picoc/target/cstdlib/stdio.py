import sys
import os
from interpreter import *
from expression import ExpressionModule
from cstdlib.memory import _get_string, _get_block

StdioDefs = "typedef struct __va_listStruct va_list; typedef struct __FILEStruct FILE;"


class StdioModule:
    @staticmethod
    def Setup(pc):
        from variable import VariableModule
        from type_sys import TypeModule
        import ctypes
        StructFileType = TypeModule.CreateOpaqueStruct(pc, None, "__FILEStruct", ctypes.sizeof(ctypes.c_void_p))
        FilePtrType = TypeModule.GetMatching(pc, None, StructFileType, BaseType.TypePointer, 0, pc.StrEmpty, True)
        TypeModule.CreateOpaqueStruct(pc, None, "__va_listStruct", ctypes.sizeof(ctypes.c_void_p))

        VariableModule.DefinePlatformVar(pc, None, "EOF", pc.IntType, -1, False)
        VariableModule.DefinePlatformVar(pc, None, "SEEK_SET", pc.IntType, 0, False)
        VariableModule.DefinePlatformVar(pc, None, "SEEK_CUR", pc.IntType, 1, False)
        VariableModule.DefinePlatformVar(pc, None, "SEEK_END", pc.IntType, 2, False)
        VariableModule.DefinePlatformVar(pc, None, "BUFSIZ", pc.IntType, 512, False)
        VariableModule.DefinePlatformVar(pc, None, "FILENAME_MAX", pc.IntType, 260, False)
        VariableModule.DefinePlatformVar(pc, None, "stdin", FilePtrType, id(sys.stdin), False)
        VariableModule.DefinePlatformVar(pc, None, "stdout", FilePtrType, id(sys.stdout), False)
        VariableModule.DefinePlatformVar(pc, None, "stderr", FilePtrType, id(sys.stderr), False)
        if not VariableModule.Defined(pc, "NULL"):
            VariableModule.DefinePlatformVar(pc, None, "NULL", pc.IntType, 0, False)

    @staticmethod
    def get_value_str(Val):
        if Val is None:
            return ""
        if Val.Typ is None:
            return ""
        bt = Val.Typ.Base
        if bt == BaseType.TypePointer and Val.Val is not None and Val.Val.Pointer is not None:
            return _get_string(Val.Val.Pointer)
        if bt == BaseType.TypeArray:
            if hasattr(Val.Val, 'Identifier'):
                return Val.Val.Identifier if Val.Val.Identifier else ""
            return ""
        if bt == BaseType.TypeChar:
            return chr(Val.Val.Character & 0xFF) if hasattr(Val.Val, 'Character') else ""
        s = ExpressionModule.CoerceInteger(Val)
        return str(s)

    @staticmethod
    def StdioBasePrintf(Parser, Stream, StrOut, StrOutLen, Format, Args):
        """Render the useful C printf subset, including flags and precision."""
        Format = Format or ""
        result, i, arg_idx = [], 0, 0
        conversion_chars = "diuoxXfFeEgGcspp"
        while i < len(Format):
            if Format[i] != '%':
                result.append(Format[i])
                i += 1
                continue
            start = i
            i += 1
            if i < len(Format) and Format[i] == '%':
                result.append('%')
                i += 1
                continue
            while i < len(Format) and Format[i] in '-+ #0':
                i += 1
            while i < len(Format) and Format[i].isdigit():
                i += 1
            if i < len(Format) and Format[i] == '.':
                i += 1
                while i < len(Format) and Format[i].isdigit():
                    i += 1
            while i < len(Format) and Format[i] in 'hlLzjt':
                i += 1
            if i >= len(Format) or Format[i] not in conversion_chars:
                result.append(Format[start:i])
                continue
            spec = Format[i]
            c_format = Format[start:i + 1]
            i += 1
            if arg_idx >= Args.NumArgs:
                result.append('XXX')
                continue
            value = Args.Param[arg_idx]
            arg_idx += 1
            if spec == 's':
                raw = StdioModule.get_value_str(value)
            elif spec == 'c':
                raw = ExpressionModule.CoerceInteger(value)
            elif spec in 'fFeEgG':
                raw = ExpressionModule.CoerceFP(value)
            elif spec in 'uoxX':
                raw = ExpressionModule.CoerceUnsignedInteger(value)
            elif spec == 'p':
                ptr = value.Val.Pointer if value.Val is not None and hasattr(value.Val, 'Pointer') else None
                result.append('(nil)' if not ptr else hex(ptr if isinstance(ptr, int) else id(ptr)))
                continue
            elif spec == 'n':
                continue
            else:
                raw = ExpressionModule.CoerceInteger(value)
            # Python's old-style formatter mirrors C's width, flag and precision
            # rules for the scalar conversions supported by picoc.
            try:
                result.append(c_format % raw)
            except (TypeError, ValueError):
                result.append(str(raw))
        output = ''.join(result)
        if Stream is not None:
            Stream.write(output)
        elif StrOut is not None:
            pass
        return len(output)


def StdioPrintf(Parser, ReturnValue, Param, NumArgs):
    class FakeArgs:
        pass
    Args = FakeArgs()
    Args.Param = Param[1:] if NumArgs > 1 else []
    Args.NumArgs = NumArgs - 1
    fmt = str(Param[0].Val.Pointer) if Param[0].Val and Param[0].Val.Pointer else ""
    count = StdioModule.StdioBasePrintf(Parser, sys.stdout, None, 0, fmt, Args)
    ReturnValue.Val.Integer = count

def _resolve_stream(ptr):
    if ptr == id(sys.stdin): return sys.stdin
    if ptr == id(sys.stdout): return sys.stdout
    if ptr == id(sys.stderr): return sys.stderr
    block = _get_block(ptr)
    return block if block is not None else sys.stdout

def StdioFprintf(Parser, ReturnValue, Param, NumArgs):
    stream_ptr = Param[0].Val.Pointer if Param[0].Val else None
    fmt = str(Param[1].Val.Pointer) if NumArgs > 1 and Param[1].Val and Param[1].Val.Pointer else ""
    class FakeArgs:
        pass
    Args = FakeArgs()
    Args.Param = Param[2:] if NumArgs > 2 else []
    Args.NumArgs = NumArgs - 2
    stream = _resolve_stream(stream_ptr)
    count = StdioModule.StdioBasePrintf(Parser, stream, None, 0, fmt, Args)
    ReturnValue.Val.Integer = count

def StdioScanf(Parser, ReturnValue, Param, NumArgs):
    if NumArgs < 1:
        ReturnValue.Val.Integer = -1
        return
    fmt = str(Param[0].Val.Pointer) if Param[0].Val and Param[0].Val.Pointer else ""
    items_read = 0
    i = 0
    arg_idx = 1
    while i < len(fmt):
        if fmt[i] in (' ', '\t', '\n'):
            i += 1
            ch = sys.stdin.read(1)
            while ch and ch in (' ', '\t', '\n'):
                ch = sys.stdin.read(1)
            if not ch:
                break
        elif fmt[i] == '%':
            i += 1
            if i >= len(fmt):
                break
            ch = fmt[i]
            if ch == '%':
                i += 1
                continue
            if arg_idx >= NumArgs:
                break
            dst = Param[arg_idx]
            if ch in ('d', 'i'):
                val_str = []
                c = sys.stdin.read(1)
                while c and c in (' ', '\t', '\n'):
                    c = sys.stdin.read(1)
                if c and (c in ('-', '+') or c.isdigit()):
                    val_str.append(c)
                    c = sys.stdin.read(1)
                    while c and c.isdigit():
                        val_str.append(c)
                        c = sys.stdin.read(1)
                if val_str:
                    val = int(''.join(val_str))
                    ExpressionModule.Assign(Parser, dst, None, False, None, 0, False)
                    if hasattr(dst.Val, 'Integer'):
                        dst.Val.Integer = val
                    items_read += 1
                arg_idx += 1
            elif ch in ('u', 'x', 'X', 'o'):
                val_str = []
                c = sys.stdin.read(1)
                while c and c in (' ', '\t', '\n'):
                    c = sys.stdin.read(1)
                while c and (c.isdigit() or c in ('a','b','c','d','e','f','A','B','C','D','E','F','x','X')):
                    val_str.append(c)
                    c = sys.stdin.read(1)
                if val_str:
                    base = 16 if ch in ('x','X') else 8 if ch == 'o' else 10
                    val = int(''.join(val_str), base)
                    ExpressionModule.Assign(Parser, dst, None, False, None, 0, False)
                    if hasattr(dst.Val, 'UnsignedInteger'):
                        dst.Val.UnsignedInteger = val
                    items_read += 1
                arg_idx += 1
            elif ch in ('f', 'e', 'g', 'E', 'G'):
                val_str = []
                c = sys.stdin.read(1)
                while c and c in (' ', '\t', '\n'):
                    c = sys.stdin.read(1)
                if c and (c in ('-','+') or c.isdigit() or c == '.'):
                    val_str.append(c)
                    c = sys.stdin.read(1)
                    while c and (c.isdigit() or c in ('.','e','E','-','+')):
                        val_str.append(c)
                        c = sys.stdin.read(1)
                if val_str:
                    val = float(''.join(val_str))
                    ExpressionModule.Assign(Parser, dst, None, False, None, 0, False)
                    if hasattr(dst.Val, 'FP'):
                        dst.Val.FP = val
                    items_read += 1
                arg_idx += 1
            elif ch == 'c':
                c = sys.stdin.read(1)
                if c:
                    ExpressionModule.Assign(Parser, dst, None, False, None, 0, False)
                    if hasattr(dst.Val, 'Character'):
                        dst.Val.Character = ord(c)
                    items_read += 1
                arg_idx += 1
            elif ch == 's':
                val_str = []
                c = sys.stdin.read(1)
                while c and c in (' ', '\t', '\n'):
                    c = sys.stdin.read(1)
                while c and c not in (' ', '\t', '\n'):
                    val_str.append(c)
                    c = sys.stdin.read(1)
                if val_str:
                    s = ''.join(val_str)
                    block = _get_block(dst.Val.Pointer)
                    if block:
                        block[:len(s)] = s.encode('latin-1', errors='replace')
                    items_read += 1
                arg_idx += 1
            i += 1
        else:
            i += 1
    ReturnValue.Val.Integer = items_read

def StdioSprintf(Parser, ReturnValue, Param, NumArgs):
    fmt = str(Param[1].Val.Pointer) if NumArgs > 1 and Param[1].Val and Param[1].Val.Pointer else ""
    class FakeArgs:
        pass
    Args = FakeArgs()
    Args.Param = Param[2:] if NumArgs > 2 else []
    Args.NumArgs = NumArgs - 2
    count = StdioModule.StdioBasePrintf(Parser, None, None, 0, fmt, Args)
    ReturnValue.Val.Integer = count

def StdioPutchar(Parser, ReturnValue, Param, NumArgs):
    ch = Param[0].Val.Integer & 0xFF
    sys.stdout.write(chr(ch))
    sys.stdout.flush()
    ReturnValue.Val.Integer = ch

def StdioPuts(Parser, ReturnValue, Param, NumArgs):
    s = str(Param[0].Val.Pointer) if Param[0].Val and Param[0].Val.Pointer else ""
    sys.stdout.write(s)
    sys.stdout.write('\n')
    ReturnValue.Val.Integer = len(s) + 1

def StdioGetchar(Parser, ReturnValue, Param, NumArgs):
    try:
        ch = sys.stdin.read(1)
        if ch:
            ReturnValue.Val.Integer = ord(ch)
        else:
            ReturnValue.Val.Integer = -1
    except EOFError:
        ReturnValue.Val.Integer = -1

_open_files = {}

def StdioFopen(Parser, ReturnValue, Param, NumArgs):
    filename = str(Param[0].Val.Pointer) if Param[0].Val and Param[0].Val.Pointer else ""
    mode = str(Param[1].Val.Pointer) if Param[1].Val and Param[1].Val.Pointer else ""
    if filename:
        f = open(filename, mode)
        fid = id(f)
        _open_files[fid] = f
        ReturnValue.Val.Pointer = fid
    else:
        ReturnValue.Val.Pointer = None

def StdioFclose(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = 0

def StdioFgetc(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = -1

def StdioFeof(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = 0

def StdioFflush(Parser, ReturnValue, Param, NumArgs):
    sys.stdout.flush()
    ReturnValue.Val.Integer = 0

def StdioRewind(Parser, ReturnValue, Param, NumArgs):
    pass

StdioFunctions = [
    LibraryFunction(StdioFopen, "FILE *fopen(char *, char *);"),
    LibraryFunction(StdioFclose, "int fclose(FILE *);"),
    LibraryFunction(StdioFgetc, "int fgetc(FILE *);"),
    LibraryFunction(StdioFgetc, "int getc(FILE *);"),
    LibraryFunction(StdioFeof, "int feof(FILE *);"),
    LibraryFunction(StdioFflush, "int fflush(FILE *);"),
    LibraryFunction(StdioRewind, "void rewind(FILE *);"),
    LibraryFunction(StdioPutchar, "int putchar(int);"),
    LibraryFunction(StdioPutchar, "int fputchar(int);"),
    LibraryFunction(StdioPuts, "int puts(char *);"),
    LibraryFunction(StdioGetchar, "int getchar();"),
    LibraryFunction(StdioPrintf, "int printf(char *, ...);"),
    LibraryFunction(StdioFprintf, "int fprintf(FILE *, char *, ...);"),
    LibraryFunction(StdioSprintf, "int sprintf(char *, char *, ...);"),
    LibraryFunction(StdioScanf, "int scanf(char *, ...);"),
    LibraryFunction(StdioScanf, "int fscanf(FILE *, char *, ...);"),
    LibraryFunction(StdioScanf, "int sscanf(char *, char *, ...);"),
]
