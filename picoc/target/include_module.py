from interpreter import *
from table import TableModule
from variable import VariableModule
from parse import ParseModule
from lex import LexModule
from type_sys import TypeModule


class IncludeModule:
    @staticmethod
    def Init(pc):
        from cstdlib.ctype import StdCtypeFunctions, CTypeModule
        from cstdlib.errno import ErrnoModule
        from cstdlib.math import MathModule, MathFunctions
        from cstdlib.stdbool import StdboolModule, StdboolDefs
        from cstdlib.stdio import StdioModule, StdioFunctions, StdioDefs
        from cstdlib.stdlib import StdlibModule, StdlibFunctions
        from cstdlib.string import StringFunctions
        from cstdlib.time import StdTimeModule, StdTimeFunctions, StdTimeDefs
        from cstdlib.unistd import UnistdModule, UnistdFunctions, UnistdDefs

        IncludeModule.Register(pc, "ctype.h", CTypeModule.Setup if hasattr(CTypeModule, 'Setup') else None, StdCtypeFunctions, None)
        IncludeModule.Register(pc, "errno.h", ErrnoModule.Setup if hasattr(ErrnoModule, 'Setup') else None, None, None)
        IncludeModule.Register(pc, "math.h", MathModule.Setup if hasattr(MathModule, 'Setup') else None, MathFunctions if 'MathFunctions' in dir() else None, None)
        IncludeModule.Register(pc, "stdbool.h", StdboolModule.Setup if hasattr(StdboolModule, 'Setup') else None, None, StdboolDefs)
        IncludeModule.Register(pc, "stdio.h", StdioModule.Setup if hasattr(StdioModule, 'Setup') else None, StdioFunctions, StdioDefs)
        IncludeModule.Register(pc, "stdlib.h", StdlibModule.Setup if hasattr(StdlibModule, 'Setup') else None, StdlibFunctions, None)
        IncludeModule.Register(pc, "string.h", None, StringFunctions, None)
        IncludeModule.Register(pc, "time.h", StdTimeModule.Setup if hasattr(StdTimeModule, 'Setup') else None, StdTimeFunctions, StdTimeDefs)
        IncludeModule.Register(pc, "unistd.h", UnistdModule.Setup if hasattr(UnistdModule, 'Setup') else None, UnistdFunctions, UnistdDefs)

    @staticmethod
    def Cleanup(pc):
        pc.IncludeLibList = None

    @staticmethod
    def Register(pc, IncludeName, SetupFunction, FuncList, SetupCSource):
        NewLib = IncludeLibrary()
        NewLib.IncludeName = TableModule.StrRegister(pc, IncludeName)
        NewLib.SetupFunction = SetupFunction
        NewLib.FuncList = FuncList
        NewLib.SetupCSource = SetupCSource
        NewLib.NextLib = pc.IncludeLibList
        pc.IncludeLibList = NewLib

    @staticmethod
    def IncludeAllSystemHeaders(pc):
        ThisInclude = pc.IncludeLibList
        while ThisInclude is not None:
            IncludeFile(pc, ThisInclude.IncludeName)
            ThisInclude = ThisInclude.NextLib


def IncludeFile(pc, Filename):
    from platform_module import PlatformModule
    from clibrary import CLibraryModule
    LibItem = pc.IncludeLibList
    while LibItem is not None:
        if LibItem.IncludeName == Filename:
            if not VariableModule.Defined(pc, Filename):
                VariableModule.DefinePlatformVar(pc, None, Filename, pc.VoidType, 0, False)
                if LibItem.SetupFunction is not None:
                    LibItem.SetupFunction(pc)
                if LibItem.SetupCSource is not None:
                    ParseModule.PicocParse(pc, Filename, LibItem.SetupCSource, len(LibItem.SetupCSource), True, True, False, False)
                if LibItem.FuncList is not None:
                    CLibraryModule.LibraryAdd(pc, LibItem.FuncList)
            return
        LibItem = LibItem.NextLib
    PlatformModule.ScanFile(pc, Filename)
