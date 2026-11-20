"""THE WORLD TODAY - Friday 20 November 2026.

A pure-stdlib Python 3.13 program that draws a one-page newspaper
front page summing up the world news of Friday 20 November 2026 and
writes it as a deterministic 1024x1024 PNG to /output/entry.png.

No network, no third-party code, no timestamps anywhere in the
output: the same bytes come out of every run. The picture is drawn
pixel by pixel with a small 5x7 bitmap font defined below, so the
program needs nothing but the standard library.

Stories on the page (all first reported on Friday 20 November 2026,
or the day's papers' lead stories that morning):
  * Trump, Xi and Putin hold their first three-way summit in China
  * Trump pushes any Iran decision to 2027 - "see what happens"
  * Cyclone Akvan makes landfall on India's Odisha coast
  * The ICJ rules Myanmar committed genocide against the Rohingya
  * NASA confirms Voyager 1 is one light-day from Earth
  * Hayabusa2's engine trouble ends its asteroid landing plan
  * GTA 6 sales pass the $1.8bn set by "The Odyssey"
  * Europe says it is ready for talks with Russia on Ukraine
  * Cricket: Nicholls 113 not out for New Zealand v India
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (250, 246, 236)
INK = (18, 18, 18)
RED = (178, 34, 34)
BLUE = (28, 68, 128)
GREY = (112, 110, 102)
PANEL = (233, 227, 214)
GOLD = (186, 146, 38)
LIGHT_BLUE = (214, 226, 238)


# ---------------------------------------------------------------- PNG ---

def _chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return out


def write_png(path, w, h, rgb):
    """Encode RGB bytes as a plain PNG (8-bit, colour type 2)."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: none, every row
        raw += rgb[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# -------------------------------------------------------------- canvas ---

class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, t=1):
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                for k in range(t):
                    self.set(px + k, py, c)
                    self.set(px, py + k, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def triangle(self, x0, y0, x1, y1, x2, y2, c):
        # Filled triangle by scanline between the three edges.
        pts = sorted(((x0, y0), (x1, y1), (x2, y2)), key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        def edge_x(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)
        for y in range(ay, cy + 1):
            if y < by:
                xa = edge_x(ax, ay, bx, by, y)
                xb = edge_x(ax, ay, cx, cy, y)
            else:
                xa = edge_x(bx, by, cx, cy, y)
                xb = edge_x(ax, ay, cx, cy, y)
            lo, hi = sorted((int(round(xa)), int(round(xb))))
            for x in range(lo, hi + 1):
                self.set(x, y, c)


# ----------------------------------------------------------- bitmap font ---
# 5x7 glyphs, each row a 5-bit int, top row first. Hand-drawn for this page.

FONT = {
    "A": (14, 17, 17, 31, 17, 17, 17),
    "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (14, 17, 16, 16, 16, 17, 14),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 15),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 27, 17),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "Z": (31, 1, 2, 4, 8, 16, 31),
    "0": (14, 17, 19, 21, 25, 17, 14),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 6, 8, 16, 31),
    "3": (31, 2, 4, 2, 1, 17, 14),
    "4": (2, 6, 10, 18, 31, 2, 2),
    "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14),
    "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14),
    "9": (14, 17, 17, 15, 1, 2, 12),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 12, 4, 8),
    "-": (0, 0, 0, 31, 0, 0, 0),
    "'": (4, 4, 8, 0, 0, 0, 0),
    "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 6, 4, 0, 4),
    ":": (0, 12, 12, 0, 12, 12, 0),
    ";": (0, 12, 12, 0, 12, 4, 8),
    "(": (2, 4, 8, 8, 8, 4, 2),
    ")": (8, 4, 2, 2, 2, 4, 8),
    "/": (1, 2, 2, 4, 8, 8, 16),
    "%": (25, 26, 2, 4, 8, 11, 19),
    "&": (12, 18, 20, 8, 21, 18, 13),
    "+": (0, 4, 4, 31, 4, 4, 0),
    "=": (0, 0, 31, 0, 31, 0, 0),
    "$": (4, 15, 20, 14, 5, 30, 4),
    '"': (10, 10, 10, 0, 0, 0, 0),
    "*": (0, 4, 21, 14, 21, 4, 0),
    "_": (0, 0, 0, 0, 0, 0, 31),
}


# ------------------------------------------------------------ text drawing ---

def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color):
    """Draw ASCII text left-aligned at (x, y); returns width drawn."""
    s = s.upper()  # the bitmap font only carries capitals
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT["?"])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 scale, scale, color)
        cx += 6 * scale
    return cx - x - scale


def draw_center(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap(s, max_w, scale):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def paragraph(cv, x, y, s, scale, color, max_w, leading=None):
    """Draw a wrapped paragraph; returns the y just below it."""
    lh = leading if leading is not None else 10 * scale
    for line in wrap(s, max_w, scale):
        draw_text(cv, x, y, line, scale, color)
        y += lh
    return y


def headline(cv, x, y, lines, scale, color=INK, leading=None):
    lh = leading if leading is not None else 10 * scale
    for line in lines:
        draw_text(cv, x, y, line, scale, color)
        y += lh
    return y


# -------------------------------------------------------------- pictograms ---

def draw_globe(cv, cx, cy, r, color):
    cv.circle(cx, cy, r, color, 2)
    cv.circle(cx, cy, r // 2, color, 1)
    cv.line(cx - r, cy, cx + r, cy, color)
    cv.line(cx, cy - r, cx, cy + r, color)
    for k in (-1, 1):
        cv.line(cx - r + 6, cy + k * r // 2, cx + r - 6, cy + k * r // 2, color)


def draw_cyclone(cv, cx, cy, color):
    # Spiral storm: widening arcs around a calm eye.
    for ring in range(4):
        r = 8 + ring * 7
        steps = 26 - ring * 4
        for i in range(steps):
            a = 2 * math.pi * i / 26 + ring * 0.9
            x = int(cx + r * math.cos(a))
            y = int(cy + r * math.sin(a))
            cv.set(x, y, color)
            cv.set(x + 1, y, color)
    cv.disc(cx, cy, 3, PAPER)
    cv.circle(cx, cy, 3, color, 1)


def draw_scales(cv, x, y, s, color):
    # Scales of justice, s = overall height in px.
    top = y
    cv.vline(x + s // 2, top, s, color, 2)
    cv.hline(x + 4, top + 6, s - 8, color, 2)
    cv.disc(x + s // 2, top + 2, 3, color)
    for side in (0, 1):
        px = x + 6 + side * (s - 12)
        cv.line(px, top + 6, px - 9, top + s // 2, color)
        cv.line(px, top + 6, px + 9, top + s // 2, color)
        cv.hline(px - 10, top + s // 2, 21, color, 2)
        cv.fill_rect(px - 8, top + s // 2, 17, 3, color)
    cv.hline(x + 2, top + s - 2, s - 4, color, 3)


def draw_probe(cv, x, y, s, color):
    # Voyager-style probe: dish + body + boom, flying up-right.
    cv.circle(x + s // 3, y + s // 3, s // 4, color, 2)
    cv.line(x + s // 3, y + s // 3, x + 2 * s // 3, y + 2 * s // 3, color)
    cv.fill_rect(x + s // 2, y + s // 2, s // 3, s // 5, color)
    cv.line(x + 5 * s // 6, y + 3 * s // 5, x + s, y + s // 2, color)
    cv.line(x + 5 * s // 6, y + 3 * s // 5, x + s, y + 3 * s // 4, color)
    for sx, sy in ((x + s // 5, y + 4 * s // 5), (x + 4 * s // 5, y + s // 5),
                   (x + s, y + s // 6)):
        cv.disc(sx, sy, 2, GOLD)


def draw_flag_us(cv, x, y, w, h):
    stripe = max(2, h // 13)
    for i in range(13):
        cv.fill_rect(x, y + i * stripe, w, stripe,
                     RED if i % 2 == 0 else (255, 255, 255))
    cw, ch = w * 2 // 5, stripe * 7
    cv.fill_rect(x, y, cw, ch, BLUE)
    for r in range(4):
        for c in range(5):
            cv.set(x + 4 + c * (cw // 6), y + 3 + r * (ch // 5),
                   (255, 255, 255))


def draw_flag_cn(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, RED)
    cv.disc(x + w // 5, y + h // 4, max(3, h // 8), GOLD)
    for dx, dy in ((w // 2, h // 6), (w * 3 // 5, h // 3),
                   (w * 3 // 5, h * 3 // 5), (w // 2, h * 4 // 5)):
        cv.disc(x + dx, y + dy, max(2, h // 14), GOLD)


def draw_flag_ru(cv, x, y, w, h):
    third = h // 3
    cv.fill_rect(x, y, w, third, (255, 255, 255))
    cv.fill_rect(x, y + third, w, third, BLUE)
    cv.fill_rect(x, y + 2 * third, w, h - 2 * third, RED)


# ------------------------------------------------------------------ page ---

def draw_page():
    cv = Canvas(W, H, PAPER)
    cv.rect(14, 14, W - 28, H - 28, INK, 2)  # outer frame

    # ---- masthead ------------------------------------------------------
    cv.hline(30, 30, W - 60, RED, 4)
    draw_center(cv, W // 2, 44, "THE WORLD TODAY", 7, INK)
    draw_center(cv, W // 2, 106, "FRIDAY, 20 NOVEMBER 2026", 3, RED)
    draw_text(cv, 34, 108, "NO. 324", 2, GREY)
    draw_text(cv, W - 34 - text_w("ONE DAY, ONE PAGE", 2), 108,
              "ONE DAY, ONE PAGE", 2, GREY)
    cv.hline(30, 134, W - 60, INK, 3)
    cv.hline(30, 140, W - 60, INK, 1)

    # ---- lead story: the trilateral summit ------------------------------
    draw_center(cv, W // 2, 156, "SUMMIT IN CHINA", 2, RED)
    draw_center(cv, W // 2, 182, "TRUMP, XI AND PUTIN", 4, INK)
    draw_center(cv, W // 2, 216, "MEET FACE TO FACE", 4, INK)
    paragraph(cv, 34, 258,
              "The three leaders hold their first three-way summit in "
              "Beijing, with nuclear arms, energy and the wars in Ukraine "
              "and the Middle East on the agenda.",
              2, INK, 620, leading=20)
    # Three flags, left to right: US, China, Russia.
    fx, fy, fw, fh = 690, 246, 88, 58
    draw_flag_us(cv, fx, fy, fw, fh)
    draw_flag_cn(cv, fx + 100, fy, fw, fh)
    draw_flag_ru(cv, fx + 200, fy, fw, fh)
    for i, label in enumerate(("USA", "CHINA", "RUSSIA")):
        draw_center(cv, fx + fw // 2 + i * 100, fy + fh + 8, label, 2, GREY)
    cv.hline(30, 330, W - 60, INK, 2)

    # ---- row two: Iran decision / Cyclone Akvan -------------------------
    # Left column.
    draw_text(cv, 34, 348, "WASHINGTON", 2, RED)
    headline(cv, 34, 372, ["IRAN DECISION PUT", "OFF TO 2027"], 3, INK)
    paragraph(cv, 34, 440,
              "President Trump says there is 'no rush' on Iran and he will "
              "'see what happens' after 1 January, pushing any decision on "
              "military action into next year.",
              2, INK, 452, leading=20)
    # Right column.
    draw_text(cv, 532, 348, "INDIA", 2, RED)
    headline(cv, 532, 372, ["CYCLONE AKVAN", "HITS ODISHA"], 3, INK)
    paragraph(cv, 532, 440,
              "Severe storm hits Odisha near Gopalpur at noon, gusts to "
              "110 km/h. About 300,000 evacuated, 69 trains cancelled.",
              2, INK, 360, leading=20)
    draw_cyclone(cv, 930, 480, BLUE)
    cv.vline(512, 348, 190, GREY, 1)
    cv.hline(30, 552, W - 60, INK, 2)

    # ---- row three: ICJ ruling / Voyager 1 ------------------------------
    draw_text(cv, 34, 570, "THE HAGUE", 2, RED)
    headline(cv, 34, 594, ["WORLD COURT: MYANMAR", "GUILTY OF GENOCIDE"], 3, INK)
    paragraph(cv, 34, 662,
              "The ICJ rules 9-6 that Myanmar committed genocide against "
              "the Rohingya in its 2017 crackdown - a first for the court.",
              2, INK, 452, leading=20)
    draw_scales(cv, 34, 748, 40, BLUE)
    draw_text(cv, 532, 570, "SPACE", 2, RED)
    headline(cv, 532, 594, ["VOYAGER 1: ONE", "LIGHT-DAY FROM EARTH"], 3, INK)
    paragraph(cv, 532, 662,
              "NASA confirms its probe, 49 years into flight, is now 16.1 "
              "billion miles away - so far that its radio signal takes a "
              "full day to reach home.",
              2, INK, 330, leading=20)
    draw_probe(cv, 900, 730, 60, BLUE)
    cv.vline(512, 570, 218, GREY, 1)
    cv.hline(30, 800, W - 60, INK, 2)

    # ---- bottom band: three short stories + sport -----------------------
    draw_text(cv, 34, 818, "JAPAN", 2, RED)
    paragraph(cv, 34, 842,
              "HAYABUSA2: engine trouble ends the asteroid landing plan.",
              2, INK, 300, leading=18)
    cv.vline(352, 818, 96, GREY, 1)
    draw_text(cv, 372, 818, "HOLLYWOOD", 2, RED)
    paragraph(cv, 372, 842,
              "GTA 6: sales pass the $1.8bn set by film 'The Odyssey'.",
              2, INK, 300, leading=18)
    cv.vline(690, 818, 96, GREY, 1)
    draw_text(cv, 710, 818, "EUROPE", 2, RED)
    paragraph(cv, 710, 842,
              "Ready for talks with Russia on ending the Ukraine war.",
              2, INK, 280, leading=18)
    cv.hline(30, 928, W - 60, INK, 1)
    draw_center(cv, W // 2, 942,
                "SPORT - CRICKET: NICHOLLS 113 NOT OUT AS NEW ZEALAND "
                "REACH 243-5 AGAINST INDIA", 2, INK)

    # ---- footer ----------------------------------------------------------
    cv.hline(30, 976, W - 60, INK, 2)
    draw_center(cv, W // 2, 988,
                "ALL STORIES REPORTED ON FRIDAY 20 NOVEMBER 2026", 2, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    page = draw_page()
    size = write_png(path, W, H, page.px)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
