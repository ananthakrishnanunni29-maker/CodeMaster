from interpreter import *
from type_sys import TypeModule
from lex import LexModule
from variable import VariableModule

OperatorPrecedence = [
    OpPrecedence(0, 0, 0, "none"),
    OpPrecedence(0, 0, 0, ","),
    OpPrecedence(0, 0, 2, "="),
    OpPrecedence(0, 0, 2, "+="),
    OpPrecedence(0, 0, 2, "-="),
    OpPrecedence(0, 0, 2, "*="),
    OpPrecedence(0, 0, 2, "/="),
    OpPrecedence(0, 0, 2, "%="),
    OpPrecedence(0, 0, 2, "<<="),
    OpPrecedence(0, 0, 2, ">>="),
    OpPrecedence(0, 0, 2, "&="),
    OpPrecedence(0, 0, 2, "|="),
    OpPrecedence(0, 0, 2, "^="),
    OpPrecedence(0, 0, 3, "?"),
    OpPrecedence(0, 0, 3, ":"),
    OpPrecedence(0, 0, 4, "||"),
    OpPrecedence(0, 0, 5, "&&"),
    OpPrecedence(0, 0, 6, "|"),
    OpPrecedence(0, 0, 7, "^"),
    OpPrecedence(14, 0, 8, "&"),
    OpPrecedence(0, 0, 9, "=="),
    OpPrecedence(0, 0, 9, "!="),
    OpPrecedence(0, 0, 10, "<"),
    OpPrecedence(0, 0, 10, ">"),
    OpPrecedence(0, 0, 10, "<="),
    OpPrecedence(0, 0, 10, ">="),
    OpPrecedence(0, 0, 11, "<<"),
    OpPrecedence(0, 0, 11, ">>"),
    OpPrecedence(14, 0, 12, "+"),
    OpPrecedence(14, 0, 12, "-"),
    OpPrecedence(14, 0, 13, "*"),
    OpPrecedence(0, 0, 13, "/"),
    OpPrecedence(0, 0, 13, "%"),
    OpPrecedence(14, 15, 0, "++"),
    OpPrecedence(14, 15, 0, "--"),
    OpPrecedence(14, 0, 0, "!"),
    OpPrecedence(14, 0, 0, "~"),
    OpPrecedence(14, 0, 0, "sizeof"),
    OpPrecedence(14, 0, 0, "cast"),
    OpPrecedence(0, 0, 15, "["),
    OpPrecedence(0, 15, 0, "]"),
    OpPrecedence(0, 0, 15, "."),
    OpPrecedence(0, 0, 15, "->"),
    OpPrecedence(15, 0, 0, "("),
    OpPrecedence(0, 15, 0, ")"),
]

BRACKET_PRECEDENCE = 20
DEEP_PRECEDENCE = BRACKET_PRECEDENCE * 1000

def IS_LEFT_TO_RIGHT(p):
    return p != 2 and p != 14

def IS_FP(v):
    return v.Typ is not None and v.Typ.Base == TypeFP

def IS_INTEGER_NUMERIC(v):
    return v.Typ is not None and TypeInt <= v.Typ.Base <= TypeUnsignedLong

def IS_NUMERIC_COERCIBLE(v):
    return IS_INTEGER_NUMERIC(v) or IS_FP(v)

def IS_POINTER_COERCIBLE(v, ap):
    return ap and v.Typ is not None and v.Typ.Base == TypePointer

def IS_NUMERIC_COERCIBLE_PLUS_POINTERS(v, ap):
    return IS_NUMERIC_COERCIBLE(v) or IS_POINTER_COERCIBLE(v, ap)

class ExpressionModule:
    @staticmethod
    def IsTypeToken(Parser, t):
        if LexToken.TokenIntType <= t <= LexToken.TokenUnsignedType:
            return True
        if t == LexToken.TokenIdentifier:
            val = Parser.pc.LexValue.Val
            ident = val.Identifier if hasattr(val, 'Identifier') else val
            if VariableModule.Defined(Parser.pc, ident):
                VarValue = VariableModule.Get(Parser.pc, Parser, ident)
                if VarValue.Typ == Parser.pc.TypeType:
                    return True
        return False

    @staticmethod
    def CoerceInteger(Val):
        if Val.Typ is None:
            return 0
        bt = Val.Typ.Base
        if Val.Val is None:
            return 0
        if bt == TypeInt:
            return Val.Val.Integer
        elif bt == TypeChar:
            return Val.Val.Character
        elif bt == TypeShort:
            return Val.Val.ShortInteger
        elif bt == TypeLong:
            return Val.Val.LongInteger
        elif bt == TypeUnsignedInt:
            return Val.Val.UnsignedInteger
        elif bt == TypeUnsignedShort:
            return Val.Val.UnsignedShortInteger
        elif bt == TypeUnsignedLong:
            return Val.Val.UnsignedLongInteger
        elif bt == TypeUnsignedChar:
            return Val.Val.UnsignedCharacter
        elif bt == TypePointer:
            return id(Val.Val.Pointer) if Val.Val.Pointer else 0
        elif bt == TypeFP:
            return int(Val.Val.FP)
        return 0

    @staticmethod
    def CoerceUnsignedInteger(Val):
        if Val.Typ is None:
            return 0
        bt = Val.Typ.Base
        if Val.Val is None:
            return 0
        if bt == TypeInt:
            return Val.Val.Integer & 0xFFFFFFFF
        elif bt == TypeChar:
            return Val.Val.Character & 0xFFFFFFFF
        elif bt == TypeShort:
            return Val.Val.ShortInteger & 0xFFFFFFFF
        elif bt == TypeLong:
            return Val.Val.LongInteger & 0xFFFFFFFF
        elif bt == TypeUnsignedInt:
            return Val.Val.UnsignedInteger
        elif bt == TypeUnsignedShort:
            return Val.Val.UnsignedShortInteger
        elif bt == TypeUnsignedLong:
            return Val.Val.UnsignedLongInteger
        elif bt == TypeUnsignedChar:
            return Val.Val.UnsignedCharacter
        elif bt == TypePointer:
            return id(Val.Val.Pointer) if Val.Val.Pointer else 0
        elif bt == TypeFP:
            return int(Val.Val.FP) & 0xFFFFFFFF
        return 0

    @staticmethod
    def CoerceFP(Val):
        if Val.Typ is None:
            return 0.0
        bt = Val.Typ.Base
        if Val.Val is None:
            return 0.0
        if bt == TypeInt:
            return float(Val.Val.Integer)
        elif bt == TypeChar:
            return float(Val.Val.Character)
        elif bt == TypeShort:
            return float(Val.Val.ShortInteger)
        elif bt == TypeLong:
            return float(Val.Val.LongInteger)
        elif bt == TypeUnsignedInt:
            return float(Val.Val.UnsignedInteger)
        elif bt == TypeUnsignedShort:
            return float(Val.Val.UnsignedShortInteger)
        elif bt == TypeUnsignedLong:
            return float(Val.Val.UnsignedLongInteger)
        elif bt == TypeUnsignedChar:
            return float(Val.Val.UnsignedCharacter)
        elif bt == TypeFP:
            return Val.Val.FP
        return 0.0

    @staticmethod
    def AssignInt(Parser, DestValue, FromInt, After):
        if not DestValue.IsLValue:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "can't assign to this")
        if After:
            Result = ExpressionModule.CoerceInteger(DestValue)
        else:
            Result = FromInt

        bt = DestValue.Typ.Base
        if bt == TypeInt:
            DestValue.Val.Integer = int(FromInt)
        elif bt == TypeShort:
            DestValue.Val.ShortInteger = int(FromInt) & 0xFFFF
        elif bt == TypeChar:
            DestValue.Val.Character = int(FromInt) & 0xFF
        elif bt == TypeLong:
            DestValue.Val.LongInteger = FromInt
        elif bt == TypeUnsignedInt:
            DestValue.Val.UnsignedInteger = FromInt & 0xFFFFFFFF
        elif bt == TypeUnsignedShort:
            DestValue.Val.UnsignedShortInteger = FromInt & 0xFFFF
        elif bt == TypeUnsignedLong:
            DestValue.Val.UnsignedLongInteger = FromInt & 0xFFFFFFFF
        elif bt == TypeUnsignedChar:
            DestValue.Val.UnsignedCharacter = FromInt & 0xFF
        return Result

    @staticmethod
    def AssignFP(Parser, DestValue, FromFP):
        if not DestValue.IsLValue:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "can't assign to this")
        DestValue.Val.FP = FromFP
        return FromFP

    @staticmethod
    def AssignToPointer(Parser, ToValue, FromValue, FuncName, ParamNo, AllowPointerCoercion):
        PointedToType = ToValue.Typ.FromType
        if FromValue.Typ == ToValue.Typ or FromValue.Typ == Parser.pc.VoidPtrType or (ToValue.Typ == Parser.pc.VoidPtrType and FromValue.Typ.Base == TypePointer):
            ToValue.Val.Pointer = FromValue.Val.Pointer
        elif FromValue.Typ.Base == TypeArray and (PointedToType == FromValue.Typ.FromType or ToValue.Typ == Parser.pc.VoidPtrType):
            ToValue.Val.Pointer = FromValue.Val
        elif FromValue.Typ.Base == TypePointer and FromValue.Typ.FromType is not None and FromValue.Typ.FromType.Base == TypeArray and (PointedToType == FromValue.Typ.FromType.FromType or ToValue.Typ == Parser.pc.VoidPtrType):
            ToValue.Val.Pointer = FromValue.Val.Pointer
        elif IS_NUMERIC_COERCIBLE(FromValue) and ExpressionModule.CoerceInteger(FromValue) == 0:
            ToValue.Val.Pointer = None
        elif AllowPointerCoercion and IS_NUMERIC_COERCIBLE(FromValue):
            ToValue.Val.Pointer = ExpressionModule.CoerceUnsignedInteger(FromValue)
        elif AllowPointerCoercion and FromValue.Typ.Base == TypePointer:
            ToValue.Val.Pointer = FromValue.Val.Pointer
        else:
            from platform_module import PlatformModule
            PlatformModule.AssignFail(Parser, "%t from %t", ToValue.Typ, FromValue.Typ, 0, 0, FuncName, ParamNo)

    @staticmethod
    def Assign(Parser, DestValue, SourceValue, Force, FuncName, ParamNo, AllowPointerCoercion):
        if not DestValue.IsLValue and not Force:
            from platform_module import PlatformModule
            PlatformModule.AssignFail(Parser, "not an lvalue", None, None, 0, 0, FuncName, ParamNo)

        if IS_NUMERIC_COERCIBLE(DestValue) and not IS_NUMERIC_COERCIBLE_PLUS_POINTERS(SourceValue, AllowPointerCoercion):
            from platform_module import PlatformModule
            PlatformModule.AssignFail(Parser, "%t from %t", DestValue.Typ, SourceValue.Typ, 0, 0, FuncName, ParamNo)

        bt = DestValue.Typ.Base
        if bt == TypeInt:
            DestValue.Val.Integer = int(ExpressionModule.CoerceInteger(SourceValue))
        elif bt == TypeShort:
            DestValue.Val.ShortInteger = int(ExpressionModule.CoerceInteger(SourceValue)) & 0xFFFF
        elif bt == TypeChar:
            DestValue.Val.Character = int(ExpressionModule.CoerceInteger(SourceValue)) & 0xFF
        elif bt == TypeLong:
            DestValue.Val.LongInteger = ExpressionModule.CoerceInteger(SourceValue)
        elif bt == TypeUnsignedInt:
            DestValue.Val.UnsignedInteger = ExpressionModule.CoerceUnsignedInteger(SourceValue) & 0xFFFFFFFF
        elif bt == TypeUnsignedShort:
            DestValue.Val.UnsignedShortInteger = ExpressionModule.CoerceUnsignedInteger(SourceValue) & 0xFFFF
        elif bt == TypeUnsignedLong:
            DestValue.Val.UnsignedLongInteger = ExpressionModule.CoerceUnsignedInteger(SourceValue) & 0xFFFFFFFF
        elif bt == TypeUnsignedChar:
            DestValue.Val.UnsignedCharacter = ExpressionModule.CoerceUnsignedInteger(SourceValue) & 0xFF
        elif bt == TypeFP:
            if not IS_NUMERIC_COERCIBLE_PLUS_POINTERS(SourceValue, AllowPointerCoercion):
                from platform_module import PlatformModule
                PlatformModule.AssignFail(Parser, "%t from %t", DestValue.Typ, SourceValue.Typ, 0, 0, FuncName, ParamNo)
            DestValue.Val.FP = ExpressionModule.CoerceFP(SourceValue)
        elif bt == TypePointer:
            ExpressionModule.AssignToPointer(Parser, DestValue, SourceValue, FuncName, ParamNo, AllowPointerCoercion)
        elif bt == TypeArray:
            if SourceValue.Typ.Base == TypeArray and DestValue.Typ.ArraySize == 0:
                DestValue.Typ = SourceValue.Typ
                VariableModule.Realloc(Parser, DestValue, TypeModule.SizeValue(DestValue, False))
                if DestValue.LValueFrom is not None:
                    DestValue.LValueFrom.Val = DestValue.Val
                    DestValue.LValueFrom.AnyValOnHeap = DestValue.AnyValOnHeap
            if DestValue.Typ.FromType is not None and DestValue.Typ.FromType.Base == TypeChar and SourceValue.Typ.Base == TypePointer and SourceValue.Typ.FromType is not None and SourceValue.Typ.FromType.Base == TypeChar:
                if DestValue.Typ.ArraySize == 0:
                    Size = len(SourceValue.Val.Pointer) + 1 if SourceValue.Val.Pointer else 1
                    DestValue.Typ = TypeModule.GetMatching(Parser.pc, Parser, DestValue.Typ.FromType, DestValue.Typ.Base, Size, DestValue.Typ.Identifier, True)
                    VariableModule.Realloc(Parser, DestValue, TypeModule.SizeValue(DestValue, False))
                if SourceValue.Val and SourceValue.Val.Pointer:
                    data = str(SourceValue.Val.Pointer)
                else:
                    data = ""
                DestValue.Val = AnyValue()
                DestValue.Val.Identifier = data
                return
            if DestValue.Typ != SourceValue.Typ:
                from platform_module import PlatformModule
                PlatformModule.AssignFail(Parser, "%t from %t", DestValue.Typ, SourceValue.Typ, 0, 0, FuncName, ParamNo)
            if DestValue.Typ.ArraySize != SourceValue.Typ.ArraySize:
                from platform_module import PlatformModule
                PlatformModule.AssignFail(Parser, "from an array of size %d to one of size %d", None, None, DestValue.Typ.ArraySize, SourceValue.Typ.ArraySize, FuncName, ParamNo)
        elif bt in (TypeStruct, TypeUnion):
            if DestValue.Typ != SourceValue.Typ:
                from platform_module import PlatformModule
                PlatformModule.AssignFail(Parser, "%t from %t", DestValue.Typ, SourceValue.Typ, 0, 0, FuncName, ParamNo)
            if SourceValue.Val is not None and DestValue.Val is not None:
                if hasattr(SourceValue.Val, 'Identifier'):
                    DestValue.Val.Identifier = SourceValue.Val.Identifier
                if hasattr(SourceValue.Val, 'Integer'):
                    DestValue.Val.Integer = SourceValue.Val.Integer
        else:
            from platform_module import PlatformModule
            PlatformModule.AssignFail(Parser, "%t", DestValue.Typ, None, 0, 0, FuncName, ParamNo)

    @staticmethod
    def StackPushValueNode(Parser, StackTop, ValueLoc):
        StackNode = ExpressionStack()
        StackNode.Next = StackTop[0]
        StackNode.Val = ValueLoc
        StackNode.Order = OperatorOrder.OrderNone
        StackTop[0] = StackNode

    @staticmethod
    def StackPushValueByType(Parser, StackTop, PushType):
        ValueLoc = VariableModule.AllocValueFromType(Parser.pc, Parser, PushType, False, None, False)
        ExpressionModule.StackPushValueNode(Parser, StackTop, ValueLoc)
        return ValueLoc

    @staticmethod
    def StackPushValue(Parser, StackTop, PushValue):
        ValueLoc = VariableModule.AllocValueAndCopy(Parser.pc, Parser, PushValue, False)
        ExpressionModule.StackPushValueNode(Parser, StackTop, ValueLoc)

    @staticmethod
    def StackPushLValue(Parser, StackTop, PushValue, Offset):
        ValueLoc = VariableModule.AllocValueShared(Parser, PushValue)
        ExpressionModule.StackPushValueNode(Parser, StackTop, ValueLoc)

    @staticmethod
    def StackPushDereference(Parser, StackTop, DereferenceValue):
        DerefType = VariableModule.DereferencePointer(DereferenceValue)
        if DerefType is None:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "NULL pointer dereference")
        ValueLoc = VariableModule.AllocValueFromExistingData(Parser, DerefType, DereferenceValue.Val.Pointer, True, DereferenceValue.LValueFrom)
        ExpressionModule.StackPushValueNode(Parser, StackTop, ValueLoc)

    @staticmethod
    def PushInt(Parser, StackTop, IntValue):
        ValueLoc = VariableModule.AllocValueFromType(Parser.pc, Parser, Parser.pc.IntType, False, None, False)
        ValueLoc.Val.UnsignedLongInteger = IntValue & 0xFFFFFFFF
        ValueLoc.Val.LongInteger = IntValue
        ValueLoc.Val.Integer = int(IntValue)
        ValueLoc.Val.ShortInteger = int(IntValue) & 0xFFFF
        ValueLoc.Val.UnsignedShortInteger = IntValue & 0xFFFF
        ValueLoc.Val.UnsignedInteger = IntValue & 0xFFFFFFFF
        ValueLoc.Val.UnsignedCharacter = IntValue & 0xFF
        ValueLoc.Val.Character = int(IntValue) & 0xFF
        ExpressionModule.StackPushValueNode(Parser, StackTop, ValueLoc)

    @staticmethod
    def PushFP(Parser, StackTop, FPValue):
        ValueLoc = VariableModule.AllocValueFromType(Parser.pc, Parser, Parser.pc.FPType, False, None, False)
        ValueLoc.Val.FP = FPValue
        ExpressionModule.StackPushValueNode(Parser, StackTop, ValueLoc)

    @staticmethod
    def ExpressionPrefixOperator(Parser, StackTop, Op, TopValue):
        from platform_module import PlatformModule
        if Op == LexToken.TokenAmpersand:
            if not TopValue.IsLValue:
                PlatformModule.ProgramFail(Parser, "can't get the address of this")
            Result = VariableModule.AllocValueFromType(Parser.pc, Parser, TypeModule.GetMatching(Parser.pc, Parser, TopValue.Typ, TypePointer, 0, Parser.pc.StrEmpty, True), False, None, False)
            Result.Val.Pointer = TopValue.Val
            ExpressionModule.StackPushValueNode(Parser, StackTop, Result)
        elif Op == LexToken.TokenAsterisk:
            ExpressionModule.StackPushDereference(Parser, StackTop, TopValue)
        elif Op == LexToken.TokenSizeof:
            if TopValue.Typ == Parser.pc.TypeType:
                Typ = TopValue.Val.Typ
            else:
                Typ = TopValue.Typ
            if Typ.FromType is not None and Typ.FromType.Base == TypeStruct:
                Typ = Typ.FromType
            ExpressionModule.PushInt(Parser, StackTop, TypeModule.Size(Typ, Typ.ArraySize, True))
        else:
            if TopValue.Typ == Parser.pc.FPType:
                ResultFP = 0.0
                if Op == LexToken.TokenPlus:
                    ResultFP = TopValue.Val.FP
                elif Op == LexToken.TokenMinus:
                    ResultFP = -TopValue.Val.FP
                elif Op == LexToken.TokenIncrement:
                    ResultFP = ExpressionModule.AssignFP(Parser, TopValue, TopValue.Val.FP + 1)
                elif Op == LexToken.TokenDecrement:
                    ResultFP = ExpressionModule.AssignFP(Parser, TopValue, TopValue.Val.FP - 1)
                elif Op == LexToken.TokenUnaryNot:
                    ResultFP = 1.0 if not TopValue.Val.FP else 0.0
                else:
                    PlatformModule.ProgramFail(Parser, "invalid operation")
                ExpressionModule.PushFP(Parser, StackTop, ResultFP)
            elif IS_NUMERIC_COERCIBLE(TopValue):
                ResultInt = 0
                if TopValue.Typ.Base == TypeLong:
                    TopInt = TopValue.Val.LongInteger
                else:
                    TopInt = ExpressionModule.CoerceInteger(TopValue)
                if Op == LexToken.TokenPlus:
                    ResultInt = TopInt
                elif Op == LexToken.TokenMinus:
                    ResultInt = -TopInt
                elif Op == LexToken.TokenIncrement:
                    ResultInt = ExpressionModule.AssignInt(Parser, TopValue, TopInt + 1, False)
                elif Op == LexToken.TokenDecrement:
                    ResultInt = ExpressionModule.AssignInt(Parser, TopValue, TopInt - 1, False)
                elif Op == LexToken.TokenUnaryNot:
                    ResultInt = 1 if not TopInt else 0
                elif Op == LexToken.TokenUnaryExor:
                    ResultInt = ~TopInt
                else:
                    PlatformModule.ProgramFail(Parser, "invalid operation")
                ExpressionModule.PushInt(Parser, StackTop, ResultInt)
            elif TopValue.Typ is not None and TopValue.Typ.Base == TypePointer:
                Size = TypeModule.Size(TopValue.Typ.FromType, 0, True)
                ResultPtr = 0
                if Op != LexToken.TokenUnaryNot and TopValue.Val.Pointer is None:
                    PlatformModule.ProgramFail(Parser, "a. invalid use of a NULL pointer")
                if not TopValue.IsLValue:
                    PlatformModule.ProgramFail(Parser, "can't assign to this")
                if Op == LexToken.TokenIncrement:
                    ResultPtr = (TopValue.Val.Pointer if TopValue.Val.Pointer is not None else 0) + Size
                    TopValue.Val.Pointer = ResultPtr
                elif Op == LexToken.TokenDecrement:
                    ResultPtr = (TopValue.Val.Pointer if TopValue.Val.Pointer is not None else 0) - Size
                    TopValue.Val.Pointer = ResultPtr
                elif Op == LexToken.TokenUnaryNot:
                    ResultPtr = 0 if TopValue.Val.Pointer else 1
                else:
                    PlatformModule.ProgramFail(Parser, "invalid operation")
                StackValue = ExpressionModule.StackPushValueByType(Parser, StackTop, TopValue.Typ)
                StackValue.Val.Pointer = ResultPtr
            else:
                PlatformModule.ProgramFail(Parser, "invalid operation")

    @staticmethod
    def ExpressionPostfixOperator(Parser, StackTop, Op, TopValue):
        from platform_module import PlatformModule
        if TopValue.Typ == Parser.pc.FPType:
            ResultFP = 0.0
            if Op == LexToken.TokenIncrement:
                ResultFP = ExpressionModule.AssignFP(Parser, TopValue, TopValue.Val.FP + 1)
            elif Op == LexToken.TokenDecrement:
                ResultFP = ExpressionModule.AssignFP(Parser, TopValue, TopValue.Val.FP - 1)
            else:
                PlatformModule.ProgramFail(Parser, "invalid operation")
            ExpressionModule.PushFP(Parser, StackTop, ResultFP)
        elif IS_NUMERIC_COERCIBLE(TopValue):
            ResultInt = 0
            TopInt = ExpressionModule.CoerceInteger(TopValue)
            if Op == LexToken.TokenIncrement:
                ResultInt = ExpressionModule.AssignInt(Parser, TopValue, TopInt + 1, True)
            elif Op == LexToken.TokenDecrement:
                ResultInt = ExpressionModule.AssignInt(Parser, TopValue, TopInt - 1, True)
            else:
                PlatformModule.ProgramFail(Parser, "invalid operation")
            ExpressionModule.PushInt(Parser, StackTop, ResultInt)
        elif TopValue.Typ is not None and TopValue.Typ.Base == TypePointer:
            Size = TypeModule.Size(TopValue.Typ.FromType, 0, True)
            OrigPointer = TopValue.Val.Pointer
            if TopValue.Val.Pointer is None:
                PlatformModule.ProgramFail(Parser, "b. invalid use of a NULL pointer")
            if not TopValue.IsLValue:
                PlatformModule.ProgramFail(Parser, "can't assign to this")
            if Op == LexToken.TokenIncrement:
                TopValue.Val.Pointer = (TopValue.Val.Pointer if TopValue.Val.Pointer is not None else 0) + Size
            elif Op == LexToken.TokenDecrement:
                TopValue.Val.Pointer = (TopValue.Val.Pointer if TopValue.Val.Pointer is not None else 0) - Size
            else:
                PlatformModule.ProgramFail(Parser, "invalid operation")
            StackValue = ExpressionModule.StackPushValueByType(Parser, StackTop, TopValue.Typ)
            StackValue.Val.Pointer = OrigPointer
        else:
            PlatformModule.ProgramFail(Parser, "invalid operation")

    @staticmethod
    def ExpressionInfixOperator(Parser, StackTop, Op, BottomValue, TopValue):
        from platform_module import PlatformModule
        if BottomValue is None or TopValue is None:
            PlatformModule.ProgramFail(Parser, "invalid expression")

        if Op == LexToken.TokenLeftSquareBracket:
            if not IS_NUMERIC_COERCIBLE(TopValue):
                PlatformModule.ProgramFail(Parser, "array index must be an integer")
            ArrayIndex = ExpressionModule.CoerceInteger(TopValue)

            if BottomValue.Typ.Base == TypeArray or BottomValue.Typ.Base == TypePointer:
                ElementType = BottomValue.Typ.FromType
                storage = BottomValue.Val
                if BottomValue.Typ.Base == TypePointer and storage is not None:
                    storage = storage.Pointer
                if storage is None or not hasattr(storage, 'Elements') or ArrayIndex < 0 or ArrayIndex >= len(storage.Elements):
                    PlatformModule.ProgramFail(Parser, "array index out of bounds")
                ResultVal = storage.Elements[ArrayIndex]
                Result = Value()
                Result.Typ = ElementType
                Result.Val = ResultVal
                Result.IsLValue = BottomValue.IsLValue
                Result.LValueFrom = BottomValue.LValueFrom if BottomValue.LValueFrom else BottomValue
            else:
                PlatformModule.ProgramFail(Parser, "this is not an array", BottomValue.Typ)
            ExpressionModule.StackPushValueNode(Parser, StackTop, Result)

        elif Op == LexToken.TokenQuestionMark:
            if not IS_NUMERIC_COERCIBLE(TopValue):
                PlatformModule.ProgramFail(Parser, "first argument to '?' should be a number")
            if ExpressionModule.CoerceInteger(TopValue):
                ExpressionModule.StackPushValue(Parser, StackTop, BottomValue)
            else:
                ExpressionModule.StackPushValueByType(Parser, StackTop, Parser.pc.VoidType)

        elif Op == LexToken.TokenColon:
            if TopValue.Typ.Base == TypeVoid:
                ExpressionModule.StackPushValue(Parser, StackTop, BottomValue)
            else:
                ExpressionModule.StackPushValue(Parser, StackTop, TopValue)

        elif (TopValue.Typ == Parser.pc.FPType and BottomValue.Typ == Parser.pc.FPType) or (TopValue.Typ == Parser.pc.FPType and IS_NUMERIC_COERCIBLE(BottomValue)) or (IS_NUMERIC_COERCIBLE(TopValue) and BottomValue.Typ == Parser.pc.FPType):
            ResultIsInt = False
            ResultFP = 0.0
            TopFP = TopValue.Val.FP if TopValue.Typ == Parser.pc.FPType else float(ExpressionModule.CoerceInteger(TopValue))
            BottomFP = BottomValue.Val.FP if BottomValue.Typ == Parser.pc.FPType else float(ExpressionModule.CoerceInteger(BottomValue))

            if Op == LexToken.TokenAssign:
                if IS_FP(BottomValue):
                    ResultFP = ExpressionModule.AssignFP(Parser, BottomValue, TopFP)
                else:
                    ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, int(TopFP), False)
                    ResultIsInt = True
            elif Op == LexToken.TokenAddAssign:
                if IS_FP(BottomValue):
                    ResultFP = ExpressionModule.AssignFP(Parser, BottomValue, BottomFP + TopFP)
                else:
                    ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, int(BottomFP + TopFP), False)
                    ResultIsInt = True
            elif Op == LexToken.TokenSubtractAssign:
                if IS_FP(BottomValue):
                    ResultFP = ExpressionModule.AssignFP(Parser, BottomValue, BottomFP - TopFP)
                else:
                    ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, int(BottomFP - TopFP), False)
                    ResultIsInt = True
            elif Op == LexToken.TokenMultiplyAssign:
                if IS_FP(BottomValue):
                    ResultFP = ExpressionModule.AssignFP(Parser, BottomValue, BottomFP * TopFP)
                else:
                    ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, int(BottomFP * TopFP), False)
                    ResultIsInt = True
            elif Op == LexToken.TokenDivideAssign:
                if IS_FP(BottomValue):
                    ResultFP = ExpressionModule.AssignFP(Parser, BottomValue, BottomFP / TopFP) if TopFP != 0 else 0.0
                else:
                    ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, int(BottomFP / TopFP) if TopFP != 0 else 0, False)
                    ResultIsInt = True
            elif Op == LexToken.TokenEqual:
                ResultInt = 1 if BottomFP == TopFP else 0
                ResultIsInt = True
            elif Op == LexToken.TokenNotEqual:
                ResultInt = 1 if BottomFP != TopFP else 0
                ResultIsInt = True
            elif Op == LexToken.TokenLessThan:
                ResultInt = 1 if BottomFP < TopFP else 0
                ResultIsInt = True
            elif Op == LexToken.TokenGreaterThan:
                ResultInt = 1 if BottomFP > TopFP else 0
                ResultIsInt = True
            elif Op == LexToken.TokenLessEqual:
                ResultInt = 1 if BottomFP <= TopFP else 0
                ResultIsInt = True
            elif Op == LexToken.TokenGreaterEqual:
                ResultInt = 1 if BottomFP >= TopFP else 0
                ResultIsInt = True
            elif Op == LexToken.TokenPlus:
                ResultFP = BottomFP + TopFP
            elif Op == LexToken.TokenMinus:
                ResultFP = BottomFP - TopFP
            elif Op == LexToken.TokenAsterisk:
                ResultFP = BottomFP * TopFP
            elif Op == LexToken.TokenSlash:
                ResultFP = BottomFP / TopFP if TopFP != 0 else 0.0
            else:
                PlatformModule.ProgramFail(Parser, "invalid operation")

            if ResultIsInt:
                ExpressionModule.PushInt(Parser, StackTop, ResultInt)
            else:
                ExpressionModule.PushFP(Parser, StackTop, ResultFP)

        elif IS_NUMERIC_COERCIBLE(TopValue) and IS_NUMERIC_COERCIBLE(BottomValue):
            TopInt = ExpressionModule.CoerceInteger(TopValue)
            BottomInt = ExpressionModule.CoerceInteger(BottomValue)

            if Op == LexToken.TokenAssign:
                ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, TopInt, False)
            elif Op == LexToken.TokenAddAssign:
                ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, BottomInt + TopInt, False)
            elif Op == LexToken.TokenSubtractAssign:
                ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, BottomInt - TopInt, False)
            elif Op == LexToken.TokenMultiplyAssign:
                ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, BottomInt * TopInt, False)
            elif Op == LexToken.TokenDivideAssign:
                ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, int(BottomInt / TopInt) if TopInt != 0 else 0, False)
            elif Op == LexToken.TokenModulusAssign:
                ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, BottomInt % TopInt if TopInt != 0 else 0, False)
            elif Op == LexToken.TokenShiftLeftAssign:
                ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, BottomInt << TopInt, False)
            elif Op == LexToken.TokenShiftRightAssign:
                if BottomValue.Typ.Base in (TypeUnsignedInt, TypeUnsignedLong):
                    ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, (BottomInt & 0xFFFFFFFF) >> (TopInt & 0x1F), False)
                else:
                    ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, BottomInt >> TopInt, False)
            elif Op == LexToken.TokenArithmeticAndAssign:
                ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, BottomInt & TopInt, False)
            elif Op == LexToken.TokenArithmeticOrAssign:
                ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, BottomInt | TopInt, False)
            elif Op == LexToken.TokenArithmeticExorAssign:
                ResultInt = ExpressionModule.AssignInt(Parser, BottomValue, BottomInt ^ TopInt, False)
            elif Op == LexToken.TokenLogicalOr:
                ResultInt = 1 if (BottomInt or TopInt) else 0
            elif Op == LexToken.TokenLogicalAnd:
                ResultInt = 1 if (BottomInt and TopInt) else 0
            elif Op == LexToken.TokenArithmeticOr:
                ResultInt = BottomInt | TopInt
            elif Op == LexToken.TokenArithmeticExor:
                ResultInt = BottomInt ^ TopInt
            elif Op == LexToken.TokenAmpersand:
                ResultInt = BottomInt & TopInt
            elif Op == LexToken.TokenEqual:
                ResultInt = 1 if BottomInt == TopInt else 0
            elif Op == LexToken.TokenNotEqual:
                ResultInt = 1 if BottomInt != TopInt else 0
            elif Op == LexToken.TokenLessThan:
                ResultInt = 1 if BottomInt < TopInt else 0
            elif Op == LexToken.TokenGreaterThan:
                ResultInt = 1 if BottomInt > TopInt else 0
            elif Op == LexToken.TokenLessEqual:
                ResultInt = 1 if BottomInt <= TopInt else 0
            elif Op == LexToken.TokenGreaterEqual:
                ResultInt = 1 if BottomInt >= TopInt else 0
            elif Op == LexToken.TokenShiftLeft:
                ResultInt = BottomInt << TopInt
            elif Op == LexToken.TokenShiftRight:
                ResultInt = BottomInt >> TopInt
            elif Op == LexToken.TokenPlus:
                ResultInt = BottomInt + TopInt
            elif Op == LexToken.TokenMinus:
                ResultInt = BottomInt - TopInt
            elif Op == LexToken.TokenAsterisk:
                ResultInt = BottomInt * TopInt
            elif Op == LexToken.TokenSlash:
                ResultInt = int(BottomInt / TopInt) if TopInt != 0 else 0
            elif Op == LexToken.TokenModulus:
                ResultInt = BottomInt % TopInt if TopInt != 0 else 0
            else:
                PlatformModule.ProgramFail(Parser, "invalid operation")
            ExpressionModule.PushInt(Parser, StackTop, ResultInt)

        elif BottomValue.Typ is not None and BottomValue.Typ.Base == TypePointer and IS_NUMERIC_COERCIBLE(TopValue):
            TopInt = ExpressionModule.CoerceInteger(TopValue)
            if Op in (LexToken.TokenEqual, LexToken.TokenNotEqual):
                if TopInt != 0:
                    PlatformModule.ProgramFail(Parser, "invalid operation")
                if Op == LexToken.TokenEqual:
                    ExpressionModule.PushInt(Parser, StackTop, 1 if BottomValue.Val.Pointer is None else 0)
                else:
                    ExpressionModule.PushInt(Parser, StackTop, 1 if BottomValue.Val.Pointer is not None else 0)
            elif Op in (LexToken.TokenPlus, LexToken.TokenMinus):
                Size = TypeModule.Size(BottomValue.Typ.FromType, 0, True)
                Pointer = BottomValue.Val.Pointer
                if Pointer is None:
                    PlatformModule.ProgramFail(Parser, "c. invalid use of a NULL pointer")
                if Op == LexToken.TokenPlus:
                    Pointer = Pointer + TopInt * Size
                else:
                    Pointer = Pointer - TopInt * Size
                StackValue = ExpressionModule.StackPushValueByType(Parser, StackTop, BottomValue.Typ)
                StackValue.Val.Pointer = Pointer
            elif Op == LexToken.TokenAssign and TopInt == 0:
                ExpressionModule.Assign(Parser, BottomValue, TopValue, False, None, 0, False)
                ExpressionModule.StackPushValueNode(Parser, StackTop, BottomValue)
            elif Op in (LexToken.TokenAddAssign, LexToken.TokenSubtractAssign):
                Size = TypeModule.Size(BottomValue.Typ.FromType, 0, True)
                Pointer = BottomValue.Val.Pointer
                if Pointer is None:
                    PlatformModule.ProgramFail(Parser, "d. invalid use of a NULL pointer")
                if Op == LexToken.TokenAddAssign:
                    Pointer = Pointer + TopInt * Size
                else:
                    Pointer = Pointer - TopInt * Size
                BottomValue.Val.Pointer = Pointer
                ExpressionModule.StackPushValueNode(Parser, StackTop, BottomValue)
            else:
                PlatformModule.ProgramFail(Parser, "invalid operation")

        elif BottomValue.Typ is not None and BottomValue.Typ.Base == TypePointer and TopValue.Typ is not None and TopValue.Typ.Base == TypePointer and Op != LexToken.TokenAssign:
            TopLoc = TopValue.Val.Pointer
            BottomLoc = BottomValue.Val.Pointer
            if Op == LexToken.TokenEqual:
                ExpressionModule.PushInt(Parser, StackTop, 1 if BottomLoc == TopLoc else 0)
            elif Op == LexToken.TokenNotEqual:
                ExpressionModule.PushInt(Parser, StackTop, 1 if BottomLoc != TopLoc else 0)
            elif Op == LexToken.TokenMinus:
                ExpressionModule.PushInt(Parser, StackTop, (BottomLoc - TopLoc) if BottomLoc is not None and TopLoc is not None else 0)
            else:
                PlatformModule.ProgramFail(Parser, "invalid operation")

        elif Op == LexToken.TokenAssign:
            ExpressionModule.Assign(Parser, BottomValue, TopValue, False, None, 0, False)
            ExpressionModule.StackPushValueNode(Parser, StackTop, BottomValue)

        elif Op == LexToken.TokenCast:
            ValueLoc = ExpressionModule.StackPushValueByType(Parser, StackTop, BottomValue.Val.Typ)
            ExpressionModule.Assign(Parser, ValueLoc, TopValue, True, None, 0, True)

        else:
            PlatformModule.ProgramFail(Parser, "invalid operation")

    @staticmethod
    def StackCollapse(Parser, StackTop, Precedence, IgnorePrecedence):
        FoundPrecedence = Precedence
        TopStackNode = StackTop[0]

        while TopStackNode is not None and TopStackNode.Next is not None and FoundPrecedence >= Precedence:
            if TopStackNode.Order == OperatorOrder.OrderNone:
                TopOperatorNode = TopStackNode.Next
            else:
                TopOperatorNode = TopStackNode

            FoundPrecedence = TopOperatorNode.Precedence

            if FoundPrecedence >= Precedence and TopOperatorNode is not None:
                if TopOperatorNode.Order == OperatorOrder.OrderPrefix:
                    TopValue = TopStackNode.Val
                    StackTop[0] = TopOperatorNode.Next
                    if Parser.Mode == RunMode.RunModeRun:
                        ExpressionModule.ExpressionPrefixOperator(Parser, StackTop, TopOperatorNode.Op, TopValue)
                    else:
                        ExpressionModule.PushInt(Parser, StackTop, 0)

                elif TopOperatorNode.Order == OperatorOrder.OrderPostfix:
                    TopValue = TopStackNode.Next.Val
                    StackTop[0] = TopStackNode.Next.Next
                    if Parser.Mode == RunMode.RunModeRun:
                        ExpressionModule.ExpressionPostfixOperator(Parser, StackTop, TopOperatorNode.Op, TopValue)
                    else:
                        ExpressionModule.PushInt(Parser, StackTop, 0)

                elif TopOperatorNode.Order == OperatorOrder.OrderInfix:
                    TopValue = TopStackNode.Val
                    if TopValue is not None:
                        BottomValue = TopOperatorNode.Next.Val
                        StackTop[0] = TopOperatorNode.Next.Next
                        if Parser.Mode == RunMode.RunModeRun:
                            ExpressionModule.ExpressionInfixOperator(Parser, StackTop, TopOperatorNode.Op, BottomValue, TopValue)
                        else:
                            ExpressionModule.PushInt(Parser, StackTop, 0)
                    else:
                        FoundPrecedence = -1
                else:
                    FoundPrecedence = -1

                if FoundPrecedence <= IgnorePrecedence[0]:
                    IgnorePrecedence[0] = DEEP_PRECEDENCE

            TopStackNode = StackTop[0]

    @staticmethod
    def StackPushOperator(Parser, StackTop, Order, Token, Precedence):
        StackNode = ExpressionStack()
        StackNode.Next = StackTop[0]
        StackNode.Order = Order
        StackNode.Op = Token
        StackNode.Precedence = Precedence
        StackTop[0] = StackNode

    @staticmethod
    def GetStructElement(Parser, StackTop, Token):
        Ident = None
        if LexModule.GetToken(Parser, True) != LexToken.TokenIdentifier:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "need an structure or union member after '%s'" % ("." if Token == LexToken.TokenDot else "->"))

        if Parser.Mode == RunMode.RunModeRun:
            ParamVal = StackTop[0].Val
            StructVal = ParamVal
            StructType = ParamVal.Typ
            DerefDataLoc = ParamVal.Val
            MemberValue = None

            if Token == LexToken.TokenArrow:
                DerefType = VariableModule.DereferencePointer(ParamVal)
                StructVal = ParamVal
                StructType = DerefType if DerefType else ParamVal.Typ.FromType

            if StructType.Base not in (TypeStruct, TypeUnion):
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "can't use '%s' on something that's not a struct or union" % ("." if Token == LexToken.TokenDot else "->"))

            ident = Parser.pc.LexValue.Val.Identifier
            MemberValue = TableModule.Get(StructType.Members, ident)
            if MemberValue is None:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "doesn't have a member called '%s'" % ident)

            StackTop[0] = StackTop[0].Next

            offset = MemberValue.Val if isinstance(MemberValue.Val, int) else 0
            Result = VariableModule.AllocValueFromExistingData(Parser, MemberValue.Typ, DerefDataLoc, True, StructVal.LValueFrom if StructVal else None)
            ExpressionModule.StackPushValueNode(Parser, StackTop, Result)

    @staticmethod
    def Parse(Parser, Result):
        PrefixState = True
        Done = False
        BracketPrecedence = 0
        Precedence = 0
        IgnorePrecedence = [DEEP_PRECEDENCE]
        TernaryDepth = 0
        StackTop = [None]

        while not Done:
            PrePos = Parser.Pos
            PreLine = Parser.Line
            PreCharPos = Parser.CharacterPos
            PreHIL = Parser.HashIfLevel
            PreHIETL = Parser.HashIfEvaluateToLevel

            Token = LexModule.GetToken(Parser, True)

            if (LexToken.TokenComma < Token <= LexToken.TokenOpenBracket or (Token == LexToken.TokenCloseBracket and BracketPrecedence != 0)) and (Token != LexToken.TokenColon or TernaryDepth > 0):
                if PrefixState:
                    if OperatorPrecedence[Token].PrefixPrecedence == 0:
                        from platform_module import PlatformModule
                        PlatformModule.ProgramFail(Parser, "operator not expected here")

                    LocalPrecedence = OperatorPrecedence[Token].PrefixPrecedence
                    Precedence = BracketPrecedence + LocalPrecedence

                    if Token == LexToken.TokenOpenBracket:
                        BracketToken = LexModule.GetToken(Parser, False)
                        if ExpressionModule.IsTypeToken(Parser, BracketToken) and (StackTop[0] is None or StackTop[0].Op != LexToken.TokenSizeof):
                            from type_sys import TypeModule
                            CastType = [None]
                            CastIdentifier = [""]
                            TypeModule.Parse(Parser, CastType, CastIdentifier, None)
                            if LexModule.GetToken(Parser, True) != LexToken.TokenCloseBracket:
                                from platform_module import PlatformModule
                                PlatformModule.ProgramFail(Parser, "brackets not closed")
                            Precedence = BracketPrecedence + OperatorPrecedence[LexToken.TokenCast].PrefixPrecedence
                            ExpressionModule.StackCollapse(Parser, StackTop, Precedence + 1, IgnorePrecedence)
                            CastTypeValue = VariableModule.AllocValueFromType(Parser.pc, Parser, Parser.pc.TypeType, False, None, False)
                            CastTypeValue.Val.Typ = CastType[0]
                            ExpressionModule.StackPushValueNode(Parser, StackTop, CastTypeValue)
                            ExpressionModule.StackPushOperator(Parser, StackTop, OperatorOrder.OrderInfix, LexToken.TokenCast, Precedence)
                        else:
                            BracketPrecedence += BRACKET_PRECEDENCE
                    else:
                        NextToken = LexModule.GetToken(Parser, False)
                        TempPrecedenceBoost = 0
                        if NextToken > LexToken.TokenComma and NextToken < LexToken.TokenOpenBracket:
                            NextPrecedence = OperatorPrecedence[NextToken].PrefixPrecedence
                            if LocalPrecedence == NextPrecedence:
                                TempPrecedenceBoost = -1

                        ExpressionModule.StackCollapse(Parser, StackTop, Precedence, IgnorePrecedence)
                        ExpressionModule.StackPushOperator(Parser, StackTop, OperatorOrder.OrderPrefix, Token, Precedence + TempPrecedenceBoost)
                else:
                    if OperatorPrecedence[Token].PostfixPrecedence != 0:
                        if Token in (LexToken.TokenCloseBracket, LexToken.TokenRightSquareBracket):
                            if BracketPrecedence == 0:
                                Parser.Pos = PrePos
                                Parser.Line = PreLine
                                Parser.CharacterPos = PreCharPos
                                Parser.HashIfLevel = PreHIL
                                Parser.HashIfEvaluateToLevel = PreHIETL
                                Done = True
                            else:
                                ExpressionModule.StackCollapse(Parser, StackTop, BracketPrecedence, IgnorePrecedence)
                                BracketPrecedence -= BRACKET_PRECEDENCE
                        else:
                            Precedence = BracketPrecedence + OperatorPrecedence[Token].PostfixPrecedence
                            ExpressionModule.StackCollapse(Parser, StackTop, Precedence, IgnorePrecedence)
                            ExpressionModule.StackPushOperator(Parser, StackTop, OperatorOrder.OrderPostfix, Token, Precedence)

                    elif OperatorPrecedence[Token].InfixPrecedence != 0:
                        Precedence = BracketPrecedence + OperatorPrecedence[Token].InfixPrecedence

                        if IS_LEFT_TO_RIGHT(OperatorPrecedence[Token].InfixPrecedence):
                            ExpressionModule.StackCollapse(Parser, StackTop, Precedence, IgnorePrecedence)
                        else:
                            ExpressionModule.StackCollapse(Parser, StackTop, Precedence + 1, IgnorePrecedence)

                        if Token in (LexToken.TokenDot, LexToken.TokenArrow):
                            ExpressionModule.GetStructElement(Parser, StackTop, Token)
                        else:
                            if Token in (LexToken.TokenLogicalOr, LexToken.TokenLogicalAnd) and StackTop[0] is not None and IS_NUMERIC_COERCIBLE(StackTop[0].Val):
                                LHSInt = ExpressionModule.CoerceInteger(StackTop[0].Val)
                                if ((Token == LexToken.TokenLogicalOr and LHSInt) or (Token == LexToken.TokenLogicalAnd and not LHSInt)) and IgnorePrecedence[0] > Precedence:
                                    IgnorePrecedence[0] = Precedence

                            ExpressionModule.StackPushOperator(Parser, StackTop, OperatorOrder.OrderInfix, Token, Precedence)
                            PrefixState = True

                            if Token == LexToken.TokenQuestionMark:
                                TernaryDepth += 1
                            elif Token == LexToken.TokenColon:
                                TernaryDepth -= 1

                        if Token == LexToken.TokenLeftSquareBracket:
                            BracketPrecedence += BRACKET_PRECEDENCE

                    else:
                        from platform_module import PlatformModule
                        PlatformModule.ProgramFail(Parser, "operator not expected here")

            elif Token == LexToken.TokenIdentifier:
                if not PrefixState:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "identifier not expected here")

                if LexModule.GetToken(Parser, False) == LexToken.TokenOpenBracket:
                    ExpressionModule.ParseFunctionCall(Parser, StackTop, Parser.pc.LexValue.Val.Identifier, Parser.Mode == RunMode.RunModeRun and Precedence < IgnorePrecedence[0])
                else:
                    if Parser.Mode == RunMode.RunModeRun:
                        VariableValue = VariableModule.Get(Parser.pc, Parser, Parser.pc.LexValue.Val.Identifier)
                        if VariableValue.Typ.Base == TypeMacro:
                            MacroParser = ParseState()
                            LexModule.ParserCopy(MacroParser, VariableValue.Val.MacroDef.Body)
                            MacroParser.Mode = Parser.Mode
                            if VariableValue.Val.MacroDef.NumParams != 0:
                                from platform_module import PlatformModule
                                PlatformModule.ProgramFail(Parser, "macro arguments missing")
                            MacroResult = [None]
                            if not ExpressionModule.Parse(MacroParser, MacroResult) or LexModule.GetToken(MacroParser, False) != LexToken.TokenEndOfFunction:
                                from platform_module import PlatformModule
                                PlatformModule.ProgramFail(Parser, "expression expected")
                            ExpressionModule.StackPushValueNode(Parser, StackTop, MacroResult[0])
                        elif VariableValue.Typ == Parser.pc.VoidType:
                            from platform_module import PlatformModule
                            PlatformModule.ProgramFail(Parser, "a void value isn't much use here")
                        else:
                            ExpressionModule.StackPushLValue(Parser, StackTop, VariableValue, 0)
                    else:
                        ExpressionModule.PushInt(Parser, StackTop, 0)

                if Precedence <= IgnorePrecedence[0]:
                    IgnorePrecedence[0] = DEEP_PRECEDENCE

                PrefixState = False

            elif LexToken.TokenCloseBracket < Token <= LexToken.TokenCharacterConstant:
                if not PrefixState:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "value not expected here")
                PrefixState = False
                ExpressionModule.StackPushValue(Parser, StackTop, Parser.pc.LexValue)

            elif ExpressionModule.IsTypeToken(Parser, Token):
                if not PrefixState:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "type not expected here")
                PrefixState = False
                Parser.Pos = PrePos
                Parser.Line = PreLine
                Parser.CharacterPos = PreCharPos
                Parser.HashIfLevel = PreHIL
                Parser.HashIfEvaluateToLevel = PreHIETL
                from type_sys import TypeModule
                Typ = [None]
                Identifier = [""]
                TypeModule.Parse(Parser, Typ, Identifier, None)
                TypeValue = VariableModule.AllocValueFromType(Parser.pc, Parser, Parser.pc.TypeType, False, None, False)
                TypeValue.Val.Typ = Typ[0]
                ExpressionModule.StackPushValueNode(Parser, StackTop, TypeValue)

            else:
                Parser.Pos = PrePos
                Parser.Line = PreLine
                Parser.CharacterPos = PreCharPos
                Parser.HashIfLevel = PreHIL
                Parser.HashIfEvaluateToLevel = PreHIETL
                Done = True

        if BracketPrecedence > 0:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "brackets not closed")

        ExpressionModule.StackCollapse(Parser, StackTop, 0, IgnorePrecedence)

        if StackTop[0] is not None:
            if Parser.Mode == RunMode.RunModeRun:
                if StackTop[0].Order != OperatorOrder.OrderNone or StackTop[0].Next is not None:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "invalid expression")
                Result[0] = StackTop[0].Val
            return True

        return False

    @staticmethod
    def ParseInt(Parser):
        Val = [None]
        if not ExpressionModule.Parse(Parser, Val):
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "expression expected")
        if Parser.Mode == RunMode.RunModeRun:
            if not IS_NUMERIC_COERCIBLE_PLUS_POINTERS(Val[0], True):
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "integer value expected")
            return ExpressionModule.CoerceInteger(Val[0])
        return 0

    @staticmethod
    def ParseFunctionCall(Parser, StackTop, FuncName, RunIt):
        from platform_module import PlatformModule
        Token = LexModule.GetToken(Parser, True)
        OldMode = Parser.Mode
        ReturnValue = None
        FuncValue = None
        ParamArray = None

        if RunIt:
            FuncValue = VariableModule.Get(Parser.pc, Parser, FuncName)
            if FuncValue.Typ.Base == TypeMacro:
                ExpressionModule.ParseMacroCall(Parser, StackTop, FuncName, FuncValue.Val.MacroDef)
                return
            if FuncValue.Typ.Base != TypeFunction:
                PlatformModule.ProgramFail(Parser, "not a function - can't call")
            ReturnValue = ExpressionModule.StackPushValueByType(Parser, StackTop, FuncValue.Val.FuncDef.ReturnType)
            ParamArray = [None] * FuncValue.Val.FuncDef.NumParams
        else:
            ExpressionModule.PushInt(Parser, StackTop, 0)
            Parser.Mode = RunMode.RunModeSkip

        ArgCount = 0
        while True:
            if RunIt:
                if ArgCount < FuncValue.Val.FuncDef.NumParams:
                    ParamArray[ArgCount] = VariableModule.AllocValueFromType(Parser.pc, Parser, FuncValue.Val.FuncDef.ParamType[ArgCount], False, None, False)
                elif FuncValue.Val.FuncDef.VarArgs:
                    ParamArray.append(VariableModule.AllocValueFromType(Parser.pc, Parser, Parser.pc.IntType, False, None, False))

            Param = [None]
            if ExpressionModule.Parse(Parser, Param):
                if RunIt:
                    if ArgCount < FuncValue.Val.FuncDef.NumParams:
                        ExpressionModule.Assign(Parser, ParamArray[ArgCount], Param[0], True, FuncName, ArgCount + 1, False)
                    elif not FuncValue.Val.FuncDef.VarArgs:
                        PlatformModule.ProgramFail(Parser, "too many arguments to %s()" % FuncName)
                    else:
                        ExpressionModule.Assign(Parser, ParamArray[ArgCount], Param[0], True, FuncName, ArgCount + 1, False)
                ArgCount += 1
                Token = LexModule.GetToken(Parser, True)
                if Token not in (LexToken.TokenComma, LexToken.TokenCloseBracket):
                    PlatformModule.ProgramFail(Parser, "comma expected")
            else:
                Token = LexModule.GetToken(Parser, True)
                if Token != LexToken.TokenCloseBracket:
                    PlatformModule.ProgramFail(Parser, "bad argument")

            if Token == LexToken.TokenCloseBracket:
                break

        if RunIt:
            if ArgCount < FuncValue.Val.FuncDef.NumParams:
                PlatformModule.ProgramFail(Parser, "not enough arguments to '%s'" % FuncName)

            if FuncValue.Val.FuncDef.Intrinsic is None:
                OldScopeID = Parser.ScopeID
                FuncParser = ParseState()
                LexModule.ParserCopy(FuncParser, FuncValue.Val.FuncDef.Body)
                FuncParser.TokenList = FuncValue.Val.FuncDef.BodyTokens
                FuncParser.Pos = 0
                VariableModule.StackFrameAdd(Parser, FuncName, 0)
                Parser.pc.TopStackFrame.NumParams = ArgCount
                Parser.pc.TopStackFrame.ReturnValue = ReturnValue
                Parser.ScopeID = -1

                for Count in range(FuncValue.Val.FuncDef.NumParams):
                    VariableModule.Def(Parser.pc, Parser, FuncValue.Val.FuncDef.ParamName[Count], ParamArray[Count], None, True)

                Parser.ScopeID = OldScopeID

                from parse import ParseModule
                if ParseModule.ParseStatement(FuncParser, True) != ParseResult.ParseResultOk:
                    PlatformModule.ProgramFail(FuncParser, "function body expected")

                if FuncParser.Mode == RunMode.RunModeRun and FuncValue.Val.FuncDef.ReturnType != Parser.pc.VoidType:
                    PlatformModule.ProgramFail(FuncParser, "no value returned from a function returning")
                elif FuncParser.Mode == RunMode.RunModeGoto:
                    PlatformModule.ProgramFail(FuncParser, "couldn't find goto label '%s'" % FuncParser.SearchGotoLabel)

                VariableModule.StackFramePop(Parser)
            else:
                FuncValue.Val.FuncDef.Intrinsic(Parser, ReturnValue, ParamArray, ArgCount)

        Parser.Mode = OldMode

    @staticmethod
    def ParseMacroCall(Parser, StackTop, MacroName, MDef):
        from platform_module import PlatformModule
        ReturnValue = None
        ParamArray = None

        if Parser.Mode == RunMode.RunModeRun:
            ExpressionModule.StackPushValueByType(Parser, StackTop, Parser.pc.FPType)
            ReturnValue = StackTop[0].Val
            ParamArray = [None] * MDef.NumParams
        else:
            ExpressionModule.PushInt(Parser, StackTop, 0)

        ArgCount = 0
        while True:
            Param = [None]
            if ExpressionModule.Parse(Parser, Param):
                if Parser.Mode == RunMode.RunModeRun:
                    if ArgCount < MDef.NumParams:
                        ParamArray[ArgCount] = Param[0]
                    else:
                        PlatformModule.ProgramFail(Parser, "too many arguments to %s()" % MacroName)
                ArgCount += 1
                Token = LexModule.GetToken(Parser, True)
                if Token not in (LexToken.TokenComma, LexToken.TokenCloseBracket):
                    PlatformModule.ProgramFail(Parser, "comma expected")
            else:
                Token = LexModule.GetToken(Parser, True)
                if Token != LexToken.TokenCloseBracket:
                    PlatformModule.ProgramFail(Parser, "bad argument")

            if Token == LexToken.TokenCloseBracket:
                break

        if Parser.Mode == RunMode.RunModeRun:
            if ArgCount < MDef.NumParams:
                PlatformModule.ProgramFail(Parser, "not enough arguments to '%s'" % MacroName)
            if MDef.BodyTokens is None:
                PlatformModule.ProgramFail(Parser, "macro '%s' is undefined" % MacroName)

            MacroParser = ParseState()
            LexModule.ParserCopy(MacroParser, MDef.Body)
            MacroParser.TokenList = MDef.BodyTokens
            MacroParser.Pos = 0
            MacroParser.Mode = Parser.Mode
            VariableModule.StackFrameAdd(Parser, MacroName, 0)
            Parser.pc.TopStackFrame.NumParams = ArgCount
            Parser.pc.TopStackFrame.ReturnValue = ReturnValue
            for Count in range(MDef.NumParams):
                VariableModule.Def(Parser.pc, Parser, MDef.ParamName[Count], ParamArray[Count], None, True)

            EvalValue = [None]
            ExpressionModule.Parse(MacroParser, EvalValue)
            ExpressionModule.Assign(Parser, ReturnValue, EvalValue[0], True, MacroName, 0, False)
            VariableModule.StackFramePop(Parser)
