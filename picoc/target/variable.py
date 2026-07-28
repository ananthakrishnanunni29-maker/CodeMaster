from interpreter import *
from table import TableModule
from type_sys import TypeModule

class VariableModule:
    @staticmethod
    def Init(pc):
        TableModule.InitTable(pc.GlobalTable, GLOBAL_TABLE_SIZE, True)
        TableModule.InitTable(pc.StringLiteralTable, STRING_LITERAL_TABLE_SIZE, True)
        pc.TopStackFrame = None
        pc.ScopeCounter = 0

    @staticmethod
    def Free(pc, Val):
        if Val is None:
            return
        if Val.ValOnHeap or Val.AnyValOnHeap:
            if Val.Typ == pc.FunctionType and Val.Val is not None and hasattr(Val.Val, 'FuncDef') and Val.Val.FuncDef is not None:
                if Val.Val.FuncDef.Intrinsic is None and Val.Val.FuncDef.BodyTokens is not None:
                    Val.Val.FuncDef.BodyTokens = None
            if Val.Typ == pc.MacroType and Val.Val is not None and hasattr(Val.Val, 'MacroDef') and Val.Val.MacroDef is not None:
                if Val.Val.MacroDef.BodyTokens is not None:
                    Val.Val.MacroDef.BodyTokens = None
            if Val.AnyValOnHeap:
                Val.Val = None
        if Val.ValOnHeap:
            pass

    @staticmethod
    def TableCleanup(pc, HashTable):
        for key in list(HashTable.entries.keys()):
            entry = HashTable.entries[key]
            VariableModule.Free(pc, entry.Val)
            del HashTable.entries[key]

    @staticmethod
    def Cleanup(pc):
        VariableModule.TableCleanup(pc, pc.GlobalTable)
        VariableModule.TableCleanup(pc, pc.StringLiteralTable)

    @staticmethod
    def Alloc(pc, Parser, Size, OnHeap):
        return bytearray(Size)

    @staticmethod
    def AllocValueAndData(pc, Parser, DataSize, IsLValue, LValueFrom, OnHeap):
        NewValue = Value()
        NewValue.Val = AnyValue()
        NewValue.ValOnHeap = OnHeap
        NewValue.AnyValOnHeap = False
        NewValue.ValOnStack = not OnHeap
        NewValue.IsLValue = IsLValue
        NewValue.LValueFrom = LValueFrom
        if Parser:
            NewValue.ScopeID = Parser.ScopeID
        NewValue.OutOfScope = False
        return NewValue

    @staticmethod
    def AllocValueFromType(pc, Parser, Typ, IsLValue, LValueFrom, OnHeap):
        Size = TypeModule.Size(Typ, Typ.ArraySize, False)
        NewValue = VariableModule.AllocValueAndData(pc, Parser, Size, IsLValue, LValueFrom, OnHeap)
        NewValue.Typ = Typ
        if Typ.Base == BaseType.TypeArray:
            NewValue.Val.Elements = [VariableModule._ArrayElement(Typ.FromType) for _ in range(Typ.ArraySize)]
        return NewValue

    @staticmethod
    def _ArrayElement(Typ):
        value = AnyValue()
        if Typ is not None and Typ.Base == BaseType.TypeArray:
            value.Elements = [VariableModule._ArrayElement(Typ.FromType) for _ in range(Typ.ArraySize)]
        return value

    @staticmethod
    def AllocValueAndCopy(pc, Parser, FromValue, OnHeap):
        NewValue = VariableModule.AllocValueAndData(pc, Parser, 0, FromValue.IsLValue, FromValue.LValueFrom, OnHeap)
        if FromValue.Val is not None:
            if isinstance(FromValue.Val, AnyValue):
                NewValue.Val = AnyValue()
                if hasattr(FromValue.Val, 'LongInteger'):
                    NewValue.Val.LongInteger = FromValue.Val.LongInteger
                if hasattr(FromValue.Val, 'Integer'):
                    NewValue.Val.Integer = FromValue.Val.Integer
                if hasattr(FromValue.Val, 'Character'):
                    NewValue.Val.Character = FromValue.Val.Character
                if hasattr(FromValue.Val, 'ShortInteger'):
                    NewValue.Val.ShortInteger = FromValue.Val.ShortInteger
                if hasattr(FromValue.Val, 'FP'):
                    NewValue.Val.FP = FromValue.Val.FP
                if hasattr(FromValue.Val, 'Pointer'):
                    NewValue.Val.Pointer = FromValue.Val.Pointer
                if hasattr(FromValue.Val, 'Identifier'):
                    NewValue.Val.Identifier = FromValue.Val.Identifier
                if hasattr(FromValue.Val, 'UnsignedInteger'):
                    NewValue.Val.UnsignedInteger = FromValue.Val.UnsignedInteger
                if hasattr(FromValue.Val, 'UnsignedShortInteger'):
                    NewValue.Val.UnsignedShortInteger = FromValue.Val.UnsignedShortInteger
                if hasattr(FromValue.Val, 'UnsignedLongInteger'):
                    NewValue.Val.UnsignedLongInteger = FromValue.Val.UnsignedLongInteger
                if hasattr(FromValue.Val, 'UnsignedCharacter'):
                    NewValue.Val.UnsignedCharacter = FromValue.Val.UnsignedCharacter
                if hasattr(FromValue.Val, 'FuncDef'):
                    NewValue.Val.FuncDef = FromValue.Val.FuncDef
                if hasattr(FromValue.Val, 'MacroDef'):
                    NewValue.Val.MacroDef = FromValue.Val.MacroDef
                if hasattr(FromValue.Val, 'Typ'):
                    NewValue.Val.Typ = FromValue.Val.Typ
            else:
                NewValue.Val = FromValue.Val
        NewValue.Typ = FromValue.Typ
        return NewValue

    @staticmethod
    def AllocValueFromExistingData(Parser, Typ, FromValue, IsLValue, LValueFrom):
        NewValue = Value()
        NewValue.Typ = Typ
        NewValue.Val = FromValue
        NewValue.ValOnHeap = False
        NewValue.AnyValOnHeap = False
        NewValue.ValOnStack = False
        NewValue.IsLValue = IsLValue
        NewValue.LValueFrom = LValueFrom
        return NewValue

    @staticmethod
    def AllocValueShared(Parser, FromValue):
        return VariableModule.AllocValueFromExistingData(Parser, FromValue.Typ, FromValue.Val, FromValue.IsLValue, FromValue if FromValue.IsLValue else None)

    @staticmethod
    def Realloc(Parser, FromValue, NewSize):
        if FromValue.AnyValOnHeap:
            pass
        FromValue.Val = AnyValue()
        if FromValue.Typ is not None and FromValue.Typ.Base == BaseType.TypeArray:
            FromValue.Val.Elements = [VariableModule._ArrayElement(FromValue.Typ.FromType) for _ in range(FromValue.Typ.ArraySize)]
        FromValue.AnyValOnHeap = True

    @staticmethod
    def ScopeBegin(Parser, OldScopeID):
        if Parser.ScopeID == -1:
            return -1

        HashTable = Parser.pc.GlobalTable if Parser.pc.TopStackFrame is None else Parser.pc.TopStackFrame.LocalTable
        Parser.pc.ScopeCounter += 1
        OldScopeID[0] = Parser.ScopeID
        Parser.ScopeID = Parser.pc.ScopeCounter

        for key, entry in list(HashTable.entries.items()):
            if entry.Val.ScopeID == Parser.ScopeID and entry.Val.OutOfScope:
                entry.Val.OutOfScope = False
                entry.Key = str(int(hash(key)) & ~1) if isinstance(key, str) else key

        return Parser.ScopeID

    @staticmethod
    def ScopeEnd(Parser, ScopeID, PrevScopeID):
        if ScopeID == -1:
            return

        HashTable = Parser.pc.GlobalTable if Parser.pc.TopStackFrame is None else Parser.pc.TopStackFrame.LocalTable

        for key, entry in list(HashTable.entries.items()):
            if entry.Val.ScopeID == ScopeID and not entry.Val.OutOfScope:
                entry.Val.OutOfScope = True

        Parser.ScopeID = PrevScopeID

    @staticmethod
    def Def(pc, Parser, Ident, InitValue, Typ, MakeWritable):
        ScopeID = Parser.ScopeID if Parser else -1
        currentTable = pc.GlobalTable if pc.TopStackFrame is None else pc.TopStackFrame.LocalTable

        if InitValue is not None:
            AssignValue = VariableModule.AllocValueAndCopy(pc, Parser, InitValue, pc.TopStackFrame is None)
        else:
            AssignValue = VariableModule.AllocValueFromType(pc, Parser, Typ, MakeWritable, None, pc.TopStackFrame is None)

        AssignValue.IsLValue = MakeWritable
        AssignValue.ScopeID = ScopeID
        AssignValue.OutOfScope = False

        if not TableModule.Set(pc, currentTable, Ident, AssignValue, Parser.FileName if Parser else None, Parser.Line if Parser else 0, Parser.CharacterPos if Parser else 0):
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "'%s' is already defined" % Ident)

        return AssignValue

    @staticmethod
    def DefButIgnoreIdentical(Parser, Ident, Typ, IsStatic, FirstVisit):
        pc = Parser.pc

        if TypeModule.IsForwardDeclared(Parser, Typ):
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "type '%s' isn't defined" % (Typ.Identifier if Typ.Identifier else "unknown"))

        if IsStatic:
            MangledName = "/" + Parser.FileName
            if pc.TopStackFrame is not None:
                MangledName += "/" + pc.TopStackFrame.FuncName
            MangledName += "/" + Ident
            RegisteredMangledName = TableModule.StrRegister(pc, MangledName)

            ExistingValue = TableModule.Get(pc.GlobalTable, RegisteredMangledName)
            if ExistingValue is None:
                ExistingValue = VariableModule.AllocValueFromType(pc, Parser, Typ, True, None, True)
                TableModule.Set(pc, pc.GlobalTable, RegisteredMangledName, ExistingValue, Parser.FileName, Parser.Line, Parser.CharacterPos)
                FirstVisit[0] = True

            VariableModule.DefinePlatformVar(pc, Parser, Ident, ExistingValue.Typ, ExistingValue.Val, True)
            return ExistingValue
        else:
            currentTable = pc.GlobalTable if pc.TopStackFrame is None else pc.TopStackFrame.LocalTable
            ExistingValue = TableModule.Get(currentTable, Ident)
            if ExistingValue is not None and Parser.Line != 0:
                return ExistingValue
            return VariableModule.Def(pc, Parser, Ident, None, Typ, True)

    @staticmethod
    def Defined(pc, Ident):
        if pc.TopStackFrame is not None:
            FoundValue = TableModule.Get(pc.TopStackFrame.LocalTable, Ident)
            if FoundValue is not None:
                return True
        FoundValue = TableModule.Get(pc.GlobalTable, Ident)
        return FoundValue is not None

    @staticmethod
    def Get(pc, Parser, Ident):
        if pc.TopStackFrame is not None:
            LVal = TableModule.Get(pc.TopStackFrame.LocalTable, Ident)
            if LVal is not None:
                return LVal
        LVal = TableModule.Get(pc.GlobalTable, Ident)
        if LVal is None:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "'%s' is undefined" % Ident)
        return LVal

    @staticmethod
    def DefinePlatformVar(pc, Parser, Ident, Typ, FromValue, IsWritable):
        SomeValue = VariableModule.AllocValueAndData(pc, None, 0, IsWritable, None, True)
        SomeValue.Typ = Typ
        if isinstance(FromValue, AnyValue):
            SomeValue.Val = FromValue
        else:
            SomeValue.Val = AnyValue()
            if Typ is not None:
                bt = Typ.Base
                if bt == TypeInt or bt == TypeShort or bt == TypeLong or bt == TypeUnsignedInt or bt == TypeUnsignedShort or bt == TypeUnsignedLong:
                    SomeValue.Val.Integer = FromValue
                elif bt == TypeChar or bt == TypeUnsignedChar:
                    SomeValue.Val.Character = FromValue
                elif bt == TypeFP:
                    SomeValue.Val.FP = FromValue
                elif bt == TypePointer or bt == TypeArray:
                    SomeValue.Val.Pointer = FromValue
                else:
                    SomeValue.Val.Integer = FromValue
            else:
                SomeValue.Val.Integer = FromValue

        currentTable = pc.GlobalTable if pc.TopStackFrame is None else pc.TopStackFrame.LocalTable
        if not TableModule.Set(pc, currentTable, TableModule.StrRegister(pc, Ident), SomeValue, Parser.FileName if Parser else None, Parser.Line if Parser else 0, Parser.CharacterPos if Parser else 0):
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "'%s' is already defined" % Ident)

    @staticmethod
    def StackPop(Parser, Var):
        from platform_module import PlatformModule
        pass

    @staticmethod
    def StackFrameAdd(Parser, FuncName, NumParams):
        NewFrame = StackFrame()
        NewFrame.FuncName = FuncName
        NewFrame.Parameter = []
        NewFrame.NumParams = 0
        NewFrame.ReturnParser = ParseState()
        from lex import LexModule
        LexModule.ParserCopy(NewFrame.ReturnParser, Parser)
        NewFrame.LocalTable = Table()
        TableModule.InitTable(NewFrame.LocalTable, LOCAL_TABLE_SIZE, False)
        NewFrame.PreviousStackFrame = Parser.pc.TopStackFrame
        Parser.pc.TopStackFrame = NewFrame

    @staticmethod
    def StackFramePop(Parser):
        if Parser.pc.TopStackFrame is None:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "stack is empty - can't go back")
        from lex import LexModule
        LexModule.ParserCopy(Parser, Parser.pc.TopStackFrame.ReturnParser)
        Parser.pc.TopStackFrame = Parser.pc.TopStackFrame.PreviousStackFrame

    @staticmethod
    def StringLiteralGet(pc, Ident):
        return TableModule.Get(pc.StringLiteralTable, Ident)

    @staticmethod
    def StringLiteralDefine(pc, Ident, Val):
        TableModule.Set(pc, pc.StringLiteralTable, Ident, Val, None, 0, 0)

    @staticmethod
    def DereferencePointer(PointerValue):
        if PointerValue.Val is None or PointerValue.Val.Pointer is None:
            return None
        DerefType = PointerValue.Typ.FromType if PointerValue.Typ else None
        return DerefType

    @staticmethod
    def ExpressionParseInt(Parser):
        from expression import ExpressionModule
        return ExpressionModule.ParseInt(Parser)
