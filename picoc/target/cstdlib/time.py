import time as pytime
from interpreter import *
from variable import VariableModule


class StdTimeModule:
    @staticmethod
    def Setup(pc):
        VariableModule.DefinePlatformVar(pc, None, "CLOCKS_PER_SEC", pc.IntType, 1000000, False)

StdTimeDefs = "typedef int clock_t; typedef int time_t; struct tm { int tm_sec; int tm_min; int tm_hour; int tm_mday; int tm_mon; int tm_year; int tm_wday; int tm_yday; int tm_isdst; };"


def StdTimeClock(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.LongInteger = int(pytime.perf_counter() * 1000000)

def StdTimeTime(Parser, ReturnValue, Param, NumArgs):
    ReturnValue.Val.LongInteger = int(pytime.time())

StdTimeFunctions = [
    LibraryFunction(StdTimeClock, "clock_t clock();"),
    LibraryFunction(StdTimeTime, "time_t time(time_t *);"),
]
