import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from interpreter import *
from table import TableModule
from heap import HeapModule
from variable import VariableModule
from lex import LexModule
from type_sys import TypeModule
from platform_module import PlatformModule
from clibrary import CLibraryModule
from include_module import IncludeModule, IncludeFile
from debug import DebugModule
from parse import ParseModule

pc = Picoc()
HeapModule.Init(pc, 128000 * 4)
TableModule.Init(pc)
VariableModule.Init(pc)
LexModule.Init(pc)
TypeModule.Init(pc)
IncludeModule.Init(pc)
CLibraryModule.LibraryInit(pc)
PlatformModule.PlatformLibraryInit(pc)
DebugModule.Init(pc)

print("Initialized OK", flush=True)

try:
    # Lex the source that has #include
    src = '#include <stdio.h>\nint x;'
    print(f"Lexing: {repr(src)}", flush=True)
    RegFileName = TableModule.StrRegister(pc, "test")
    tokens = LexModule.LexAnalyze(pc, RegFileName, src, len(src), None)
    print(f"Got {len(tokens)} tokens", flush=True)
    for i, t in enumerate(tokens):
        print(f"  Token {i}: type={t[0]}, val={t[2] if len(t) > 2 else None}", flush=True)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    DebugModule.Cleanup(pc)
    IncludeModule.Cleanup(pc)
    ParseModule.Cleanup(pc)
    LexModule.Cleanup(pc)
    VariableModule.Cleanup(pc)
    TypeModule.Cleanup(pc)
    TableModule.StrFree(pc)
    HeapModule.Cleanup(pc)
    PlatformModule.Cleanup(pc)
