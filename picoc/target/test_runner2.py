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

print("Initialized OK")

try:
    code = 'int x;'
    ParseModule.PicocParse(pc, 'test', code, len(code), True, True, False, False)
    print('Parse1 OK')
    code = 'x = 42;'
    ParseModule.PicocParse(pc, 'test', code, len(code), True, True, False, False)
    print('Parse2 OK')
    code2 = 'int main() { return x; }'
    ParseModule.PicocParse(pc, 'test', code2, len(code2), True, True, False, False)
    print('Parse3 OK - function defined')
except Exception as e:
    import traceback
    traceback.print_exc()
