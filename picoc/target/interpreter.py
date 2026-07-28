import sys
from enum import IntEnum

GLOBAL_TABLE_SIZE = 97
STRING_TABLE_SIZE = 97
STRING_LITERAL_TABLE_SIZE = 97
RESERVED_WORD_TABLE_SIZE = 97
PARAMETER_MAX = 16
LINEBUFFER_MAX = 256
LOCAL_TABLE_SIZE = 11
STRUCT_TABLE_SIZE = 11

INTERACTIVE_PROMPT_START = "starting picoc v2.3.2 (Ctrl+D to exit)\n"
INTERACTIVE_PROMPT_STATEMENT = "picoc> "
INTERACTIVE_PROMPT_LINE = "     > "

FREELIST_BUCKETS = 8
SPLIT_MEM_THRESHOLD = 16
BREAKPOINT_TABLE_SIZE = 21
TOKEN_DATA_OFFSET = 2
MAX_TMP_COPY_BUF = 256

class LexToken(IntEnum):
    TokenNone = 0
    TokenComma = 1
    TokenAssign = 2
    TokenAddAssign = 3
    TokenSubtractAssign = 4
    TokenMultiplyAssign = 5
    TokenDivideAssign = 6
    TokenModulusAssign = 7
    TokenShiftLeftAssign = 8
    TokenShiftRightAssign = 9
    TokenArithmeticAndAssign = 10
    TokenArithmeticOrAssign = 11
    TokenArithmeticExorAssign = 12
    TokenQuestionMark = 13
    TokenColon = 14
    TokenLogicalOr = 15
    TokenLogicalAnd = 16
    TokenArithmeticOr = 17
    TokenArithmeticExor = 18
    TokenAmpersand = 19
    TokenEqual = 20
    TokenNotEqual = 21
    TokenLessThan = 22
    TokenGreaterThan = 23
    TokenLessEqual = 24
    TokenGreaterEqual = 25
    TokenShiftLeft = 26
    TokenShiftRight = 27
    TokenPlus = 28
    TokenMinus = 29
    TokenAsterisk = 30
    TokenSlash = 31
    TokenModulus = 32
    TokenIncrement = 33
    TokenDecrement = 34
    TokenUnaryNot = 35
    TokenUnaryExor = 36
    TokenSizeof = 37
    TokenCast = 38
    TokenLeftSquareBracket = 39
    TokenRightSquareBracket = 40
    TokenDot = 41
    TokenArrow = 42
    TokenOpenBracket = 43
    TokenCloseBracket = 44
    TokenIdentifier = 45
    TokenIntegerConstant = 46
    TokenFPConstant = 47
    TokenStringConstant = 48
    TokenCharacterConstant = 49
    TokenSemicolon = 50
    TokenEllipsis = 51
    TokenLeftBrace = 52
    TokenRightBrace = 53
    TokenIntType = 54
    TokenCharType = 55
    TokenFloatType = 56
    TokenDoubleType = 57
    TokenVoidType = 58
    TokenEnumType = 59
    TokenLongType = 60
    TokenSignedType = 61
    TokenShortType = 62
    TokenStaticType = 63
    TokenAutoType = 64
    TokenRegisterType = 65
    TokenExternType = 66
    TokenStructType = 67
    TokenUnionType = 68
    TokenUnsignedType = 69
    TokenTypedef = 70
    TokenContinue = 71
    TokenDo = 72
    TokenElse = 73
    TokenFor = 74
    TokenGoto = 75
    TokenIf = 76
    TokenWhile = 77
    TokenBreak = 78
    TokenSwitch = 79
    TokenCase = 80
    TokenDefault = 81
    TokenReturn = 82
    TokenHashDefine = 83
    TokenHashInclude = 84
    TokenHashIf = 85
    TokenHashIfdef = 86
    TokenHashIfndef = 87
    TokenHashElse = 88
    TokenHashEndif = 89
    TokenNew = 90
    TokenDelete = 91
    TokenOpenMacroBracket = 92
    TokenEOF = 93
    TokenEndOfLine = 94
    TokenEndOfFunction = 95
    TokenBackSlash = 96

class RunMode(IntEnum):
    RunModeRun = 0
    RunModeSkip = 1
    RunModeReturn = 2
    RunModeCaseSearch = 3
    RunModeBreak = 4
    RunModeContinue = 5
    RunModeGoto = 6

class BaseType(IntEnum):
    TypeVoid = 0
    TypeInt = 1
    TypeShort = 2
    TypeChar = 3
    TypeLong = 4
    TypeUnsignedInt = 5
    TypeUnsignedShort = 6
    TypeUnsignedChar = 7
    TypeUnsignedLong = 8
    TypeFP = 9
    TypeFunction = 10
    TypeMacro = 11
    TypePointer = 12
    TypeArray = 13
    TypeStruct = 14
    TypeUnion = 15
    TypeEnum = 16
    TypeGotoLabel = 17
    Type_Type = 18

TypeVoid = BaseType.TypeVoid
TypeInt = BaseType.TypeInt
TypeShort = BaseType.TypeShort
TypeChar = BaseType.TypeChar
TypeLong = BaseType.TypeLong
TypeUnsignedInt = BaseType.TypeUnsignedInt
TypeUnsignedShort = BaseType.TypeUnsignedShort
TypeUnsignedChar = BaseType.TypeUnsignedChar
TypeUnsignedLong = BaseType.TypeUnsignedLong
TypeFP = BaseType.TypeFP
TypeFunction = BaseType.TypeFunction
TypeMacro = BaseType.TypeMacro
TypePointer = BaseType.TypePointer
TypeArray = BaseType.TypeArray
TypeStruct = BaseType.TypeStruct
TypeUnion = BaseType.TypeUnion
TypeEnum = BaseType.TypeEnum
TypeGotoLabel = BaseType.TypeGotoLabel
Type_Type = BaseType.Type_Type

class LexMode(IntEnum):
    LexModeNormal = 0
    LexModeHashInclude = 1
    LexModeHashDefine = 2
    LexModeHashDefineSpace = 3
    LexModeHashDefineSpaceIdent = 4

class ParseResult(IntEnum):
    ParseResultEOF = 0
    ParseResultError = 1
    ParseResultOk = 2

class OperatorOrder(IntEnum):
    OrderNone = 0
    OrderPrefix = 1
    OrderInfix = 2
    OrderPostfix = 3

class StdOutStream:
    def __init__(self, file_ptr=None, str_out_ptr=None, str_out_len=0, char_count=0):
        self.FilePtr = file_ptr
        self.StrOutPtr = str_out_ptr
        self.StrOutLen = str_out_len
        self.CharCount = char_count

class StdVararg:
    def __init__(self, param=None, num_args=0):
        self.Param = param
        self.NumArgs = num_args

class FuncDef:
    def __init__(self):
        self.ReturnType = None
        self.NumParams = 0
        self.VarArgs = False
        self.ParamType = []
        self.ParamName = []
        self.Intrinsic = None
        self.Body = None
        self.BodyTokens = None

class MacroDef:
    def __init__(self):
        self.NumParams = 0
        self.ParamName = []
        self.Body = None
        self.BodyTokens = None

class ValueType:
    def __init__(self):
        self.Base = BaseType.TypeVoid
        self.ArraySize = 0
        self.Sizeof = 0
        self.AlignBytes = 0
        self.Identifier = ""
        self.FromType = None
        self.DerivedTypeList = None
        self.Next = None
        self.Members = None
        self.OnHeap = False
        self.StaticQualifier = False

class Value:
    def __init__(self):
        self.Typ = None
        self.Val = None
        self.LValueFrom = None
        self.ValOnHeap = False
        self.ValOnStack = False
        self.AnyValOnHeap = False
        self.IsLValue = False
        self.ScopeID = 0
        self.OutOfScope = False
        self.RawData = None

class TableEntry:
    def __init__(self):
        self.Next = None
        self.DeclFileName = None
        self.DeclLine = 0
        self.DeclColumn = 0
        self.Key = ""
        self.Val = None

class Table:
    def __init__(self):
        self.Size = 0
        self.OnHeap = False
        self.entries = {}

class StackFrame:
    def __init__(self):
        self.ReturnParser = None
        self.FuncName = ""
        self.ReturnValue = None
        self.Parameter = []
        self.NumParams = 0
        self.LocalTable = None
        self.PreviousStackFrame = None

class LexState:
    def __init__(self):
        self.Pos = 0
        self.Source = ""
        self.End = 0
        self.FileName = ""
        self.Line = 0
        self.CharacterPos = 0
        self.SourceText = ""
        self.Mode = LexMode.LexModeNormal
        self.EmitExtraNewlines = 0

class ParseState:
    def __init__(self):
        self.pc = None
        self.Pos = 0
        self.TokenList = None
        self.FileName = ""
        self.Line = 0
        self.CharacterPos = 0
        self.Mode = RunMode.RunModeRun
        self.SearchLabel = 0
        self.SearchGotoLabel = ""
        self.SourceText = ""
        self.HashIfLevel = 0
        self.HashIfEvaluateToLevel = 0
        self.DebugMode = False
        self.ScopeID = 0

class LibraryFunction:
    def __init__(self, func=None, prototype=""):
        self.Func = func
        self.Prototype = prototype

class IncludeLibrary:
    def __init__(self):
        self.IncludeName = ""
        self.SetupFunction = None
        self.FuncList = None
        self.SetupCSource = None
        self.NextLib = None

class CleanupTokenNode:
    def __init__(self):
        self.Tokens = None
        self.SourceText = None
        self.Next = None

class TokenLine:
    def __init__(self):
        self.Next = None
        self.Tokens = None
        self.NumBytes = 0

class ExpressionStack:
    def __init__(self):
        self.Next = None
        self.Val = None
        self.Op = LexToken.TokenNone
        self.Precedence = 0
        self.Order = OperatorOrder.OrderNone

class OpPrecedence:
    def __init__(self, prefix=0, postfix=0, infix=0, name=""):
        self.PrefixPrecedence = prefix
        self.PostfixPrecedence = postfix
        self.InfixPrecedence = infix
        self.Name = name

class ReservedWord:
    def __init__(self, word="", token=LexToken.TokenNone):
        self.Word = word
        self.Token = token

class AnyValue:
    def __init__(self):
        self.Integer = 0
        self.Pointer = None
        self.Identifier = ""
        self.Character = 0
        self.ShortInteger = 0
        self.LongInteger = 0
        self.UnsignedInteger = 0
        self.UnsignedShortInteger = 0
        self.UnsignedLongInteger = 0
        self.UnsignedCharacter = 0
        self.FP = 0.0
        self.FuncDef = None
        self.MacroDef = None

class Picoc:
    def __init__(self):
        self.GlobalTable = Table()
        self.CleanupTokenList = None
        self.InteractiveHead = None
        self.InteractiveTail = None
        self.InteractiveCurrentLine = None
        self.LexUseStatementPrompt = False
        self.LexValue = Value()
        self.ReservedWordTable = Table()
        self.StringLiteralTable = Table()
        self.TopStackFrame = None
        self.PicocExitValue = 0
        self.IncludeLibList = None
        self.HeapBottom = 0
        self.StackFramePos = 0
        self.HeapStackTop = 0
        self.UberType = ValueType()
        self.IntType = ValueType()
        self.ShortType = ValueType()
        self.CharType = ValueType()
        self.LongType = ValueType()
        self.UnsignedIntType = ValueType()
        self.UnsignedShortType = ValueType()
        self.UnsignedLongType = ValueType()
        self.UnsignedCharType = ValueType()
        self.FPType = ValueType()
        self.VoidType = ValueType()
        self.TypeType = ValueType()
        self.FunctionType = ValueType()
        self.MacroType = ValueType()
        self.EnumType = ValueType()
        self.GotoLabelType = ValueType()
        self.CharPtrType = None
        self.CharPtrPtrType = None
        self.CharArrayType = None
        self.VoidPtrType = None
        self.BreakpointTable = Table()
        self.BreakpointCount = 0
        self.DebugManualBreak = False
        self.BigEndian = False
        self.LittleEndian = False
        self.CStdOut = sys.stdout
        self.VersionString = ""
        self.PicocExitBuf = None
        self.StringTable = Table()
        self.StrEmpty = ""
        self.ScopeCounter = 0
