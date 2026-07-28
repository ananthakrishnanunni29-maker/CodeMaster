#!/usr/bin/env python3
"""
qrterminal - QR code generator for the terminal (Pure Python Port).
Converted from Go (qrterminal.go & cmd/qrterminal/main.go) to pure Python.
No external dependencies required.
"""

import sys
import os

# Reconfigure stdout/stderr to UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Enable ANSI console colors on Windows
if os.name == "nt":
    try:
        import colorama
        colorama.just_fix_windows_console()
    except Exception:
        os.system("")

# Constants matching qrterminal.go
WHITE = "\033[47m  \033[0m"
BLACK = "\033[40m  \033[0m"

BLACK_WHITE = "▄"
BLACK_BLACK = " "
WHITE_BLACK = "▀"
WHITE_WHITE = "█"

L = 0  # 7%
M = 1  # 15%
Q = 2  # 25%
H = 3  # 30%

QUIET_ZONE = 4

SIXEL_BEGIN = "\x1bPq\n#0;2;0;0;0#1;2;100;100;100\n"
SIXEL_END = "\x1b\\"
SIXEL_BLOCK_SIZE = 12

LEVEL_CODES = {
    L: 0b01,
    M: 0b00,
    Q: 0b11,
    H: 0b10,
}

# Galois Field GF(2^8) math for Reed-Solomon
GF_EXP = [0] * 512
GF_LOG = [0] * 256

def _init_gf():
    x = 1
    for i in range(255):
        GF_EXP[i] = x
        GF_LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        GF_EXP[i] = GF_EXP[i - 255]

_init_gf()

def gf_mul(x, y):
    if x == 0 or y == 0:
        return 0
    return GF_EXP[GF_LOG[x] + GF_LOG[y]]

def rs_generator_poly(nsym):
    g = [1]
    for i in range(nsym):
        g_next = [0] * (len(g) + 1)
        for j, coef in enumerate(g):
            g_next[j] ^= coef
            g_next[j + 1] ^= gf_mul(coef, GF_EXP[i])
        g = g_next
    return g

def rs_encode(data, nsym):
    gen = rs_generator_poly(nsym)
    res = [0] * nsym
    for b in data:
        factor = b ^ res[0]
        res = res[1:] + [0]
        if factor != 0:
            for j in range(nsym):
                res[j] ^= gf_mul(gen[j + 1], factor)
    return res

# QR Spec Table for versions 1 to 40
SPEC = {
    1: {L: (26, 7, 1, 19, 0, 0), M: (26, 10, 1, 16, 0, 0), Q: (26, 13, 1, 13, 0, 0), H: (26, 17, 1, 9, 0, 0)},
    2: {L: (44, 10, 1, 34, 0, 0), M: (44, 16, 1, 28, 0, 0), Q: (44, 22, 1, 22, 0, 0), H: (44, 28, 1, 16, 0, 0)},
    3: {L: (70, 15, 1, 55, 0, 0), M: (70, 26, 1, 44, 0, 0), Q: (70, 18, 2, 17, 0, 0), H: (70, 22, 2, 13, 0, 0)},
    4: {L: (100, 20, 1, 80, 0, 0), M: (100, 18, 2, 32, 0, 0), Q: (100, 26, 2, 24, 0, 0), H: (100, 16, 4, 9, 0, 0)},
    5: {L: (134, 26, 1, 108, 0, 0), M: (134, 24, 2, 43, 0, 0), Q: (134, 18, 2, 15, 2, 16), H: (134, 22, 2, 11, 2, 12)},
    6: {L: (172, 18, 2, 68, 0, 0), M: (172, 16, 4, 27, 0, 0), Q: (172, 24, 4, 19, 0, 0), H: (172, 28, 4, 15, 0, 0)},
    7: {L: (196, 20, 2, 78, 0, 0), M: (196, 18, 4, 31, 0, 0), Q: (196, 18, 2, 14, 4, 15), H: (196, 26, 4, 13, 1, 14)},
    8: {L: (242, 24, 2, 97, 0, 0), M: (242, 22, 2, 38, 2, 39), Q: (242, 22, 4, 18, 2, 19), H: (242, 26, 4, 14, 2, 15)},
    9: {L: (292, 30, 2, 116, 0, 0), M: (292, 22, 3, 36, 2, 37), Q: (292, 20, 4, 16, 4, 17), H: (292, 24, 4, 12, 4, 13)},
    10: {L: (346, 18, 2, 68, 2, 69), M: (346, 26, 4, 43, 1, 44), Q: (346, 24, 6, 19, 2, 20), H: (346, 28, 6, 15, 2, 16)},
    11: {L: (404, 20, 4, 81, 0, 0), M: (404, 30, 1, 50, 4, 51), Q: (404, 28, 4, 22, 4, 23), H: (404, 24, 3, 12, 8, 13)},
    12: {L: (466, 24, 2, 92, 2, 93), M: (466, 22, 6, 36, 2, 37), Q: (466, 26, 4, 20, 6, 21), H: (466, 28, 7, 14, 4, 15)},
    13: {L: (532, 26, 4, 107, 0, 0), M: (532, 22, 8, 37, 1, 38), Q: (532, 24, 8, 20, 4, 21), H: (532, 22, 12, 11, 4, 12)},
    14: {L: (581, 30, 3, 115, 1, 116), M: (581, 24, 4, 40, 5, 41), Q: (581, 20, 11, 16, 5, 17), H: (581, 24, 11, 12, 5, 13)},
    15: {L: (655, 22, 5, 87, 1, 88), M: (655, 24, 5, 41, 5, 42), Q: (655, 30, 5, 24, 7, 25), H: (655, 24, 11, 12, 7, 13)},
    16: {L: (733, 24, 5, 98, 1, 99), M: (733, 28, 7, 45, 3, 46), Q: (733, 24, 15, 19, 2, 20), H: (733, 30, 3, 15, 13, 16)},
    17: {L: (815, 28, 1, 107, 5, 108), M: (815, 28, 10, 46, 1, 47), Q: (815, 28, 1, 22, 15, 23), H: (815, 28, 2, 14, 17, 15)},
    18: {L: (901, 30, 5, 120, 1, 121), M: (901, 26, 9, 43, 4, 44), Q: (901, 28, 17, 22, 1, 23), H: (901, 28, 2, 14, 19, 15)},
    19: {L: (991, 28, 3, 113, 4, 114), M: (991, 26, 3, 44, 11, 45), Q: (991, 26, 17, 21, 4, 22), H: (991, 26, 9, 13, 16, 14)},
    20: {L: (1085, 28, 3, 107, 5, 108), M: (1085, 26, 3, 41, 13, 42), Q: (1085, 30, 15, 24, 5, 25), H: (1085, 28, 15, 15, 10, 16)},
    21: {L: (1156, 28, 4, 116, 4, 117), M: (1156, 26, 17, 42, 0, 0), Q: (1156, 28, 17, 22, 6, 23), H: (1156, 30, 19, 16, 6, 17)},
    22: {L: (1258, 28, 2, 111, 7, 112), M: (1258, 28, 17, 46, 0, 0), Q: (1258, 30, 7, 24, 16, 25), H: (1258, 24, 34, 13, 0, 0)},
    23: {L: (1364, 30, 4, 121, 5, 122), M: (1364, 28, 4, 47, 14, 48), Q: (1364, 30, 11, 24, 14, 25), H: (1364, 30, 16, 15, 14, 16)},
    24: {L: (1474, 30, 6, 117, 4, 118), M: (1474, 28, 6, 45, 14, 46), Q: (1474, 30, 11, 24, 16, 25), H: (1474, 30, 30, 16, 2, 17)},
    25: {L: (1588, 26, 8, 106, 4, 107), M: (1588, 28, 8, 47, 13, 48), Q: (1588, 30, 7, 24, 22, 25), H: (1588, 30, 22, 15, 13, 16)},
    26: {L: (1706, 28, 10, 114, 2, 115), M: (1706, 28, 19, 46, 4, 47), Q: (1706, 28, 28, 22, 6, 23), H: (1706, 30, 33, 16, 4, 17)},
    27: {L: (1828, 30, 8, 122, 4, 123), M: (1828, 28, 22, 45, 3, 46), Q: (1828, 30, 8, 23, 26, 24), H: (1828, 30, 12, 15, 28, 16)},
    28: {L: (1921, 30, 3, 117, 10, 118), M: (1921, 28, 3, 45, 23, 46), Q: (1921, 30, 4, 24, 31, 25), H: (1921, 30, 11, 15, 31, 16)},
    29: {L: (2051, 30, 7, 116, 7, 117), M: (2051, 28, 21, 45, 7, 46), Q: (2051, 30, 1, 23, 37, 24), H: (2051, 30, 19, 15, 26, 16)},
    30: {L: (2185, 30, 5, 115, 10, 116), M: (2185, 28, 19, 47, 10, 48), Q: (2185, 30, 15, 24, 25, 25), H: (2185, 30, 23, 15, 25, 16)},
    31: {L: (2323, 30, 13, 115, 3, 116), M: (2323, 28, 2, 46, 29, 47), Q: (2323, 30, 42, 24, 1, 25), H: (2323, 30, 23, 15, 28, 16)},
    32: {L: (2465, 30, 17, 115, 0, 0), M: (2465, 28, 10, 46, 23, 47), Q: (2465, 30, 10, 24, 35, 25), H: (2465, 30, 19, 15, 35, 16)},
    33: {L: (2611, 30, 17, 115, 1, 116), M: (2611, 28, 14, 46, 21, 47), Q: (2611, 30, 29, 24, 19, 25), H: (2611, 30, 11, 15, 46, 16)},
    34: {L: (2761, 30, 13, 115, 6, 116), M: (2761, 28, 14, 46, 23, 47), Q: (2761, 30, 44, 24, 7, 25), H: (2761, 30, 59, 16, 1, 17)},
    35: {L: (2876, 30, 12, 121, 7, 122), M: (2876, 28, 12, 47, 26, 48), Q: (2876, 30, 39, 24, 14, 25), H: (2876, 30, 22, 15, 41, 16)},
    36: {L: (3034, 30, 6, 121, 14, 122), M: (3034, 28, 6, 47, 34, 48), Q: (3034, 30, 46, 24, 10, 25), H: (3034, 30, 2, 15, 64, 16)},
    37: {L: (3196, 30, 17, 122, 4, 123), M: (3196, 28, 29, 46, 14, 47), Q: (3196, 30, 49, 24, 10, 25), H: (3196, 30, 24, 15, 46, 16)},
    38: {L: (3362, 30, 4, 122, 18, 123), M: (3362, 28, 13, 46, 32, 47), Q: (3362, 30, 48, 24, 14, 25), H: (3362, 30, 42, 15, 32, 16)},
    39: {L: (3532, 30, 20, 117, 4, 118), M: (3532, 28, 40, 47, 7, 48), Q: (3532, 30, 43, 24, 22, 25), H: (3532, 30, 10, 15, 67, 16)},
    40: {L: (3706, 30, 19, 118, 6, 119), M: (3706, 28, 18, 47, 31, 48), Q: (3706, 30, 34, 24, 34, 25), H: (3706, 30, 20, 15, 61, 16)},
}

ALIGNMENT_LOC = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42],
    9: [6, 26, 46], 10: [6, 28, 50], 11: [6, 30, 54], 12: [6, 32, 58], 13: [6, 34, 62], 14: [6, 26, 46, 66],
    15: [6, 26, 48, 70], 16: [6, 26, 50, 74], 17: [6, 30, 54, 78], 18: [6, 30, 56, 82], 19: [6, 30, 58, 86],
    20: [6, 34, 62, 90], 21: [6, 28, 50, 72, 94], 22: [6, 26, 50, 74, 98], 23: [6, 30, 54, 78, 102],
    24: [6, 28, 54, 80, 106], 25: [6, 32, 58, 84, 110], 26: [6, 30, 58, 86, 114], 27: [6, 34, 62, 90, 118],
    28: [6, 26, 50, 74, 98, 122], 29: [6, 30, 54, 78, 102, 126], 30: [6, 26, 52, 78, 104, 130],
    31: [6, 30, 56, 82, 108, 134], 32: [6, 34, 60, 86, 112, 138], 33: [6, 30, 58, 86, 114, 142],
    34: [6, 34, 62, 90, 118, 146], 35: [6, 30, 54, 78, 102, 126, 150], 36: [6, 24, 50, 76, 102, 128, 154],
    37: [6, 28, 54, 80, 106, 132, 158], 38: [6, 32, 58, 84, 110, 136, 162], 39: [6, 26, 54, 82, 110, 138, 166],
    40: [6, 30, 58, 86, 114, 142, 170],
}

class Code:
    def __init__(self, version, matrix):
        self.version = version
        self.grid_size = 17 + 4 * version
        self.size = self.grid_size - 1  # Matches rsc.io/qr convention
        self.matrix = matrix

    def black(self, x, y):
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            return bool(self.matrix[y][x])
        return False

def get_bch_format(data):
    d = data << 10
    g = 0x537
    for i in range(4, -1, -1):
        if (d >> (i + 10)) & 1:
            d ^= g << i
    return ((data << 10) | d) ^ 0x5412

def get_bch_version(version):
    d = version << 12
    g = 0x1F25
    for i in range(5, -1, -1):
        if (d >> (i + 12)) & 1:
            d ^= g << i
    return (version << 12) | d

def select_version_and_level(data_len, level):
    if level not in LEVEL_CODES:
        level = L
    for v in range(1, 41):
        spec = SPEC[v][level]
        g1_b, g1_d, g2_b, g2_d = spec[2], spec[3], spec[4], spec[5]
        total_data_bytes = g1_b * g1_d + g2_b * g2_d
        cc_bits = 8 if v <= 9 else 16
        req_bits = 4 + cc_bits + data_len * 8
        if req_bits <= total_data_bytes * 8:
            return v, level
    raise ValueError("Data too long for QR Code")

def qr_encode(text, level=L):
    if level not in LEVEL_CODES:
        level = L
    data_bytes = text.encode("utf-8")
    version, level = select_version_and_level(len(data_bytes), level)
    
    spec = SPEC[version][level]
    total_cw, ec_bytes_per_block, g1_b, g1_d, g2_b, g2_d = spec
    total_data_bytes = g1_b * g1_d + g2_b * g2_d
    
    bits = []
    for b in "0100":
        bits.append(int(b))
    
    cc_bits = 8 if version <= 9 else 16
    cc_str = format(len(data_bytes), f"0{cc_bits}b")
    for b in cc_str:
        bits.append(int(b))
        
    for byte in data_bytes:
        for b in format(byte, "08b"):
            bits.append(int(b))
            
    term_len = min(4, total_data_bytes * 8 - len(bits))
    bits.extend([0] * term_len)
    
    while len(bits) % 8 != 0:
        bits.append(0)
        
    cw_bytes = []
    for i in range(0, len(bits), 8):
        b_val = 0
        for j in range(8):
            b_val = (b_val << 1) | bits[i + j]
        cw_bytes.append(b_val)
        
    pad_bytes = [0xEC, 0x11]
    pad_idx = 0
    while len(cw_bytes) < total_data_bytes:
        cw_bytes.append(pad_bytes[pad_idx])
        pad_idx = 1 - pad_idx
        
    blocks_data = []
    blocks_ec = []
    idx = 0
    for _ in range(g1_b):
        b = cw_bytes[idx : idx + g1_d]
        idx += g1_d
        blocks_data.append(b)
        blocks_ec.append(rs_encode(b, ec_bytes_per_block))
    for _ in range(g2_b):
        b = cw_bytes[idx : idx + g2_d]
        idx += g2_d
        blocks_data.append(b)
        blocks_ec.append(rs_encode(b, ec_bytes_per_block))
        
    final_data = []
    max_d_len = max(len(b) for b in blocks_data)
    for i in range(max_d_len):
        for b in blocks_data:
            if i < len(b):
                final_data.append(b[i])
    for i in range(ec_bytes_per_block):
        for b in blocks_ec:
            final_data.append(b[i])
            
    N = 17 + 4 * version
    matrix = [[0] * N for _ in range(N)]
    reserved = [[False] * N for _ in range(N)]
    
    def place_finder(top_r, left_c):
        for r in range(7):
            for c in range(7):
                if r == 0 or r == 6 or c == 0 or c == 6 or (2 <= r <= 4 and 2 <= c <= 4):
                    matrix[top_r + r][left_c + c] = 1
                else:
                    matrix[top_r + r][left_c + c] = 0
                reserved[top_r + r][left_c + c] = True
        for r in range(-1, 8):
            for c in range(-1, 8):
                nr, nc = top_r + r, left_c + c
                if 0 <= nr < N and 0 <= nc < N:
                    reserved[nr][nc] = True
                    
    place_finder(0, 0)
    place_finder(0, N - 7)
    place_finder(N - 7, 0)
    
    for i in range(N):
        if not reserved[6][i]:
            matrix[6][i] = 1 if i % 2 == 0 else 0
            reserved[6][i] = True
        if not reserved[i][6]:
            matrix[i][6] = 1 if i % 2 == 0 else 0
            reserved[i][6] = True
            
    locs = ALIGNMENT_LOC[version]
    for r in locs:
        for c in locs:
            if any(reserved[r + dr][c + dc] for dr in range(-2, 3) for dc in range(-2, 3)):
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr, nc = r + dr, c + dc
                    if abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0):
                        matrix[nr][nc] = 1
                    else:
                        matrix[nr][nc] = 0
                    reserved[nr][nc] = True
                    
    for i in range(9):
        reserved[8][i] = True
        reserved[i][8] = True
    for i in range(8):
        reserved[8][N - 1 - i] = True
    for i in range(7):
        reserved[N - 1 - i][8] = True
    matrix[N - 8][8] = 1
    reserved[N - 8][8] = True
    
    if version >= 7:
        for r in range(6):
            for c in range(3):
                reserved[N - 11 + c][r] = True
                reserved[r][N - 11 + c] = True
                
    all_data_bits = []
    for val in final_data:
        for b in format(val, "08b"):
            all_data_bits.append(int(b))
            
    bit_idx = 0
    col = N - 1
    up = True
    while col > 0:
        if col == 6:
            col -= 1
        row_range = range(N - 1, -1, -1) if up else range(N)
        for row in row_range:
            for c in (col, col - 1):
                if not reserved[row][c]:
                    if bit_idx < len(all_data_bits):
                        matrix[row][c] = all_data_bits[bit_idx]
                        bit_idx += 1
                    else:
                        matrix[row][c] = 0
        col -= 2
        up = not up
        
    def get_masked_bit(r, c, mask_idx, val):
        if mask_idx == 0:
            cond = (r + c) % 2 == 0
        elif mask_idx == 1:
            cond = r % 2 == 0
        elif mask_idx == 2:
            cond = c % 3 == 0
        elif mask_idx == 3:
            cond = (r + c) % 3 == 0
        elif mask_idx == 4:
            cond = (r // 2 + c // 3) % 2 == 0
        elif mask_idx == 5:
            cond = ((r * c) % 2) + ((r * c) % 3) == 0
        elif mask_idx == 6:
            cond = (((r * c) % 2) + ((r * c) % 3)) % 2 == 0
        else:
            cond = (((r + c) % 2) + ((r * c) % 3)) % 2 == 0
        return val ^ (1 if cond else 0)

    best_mask = 0
    min_penalty = float("inf")
    best_grid = None

    for mask_idx in range(8):
        grid = [[0] * N for _ in range(N)]
        for r in range(N):
            for c in range(N):
                if reserved[r][c]:
                    grid[r][c] = matrix[r][c]
                else:
                    grid[r][c] = get_masked_bit(r, c, mask_idx, matrix[r][c])

        penalty = 0
        for r in range(N):
            cnt = 1
            for c in range(1, N):
                if grid[r][c] == grid[r][c - 1]:
                    cnt += 1
                else:
                    if cnt >= 5:
                        penalty += 3 + (cnt - 5)
                    cnt = 1
            if cnt >= 5:
                penalty += 3 + (cnt - 5)

        for c in range(N):
            cnt = 1
            for r in range(1, N):
                if grid[r][c] == grid[r - 1][c]:
                    cnt += 1
                else:
                    if cnt >= 5:
                        penalty += 3 + (cnt - 5)
                    cnt = 1
            if cnt >= 5:
                penalty += 3 + (cnt - 5)

        for r in range(N - 1):
            for c in range(N - 1):
                if grid[r][c] == grid[r + 1][c] == grid[r][c + 1] == grid[r + 1][c + 1]:
                    penalty += 3

        p1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
        p2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]
        for r in range(N):
            for c in range(N - 10):
                sub = grid[r][c : c + 11]
                if sub == p1 or sub == p2:
                    penalty += 40
        for c in range(N):
            for r in range(N - 10):
                sub = [grid[r + k][c] for k in range(11)]
                if sub == p1 or sub == p2:
                    penalty += 40

        dark_cnt = sum(sum(row) for row in grid)
        pct = (dark_cnt * 100) // (N * N)
        k = abs(pct - 50) // 5
        penalty += k * 10

        if penalty < min_penalty:
            min_penalty = penalty
            best_mask = mask_idx
            best_grid = grid

    final_grid = best_grid
    lvl_bits = LEVEL_CODES[level]
    format_data = (lvl_bits << 3) | best_mask
    format_bch = get_bch_format(format_data)
    
    f_bits = [int(x) for x in format(format_bch, "015b")]
    
    final_grid[8][0] = f_bits[0]
    final_grid[8][1] = f_bits[1]
    final_grid[8][2] = f_bits[2]
    final_grid[8][3] = f_bits[3]
    final_grid[8][4] = f_bits[4]
    final_grid[8][5] = f_bits[5]
    final_grid[8][7] = f_bits[6]
    final_grid[8][8] = f_bits[7]
    
    final_grid[7][8] = f_bits[8]
    final_grid[5][8] = f_bits[9]
    final_grid[4][8] = f_bits[10]
    final_grid[3][8] = f_bits[11]
    final_grid[2][8] = f_bits[12]
    final_grid[1][8] = f_bits[13]
    final_grid[0][8] = f_bits[14]
    
    for i in range(7):
        final_grid[N - 1 - i][8] = f_bits[i]
        
    for i in range(8):
        final_grid[8][N - 8 + i] = f_bits[7 + i]
        
    if version >= 7:
        v_bch = get_bch_version(version)
        v_bits = [int(x) for x in format(v_bch, "018b")]
        idx = 17
        for r in range(6):
            for c in range(3):
                bit = v_bits[idx]
                final_grid[r][N - 11 + c] = bit
                final_grid[N - 11 + c][r] = bit
                idx -= 1

    return Code(version, final_grid)

class Config:
    def __init__(
        self,
        level=L,
        writer=None,
        half_blocks=False,
        black_char="",
        black_white_char="",
        white_char="",
        white_black_char="",
        quiet_zone=QUIET_ZONE,
        with_sixel=False,
    ):
        self.level = level
        self.writer = writer if writer is not None else sys.stdout
        self.half_blocks = half_blocks
        self.black_char = black_char
        self.black_white_char = black_white_char
        self.white_char = white_char
        self.white_black_char = white_black_char
        self.quiet_zone = quiet_zone
        self.with_sixel = with_sixel

def _safe_write(w, s):
    try:
        w.write(s)
    except (UnicodeEncodeError, AttributeError):
        if hasattr(w, "buffer"):
            w.buffer.write(s.encode("utf-8"))
            w.buffer.flush()
        else:
            w.write(s.encode("utf-8", "replace").decode("utf-8", "replace"))

def is_sixel_supported(w=None):
    if w is None:
        w = sys.stdout
    if w != sys.stdout:
        return False
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    return False

def _string_repeat(s, count):
    if count <= 0:
        return ""
    return s * count

def write_sixel(config, w, code):
    size = SIXEL_BLOCK_SIZE
    if code.size > 50:
        size //= 2
    line = size // 6

    _safe_write(w, SIXEL_BEGIN)
    top_line = f"#1!{size * (code.size + config.quiet_zone * 2)}~-\n"
    _safe_write(w, _string_repeat(top_line, config.quiet_zone * line))

    for i in range(code.size + 1):
        flag = -1
        repeat = 0
        content = []
        if config.quiet_zone > 0:
            content.append(f"#1!{size * config.quiet_zone}~")

        for j in range(code.size + 1):
            if code.black(j, i):
                if flag == 1:
                    content.append(f"#1!{size * repeat}~")
                    repeat = 0
                flag = 0
                repeat += 1
            else:
                if flag == 0:
                    content.append(f"#0!{size * repeat}~")
                    repeat = 0
                flag = 1
                repeat += 1
        if repeat > 0:
            content.append(f"#{flag}!{size * repeat}~")
        if config.quiet_zone > 1:
            content.append(f"#1!{size * (config.quiet_zone - 1)}~")
        content.append("-\n")

        line_str = "".join(content)
        for _ in range(line):
            _safe_write(w, line_str)

    bottom_line = f"#1!{size * (code.size + config.quiet_zone * 2)}~-\n"
    _safe_write(w, _string_repeat(bottom_line, (config.quiet_zone - 1) * line))
    if config.quiet_zone > 1:
        _safe_write(w, f"#1!{size * (code.size + config.quiet_zone * 2)}~-")
    _safe_write(w, SIXEL_END)

def write_full_blocks(config, w, code):
    white = config.white_char
    black = config.black_char

    full_width = code.size + config.quiet_zone * 2
    top_border = _string_repeat(_string_repeat(white, full_width) + "\n", config.quiet_zone)
    _safe_write(w, top_border)

    for i in range(code.size + 1):
        _safe_write(w, _string_repeat(white, config.quiet_zone))
        for j in range(code.size + 1):
            if code.black(j, i):
                _safe_write(w, black)
            else:
                _safe_write(w, white)
        _safe_write(w, _string_repeat(white, config.quiet_zone - 1) + "\n")

    bottom_border = _string_repeat(_string_repeat(white, full_width) + "\n", config.quiet_zone - 1)
    _safe_write(w, bottom_border)

def write_half_blocks(config, w, code):
    ww = config.white_char
    bb = config.black_char
    wb = config.white_black_char
    bw = config.black_white_char

    full_width = code.size + config.quiet_zone * 2
    if config.quiet_zone % 2 != 0:
        _safe_write(w, _string_repeat(bw, full_width) + "\n")
        _safe_write(w, _string_repeat(_string_repeat(ww, full_width) + "\n", config.quiet_zone // 2))
    else:
        _safe_write(w, _string_repeat(_string_repeat(ww, full_width) + "\n", config.quiet_zone // 2))

    for i in range(0, code.size + 1, 2):
        _safe_write(w, _string_repeat(ww, config.quiet_zone))
        for j in range(code.size + 1):
            next_black = False
            if i + 1 < code.size:
                next_black = code.black(j, i + 1)
            curr_black = code.black(j, i)
            if curr_black and next_black:
                _safe_write(w, bb)
            elif curr_black and not next_black:
                _safe_write(w, bw)
            elif not curr_black and not next_black:
                _safe_write(w, ww)
            else:
                _safe_write(w, wb)
        _safe_write(w, _string_repeat(ww, config.quiet_zone - 1) + "\n")

    if config.quiet_zone % 2 == 0:
        _safe_write(w, _string_repeat(_string_repeat(ww, full_width) + "\n", config.quiet_zone // 2 - 1))
        _safe_write(w, _string_repeat(wb, full_width) + "\n")
    else:
        _safe_write(w, _string_repeat(_string_repeat(ww, full_width) + "\n", config.quiet_zone // 2))

def generate_with_config(text, config):
    if config.quiet_zone < 1:
        config.quiet_zone = 1

    w = config.writer
    code = qr_encode(text, config.level)

    if not config.black_char:
        config.black_char = BLACK_BLACK
    if not config.white_black_char:
        config.white_black_char = WHITE_BLACK
    if not config.white_char:
        config.white_char = WHITE_WHITE
    if not config.black_white_char:
        config.black_white_char = BLACK_WHITE

    if config.half_blocks:
        write_half_blocks(config, w, code)
    elif config.with_sixel:
        write_sixel(config, w, code)
    else:
        write_full_blocks(config, w, code)

def generate(text, l=L, w=None):
    if w is None:
        w = sys.stdout
    config = Config(
        level=l,
        writer=w,
        black_char=BLACK,
        white_char=WHITE,
        quiet_zone=QUIET_ZONE,
    )
    config.with_sixel = is_sixel_supported(w)
    generate_with_config(text, config)

def generate_half_block(text, l=L, w=None):
    if w is None:
        w = sys.stdout
    config = Config(
        level=l,
        writer=w,
        half_blocks=True,
        black_char=BLACK_BLACK,
        white_black_char=WHITE_BLACK,
        white_char=WHITE_WHITE,
        black_white_char=BLACK_WHITE,
        quiet_zone=QUIET_ZONE,
    )
    generate_with_config(text, config)

def get_level(s):
    l = s.lower()
    if l == "l":
        return L
    elif l == "m":
        return M
    elif l == "h":
        return H
    else:
        return -1

def main():
    args = sys.argv[1:]
    verbose_flag = False
    level_flag = "L"
    quiet_zone_flag = 2
    sixel_disable_flag = False
    half_blocks_flag = False

    pos_args = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-m", "--m", "-half", "--half"):
            half_blocks_flag = True
            i += 1
        elif arg.startswith("-m=") or arg.startswith("--m=") or arg.startswith("--half="):
            val = arg.split("=", 1)[1]
            half_blocks_flag = val.lower() in ("true", "1", "t", "yes")
            i += 1
        elif arg in ("-v", "--v"):
            verbose_flag = True
            i += 1
        elif arg.startswith("-v=") or arg.startswith("--v="):
            val = arg.split("=", 1)[1]
            verbose_flag = val.lower() in ("true", "1", "t", "yes")
            i += 1
        elif arg in ("-l", "--l"):
            if i + 1 < len(args):
                level_flag = args[i + 1]
                i += 2
            else:
                i += 1
        elif arg.startswith("-l=") or arg.startswith("--l="):
            level_flag = arg.split("=", 1)[1]
            i += 1
        elif arg in ("-q", "--q"):
            if i + 1 < len(args):
                try:
                    quiet_zone_flag = int(args[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                i += 1
        elif arg.startswith("-q=") or arg.startswith("--q="):
            try:
                quiet_zone_flag = int(arg.split("=", 1)[1])
            except ValueError:
                pass
            i += 1
        elif arg in ("-s", "--s"):
            sixel_disable_flag = True
            i += 1
        elif arg.startswith("-s=") or arg.startswith("--s="):
            val = arg.split("=", 1)[1]
            sixel_disable_flag = val.lower() in ("true", "1", "t", "yes")
            i += 1
        elif arg == "--":
            pos_args.extend(args[i + 1 :])
            break
        elif arg.startswith("-") and len(arg) > 1:
            if arg.startswith("-l"):
                level_flag = arg[2:]
            elif arg.startswith("-q"):
                try:
                    quiet_zone_flag = int(arg[2:])
                except ValueError:
                    pass
            i += 1
        else:
            pos_args.append(arg)
            i += 1

    level = get_level(level_flag)
    content = " ".join(pos_args)

    if len(content) < 1:
        content = sys.stdin.read()
    elif level < 0:
        _safe_write(sys.stderr, f"Invalid error correction level: {level_flag}\n")
        _safe_write(sys.stderr, "Valid options are [L, M, H]\n")
        sys.exit(1)

    if level < 0:
        _safe_write(sys.stderr, f"Invalid error correction level: {level_flag}\n")
        _safe_write(sys.stderr, "Valid options are [L, M, H]\n")
        sys.exit(1)

    cfg = Config(
        level=level,
        writer=sys.stdout,
        quiet_zone=quiet_zone_flag,
        black_char=BLACK,
        white_char=WHITE,
    )
    if half_blocks_flag:
        cfg.half_blocks = True
        cfg.black_char = BLACK_BLACK
        cfg.white_black_char = WHITE_BLACK
        cfg.white_char = WHITE_WHITE
        cfg.black_white_char = BLACK_WHITE
    if not sixel_disable_flag:
        cfg.with_sixel = is_sixel_supported(sys.stdout)

    if verbose_flag:
        _safe_write(sys.stdout, f"Level: {level_flag} \n")
        _safe_write(sys.stdout, f"Quietzone Border Size: {quiet_zone_flag} \n")
        _safe_write(sys.stdout, f"Encoded data: {'\n'.join(pos_args)} \n")
        _safe_write(sys.stdout, "\n")

    _safe_write(sys.stdout, "\n")
    generate_with_config(content, cfg)

if __name__ == "__main__":
    main()
