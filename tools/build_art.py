#!/usr/bin/env python3
"""Favicon, home-screen icons and the web app manifest of luci-theme-pixel.

    python3 build_art.py ../htdocs/luci-static/pixel

Standard library only: PNGs are written with zlib. The mark is the theme's
9x9 router icon, two-tone (bright top, dim bottom) with a one-pixel shadow on
a dark screen, with scanlines baked into the PNGs.
"""
import json
import struct
import sys
import zlib
from pathlib import Path

ROUTER = ".#.....#. .#.....#. .#.....#. .#.....#. ######### #.......# #.#.#.#.# #.......# #########".split()
BG, HI, LO, SH = (0x0a, 0x0a, 0x0a), (0xe4, 0xe4, 0xe4), (0x8c, 0x8c, 0x8c), (0x26, 0x26, 0x26)


def png(path, w, h, px):
    raw = b"".join(b"\x00" + bytes(c for p in px[y * w:(y + 1) * w] for c in p) for y in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def grid(n=16):
    """n x n cells: the 9x9 mark at 1 cell per pixel, centred, with its shadow."""
    g = [[BG] * n for _ in range(n)]
    ox, oy = (n - 10) // 2, (n - 10) // 2
    for y, row in enumerate(ROUTER):
        for x, c in enumerate(row):
            if c == "#":
                g[oy + y + 1][ox + x + 1] = SH
    for y, row in enumerate(ROUTER):
        for x, c in enumerate(row):
            if c == "#":
                g[oy + y][ox + x] = HI if y < 5 else LO
    return g


def icon(path, size, cells, margin=0):
    g = grid(cells)
    scale = (size - 2 * margin) // cells
    off = (size - scale * cells) // 2
    px = []
    for y in range(size):
        for x in range(size):
            gx, gy = (x - off) // scale, (y - off) // scale
            c = g[gy][gx] if 0 <= gx < cells and 0 <= gy < cells and x >= off and y >= off else BG
            if y % 3 == 2:
                c = tuple(int(v * 0.72) for v in c)
            px.append(c)
    png(path, size, size, px)


def main(out):
    out = Path(out)
    icon(out / "icon-192.png", 192, 16)
    icon(out / "icon-512.png", 512, 16)
    icon(out / "icon-180.png", 180, 16)
    icon(out / "icon-mask-512.png", 512, 24)
    rects = lambda rows, pick, ox, oy: "".join(
        f"M{ox + x} {oy + y}h1v1h-1z" for y, r in enumerate(rows) for x, c in enumerate(r) if pick(y, c))
    (out / "logo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" shape-rendering="crispEdges">'
        '<path fill="#0a0a0a" d="M1 0h14v1h1v14h-1v1H1v-1H0V1h1z"/>'
        f'<path fill="#e4e4e4" d="{rects(ROUTER, lambda y, c: c == "#" and y < 5, 3, 3)}"/>'
        f'<path fill="#8c8c8c" d="{rects(ROUTER, lambda y, c: c == "#" and y >= 5, 3, 3)}"/></svg>\n')
    (out / "app.webmanifest").write_text(json.dumps({
        "name": "OpenWrt", "short_name": "OpenWrt", "description": "Router administration (LuCI)",
        "start_url": "/cgi-bin/luci/", "scope": "/", "display": "standalone",
        "background_color": "#0a0a0a", "theme_color": "#0a0a0a",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icon-mask-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]
    }, indent="\t") + "\n")
    print("art written to", out)


if __name__ == "__main__":
    main(sys.argv[1])
