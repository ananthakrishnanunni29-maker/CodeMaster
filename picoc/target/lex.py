from interpreter import *
from table import TableModule

ReservedWords = [
    ReservedWord("#define", LexToken.TokenHashDefine),
    ReservedWord("#else", LexToken.TokenHashElse),
    ReservedWord("#endif", LexToken.TokenHashEndif),
    ReservedWord("#if", LexToken.TokenHashIf),
    ReservedWord("#ifdef", LexToken.TokenHashIfdef),
    ReservedWord("#ifndef", LexToken.TokenHashIfndef),
    ReservedWord("#include", LexToken.TokenHashInclude),
    ReservedWord("auto", LexToken.TokenAutoType),
    ReservedWord("break", LexToken.TokenBreak),
    ReservedWord("case", LexToken.TokenCase),
    ReservedWord("char", LexToken.TokenCharType),
    ReservedWord("continue", LexToken.TokenContinue),
    ReservedWord("default", LexToken.TokenDefault),
    ReservedWord("delete", LexToken.TokenDelete),
    ReservedWord("do", LexToken.TokenDo),
    ReservedWord("double", LexToken.TokenDoubleType),
    ReservedWord("else", LexToken.TokenElse),
    ReservedWord("enum", LexToken.TokenEnumType),
    ReservedWord("extern", LexToken.TokenExternType),
    ReservedWord("float", LexToken.TokenFloatType),
    ReservedWord("for", LexToken.TokenFor),
    ReservedWord("goto", LexToken.TokenGoto),
    ReservedWord("if", LexToken.TokenIf),
    ReservedWord("int", LexToken.TokenIntType),
    ReservedWord("long", LexToken.TokenLongType),
    ReservedWord("new", LexToken.TokenNew),
    ReservedWord("register", LexToken.TokenRegisterType),
    ReservedWord("return", LexToken.TokenReturn),
    ReservedWord("short", LexToken.TokenShortType),
    ReservedWord("signed", LexToken.TokenSignedType),
    ReservedWord("sizeof", LexToken.TokenSizeof),
    ReservedWord("static", LexToken.TokenStaticType),
    ReservedWord("struct", LexToken.TokenStructType),
    ReservedWord("switch", LexToken.TokenSwitch),
    ReservedWord("typedef", LexToken.TokenTypedef),
    ReservedWord("union", LexToken.TokenUnionType),
    ReservedWord("unsigned", LexToken.TokenUnsignedType),
    ReservedWord("void", LexToken.TokenVoidType),
    ReservedWord("while", LexToken.TokenWhile),
]

def isCidstart(c):
    return c.isalpha() or c == '_' or c == '#'

def isCident(c):
    return c.isalnum() or c == '_' or c == '#'

class LexModule:
    @staticmethod
    def Init(pc):
        for rw in ReservedWords:
            TableModule.Set(pc, pc.ReservedWordTable, TableModule.StrRegister(pc, rw.Word), rw, None, 0, 0)
        pc.LexValue.Typ = None
        pc.LexValue.IsLValue = False

    @staticmethod
    def Cleanup(pc):
        LexModule.InteractiveClear(pc, None)
        for rw in ReservedWords:
            TableModule.Delete(pc, pc.ReservedWordTable, TableModule.StrRegister(pc, rw.Word))

    @staticmethod
    def CheckReservedWord(pc, Word):
        val = TableModule.Get(pc.ReservedWordTable, Word)
        if val is not None:
            return val.Token
        return LexToken.TokenNone

    @staticmethod
    def LexGetNumber(Lexer, Value):
        pc = None
        Result = 0
        Base = 10
        Source = Lexer.Source
        pos = Lexer.Pos
        end = Lexer.End

        if pos < end and Source[pos] == '0':
            pos += 1
            Lexer.CharacterPos += 1
            if pos < end:
                if Source[pos] in ('x', 'X'):
                    Base = 16
                    pos += 1
                    Lexer.CharacterPos += 1
                elif Source[pos] in ('b', 'B'):
                    Base = 2
                    pos += 1
                    Lexer.CharacterPos += 1
                elif Source[pos] != '.':
                    Base = 8

        while pos < end:
            c = Source[pos]
            if c.isdigit():
                val = ord(c) - ord('0')
                if val < Base:
                    Result = Result * Base + val
                    pos += 1
                    Lexer.CharacterPos += 1
                    continue
            elif Base > 10 and 'a' <= c <= 'f':
                Result = Result * Base + (ord(c) - ord('a') + 10)
                pos += 1
                Lexer.CharacterPos += 1
                continue
            elif Base > 10 and 'A' <= c <= 'F':
                Result = Result * Base + (ord(c) - ord('A') + 10)
                pos += 1
                Lexer.CharacterPos += 1
                continue
            break

        if pos < end and Source[pos] in ('u', 'U'):
            pos += 1
            Lexer.CharacterPos += 1
        if pos < end and Source[pos] in ('l', 'L'):
            pos += 1
            Lexer.CharacterPos += 1

        Lexer.Pos = pos

        if pos >= end or (Source[pos] != '.' and Source[pos] != 'e' and Source[pos] != 'E'):
            Value.Val = AnyValue()
            Value.Val.LongInteger = Result
            Value.Typ = None
            return LexToken.TokenIntegerConstant

        FPResult = float(Result)
        if pos < end and Source[pos] == '.':
            pos += 1
            Lexer.CharacterPos += 1
            FPDiv = 1.0 / Base
            while pos < end:
                c = Source[pos]
                if c.isdigit():
                    val = ord(c) - ord('0')
                    if val < Base:
                        FPResult += val * FPDiv
                        FPDiv /= Base
                        pos += 1
                        Lexer.CharacterPos += 1
                        continue
                elif Base > 10 and 'a' <= c <= 'f':
                    FPResult += (ord(c) - ord('a') + 10) * FPDiv
                    FPDiv /= Base
                    pos += 1
                    Lexer.CharacterPos += 1
                    continue
                elif Base > 10 and 'A' <= c <= 'F':
                    FPResult += (ord(c) - ord('A') + 10) * FPDiv
                    FPDiv /= Base
                    pos += 1
                    Lexer.CharacterPos += 1
                    continue
                break

        if pos < end and Source[pos] in ('e', 'E'):
            pos += 1
            Lexer.CharacterPos += 1
            ExponentSign = 1
            if pos < end and Source[pos] == '-':
                ExponentSign = -1
                pos += 1
                Lexer.CharacterPos += 1
            ExpResult = 0
            while pos < end and Source[pos].isdigit():
                ExpResult = ExpResult * 10 + (ord(Source[pos]) - ord('0'))
                pos += 1
                Lexer.CharacterPos += 1
            FPResult *= pow(float(Base), float(ExpResult) * ExponentSign)

        if pos < end and Source[pos] in ('f', 'F'):
            pos += 1
            Lexer.CharacterPos += 1

        Lexer.Pos = pos
        Value.Val = AnyValue()
        Value.Val.FP = FPResult
        Value.Typ = None
        return LexToken.TokenFPConstant

    @staticmethod
    def LexGetWord(Lexer, Value):
        pc = Lexer.pc if hasattr(Lexer, 'pc') and Lexer.pc else None
        Source = Lexer.Source
        pos = Lexer.Pos
        start_pos = pos
        end = Lexer.End

        while pos < end and isCident(Source[pos]):
            pos += 1
            Lexer.CharacterPos += 1

        Lexer.Pos = pos
        word = Source[start_pos:pos]

        Value.Val = AnyValue()
        Value.Val.Identifier = TableModule.StrRegister2(pc, word, len(word))

        LexModule._check_reserved_word_mode(Value, word, Lexer)

        token = LexModule.CheckReservedWord(pc, word)
        if token != LexToken.TokenNone:
            return token

        if Lexer.Mode == LexMode.LexModeHashDefineSpace:
            Lexer.Mode = LexMode.LexModeHashDefineSpaceIdent

        return LexToken.TokenIdentifier

    @staticmethod
    def _check_reserved_word_mode(Value, word, Lexer):
        if word == "#include":
            Lexer.Mode = LexMode.LexModeHashInclude
        elif word == "#define":
            Lexer.Mode = LexMode.LexModeHashDefine

    @staticmethod
    def LexUnEscapeCharacterConstant(From, FirstChar, Base):
        Total = int(FirstChar, Base) if isinstance(FirstChar, str) else FirstChar
        count = 0
        source = From[0]
        pos = From[1]
        end = source
        while pos < len(source):
            c = source[pos]
            if c.isdigit():
                val = ord(c) - ord('0')
                if val < Base:
                    Total = Total * Base + val
                    pos += 1
                    count += 1
                    if count >= 2:
                        break
                    continue
            elif Base > 10 and 'a' <= c <= 'f':
                Total = Total * Base + (ord(c) - ord('a') + 10)
                pos += 1
                count += 1
                if count >= 2:
                    break
                continue
            elif Base > 10 and 'A' <= c <= 'F':
                Total = Total * Base + (ord(c) - ord('A') + 10)
                pos += 1
                count += 1
                if count >= 2:
                    break
                continue
            break
        From[1] = pos
        return Total

    @staticmethod
    def LexUnEscapeCharacter(From, End):
        source = From[0]
        pos = From[1]

        while pos < len(source) and source[pos] == '\\' and pos + 1 < len(source) and source[pos + 1] == '\n':
            pos += 2
        while pos < len(source) and source[pos] == '\\' and pos + 2 < len(source) and source[pos + 1] == '\r' and source[pos + 2] == '\n':
            pos += 3

        if pos >= len(source):
            From[1] = pos
            return ord('\\')

        if source[pos] == '\\':
            pos += 1
            if pos >= len(source):
                From[1] = pos
                return ord('\\')
            ch = source[pos]
            pos += 1
            escape_map = {
                '\\': '\\', '\'': '\'', '"': '"', 'a': '\a',
                'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r',
                't': '\t', 'v': '\v',
            }
            if ch in escape_map:
                From[1] = pos
                return ord(escape_map[ch])
            if ch in '0123':
                From[1] = pos
                return LexModule.LexUnEscapeCharacterConstant(From, ch, 8)
            if ch == 'x':
                From[1] = pos
                return LexModule.LexUnEscapeCharacterConstant(From, '0', 16)
            From[1] = pos
            return ord(ch)
        else:
            ch = source[pos]
            pos += 1
            From[1] = pos
            return ord(ch)

    @staticmethod
    def LexGetStringConstant(Lexer, Value, EndChar):
        pc = Lexer.pc if hasattr(Lexer, 'pc') else None
        Source = Lexer.Source
        pos = Lexer.Pos
        end = Lexer.End
        start = pos

        Escape = False
        while pos < end:
            ch = Source[pos]
            if ch == EndChar and not Escape:
                break
            if Escape:
                if ch == '\r' and pos + 1 < end:
                    pos += 1
                if ch == '\n' and pos + 1 < end:
                    Lexer.Line += 1
                    pos += 1
                    Lexer.CharacterPos = 0
                    Lexer.EmitExtraNewlines += 1
                Escape = False
            elif ch == '\\':
                Escape = True
            pos += 1
            Lexer.CharacterPos += 1

        end_pos = pos
        result_bytes = bytearray()
        pos = start
        while pos < end_pos:
            From = [Source, pos]
            result_bytes.append(LexModule.LexUnEscapeCharacter(From, end_pos))
            pos = From[1]

        RegString = TableModule.StrRegister2(pc, result_bytes.decode('latin-1', errors='replace'), len(result_bytes))

        Value.Val = AnyValue()
        Value.Val.Pointer = RegString
        Value.Typ = None

        if pos < end and Source[pos] == EndChar:
            pos += 1
            Lexer.CharacterPos += 1

        Lexer.Pos = pos
        return LexToken.TokenStringConstant

    @staticmethod
    def LexGetCharacterConstant(Lexer, Value):
        Source = Lexer.Source
        From = [Source, Lexer.Pos]
        ch = LexModule.LexUnEscapeCharacter(From, Lexer.End)
        Lexer.Pos = From[1]
        Lexer.CharacterPos += 1

        Value.Val = AnyValue()
        Value.Val.Character = ch

        if Lexer.Pos < Lexer.End and Source[Lexer.Pos] != '\'':
            pass
        if Lexer.Pos < Lexer.End:
            Lexer.Pos += 1
            Lexer.CharacterPos += 1

        return LexToken.TokenCharacterConstant

    @staticmethod
    def LexSkipComment(Lexer, NextChar):
        Source = Lexer.Source
        pos = Lexer.Pos
        end = Lexer.End

        if NextChar == '*':
            while pos < end:
                if pos > 0 and Source[pos - 1] == '*' and Source[pos] == '/':
                    pos += 1
                    break
                if pos < end and Source[pos] == '\n':
                    Lexer.EmitExtraNewlines += 1
                pos += 1
                Lexer.CharacterPos += 1
            if pos < end:
                pos += 1
                Lexer.CharacterPos += 1
            Lexer.Mode = LexMode.LexModeNormal
        else:
            while pos < end and Source[pos] != '\n':
                pos += 1
                Lexer.CharacterPos += 1

        Lexer.Pos = pos

    @staticmethod
    def LexScanGetToken(Lexer, _ignored):
        Value = Lexer.pc.LexValue
        Source = Lexer.Source
        pos = Lexer.Pos
        end = Lexer.End

        if Lexer.EmitExtraNewlines > 0:
            Lexer.EmitExtraNewlines -= 1
            return LexToken.TokenEndOfLine

        if Lexer.Mode == LexMode.LexModeHashInclude:
            include_start = pos
            while pos < end and Source[pos].isspace():
                pos += 1
                Lexer.CharacterPos += 1
            delim = Source[pos] if pos < end else None
            if delim == '<':
                pos += 1
                Lexer.CharacterPos += 1
                while pos < end and Source[pos] != '>':
                    pos += 1
                    Lexer.CharacterPos += 1
                if pos < end and Source[pos] == '>':
                    pos += 1
                    Lexer.CharacterPos += 1
            elif delim == '"':
                pos += 1
                Lexer.CharacterPos += 1
                while pos < end and Source[pos] != '"':
                    pos += 1
                    Lexer.CharacterPos += 1
                if pos < end and Source[pos] == '"':
                    pos += 1
                    Lexer.CharacterPos += 1
            else:
                while pos < end and Source[pos] not in ('\n', '\0'):
                    pos += 1
                    Lexer.CharacterPos += 1
            inc_name = Source[include_start:pos].strip()
            if inc_name.startswith('<') and inc_name.endswith('>'):
                inc_name = inc_name[1:-1]
            elif inc_name.startswith('"') and inc_name.endswith('"'):
                inc_name = inc_name[1:-1]
            Lexer.Pos = pos
            Lexer.Mode = LexMode.LexModeNormal
            Value.Val = AnyValue()
            Value.Val.Identifier = TableModule.StrRegister2(Lexer.pc, inc_name, len(inc_name))
            return LexToken.TokenIdentifier

        while True:
            while pos < end and Source[pos].isspace():
                if Source[pos] == '\n':
                    Lexer.Line += 1
                    pos += 1
                    Lexer.Mode = LexMode.LexModeNormal
                    Lexer.CharacterPos = 0
                    Lexer.Pos = pos
                    return LexToken.TokenEndOfLine
                elif Lexer.Mode in (LexMode.LexModeHashDefine, LexMode.LexModeHashDefineSpace):
                    Lexer.Mode = LexMode.LexModeHashDefineSpace
                elif Lexer.Mode == LexMode.LexModeHashDefineSpaceIdent:
                    Lexer.Mode = LexMode.LexModeNormal
                pos += 1
                Lexer.CharacterPos += 1

            if pos >= end or (pos < end and Source[pos] == '\0'):
                Lexer.Pos = pos
                return LexToken.TokenEOF

            ThisChar = Source[pos]
            Lexer.Pos = pos

            if isCidstart(ThisChar):
                Lexer.Pos = pos
                return LexModule.LexGetWord(Lexer, Value)

            if ThisChar.isdigit():
                Lexer.Pos = pos
                return LexModule.LexGetNumber(Lexer, Value)

            NextChar = Source[pos + 1] if pos + 1 < end else '\0'
            pos += 1
            Lexer.CharacterPos += 1
            Lexer.Pos = pos

            if ThisChar == '"':
                Lexer.Pos = pos
                return LexModule.LexGetStringConstant(Lexer, Value, '"')
            elif ThisChar == '\'':
                Lexer.Pos = pos
                return LexModule.LexGetCharacterConstant(Lexer, Value)
            elif ThisChar == '(':
                if Lexer.Mode == LexMode.LexModeHashDefineSpaceIdent:
                    Lexer.Mode = LexMode.LexModeNormal
                    return LexToken.TokenOpenMacroBracket
                return LexToken.TokenOpenBracket
            elif ThisChar == ')':
                return LexToken.TokenCloseBracket
            elif ThisChar == '=':
                return LexToken.TokenEqual if NextChar == '=' else LexToken.TokenAssign
            elif ThisChar == '+':
                if NextChar == '=':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenAddAssign
                elif NextChar == '+':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenIncrement
                return LexToken.TokenPlus
            elif ThisChar == '-':
                if NextChar == '=':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenSubtractAssign
                elif NextChar == '>':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenArrow
                elif NextChar == '-':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenDecrement
                return LexToken.TokenMinus
            elif ThisChar == '*':
                if NextChar == '=':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenMultiplyAssign
                return LexToken.TokenAsterisk
            elif ThisChar == '/':
                if NextChar == '/' or NextChar == '*':
                    pos += 1; Lexer.CharacterPos += 1;
                    Lexer.Pos = pos
                    LexModule.LexSkipComment(Lexer, NextChar)
                    pos = Lexer.Pos
                    continue
                elif NextChar == '=':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenDivideAssign
                return LexToken.TokenSlash
            elif ThisChar == '%':
                if NextChar == '=':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenModulusAssign
                return LexToken.TokenModulus
            elif ThisChar == '<':
                if Lexer.Mode == LexMode.LexModeHashInclude:
                    Lexer.Pos = pos
                    return LexModule.LexGetStringConstant(Lexer, Value, '>')
                elif NextChar == '=':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenLessEqual
                elif NextChar == '<':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos
                    if pos < end and Source[pos] == '=':
                        pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenShiftLeftAssign
                    return LexToken.TokenShiftLeft
                return LexToken.TokenLessThan
            elif ThisChar == '>':
                if NextChar == '=':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenGreaterEqual
                elif NextChar == '>':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos
                    if pos < end and Source[pos] == '=':
                        pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenShiftRightAssign
                    return LexToken.TokenShiftRight
                return LexToken.TokenGreaterThan
            elif ThisChar == ';':
                return LexToken.TokenSemicolon
            elif ThisChar == '&':
                if NextChar == '=':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenArithmeticAndAssign
                elif NextChar == '&':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenLogicalAnd
                return LexToken.TokenAmpersand
            elif ThisChar == '|':
                if NextChar == '=':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenArithmeticOrAssign
                elif NextChar == '|':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenLogicalOr
                return LexToken.TokenArithmeticOr
            elif ThisChar == '{':
                return LexToken.TokenLeftBrace
            elif ThisChar == '}':
                return LexToken.TokenRightBrace
            elif ThisChar == '[':
                return LexToken.TokenLeftSquareBracket
            elif ThisChar == ']':
                return LexToken.TokenRightSquareBracket
            elif ThisChar == '!':
                if NextChar == '=':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenNotEqual
                return LexToken.TokenUnaryNot
            elif ThisChar == '^':
                if NextChar == '=':
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos; return LexToken.TokenArithmeticExorAssign
                return LexToken.TokenArithmeticExor
            elif ThisChar == '~':
                return LexToken.TokenUnaryExor
            elif ThisChar == ',':
                return LexToken.TokenComma
            elif ThisChar == '.':
                if NextChar == '.' and pos + 1 < end and Source[pos + 1] == '.':
                    pos += 2; Lexer.CharacterPos += 2; Lexer.Pos = pos; return LexToken.TokenEllipsis
                return LexToken.TokenDot
            elif ThisChar == '?':
                return LexToken.TokenQuestionMark
            elif ThisChar == ':':
                return LexToken.TokenColon
            elif ThisChar == '\\':
                if NextChar in (' ', '\n'):
                    pos += 1; Lexer.CharacterPos += 1; Lexer.Pos = pos
                    while pos < end and Source[pos] != '\n':
                        pos += 1; Lexer.CharacterPos += 1
                    Lexer.Pos = pos
                    continue
                from platform_module import PlatformModule
                PlatformModule.LexFail(None, Lexer, "illegal character '\\'")
                return LexToken.TokenNone
            else:
                from platform_module import PlatformModule
                PlatformModule.LexFail(None, Lexer, "illegal character '%c'" % ThisChar)
                return LexToken.TokenNone

    @staticmethod
    def LexTokenSize(Token):
        if Token in (LexToken.TokenIdentifier, LexToken.TokenStringConstant):
            return 8
        if Token == LexToken.TokenIntegerConstant:
            return 8
        if Token == LexToken.TokenCharacterConstant:
            return 1
        if Token == LexToken.TokenFPConstant:
            return 8
        return 0

    @staticmethod
    def LexTokenize(Lexer):
        tokens = []
        while True:
            pos_before = Lexer.Pos
            charpos = Lexer.CharacterPos
            Token = LexModule.LexScanGetToken(Lexer, None)
            val = None
            if Token in (LexToken.TokenIdentifier, LexToken.TokenStringConstant):
                if Lexer.pc and Lexer.pc.LexValue and Lexer.pc.LexValue.Val:
                    val = Lexer.pc.LexValue.Val.Identifier if Token == LexToken.TokenIdentifier else Lexer.pc.LexValue.Val.Pointer
            elif Token == LexToken.TokenIntegerConstant:
                if Lexer.pc and Lexer.pc.LexValue and Lexer.pc.LexValue.Val:
                    val = Lexer.pc.LexValue.Val.LongInteger
            elif Token == LexToken.TokenFPConstant:
                if Lexer.pc and Lexer.pc.LexValue and Lexer.pc.LexValue.Val:
                    val = Lexer.pc.LexValue.Val.FP
            elif Token == LexToken.TokenCharacterConstant:
                if Lexer.pc and Lexer.pc.LexValue and Lexer.pc.LexValue.Val:
                    val = Lexer.pc.LexValue.Val.Character
            tokens.append((Token, charpos, val))
            if Token == LexToken.TokenEOF:
                break
        return tokens

    @staticmethod
    def LexAnalyze(pc, FileName, Source, SourceLen, TokenLen):
        Lexer = LexState()
        Lexer.pc = pc
        Lexer.Source = Source
        Lexer.Pos = 0
        Lexer.End = SourceLen
        Lexer.Line = 1
        Lexer.FileName = FileName
        Lexer.Mode = LexMode.LexModeNormal
        Lexer.EmitExtraNewlines = 0
        Lexer.CharacterPos = 1
        Lexer.SourceText = Source

        tokens = LexModule.LexTokenize(Lexer)
        if TokenLen is not None:
            TokenLen[0] = len(tokens)
        return tokens

    @staticmethod
    def LexInitParser(Parser, pc, SourceText, TokenSource, FileName, RunIt, EnableDebugger):
        Parser.pc = pc
        Parser.TokenList = TokenSource
        Parser.Pos = 0
        Parser.Line = 1
        Parser.FileName = FileName
        Parser.Mode = RunMode.RunModeRun if RunIt else RunMode.RunModeSkip
        Parser.SearchLabel = 0
        Parser.HashIfLevel = 0
        Parser.HashIfEvaluateToLevel = 0
        Parser.CharacterPos = 0
        Parser.SourceText = SourceText
        Parser.DebugMode = EnableDebugger

    @staticmethod
    def LexGetRawToken(Parser, IncPos):
        Token = LexToken.TokenNone
        pc = Parser.pc

        while True:
            if Parser.TokenList is None and pc.InteractiveHead is not None:
                Parser.TokenList = pc.InteractiveHead.Tokens
                Parser.Pos = 0

            if Parser.FileName != pc.StrEmpty or pc.InteractiveHead is not None:
                while Parser.Pos < len(Parser.TokenList):
                    Token = Parser.TokenList[Parser.Pos][0]
                    if Token != LexToken.TokenEndOfLine:
                        break
                    Parser.Line += 1
                    Parser.Pos += 1

            if Parser.FileName == pc.StrEmpty and (pc.InteractiveHead is None or Token == LexToken.TokenEOF):
                import platform_module as pm
                LineBuffer = [None] * LINEBUFFER_MAX
                if pc.InteractiveHead is None or (Parser.Pos >= len(Parser.TokenList) - 1 and len(Parser.TokenList) > 0 and Parser.TokenList[-1][0] == LexToken.TokenEOF):
                    if pc.LexUseStatementPrompt:
                        Prompt = INTERACTIVE_PROMPT_STATEMENT
                        pc.LexUseStatementPrompt = False
                    else:
                        Prompt = INTERACTIVE_PROMPT_LINE

                    line = pm.PlatformModule.GetLine(LINEBUFFER_MAX, Prompt)
                    if line is None:
                        return LexToken.TokenEOF

                    LineTokens = LexModule.LexAnalyze(pc, pc.StrEmpty, line, len(line), None)
                    LineNode = TokenLine()
                    LineNode.Tokens = LineTokens
                    LineNode.NumBytes = len(LineTokens)
                    if pc.InteractiveHead is None:
                        pc.InteractiveHead = LineNode
                        Parser.Line = 1
                        Parser.CharacterPos = 0
                    else:
                        pc.InteractiveTail.Next = LineNode
                    pc.InteractiveTail = LineNode
                    pc.InteractiveCurrentLine = LineNode
                    Parser.TokenList = LineTokens
                    Parser.Pos = 0
                else:
                    cur = pc.InteractiveCurrentLine
                    target_tokens = None
                    for tn in [pc.InteractiveHead]:
                        n = tn
                        while n:
                            if n is cur:
                                target_tokens = n.Next
                                break
                            n = n.Next
                    if target_tokens:
                        pc.InteractiveCurrentLine = target_tokens
                        Parser.TokenList = target_tokens.Tokens
                        Parser.Pos = 0

                Token = Parser.TokenList[Parser.Pos][0] if Parser.Pos < len(Parser.TokenList) else LexToken.TokenEOF

            if not (Parser.FileName == pc.StrEmpty and Token == LexToken.TokenEOF) and Token != LexToken.TokenEndOfLine:
                break
            if Token != LexToken.TokenEndOfLine:
                break

        if Parser.Pos < len(Parser.TokenList):
            Parser.CharacterPos = Parser.TokenList[Parser.Pos][1]
            entry = Parser.TokenList[Parser.Pos]
            Token = entry[0]
            val = entry[2] if len(entry) > 2 else None

            if val is not None:
                token_entry = entry
                pc.LexValue.Val = AnyValue()
                if Token == LexToken.TokenStringConstant:
                    pc.LexValue.Typ = pc.CharPtrType
                    pc.LexValue.Val.Pointer = val
                elif Token == LexToken.TokenIdentifier:
                    pc.LexValue.Typ = None
                    pc.LexValue.Val.Identifier = val
                elif Token == LexToken.TokenIntegerConstant:
                    pc.LexValue.Typ = pc.LongType
                    pc.LexValue.Val.LongInteger = val
                elif Token == LexToken.TokenCharacterConstant:
                    pc.LexValue.Typ = pc.CharType
                    pc.LexValue.Val.Character = val
                elif Token == LexToken.TokenFPConstant:
                    pc.LexValue.Typ = pc.FPType
                    pc.LexValue.Val.FP = val
                pc.LexValue.ValOnHeap = False
                pc.LexValue.ValOnStack = False
                pc.LexValue.IsLValue = False
                pc.LexValue.LValueFrom = None

            if IncPos:
                Parser.Pos += 1

        return Token

    @staticmethod
    def GetToken(Parser, IncPos):
        TryNextToken = True
        while TryNextToken:
            WasPreProcToken = True
            Token = LexModule.LexGetRawToken(Parser, IncPos)

            if Token == LexToken.TokenHashIfdef:
                if not IncPos:
                    LexModule.LexGetRawToken(Parser, True)
                LexModule.LexHashIfdef(Parser, False)
            elif Token == LexToken.TokenHashIfndef:
                if not IncPos:
                    LexModule.LexGetRawToken(Parser, True)
                LexModule.LexHashIfdef(Parser, True)
            elif Token == LexToken.TokenHashIf:
                if not IncPos:
                    LexModule.LexGetRawToken(Parser, True)
                LexModule.LexHashIf(Parser)
            elif Token == LexToken.TokenHashElse:
                if not IncPos:
                    LexModule.LexGetRawToken(Parser, True)
                LexModule.LexHashElse(Parser)
            elif Token == LexToken.TokenHashEndif:
                if not IncPos:
                    LexModule.LexGetRawToken(Parser, True)
                LexModule.LexHashEndif(Parser)
            elif Token == LexToken.TokenHashInclude:
                if not IncPos:
                    LexModule.LexGetRawToken(Parser, True)
                LexModule.LexGetRawToken(Parser, True)
                from include_module import IncludeFile
                IncludeFileName = Parser.pc.LexValue.Val.Identifier
                if IncludeFileName.startswith('<') and IncludeFileName.endswith('>'):
                    IncludeFileName = IncludeFileName[1:-1]
                IncludeFile(Parser.pc, IncludeFileName)
                Token = LexModule.LexGetRawToken(Parser, False)
                if Token == LexToken.TokenEndOfLine:
                    LexModule.LexGetRawToken(Parser, True)
                TryNextToken = True
            elif Token == LexToken.TokenHashDefine:
                LexModule.LexToEndOfMacro(Parser)
                from parse import ParseModule
                ParseModule.ParseMacroDefinition(Parser)
                TryNextToken = True
            else:
                WasPreProcToken = False

            TryNextToken = (Parser.HashIfEvaluateToLevel < Parser.HashIfLevel and Token != LexToken.TokenEOF) or WasPreProcToken
            if not IncPos and TryNextToken:
                LexModule.LexGetRawToken(Parser, True)

        return Token

    @staticmethod
    def LexHashIncPos(Parser, IncPos):
        if not IncPos:
            LexModule.LexGetRawToken(Parser, True)

    @staticmethod
    def LexHashIfdef(Parser, IfNot):
        IdentValue = None
        Token = LexModule.LexGetRawToken(Parser, True)
        if Token != LexToken.TokenIdentifier:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "identifier expected")
        ident = Parser.pc.LexValue.Val.Identifier
        IsDefined = TableModule.Get(Parser.pc.GlobalTable, ident) is not None
        if Parser.HashIfEvaluateToLevel == Parser.HashIfLevel and ((IsDefined and not IfNot) or (not IsDefined and IfNot)):
            Parser.HashIfEvaluateToLevel += 1
        Parser.HashIfLevel += 1

    @staticmethod
    def LexHashIf(Parser):
        IdentValue = None
        SavedValue = None
        Token = LexModule.LexGetRawToken(Parser, True)
        if Token == LexToken.TokenIdentifier:
            SavedValue = TableModule.Get(Parser.pc.GlobalTable, Parser.pc.LexValue.Val.Identifier)
            if SavedValue is None:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "'%s' is undefined" % Parser.pc.LexValue.Val.Identifier)
            if SavedValue.Typ.Base != BaseType.TypeMacro:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "value expected")
            MacroParser = ParseState()
            LexModule.ParserCopy(MacroParser, SavedValue.Val.MacroDef.Body)
            MacroParser.Pos = 0
            Token = LexModule.LexGetRawToken(MacroParser, True)

        if Token != LexToken.TokenCharacterConstant and Token != LexToken.TokenIntegerConstant:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "value expected")

        val = Parser.pc.LexValue.Val.Character
        if Parser.HashIfEvaluateToLevel == Parser.HashIfLevel and val:
            Parser.HashIfEvaluateToLevel += 1
        Parser.HashIfLevel += 1

    @staticmethod
    def LexHashElse(Parser):
        if Parser.HashIfEvaluateToLevel == Parser.HashIfLevel - 1:
            Parser.HashIfEvaluateToLevel += 1
        elif Parser.HashIfEvaluateToLevel == Parser.HashIfLevel:
            if Parser.HashIfLevel == 0:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "#else without #if")
            Parser.HashIfEvaluateToLevel -= 1

    @staticmethod
    def LexHashEndif(Parser):
        if Parser.HashIfLevel == 0:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "#endif without #if")
        Parser.HashIfLevel -= 1
        if Parser.HashIfEvaluateToLevel > Parser.HashIfLevel:
            Parser.HashIfEvaluateToLevel = Parser.HashIfLevel

    @staticmethod
    def LexRawPeekToken(Parser):
        if Parser.TokenList and Parser.Pos < len(Parser.TokenList):
            return Parser.TokenList[Parser.Pos][0]
        return LexToken.TokenEOF

    @staticmethod
    def LexToEndOfMacro(Parser):
        isContinued = False
        while True:
            if Parser.Pos >= len(Parser.TokenList):
                return
            Token = Parser.TokenList[Parser.Pos][0]
            if Token == LexToken.TokenEOF:
                return
            elif Token == LexToken.TokenEndOfLine:
                if not isContinued:
                    return
                isContinued = False
            if Token == LexToken.TokenBackSlash:
                isContinued = True
            LexModule.LexGetRawToken(Parser, True)

    @staticmethod
    def LexCopyTokens(StartParser, EndParser):
        start = StartParser.Pos
        end = EndParser.Pos
        tokens = StartParser.TokenList[start:end]
        tokens.append((LexToken.TokenEndOfFunction, 0, None))
        return tokens

    @staticmethod
    def ParserCopy(To, From):
        To.pc = From.pc
        To.TokenList = From.TokenList
        To.Pos = From.Pos
        To.FileName = From.FileName
        To.Line = From.Line
        To.CharacterPos = From.CharacterPos
        To.Mode = From.Mode
        To.SearchLabel = From.SearchLabel
        To.SearchGotoLabel = From.SearchGotoLabel
        To.SourceText = From.SourceText
        To.HashIfLevel = From.HashIfLevel
        To.HashIfEvaluateToLevel = From.HashIfEvaluateToLevel
        To.DebugMode = From.DebugMode
        To.ScopeID = From.ScopeID

    @staticmethod
    def ParserCopyPos(To, From):
        To.Pos = From.Pos
        To.Line = From.Line
        To.HashIfLevel = From.HashIfLevel
        To.HashIfEvaluateToLevel = From.HashIfEvaluateToLevel
        To.CharacterPos = From.CharacterPos

    @staticmethod
    def InteractiveClear(pc, Parser):
        pc.InteractiveHead = None
        pc.InteractiveTail = None
        if Parser is not None:
            Parser.TokenList = None

    @staticmethod
    def InteractiveCompleted(pc, Parser):
        pass

    @staticmethod
    def InteractiveStatementPrompt(pc):
        pc.LexUseStatementPrompt = True
