from interpreter import *
from table import TableModule
from lex import LexModule
from type_sys import TypeModule
from variable import VariableModule
from parse import ParseModule


class CLibraryModule:
    @staticmethod
    def BasicIOInit(pc):
        import sys
        pc.CStdOut = sys.stdout

    @staticmethod
    def PrintCh(OutCh, Stream):
        Stream.write(chr(OutCh & 0xFF))

    @staticmethod
    def PrintSimpleInt(Num, Stream):
        Stream.write(str(Num))

    @staticmethod
    def PrintInt(Num, FieldWidth, ZeroPad, LeftJustify, Stream):
        fmt = "%"
        if ZeroPad:
            fmt += "0"
        if FieldWidth > 0:
            fmt += str(FieldWidth)
        if LeftJustify:
            fmt = "%-" + str(FieldWidth) if FieldWidth > 0 else "%-"
        fmt += "d"
        Stream.write(fmt % Num)

    @staticmethod
    def PrintStr(Str, Stream):
        if Str is not None:
            Stream.write(Str)

    @staticmethod
    def PrintFP(Num, Stream):
        Stream.write(str(Num))

    @staticmethod
    def PrintType(Typ, Stream):
        if Typ is None:
            return
        if Typ.Base == BaseType.TypeVoid:
            Stream.write("void")
        elif Typ.Base == BaseType.TypeInt:
            Stream.write("int")
        elif Typ.Base == BaseType.TypeShort:
            Stream.write("short")
        elif Typ.Base == BaseType.TypeChar:
            Stream.write("char")
        elif Typ.Base == BaseType.TypeLong:
            Stream.write("long")
        elif Typ.Base == BaseType.TypeUnsignedInt:
            Stream.write("unsigned int")
        elif Typ.Base == BaseType.TypeUnsignedShort:
            Stream.write("unsigned short")
        elif Typ.Base == BaseType.TypeUnsignedLong:
            Stream.write("unsigned long")
        elif Typ.Base == BaseType.TypeUnsignedChar:
            Stream.write("unsigned char")
        elif Typ.Base == BaseType.TypeFP:
            Stream.write("double")
        elif Typ.Base == BaseType.TypeFunction:
            Stream.write("function")
        elif Typ.Base == BaseType.TypeMacro:
            Stream.write("macro")
        elif Typ.Base == BaseType.TypePointer:
            if Typ.FromType:
                CLibraryModule.PrintType(Typ.FromType, Stream)
            Stream.write("*")
        elif Typ.Base == BaseType.TypeArray:
            CLibraryModule.PrintType(Typ.FromType, Stream)
            Stream.write("[")
            if Typ.ArraySize != 0:
                Stream.write(str(Typ.ArraySize))
            Stream.write("]")
        elif Typ.Base == BaseType.TypeStruct:
            Stream.write("struct ")
            Stream.write(Typ.Identifier if Typ.Identifier else "")
        elif Typ.Base == BaseType.TypeUnion:
            Stream.write("union ")
            Stream.write(Typ.Identifier if Typ.Identifier else "")
        elif Typ.Base == BaseType.TypeEnum:
            Stream.write("enum ")
            Stream.write(Typ.Identifier if Typ.Identifier else "")
        elif Typ.Base == BaseType.TypeGotoLabel:
            Stream.write("goto label ")
        elif Typ.Base == BaseType.Type_Type:
            Stream.write("type ")

    @staticmethod
    def LibraryInit(pc):
        pc.VersionString = TableModule.StrRegister(pc, "picoc v2.3.2")
        VariableModule.DefinePlatformVar(pc, None, "PICOC_VERSION", pc.CharPtrType, pc.VersionString, False)

        import sys
        BigEndian = sys.byteorder == 'big'
        LittleEndian = sys.byteorder == 'little'
        VariableModule.DefinePlatformVar(pc, None, "BIG_ENDIAN", pc.IntType, 1 if BigEndian else 0, False)
        VariableModule.DefinePlatformVar(pc, None, "LITTLE_ENDIAN", pc.IntType, 1 if LittleEndian else 0, False)

    @staticmethod
    def LibraryAdd(pc, FuncList):
        IntrinsicName = TableModule.StrRegister(pc, "c library")
        for FuncEntry in FuncList:
            if FuncEntry.Prototype is None:
                break
            Tokens = LexModule.LexAnalyze(pc, IntrinsicName, FuncEntry.Prototype, len(FuncEntry.Prototype), None)
            Parser = ParseState()
            LexModule.LexInitParser(Parser, pc, FuncEntry.Prototype, Tokens, IntrinsicName, True, False)
            ReturnType = [None]
            Identifier = [""]
            TypeModule.Parse(Parser, ReturnType, Identifier, None)
            NewValue = ParseModule.ParseFunctionDefinition(Parser, ReturnType[0], Identifier[0])
            NewValue.Val.FuncDef.Intrinsic = FuncEntry.Func

    @staticmethod
    def LibPrintf(Parser, ReturnValue, Param, NumArgs):
        from platform_module import PlatformModule
        if NumArgs < 1:
            return
        fmt_val = Param[0]
        if fmt_val.Typ is not None and fmt_val.Typ.Base == BaseType.TypePointer:
            fmt_str = str(fmt_val.Val.Pointer) if fmt_val.Val.Pointer else ""
        elif hasattr(fmt_val.Val, 'Identifier'):
            fmt_str = str(fmt_val.Val.Identifier)
        else:
            fmt_str = str(fmt_val.Val.Pointer) if hasattr(fmt_val.Val, 'Pointer') and fmt_val.Val.Pointer else ""
        args = []
        for i in range(1, NumArgs):
            args.append(Param[i])
        PlatformModule.VPrintf(Parser.pc.CStdOut, fmt_str, tuple(args))
