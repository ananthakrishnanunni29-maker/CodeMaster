import sys
import os
import argparse
import math
import time
from datetime import datetime, timedelta

# Ensure target directory is in sys.path for direct script execution
target_dir = os.path.dirname(os.path.abspath(__file__))
if target_dir not in sys.path:
    sys.path.insert(0, target_dir)

# Import target submodules
from bignum import time_string
from duration import parse_duration, parse_date_time
from ansipixels import AnsiPixels, RGBColor, parse_color, blend_linear, blend_nsrgb, detect_truecolor, ColorHelp, RESET, INVERSE
from analog import draw_hands
from image_analog import draw_image
from stdin_tail import stdin_tail

TRUE_COLOR_DISC_DEFAULT = "E0C020"
NO_TRUE_COLOR_DISC_DEFAULT = "FFFFFF"


def bounce_val(frame: int, maximum: int) -> int:
    if maximum <= 0:
        return 0
    m = frame % (2 * maximum)
    if m < maximum:
        return m
    return 2 * maximum - 1 - m


def format_time_str(dt: datetime, use_24: bool, seconds: bool) -> str:
    if use_24:
        s = f"{dt.hour:02d}:{dt.minute:02d}"
    else:
        hour_12 = dt.hour % 12
        if hour_12 == 0:
            hour_12 = 12
        s = f"{hour_12}:{dt.minute:02d}"
    if seconds:
        s += f":{dt.second:02d}"
    return s


def duration_ddhhmm(dur: timedelta) -> str:
    total_seconds = int(dur.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    total_minutes = total_seconds // 60
    total_hours = total_minutes // 60

    minutes = total_minutes % 60
    hours = total_hours % 24

    if total_hours >= 24:
        days = total_hours // 24
        return f"{days:02d}:{hours:02d}:{minutes:02d}"
    if total_hours >= 1:
        return f"{hours:02d}:{minutes:02d}"
    return f"{minutes:02d}"


def duration_string(dur: timedelta, with_seconds: bool) -> str:
    s = duration_ddhhmm(dur)
    if with_seconds:
        secs = int(dur.total_seconds()) % 60
        s += f":{secs:02d}"
    return s


class Config:
    def __init__(self):
        self.ap: AnsiPixels | None = None
        self.boxed: bool = False
        self.color: str = ""
        self.color_box: str = ""
        self.analog: bool = False
        self.inverse: bool = False
        self.debug: bool = False
        self.bounce: int = 0
        self.bounce_speed: int = 0
        self.frame: int = 0
        self.breath: bool = False
        self.bcolor: RGBColor = RGBColor(0, 0, 0)
        self.color_output = None
        self.color_disc: RGBColor | None = None
        self.radius: float = 1.2
        self.fill_black: bool = False
        self.aliasing: float = 0.8
        self.black_bg: str = ""
        self.blending_function = blend_nsrgb
        self.text: str = ""
        self.top_right: bool = False
        self.tail = None
        self.count_down: bool = False
        self.end: datetime = datetime.now()
        self.extra_newlines_at_end: bool = True
        self.use_24: bool = False
        self.format_str: str = ""
        self.track_mouse: bool = False
        self.blink_enabled: bool = True
        self.seconds: bool = True
        self.now: datetime = datetime.now()
        self.aa: bool = False
        self.continuous: bool = False

    def format_time(self, dt: datetime) -> str:
        return format_time_str(dt, self.use_24, self.seconds)

    def duration_string(self, dur: timedelta, with_seconds: bool) -> str:
        return duration_string(dur, with_seconds)

    def breath_color(self) -> RGBColor:
        spread = 100
        alpha = 0.15 + 0.85 * float(bounce_val(self.frame, spread)) / float(spread)
        bg = self.ap.Background if self.ap else RGBColor(0, 0, 0)
        return self.blending_function(bg, self.bcolor, alpha)

    def tail_mode(self):
        self.top_right = True
        self.color_disc = None
        self.boxed = True
        return self

    def clear_screen(self):
        if self.fill_black:
            self.ap.write_string(self.black_bg)
        self.ap.clear_screen()

    def draw_at(self, x: int, y: int, s: str):
        if self.aa:
            draw_image(self, self.now, self.seconds)
            return
        if self.analog:
            radius = min(self.ap.W // 2, self.ap.H) - 1
            draw_hands(self, self.ap.W // 2, self.ap.H // 2, radius, self.ap.Background, self.now, self.seconds)
            return
        if self.debug:
            self.ap.draw_square_box(0, 0, self.ap.W, self.ap.H)
            self.ap.write_at(0, self.ap.H - 1, f"Mouse {self.ap.Mx}, {self.ap.My} [{self.ap.W}x{self.ap.H}]")

        lines = s.split("\n")
        width = self.ap.screen_width(lines[0])
        if self.boxed:
            width += 2
        height = len(lines)
        if self.boxed:
            height += 2

        if (x < 0 and y < 0) or self.analog:
            x = self.ap.W // 2 + width // 2
            y = self.ap.H // 2 + height // 2

        if self.top_right:
            x = self.ap.W - 1
            y = height - 1

        x = min(x, self.ap.W - 1)
        y = min(y, self.ap.H - 1)

        if self.bounce != 0:
            x = width - 1 + bounce_val(self.bounce, self.ap.W - width + 1)
            y = height - 1 + bounce_val(self.bounce, self.ap.H - height + 1)

        x += 1
        y += 1
        x = max(x, width)
        y = max(y, height)

        if self.color_disc is not None:
            mult = self.radius
            if self.breath:
                mult *= (1.0 + float(bounce_val(self.frame // 7, 10)) / 15.0)
            rad = 2 * int(round(mult * float(width) / 4.0))
            if rad <= height:
                rad = (2 * (height + 1)) // 2
            cx = x - width // 2 - 1
            cy = y - height // 2 - 1
            bg = self.ap.Background if self.ap else RGBColor(0, 0, 0)
            self.ap.disc_blend_fn(cx, cy, rad, bg, self.color_disc, self.aliasing, self.blending_function)

        if self.boxed:
            if self.color_box:
                self.ap.draw_colored_box(x - width, y - height, width, height, self.color_box, False)
            else:
                self.ap.draw_round_box(x - width, y - height, width, height)
            x -= 1
            y -= 1
            width -= 2
            height -= 2

        prefix = self.color
        if self.breath:
            prefix = self.color_output.foreground(self.breath_color())
        if self.inverse:
            prefix = INVERSE + self.color
        suffix = self.black_bg if self.fill_black else RESET

        for i, line in enumerate(lines):
            self.ap.write_at_str(x - width, y - height + i, prefix + line + suffix)

        if self.text:
            center = x - width // 2 - self.ap.screen_width(self.text) // 2 - 1
            self.ap.write_at_str(center, y + 1, self.text)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Terminal clock with analog/digital modes, countdown, and tailing.",
        add_help=False
    )
    parser.add_argument("-bounce", type=int, default=0, help="Bounce speed")
    parser.add_argument("-24", action="store_true", dest="use_24", help="Use 24-hour time format")
    parser.add_argument("-analog", action="store_true", help="Analog clock")
    parser.add_argument("-no-seconds", action="store_true", help="Don't show seconds")
    parser.add_argument("-no-blink", action="store_true", help="Don't blink the colon")
    parser.add_argument("-box", action="store_true", help="Draw a rounded outline")
    parser.add_argument("-color-disc", type=str, default=None, help="Color disc around time")
    parser.add_argument("-radius", type=float, default=1.2, help="Radius of disc")
    parser.add_argument("-black-bg", action="store_true", help="Set black background")
    parser.add_argument("-aliasing", type=float, default=0.8, help="Aliasing factor")
    parser.add_argument("-color-box", type=str, default="", help="Color box around time")
    parser.add_argument("-color", type=str, default="red", help="Color to use")
    parser.add_argument("-breath", action="store_true", help="Pulse color")
    parser.add_argument("-inverse", action="store_true", help="Inverse fg/bg")
    parser.add_argument("-debug", action="store_true", help="Debug mode")
    parser.add_argument("-truecolor", type=bool, default=None, help="Use true color")
    parser.add_argument("-linear", action="store_true", help="Linear blending")
    parser.add_argument("-countdown", type=str, default="", help="Countdown duration")
    parser.add_argument("-text", type=str, default="", help="Text below clock")
    parser.add_argument("-until", type=str, default="", help="Countdown until date/time")
    parser.add_argument("-tail", type=str, default="", help="Tail filename")
    parser.add_argument("-aa", action="store_true", help="Antialiased image clock")
    parser.add_argument("-c", action="store_true", dest="continuous", help="Continuous analog update")
    parser.add_argument("-fps", type=float, default=30.0, help="Max FPS")
    parser.add_argument("args", nargs="*", help="Positional arguments")

    return parser.parse_args()


def raw_mode_loop(cfg: Config) -> int:
    ap = cfg.ap
    blink = False
    prev_now = None
    x, y = ap.Mx, ap.My
    frame = 0
    prev = ""

    def on_resize():
        cfg.clear_screen()
        ap.start_sync_mode()
        cfg.draw_at(-1, -1, time_string(prev, False))
        ap.end_sync_mode()

    ap.OnResize = on_resize

    try:
        while True:
            _, err = ap.read_or_resize_or_signal_once()
            if err:
                return 1

            do_draw = cfg.breath or cfg.continuous

            if ap.Data:
                ch = ap.Data[0]
                if ch in ('q', '\x03'):
                    if cfg.count_down:
                        ap.write_at(0, ap.H - 3, "Countdown aborted at %s\r\n", cfg.format_time(cfg.now))
                        return 1
                    return 0
                elif ch in ('a', 'A'):
                    cfg.aa = not cfg.aa
                    cfg.analog = not cfg.aa
                    do_draw = True
                elif ch in ('c', 'C'):
                    cfg.continuous = not cfg.continuous
                    do_draw = True

            if ap.left_click() and ap.mouse_release():
                cfg.track_mouse = not cfg.track_mouse

            cfg.now = datetime.now()

            if cfg.count_down:
                left = cfg.end - cfg.now
                if left.total_seconds() < 0:
                    ap.write_at(0, ap.H - 2, "\aTime's up reached at %s\r\n", cfg.format_time(cfg.now))
                    cfg.extra_newlines_at_end = False
                    return 0
                num_str = cfg.duration_string(left, cfg.seconds)
            else:
                num_str = cfg.format_time(cfg.now)

            if num_str != prev:
                do_draw = True
            prev = num_str

            if not cfg.continuous:
                cfg.now = cfg.now.replace(microsecond=0)

            if cfg.now != prev_now and cfg.blink_enabled:
                blink = not blink
                do_draw = True
            prev_now = cfg.now

            if cfg.bounce_speed > 0:
                if frame % cfg.bounce_speed == 0:
                    cfg.bounce += 1
                    do_draw = True
                frame += 1
            elif cfg.track_mouse and (ap.Mx != x or ap.My != y):
                x, y = ap.Mx, ap.My
                do_draw = True

            buf = ""
            n = 0
            if cfg.tail is not None:
                try:
                    buf = cfg.tail.read(4096)
                    n = len(buf)
                except Exception:
                    pass

            if do_draw or n > 0:
                cfg.frame += 1
                ap.start_sync_mode()
                if cfg.tail is None:
                    cfg.clear_screen()
                if n > 0:
                    ap.Out.write(buf)
                    ap.save_cursor_pos()
                cfg.draw_at(x - 1, y - 1, time_string(num_str, blink))
                ap.restore_cursor_pos()
                ap.end_sync_mode()

    except KeyboardInterrupt:
        return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    truecolor_default = detect_truecolor()
    disc_default = TRUE_COLOR_DISC_DEFAULT if truecolor_default else NO_TRUE_COLOR_DISC_DEFAULT

    opts = parse_args()

    cfg = Config()
    cfg.boxed = opts.box
    cfg.inverse = opts.inverse
    cfg.debug = opts.debug
    cfg.breath = opts.breath
    cfg.radius = opts.radius
    cfg.fill_black = opts.black_bg
    cfg.aliasing = opts.aliasing
    cfg.use_24 = opts.use_24
    cfg.seconds = not opts.no_seconds
    cfg.bounce_speed = opts.bounce
    cfg.blink_enabled = not opts.no_blink
    cfg.extra_newlines_at_end = True
    cfg.analog = opts.analog
    cfg.aa = opts.aa
    cfg.continuous = opts.continuous

    if cfg.continuous and not cfg.analog and not cfg.aa:
        cfg.aa = True

    ap = AnsiPixels(opts.fps)
    if opts.truecolor is not None:
        ap.TrueColor = opts.truecolor
    else:
        ap.TrueColor = truecolor_default
    cfg.ap = ap
    cfg.color_output = ap.ColorOutput

    color_disc = opts.color_disc if opts.color_disc is not None else disc_default

    show_text = opts.text != "none"
    if show_text:
        cfg.text = opts.text

    cfg.now = datetime.now()

    if opts.countdown:
        try:
            dur = parse_duration(opts.countdown)
            if dur.total_seconds() > 0:
                cfg.count_down = True
                cfg.end = cfg.now + dur
        except ValueError as e:
            sys.stderr.write(f"Invalid countdown duration: {e}\n")
            return 1

    if opts.until:
        cfg.count_down = True
        try:
            cfg.end = parse_date_time(cfg.now, opts.until)
        except ValueError as e:
            sys.stderr.write(f"Invalid until time: {e}\n")
            return 1

    if cfg.count_down and show_text and not cfg.text:
        to_str = cfg.format_time(cfg.end)
        if (cfg.end - cfg.now) >= timedelta(days=1):
            to_str = f"{cfg.end.strftime('%Y-%m-%d')} {to_str}"
        extra = ""
        if not cfg.use_24 and cfg.end.hour >= 12:
            extra = " pm"
        cfg.text = f"Countdown to {to_str}{extra}"

    if opts.linear:
        cfg.blending_function = blend_linear
    else:
        cfg.blending_function = blend_nsrgb

    if cfg.breath:
        col = parse_color(opts.color)
        cfg.bcolor = col
    else:
        try:
            col = parse_color(opts.color)
            cfg.color = ap.ColorOutput.foreground(col)
        except ValueError as e:
            sys.stderr.write(f"Color error: {e}\n")
            return 1

    if opts.color_box:
        try:
            col = parse_color(opts.color_box)
            cfg.color_box = ap.ColorOutput.foreground(col)
            cfg.boxed = True
        except ValueError as e:
            sys.stderr.write(f"Color box error: {e}\n")
            return 1

    if color_disc:
        try:
            col = parse_color(color_disc)
            cfg.color_disc = col
        except ValueError as e:
            sys.stderr.write(f"Color disc error: {e}\n")
            return 1

    ap.get_size()
    if ap.TrueColor:
        cfg.black_bg = RGBColor(0, 0, 0).background(ap.TrueColor)
    else:
        cfg.black_bg = RGBColor(0, 0, 0).background(ap.TrueColor)
    ap.Background = RGBColor(0, 0, 0)

    positional_args = opts.args
    if len(positional_args) == 1:
        num_str = positional_args[0]
        if num_str == "-":
            return stdin_tail(cfg.tail_mode())
        if not num_str or num_str[0] < '0' or num_str[0] > '9':
            sys.stderr.write("No arguments, or <digits> or -\n")
            return 1
        print(time_string(num_str, False))
        return 0

    if opts.tail:
        cfg.tail_mode()
        if opts.tail == "-":
            return stdin_tail(cfg)
        try:
            f = open(opts.tail, "r")
            cfg.tail = f
        except Exception as e:
            sys.stderr.write(f"Error opening tail file: {e}\n")
            return 1
        ap.save_cursor_pos()
        cfg.extra_newlines_at_end = False

    ap.open()
    try:
        if not cfg.top_right:
            ap.hide_cursor()
            if not cfg.fill_black:
                ap.sync_background_color()
            cfg.clear_screen()

        if cfg.bounce_speed <= 0 and not cfg.top_right and not cfg.analog:
            ap.mouse_tracking_on()
            cfg.track_mouse = True

        return raw_mode_loop(cfg)
    finally:
        if cfg.extra_newlines_at_end:
            ap.Out.write("\r\n\n\n\n")
        ap.show_cursor()
        ap.mouse_tracking_off()
        ap.end_sync_mode()
        ap.restore()


if __name__ == "__main__":
    sys.exit(main())
