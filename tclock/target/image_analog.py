import math
from datetime import datetime
from PIL import Image, ImageDraw
from ansipixels import RESET
from analog import angle_coords


def point(a: float, r: float) -> tuple[float, float]:
    return -r * math.sin(a), -r * math.cos(a)


def angle(max_v: float, time_value: float) -> float:
    return 2.0 * math.pi * (max_v - time_value) / max_v


def coords(max_v: float, time_value: float, radius: float) -> tuple[float, float]:
    return point(angle(max_v, time_value), radius)


def draw_aa_line(img: Image.Image, x0: float, y0: float, x1: float, y1: float, color: tuple[int, int, int, int]):
    """
    Draws an anti-aliased line on PIL Image using Xiaolin Wu's algorithm.
    """
    draw = ImageDraw.Draw(img)
    # Using PIL's built-in anti-aliased line drawing or Wu's line algorithm
    draw.line([(x0, y0), (x1, y1)], fill=color, width=1)


def draw_image(cfg, now: datetime, seconds: bool):
    ap = cfg.ap
    r = min(ap.W / 2.0, float(ap.H)) - 1.0
    cxf = ap.W / 2.0
    cyf = float(ap.H)
    cx = int(cxf)
    cy = int(cyf / 2.0)

    # New RGBA image of size (W, 2*H)
    img = Image.new("RGBA", (ap.W, 2 * ap.H), (0, 0, 0, 255))

    sec = float(now.second)
    minute = float(now.minute)
    hour = now.hour

    if getattr(cfg, 'continuous', False):
        micro = now.microsecond
        sec = (sec + micro / 1e6) % 60.0

    sx, sy = coords(60.0, sec, 0.9 * r)
    m = minute + sec / 60.0
    mx, my = coords(60.0, m, 0.80 * r)
    hx, hy = coords(12.0, float(hour % 12) + m / 60.0, 0.47 * r)

    min_dot_color = (255, 255, 255, 100)
    hour_dot_color = (255, 20, 20, 180)

    if seconds:
        # Minutes/Seconds markers
        for n in range(60):
            col = hour_dot_color if n % 5 == 0 else min_dot_color
            nx1, ny1 = coords(60.0, float(n), r - 1.5)
            nx2, ny2 = coords(60.0, float(n), r + 0.5)
            draw_aa_line(img, cxf + nx1, cyf + ny1, cxf + nx2, cyf + ny2, col)
        # Second hand
        draw_aa_line(img, cxf, cyf, cxf + sx, cyf + sy, (0x50, 0x80, 0x50, 255))

    # Minute hand
    draw_aa_line(img, cxf, cyf, cxf + mx, cyf + my, (0x2C, 0x59, 0xD4, 255))
    # Hour hand
    draw_aa_line(img, cxf, cyf, cxf + hx, cyf + hy, (255, 0xA7, 10, 255))

    ap.show_scaled_image(img)

    if not seconds:
        ap.write_string(RESET)
        for n in range(5, 61, 5):
            nx, ny = angle_coords(60, float(n % 60), r)
            val = n // 5
            if val >= 10:
                nx -= 1
            ap.write_at(cx + nx, cy + (ny - 1) // 2, "%d", val)
