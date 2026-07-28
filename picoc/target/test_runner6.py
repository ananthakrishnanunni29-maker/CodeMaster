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
from include_module import IncludeModule
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
    # Parse code with inline #include
    code = '#include <stdio.h>\nint main() { printf("hello\\n"); return 0; }'
    print("Parsing code with include...", flush=True)
    ParseModule.PicocParse(pc, 'test', code, len(code), True, True, False, False)
    print("Parse OK", flush=True)
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
