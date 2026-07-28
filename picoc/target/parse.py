from interpreter import *
from lex import LexModule
from type_sys import TypeModule
from variable import VariableModule
from table import TableModule
from expression import ExpressionModule


def IncludeFile(pc, Filename):
    from platform_module import PlatformModule
    LibItem = pc.IncludeLibList
    while LibItem is not None:
        if LibItem.IncludeName == Filename:
            if LibItem.SetupFunction is not None:
                LibItem.SetupFunction(pc)
            elif LibItem.SetupCSource is not None:
                ParseModule.PicocParse(pc, Filename, LibItem.SetupCSource, len(LibItem.SetupCSource), True, False, True, False)
            else:
                PlatformModule.ProgramFailNoParser(pc, "don't know how to include '%s'" % Filename)
            return
        LibItem = LibItem.NextLib
    PlatformModule.ScanFile(pc, Filename)


class ParseModule:
    @staticmethod
    def Cleanup(pc):
        pc.CleanupTokenList = None

    @staticmethod
    def ParseStatementMaybeRun(Parser, Condition, CheckTrailingSemicolon):
        if Parser.Mode != RunMode.RunModeSkip and not Condition:
            OldMode = Parser.Mode
            Parser.Mode = RunMode.RunModeSkip
            Result = ParseModule.ParseStatement(Parser, CheckTrailingSemicolon)
            Parser.Mode = OldMode
            return Result
        else:
            return ParseModule.ParseStatement(Parser, CheckTrailingSemicolon)

    @staticmethod
    def ParseCountParams(Parser):
        ParamCount = 0
        Token = LexModule.GetToken(Parser, True)
        if Token != LexToken.TokenCloseBracket and Token != LexToken.TokenEOF:
            ParamCount += 1
            while True:
                Token = LexModule.GetToken(Parser, True)
                if Token == LexToken.TokenCloseBracket or Token == LexToken.TokenEOF:
                    break
                if Token == LexToken.TokenComma:
                    ParamCount += 1
        return ParamCount

    @staticmethod
    def ParseFunctionDefinition(Parser, ReturnType, Identifier):
        pc = Parser.pc
        if pc.TopStackFrame is not None:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "nested function definitions are not allowed")

        LexModule.GetToken(Parser, True)
        ParamParser = ParseState()
        LexModule.ParserCopy(ParamParser, Parser)
        ParamCount = ParseModule.ParseCountParams(Parser)
        if ParamCount > PARAMETER_MAX:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "too many parameters (%d allowed)" % PARAMETER_MAX)

        Token = LexToken.TokenNone
        FuncValue = VariableModule.AllocValueAndData(pc, Parser, 0, False, None, True)
        FuncValue.Typ = pc.FunctionType
        FuncValue.Val = AnyValue()
        FuncValue.Val.FuncDef = FuncDef()
        FuncValue.Val.FuncDef.ReturnType = ReturnType
        FuncValue.Val.FuncDef.NumParams = ParamCount
        FuncValue.Val.FuncDef.VarArgs = False

        Count = 0
        while Count < FuncValue.Val.FuncDef.NumParams:
            if Count == FuncValue.Val.FuncDef.NumParams - 1 and LexModule.GetToken(ParamParser, False) == LexToken.TokenEllipsis:
                FuncValue.Val.FuncDef.NumParams -= 1
                FuncValue.Val.FuncDef.VarArgs = True
                break
            else:
                ParamType = [None]
                ParamIdentifier = [""]
                TypeModule.Parse(ParamParser, ParamType, ParamIdentifier, None)
                if ParamType[0].Base == BaseType.TypeVoid:
                    FuncValue.Val.FuncDef.NumParams -= 1
                else:
                    FuncValue.Val.FuncDef.ParamType.append(ParamType[0])
                    FuncValue.Val.FuncDef.ParamName.append(ParamIdentifier[0])
                Count += 1

            Token = LexModule.GetToken(ParamParser, True)
            if Token != LexToken.TokenComma and Count < FuncValue.Val.FuncDef.NumParams - 1:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(ParamParser, "comma expected")

        if FuncValue.Val.FuncDef.NumParams != 0 and Token != LexToken.TokenCloseBracket and Token != LexToken.TokenComma and Token != LexToken.TokenEllipsis:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(ParamParser, "bad parameter")

        if Identifier == "main":
            if FuncValue.Val.FuncDef.ReturnType is not pc.IntType and FuncValue.Val.FuncDef.ReturnType is not pc.VoidType:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "main() should return an int or void")
            if FuncValue.Val.FuncDef.NumParams != 0 and (FuncValue.Val.FuncDef.NumParams != 2 or FuncValue.Val.FuncDef.ParamType[0] is not pc.IntType):
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "bad parameters to main()")

        Token = LexModule.GetToken(Parser, False)
        if Token == LexToken.TokenSemicolon:
            LexModule.GetToken(Parser, True)
        else:
            if Token != LexToken.TokenLeftBrace:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "bad function definition")

            FuncBody = ParseState()
            LexModule.ParserCopy(FuncBody, Parser)
            if ParseModule.ParseStatementMaybeRun(Parser, False, True) != ParseResult.ParseResultOk:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "function definition expected")

            FuncValue.Val.FuncDef.Body = FuncBody
            FuncValue.Val.FuncDef.BodyTokens = LexModule.LexCopyTokens(FuncBody, Parser)

            OldFuncValue = TableModule.Get(pc.GlobalTable, Identifier)
            if OldFuncValue is not None:
                if OldFuncValue.Val is not None and hasattr(OldFuncValue.Val, 'FuncDef') and OldFuncValue.Val.FuncDef.BodyTokens is None:
                    VariableModule.Free(pc, TableModule.Delete(pc, pc.GlobalTable, Identifier))
                else:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "'%s' is already defined" % Identifier)

        if not TableModule.Set(pc, pc.GlobalTable, Identifier, FuncValue, Parser.FileName, Parser.Line, Parser.CharacterPos):
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "'%s' is already defined" % Identifier)

        return FuncValue

    @staticmethod
    def ParseArrayInitializer(Parser, NewVariable, DoAssignment):
        ArrayIndex = 0
        if DoAssignment and Parser.Mode == RunMode.RunModeRun:
            CountParser = ParseState()
            LexModule.ParserCopy(CountParser, Parser)
            NumElements = ParseModule.ParseArrayInitializer(CountParser, NewVariable, False)

            if NewVariable.Typ.Base != BaseType.TypeArray:
                from platform_module import PlatformModule
                PlatformModule.AssignFail(Parser, "%t from array initializer", NewVariable.Typ, None, 0, 0, None, 0)

            if NewVariable.Typ.ArraySize == 0:
                NewVariable.Typ = TypeModule.GetMatching(Parser.pc, Parser, NewVariable.Typ.FromType, NewVariable.Typ.Base, NumElements, NewVariable.Typ.Identifier, True)
                VariableModule.Realloc(Parser, NewVariable, TypeModule.SizeValue(NewVariable, False))

        Token = LexModule.GetToken(Parser, False)
        while Token != LexToken.TokenRightBrace:
            if LexModule.GetToken(Parser, False) == LexToken.TokenLeftBrace:
                SubArraySize = 0
                SubArray = NewVariable
                if Parser.Mode == RunMode.RunModeRun and DoAssignment:
                    SubArraySize = TypeModule.Size(NewVariable.Typ.FromType, NewVariable.Typ.FromType.ArraySize, True)
                    SubArray = VariableModule.AllocValueFromExistingData(Parser, NewVariable.Typ.FromType, NewVariable.Val.Elements[ArrayIndex], True, NewVariable)
                    if ArrayIndex >= NewVariable.Typ.ArraySize:
                        from platform_module import PlatformModule
                        PlatformModule.ProgramFail(Parser, "too many array elements")
                LexModule.GetToken(Parser, True)
                ParseModule.ParseArrayInitializer(Parser, SubArray, DoAssignment)
            else:
                ArrayElement = None
                if Parser.Mode == RunMode.RunModeRun and DoAssignment:
                    ElementType = NewVariable.Typ
                    TotalSize = 1
                    ElementSize = 0
                    while ElementType.Base == BaseType.TypeArray:
                        TotalSize *= ElementType.ArraySize
                        ElementType = ElementType.FromType
                        if LexModule.GetToken(Parser, False) == LexToken.TokenStringConstant and ElementType.FromType is not None and ElementType.FromType.Base == BaseType.TypeChar:
                            break
                    ElementSize = TypeModule.Size(ElementType, ElementType.ArraySize, True)
                    if ArrayIndex >= TotalSize:
                        from platform_module import PlatformModule
                        PlatformModule.ProgramFail(Parser, "too many array elements")
                    ArrayElement = VariableModule.AllocValueFromExistingData(Parser, ElementType, NewVariable.Val.Elements[ArrayIndex], True, NewVariable)

                CValue = [None]
                if not ExpressionModule.Parse(Parser, CValue):
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "expression expected")

                if Parser.Mode == RunMode.RunModeRun and DoAssignment:
                    ExpressionModule.Assign(Parser, ArrayElement, CValue[0], False, None, 0, False)
                    VariableModule.StackPop(Parser, CValue[0])
                    VariableModule.StackPop(Parser, ArrayElement)

            ArrayIndex += 1

            Token = LexModule.GetToken(Parser, False)
            if Token == LexToken.TokenComma:
                LexModule.GetToken(Parser, True)
                Token = LexModule.GetToken(Parser, False)
            elif Token != LexToken.TokenRightBrace:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "comma expected")

        if Token == LexToken.TokenRightBrace:
            LexModule.GetToken(Parser, True)
        else:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "'}' expected")

        return ArrayIndex

    @staticmethod
    def ParseDeclarationAssignment(Parser, NewVariable, DoAssignment):
        if LexModule.GetToken(Parser, False) == LexToken.TokenLeftBrace:
            LexModule.GetToken(Parser, True)
            ParseModule.ParseArrayInitializer(Parser, NewVariable, DoAssignment)
        else:
            CValue = [None]
            if not ExpressionModule.Parse(Parser, CValue):
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "expression expected")
            if Parser.Mode == RunMode.RunModeRun and DoAssignment:
                ExpressionModule.Assign(Parser, NewVariable, CValue[0], False, None, 0, False)
                VariableModule.StackPop(Parser, CValue[0])

    @staticmethod
    def ParseDeclaration(Parser, Token):
        IsStatic = [False]
        FirstVisit = [False]
        BasicType = [None]
        pc = Parser.pc

        TypeModule.ParseFront(Parser, BasicType, IsStatic)
        while True:
            Typ = [None]
            Identifier = [""]
            TypeModule.ParseIdentPart(Parser, BasicType[0], Typ, Identifier)
            if Token not in (LexToken.TokenVoidType, LexToken.TokenStructType, LexToken.TokenUnionType, LexToken.TokenEnumType) and Identifier[0] == pc.StrEmpty:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "identifier expected")

            if Identifier[0] != pc.StrEmpty:
                if LexModule.GetToken(Parser, False) == LexToken.TokenOpenBracket:
                    ParseModule.ParseFunctionDefinition(Parser, Typ[0], Identifier[0])
                    return False
                else:
                    if Typ[0] is pc.VoidType and Identifier[0] != pc.StrEmpty:
                        from platform_module import PlatformModule
                        PlatformModule.ProgramFail(Parser, "can't define a void variable")

                    NewVariable = None
                    if Parser.Mode in (RunMode.RunModeRun, RunMode.RunModeGoto):
                        NewVariable = VariableModule.DefButIgnoreIdentical(Parser, Identifier[0], Typ[0], IsStatic[0], FirstVisit)

                    if LexModule.GetToken(Parser, False) == LexToken.TokenAssign:
                        LexModule.GetToken(Parser, True)
                        ParseModule.ParseDeclarationAssignment(Parser, NewVariable, not IsStatic[0] or FirstVisit[0])

            Token = LexModule.GetToken(Parser, False)
            if Token == LexToken.TokenComma:
                LexModule.GetToken(Parser, True)
            else:
                break

        return True

    @staticmethod
    def ParseMacroDefinition(Parser):
        pc = Parser.pc
        Token = LexModule.GetToken(Parser, True)
        if Token != LexToken.TokenIdentifier:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "identifier expected")

        MacroNameStr = Parser.pc.LexValue.Val.Identifier

        if LexModule.LexRawPeekToken(Parser) == LexToken.TokenOpenMacroBracket:
            Token = LexModule.GetToken(Parser, True)
            ParamParser = ParseState()
            LexModule.ParserCopy(ParamParser, Parser)
            NumParams = ParseModule.ParseCountParams(ParamParser)

            MacroValue = VariableModule.AllocValueAndData(pc, Parser, 0, False, None, True)
            MacroValue.Val = AnyValue()
            MacroValue.Val.MacroDef = MacroDef()
            MacroValue.Val.MacroDef.NumParams = NumParams

            ParamCount = 0
            Token = LexModule.GetToken(Parser, True)
            while Token == LexToken.TokenIdentifier:
                MacroValue.Val.MacroDef.ParamName.append(Parser.pc.LexValue.Val.Identifier)
                ParamCount += 1
                Token = LexModule.GetToken(Parser, True)
                if Token == LexToken.TokenComma:
                    Token = LexModule.GetToken(Parser, True)
                elif Token != LexToken.TokenCloseBracket:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "comma expected")

            if Token != LexToken.TokenCloseBracket:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "close bracket expected")
        else:
            MacroValue = VariableModule.AllocValueAndData(pc, Parser, 0, False, None, True)
            MacroValue.Val = AnyValue()
            MacroValue.Val.MacroDef = MacroDef()
            MacroValue.Val.MacroDef.NumParams = 0

        MacroValue.Typ = pc.MacroType
        MacroBody = ParseState()
        LexModule.ParserCopy(MacroBody, Parser)
        LexModule.LexToEndOfMacro(Parser)
        MacroValue.Val.MacroDef.Body = MacroBody
        MacroValue.Val.MacroDef.BodyTokens = LexModule.LexCopyTokens(MacroBody, Parser)

        if not TableModule.Set(pc, pc.GlobalTable, MacroNameStr, MacroValue, Parser.FileName, Parser.Line, Parser.CharacterPos):
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "'%s' is already defined" % MacroNameStr)

    @staticmethod
    def ParseFor(Parser):
        Condition = True
        pc = Parser.pc
        OldMode = Parser.Mode
        PrevScopeID = [0]
        ScopeID = VariableModule.ScopeBegin(Parser, PrevScopeID)

        if LexModule.GetToken(Parser, True) != LexToken.TokenOpenBracket:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "'(' expected")

        if ParseModule.ParseStatement(Parser, True) != ParseResult.ParseResultOk:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "statement expected")

        PreConditional = ParseState()
        LexModule.ParserCopyPos(PreConditional, Parser)
        if LexModule.GetToken(Parser, False) == LexToken.TokenSemicolon:
            Condition = True
        else:
            Condition = VariableModule.ExpressionParseInt(Parser)

        if LexModule.GetToken(Parser, True) != LexToken.TokenSemicolon:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "';' expected")

        PreIncrement = ParseState()
        LexModule.ParserCopyPos(PreIncrement, Parser)
        ParseModule.ParseStatementMaybeRun(Parser, False, False)

        if LexModule.GetToken(Parser, True) != LexToken.TokenCloseBracket:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "')' expected")

        PreStatement = ParseState()
        LexModule.ParserCopyPos(PreStatement, Parser)
        if ParseModule.ParseStatementMaybeRun(Parser, Condition, True) != ParseResult.ParseResultOk:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "statement expected")

        if Parser.Mode == RunMode.RunModeContinue and OldMode == RunMode.RunModeRun:
            Parser.Mode = RunMode.RunModeRun

        After = ParseState()
        LexModule.ParserCopyPos(After, Parser)

        while Condition and Parser.Mode == RunMode.RunModeRun:
            LexModule.ParserCopyPos(Parser, PreIncrement)
            ParseModule.ParseStatement(Parser, False)

            LexModule.ParserCopyPos(Parser, PreConditional)
            if LexModule.GetToken(Parser, False) == LexToken.TokenSemicolon:
                Condition = True
            else:
                Condition = VariableModule.ExpressionParseInt(Parser)

            if Condition:
                LexModule.ParserCopyPos(Parser, PreStatement)
                ParseModule.ParseStatement(Parser, True)
                if Parser.Mode == RunMode.RunModeContinue:
                    Parser.Mode = RunMode.RunModeRun

        if Parser.Mode == RunMode.RunModeBreak and OldMode == RunMode.RunModeRun:
            Parser.Mode = RunMode.RunModeRun

        VariableModule.ScopeEnd(Parser, ScopeID, PrevScopeID[0])
        LexModule.ParserCopyPos(Parser, After)

    @staticmethod
    def ParseBlock(Parser, AbsorbOpenBrace, Condition):
        PrevScopeID = [0]
        ScopeID = VariableModule.ScopeBegin(Parser, PrevScopeID)

        if AbsorbOpenBrace and LexModule.GetToken(Parser, True) != LexToken.TokenLeftBrace:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "'{' expected")

        if Parser.Mode == RunMode.RunModeSkip or not Condition:
            OldMode = Parser.Mode
            Parser.Mode = RunMode.RunModeSkip
            while ParseModule.ParseStatement(Parser, True) == ParseResult.ParseResultOk:
                pass
            Parser.Mode = OldMode
        else:
            while ParseModule.ParseStatement(Parser, True) == ParseResult.ParseResultOk:
                pass

        if LexModule.GetToken(Parser, True) != LexToken.TokenRightBrace:
            from platform_module import PlatformModule
            PlatformModule.ProgramFail(Parser, "'}' expected")

        VariableModule.ScopeEnd(Parser, ScopeID, PrevScopeID[0])
        return Parser.Mode

    @staticmethod
    def ParseTypedef(Parser):
        Typ = [None]
        TypeName = [""]
        TypeModule.Parse(Parser, Typ, TypeName, None)

        if Parser.Mode == RunMode.RunModeRun:
            InitValue = Value()
            InitValue.Typ = Parser.pc.TypeType
            InitValue.Val = Typ[0]
            VariableModule.Def(Parser.pc, Parser, TypeName[0], InitValue, None, False)

    @staticmethod
    def ParseStatement(Parser, CheckTrailingSemicolon):
        Condition = 0
        Token = LexToken.TokenNone
        PreState = ParseState()

        LexModule.ParserCopy(PreState, Parser)
        Token = LexModule.GetToken(Parser, True)

        if Token == LexToken.TokenEOF:
            return ParseResult.ParseResultEOF

        if Token == LexToken.TokenIdentifier:
            if VariableModule.Defined(Parser.pc, Parser.pc.LexValue.Val.Identifier):
                VarValue = VariableModule.Get(Parser.pc, Parser, Parser.pc.LexValue.Val.Identifier)
                if VarValue.Typ is Parser.pc.TypeType:
                    LexModule.ParserCopy(Parser, PreState)
                    ParseModule.ParseDeclaration(Parser, Token)
                    CheckTrailingSemicolon = False
                else:
                    NextToken = LexModule.GetToken(Parser, False)
                    if NextToken == LexToken.TokenColon:
                        LexModule.GetToken(Parser, True)
                        if Parser.Mode == RunMode.RunModeGoto and Parser.pc.LexValue.Val.Identifier == Parser.SearchGotoLabel:
                            Parser.Mode = RunMode.RunModeRun
                        CheckTrailingSemicolon = False
                    else:
                        LexModule.ParserCopy(Parser, PreState)
                        CValue = [None]
                        ExpressionModule.Parse(Parser, CValue)
                        if Parser.Mode == RunMode.RunModeRun:
                            VariableModule.StackPop(Parser, CValue[0])
            else:
                NextToken = LexModule.GetToken(Parser, False)
                if NextToken == LexToken.TokenColon:
                    LexModule.GetToken(Parser, True)
                    if Parser.Mode == RunMode.RunModeGoto and Parser.pc.LexValue.Val.Identifier == Parser.SearchGotoLabel:
                        Parser.Mode = RunMode.RunModeRun
                    CheckTrailingSemicolon = False
                else:
                    LexModule.ParserCopy(Parser, PreState)
                    CValue = [None]
                    ExpressionModule.Parse(Parser, CValue)
                    if Parser.Mode == RunMode.RunModeRun:
                        VariableModule.StackPop(Parser, CValue[0])

        elif Token in (LexToken.TokenAsterisk, LexToken.TokenAmpersand, LexToken.TokenIncrement, LexToken.TokenDecrement, LexToken.TokenOpenBracket):
            LexModule.ParserCopy(Parser, PreState)
            CValue = [None]
            ExpressionModule.Parse(Parser, CValue)
            if Parser.Mode == RunMode.RunModeRun:
                VariableModule.StackPop(Parser, CValue[0])

        elif Token == LexToken.TokenLeftBrace:
            ParseModule.ParseBlock(Parser, False, True)
            CheckTrailingSemicolon = False

        elif Token == LexToken.TokenIf:
            if LexModule.GetToken(Parser, True) != LexToken.TokenOpenBracket:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "'(' expected")
            Condition = VariableModule.ExpressionParseInt(Parser)
            if LexModule.GetToken(Parser, True) != LexToken.TokenCloseBracket:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "')' expected")
            if ParseModule.ParseStatementMaybeRun(Parser, Condition, True) != ParseResult.ParseResultOk:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "statement expected")
            if LexModule.GetToken(Parser, False) == LexToken.TokenElse:
                LexModule.GetToken(Parser, True)
                if ParseModule.ParseStatementMaybeRun(Parser, not Condition, True) != ParseResult.ParseResultOk:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "statement expected")
            CheckTrailingSemicolon = False

        elif Token == LexToken.TokenWhile:
            PreConditional = ParseState()
            PreMode = Parser.Mode
            if LexModule.GetToken(Parser, True) != LexToken.TokenOpenBracket:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "'(' expected")
            LexModule.ParserCopyPos(PreConditional, Parser)
            while True:
                LexModule.ParserCopyPos(Parser, PreConditional)
                Condition = VariableModule.ExpressionParseInt(Parser)
                if LexModule.GetToken(Parser, True) != LexToken.TokenCloseBracket:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "')' expected")
                if ParseModule.ParseStatementMaybeRun(Parser, Condition, True) != ParseResult.ParseResultOk:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "statement expected")
                if Parser.Mode == RunMode.RunModeContinue:
                    Parser.Mode = PreMode
                if not (Parser.Mode == RunMode.RunModeRun and Condition):
                    break
            if Parser.Mode == RunMode.RunModeBreak:
                Parser.Mode = PreMode
            CheckTrailingSemicolon = False

        elif Token == LexToken.TokenDo:
            PreStatement = ParseState()
            PreMode = Parser.Mode
            LexModule.ParserCopyPos(PreStatement, Parser)
            while True:
                LexModule.ParserCopyPos(Parser, PreStatement)
                if ParseModule.ParseStatement(Parser, True) != ParseResult.ParseResultOk:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "statement expected")
                if Parser.Mode == RunMode.RunModeContinue:
                    Parser.Mode = PreMode
                if LexModule.GetToken(Parser, True) != LexToken.TokenWhile:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "'while' expected")
                if LexModule.GetToken(Parser, True) != LexToken.TokenOpenBracket:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "'(' expected")
                Condition = VariableModule.ExpressionParseInt(Parser)
                if LexModule.GetToken(Parser, True) != LexToken.TokenCloseBracket:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "')' expected")
                if not (Condition and Parser.Mode == RunMode.RunModeRun):
                    break
            if Parser.Mode == RunMode.RunModeBreak:
                Parser.Mode = PreMode
            CheckTrailingSemicolon = False

        elif Token == LexToken.TokenFor:
            ParseModule.ParseFor(Parser)
            CheckTrailingSemicolon = False

        elif Token == LexToken.TokenSemicolon:
            CheckTrailingSemicolon = False

        elif Token in (LexToken.TokenIntType, LexToken.TokenShortType, LexToken.TokenCharType, LexToken.TokenLongType, LexToken.TokenFloatType, LexToken.TokenDoubleType, LexToken.TokenVoidType, LexToken.TokenStructType, LexToken.TokenUnionType, LexToken.TokenEnumType, LexToken.TokenSignedType, LexToken.TokenUnsignedType, LexToken.TokenStaticType, LexToken.TokenAutoType, LexToken.TokenRegisterType, LexToken.TokenExternType):
            LexModule.ParserCopy(Parser, PreState)
            CheckTrailingSemicolon = ParseModule.ParseDeclaration(Parser, Token)

        elif Token == LexToken.TokenHashDefine:
            ParseModule.ParseMacroDefinition(Parser)
            CheckTrailingSemicolon = False

        elif Token == LexToken.TokenHashInclude:
            if LexModule.GetToken(Parser, True) != LexToken.TokenStringConstant:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "\"filename.h\" expected")
            IncludeFile(Parser.pc, Parser.pc.LexValue.Val.Pointer)
            CheckTrailingSemicolon = False

        elif Token == LexToken.TokenSwitch:
            if LexModule.GetToken(Parser, True) != LexToken.TokenOpenBracket:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "'(' expected")
            Condition = VariableModule.ExpressionParseInt(Parser)
            if LexModule.GetToken(Parser, True) != LexToken.TokenCloseBracket:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "')' expected")
            if LexModule.GetToken(Parser, False) != LexToken.TokenLeftBrace:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "'{' expected")
            OldMode = Parser.Mode
            OldSearchLabel = Parser.SearchLabel
            Parser.Mode = RunMode.RunModeCaseSearch
            Parser.SearchLabel = Condition
            ParseModule.ParseBlock(Parser, True, OldMode not in (RunMode.RunModeSkip, RunMode.RunModeReturn))
            if Parser.Mode != RunMode.RunModeReturn:
                Parser.Mode = OldMode
            Parser.SearchLabel = OldSearchLabel
            CheckTrailingSemicolon = False

        elif Token == LexToken.TokenCase:
            if Parser.Mode == RunMode.RunModeCaseSearch:
                Parser.Mode = RunMode.RunModeRun
                Condition = VariableModule.ExpressionParseInt(Parser)
                Parser.Mode = RunMode.RunModeCaseSearch
            else:
                Condition = VariableModule.ExpressionParseInt(Parser)
            if LexModule.GetToken(Parser, True) != LexToken.TokenColon:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "':' expected")
            if Parser.Mode == RunMode.RunModeCaseSearch and Condition == Parser.SearchLabel:
                Parser.Mode = RunMode.RunModeRun
            CheckTrailingSemicolon = False

        elif Token == LexToken.TokenDefault:
            if LexModule.GetToken(Parser, True) != LexToken.TokenColon:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "':' expected")
            if Parser.Mode == RunMode.RunModeCaseSearch:
                Parser.Mode = RunMode.RunModeRun
            CheckTrailingSemicolon = False

        elif Token == LexToken.TokenBreak:
            if Parser.Mode == RunMode.RunModeRun:
                Parser.Mode = RunMode.RunModeBreak

        elif Token == LexToken.TokenContinue:
            if Parser.Mode == RunMode.RunModeRun:
                Parser.Mode = RunMode.RunModeContinue

        elif Token == LexToken.TokenReturn:
            if Parser.Mode == RunMode.RunModeRun:
                if Parser.pc.TopStackFrame is None or Parser.pc.TopStackFrame.ReturnValue.Typ.Base != BaseType.TypeVoid:
                    CValue = [None]
                    if not ExpressionModule.Parse(Parser, CValue):
                        from platform_module import PlatformModule
                        PlatformModule.ProgramFail(Parser, "value required in return")
                    if Parser.pc.TopStackFrame is None:
                        from platform_module import PlatformModule
                        PlatformModule.Exit(Parser.pc, ExpressionModule.CoerceInteger(CValue[0]))
                    else:
                        ExpressionModule.Assign(Parser, Parser.pc.TopStackFrame.ReturnValue, CValue[0], True, None, 0, False)
                        VariableModule.StackPop(Parser, CValue[0])
                else:
                    CValue = [None]
                    if ExpressionModule.Parse(Parser, CValue):
                        from platform_module import PlatformModule
                        PlatformModule.ProgramFail(Parser, "value in return from a void function")
                Parser.Mode = RunMode.RunModeReturn
            else:
                CValue = [None]
                ExpressionModule.Parse(Parser, CValue)

        elif Token == LexToken.TokenTypedef:
            ParseModule.ParseTypedef(Parser)

        elif Token == LexToken.TokenGoto:
            if LexModule.GetToken(Parser, True) != LexToken.TokenIdentifier:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "identifier expected")
            if Parser.Mode == RunMode.RunModeRun:
                Parser.SearchGotoLabel = Parser.pc.LexValue.Val.Identifier
                Parser.Mode = RunMode.RunModeGoto

        elif Token == LexToken.TokenDelete:
            if LexModule.GetToken(Parser, True) != LexToken.TokenIdentifier:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "identifier expected")
            if Parser.Mode == RunMode.RunModeRun:
                CValue = TableModule.Delete(Parser.pc, Parser.pc.GlobalTable, Parser.pc.LexValue.Val.Identifier)
                if CValue is None:
                    from platform_module import PlatformModule
                    PlatformModule.ProgramFail(Parser, "'%s' is not defined" % Parser.pc.LexValue.Val.Identifier)
                VariableModule.Free(Parser.pc, CValue)

        else:
            LexModule.ParserCopy(Parser, PreState)
            return ParseResult.ParseResultError

        if CheckTrailingSemicolon:
            if LexModule.GetToken(Parser, True) != LexToken.TokenSemicolon:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "';' expected")

        return ParseResult.ParseResultOk

    @staticmethod
    def PicocParse(pc, FileName, Source, SourceLen, RunIt, CleanupNow, CleanupSource, EnableDebugger):
        RegFileName = TableModule.StrRegister(pc, FileName)
        Tokens = LexModule.LexAnalyze(pc, RegFileName, Source, SourceLen, None)

        if not CleanupNow:
            NewCleanupNode = CleanupTokenNode()
            NewCleanupNode.Tokens = Tokens
            if CleanupSource:
                NewCleanupNode.SourceText = Source
            else:
                NewCleanupNode.SourceText = None
            NewCleanupNode.Next = pc.CleanupTokenList
            pc.CleanupTokenList = NewCleanupNode

        Parser = ParseState()
        LexModule.LexInitParser(Parser, pc, Source, Tokens, RegFileName, RunIt, EnableDebugger)

        while True:
            Ok = ParseModule.ParseStatement(Parser, True)
            if Ok == ParseResult.ParseResultEOF:
                break
            if Ok == ParseResult.ParseResultError:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "parse error")

        if CleanupNow:
            pass

    @staticmethod
    def PicocParseInteractiveNoStartPrompt(pc, EnableDebugger):
        Parser = ParseState()
        LexModule.LexInitParser(Parser, pc, None, None, pc.StrEmpty, True, EnableDebugger)
        LexModule.InteractiveClear(pc, Parser)

        while True:
            LexModule.InteractiveStatementPrompt(pc)
            Ok = ParseModule.ParseStatement(Parser, True)
            LexModule.InteractiveCompleted(pc, Parser)
            if Ok == ParseResult.ParseResultEOF:
                break
            if Ok == ParseResult.ParseResultError:
                from platform_module import PlatformModule
                PlatformModule.ProgramFail(Parser, "parse error")

    @staticmethod
    def PicocParseInteractive(pc):
        from platform_module import PlatformModule
        PlatformModule.Printf(pc.CStdOut, INTERACTIVE_PROMPT_START)
        ParseModule.PicocParseInteractiveNoStartPrompt(pc, False)
