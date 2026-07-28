#!/usr/bin/env python3
"""A small terminal aquarium animation.

This is an independent Python implementation for the reLang asciiquarium task.
It uses only the standard library and ANSI terminal control sequences.
"""

from __future__ import annotations

import argparse
import ctypes
import math
import os
import random
import shutil
import sys
import time
from dataclasses import dataclass
from typing import Iterable

if os.name != "nt":
    import select
    import termios
    import tty


RESET = "\x1b[0m"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
ENTER_ALT_SCREEN = "\x1b[?1049h"
LEAVE_ALT_SCREEN = "\x1b[?1049l"
CLEAR = "\x1b[2J\x1b[H"
HOME = "\x1b[H"

COLORS = {
    "water": "\x1b[38;5;38m",
    "deep_water": "\x1b[38;5;31m",
    "foam": "\x1b[38;5;117m",
    "sand": "\x1b[38;5;179m",
    "stone": "\x1b[38;5;245m",
    "green": "\x1b[38;5;77m",
    "kelp": "\x1b[38;5;35m",
    "coral": "\x1b[38;5;203m",
    "pink": "\x1b[38;5;213m",
    "orange": "\x1b[38;5;214m",
    "yellow": "\x1b[38;5;220m",
    "blue": "\x1b[38;5;75m",
    "purple": "\x1b[38;5;141m",
    "white": "\x1b[38;5;255m",
    "gray": "\x1b[38;5;250m",
    "red": "\x1b[38;5;196m",
}

FISH_COLORS = ["orange", "yellow", "blue", "purple", "pink", "white"]

FISH_SPRITES = [
    (
        ["  /`._", "><_)))'>", "  \\_.'"],
        ["_.`\\  ", "<'(((_<", "'._/  "],
    ),
    (
        ["  .-.", "><(((o>", "  `-'"],
        [".-.  ", "<o)))><", "`-'  "],
    ),
    (
        ["   __", "><_'>", "  ``"],
        ["__   ", "<'_^<", " ``  "],
    ),
    (
        ["  /\\", "><_>", "  \\/"],
        ["/\\  ", "<_><", "\\/  "],
    ),
    (
        ["   _.-.", "><((((*>", "   `-`"],
        [".-._   ", "<*))))><", "`-`   "],
    ),
]

BIG_SPRITES = [
    (
        [
            "        __",
            "   _.-'  `--.",
            "  /  o       \\",
            " /        _.-'",
            "'-..___.-'",
        ],
        [
            "__        ",
            ".--`  `-._   ",
            "/       o  \\  ",
            "`-._        \\ ",
            "    `-.___..-'",
        ],
        "blue",
    ),
    (
        [
            "      /\\",
            " ___ /  \\___",
            "<___      _/",
            "    \\____/",
        ],
        [
            "      /\\",
            " ___ /  \\___",
            "\\_      ___>",
            "  \\____/",
        ],
        "gray",
    ),
]

CLASSIC_BIG_SPRITE = (
    [
        "      .-.",
        " ___ /   \\",
        "<___|  o  |",
        "    \\___/",
    ],
    [
        ".-.      ",
        "/   \\ ___",
        "|  o |___>",
        "\\___/    ",
    ],
    "white",
)

SHELLS = [
    [" _", "(_)", " "],
    [" /\\", "/__\\", " "],
    [" __", "/__)", " "],
]


def color_code(name: str | None, enabled: bool) -> str:
    if not enabled or not name:
        return ""
    return COLORS.get(name, "")


def enable_ansi_on_windows() -> None:
    if os.name != "nt":
        return
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    mode = ctypes.c_uint32()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)


class KeyReader:
    def __init__(self) -> None:
        self._fd: int | None = None
        self._old_settings: list[int | bytes] | None = None

    def __enter__(self) -> "KeyReader":
        if os.name != "nt" and sys.stdin.isatty():
            self._fd = sys.stdin.fileno()
            self._old_settings = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        return self

    def __exit__(self, *_: object) -> None:
        if self._fd is not None and self._old_settings is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)

    def read_key(self) -> str | None:
        if not sys.stdin.isatty():
            return None
        if os.name == "nt":
            import msvcrt

            if not msvcrt.kbhit():
                return None
            key = msvcrt.getwch()
            if key in ("\x00", "\xe0"):
                if msvcrt.kbhit():
                    msvcrt.getwch()
                return None
            return key
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if ready:
            return sys.stdin.read(1)
        return None


class Terminal:
    def __init__(self, color: bool, alt_screen: bool) -> None:
        self.color = color
        self.alt_screen = alt_screen

    def __enter__(self) -> "Terminal":
        enable_ansi_on_windows()
        prefix = ENTER_ALT_SCREEN if self.alt_screen else ""
        sys.stdout.write(prefix + HIDE_CURSOR + CLEAR)
        sys.stdout.flush()
        return self

    def __exit__(self, *_: object) -> None:
        suffix = LEAVE_ALT_SCREEN if self.alt_screen else ""
        sys.stdout.write(RESET + SHOW_CURSOR + suffix)
        sys.stdout.flush()


class Canvas:
    def __init__(self, width: int, height: int, color: bool) -> None:
        self.width = width
        self.height = height
        self.color = color
        self.chars = [[" " for _ in range(width)] for _ in range(height)]
        self.colors: list[list[str | None]] = [
            [None for _ in range(width)] for _ in range(height)
        ]

    def put(self, x: int, y: int, char: str, color: str | None = None) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.chars[y][x] = char
            self.colors[y][x] = color

    def text(
        self,
        x: int,
        y: int,
        value: str,
        color: str | None = None,
        transparent: bool = True,
    ) -> None:
        if y < 0 or y >= self.height:
            return
        for offset, char in enumerate(value):
            if char == " " and transparent:
                continue
            self.put(x + offset, y, char, color)

    def sprite(
        self,
        x: int,
        y: int,
        lines: Iterable[str],
        color: str | None = None,
        transparent: bool = True,
    ) -> None:
        for row, line in enumerate(lines):
            self.text(x, y + row, line, color, transparent)

    def render(self) -> str:
        rendered: list[str] = []
        for y in range(self.height):
            active_color: str | None = None
            line_parts: list[str] = []
            for x in range(self.width):
                cell_color = self.colors[y][x]
                if self.color and cell_color != active_color:
                    line_parts.append(color_code(cell_color, True) if cell_color else RESET)
                    active_color = cell_color
                line_parts.append(self.chars[y][x])
            if self.color and active_color:
                line_parts.append(RESET)
            rendered.append("".join(line_parts))
        return HOME + "\n".join(rendered)


@dataclass
class Bubble:
    x: float
    y: float
    drift: float
    speed: float
    age: int = 0
    alive: bool = True

    def update(self, tick: int, width: int, height: int) -> None:
        self.age += 1
        self.y -= self.speed
        self.x += math.sin((tick + self.age) / 7.0) * 0.08 + self.drift
        if self.y < 1 or self.x < -2 or self.x > width + 2 or height < 1:
            self.alive = False

    def draw(self, canvas: Canvas, tick: int) -> None:
        glyphs = [".", "o", "O", "o"]
        glyph = glyphs[(self.age // 6 + tick // 12) % len(glyphs)]
        canvas.put(round(self.x), round(self.y), glyph, "foam")


@dataclass
class Fish:
    right: list[str]
    left: list[str]
    direction: int
    x: float
    base_y: float
    speed: float
    color: str
    phase: float
    alive: bool = True

    @property
    def lines(self) -> list[str]:
        return self.right if self.direction > 0 else self.left

    @property
    def width(self) -> int:
        return max(len(line) for line in self.lines)

    @property
    def height(self) -> int:
        return len(self.lines)

    def update(self, tank: "Aquarium") -> None:
        self.x += self.speed * self.direction
        if random.random() < 0.025:
            tank.add_bubble_from(self)
        if self.direction > 0 and self.x > tank.width + 2:
            self.alive = False
        elif self.direction < 0 and self.x < -self.width - 2:
            self.alive = False

    def draw(self, canvas: Canvas, tick: int) -> None:
        y = round(self.base_y + math.sin(tick / 9.0 + self.phase))
        canvas.sprite(round(self.x), y, self.lines, self.color)


@dataclass
class BigCreature:
    right: list[str]
    left: list[str]
    direction: int
    x: float
    base_y: float
    speed: float
    color: str
    phase: float
    alive: bool = True

    @property
    def lines(self) -> list[str]:
        return self.right if self.direction > 0 else self.left

    @property
    def width(self) -> int:
        return max(len(line) for line in self.lines)

    def update(self, tank: "Aquarium") -> None:
        self.x += self.speed * self.direction
        if random.random() < 0.05:
            tank.bubbles.append(
                Bubble(
                    self.x + (self.width if self.direction > 0 else 0),
                    self.base_y + 1,
                    random.uniform(-0.03, 0.03),
                    random.uniform(0.18, 0.34),
                )
            )
        if self.direction > 0 and self.x > tank.width + 4:
            self.alive = False
        elif self.direction < 0 and self.x < -self.width - 4:
            self.alive = False

    def draw(self, canvas: Canvas, tick: int) -> None:
        y = round(self.base_y + math.sin(tick / 14.0 + self.phase) * 0.6)
        canvas.sprite(round(self.x), y, self.lines, self.color)


@dataclass
class Seaweed:
    x: int
    height: int
    phase: int
    color: str

    def draw(self, canvas: Canvas, tick: int, bottom: int) -> None:
        for index in range(self.height):
            y = bottom - index
            sway = int(math.sin((tick + self.phase + index * 4) / 8.0))
            char = "(" if (index + self.phase + tick // 8) % 2 else ")"
            if index % 3 == 1:
                char = "|"
            canvas.put(self.x + sway, y, char, self.color)


@dataclass
class Coral:
    x: int
    color: str
    shape: list[str]

    def draw(self, canvas: Canvas, bottom: int) -> None:
        canvas.sprite(self.x, bottom - len(self.shape) + 1, self.shape, self.color)


class Aquarium:
    def __init__(self, classic: bool, color: bool) -> None:
        self.classic = classic
        self.color = color
        self.width = 0
        self.height = 0
        self.tick = 0
        self.paused = False
        self.fish: list[Fish] = []
        self.big_creatures: list[BigCreature] = []
        self.bubbles: list[Bubble] = []
        self.seaweed: list[Seaweed] = []
        self.coral: list[Coral] = []
        self.shells: list[tuple[int, list[str], str]] = []
        self.sand_marks: list[tuple[int, str]] = []

    def resize_if_needed(self) -> None:
        size = shutil.get_terminal_size((100, 30))
        width = max(1, size.columns)
        height = max(1, size.lines)
        if width != self.width or height != self.height:
            self.reset(width, height)

    def reset(self, width: int | None = None, height: int | None = None) -> None:
        if width is None or height is None:
            size = shutil.get_terminal_size((100, 30))
            width = max(1, size.columns)
            height = max(1, size.lines)
        self.width = width
        self.height = height
        self.fish.clear()
        self.big_creatures.clear()
        self.bubbles.clear()
        self.seaweed = self.build_seaweed()
        self.coral = self.build_coral()
        self.shells = self.build_shells()
        self.sand_marks = self.build_sand_marks()
        fish_count = max(5, min(18, (self.width * self.height) // 430))
        for _ in range(fish_count):
            fish = self.create_fish()
            fish.x = random.uniform(0, self.width - 1)
            self.fish.append(fish)
        for _ in range(max(10, self.width // 8)):
            self.bubbles.append(
                Bubble(
                    random.uniform(0, self.width - 1),
                    random.uniform(2, self.height - 5),
                    random.uniform(-0.025, 0.025),
                    random.uniform(0.12, 0.32),
                    random.randint(0, 40),
                )
            )

    def build_seaweed(self) -> list[Seaweed]:
        bottom = self.height - 3
        if bottom < 8:
            return []
        weeds: list[Seaweed] = []
        x = random.randint(1, 5)
        while x < self.width - 2:
            if random.random() < 0.72:
                weeds.append(
                    Seaweed(
                        x=x,
                        height=random.randint(3, min(9, max(3, self.height // 3))),
                        phase=random.randint(0, 80),
                        color=random.choice(["green", "kelp"]),
                    )
                )
            x += random.randint(5, 12)
        return weeds

    def build_coral(self) -> list[Coral]:
        shapes = [
            ["\\|/", "-Y-", "/|\\"],
            [" | ", "\\|/", " | "],
            ["\\ /", " | ", "/ \\"],
        ]
        coral: list[Coral] = []
        count = max(2, self.width // 36)
        for _ in range(count):
            coral.append(
                Coral(
                    x=random.randint(1, max(1, self.width - 5)),
                    color=random.choice(["coral", "pink", "purple"]),
                    shape=random.choice(shapes),
                )
            )
        return coral

    def build_shells(self) -> list[tuple[int, list[str], str]]:
        shells: list[tuple[int, list[str], str]] = []
        for _ in range(max(3, self.width // 30)):
            shells.append(
                (
                    random.randint(0, max(0, self.width - 4)),
                    random.choice(SHELLS),
                    random.choice(["white", "sand", "pink"]),
                )
            )
        return shells

    def build_sand_marks(self) -> list[tuple[int, str]]:
        marks = [".", ".", "'", "`", "-"]
        return [(x, random.choice(marks)) for x in range(0, self.width, 3)]

    def create_fish(self) -> Fish:
        right, left = random.choice(FISH_SPRITES)
        direction = random.choice([-1, 1])
        width = max(len(line) for line in (right if direction > 0 else left))
        x = -width - 1 if direction > 0 else self.width + 1
        top = 3
        bottom = max(top, self.height - 8)
        return Fish(
            right=list(right),
            left=list(left),
            direction=direction,
            x=x,
            base_y=random.uniform(top, bottom),
            speed=random.uniform(0.18, 0.58),
            color=random.choice(FISH_COLORS),
            phase=random.random() * math.tau,
        )

    def create_big_creature(self) -> BigCreature:
        if self.classic:
            right, left, color = CLASSIC_BIG_SPRITE
        else:
            right, left, color = random.choice(BIG_SPRITES + [CLASSIC_BIG_SPRITE])
        direction = random.choice([-1, 1])
        lines = right if direction > 0 else left
        width = max(len(line) for line in lines)
        x = -width - 2 if direction > 0 else self.width + 2
        top = max(4, self.height // 4)
        bottom = max(top, self.height - 11)
        return BigCreature(
            right=list(right),
            left=list(left),
            direction=direction,
            x=x,
            base_y=random.uniform(top, bottom),
            speed=random.uniform(0.12, 0.3),
            color=color,
            phase=random.random() * math.tau,
        )

    def add_bubble_from(self, fish: Fish) -> None:
        if fish.direction > 0:
            bubble_x = fish.x + fish.width - 2
        else:
            bubble_x = fish.x + 1
        bubble_y = fish.base_y + fish.height / 2
        self.bubbles.append(
            Bubble(
                x=bubble_x,
                y=bubble_y,
                drift=random.uniform(-0.035, 0.035),
                speed=random.uniform(0.12, 0.32),
            )
        )

    def update(self) -> None:
        self.tick += 1
        for fish in self.fish:
            fish.update(self)
        self.fish = [fish for fish in self.fish if fish.alive]
        while len(self.fish) < max(5, min(18, (self.width * self.height) // 430)):
            self.fish.append(self.create_fish())

        for creature in self.big_creatures:
            creature.update(self)
        self.big_creatures = [creature for creature in self.big_creatures if creature.alive]
        if len(self.big_creatures) < 2 and random.random() < 0.006:
            self.big_creatures.append(self.create_big_creature())

        if random.random() < 0.18:
            self.bubbles.append(
                Bubble(
                    x=random.uniform(0, self.width - 1),
                    y=self.height - 4,
                    drift=random.uniform(-0.03, 0.03),
                    speed=random.uniform(0.1, 0.28),
                )
            )

        for bubble in self.bubbles:
            bubble.update(self.tick, self.width, self.height)
        self.bubbles = [bubble for bubble in self.bubbles if bubble.alive]
        if len(self.bubbles) > self.width * 2:
            self.bubbles = self.bubbles[-self.width * 2 :]

    def draw_environment(self, canvas: Canvas) -> None:
        waterline = "".join("~" if (x + self.tick // 3) % 4 else "^" for x in range(self.width))
        canvas.text(0, 0, waterline[: self.width], "water", transparent=False)
        for y in range(1, max(1, self.height - 2)):
            if y % 4 == 0:
                for x in range((self.tick // 5 + y) % 17, self.width, 17):
                    canvas.put(x, y, ".", "deep_water")

        bottom = self.height - 3
        for x, mark in self.sand_marks:
            canvas.put(x, self.height - 2, mark, "sand")
        canvas.text(0, self.height - 1, "_" * self.width, "sand", transparent=False)

        for weed in self.seaweed:
            weed.draw(canvas, self.tick, bottom)
        for coral in self.coral:
            coral.draw(canvas, bottom)
        for x, shell, color in self.shells:
            canvas.sprite(x, bottom - len(shell) + 2, shell, color)

        if self.width >= 58 and self.height >= 22:
            castle = [
                "      []__[]",
                "   ___|_||_|___",
                "  |  _  __  _  |",
                "__|_| |_| |_| |_|__",
            ]
            canvas.sprite(self.width // 2 - 11, self.height - 6, castle, "stone")

    def draw_overlay(self, canvas: Canvas) -> None:
        label = " q quit  p pause  r redraw "
        if self.paused:
            label += " PAUSED "
        x = max(0, self.width - len(label) - 1)
        canvas.text(x, 1, label[: self.width], "white", transparent=False)

    def frame(self) -> str:
        self.resize_if_needed()
        canvas = Canvas(self.width, self.height, self.color)
        self.draw_environment(canvas)
        for bubble in self.bubbles:
            bubble.draw(canvas, self.tick)
        for creature in self.big_creatures:
            creature.draw(canvas, self.tick)
        for fish in self.fish:
            fish.draw(canvas, self.tick)
        self.draw_overlay(canvas)
        return canvas.render()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Animate an ASCII aquarium in the terminal."
    )
    parser.add_argument(
        "-c",
        "--classic",
        action="store_true",
        help="use a smaller set of creature types",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=15.0,
        help="target frames per second (default: 15)",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=0,
        help="draw a fixed number of frames and exit",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI colors",
    )
    parser.add_argument(
        "--no-alt-screen",
        action="store_true",
        help="draw in the current terminal buffer",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    delay = 1.0 / max(1.0, args.fps)
    aquarium = Aquarium(classic=args.classic, color=not args.no_color)
    aquarium.reset()
    frames_drawn = 0

    with Terminal(color=not args.no_color, alt_screen=not args.no_alt_screen), KeyReader() as keys:
        while True:
            frame_started = time.perf_counter()
            key = keys.read_key()
            if key in ("q", "Q", "\x03"):
                break
            if key in ("p", "P"):
                aquarium.paused = not aquarium.paused
            elif key in ("r", "R"):
                aquarium.reset()

            if not aquarium.paused:
                aquarium.update()
            sys.stdout.write(aquarium.frame())
            sys.stdout.flush()
            frames_drawn += 1

            if args.frames and frames_drawn >= args.frames:
                break

            elapsed = time.perf_counter() - frame_started
            time.sleep(max(0.0, delay - elapsed))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
