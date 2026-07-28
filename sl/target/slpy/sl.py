"""
Pure Python implementation of sl (Steam Locomotive).
Direct conversion from sl.c and sl.h.
"""

import sys
import random

# Constants from sl.h
D51HEIGHT = 10
D51FUNNEL = 7
D51LENGTH = 83
D51PATTERNS = 6

D51STR1 = "      ====        ________                ___________ "
D51STR2 = "  _D _|  |_______/        \\__I_I_____===__|_________| "
D51STR3 = "   |(_)---  |   H\\________/ |   |        =|___ ___|   "
D51STR4 = "   /     |  |   H  |  |     |   |         ||_| |_||   "
D51STR5 = "  |      |  |   H  |__--------------------| [___] |   "
D51STR6 = "  | ________|___H__/__|_____/[][]~\\_______|       |   "
D51STR7 = "  |/ |   |-----------I_____I [][] []  D   |=======|__ "

D51WHL11 = "__/ =| o |=-~~\\  /~~\\  /~~\\  /~~\\ ____Y___________|__ "
D51WHL12 = " |/-=|___|=    ||    ||    ||    |_____/~\\___/        "
D51WHL13 = "  \\_/      \\O=====O=====O=====O_/      \\_/            "

D51WHL21 = "__/ =| o |=-~~\\  /~~\\  /~~\\  /~~\\ ____Y___________|__ "
D51WHL22 = " |/-=|___|=O=====O=====O=====O   |_____/~\\___/        "
D51WHL23 = "  \\_/      \\__/  \\__/  \\__/  \\__/      \\_/            "

D51WHL31 = "__/ =| o |=-O=====O=====O=====O \\ ____Y___________|__ "
D51WHL32 = " |/-=|___|=    ||    ||    ||    |_____/~\\___/        "
D51WHL33 = "  \\_/      \\__/  \\__/  \\__/  \\__/      \\_/            "

D51WHL41 = "__/ =| o |=-~O=====O=====O=====O\\ ____Y___________|__ "
D51WHL42 = " |/-=|___|=    ||    ||    ||    |_____/~\\___/        "
D51WHL43 = "  \\_/      \\__/  \\__/  \\__/  \\__/      \\_/            "

D51WHL51 = "__/ =| o |=-~~\\  /~~\\  /~~\\  /~~\\ ____Y___________|__ "
D51WHL52 = " |/-=|___|=   O=====O=====O=====O|_____/~\\___/        "
D51WHL53 = "  \\_/      \\__/  \\__/  \\__/  \\__/      \\_/            "

D51WHL61 = "__/ =| o |=-~~\\  /~~\\  /~~\\  /~~\\ ____Y___________|__ "
D51WHL62 = " |/-=|___|=    ||    ||    ||    |_____/~\\___/        "
D51WHL63 = "  \\_/      \\_O=====O=====O=====O/      \\_/            "

D51DEL = "                                                      "

COAL01 = "                              "
COAL02 = "                              "
COAL03 = "    _________________         "
COAL04 = "   _|                \\_____A  "
COAL05 = " =|                        |  "
COAL06 = " -|                        |  "
COAL07 = "__|________________________|_ "
COAL08 = "|__________________________|_ "
COAL09 = "   |_D__D__D_|  |_D__D__D_|   "
COAL10 = "    \\_/   \\_/    \\_/   \\_/    "

COALDEL = "                              "

LOGOHEIGHT = 6
LOGOFUNNEL = 4
LOGOLENGTH = 84
LOGOPATTERNS = 6

LOGO1 = "     ++      +------ "
LOGO2 = "     ||      |+-+ |  "
LOGO3 = "   /---------|| | |  "
LOGO4 = "  + ========  +-+ |  "

LWHL11 = " _|--O========O~\\-+  "
LWHL12 = "//// \\_/      \\_/    "

LWHL21 = " _|--/O========O\\-+  "
LWHL22 = "//// \\_/      \\_/    "

LWHL31 = " _|--/~O========O-+  "
LWHL32 = "//// \\_/      \\_/    "

LWHL41 = " _|--/~\\------/~\\-+  "
LWHL42 = "//// \\_O========O    "

LWHL51 = " _|--/~\\------/~\\-+  "
LWHL52 = "//// \\O========O/    "

LWHL61 = " _|--/~\\------/~\\-+  "
LWHL62 = "//// O========O_/    "

LCOAL1 = "____                 "
LCOAL2 = "|   \\@@@@@@@@@@@     "
LCOAL3 = "|    \\@@@@@@@@@@@@@_ "
LCOAL4 = "|                  | "
LCOAL5 = "|__________________| "
LCOAL6 = "   (O)       (O)     "

LCAR1 = "____________________ "
LCAR2 = "|  ___ ___ ___ ___ | "
LCAR3 = "|  |_| |_| |_| |_| | "
LCAR4 = "|__________________| "
LCAR5 = "|__________________| "
LCAR6 = "   (O)        (O)    "

DELLN = "                     "

C51HEIGHT = 11
C51FUNNEL = 7
C51LENGTH = 87
C51PATTERNS = 6

C51DEL = "                                                       "

C51STR1 = "        ___                                            "
C51STR2 = "       _|_|_  _     __       __             ___________"
C51STR3 = "    D__/   \\_(_)___|  |__H__|  |_____I_Ii_()|_________|"
C51STR4 = "     | `---'   |:: `--'  H  `--'         |  |___ ___|  "
C51STR5 = "    +|~~~~~~~~++::~~~~~~~H~~+=====+~~~~~~|~~||_| |_||  "
C51STR6 = "    ||        | ::       H  +=====+      |  |::  ...|  "
C51STR7 = "|    | _______|_::-----------------[][]-----|       |  "

C51WH11 = "| /~~ ||   |-----/~~~~\\  /[I_____I][][] --|||_______|__"
C51WH12 = "------'|oOo|=[]=-      ||      ||      |  ||=======_|__"
C51WH13 = "/~\\____|___|/~\\_|  O=======O=======O   |__|+-/~\\_|     "
C51WH14 = "\\_/         \\_/  \\____/  \\____/  \\____/      \\_/       "

C51WH21 = "| /~~ ||   |-----/~~~~\\  /[I_____I][][] --|||_______|__"
C51WH22 = "------'|oOo|=[]=- O=======O=======O    |  ||=======_|__"
C51WH23 = "/~\\____|___|/~\\_|      ||      ||      |__|+-/~\\_|     "
C51WH24 = "\\_/         \\_/  \\____/  \\____/  \\____/      \\_/       "

C51WH31 = "| /~~ ||   |-----/~~~~\\  /[I_____I][][] --|||_______|__"
C51WH32 = "------'|oOo|==[]=- O=======O=======O   |  ||=======_|__"
C51WH33 = "/~\\____|___|/~\\_|      ||      ||      |__|+-/~\\_|     "
C51WH34 = "\\_/         \\_/  \\____/  \\____/  \\____/      \\_/       "

C51WH41 = "| /~~ ||   |-----/~~~~\\  /[I_____I][][] --|||_______|__"
C51WH42 = "------'|oOo|===[]=- O=======O=======O  |  ||=======_|__"
C51WH43 = "/~\\____|___|/~\\_|      ||      ||      |__|+-/~\\_|     "
C51WH44 = "\\_/         \\_/  \\____/  \\____/  \\____/      \\_/       "

C51WH51 = "| /~~ ||   |-----/~~~~\\  /[I_____I][][] --|||_______|__"
C51WH52 = "------'|oOo|===[]=-    ||      ||      |  ||=======_|__"
C51WH53 = "/~\\____|___|/~\\_|    O=======O=======O |__|+-/~\\_|     "
C51WH54 = "\\_/         \\_/  \\____/  \\____/  \\____/      \\_/       "

C51WH61 = "| /~~ ||   |-----/~~~~\\  /[I_____I][][] --|||_______|__"
C51WH62 = "------'|oOo|==[]=-     ||      ||      |  ||=======_|__"
C51WH63 = "/~\\____|___|/~\\_|   O=======O=======O  |__|+-/~\\_|     "
C51WH64 = "\\_/         \\_/  \\____/  \\____/  \\____/      \\_/       "

D51_PATTERNS = [
    [D51STR1, D51STR2, D51STR3, D51STR4, D51STR5, D51STR6, D51STR7, D51WHL11, D51WHL12, D51WHL13, D51DEL],
    [D51STR1, D51STR2, D51STR3, D51STR4, D51STR5, D51STR6, D51STR7, D51WHL21, D51WHL22, D51WHL23, D51DEL],
    [D51STR1, D51STR2, D51STR3, D51STR4, D51STR5, D51STR6, D51STR7, D51WHL31, D51WHL32, D51WHL33, D51DEL],
    [D51STR1, D51STR2, D51STR3, D51STR4, D51STR5, D51STR6, D51STR7, D51WHL41, D51WHL42, D51WHL43, D51DEL],
    [D51STR1, D51STR2, D51STR3, D51STR4, D51STR5, D51STR6, D51STR7, D51WHL51, D51WHL52, D51WHL53, D51DEL],
    [D51STR1, D51STR2, D51STR3, D51STR4, D51STR5, D51STR6, D51STR7, D51WHL61, D51WHL62, D51WHL63, D51DEL],
]

D51_COAL = [COAL01, COAL02, COAL03, COAL04, COAL05, COAL06, COAL07, COAL08, COAL09, COAL10, COALDEL]

LOGO_PATTERNS = [
    [LOGO1, LOGO2, LOGO3, LOGO4, LWHL11, LWHL12, DELLN],
    [LOGO1, LOGO2, LOGO3, LOGO4, LWHL21, LWHL22, DELLN],
    [LOGO1, LOGO2, LOGO3, LOGO4, LWHL31, LWHL32, DELLN],
    [LOGO1, LOGO2, LOGO3, LOGO4, LWHL41, LWHL42, DELLN],
    [LOGO1, LOGO2, LOGO3, LOGO4, LWHL51, LWHL52, DELLN],
    [LOGO1, LOGO2, LOGO3, LOGO4, LWHL61, LWHL62, DELLN],
]

LOGO_COAL = [LCOAL1, LCOAL2, LCOAL3, LCOAL4, LCOAL5, LCOAL6, DELLN]
LOGO_CAR = [LCAR1, LCAR2, LCAR3, LCAR4, LCAR5, LCAR6, DELLN]

C51_PATTERNS = [
    [C51STR1, C51STR2, C51STR3, C51STR4, C51STR5, C51STR6, C51STR7, C51WH11, C51WH12, C51WH13, C51WH14, C51DEL],
    [C51STR1, C51STR2, C51STR3, C51STR4, C51STR5, C51STR6, C51STR7, C51WH21, C51WH22, C51WH23, C51WH24, C51DEL],
    [C51STR1, C51STR2, C51STR3, C51STR4, C51STR5, C51STR6, C51STR7, C51WH31, C51WH32, C51WH33, C51WH34, C51DEL],
    [C51STR1, C51STR2, C51STR3, C51STR4, C51STR5, C51STR6, C51STR7, C51WH41, C51WH42, C51WH43, C51WH44, C51DEL],
    [C51STR1, C51STR2, C51STR3, C51STR4, C51STR5, C51STR6, C51STR7, C51WH51, C51WH52, C51WH53, C51WH54, C51DEL],
    [C51STR1, C51STR2, C51STR3, C51STR4, C51STR5, C51STR6, C51STR7, C51WH61, C51WH62, C51WH63, C51WH64, C51DEL],
]

C51_COAL = [COALDEL, COAL01, COAL02, COAL03, COAL04, COAL05, COAL06, COAL07, COAL08, COAL09, COAL10, COALDEL]

SMOKEPTNS = 16

Smoke = [
    ["(   )", "(    )", "(    )", "(   )", "(  )",
     "(  )", "( )", "( )", "()", "()",
     "O", "O", "O", "O", "O",
     " "],
    ["(@@@)", "(@@@@)", "(@@@@)", "(@@@)", "(@@)",
     "(@@)", "(@)", "(@)", "@@", "@@",
     "@", "@", "@", "@", "@",
     " "]
]

Eraser = [
    "     ", "      ", "      ", "     ", "    ",
    "    ", "   ", "   ", "  ", "  ",
    " ", " ", " ", " ", " ",
    " "
]

dy_smoke = [2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
dx_smoke = [-2, -1, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3]


class SmokeItem:
    __slots__ = ('y', 'x', 'ptrn', 'kind')

    def __init__(self, y, x, ptrn, kind):
        self.y = y
        self.x = x
        self.ptrn = ptrn
        self.kind = kind


class SL:
    def __init__(self):
        self.ACCIDENT = 0
        self.LOGO = 0
        self.FLY = 0
        self.C51 = 0
        self.DANCE = 0
        self.RAND = 0
        self.COLS = 0
        self.LINES = 0
        self.N = 0
        self.output_map = []
        self.sl_step = 0
        self.smoke_S = []
        self.smoke_sum = 0

    def count(self):
        min_val = 0
        offset = 21
        if self.LOGO >= 1:
            min_val = -LOGOLENGTH - 1 - offset * (self.LOGO - 1)
        elif self.C51 == 1:
            min_val = -C51LENGTH - 1
        else:
            min_val = -D51LENGTH - 1
        return min_val

    def addchModify(self, y, x, c):
        if y < 0 or x < 0 or x >= self.COLS or y >= self.LINES:
            return -1
        self.output_map[y][x] = ord(c) if isinstance(c, str) else c
        return 0

    def my_mvaddstr(self, y, x, s):
        idx = 0
        n = len(s)
        while x < 0:
            if idx >= n:
                return -1
            idx += 1
            x += 1
        while idx < n:
            if self.addchModify(y, x, s[idx]) == -1:
                return -1
            idx += 1
            x += 1
        return 0

    def option(self, s):
        for ch in s:
            if ch == '-':
                break
            if ch == 'l':
                self.LOGO += 1
            elif ch == 'a':
                self.ACCIDENT = 1
            elif ch == 'F':
                self.FLY = 1
            elif ch == 'c':
                self.C51 = 1
            elif ch == 'd':
                self.DANCE = 1
            elif ch == 'r':
                self.RAND = 1

    def windowInit(self, c, l, arg):
        self.COLS = c
        self.LINES = l
        self.ACCIDENT = 0
        self.LOGO = 0
        self.FLY = 0
        self.C51 = 0
        self.DANCE = 0
        self.RAND = 0

        i = 0
        n = len(arg)
        while i < n:
            if arg[i] == '-':
                self.option(arg[i + 1:])
            i += 1

        if self.RAND == 1:
            random.seed()
            self.ACCIDENT |= random.randint(0, 1)
            self.LOGO |= random.randint(0, 1)
            self.FLY |= random.randint(0, 1)
            self.C51 |= random.randint(0, 1)
            self.DANCE |= random.randint(0, 1)

        self.N = -self.count() + self.COLS - 1
        self.output_map = [bytearray(b' ' * self.COLS) for _ in range(self.LINES)]
        self.sl_step = 0
        self.smoke_S = []
        self.smoke_sum = 0

    def windowDestroy(self):
        self.output_map = []

    def step(self):
        if self.sl_step < self.N:
            self.mapModify(self.sl_step)
            self.sl_step += 1
            return "\n".join(row.decode('latin1') for row in self.output_map)
        elif self.sl_step == self.N:
            self.windowDestroy()
            self.sl_step += 1
            return None
        else:
            return None

    def mapModify(self, mod):
        x = -mod + self.COLS - 1
        if self.LOGO >= 1:
            self.add_sl(x)
        elif self.C51 == 1:
            self.add_C51(x)
        else:
            self.add_D51(x)

    def add_sl(self, x):
        py1 = 0
        py2 = 0
        py3 = 0
        offset = 21
        yoffset = 0

        y = self.LINES // 2 - 3

        if self.FLY == 1:
            y = int(x / 6) + self.LINES - int(self.COLS / 6) - LOGOHEIGHT
            py1 = 2
            py2 = 4
            py3 = 6

        pat_idx = int((LOGOLENGTH + offset * (self.LOGO - 1) + x) / 3) % LOGOPATTERNS
        for i in range(LOGOHEIGHT + 1):
            self.my_mvaddstr(y + i, x, LOGO_PATTERNS[pat_idx][i])
            self.my_mvaddstr(y + i + py1, x + 21, LOGO_COAL[i])
            for j in range(self.LOGO + 1):
                yoffset = 2 * j * self.FLY
                self.my_mvaddstr(y + i + py3 + yoffset, x + 42 + offset * j, LOGO_CAR[i])

        if self.ACCIDENT == 1:
            self.add_man(y + 1, x + 14)
            yoffset = 0
            for j in range(self.LOGO + 1):
                yoffset = self.FLY * (2 + 2 * j)
                self.add_man(y + 1 + py2 + yoffset, x + 45 + offset * j)
                self.add_man(y + 1 + py2 + yoffset, x + 53 + offset * j)

        if self.DANCE == 1 and self.ACCIDENT == 0 and self.FLY == 0:
            self.add_mdancer(y - 2, x + 21)
            for j in range(self.LOGO + 1):
                self.add_mdancer(y + py2 - 2, x + 45 + offset * j)
                self.add_mdancer(y + py2 - 2, x + 50 + offset * j)
                self.add_mdancer(y + py2 - 2, x + 55 + offset * j)

        self.add_smoke(y - 1, x + LOGOFUNNEL)
        return 0

    def add_D51(self, x):
        dy = 0
        y = self.LINES // 2 - 5

        if self.FLY == 1:
            y = int(x / 7) + self.LINES - int(self.COLS / 7) - D51HEIGHT
            dy = 1

        pat_idx = (D51LENGTH + x) % D51PATTERNS
        for i in range(D51HEIGHT + 1):
            self.my_mvaddstr(y + i, x, D51_PATTERNS[pat_idx][i])
            self.my_mvaddstr(y + i + dy, x + 53, D51_COAL[i])

        if self.ACCIDENT == 1:
            self.add_man(y + 2, x + 43)
            self.add_man(y + 2, x + 47)

        if self.DANCE == 1 and self.ACCIDENT == 0 and self.FLY == 0:
            self.add_mdancer(y - 2, x + 43)
            self.add_fdancer(y - 2, x + 48)

        self.add_smoke(y - 1, x + D51FUNNEL)
        return 0

    def add_C51(self, x):
        dy = 0
        y = self.LINES // 2 - 5

        if self.FLY == 1:
            y = int(x / 7) + self.LINES - int(self.COLS / 7) - C51HEIGHT
            dy = 1

        pat_idx = (C51LENGTH + x) % C51PATTERNS
        for i in range(C51HEIGHT + 1):
            self.my_mvaddstr(y + i, x, C51_PATTERNS[pat_idx][i])
            self.my_mvaddstr(y + i + dy, x + 55, C51_COAL[i])

        if self.ACCIDENT == 1:
            self.add_man(y + 3, x + 45)
            self.add_man(y + 3, x + 49)

        if self.DANCE == 1 and self.ACCIDENT == 0 and self.FLY == 0:
            self.add_mdancer(y - 1, x + 45)
            self.add_fdancer(y - 1, x + 50)

        self.add_smoke(y - 1, x + C51FUNNEL)
        return 0

    def add_man(self, y, x):
        man = [["", "(O)"], ["Help!", "\\O/"]]
        pat_idx = int((LOGOLENGTH + x) / 12) % 2
        for i in range(2):
            self.my_mvaddstr(y + i, x, man[pat_idx][i])

    def add_fdancer(self, y, x):
        fdancer = [["\\\\0", "/\\", "|\\"], ["0//", "/\\", "/|"]]
        Efdancer = [["   ", "  ", "  "], ["   ", "  ", "  "]]
        pat_idx = int((LOGOLENGTH + x) / 12) % 2
        for i in range(3):
            self.my_mvaddstr(y + i, x + 1, Efdancer[pat_idx][i])
            self.my_mvaddstr(y + i, x, fdancer[pat_idx][i])

    def add_mdancer(self, y, x):
        mdancer = [["_O_", " #", "/\\"], ["(0)", " #", "/\\"], ["(O_", " #", "/\\"]]
        Emdancer = [["   ", "  ", "  "], ["   ", "  ", "  "], ["   ", "  ", "  "]]
        pat_idx = int((LOGOLENGTH + x) / 12) % 3
        for i in range(3):
            self.my_mvaddstr(y + i, x + 1, Emdancer[pat_idx][i])
            self.my_mvaddstr(y + i, x, mdancer[pat_idx][i])

    def add_smoke(self, y, x):
        if x % 4 == 0:
            for i in range(self.smoke_sum):
                item = self.smoke_S[i]
                self.my_mvaddstr(item.y, item.x, Eraser[item.ptrn])
                item.y -= dy_smoke[item.ptrn]
                item.x += dx_smoke[item.ptrn]
                if item.ptrn < SMOKEPTNS - 1:
                    item.ptrn += 1
                self.my_mvaddstr(item.y, item.x, Smoke[item.kind][item.ptrn])

            self.my_mvaddstr(y, x, Smoke[self.smoke_sum % 2][0])
            self.smoke_S.append(SmokeItem(y, x, 0, self.smoke_sum % 2))
            self.smoke_sum += 1


def sl(cols, lines, arg=''):
    engine = SL()
    engine.windowInit(cols, lines, arg)
    while True:
        x = engine.step()
        if x is not None:
            yield x
        else:
            return
