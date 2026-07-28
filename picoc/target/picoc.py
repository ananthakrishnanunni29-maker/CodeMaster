import sys
import os

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

PICOC_STACK_SIZE = 128000 * 4


def PicocInitialize(pc, StackSize):
    pc.CStdOut = sys.stdout
    HeapModule.Init(pc, StackSize)
    TableModule.Init(pc)
    VariableModule.Init(pc)
    LexModule.Init(pc)
    TypeModule.Init(pc)
    IncludeModule.Init(pc)
    CLibraryModule.LibraryInit(pc)
    PlatformModule.PlatformLibraryInit(pc)
    DebugModule.Init(pc)


def PicocCleanup(pc):
    DebugModule.Cleanup(pc)
    IncludeModule.Cleanup(pc)
    ParseModule.Cleanup(pc)
    LexModule.Cleanup(pc)
    VariableModule.Cleanup(pc)
    TypeModule.Cleanup(pc)
    TableModule.StrFree(pc)
    HeapModule.Cleanup(pc)
    PlatformModule.Cleanup(pc)


def PicocCallMain(pc, argc, argv):
    if not VariableModule.Defined(pc, "main"):
        from platform_module import PlatformModule
        PlatformModule.ProgramFailNoParser(pc, "main() is not defined")

    FuncValue = VariableModule.Get(pc, None, "main")
    if FuncValue.Typ.Base != BaseType.TypeFunction:
        from platform_module import PlatformModule
        PlatformModule.ProgramFailNoParser(pc, "main is not a function - can't call it")

    if FuncValue.Val.FuncDef.NumParams != 0:
        VariableModule.DefinePlatformVar(pc, None, "__argc", pc.IntType, argc, False)
        VariableModule.DefinePlatformVar(pc, None, "__argv", pc.CharPtrPtrType, argv, False)

    if FuncValue.Val.FuncDef.ReturnType is pc.VoidType:
        if FuncValue.Val.FuncDef.NumParams == 0:
            ParseModule.PicocParse(pc, "startup", "main();", 7, True, True, False, False)
        else:
            ParseModule.PicocParse(pc, "startup", "main(__argc,__argv);", 21, True, True, False, False)
    else:
        VariableModule.DefinePlatformVar(pc, None, "__exit_value", pc.IntType, pc.PicocExitValue, True)
        if FuncValue.Val.FuncDef.NumParams == 0:
            ParseModule.PicocParse(pc, "startup", "__exit_value = main();", 22, True, True, False, False)
        else:
            ParseModule.PicocParse(pc, "startup", "__exit_value = main(__argc,__argv);", 36, True, True, False, False)


def PicocIncludeAllSystemHeaders(pc):
    IncludeModule.IncludeAllSystemHeaders(pc)


def PicocPlatformScanFile(pc, FileName):
    PlatformModule.ScanFile(pc, FileName)


def main():
    if len(sys.argv) < 2 or sys.argv[1] == '-h':
        print("picoc v2.3.2")
        print("Format:")
        print("> picoc <file1.c>... [- <arg1>...]    : run a program, calls main() as the entry point")
        print("> picoc -s <file1.c>... [- <arg1>...] : run a script, runs the program without calling main()")
        print("> picoc -i                            : interactive mode, Ctrl+d to exit")
        print("> picoc -c                            : copyright info")
        print("> picoc -h                            : this help message")
        return 0

    if sys.argv[1] == '-c':
        print("picoc - Copyright (c) 2009-2011, Zik Saleba")
        return 0

    StackSizeEnv = os.environ.get('STACKSIZE')
    if StackSizeEnv is not None:
        try:
            StackSize = int(StackSizeEnv)
        except ValueError:
            StackSize = PICOC_STACK_SIZE
    else:
        StackSize = PICOC_STACK_SIZE

    pc = Picoc()
    PicocInitialize(pc, StackSize)

    ParamCount = 1
    DontRunMain = False

    if sys.argv[ParamCount] == '-s':
        DontRunMain = True
        PicocIncludeAllSystemHeaders(pc)
        ParamCount += 1

    if len(sys.argv) > ParamCount and sys.argv[ParamCount] == '-i':
        PicocIncludeAllSystemHeaders(pc)
        ParseModule.PicocParseInteractive(pc)
    else:
        try:
            while ParamCount < len(sys.argv) and sys.argv[ParamCount] != '-':
                PicocPlatformScanFile(pc, sys.argv[ParamCount])
                ParamCount += 1

            if not DontRunMain:
                PicocCallMain(pc, len(sys.argv) - ParamCount, sys.argv[ParamCount:] if ParamCount < len(sys.argv) else [])
        except SystemExit as e:
            PicocCleanup(pc)
            return e.code if e.code is not None else 0

    PicocCleanup(pc)
    return pc.PicocExitValue


if __name__ == '__main__':
    sys.exit(main())
