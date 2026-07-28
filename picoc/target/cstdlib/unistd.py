from interpreter import *
from variable import VariableModule

UnistdDefs = "typedef int size_t; typedef long ssize_t;"


class UnistdModule:
    @staticmethod
    def Setup(pc):
        pass


def UnistdSleep(Parser, ReturnValue, Param, NumArgs):
    import time
    time.sleep(Param[0].Val.Integer)
    ReturnValue.Val.Integer = 0

def UnistdUsleep(Parser, ReturnValue, Param, NumArgs):
    import time
    time.sleep(Param[0].Val.Integer / 1000000.0)
    ReturnValue.Val.Integer = 0

def UnistdGetpid(Parser, ReturnValue, Param, NumArgs):
    import os
    ReturnValue.Val.Integer = os.getpid()

UnistdFunctions = [
    LibraryFunction(UnistdSleep, "unsigned int sleep(unsigned int);"),
    LibraryFunction(UnistdUsleep, "int usleep(int);"),
    LibraryFunction(UnistdGetpid, "int getpid();"),
]
