import ctypes

from interpreter import *

ALIGN_SIZE = 8


def MEM_ALIGN(x):
    return (x + ALIGN_SIZE - 1) & ~(ALIGN_SIZE - 1)


class HeapModule:
    @staticmethod
    def Init(pc, StackSize):
        pc.HeapMemory = bytearray(StackSize)
        AlignOffset = 0
        pc.StackFrame = AlignOffset
        pc.HeapStackTop = AlignOffset
        pc.HeapBottom = StackSize - ALIGN_SIZE + AlignOffset
        pc.FreeListBig = None
        pc.FreeListBucket = [None] * FREELIST_BUCKETS

    @staticmethod
    def Cleanup(pc):
        pc.HeapMemory = None

    @staticmethod
    def AllocStack(pc, Size):
        NewMem = pc.HeapStackTop
        NewTop = pc.HeapStackTop + MEM_ALIGN(Size)
        if NewTop > pc.HeapBottom:
            return None
        pc.HeapStackTop = NewTop
        return NewMem

    @staticmethod
    def UnpopStack(pc, Size):
        pc.HeapStackTop += MEM_ALIGN(Size)

    @staticmethod
    def PopStack(pc, Addr, Size):
        ToLose = MEM_ALIGN(Size)
        if ToLose > (pc.HeapStackTop - 0):
            return False
        pc.HeapStackTop -= ToLose
        return True

    @staticmethod
    def PushStackFrame(pc):
        pc.StackFrame = pc.HeapStackTop
        pc.HeapStackTop += MEM_ALIGN(ALIGN_SIZE)

    @staticmethod
    def PopStackFrame(pc):
        if pc.StackFrame is not None and pc.HeapStackTop is not None:
            pc.HeapStackTop = pc.StackFrame
            return True
        return False

    @staticmethod
    def AllocMem(pc, Size):
        return bytearray(Size)

    @staticmethod
    def FreeMem(pc, Mem):
        pass
