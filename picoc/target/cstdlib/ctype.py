from interpreter import *
from expression import ExpressionModule

class CTypeModule:
    @staticmethod
    def Setup(pc):
        pass

class CTypeFunctions:
    pass

def StdIsalnum(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = 1 if str.isalnum(chr(Param[0].Val.Integer & 0xFF)) else 0

def StdIsalpha(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = 1 if chr(Param[0].Val.Integer & 0xFF).isalpha() else 0

def StdIsblank(Parser, ReturnValue, Param, NumArgs):
    ch = Param[0].Val.Integer & 0xFF
    ReturnValue.Val.Integer = 1 if ch == ord(' ') or ch == ord('\t') else 0

def StdIscntrl(Parser, ReturnValue, Param, NumArgs):
    ch = Param[0].Val.Integer & 0xFF
    ReturnValue.Val.Integer = 1 if ch < 32 or ch == 127 else 0

def StdIsdigit(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = 1 if chr(Param[0].Val.Integer & 0xFF).isdigit() else 0

def StdIsgraph(Parser, ReturnValue, Param, NumArgs):
    ch = Param[0].Val.Integer & 0xFF
    ReturnValue.Val.Integer = 1 if 33 <= ch <= 126 else 0

def StdIslower(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = 1 if chr(Param[0].Val.Integer & 0xFF).islower() else 0

def StdIsprint(Parser, ReturnValue, Param, NumArgs):
    ch = Param[0].Val.Integer & 0xFF
    ReturnValue.Val.Integer = 1 if 32 <= ch <= 126 else 0

def StdIspunct(Parser, ReturnValue, Param, NumArgs):
    ch = Param[0].Val.Integer & 0xFF
    ReturnValue.Val.Integer = 1 if (33 <= ch <= 47) or (58 <= ch <= 64) or (91 <= ch <= 96) or (123 <= ch <= 126) else 0

def StdIsspace(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = 1 if chr(Param[0].Val.Integer & 0xFF).isspace() else 0

def StdIsupper(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = 1 if chr(Param[0].Val.Integer & 0xFF).isupper() else 0

def StdIsxdigit(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = 1 if chr(Param[0].Val.Integer & 0xFF).isxdigit() else 0

def StdTolower(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = chr(Param[0].Val.Integer & 0xFF).lower()

def StdToupper(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.Integer = chr(Param[0].Val.Integer & 0xFF).upper()

StdCtypeFunctions = [
    LibraryFunction(StdIsalnum, "int isalnum(int);"),
    LibraryFunction(StdIsalpha, "int isalpha(int);"),
    LibraryFunction(StdIsblank, "int isblank(int);"),
    LibraryFunction(StdIscntrl, "int iscntrl(int);"),
    LibraryFunction(StdIsdigit, "int isdigit(int);"),
    LibraryFunction(StdIsgraph, "int isgraph(int);"),
    LibraryFunction(StdIslower, "int islower(int);"),
    LibraryFunction(StdIsprint, "int isprint(int);"),
    LibraryFunction(StdIspunct, "int ispunct(int);"),
    LibraryFunction(StdIsspace, "int isspace(int);"),
    LibraryFunction(StdIsupper, "int isupper(int);"),
    LibraryFunction(StdIsxdigit, "int isxdigit(int);"),
    LibraryFunction(StdTolower, "int tolower(int);"),
    LibraryFunction(StdToupper, "int toupper(int);"),
]
