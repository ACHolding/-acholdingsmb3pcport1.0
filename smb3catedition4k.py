#!/usr/bin/env python3
"""SMB3 Cat Edition 0 — full id Software / IFD 1990 PC demo (FILES=OFF).

Parts: title menu · SMB3 world map · 9 demo stages · 2.5D cat hero · score/coins/
lives/time · ? blocks · breakable bricks · goal poles · Carmack smooth scroll.
Python 3.10+ · NES 256×240 @ 60 FPS · import math · no PNG/WAV.
"""

from __future__ import annotations

import array
import math
import sys
from dataclasses import dataclass, field

try:
    import pygame
except ImportError:
    print("Install pygame: pip install pygame-ce")
    sys.exit(1)

# --- NES timing & display ---
TILE = 16
NES_W, NES_H = 256, 240
SCALE = 3
WIN_W, WIN_H = NES_W * SCALE, NES_H * SCALE
FPS = 60
ROWS = NES_H // TILE
COLS_VIS = NES_W // TILE

GRAVITY = 0.38
JUMP_V = -5.2
MAX_FALL = 6.5
WALK = 1.4
RUN = 2.6
ACCEL = 0.22
FRICTION = 0.18

APP_NAME = "SMB3 Cat Edition 0"
WINDOW_TITLE = f"{APP_NAME} — IFD PC port · NES 60 FPS"

# --- Procedural palette (SMB3 overworld-ish) ---
P = {
    "sky": (92, 148, 252),
    "sky2": (68, 120, 220),
    "white": (252, 252, 252),
    "ground": (196, 112, 48),
    "ground_d": (148, 72, 28),
    "ground_l": (228, 156, 88),
    "brick": (200, 96, 48),
    "brick_d": (148, 56, 24),
    "q": (248, 196, 56),
    "q_d": (200, 140, 16),
    "pipe": (72, 188, 88),
    "pipe_d": (36, 132, 56),
    "sand": (228, 188, 96),
    "sand_d": (180, 140, 64),
    "star": (248, 220, 72),
    "mush": (248, 72, 72),
    "mush_w": (252, 252, 252),
    "hill": (88, 184, 88),
    "hill_d": (52, 136, 52),
    "map_grass": (96, 176, 72),
    "map_path": (228, 188, 120),
    "map_water": (60, 120, 248),
    "map_sel": (248, 200, 48),
    "text": (252, 252, 252),
    "m_red": (220, 48, 40),
    "m_skin": (248, 192, 140),
    "m_blue": (56, 72, 200),
    "goomba": (168, 88, 32),
    # 2.5D cat hero
    "cat": (248, 148, 56),
    "cat_l": (255, 188, 96),
    "cat_d": (188, 96, 28),
    "cat_eye": (40, 24, 12),
    "cat_nose": (255, 140, 160),
    "u_bg": (8, 8, 36),
    "u_brick": (72, 120, 220),
    "c_bg": (24, 16, 32),
    "c_brick": (180, 180, 188),
    "s_bg": (120, 168, 252),
    "coin": (248, 200, 48),
    "flag": (248, 72, 72),
    "pole": (220, 220, 220),
    "used": (160, 110, 60),
}

T_SOLID = frozenset("#=B?PM*S^LKTlktieUP")
T_BREAK = frozenset("=B")
T_BUMP = frozenset("?=")
GOAL_CHAR = "G"
COIN_CHAR = "C"
USED_CHAR = "U"

MENU_ITEMS = ("PLAY GAME", "CONTROLS", "CREDITS")

# All maps from id Software / IFD 1990 SMB3 PC demo (Romero 2015 · Strong Museum)
# . sky  # ground  = brick  ? qblock  ^ pyramid  E enemy  I/F/D/M/* IFD logo
# L/K/T/E/I blocks spell "LIKE IT?" on demo-2 (Ars Technica / Romero pitch level)

_W = 72  # tiles wide (scrollable PC demo stages)

def _blank_rows(n: int) -> list[str]:
    return ["." * _W for _ in range(n)]


def _ground_row(prefix: str = "", suffix: str = "") -> str:
    mid = _W - len(prefix) - len(suffix)
    return prefix + ("#" * max(0, mid)) + suffix


LEVELS: dict[str, dict] = {
    "1-1": {
        "name": "Demo 1 — World 1-1 (IFD logo)",
        "theme": "overworld",
        "lines": [
            "I...F...D.........................................................",
            "IMSM*MSM*MS........................................................",
            *_blank_rows(2),
            "........................?..........................................",
            "..................?===?............................................",
            *_blank_rows(3),
            "........................................E..........................",
            *_blank_rows(2),
            _ground_row(),
            _ground_row(),
            _ground_row("", "....G"),
        ],
    },
    "demo-2": {
        "name": "Demo 2 — LIKE IT? (id pitch to Nintendo)",
        "theme": "overworld",
        "lines": [
            *_blank_rows(3),
            "....l...........i...........k...........e...........................",
            "....l...........i...........k...........e...........i..............",
            "....l....===....i....===....k....===....e....===....i....===....t....?",
            "....l...........i...........k...........e...........i..............",
            "....llll........iii.........kkk.........eee.........iii.........ttt.",
            *_blank_rows(2),
            "..............................E....................................",
            *_blank_rows(2),
            _ground_row(),
            _ground_row(),
            _ground_row("", "....G"),
        ],
    },
    "demo-3": {
        "name": "Demo 3 — Carmack scroll showcase",
        "theme": "overworld",
        "lines": [
            *_blank_rows(2),
            "..............?===?....................?===?.......................",
            "...................................................................",
            "..........P..................P......................P................",
            "..........P..................P......................P................",
            "........===..................===....................===..............",
            "........................................E..........................",
            "....................?..............................................",
            "....................................................E..............",
            *_blank_rows(2),
            _ground_row("##", ""),
            _ground_row("##", ""),
            _ground_row("##", "....G"),
        ],
    },
    "1-4": {
        "name": "Demo 4 — World 1-4 (flat + pyramid)",
        "theme": "overworld",
        "lines": [
            *_blank_rows(7),
            "........................................................E..........",
            *_blank_rows(1),
            "........................................................^..........",
            "......................................................^=^........",
            "....................................................^=B=^........",
            "..................................................^=B=B=^........",
            "................................................^=B=B=B=^........",
            _ground_row("", "^=B=B=B=B=^....G"),
        ],
    },
    "demo-5": {
        "name": "Demo 5 — pipe valley (PC original)",
        "theme": "overworld",
        "lines": [
            *_blank_rows(2),
            "........?===?........................?===?.......................",
            "...................................................................",
            "......P......P......P......P......P......P......P......P..........",
            "......P......P......P......P......P......P......P......P..........",
            "....................................E..............................",
            "....................................................E..............",
            *_blank_rows(3),
            _ground_row(),
            _ground_row(),
            _ground_row("", "....G"),
        ],
    },
    "demo-6": {
        "name": "Demo 6 — hill clouds finale",
        "theme": "overworld",
        "lines": [
            *_blank_rows(1),
            "....?........................?........................?..............",
            "....=........................=........................=..............",
            "....=..........E.............=..........E.............=..............",
            "....=........................=........................=..............",
            "....=........................=........................=..............",
            "....=======..................=======..................=======......",
            "........................................................E..........",
            *_blank_rows(2),
            _ground_row(),
            _ground_row(),
            _ground_row("", "....G"),
        ],
    },
    "demo-7": {
        "name": "Demo 7 — underground test (PC build)",
        "theme": "underground",
        "lines": [
            *_blank_rows(2),
            "............?===?............?===?...............................",
            "...................................................................",
            "........E..............................E...........................",
            "....========..................========.............................",
            "...................................................................",
            "....========..................========.............................",
            *_blank_rows(3),
            _ground_row("========", "....G"),
            _ground_row("========", ""),
            _ground_row("========", ""),
        ],
    },
    "demo-8": {
        "name": "Demo 8 — castle (PC build)",
        "theme": "castle",
        "lines": [
            *_blank_rows(2),
            "............?===?............?===?...............................",
            "...................................................................",
            "........E..............................E...........................",
            "....BBBBBB..................BBBBBB.................................",
            "...................................................................",
            "....BBBBBB..................BBBBBB.................................",
            *_blank_rows(3),
            _ground_row("BBBB", "....G"),
            _ground_row("BBBB", ""),
            _ground_row("BBBB", ""),
        ],
    },
    "demo-9": {
        "name": "Demo 9 — sky / cloud (PC build)",
        "theme": "sky",
        "lines": [
            *_blank_rows(1),
            "....?........................?........................?..............",
            "....=........................=........................=..............",
            "....=..........E.............=..........E.............=..............",
            "....=........................=........................=..............",
            "....=======..................=======..................=======......",
            "........................................................C..........",
            *_blank_rows(2),
            _ground_row("", "....G"),
            _ground_row("", ""),
            _ground_row("", ""),
        ],
    },
}

# IFD PC demo — all parts (Romero 2015 · Strong Museum order)
MAP_NODES: list[tuple[str, int, int]] = [
    ("START", 1, 8),
    ("1-1", 3, 8),
    ("demo-2", 5, 7),
    ("demo-3", 7, 8),
    ("1-4", 9, 6),
    ("demo-5", 11, 7),
    ("demo-6", 13, 8),
    ("demo-7", 15, 7),
    ("demo-8", 5, 4),
    ("demo-9", 11, 4),
]

IFD_DEMO_ORDER = [
    "1-1", "demo-2", "demo-3", "1-4", "demo-5", "demo-6", "demo-7", "demo-8", "demo-9",
]


def _parse_level(lines: list[str]) -> tuple[list[list[str]], int, int]:
    h = len(lines)
    w = max(len(r) for r in lines) if lines else COLS_VIS
    grid = []
    for row in lines:
        r = list(row.ljust(w, "."))
        grid.append(r)
    return grid, w, h


@dataclass
class Session:
    score: int = 0
    coins: int = 0
    lives: int = 3
    time_left: int = 300
    cleared: set[str] = field(default_factory=set)


@dataclass
class Entity:
    kind: str
    x: float
    y: float
    vx: float = 0.0
    alive: bool = True
    w: int = 14
    h: int = 14


@dataclass
class Player:
    x: float = 32.0
    y: float = 160.0
    vx: float = 0.0
    vy: float = 0.0
    on_ground: bool = False
    big: bool = False
    dead: bool = False
    invuln: int = 0
    facing: int = 1


def draw_cat_25d(
    surf: pygame.Surface,
    cx: int,
    cy: int,
    vx: float,
    vy: float,
    on_ground: bool,
    big: bool,
    invuln_flash: bool,
    tick_ms: int,
) -> None:
    """Procedural 2.5D cat — math.sin/cos depth, shadow, sway tail (FILES=OFF)."""
    if invuln_flash:
        return
    t = tick_ms / 1000.0
    facing = 1 if vx >= 0 else -1
    moving = abs(vx) > 0.12
    bob = math.sin(t * 9.0) * (1.1 if moving and on_ground else 0.25)
    cy = int(cy + bob)
    scale = 1.0 + (0.12 if big else 0.0)
    w = int(13 * scale)
    h = int(16 * scale)

    # ground shadow (depth)
    sh_w = int(w * (1.15 + 0.05 * math.sin(t * 4.0)))
    shadow = pygame.Surface((sh_w, 7), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 75), (0, 0, sh_w, 7))
    surf.blit(shadow, (cx - sh_w // 2 + w // 2, cy + h - 3))

    body_w = int(w * (1.0 + 0.1 * math.cos(t * 5.5)))
    body_h = int(h * 0.82)
    bx, by = cx + 1, cy + 5
    pygame.draw.ellipse(
        surf, P["cat_d"],
        (bx - body_w // 2 + 2, by - body_h // 2 + 2, body_w, body_h),
    )
    pygame.draw.ellipse(surf, P["cat"], (bx - body_w // 2, by - body_h // 2, body_w, body_h))
    gleam = (
        min(255, P["cat"][0] + 35),
        min(255, P["cat"][1] + 28),
        min(255, P["cat"][2] + 18),
    )
    pygame.draw.ellipse(
        surf, gleam,
        (bx - body_w // 4, by - body_h // 2, body_w // 2, body_h // 3),
    )

    hr = int(8 * scale)
    hx = bx + int(facing * 2)
    hy = by - body_h // 2 - hr + 5
    pygame.draw.circle(surf, P["cat_d"], (hx + 1, hy + 1), hr)
    pygame.draw.circle(surf, P["cat"], (hx, hy), hr)
    pygame.draw.circle(surf, gleam, (hx - facing * 2, hy - 2), max(2, hr // 3))

    for side, back in ((-1, True), (1, False)):
        ex = hx + side * 5 * facing
        ear = P["cat_d"] if back else P["cat_l"]
        tip_y = hy - hr - int(4 + math.sin(t * 7 + side) * 1.5)
        pts = [
            (ex, hy - hr + 2),
            (ex + side * 3 * facing, tip_y),
            (ex + side * 6 * facing, hy - hr + 1),
        ]
        pygame.draw.polygon(surf, ear, pts)

    for ex in (-3, 3):
        eye_x = hx + ex * facing
        pygame.draw.circle(surf, P["cat_eye"], (eye_x, hy), 2)
        pygame.draw.circle(surf, P["white"], (eye_x + facing, hy - 1), 1)

    pygame.draw.circle(surf, P["cat_nose"], (hx + facing * 2, hy + 3), 2)
    for i in range(3):
        wy = hy + 1 + i
        wx1 = hx - 4 * facing
        wx2 = hx + 8 * facing
        wob = int(math.sin(t * 8 + i) * 0.5)
        pygame.draw.line(
            surf, P["white"], (wx1, wy), (wx1 - 5 * facing, wy + i - 1 + wob), 1
        )
        pygame.draw.line(
            surf, P["white"], (wx2, wy), (wx2 + 5 * facing, wy + i - 1 + wob), 1
        )

    tail_base = (bx - facing * body_w // 2, by + body_h // 4)
    tail_pts: list[tuple[int, int]] = []
    for i in range(9):
        frac = i / 8.0
        sway = math.sin(t * 6.0 + frac * math.pi) * 4.0
        tx = int(tail_base[0] - facing * (frac * 16 + sway))
        ty = int(tail_base[1] - frac * 10 - math.sin(frac * math.pi) * 8)
        tail_pts.append((tx, ty))
    if len(tail_pts) >= 2:
        pygame.draw.lines(surf, P["cat_d"], False, tail_pts, 3)
        pygame.draw.lines(surf, P["cat_l"], False, tail_pts[2:], 2)

    if on_ground:
        step = math.sin(t * 11.0) * 2.5 if moving else 0.0
        for lx in (-4, 4):
            leg_y = cy + h - 4 + int(step * (1 if lx < 0 else -1) * (1 if moving else 0))
            pygame.draw.rect(surf, P["cat_d"], (bx + lx - 2, leg_y, 4, 5))
            pygame.draw.rect(surf, P["cat"], (bx + lx - 2, leg_y - 1, 4, 4))


class Level:
    def __init__(self, key: str) -> None:
        spec = LEVELS[key]
        self.key = key
        self.name = spec["name"]
        self.theme = spec["theme"]
        self.grid, self.w_tiles, self.h_tiles = _parse_level(spec["lines"])
        self.px_w = self.w_tiles * TILE
        self.px_h = self.h_tiles * TILE
        self.entities: list[Entity] = []
        self.cleared = False
        self.coins_taken: set[tuple[int, int]] = set()
        self.goal_x = 0
        self.goal_y = 0
        for y, row in enumerate(self.grid):
            for x, ch in enumerate(row):
                if ch == GOAL_CHAR:
                    self.goal_x = x * TILE
                    self.goal_y = y * TILE
        self.player = Player()
        for y, row in enumerate(self.grid):
            for x, ch in enumerate(row):
                if ch == "E":
                    self.entities.append(Entity("goomba", x * TILE + 2, y * TILE - 2, vx=-0.6))
        for y, row in enumerate(self.grid):
            for x, ch in enumerate(row):
                if ch in T_SOLID and ch != GOAL_CHAR and y > 0:
                    self.player.x = max(16, x * TILE)
                    self.player.y = (y - 1) * TILE
                    return

    def bump_block(self, tx: int, ty: int, session: Session) -> None:
        if ty < 0 or ty >= self.h_tiles or tx < 0 or tx >= self.w_tiles:
            return
        ch = self.grid[ty][tx]
        if ch == "?":
            self.grid[ty][tx] = USED_CHAR
            session.coins += 1
            session.score += 200
            if not self.player.big:
                self.player.big = True
                self.player.invuln = 90
        elif ch in T_BREAK:
            self.grid[ty][tx] = "."
            session.score += 50

    def try_collect_coin(self, session: Session) -> None:
        tx = int((self.player.x + 6) // TILE)
        ty = int((self.player.y + 6) // TILE)
        if (tx, ty) in self.coins_taken:
            return
        if self.tile(tx, ty) == COIN_CHAR:
            self.coins_taken.add((tx, ty))
            session.coins += 1
            session.score += 100

    def at_goal(self) -> bool:
        p = self.player
        return (
            abs(p.x + 6 - (self.goal_x + 8)) < 20
            and abs(p.y + 10 - self.goal_y) < 24
            and self.goal_x > 0
        )

    def _spawn_entities(self) -> None:
        pass

    def tile(self, tx: int, ty: int) -> str:
        if ty < 0 or ty >= self.h_tiles or tx < 0 or tx >= self.w_tiles:
            return "."
        return self.grid[ty][tx]

    def solid_at(self, px: float, py: float, pw: int = 12, ph: int = 14) -> bool:
        for dy in (0, ph - 1):
            for dx in (0, pw - 1):
                tx = int((px + dx) // TILE)
                ty = int((py + dy) // TILE)
                if self.tile(tx, ty) in T_SOLID and self.tile(tx, ty) != GOAL_CHAR:
                    return True
        return False

    def head_bump_tile(self, px: float, py: float) -> tuple[int, int] | None:
        tx = int((px + 6) // TILE)
        ty = int(py // TILE) - 1
        if 0 <= ty < self.h_tiles and 0 <= tx < self.w_tiles:
            if self.tile(tx, ty) in T_BUMP or self.tile(tx, ty) in T_BREAK:
                return tx, ty
        return None


class Game:
    def __init__(self) -> None:
        pygame.mixer.pre_init(22050, -16, 1, 256)
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.canvas = pygame.Surface((NES_W, NES_H))
        self.font = pygame.font.Font(None, 16)
        self.font_lg = pygame.font.Font(None, 24)
        self.state = "title"
        self.menu_sel = 0
        self.map_idx = 0
        self.session = Session()
        self.level: Level | None = None
        self.cam_x = 0.0
        self.pause = False
        self.clear_timer = 0
        self.status = "id Software PC port · FILES=OFF"
        self.music = self._build_overworld_loop()

    def _build_overworld_loop(self) -> pygame.mixer.Sound | None:
        try:
            sr = 22050
            bpm = 150
            tick = 60.0 / bpm / 4
            notes = [659, 523, 659, 784, 659, 523, 440, 440]
            samples: list[float] = []
            phase = 0.0
            for freq in notes * 4:
                n = int(tick * 2 * sr)
                if freq <= 0:
                    samples.extend([0.0] * n)
                    continue
                step = freq / sr
                for i in range(n):
                    phase = (phase + step) % 1.0
                    raw = 1.0 if phase < 0.25 else -1.0
                    t = i / max(1, n - 1)
                    samples.append(raw * (1.0 - t) * 0.35)
            buf = array.array("h")
            for s in samples:
                buf.append(int(max(-32768, min(32767, s * 9000))))
            return pygame.mixer.Sound(buffer=buf)
        except (pygame.error, ValueError, OSError):
            return None

    def _play_music(self) -> None:
        if self.music:
            try:
                self.music.play(loops=-1)
            except pygame.error:
                pass

    def _stop_music(self) -> None:
        if self.music:
            try:
                self.music.stop()
            except pygame.error:
                pass

    def start_level(self, key: str) -> None:
        self.level = Level(key)
        self.state = "level"
        self.cam_x = 0.0
        self.session.time_left = 300
        self.status = self.level.name
        self._play_music()

    def _respawn_level(self) -> None:
        if self.level is None:
            return
        key = self.level.key
        self.level = Level(key)

    def _handle_title(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self.menu_sel = (self.menu_sel - 1) % len(MENU_ITEMS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.menu_sel = (self.menu_sel + 1) % len(MENU_ITEMS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.menu_sel == 0:
                self.state = "world_map"
                self.map_idx = 0
            elif self.menu_sel == 1:
                self.state = "controls"
            else:
                self.state = "credits"
        elif event.key == pygame.K_ESCAPE:
            if self.state in ("controls", "credits"):
                self.state = "title"

    def _handle_controls_credits(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self.state = "title"

    def _handle_map(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RIGHT, pygame.K_d):
            self.map_idx = min(len(MAP_NODES) - 1, self.map_idx + 1)
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.map_idx = max(0, self.map_idx - 1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            label = MAP_NODES[self.map_idx][0]
            if label != "START" and label in LEVELS:
                self.start_level(label)
        elif event.key == pygame.K_ESCAPE:
            self.state = "title"

    def _handle_level(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._stop_music()
                self.state = "world_map"
                self.level = None
            elif event.key == pygame.K_p:
                self.pause = not self.pause

    def _update_level(self, keys) -> None:
        lv = self.level
        if lv is None or lv.cleared or lv.player.dead or self.pause:
            return
        if self.session.time_left > 0:
            self.session.time_left -= 1 / FPS
        elif not lv.player.dead:
            lv.player.dead = True
        p = lv.player
        run = keys[pygame.K_x] or keys[pygame.K_LSHIFT]
        target = RUN if run else WALK
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            p.vx = max(p.vx - ACCEL, -target)
            p.facing = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            p.vx = min(p.vx + ACCEL, target)
            p.facing = 1
        else:
            if p.vx > 0:
                p.vx = max(0, p.vx - FRICTION)
            elif p.vx < 0:
                p.vx = min(0, p.vx + FRICTION)
        if (keys[pygame.K_z] or keys[pygame.K_SPACE]) and p.on_ground:
            p.vy = JUMP_V
            p.on_ground = False
        p.vy = min(p.vy + GRAVITY, MAX_FALL)
        prev_y = p.y
        nx = p.x + p.vx
        if not lv.solid_at(nx, p.y):
            p.x = nx
        else:
            p.vx = 0
        ny = p.y + p.vy
        if not lv.solid_at(p.x, ny):
            p.y = ny
            p.on_ground = False
        else:
            if p.vy > 0:
                p.on_ground = True
            elif p.vy < 0:
                hit = lv.head_bump_tile(p.x, p.y)
                if hit:
                    lv.bump_block(hit[0], hit[1], self.session)
            p.vy = 0
        if p.vy < 0 and p.y >= prev_y:
            hit = lv.head_bump_tile(p.x, p.y)
            if hit:
                lv.bump_block(hit[0], hit[1], self.session)
        lv.try_collect_coin(self.session)
        if p.y > lv.px_h:
            p.dead = True
        target_cam = max(0, min(p.x + 8 - NES_W // 2, max(0, lv.px_w - NES_W)))
        self.cam_x += (target_cam - self.cam_x) * 0.25
        for e in lv.entities:
            if not e.alive:
                continue
            e.x += e.vx
            if lv.solid_at(e.x, e.y):
                e.vx *= -1
            er = pygame.Rect(int(e.x), int(e.y), e.w, e.h)
            pr = pygame.Rect(int(p.x), int(p.y), 12, 14)
            if er.colliderect(pr):
                if p.vy > 0 and p.y + 10 < e.y + 4:
                    e.alive = False
                    p.vy = JUMP_V * 0.65
                    self.session.score += 100
                elif p.invuln <= 0:
                    if p.big:
                        p.big = False
                        p.invuln = 120
                    else:
                        p.dead = True
        if p.invuln > 0:
            p.invuln -= 1
        if lv.at_goal():
            lv.cleared = True
            self.session.cleared.add(lv.key)
            self.session.score += 1000
            self.clear_timer = 120
            self.state = "level_clear"
            self.status = f"Cleared {lv.key}!"
        if p.dead:
            self.session.lives -= 1
            if self.session.lives > 0:
                self._respawn_level()
                self.status = f"Lives {self.session.lives}"
            else:
                self.state = "title"
                self.session.lives = 3
                self._stop_music()
                self.level = None
                self.status = "Game Over — IFD demo"

    def _draw_tile(self, ch: str, sx: int, sy: int, theme: str = "overworld") -> None:
        r = pygame.Rect(sx, sy, TILE, TILE)
        if ch == ".":
            return
        if ch == "#":
            col = P["u_brick"] if theme == "underground" else P["ground"]
            col_d = (28, 48, 140) if theme == "underground" else P["ground_d"]
            col_l = (120, 160, 255) if theme == "underground" else P["ground_l"]
            pygame.draw.rect(self.canvas, col, r)
            pygame.draw.rect(self.canvas, col_d, r, 1)
            pygame.draw.line(self.canvas, col_l, (sx, sy), (sx + TILE, sy))
        elif ch in ("=", "B") or (ch.lower() in "lktie" and ch.isalpha()):
            pygame.draw.rect(self.canvas, P["brick"], r)
            pygame.draw.rect(self.canvas, P["brick_d"], r, 1)
            if ch.lower() in "lktie":
                t = self.font.render(ch.upper(), True, P["white"])
                self.canvas.blit(t, (sx + 4, sy + 1))
        elif ch == USED_CHAR:
            pygame.draw.rect(self.canvas, P["used"], r)
            pygame.draw.rect(self.canvas, P["brick_d"], r, 1)
        elif ch == COIN_CHAR:
            pygame.draw.circle(self.canvas, P["coin"], (sx + 8, sy + 8), 5)
            pygame.draw.rect(self.canvas, P["white"], (sx + 6, sy + 5, 4, 6), 1)
        elif ch == GOAL_CHAR:
            pygame.draw.rect(self.canvas, P["pole"], (sx + 7, sy, 3, 16))
            pygame.draw.rect(self.canvas, P["flag"], (sx + 10, sy + 2, 8, 6))
        elif ch == "?":
            pygame.draw.rect(self.canvas, P["q"], r)
            pygame.draw.rect(self.canvas, P["q_d"], r, 1)
            t = self.font.render("?", True, P["white"])
            self.canvas.blit(t, (sx + 4, sy + 1))
        elif ch == "P":
            pygame.draw.rect(self.canvas, P["pipe"], r)
            pygame.draw.rect(self.canvas, P["pipe_d"], r, 2)
        elif ch == "*":
            pygame.draw.rect(self.canvas, P["star"], r)
            pygame.draw.polygon(
                self.canvas, P["white"],
                [(sx + 8, sy + 2), (sx + 10, sy + 8), (sx + 14, sy + 8),
                 (sx + 11, sy + 11), (sx + 12, sy + 15), (sx + 8, sy + 12),
                 (sx + 4, sy + 15), (sx + 5, sy + 11), (sx + 2, sy + 8), (sx + 6, sy + 8)],
            )
        elif ch in ("M", "I", "F", "D", "S"):
            if ch == "M" or ch == "S":
                pygame.draw.ellipse(self.canvas, P["mush"], (sx + 2, sy + 2, 12, 8))
                pygame.draw.rect(self.canvas, P["mush_w"], (sx + 5, sy + 8, 6, 6))
            else:
                pygame.draw.rect(self.canvas, P["mush"], r)
            if ch in "IFD":
                t = self.font.render(ch, True, P["white"])
                self.canvas.blit(t, (sx + 3, sy + 2))
        elif ch == "^":
            pygame.draw.polygon(
                self.canvas, P["sand"],
                [(sx + 8, sy + 2), (sx + 14, sy + 14), (sx + 2, sy + 14)],
            )
            pygame.draw.polygon(
                self.canvas, P["sand_d"],
                [(sx + 8, sy + 6), (sx + 12, sy + 14), (sx + 4, sy + 14)],
            )

    def _draw_player(self, p: Player) -> None:
        sx = int(p.x - self.cam_x)
        sy = int(p.y)
        flash = p.invuln > 0 and (pygame.time.get_ticks() // 80) % 2 == 0
        draw_cat_25d(
            self.canvas, sx, sy, p.vx, p.vy, p.on_ground, p.big, flash,
            pygame.time.get_ticks(),
        )

    def _draw_level(self) -> None:
        lv = self.level
        if lv is None:
            return
        theme = lv.theme
        if theme == "underground":
            bg = P["u_bg"]
        elif theme == "castle":
            bg = P["c_bg"]
        elif theme == "sky":
            bg = P["s_bg"]
        else:
            bg = P["sky"]
        self.canvas.fill(bg)
        if theme == "underground":
            for i in range(4):
                hx = int(i * 80 - (self.cam_x * 0.15) % 80)
                pygame.draw.rect(self.canvas, P["u_brick"], (hx, 180, 40, 8))
        elif theme == "castle":
            for i in range(3):
                hx = int(i * 64 - (self.cam_x * 0.2) % 64)
                pygame.draw.rect(self.canvas, P["c_brick"], (hx, 160, 48, 12))
        elif theme in ("overworld", "sky"):
            for i in range(3):
                hx = int(i * 96 - (self.cam_x * 0.3) % 96)
                pygame.draw.ellipse(self.canvas, P["hill"], (hx - 20, 140, 80, 40))
                pygame.draw.ellipse(self.canvas, P["hill_d"], (hx - 10, 148, 60, 28))
        tx0 = int(self.cam_x // TILE)
        tx1 = tx0 + COLS_VIS + 2
        for ty in range(lv.h_tiles):
            for tx in range(tx0, tx1):
                ch = lv.tile(tx, ty)
                if ch == COIN_CHAR and (tx, ty) in lv.coins_taken:
                    ch = "."
                sx = tx * TILE - int(self.cam_x)
                sy = ty * TILE
                self._draw_tile(ch, sx, sy, lv.theme)
        if lv.goal_x > 0:
            gx = lv.goal_x - int(self.cam_x)
            self._draw_tile(GOAL_CHAR, gx, lv.goal_y, lv.theme)
        for e in lv.entities:
            if e.alive:
                ex = int(e.x - self.cam_x)
                ey = int(e.y)
                pygame.draw.ellipse(self.canvas, P["goomba"], (ex, ey + 4, 14, 10))
                pygame.draw.rect(self.canvas, (40, 20, 0), (ex + 2, ey + 2, 4, 4))
                pygame.draw.rect(self.canvas, (40, 20, 0), (ex + 8, ey + 2, 4, 4))
        self._draw_player(lv.player)
        s = self.session
        hud = self.font.render(
            f"{lv.key}  {s.score:06d}  x{s.coins:02d}  L{s.lives}  T{int(s.time_left):03d}",
            True, P["text"],
        )
        self.canvas.blit(hud, (4, 4))
        if self.pause:
            ov = self.font_lg.render("PAUSE", True, P["text"])
            self.canvas.blit(ov, (NES_W // 2 - ov.get_width() // 2, NES_H // 2 - 12))

    def _draw_world_map(self) -> None:
        self.canvas.fill(P["map_water"])
        for y in range(ROWS):
            for x in range(COLS_VIS):
                if (x + y) % 5 == 0:
                    pygame.draw.rect(self.canvas, P["map_grass"], (x * TILE, y * TILE, TILE, TILE))
        # path lines between nodes
        for i in range(len(MAP_NODES) - 1):
            x1, y1 = MAP_NODES[i][1] * TILE + 8, MAP_NODES[i][2] * TILE + 8
            x2, y2 = MAP_NODES[i + 1][1] * TILE + 8, MAP_NODES[i + 1][2] * TILE + 8
            pygame.draw.line(self.canvas, P["map_path"], (x1, y1), (x2, y2), 3)
        t = self.font_lg.render("IFD PC DEMO MAP", True, P["text"])
        self.canvas.blit(t, (NES_W // 2 - t.get_width() // 2, 8))
        sub = self.font.render(f"{len(IFD_DEMO_ORDER)} stages · cat moves map · Enter", True, P["text"])
        self.canvas.blit(sub, (4, NES_H - 14))
        for i, (label, mx, my) in enumerate(MAP_NODES):
            px, py = mx * TILE, my * TILE
            col = P["map_sel"] if i == self.map_idx else P["map_path"]
            pygame.draw.circle(self.canvas, col, (px + 8, py + 8), 8)
            if label in self.session.cleared:
                pygame.draw.line(self.canvas, P["white"], (px + 4, py + 8), (px + 8, py + 12), 2)
                pygame.draw.line(self.canvas, P["white"], (px + 8, py + 12), (px + 14, py + 4), 2)
            if label != "START":
                short = label.replace("demo-", "D")
                tx = self.font.render(short, True, P["text"])
                self.canvas.blit(tx, (px - 2, py - 12))
        # cat avatar on selected node
        _, mx, my = MAP_NODES[self.map_idx]
        draw_cat_25d(
            self.canvas, mx * TILE + 8, my * TILE - 6, 0.0, 0.0, True, False, False,
            pygame.time.get_ticks(),
        )

    def _draw_title(self) -> None:
        self.canvas.fill(P["sky2"])
        t1 = self.font_lg.render(APP_NAME, True, P["text"])
        self.canvas.blit(t1, (NES_W // 2 - t1.get_width() // 2, 36))
        draw_cat_25d(self.canvas, NES_W // 2, 88, 0.0, 0.0, True, False, False, pygame.time.get_ticks())
        for i, item in enumerate(MENU_ITEMS):
            col = P["map_sel"] if i == self.menu_sel else P["text"]
            t = self.font.render(item, True, col)
            self.canvas.blit(t, (NES_W // 2 - t.get_width() // 2, 130 + i * 22))
        sub = self.font.render("IFD 1990 PC demo · NES 60 · FILES=OFF", True, P["text"])
        self.canvas.blit(sub, (NES_W // 2 - sub.get_width() // 2, NES_H - 16))

    def _draw_controls(self) -> None:
        self.canvas.fill(P["sky2"])
        lines = (
            "CONTROLS",
            "← → move   Z/Space jump",
            "X/Shift run   P pause",
            "Esc map / menu",
            "Bump ? for power-up",
            "Head-bump = break bricks",
            "Reach flag pole to clear",
        )
        for i, line in enumerate(lines):
            f = self.font_lg if i == 0 else self.font
            t = f.render(line, True, P["text"])
            self.canvas.blit(t, (16, 40 + i * 24))

    def _draw_credits(self) -> None:
        self.canvas.fill(P["sky2"])
        lines = (
            "CREDITS",
            "id Software / IFD 1990",
            "SMB3 PC demo for Nintendo",
            "Carmack smooth scroll",
            "Romero 2015 · Strong Museum",
            "Clean-room cat edition",
            "AC Holding · FILES=OFF",
        )
        for i, line in enumerate(lines):
            f = self.font_lg if i == 0 else self.font
            t = f.render(line, True, P["text"])
            self.canvas.blit(t, (12, 36 + i * 22))

    def _draw_level_clear(self) -> None:
        if self.level:
            self._draw_level()
        ov = pygame.Surface((NES_W, NES_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 120))
        self.canvas.blit(ov, (0, 0))
        t = self.font_lg.render("STAGE CLEAR!", True, P["text"])
        self.canvas.blit(t, (NES_W // 2 - t.get_width() // 2, 100))
        if self.level:
            t2 = self.font.render(self.level.name, True, P["text"])
            self.canvas.blit(t2, (NES_W // 2 - t2.get_width() // 2, 130))

    def run(self) -> None:
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._stop_music()
                    pygame.quit()
                    return
                if self.state == "title":
                    self._handle_title(event)
                elif self.state in ("controls", "credits"):
                    self._handle_controls_credits(event)
                elif self.state == "world_map":
                    self._handle_map(event)
                elif self.state == "level":
                    self._handle_level(event)
                elif self.state == "level_clear":
                    if event.type == pygame.KEYDOWN:
                        self.state = "world_map"
                        self.level = None
                        self._stop_music()

            if self.state == "level":
                self._update_level(pygame.key.get_pressed())
            elif self.state == "level_clear":
                self.clear_timer -= 1
                if self.clear_timer <= 0:
                    self.state = "world_map"
                    self.level = None
                    self._stop_music()

            if self.state == "title":
                self._draw_title()
            elif self.state == "controls":
                self._draw_controls()
            elif self.state == "credits":
                self._draw_credits()
            elif self.state == "world_map":
                self._draw_world_map()
            elif self.state == "level":
                self._draw_level()
            elif self.state == "level_clear":
                self._draw_level_clear()

            scaled = pygame.transform.scale(self.canvas, (WIN_W, WIN_H))
            self.screen.blit(scaled, (0, 0))
            pygame.display.flip()


def main() -> None:
    Game().run()


if __name__ == "__main__":
    main()
