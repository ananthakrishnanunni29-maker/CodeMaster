from interpreter import *

def TableHash(Key, Len):
    h = Len
    offset = 8
    for i in range(Len):
        if offset > 25:
            offset -= 25
        h ^= (ord(Key[i]) if isinstance(Key[i], str) else Key[i]) << offset
        offset += 7
    return h

class TableModule:
    @staticmethod
    def Init(pc):
        TableModule.InitTable(pc.StringTable, STRING_TABLE_SIZE, True)
        pc.StrEmpty = TableModule.StrRegister(pc, "")

    @staticmethod
    def InitTable(Tbl, size, on_heap):
        Tbl.Size = size
        Tbl.OnHeap = on_heap
        Tbl.entries = {}

    @staticmethod
    def Set(pc, Tbl, Key, Val, DeclFileName=None, DeclLine=0, DeclColumn=0):
        if Key is None or Key == "":
            return False
        if Key in Tbl.entries:
            return False
        entry = TableEntry()
        entry.DeclFileName = DeclFileName
        entry.DeclLine = DeclLine
        entry.DeclColumn = DeclColumn
        entry.Key = Key
        entry.Val = Val
        Tbl.entries[Key] = entry
        return True

    @staticmethod
    def Get(Tbl, Key):
        if Key is None or Key == "":
            return None
        entry = Tbl.entries.get(Key)
        if entry is not None:
            return entry.Val
        return None

    @staticmethod
    def Delete(pc, Tbl, Key):
        if Key is None or Key == "":
            return None
        entry = Tbl.entries.pop(Key, None)
        if entry is not None:
            return entry.Val
        return None

    @staticmethod
    def StrRegister(pc, Str):
        if Str is None:
            return ""
        return TableModule.StrRegister2(pc, Str, len(Str))

    @staticmethod
    def StrRegister2(pc, Str, Len):
        if Str is None:
            return ""
        key = Str[:Len]
        existing = pc.StringTable.entries.get(key)
        if existing is not None:
            return existing.Key
        entry = TableEntry()
        entry.Key = key
        pc.StringTable.entries[key] = entry
        return key

    @staticmethod
    def StrFree(pc):
        pc.StringTable.entries = {}

    @staticmethod
    def SetIdentifier(pc, Tbl, Ident, IdentLen):
        key = Ident[:IdentLen]
        existing = Tbl.entries.get(key)
        if existing is not None:
            return existing.Key
        entry = TableEntry()
        entry.Key = key
        Tbl.entries[key] = entry
        return key
