import math
from datetime import datetime
from ansipixels import AnsiPixels, RGBColor, RESET, FULL_PIXEL, BOTTOM_HALF_PIXEL


Point = tuple[int, int]
Pixels = dict[Point, RGBColor]


def draw_line(pix: Pixels, sx: int, sy: int, x0i: int, y0i: int, color: RGBColor):
    x1i = x0i + sx
    y0i *= 2
    y1i = y0i + sy

    steep = abs(y1i - y0i) > abs(x1i - x0i)
    if steep:
        x0i, y0i = y0i, x0i
        x1i, y1i = y1i, x1i

    if x0i > x1i:
        x0i, x1i = x1i, x0i
        y0i, y1i = y1i, y0i

    dx = x1i - x0i
    dy = abs(y1i - y0i)
    err = dx / 2.0
    y_step = 1 if y0i < y1i else -1

    y = y0i
    for x in range(x0i, x1i + 1):
        if steep:
            pix[(y, x)] = color
        else:
            pix[(x, y)] = color
        err -= dy
        if err < 0:
            y += y_step
            err += dx


class ColorState:
    def __init__(self):
        self.fg: RGBColor | None = None
        self.bg: RGBColor | None = None

    def set_fg(self, ap: AnsiPixels, c: RGBColor):
        if self.fg != c:
            self.fg = c
            ap.write_string(c.foreground(ap.TrueColor))

    def set_bg(self, ap: AnsiPixels, c: RGBColor):
        if self.bg != c:
            self.bg = c
            ap.write_string(c.background(ap.TrueColor))

    def set_colors(self, ap: AnsiPixels, fg: RGBColor, bg: RGBColor):
        self.set_fg(ap, fg)
        self.set_bg(ap, bg)


def draw_pixels(ap: AnsiPixels, pixels: Pixels, background: RGBColor):
    cs = ColorState()
    coords = list(pixels.keys())
    for coord_ary in coords:
        if coord_ary not in pixels:
            continue
        color = pixels[coord_ary]
        x, y = coord_ary[0], coord_ary[1]
        
        if y % 2 == 0:
            ap.move_cursor(x, y // 2)
            lower: Point = (x, y + 1)
            if lower in pixels:
                v = pixels[lower]
                if v == color:
                    cs.set_colors(ap, color, color)
                    ap.write_rune(FULL_PIXEL)
                    continue
                cs.set_colors(ap, v, color)
                del pixels[lower]  # drawn together
            else:
                cs.set_colors(ap, background, color)
            ap.write_rune(BOTTOM_HALF_PIXEL)
        else:
            upper: Point = (x, y - 1)
            if upper not in pixels:
                ap.move_cursor(x, y // 2)
                cs.set_colors(ap, color, background)
                ap.write_rune(BOTTOM_HALF_PIXEL)


def rotate_from_12(theta: float, radius: float) -> tuple[int, int]:
    return int(round(-math.sin(theta) * radius)), int(round(-math.cos(theta) * radius))


def calculate_angle(max_v: float, time_value: float) -> float:
    return 2.0 * math.pi * (max_v - time_value) / max_v


def angle_coords(max_v: float, time_value: float, radius: float) -> tuple[int, int]:
    return rotate_from_12(calculate_angle(max_v, time_value), radius)


def draw_hands(cfg, cx: int, cy: int, radius: int, background: RGBColor, now: datetime, seconds: bool):
    sec = float(now.second)
    minute = float(now.minute)
    hour = now.hour

    if getattr(cfg, 'continuous', False):
        micro = now.microsecond
        sec = (sec + micro / 1e6) % 60

    r = float(radius)
    sx, sy = angle_coords(60, sec, 0.9 * r)
    m = minute + sec / 60.0
    mx, my = angle_coords(60, m, 0.80 * r)
    hx, hy = angle_coords(12, float(hour % 12) + m / 60.0, 0.47 * r)

    pix: Pixels = {}
    if seconds:
        draw_line(pix, sx, sy, cx, cy, RGBColor(0x50, 0x80, 0x50))
    draw_line(pix, mx, my, cx, cy, RGBColor(0x2C, 0x59, 0xD4))
    draw_line(pix, hx, hy, cx, cy, RGBColor(255, 0xA7, 10))

    draw_pixels(cfg.ap, pix, background)
    cfg.ap.write_string(RESET)

    for n in range(1, 61):
        nx, ny = angle_coords(60, float(n % 60), r)
        if n % 5 == 0:
            val = n // 5
            if val >= 10:
                nx -= 1
            cfg.ap.write_at(cx + nx, cy + (ny - 1) // 2, "%d", val)
        elif seconds:
            cfg.ap.write_at(cx + nx, cy + (ny - 1) // 2, "•")
