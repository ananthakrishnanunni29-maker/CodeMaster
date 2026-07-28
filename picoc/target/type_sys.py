import ctypes
import struct

from interpreter import *

class TypeModule:
    @staticmethod
    def Add(pc, Parser, ParentType, Base, ArraySize, Identifier, Sizeof, AlignBytes):
        NewType = ValueType()
        NewType.Base = Base
        NewType.ArraySize = ArraySize
        NewType.Sizeof = Sizeof
        NewType.AlignBytes = AlignBytes
        NewType.Identifier = Identifier
        NewType.Members = None
        NewType.FromType = ParentType
        NewType.DerivedTypeList = None
        NewType.OnHeap = True
        NewType.Next = ParentType.DerivedTypeList
        ParentType.DerivedTypeList = NewType
        return NewType

    @staticmethod
    def GetMatching(pc, Parser, ParentType, Base, ArraySize, Identifier, AllowDuplicates):
        ThisType = ParentType.DerivedTypeList
        while ThisType is not None:
            if (ThisType.Base == Base and ThisType.ArraySize == ArraySize and ThisType.Identifier == Identifier):
                if AllowDuplicates:
                    return ThisType
                from platform_module import PlatformModule
                PlatformModule.ProgramFailNoParser(pc, "data type '%s' is already defined" % Identifier)
                return None
            ThisType = ThisType.Next

        IntAlignBytes = 4
        PointerAlignBytes = ctypes.sizeof(ctypes.c_void_p)

        if Base == TypePointer:
            Sizeof = ctypes.sizeof(ctypes.c_void_p)
            AlignBytes = PointerAlignBytes
        elif Base == TypeArray:
            Sizeof = ArraySize * ParentType.Sizeof
            AlignBytes = ParentType.AlignBytes
        elif Base == TypeEnum:
            Sizeof = ctypes.sizeof(ctypes.c_int)
            AlignBytes = IntAlignBytes
        else:
            Sizeof = 0
            AlignBytes = 0

        return TypeModule.Add(pc, Parser, ParentType, Base, ArraySize, Identifier, Sizeof, AlignBytes)

    @staticmethod
    def StackSizeValue(Val):
        if Val is not None and Val.ValOnStack:
            return TypeModule.SizeValue(Val, False)
        return 0

    @staticmethod
    def SizeValue(Val, Compact):
        if Val.Typ is None:
            return 0
        Typ = Val.Typ
        if Typ.Base in (TypeInt, TypeShort, TypeChar, TypeLong, TypeUnsignedInt, TypeUnsignedShort, TypeUnsignedLong, TypeUnsignedChar):
            if not Compact:
                return 8
        if Typ.Base != TypeArray:
            return Typ.Sizeof
        return Typ.FromType.Sizeof * Typ.ArraySize

    @staticmethod
    def Size(Typ, ArraySize, Compact):
        if Typ is None:
            return 0
        if Typ.Base in (TypeInt, TypeShort, TypeChar, TypeLong, TypeUnsignedInt, TypeUnsignedShort, TypeUnsignedLong, TypeUnsignedChar):
            if not Compact:
                return 8
        if Typ.Base != TypeArray:
            return Typ.Sizeof
        return Typ.FromType.Sizeof * ArraySize

    @staticmethod
    def AddBaseType(pc, TypeNode, Base, Sizeof, AlignBytes):
        TypeNode.Base = Base
        TypeNode.ArraySize = 0
        TypeNode.Sizeof = Sizeof
        TypeNode.AlignBytes = AlignBytes
        TypeNode.Identifier = pc.StrEmpty
        TypeNode.Members = None
        TypeNode.FromType = None
        TypeNode.DerivedTypeList = None
        TypeNode.OnHeap = False
        TypeNode.Next = pc.UberType.DerivedTypeList
        pc.UberType.DerivedTypeList = TypeNode

    @staticmethod
    def Init(pc):
        IntAlignBytes = 4
        PointerAlignBytes = ctypes.sizeof(ctypes.c_void_p)

        pc.UberType.DerivedTypeList = None
        TypeModule.AddBaseType(pc, pc.IntType, TypeInt, ctypes.sizeof(ctypes.c_int), IntAlignBytes)
        TypeModule.AddBaseType(pc, pc.ShortType, TypeShort, ctypes.sizeof(ctypes.c_short), 2)
        TypeModule.AddBaseType(pc, pc.CharType, TypeChar, ctypes.sizeof(ctypes.c_byte), 1)
        TypeModule.AddBaseType(pc, pc.LongType, TypeLong, ctypes.sizeof(ctypes.c_long), 4)
        TypeModule.AddBaseType(pc, pc.UnsignedIntType, TypeUnsignedInt, ctypes.sizeof(ctypes.c_uint), IntAlignBytes)
        TypeModule.AddBaseType(pc, pc.UnsignedShortType, TypeUnsignedShort, ctypes.sizeof(ctypes.c_ushort), 2)
        TypeModule.AddBaseType(pc, pc.UnsignedLongType, TypeUnsignedLong, ctypes.sizeof(ctypes.c_ulong), 4)
        TypeModule.AddBaseType(pc, pc.UnsignedCharType, TypeUnsignedChar, ctypes.sizeof(ctypes.c_byte), 1)
        TypeModule.AddBaseType(pc, pc.VoidType, TypeVoid, 0, 1)
        TypeModule.AddBaseType(pc, pc.FunctionType, TypeFunction, ctypes.sizeof(ctypes.c_int), IntAlignBytes)
        TypeModule.AddBaseType(pc, pc.MacroType, TypeMacro, ctypes.sizeof(ctypes.c_int), IntAlignBytes)
        TypeModule.AddBaseType(pc, pc.GotoLabelType, TypeGotoLabel, 0, 1)
        TypeModule.AddBaseType(pc, pc.FPType, TypeFP, ctypes.sizeof(ctypes.c_double), 8)
        TypeModule.AddBaseType(pc, pc.TypeType, Type_Type, ctypes.sizeof(ctypes.c_double), 8)
        pc.CharArrayType = TypeModule.Add(pc, None, pc.CharType, TypeArray, 0, pc.StrEmpty, ctypes.sizeof(ctypes.c_byte), 1)
        pc.CharPtrType = TypeModule.Add(pc, None, pc.CharType, TypePointer, 0, pc.StrEmpty, ctypes.sizeof(ctypes.c_void_p), PointerAlignBytes)
        pc.CharPtrPtrType = TypeModule.Add(pc, None, pc.CharPtrType, TypePointer, 0, pc.StrEmpty, ctypes.sizeof(ctypes.c_void_p), PointerAlignBytes)
        pc.VoidPtrType = TypeModule.Add(pc, None, pc.VoidType, TypePointer, 0, pc.StrEmpty, ctypes.sizeof(ctypes.c_void_p), PointerAlignBytes)

    @staticmethod
    def CleanupNode(pc, Typ):
        SubType = Typ.DerivedTypeList
        while SubType is not None:
            NextSubType = SubType.Next
            TypeModule.CleanupNode(pc, SubType)
            if SubType.OnHeap:
                if SubType.Members is not None:
                    from variable import VariableModule
                    VariableModule.TableCleanup(pc, SubType.Members)
                pass
            SubType = NextSubType

    @staticmethod
    def Cleanup(pc):
        TypeModule.CleanupNode(pc, pc.UberType)

    @staticmethod
    def ParseStruct(Parser, TypPtr, IsStruct):
        from lex import LexModule
        from variable import VariableModule
        from platform_module import PlatformModule
        pc = Parser.pc
        Token = LexModule.GetToken(Parser, False)
        if Token == LexToken.TokenIdentifier:
            LexValue = Parser.pc.LexValue
            LexModule.GetToken(Parser, True)
            StructIdentifier = LexValue.Val.Identifier
            Token = LexModule.GetToken(Parser, False)
        else:
            from platform_module import PlatformModule
            StructIdentifier = PlatformModule.MakeTempName(pc, "^s0000")

        typ = TypeModule.GetMatching(pc, Parser, pc.UberType, TypeStruct if IsStruct else TypeUnion, 0, StructIdentifier, True)
        TypPtr[0] = typ

        if Token == LexToken.TokenLeftBrace and typ.Members is not None:
            PlatformModule.ProgramFail(Parser, "data type '%s' is already defined" % StructIdentifier)

        Token = LexModule.GetToken(Parser, False)
        if Token != LexToken.TokenLeftBrace:
            return

        if pc.TopStackFrame is not None:
            PlatformModule.ProgramFail(Parser, "struct/union definitions can only be globals")

        LexModule.GetToken(Parser, True)
        typ.Members = Table()

        from table import TableModule
        TableModule.InitTable(typ.Members, STRUCT_TABLE_SIZE, True)

        while True:
            MemberType = [None]
            MemberIdentifier = [""]
            TypeModule.Parse(Parser, MemberType, MemberIdentifier, None)
            if MemberType[0] is None or MemberIdentifier[0] is None or MemberIdentifier[0] == "":
                PlatformModule.ProgramFail(Parser, "invalid type in struct")

            MemberValue = VariableModule.AllocValueAndData(pc, Parser, ctypes.sizeof(ctypes.c_int), False, None, True)
            MemberValue.Typ = MemberType[0]
            if IsStruct:
                AlignBoundary = MemberValue.Typ.AlignBytes
                if AlignBoundary > 0 and (typ.Sizeof & (AlignBoundary - 1)) != 0:
                    typ.Sizeof += AlignBoundary - (typ.Sizeof & (AlignBoundary - 1))
                MemberValue.Val = typ.Sizeof
                typ.Sizeof += TypeModule.SizeValue(MemberValue, True)
            else:
                MemberValue.Val = 0
                sv = TypeModule.SizeValue(MemberValue, True)
                if sv > typ.Sizeof:
                    typ.Sizeof = sv

            if typ.AlignBytes < MemberValue.Typ.AlignBytes:
                typ.AlignBytes = MemberValue.Typ.AlignBytes

            TableModule.Set(pc, typ.Members, MemberIdentifier[0], MemberValue, Parser.FileName, Parser.Line, Parser.CharacterPos)

            if LexModule.GetToken(Parser, True) != LexToken.TokenSemicolon:
                PlatformModule.ProgramFail(Parser, "semicolon expected")

            if LexModule.GetToken(Parser, False) == LexToken.TokenRightBrace:
                break

        AlignBoundary = typ.AlignBytes
        if AlignBoundary > 0 and (typ.Sizeof & (AlignBoundary - 1)) != 0:
            typ.Sizeof += AlignBoundary - (typ.Sizeof & (AlignBoundary - 1))

        LexModule.GetToken(Parser, True)

    @staticmethod
    def CreateOpaqueStruct(pc, Parser, StructName, Size):
        Typ = TypeModule.GetMatching(pc, Parser, pc.UberType, TypeStruct, 0, StructName, False)
        Typ.Members = Table()
        from table import TableModule
        TableModule.InitTable(Typ.Members, STRUCT_TABLE_SIZE, True)
        Typ.Sizeof = Size
        return Typ

    @staticmethod
    def ParseEnum(Parser, TypPtr):
        from lex import LexModule
        from variable import VariableModule
        from platform_module import PlatformModule
        pc = Parser.pc
        Token = LexModule.GetToken(Parser, False)
        if Token == LexToken.TokenIdentifier:
            LexValue = Parser.pc.LexValue
            LexModule.GetToken(Parser, True)
            EnumIdentifier = LexValue.Val.Identifier
            Token = LexModule.GetToken(Parser, False)
        else:
            EnumIdentifier = PlatformModule.MakeTempName(pc, "^e0000")

        TypeModule.GetMatching(pc, Parser, pc.UberType, TypeEnum, 0, EnumIdentifier, Token != LexToken.TokenLeftBrace)
        TypPtr[0] = pc.IntType

        if Token != LexToken.TokenLeftBrace:
            return

        if pc.TopStackFrame is not None:
            PlatformModule.ProgramFail(Parser, "enum definitions can only be globals")

        LexModule.GetToken(Parser, True)
        EnumValue = 0
        InitValue = Value()
        InitValue.Typ = pc.IntType
        InitValue.Val = EnumValue

        while True:
            LexValue = Parser.pc.LexValue
            if LexModule.GetToken(Parser, True) != LexToken.TokenIdentifier:
                PlatformModule.ProgramFail(Parser, "identifier expected")
            EnumIdentifier = LexValue.Val.Identifier

            if LexModule.GetToken(Parser, False) == LexToken.TokenAssign:
                LexModule.GetToken(Parser, True)
                EnumValue = VariableModule.ExpressionParseInt(Parser)

            InitValue.Val = EnumValue
            VariableModule.Define(pc, Parser, EnumIdentifier, InitValue, None, False)

            Token = LexModule.GetToken(Parser, True)
            if Token != LexToken.TokenComma and Token != LexToken.TokenRightBrace:
                PlatformModule.ProgramFail(Parser, "comma expected")
            EnumValue += 1
            if Token == LexToken.TokenRightBrace:
                break

    @staticmethod
    def ParseFront(Parser, TypPtr, IsStaticPtr):
        from lex import LexModule
        from variable import VariableModule
        from platform_module import PlatformModule
        pc = Parser.pc
        Unsigned = False
        StaticQualifier = False

        BeforePos = Parser.Pos
        BeforeLine = Parser.Line
        BeforeHashIfLevel = Parser.HashIfLevel
        BeforeHashIfEvaluateToLevel = Parser.HashIfEvaluateToLevel
        BeforeCharacterPos = Parser.CharacterPos

        Token = LexModule.GetToken(Parser, True)
        while Token in (LexToken.TokenStaticType, LexToken.TokenAutoType, LexToken.TokenRegisterType, LexToken.TokenExternType):
            if Token == LexToken.TokenStaticType:
                StaticQualifier = True
            Token = LexModule.GetToken(Parser, True)

        if IsStaticPtr is not None:
            IsStaticPtr[0] = StaticQualifier

        if Token == LexToken.TokenSignedType or Token == LexToken.TokenUnsignedType:
            FollowToken = LexModule.GetToken(Parser, False)
            Unsigned = (Token == LexToken.TokenUnsignedType)
            if FollowToken not in (LexToken.TokenIntType, LexToken.TokenLongType, LexToken.TokenShortType, LexToken.TokenCharType):
                TypPtr[0] = pc.UnsignedIntType if Unsigned else pc.IntType
                return True
            Token = LexModule.GetToken(Parser, True)

        if Token == LexToken.TokenIntType:
            TypPtr[0] = pc.UnsignedIntType if Unsigned else pc.IntType
        elif Token == LexToken.TokenShortType:
            TypPtr[0] = pc.UnsignedShortType if Unsigned else pc.ShortType
        elif Token == LexToken.TokenCharType:
            TypPtr[0] = pc.UnsignedCharType if Unsigned else pc.CharType
        elif Token == LexToken.TokenLongType:
            TypPtr[0] = pc.UnsignedLongType if Unsigned else pc.LongType
        elif Token in (LexToken.TokenFloatType, LexToken.TokenDoubleType):
            TypPtr[0] = pc.FPType
        elif Token == LexToken.TokenVoidType:
            TypPtr[0] = pc.VoidType
        elif Token in (LexToken.TokenStructType, LexToken.TokenUnionType):
            TypeModule.ParseStruct(Parser, TypPtr, Token == LexToken.TokenStructType)
        elif Token == LexToken.TokenEnumType:
            TypeModule.ParseEnum(Parser, TypPtr)
        elif Token == LexToken.TokenIdentifier:
            VarValue = VariableModule.Get(pc, Parser, Parser.pc.LexValue.Val.Identifier)
            if VarValue.Typ is pc.TypeType:
                TypPtr[0] = VarValue.Val
            else:
                TypPtr[0] = pc.TypeType
        else:
            Parser.Pos = BeforePos
            Parser.Line = BeforeLine
            Parser.HashIfLevel = BeforeHashIfLevel
            Parser.HashIfEvaluateToLevel = BeforeHashIfEvaluateToLevel
            Parser.CharacterPos = BeforeCharacterPos
            return False

        return True

    @staticmethod
    def ParseBack(Parser, FromType):
        from lex import LexModule
        BeforePos = Parser.Pos
        BeforeLine = Parser.Line
        BeforeCharacterPos = Parser.CharacterPos

        Token = LexModule.GetToken(Parser, True)
        if Token == LexToken.TokenLeftSquareBracket:
            if LexModule.GetToken(Parser, False) == LexToken.TokenRightSquareBracket:
                LexModule.GetToken(Parser, True)
                return TypeModule.GetMatching(Parser.pc, Parser, TypeModule.ParseBack(Parser, FromType), TypeArray, 0, Parser.pc.StrEmpty, True)
            else:
                OldMode = Parser.Mode
                Parser.Mode = RunMode.RunModeRun
                from variable import VariableModule
                ArraySize = VariableModule.ExpressionParseInt(Parser)
                Parser.Mode = OldMode
                if LexModule.GetToken(Parser, True) != LexToken.TokenRightSquareBracket:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "']' expected")
                return TypeModule.GetMatching(Parser.pc, Parser, TypeModule.ParseBack(Parser, FromType), TypeArray, ArraySize, Parser.pc.StrEmpty, True)
        else:
            Parser.Pos = BeforePos
            Parser.Line = BeforeLine
            Parser.CharacterPos = BeforeCharacterPos
            return FromType

    @staticmethod
    def ParseIdentPart(Parser, BasicTyp, TypPtr, IdentifierPtr):
        from lex import LexModule
        from platform_module import PlatformModule
        pc = Parser.pc
        Done = False
        TypPtr[0] = BasicTyp
        IdentifierPtr[0] = pc.StrEmpty

        while not Done:
            BeforePos = Parser.Pos
            BeforeLine = Parser.Line
            BeforeCharacterPos = Parser.CharacterPos

            Token = LexModule.GetToken(Parser, True)
            if Token == LexToken.TokenOpenBracket:
                if TypPtr[0] is not None:
                    PlatformModule.ProgramFail(Parser, "bad type declaration")
                SubTyp = [None]
                SubIdent = [""]
                TypeModule.Parse(Parser, SubTyp, SubIdent, None)
                TypPtr[0] = SubTyp[0]
                if LexModule.GetToken(Parser, True) != LexToken.TokenCloseBracket:
                    PlatformModule.ProgramFail(Parser, "')' expected")
            elif Token == LexToken.TokenAsterisk:
                if TypPtr[0] is None:
                    PlatformModule.ProgramFail(Parser, "bad type declaration")
                TypPtr[0] = TypeModule.GetMatching(pc, Parser, TypPtr[0], TypePointer, 0, pc.StrEmpty, True)
            elif Token == LexToken.TokenIdentifier:
                if TypPtr[0] is None or IdentifierPtr[0] != pc.StrEmpty:
                    PlatformModule.ProgramFail(Parser, "bad type declaration")
                IdentifierPtr[0] = Parser.pc.LexValue.Val.Identifier
                Done = True
            else:
                Parser.Pos = BeforePos
                Parser.Line = BeforeLine
                Parser.CharacterPos = BeforeCharacterPos
                Done = True

        if TypPtr[0] is None:
            PlatformModule.ProgramFail(Parser, "bad type declaration")

        if IdentifierPtr[0] != pc.StrEmpty:
            TypPtr[0] = TypeModule.ParseBack(Parser, TypPtr[0])

    @staticmethod
    def Parse(Parser, TypPtr, IdentifierPtr, IsStaticPtr):
        BasicType = [None]
        TypeModule.ParseFront(Parser, BasicType, IsStaticPtr)
        TypeModule.ParseIdentPart(Parser, BasicType[0], TypPtr, IdentifierPtr)

    @staticmethod
    def IsForwardDeclared(Parser, Typ):
        if Typ.Base == TypeArray:
            return TypeModule.IsForwardDeclared(Parser, Typ.FromType)
        if (Typ.Base == TypeStruct or Typ.Base == TypeUnion) and Typ.Members is None:
            return True
        return False
