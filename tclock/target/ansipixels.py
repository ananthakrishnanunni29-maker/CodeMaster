import sys
import os
import math
import shutil
import time
import colorsys
import select

# Try importing termios/tty/msvcrt for raw terminal mode
IS_WINDOWS = sys.platform == "win32"
if IS_WINDOWS:
    import msvcrt
    import ctypes
    from ctypes import wintypes
else:
    import termios
    import tty

# ANSI Escape Sequences
RESET = "\x1b[0m"
INVERSE = "\x1b[7m"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
CLEAR_SCREEN = "\x1b[2J\x1b[H"
SAVE_CURSOR = "\x1b[s"
RESTORE_CURSOR = "\x1b[u"
SYNC_START = "\x1b[?2026h"
SYNC_END = "\x1b[?2026l"

FULL_PIXEL = "█"
BOTTOM_HALF_PIXEL = "▄"

ColorHelp = "red, green, blue, yellow, cyan, magenta, white, black, gray, orange, RRGGBB, or h,s,l"


class RGBColor:
    def __init__(self, r: int = 0, g: int = 0, b: int = 0):
        self.r = max(0, min(255, int(r)))
        self.g = max(0, min(255, int(g)))
        self.b = max(0, min(255, int(b)))

    def __eq__(self, other):
        if not isinstance(other, RGBColor):
            return False
        return self.r == other.r and self.g == other.g and self.b == other.b

    def __hash__(self):
        return hash((self.r, self.g, self.b))

    def foreground(self, truecolor: bool = True) -> str:
        if truecolor:
            return f"\x1b[38;2;{self.r};{self.g};{self.b}m"
        # 256-color fallback
        code = 16 + (36 * (self.r // 51)) + (6 * (self.g // 51)) + (self.b // 51)
        return f"\x1b[38;5;{code}m"

    def background(self, truecolor: bool = True) -> str:
        if truecolor:
            return f"\x1b[48;2;{self.r};{self.g};{self.b}m"
        code = 16 + (36 * (self.r // 51)) + (6 * (self.g // 51)) + (self.b // 51)
        return f"\x1b[48;5;{code}m"

    def color(self) -> 'RGBColor':
        return self


BLACK = RGBColor(0, 0, 0)
WHITE = RGBColor(255, 255, 255)
RED = RGBColor(255, 0, 0)
GREEN = RGBColor(0, 255, 0)
BLUE = RGBColor(0, 0, 255)
YELLOW = RGBColor(255, 255, 0)
CYAN = RGBColor(0, 255, 255)
MAGENTA = RGBColor(255, 0, 255)
GRAY = RGBColor(128, 128, 128)
ORANGE = RGBColor(255, 165, 0)

NAMED_COLORS = {
    "black": BLACK,
    "white": WHITE,
    "red": RED,
    "green": GREEN,
    "blue": BLUE,
    "yellow": YELLOW,
    "cyan": CYAN,
    "magenta": MAGENTA,
    "gray": GRAY,
    "grey": GRAY,
    "orange": ORANGE,
}


def parse_color(s: str) -> RGBColor:
    s = s.strip().lower()
    if not s:
        return BLACK
    if s in NAMED_COLORS:
        return NAMED_COLORS[s]
    if s.startswith("#"):
        s = s[1:]
    if len(s) == 6:
        try:
            r = int(s[0:2], 16)
            g = int(s[2:4], 16)
            b = int(s[4:6], 16)
            return RGBColor(r, g, b)
        except ValueError:
            pass
    if len(s) == 3:
        try:
            r = int(s[0] * 2, 16)
            g = int(s[1] * 2, 16)
            b = int(s[2] * 2, 16)
            return RGBColor(r, g, b)
        except ValueError:
            pass
    # HSL or float RGB: e.g. "0.5,1.0,0.5"
    if "," in s:
        parts = [p.strip() for p in s.split(",")]
        if len(parts) == 3:
            try:
                vals = [float(p) for p in parts]
                if all(0.0 <= v <= 1.0 for v in vals):
                    # Interpret as HSL
                    h, s_val, l = vals
                    r_f, g_f, b_f = colorsys.hls_to_rgb(h, l, s_val)
                    return RGBColor(r_f * 255, g_f * 255, b_f * 255)
            except ValueError:
                pass
    raise ValueError(f"Invalid color specification: {s}")


def blend_nsrgb(c1: RGBColor, c2: RGBColor, alpha: float) -> RGBColor:
    alpha = max(0.0, min(1.0, alpha))
    r = c1.r * (1.0 - alpha) + c2.r * alpha
    g = c1.g * (1.0 - alpha) + c2.g * alpha
    b = c1.b * (1.0 - alpha) + c2.b * alpha
    return RGBColor(r, g, b)


def blend_linear(c1: RGBColor, c2: RGBColor, alpha: float) -> RGBColor:
    alpha = max(0.0, min(1.0, alpha))
    r = math.sqrt((c1.r ** 2) * (1.0 - alpha) + (c2.r ** 2) * alpha)
    g = math.sqrt((c1.g ** 2) * (1.0 - alpha) + (c2.g ** 2) * alpha)
    b = math.sqrt((c1.b ** 2) * (1.0 - alpha) + (c2.b ** 2) * alpha)
    return RGBColor(r, g, b)


class ColorOutput:
    def __init__(self, truecolor: bool = True):
        self.truecolor = truecolor

    def foreground(self, color: RGBColor) -> str:
        return color.foreground(self.truecolor)

    def background(self, color: RGBColor) -> str:
        return color.background(self.truecolor)


def detect_truecolor() -> bool:
    ct = os.environ.get("COLORTERM", "").lower()
    if ct in ("truecolor", "24bit"):
        return True
    term = os.environ.get("TERM", "").lower()
    if "direct" in term or "24bit" in term or "truecolor" in term:
        return True
    return True  # Modern terminals almost all support 24-bit RGB


class AnsiPixels:
    def __init__(self, fps: float = 30.0):
        self.fps = fps
        self.TrueColor = detect_truecolor()
        self.ColorOutput = ColorOutput(self.TrueColor)
        self.Background = BLACK
        self.W = 80
        self.H = 24
        self.Mx = -1
        self.My = -1
        self._left_click = False
        self._mouse_release = False
        self.Data = ""
        self.Out = sys.stdout
        self.old_settings = None
        self.OnResize = None
        self.get_size()

    def get_size(self) -> tuple[int, int]:
        try:
            cols, lines = shutil.get_terminal_size((80, 24))
            self.W = cols
            self.H = lines
        except Exception:
            self.W = 80
            self.H = 24
        return self.W, self.H

    def open(self):
        self.get_size()
        if not IS_WINDOWS and sys.stdin.isatty():
            try:
                self.old_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno())
            except Exception:
                pass

    def restore(self):
        if not IS_WINDOWS and self.old_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            except Exception:
                pass

    def write_string(self, s: str):
        self.Out.write(s)
        self.Out.flush()

    def write_rune(self, r: str):
        self.Out.write(r)

    def move_cursor(self, x: int, y: int):
        # ANSI 1-based indexing
        self.Out.write(f"\x1b[{y + 1};{x + 1}H")

    def write_at(self, x: int, y: int, fmt: str, *args):
        self.move_cursor(x, y)
        if args:
            self.Out.write(fmt % args)
        else:
            self.Out.write(fmt)

    def write_at_str(self, x: int, y: int, s: str):
        self.move_cursor(x, y)
        self.Out.write(s)

    def start_sync_mode(self):
        self.Out.write(SYNC_START)

    def end_sync_mode(self):
        self.Out.write(SYNC_END)
        self.Out.flush()

    def clear_screen(self):
        self.Out.write(CLEAR_SCREEN)
        self.Out.flush()

    def hide_cursor(self):
        self.Out.write(HIDE_CURSOR)
        self.Out.flush()

    def show_cursor(self):
        self.Out.write(SHOW_CURSOR)
        self.Out.flush()

    def mouse_tracking_on(self):
        self.Out.write("\x1b[?1000h\x1b[?1002h\x1b[?1006h")
        self.Out.flush()

    def mouse_tracking_off(self):
        self.Out.write("\x1b[?1006l\x1b[?1002l\x1b[?1000l")
        self.Out.flush()

    def save_cursor_pos(self):
        self.Out.write(SAVE_CURSOR)
        self.Out.flush()

    def restore_cursor_pos(self):
        self.Out.write(RESTORE_CURSOR)
        self.Out.flush()

    def sync_background_color(self):
        pass

    def screen_width(self, s: str) -> int:
        # Calculate visual width stripping ANSI sequences
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        plain = ansi_escape.sub('', s)
        return len(plain)

    def draw_round_box(self, x: int, y: int, w: int, h: int):
        if w < 2 or h < 2:
            return
        # Top line
        self.write_at_str(x, y, "╭" + "─" * (w - 2) + "╮")
        # Sides
        for i in range(1, h - 1):
            self.write_at_str(x, y + i, "│")
            self.write_at_str(x + w - 1, y + i, "│")
        # Bottom line
        self.write_at_str(x, y + h - 1, "╰" + "─" * (w - 2) + "╯")

    def draw_square_box(self, x: int, y: int, w: int, h: int):
        if w < 2 or h < 2:
            return
        self.write_at_str(x, y, "┌" + "─" * (w - 2) + "┐")
        for i in range(1, h - 1):
            self.write_at_str(x, y + i, "│")
            self.write_at_str(x + w - 1, y + i, "│")
        self.write_at_str(x, y + h - 1, "└" + "─" * (w - 2) + "┘")

    def draw_colored_box(self, x: int, y: int, w: int, h: int, color_prefix: str, fill: bool = False):
        self.Out.write(color_prefix)
        self.draw_round_box(x, y, w, h)
        self.Out.write(RESET)

    def disc_blend_fn(self, cx: int, cy: int, radius: int, bg: RGBColor, fg: RGBColor, aliasing: float, blending_fn):
        if radius <= 0:
            return
        inner_r = radius * (1.0 - aliasing)
        
        # Subpixel resolution (2 vertical subpixels per char cell)
        sub_cy = cy * 2
        sub_r = radius * 2
        
        for y_cell in range(max(0, cy - radius), min(self.H, cy + radius + 1)):
            for x_cell in range(max(0, cx - radius), min(self.W, cx + radius + 1)):
                # Top subpixel
                py0 = y_cell * 2
                dist0 = math.sqrt((x_cell - cx) ** 2 + ((py0 - sub_cy) / 2.0) ** 2)
                
                # Bottom subpixel
                py1 = y_cell * 2 + 1
                dist1 = math.sqrt((x_cell - cx) ** 2 + ((py1 - sub_cy) / 2.0) ** 2)

                def get_color(dist: float) -> RGBColor:
                    if dist >= radius:
                        return bg
                    if dist <= inner_r or aliasing <= 0:
                        return fg
                    alpha = (radius - dist) / (radius * aliasing)
                    return blending_fn(bg, fg, alpha)

                c0 = get_color(dist0)
                c1 = get_color(dist1)

                if c0 == bg and c1 == bg:
                    continue

                self.move_cursor(x_cell, y_cell)
                if c0 == c1:
                    self.Out.write(c0.foreground(self.TrueColor) + c0.background(self.TrueColor) + FULL_PIXEL)
                else:
                    self.Out.write(c1.foreground(self.TrueColor) + c0.background(self.TrueColor) + BOTTOM_HALF_PIXEL)
        
        self.Out.write(RESET)

    def show_scaled_image(self, img) -> bool:
        """
        Renders a PIL Image to terminal using ANSI subpixel half-blocks.
        img bounds: width = W, height = 2*H
        """
        if img is None:
            return False
        w, h = img.size
        pixels = img.load()
        for y_cell in range(h // 2):
            self.move_cursor(0, y_cell)
            for x in range(w):
                p_top = pixels[x, 2 * y_cell]
                p_bot = pixels[x, 2 * y_cell + 1]
                
                # Handle RGBA/RGB/NRGBA tuple
                c_top = RGBColor(p_top[0], p_top[1], p_top[2])
                c_bot = RGBColor(p_bot[0], p_bot[1], p_bot[2])
                
                if c_top == c_bot:
                    self.Out.write(c_top.foreground(self.TrueColor) + c_top.background(self.TrueColor) + FULL_PIXEL)
                else:
                    self.Out.write(c_bot.foreground(self.TrueColor) + c_top.background(self.TrueColor) + BOTTOM_HALF_PIXEL)
        self.Out.write(RESET)
        self.Out.flush()
        return True

    def left_click(self) -> bool:
        return self._left_click

    def mouse_release(self) -> bool:
        return self._mouse_release

    def read_or_resize_or_signal_once(self) -> tuple[int, Exception | None]:
        # Check window resize
        old_w, old_h = self.W, self.H
        self.get_size()
        if (self.W != old_w or self.H != old_h) and self.OnResize:
            self.OnResize()

        self.Data = ""
        self._left_click = False
        self._mouse_release = False

        timeout = 1.0 / self.fps if self.fps > 0 else 0.05
        
        if IS_WINDOWS:
            time.sleep(timeout)
            if msvcrt.kbhit():
                try:
                    ch = msvcrt.getch().decode('utf-8', errors='ignore')
                    self.Data = ch
                except Exception:
                    pass
            return len(self.Data), None
        else:
            rlist, _, _ = select.select([sys.stdin], [], [], timeout)
            if rlist:
                try:
                    data = sys.stdin.read(1024)
                    self.Data = data
                    # Check mouse SGR sequence: \x1b[<0;X;YM or \x1b[<0;X;Ym
                    if "\x1b[<" in data:
                        import re
                        m = re.search(r'\x1b\[<(\d+);(\d+);(\d+)([Mm])', data)
                        if m:
                            btn, mx, my, release = int(m.group(1)), int(m.group(2)) - 1, int(m.group(3)) - 1, m.group(4)
                            self.Mx, self.My = mx, my
                            if btn == 0:
                                self._left_click = True
                                if release == 'm':
                                    self._mouse_release = True
                except Exception:
                    pass
            return len(self.Data), None
