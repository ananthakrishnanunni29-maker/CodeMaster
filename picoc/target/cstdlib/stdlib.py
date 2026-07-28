import random
import ctypes
from interpreter import *
from expression import ExpressionModule
from variable import VariableModule
from cstdlib.memory import _get_block as _get_block, _put_block, _del_block as _del_block, _get_string as _get_string


def _store_block(Data):
    block_id = id(Data)
    _put_block(block_id, Data)
    return block_id


class StdlibModule:
    @staticmethod
    def Setup(pc):
        VariableModule.DefinePlatformVar(pc, None, "EXIT_SUCCESS", pc.IntType, 0, False)
        VariableModule.DefinePlatformVar(pc, None, "EXIT_FAILURE", pc.IntType, 1, False)
        VariableModule.DefinePlatformVar(pc, None, "RAND_MAX", pc.IntType, 32767, False)
        if not VariableModule.Defined(pc, "NULL"):
            VariableModule.DefinePlatformVar(pc, None, "NULL", pc.IntType, 0, False)


def StdlibMalloc(Parser, ReturnValue, Param, NumArgs):
    Size = max(0, Param[0].Val.Integer)
    Data = bytearray(Size)
    ReturnValue.Val.Pointer = _store_block(Data)

def StdlibFree(Parser, ReturnValue, Param, NumArgs):
    ptr = Param[0].Val.Pointer
    if isinstance(ptr, int):
        _del_block(ptr)

def StdlibCalloc(Parser, ReturnValue, Param, NumArgs):
    nmemb = max(0, Param[0].Val.Integer)
    size = max(0, Param[1].Val.Integer)
    Data = bytearray(nmemb * size)
    ReturnValue.Val.Pointer = _store_block(Data)

def StdlibRealloc(Parser, ReturnValue, Param, NumArgs):
    size = max(0, Param[1].Val.Integer)
    Data = bytearray(size)
    ReturnValue.Val.Pointer = _store_block(Data)

def StdlibAtoi(Parser, ReturnValue, Param, NumArgs):
    s = _get_string(Param[0].Val.Pointer)
    if s is None:
        ReturnValue.Val.Integer = 0
    else:
        try:
            ReturnValue.Val.Integer = int(s)
        except ValueError:
            ReturnValue.Val.Integer = 0

def StdlibAtol(Parser, ReturnValue, Param, NumArgs):
    s = _get_string(Param[0].Val.Pointer)
    if s is None:
        ReturnValue.Val.LongInteger = 0
    else:
        try:
            ReturnValue.Val.LongInteger = int(s)
        except ValueError:
            ReturnValue.Val.LongInteger = 0

def StdlibAtod(Parser, ReturnValue, Param, NumArgs):
    s = _get_string(Param[0].Val.Pointer)
    if s is None:
        ReturnValue.Val.FP = 0.0
    else:
        try:
            ReturnValue.Val.FP = float(s)
        except ValueError:
            ReturnValue.Val.FP = 0.0

def StdlibAtof(Parser, ReturnValue, Param, NumArgs):
    StdlibAtod(Parser, ReturnValue, Param, NumArgs)

def StdlibStrtof(Parser, ReturnValue, Param, NumArgs):
    s = _get_string(Param[0].Val.Pointer)
    if s is None:
        ReturnValue.Val.FP = 0.0
    else:
        try:
            ReturnValue.Val.FP = float(s)
        except ValueError:
            ReturnValue.Val.FP = 0.0

def StdlibStrtoi(Parser, ReturnValue, Param, NumArgs):
    s = _get_string(Param[0].Val.Pointer)
    if s is None:
        ReturnValue.Val.Integer = 0
    else:
        try:
            ReturnValue.Val.Integer = int(s)
        except ValueError:
            ReturnValue.Val.Integer = 0

def StdlibAbs(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = abs(Param[0].Val.Integer)

def StdlibLabs(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.LongInteger = abs(Param[0].Val.LongInteger)

def StdlibRand(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = random.randint(0, 32767)

def StdlibSrand(Parser, ReturnValue, Param, NumArgs):
    random.seed(Param[0].Val.Integer)

def StdlibExit(Parser, ReturnValue, Param, NumArgs):
    from platform_module import PlatformModule
    PlatformModule.Exit(Parser.pc, Param[0].Val.Integer)

def StdlibAbort(Parser, ReturnValue, Param, NumArgs):
    from platform_module import PlatformModule
    PlatformModule.Exit(Parser.pc, 1)

def StdlibSystem(Parser, ReturnValue, Param, NumArgs):
    cmd = _get_string(Param[0].Val.Pointer) if Param[0].Val is not None else None
    if cmd is None or not cmd:
        ReturnValue.Val.Integer = 1
    else:
        import subprocess
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True)
            ReturnValue.Val.Integer = result.returncode
        except Exception:
            ReturnValue.Val.Integer = -1

def StdlibQsort(Parser, ReturnValue, Param, NumArgs):
    pass

def StdlibBsearch(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Pointer = None

StdlibFunctions = [
    LibraryFunction(StdlibMalloc, "void *malloc(int);"),
    LibraryFunction(StdlibFree, "void free(void *);"),
    LibraryFunction(StdlibCalloc, "void *calloc(int, int);"),
    LibraryFunction(StdlibRealloc, "void *realloc(void *, int);"),
    LibraryFunction(StdlibAtoi, "int atoi(char *);"),
    LibraryFunction(StdlibAtol, "long atol(char *);"),
    LibraryFunction(StdlibAtod, "double atof(char *);"),
    LibraryFunction(StdlibAbs, "int abs(int);"),
    LibraryFunction(StdlibLabs, "long labs(long);"),
    LibraryFunction(StdlibRand, "int rand();"),
    LibraryFunction(StdlibSrand, "void srand(int);"),
    LibraryFunction(StdlibExit, "void exit(int);"),
    LibraryFunction(StdlibAbort, "void abort();"),
    LibraryFunction(StdlibSystem, "int system(char *);"),
    LibraryFunction(StdlibQsort, "void qsort(void *, int, int, void *);"),
    LibraryFunction(StdlibBsearch, "void *bsearch(void *, void *, int, int, void *);"),
]
