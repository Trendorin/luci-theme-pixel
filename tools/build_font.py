#!/usr/bin/env python3
"""Build the Pixel 5x7 web font of luci-theme-pixel.

    python3 build_font.py OUT.woff2      (needs fonttools + brotli)

The 5x7 glyphs come from github.com/Trendorin (profile build.py); Cyrillic and the
extra symbols are in extra_glyphs.py.

One font pixel = 100 units, 1 em = 10 pixels, so font-size 20px draws 2px
pixels, 30px draws 3px, 40px draws 4px. Every connected group of pixels is
traced into one outline (no overlapping squares), so the glyphs stay free of
hairline seams when a phone scales them by a fractional factor.
"""
import sys
from collections import defaultdict

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.woff2 import compress

from profile_glyphs import FONT
from extra_glyphs import EXTRA, ALIASES, SPACES

U = 100  # font units per pixel


def parse(spec):
    top = 0
    if spec.startswith("^"):
        top, spec = -1, spec[1:]
    rows = spec.split()
    pts = {(x, top + y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == "#"}
    return pts, len(rows[0])


def trace(pixels):
    """Outline of a pixel set as closed clockwise loops (y up), holes counter-clockwise."""
    cells = {(x, 6 - r) for x, r in pixels}  # row r -> cell whose bottom edge is y = 6 - r
    out = defaultdict(list)
    for x, y in cells:
        if (x, y + 1) not in cells:
            out[(x, y + 1)].append((x + 1, y + 1))
        if (x + 1, y) not in cells:
            out[(x + 1, y + 1)].append((x + 1, y))
        if (x, y - 1) not in cells:
            out[(x + 1, y)].append((x, y))
        if (x - 1, y) not in cells:
            out[(x, y)].append((x, y + 1))
    loops = []
    while any(out.values()):
        start = next(p for p, v in out.items() if v)
        loop, cur, prev_dir = [start], start, None
        while True:
            cands = out[cur]
            if len(cands) > 1 and prev_dir:
                # at a corner where two regions touch diagonally, turn right first
                def rank(n):
                    d = (n[0] - cur[0], n[1] - cur[1])
                    right = (prev_dir[1], -prev_dir[0])
                    return 0 if d == right else (1 if d == prev_dir else 2)
                cands.sort(key=rank)
            nxt = cands.pop(0)
            prev_dir = (nxt[0] - cur[0], nxt[1] - cur[1])
            cur = nxt
            if cur == start:
                break
            loop.append(cur)
        # drop points in the middle of straight runs
        simple = []
        n = len(loop)
        for i, p in enumerate(loop):
            a, c = loop[i - 1], loop[(i + 1) % n]
            if (p[0] - a[0]) * (c[1] - p[1]) != (p[1] - a[1]) * (c[0] - p[0]):
                simple.append(p)
        loops.append(simple)
    return loops


def glyph_from(pixels):
    pen = TTGlyphPen(None)
    for loop in trace(pixels):
        pen.moveTo((loop[0][0] * U, loop[0][1] * U))
        for p in loop[1:]:
            pen.lineTo((p[0] * U, p[1] * U))
        pen.closePath()
    return pen.glyph()


def main(out):
    specs = dict(FONT)
    specs.update(EXTRA)
    for ch, src in ALIASES.items():
        specs.setdefault(ch, specs[src])

    order, cmap, glyphs, metrics = [".notdef"], {}, {".notdef": TTGlyphPen(None).glyph()}, {".notdef": (600, 0)}
    for ch in sorted(set(specs) | set(SPACES)):
        name = "uni%04X" % ord(ch)
        order.append(name)
        cmap[ord(ch)] = name
        if ch in SPACES:
            glyphs[name] = TTGlyphPen(None).glyph()
            metrics[name] = (SPACES[ch] * U, 0)
            continue
        pts, width = parse(specs[ch])
        glyphs[name] = glyph_from(pts)
        metrics[name] = ((width + 1) * U, min((x for x, _ in pts), default=0) * U)

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=800, descent=-300, lineGap=0)
    fb.setupNameTable({"familyName": "Pixel 5x7", "styleName": "Regular",
                       "uniqueFontIdentifier": "Pixel 5x7 Regular 1.0", "fullName": "Pixel 5x7",
                       "psName": "Pixel5x7-Regular", "version": "Version 1.0",
                       "copyright": "Pixel 5x7 by Trendon (github.com/Trendorin), part of luci-theme-pixel, Apache-2.0"})
    fb.setupOS2(version=4, sTypoAscender=800, sTypoDescender=-300, sTypoLineGap=0, usWinAscent=800, usWinDescent=300,
                sxHeight=500, sCapHeight=700, fsSelection=0x40 | 0x80, achVendID="NONE")
    fb.setupPost(isFixedPitch=0)
    tmp = out + ".ttf"
    fb.save(tmp)
    compress(tmp, out)
    import os
    os.remove(tmp)
    print("glyphs:", len(order) - 1, "->", out)


if __name__ == "__main__":
    main(sys.argv[1])
