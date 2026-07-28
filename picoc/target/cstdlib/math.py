import math
from interpreter import *
from variable import VariableModule


class MathModule:
    @staticmethod
    def Setup(pc):
        VariableModule.DefinePlatformVar(pc, None, "M_E", pc.FPType, math.e, False)
        VariableModule.DefinePlatformVar(pc, None, "M_LOG2E", pc.FPType, math.log2(math.e), False)
        VariableModule.DefinePlatformVar(pc, None, "M_LOG10E", pc.FPType, math.log10(math.e), False)
        VariableModule.DefinePlatformVar(pc, None, "M_LN2", pc.FPType, math.log(2), False)
        VariableModule.DefinePlatformVar(pc, None, "M_LN10", pc.FPType, math.log(10), False)
        VariableModule.DefinePlatformVar(pc, None, "M_PI", pc.FPType, math.pi, False)
        VariableModule.DefinePlatformVar(pc, None, "M_PI_2", pc.FPType, math.pi / 2, False)
        VariableModule.DefinePlatformVar(pc, None, "M_PI_4", pc.FPType, math.pi / 4, False)
        VariableModule.DefinePlatformVar(pc, None, "M_1_PI", pc.FPType, 1.0 / math.pi, False)
        VariableModule.DefinePlatformVar(pc, None, "M_2_PI", pc.FPType, 2.0 / math.pi, False)
        VariableModule.DefinePlatformVar(pc, None, "M_2_SQRTPI", pc.FPType, 2.0 / math.sqrt(math.pi), False)
        VariableModule.DefinePlatformVar(pc, None, "M_SQRT2", pc.FPType, math.sqrt(2), False)
        VariableModule.DefinePlatformVar(pc, None, "M_SQRT1_2", pc.FPType, 1.0 / math.sqrt(2), False)


def MathSin(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.sin(Param[0].Val.FP)

def MathCos(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.cos(Param[0].Val.FP)

def MathTan(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.tan(Param[0].Val.FP)

def MathAsin(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.asin(Param[0].Val.FP)

def MathAcos(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.acos(Param[0].Val.FP)

def MathAtan(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.atan(Param[0].Val.FP)

def MathAtan2(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.atan2(Param[0].Val.FP, Param[1].Val.FP)

def MathSinh(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.sinh(Param[0].Val.FP)

def MathCosh(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.cosh(Param[0].Val.FP)

def MathTanh(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.tanh(Param[0].Val.FP)

def MathExp(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.exp(Param[0].Val.FP)

def MathFabs(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.fabs(Param[0].Val.FP)

def MathFmod(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.fmod(Param[0].Val.FP, Param[1].Val.FP)

def MathLdexp(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.ldexp(Param[0].Val.FP, int(Param[1].Val.Integer))

def MathLog(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.log(Param[0].Val.FP)

def MathLog10(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.log10(Param[0].Val.FP)

def MathPow(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.pow(Param[0].Val.FP, Param[1].Val.FP)

def MathSqrt(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.sqrt(Param[0].Val.FP)

def MathCeil(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.ceil(Param[0].Val.FP)

def MathFloor(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.FP = math.floor(Param[0].Val.FP)

MathFunctions = [
    LibraryFunction(MathAcos, "float acos(float);"),
    LibraryFunction(MathAsin, "float asin(float);"),
    LibraryFunction(MathAtan, "float atan(float);"),
    LibraryFunction(MathAtan2, "float atan2(float, float);"),
    LibraryFunction(MathCeil, "float ceil(float);"),
    LibraryFunction(MathCos, "float cos(float);"),
    LibraryFunction(MathCosh, "float cosh(float);"),
    LibraryFunction(MathExp, "float exp(float);"),
    LibraryFunction(MathFabs, "float fabs(float);"),
    LibraryFunction(MathFloor, "float floor(float);"),
    LibraryFunction(MathFmod, "float fmod(float, float);"),
    LibraryFunction(MathLdexp, "float ldexp(float, int);"),
    LibraryFunction(MathLog, "float log(float);"),
    LibraryFunction(MathLog10, "float log10(float);"),
    LibraryFunction(MathPow, "float pow(float,float);"),
    LibraryFunction(MathSin, "float sin(float);"),
    LibraryFunction(MathSinh, "float sinh(float);"),
    LibraryFunction(MathSqrt, "float sqrt(float);"),
    LibraryFunction(MathTan, "float tan(float);"),
    LibraryFunction(MathTanh, "float tanh(float);"),
]
