_malloc_blocks = {}

def _get_block(ptr):
    if ptr is None:
        return None
    if isinstance(ptr, str):
        return ptr.encode('latin-1', errors='replace')
    if isinstance(ptr, int):
        return _malloc_blocks.get(ptr)
    return None

def _get_string(ptr):
    if ptr is None:
        return ""
    if isinstance(ptr, str):
        return ptr
    if isinstance(ptr, int):
        block = _malloc_blocks.get(ptr)
        if block is not None:
            null_pos = block.find(b'\x00')
            if null_pos >= 0:
                return block[:null_pos].decode('latin-1', errors='replace')
            return block.decode('latin-1', errors='replace')
    return str(ptr)

def _put_block(key, block):
    _malloc_blocks[key] = block

def _del_block(key):
    _malloc_blocks.pop(key, None)