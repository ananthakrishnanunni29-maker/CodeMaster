import sys
import os

from interpreter import *

class PlatformModule:
    @staticmethod
    def Init(pc):
        pass

    @staticmethod
    def Cleanup(pc):
        pass

    @staticmethod
    def GetLine(MaxLen, Prompt):
        try:
            if Prompt:
                sys.stdout.write(Prompt)
                sys.stdout.flush()
            line = sys.stdin.readline()
            if not line:
                return None
            return line
        except (EOFError, KeyboardInterrupt):
            return None

    @staticmethod
    def GetCharacter():
        sys.stdout.flush()
        try:
            return ord(sys.stdin.read(1))
        except (EOFError, KeyboardInterrupt):
            return -1

    @staticmethod
    def Putc(OutCh, StreamInfo=None):
        sys.stdout.write(chr(OutCh))
        sys.stdout.flush()

    @staticmethod
    def Printf(Stream, Format, *args):
        PlatformModule.VPrintf(Stream, Format, args)

    @staticmethod
    def VPrintf(Stream, Format, Args):
        FPos = 0
        while FPos < len(Format):
            if Format[FPos] == '%':
                FPos += 1
                if FPos >= len(Format):
                    break
                ch = Format[FPos]
                if ch == 's':
                    s = Args[0] if Args else ""
                    if isinstance(s, bytes):
                        s = s.decode('latin-1')
                    if isinstance(Stream, type(sys.stdout)):
                        Stream.write(s)
                    else:
                        Stream.write(s)
                    Args = Args[1:] if Args else []
                elif ch == 'd':
                    val = int(Args[0]) if Args else 0
                    Stream.write(str(val))
                    Args = Args[1:] if Args else []
                elif ch == 'c':
                    Stream.write(chr(int(Args[0]) if Args else 0))
                    Args = Args[1:] if Args else []
                elif ch == 't':
                    from clibrary import CLibraryModule
                    typ = Args[0] if Args else None
                    CLibraryModule.PrintType(typ, Stream)
                    Args = Args[1:] if Args else []
                elif ch == 'f':
                    val = float(Args[0]) if Args else 0.0
                    Stream.write(str(val))
                    Args = Args[1:] if Args else []
                elif ch == '%':
                    Stream.write('%')
                elif ch == '\0':
                    FPos -= 1
                elif ch == 'l':
                    continue
                else:
                    Stream.write('%' + ch)
                    if Args:
                        Args = Args[1:] if Args else []
            else:
                Stream.write(Format[FPos])
            FPos += 1

    @staticmethod
    def MakeTempName(pc, TempNameBuffer):
        TempNameBuffer = list(TempNameBuffer)
        CPos = 5
        while CPos > 1:
            if TempNameBuffer[CPos] < '9':
                TempNameBuffer[CPos] = chr(ord(TempNameBuffer[CPos]) + 1)
                return TableModule.StrRegister(pc, ''.join(TempNameBuffer))
            else:
                TempNameBuffer[CPos] = '0'
                CPos -= 1
        return TableModule.StrRegister(pc, ''.join(TempNameBuffer))

    @staticmethod
    def ReadFile(pc, FileName):
        try:
            with open(FileName, 'r') as f:
                data = f.read()
                if data.startswith('#!'):
                    lines = data.split('\n')
                    if lines:
                        lines[0] = '//' + lines[0][2:]
                    data = '\n'.join(lines)
                return data
            return None
        except IOError:
            from platform_module import PlatformModule
            PlatformModule.ProgramFailNoParser(pc, "can't read file %s\n" % FileName)
            return None

    @staticmethod
    def ScanFile(pc, FileName):
        SourceStr = PlatformModule.ReadFile(pc, FileName)
        if SourceStr is not None and SourceStr.startswith('#!'):
            SourceStr = '//' + SourceStr[2:]
        from parse import ParseModule
        ParseModule.PicocParse(pc, FileName, SourceStr, len(SourceStr), True, False, True, False)

    @staticmethod
    def Exit(pc, RetVal):
        pc.PicocExitValue = RetVal
        raise SystemExit(RetVal)

    @staticmethod
    def ProgramFail(Parser, Message):
        Stream = Parser.pc.CStdOut
        PlatformModule.PrintSourceTextErrorLine(Stream, Parser.FileName, Parser.SourceText, Parser.Line, Parser.CharacterPos)
        Stream.write("\n")
        Stream.write(Message)
        Stream.write("\n")
        raise SystemExit(1)

    @staticmethod
    def ProgramFailNoParser(pc, Message):
        Stream = pc.CStdOut
        Stream.write(Message)
        Stream.write("\n")
        raise SystemExit(1)

    @staticmethod
    def AssignFail(Parser, Format, Type1=None, Type2=None, Num1=0, Num2=0, FuncName=None, ParamNo=0):
        Stream = Parser.pc.CStdOut
        PlatformModule.PrintSourceTextErrorLine(Stream, Parser.FileName, Parser.SourceText, Parser.Line, Parser.CharacterPos)
        Stream.write("can't ")
        if FuncName is None:
            Stream.write("assign")
        else:
            Stream.write("set")
        Stream.write(" ")
        if Type1 is not None:
            from clibrary import CLibraryModule
            CLibraryModule.PrintType(Type1, Stream)
            Stream.write(" ")
            CLibraryModule.PrintType(Type2, Stream)
        else:
            Stream.write(str(Num1))
            Stream.write(" ")
            Stream.write(str(Num2))
        if FuncName is not None:
            Stream.write(" in argument %d of call to %s()" % (ParamNo, FuncName))
        Stream.write("\n")
        raise SystemExit(1)

    @staticmethod
    def LexFail(pc, Lexer, Message):
        Stream = pc.CStdOut
        PlatformModule.PrintSourceTextErrorLine(Stream, Lexer.FileName, Lexer.SourceText, Lexer.Line, Lexer.CharacterPos)
        Stream.write("\n")
        Stream.write(Message)
        Stream.write("\n")
        raise SystemExit(1)

    @staticmethod
    def PrintSourceTextErrorLine(Stream, FileName, SourceText, Line, CharacterPos):
        if SourceText:
            LinePos = 0
            LineCount = 1
            while LinePos < len(SourceText) and LineCount < Line:
                if SourceText[LinePos] == '\n':
                    LineCount += 1
                LinePos += 1
            end = LinePos
            while end < len(SourceText) and SourceText[end] != '\n' and SourceText[end] != '\0':
                end += 1
            Stream.write(SourceText[LinePos:end])
            Stream.write('\n')
            CCount = 0
            CPos = LinePos
            while CPos < end and (CCount < CharacterPos or SourceText[CPos] == ' '):
                if SourceText[CPos] == '\t':
                    Stream.write('\t')
                else:
                    Stream.write(' ')
                CCount += 1
                CPos += 1
        else:
            for _ in range(CharacterPos + len(INTERACTIVE_PROMPT_STATEMENT)):
                Stream.write(' ')
        Stream.write('^\n')
        Stream.write("%s:%d:%d " % (FileName, Line, CharacterPos))

    @staticmethod
    def PlatformLibraryInit(pc):
        from platform.library_unix import UnixLibraryModule
        UnixLibraryModule.PlatformLibraryInit(pc)
