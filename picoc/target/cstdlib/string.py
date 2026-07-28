import ctypes
from interpreter import *
from expression import ExpressionModule
from cstdlib.memory import _get_string, _get_block

class StringModule:
    @staticmethod
    def Setup(pc):
        pass

def StringStrcpy(Parser, ReturnValue, Param, NumArgs):
    dst_ptr = Param[0].Val.Pointer
    src = _get_string(Param[1].Val.Pointer)
    if dst_ptr is not None:
        block = _get_block(dst_ptr)
        if block is not None:
            data = (src + '\x00').encode('latin-1', errors='replace')
            block[:len(data)] = data
    ReturnValue.Val.Pointer = dst_ptr

def StringStrncpy(Parser, ReturnValue, Param, NumArgs):
    dst_ptr = Param[0].Val.Pointer
    src = _get_string(Param[1].Val.Pointer)
    n = max(0, Param[2].Val.Integer)
    if dst_ptr is not None:
        block = _get_block(dst_ptr)
        if block is not None:
            truncated = src[:n]
            data = truncated.encode('latin-1', errors='replace')
            if len(data) < n:
                data = data + b'\x00' * (n - len(data))
            block[:len(data)] = data
    ReturnValue.Val.Pointer = dst_ptr

def StringStrcat(Parser, ReturnValue, Param, NumArgs):
    dst_ptr = Param[0].Val.Pointer
    src = _get_string(Param[1].Val.Pointer)
    if dst_ptr is not None:
        block = _get_block(dst_ptr)
        if block is not None:
            cur = _get_string(dst_ptr)
            new_str = cur + src + '\x00'
            data = new_str.encode('latin-1', errors='replace')
            block[:len(data)] = data
    ReturnValue.Val.Pointer = dst_ptr

def StringStrncat(Parser, ReturnValue, Param, NumArgs):
    dst_ptr = Param[0].Val.Pointer
    src = _get_string(Param[1].Val.Pointer)
    n = max(0, Param[2].Val.Integer)
    if dst_ptr is not None:
        block = _get_block(dst_ptr)
        if block is not None:
            cur = _get_string(dst_ptr)
            new_str = cur + src[:n] + '\x00'
            data = new_str.encode('latin-1', errors='replace')
            block[:len(data)] = data
    ReturnValue.Val.Pointer = dst_ptr

def StringStrlen(Parser, ReturnValue, Param, NumArgs):
    s = _get_string(Param[0].Val.Pointer)
    ReturnValue.Val.Integer = len(s)

def StringStrcmp(Parser, ReturnValue, Param, NumArgs):
    s1 = _get_string(Param[0].Val.Pointer)
    s2 = _get_string(Param[1].Val.Pointer)
    if s1 < s2:
        ReturnValue.Val.Integer = -1
    elif s1 > s2:
        ReturnValue.Val.Integer = 1
    else:
        ReturnValue.Val.Integer = 0

def StringStrncmp(Parser, ReturnValue, Param, NumArgs):
    s1 = _get_string(Param[0].Val.Pointer)
    s2 = _get_string(Param[1].Val.Pointer)
    n = max(0, Param[2].Val.Integer)
    s1 = s1[:n]
    s2 = s2[:n]
    if s1 < s2:
        ReturnValue.Val.Integer = -1
    elif s1 > s2:
        ReturnValue.Val.Integer = 1
    else:
        ReturnValue.Val.Integer = 0

def StringStrchr(Parser, ReturnValue, Param, NumArgs):
    s = _get_string(Param[0].Val.Pointer)
    c = chr(Param[1].Val.Integer & 0xFF)
    idx = s.find(c)
    if idx >= 0:
        ReturnValue.Val.Pointer = id(Param[0].Val) + idx
    else:
        ReturnValue.Val.Pointer = None

def StringStrrchr(Parser, ReturnValue, Param, NumArgs):
    s = _get_string(Param[0].Val.Pointer)
    c = chr(Param[1].Val.Integer & 0xFF)
    idx = s.rfind(c)
    if idx >= 0:
        ReturnValue.Val.Pointer = id(Param[0].Val) + idx
    else:
        ReturnValue.Val.Pointer = None

def StringStrstr(Parser, ReturnValue, Param, NumArgs):
    s1 = _get_string(Param[0].Val.Pointer)
    s2 = _get_string(Param[1].Val.Pointer)
    idx = s1.find(s2)
    if idx >= 0:
        ReturnValue.Val.Pointer = id(Param[0].Val) + idx
    else:
        ReturnValue.Val.Pointer = None

def StringMemcpy(Parser, ReturnValue, Param, NumArgs):
    dst_ptr = Param[0].Val.Pointer
    src_ptr = Param[1].Val.Pointer
    n = max(0, Param[2].Val.Integer)
    if dst_ptr is not None and src_ptr is not None:
        src_block = _get_block(src_ptr)
        dst_block = _get_block(dst_ptr)
        if src_block is not None and dst_block is not None:
            dst_block[:n] = src_block[:n]
    ReturnValue.Val.Pointer = dst_ptr

def StringMemmove(Parser, ReturnValue, Param, NumArgs):
    dst_ptr = Param[0].Val.Pointer
    src_ptr = Param[1].Val.Pointer
    n = max(0, Param[2].Val.Integer)
    if dst_ptr is not None and src_ptr is not None:
        src_block = _get_block(src_ptr)
        dst_block = _get_block(dst_ptr)
        if src_block is not None and dst_block is not None:
            dst_block[:n] = src_block[:n]
    ReturnValue.Val.Pointer = dst_ptr

def StringMemset(Parser, ReturnValue, Param, NumArgs):
    dst_ptr = Param[0].Val.Pointer
    val = Param[1].Val.Integer & 0xFF
    n = max(0, Param[2].Val.Integer)
    if dst_ptr is not None:
        block = _get_block(dst_ptr)
        if block is not None:
            block[:n] = bytes([val] * n)
    ReturnValue.Val.Pointer = dst_ptr

def StringMemcmp(Parser, ReturnValue, Param, NumArgs):
    s1_block = _get_block(Param[0].Val.Pointer)
    s2_block = _get_block(Param[1].Val.Pointer)
    n = max(0, Param[2].Val.Integer)
    if s1_block is None or s2_block is None:
        ReturnValue.Val.Integer = -1 if s1_block is None else 1
    else:
        b1 = s1_block[:n]
        b2 = s2_block[:n]
        if b1 < b2:
            ReturnValue.Val.Integer = -1
        elif b1 > b2:
            ReturnValue.Val.Integer = 1
        else:
            ReturnValue.Val.Integer = 0

StringFunctions = [
    LibraryFunction(StringStrcpy, "char *strcpy(char *, char *);"),
    LibraryFunction(StringStrncpy, "char *strncpy(char *, char *, int);"),
    LibraryFunction(StringStrcat, "char *strcat(char *, char *);"),
    LibraryFunction(StringStrncat, "char *strncat(char *, char *, int);"),
    LibraryFunction(StringStrlen, "int strlen(char *);"),
    LibraryFunction(StringStrcmp, "int strcmp(char *, char *);"),
    LibraryFunction(StringStrncmp, "int strncmp(char *, char *, int);"),
    LibraryFunction(StringStrchr, "char *strchr(char *, int);"),
    LibraryFunction(StringStrrchr, "char *strrchr(char *, int);"),
    LibraryFunction(StringStrstr, "char *strstr(char *, char *);"),
    LibraryFunction(StringMemcpy, "void *memcpy(void *, void *, int);"),
    LibraryFunction(StringMemmove, "void *memmove(void *, void *, int);"),
    LibraryFunction(StringMemset, "void *memset(void *, int, int);"),
    LibraryFunction(StringMemcmp, "int memcmp(void *, void *, int);"),
]