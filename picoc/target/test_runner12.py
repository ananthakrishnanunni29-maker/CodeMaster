import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from interpreter import *
from table import TableModule
from heap import HeapModule
from variable import VariableModule
from lex import LexModule
from type_sys import TypeModule
from platform_module import PlatformModule
from clibrary import CLibraryModule
from include_module import IncludeModule, IncludeFile
from debug import DebugModule
from parse import ParseModule

pc = Picoc()
HeapModule.Init(pc, 128000 * 4)
TableModule.Init(pc)
VariableModule.Init(pc)
LexModule.Init(pc)
TypeModule.Init(pc)
IncludeModule.Init(pc)
CLibraryModule.LibraryInit(pc)
PlatformModule.PlatformLibraryInit(pc)
DebugModule.Init(pc)

print("Initialized OK", flush=True)

# Test LexAnalyze
import ctypes
src = '#include <stdio.h>\n'

print(f"LexAnalyze on: {repr(src)}", flush=True)
Lexer = LexState()
Lexer.pc = pc
Lexer.Source = src
Lexer.Pos = 0
Lexer.End = len(src)
Lexer.Line = 1
Lexer.FileName = "test"
Lexer.Mode = LexMode.LexModeNormal
Lexer.EmitExtraNewlines = 0
Lexer.CharacterPos = 1
Lexer.SourceText = src

tokens = []
count = 0
while True:
    count += 1
    if count > 20:
        print("BREAK - too many tokens", flush=True)
        break
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
    print(f"  Token {count}: type={Token}, name={Token.name}, val={val}", flush=True)
    if Token == LexToken.TokenEOF:
        break
