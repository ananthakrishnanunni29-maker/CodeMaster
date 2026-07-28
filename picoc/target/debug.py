from interpreter import *


class DebugModule:
    @staticmethod
    def Init(pc):
        pc.BreakpointCount = 0

    @staticmethod
    def Cleanup(pc):
        pass

    @staticmethod
    def CheckStatement(Parser):
        pass

    @staticmethod
    def SetBreakpoint(Parser):
        pass

    @staticmethod
    def ClearBreakpoint(Parser):
        return False
