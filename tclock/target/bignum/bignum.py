# Package bignum implements a display for large numbers using 7 segments style
# unicode for terminal output. In the style of early digital clocks.

NUMBERS = """
 ━━
┃  ┃

┃  ┃
 ━━


   ┃

   ┃


 ━━
   ┃
 ━━
┃
 ━━

 ━━
   ┃
 ━━
   ┃
 ━━


┃  ┃
 ━━
   ┃


 ━━
┃
 ━━
   ┃
 ━━

 ━━
┃
 ━━
┃  ┃
 ━━

 ━━
   ┃

   ┃


 ━━
┃  ┃
 ━━
┃  ┃
 ━━

 ━━
┃  ┃
 ━━
   ┃
 ━━



::





..


"""

HEIGHT = 5
WIDTH = 4

NumberLines: list[str] = []


def add_trailing_spaces(s: str, extra: int) -> str:
    needed = WIDTH + extra - len(s)
    if needed > 0:
        s += " " * needed
    return s


def _init_number_lines():
    global NumberLines
    lines = NUMBERS.split("\n")[1:]
    processed = []
    for i, line in enumerate(lines):
        extra = 1
        if i >= 10 * (HEIGHT + 1):
            extra = -1  # no trailing space for colon / dot
        processed.append(add_trailing_spaces(line, extra))
    NumberLines = processed


_init_number_lines()


class Display:
    def __init__(self):
        self.lines = [""] * HEIGHT
        self.col = 0

    def __str__(self) -> str:
        return "\n".join(self.lines)

    def place_digit(self, r: str, blink: bool = False):
        if '0' <= r <= '9':
            digit = ord(r) - ord('0')
        else:
            digit = 10  # treat as colon
            if blink:
                digit = 11  # treat as dot
        start = digit * (HEIGHT + 1)
        for i in range(HEIGHT):
            if start + i < len(NumberLines):
                self.lines[i] += NumberLines[start + i]
        self.col += 1


def time_string(num_str: str, blink: bool = False) -> str:
    d = Display()
    for c in num_str:
        d.place_digit(c, blink)
    return str(d)
