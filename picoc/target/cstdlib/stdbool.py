from interpreter import *
from variable import VariableModule

StdboolDefs = "typedef int bool;"


class StdboolModule:
    @staticmethod
    def Setup(pc):
        trueVal = 1
        falseVal = 0
        VariableModule.DefinePlatformVar(pc, None, "true", pc.IntType, trueVal, False)
        VariableModule.DefinePlatformVar(pc, None, "false", pc.IntType, falseVal, False)
        VariableModule.DefinePlatformVar(pc, None, "__bool_true_false_are_defined", pc.IntType, trueVal, False)
