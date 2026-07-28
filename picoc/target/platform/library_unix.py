from interpreter import *


class UnixLibraryModule:
    @staticmethod
    def PlatformLibraryInit(pc):
        from include_module import IncludeModule
        IncludeModule.Register(pc, "picoc_unix.h", None, None, None)
