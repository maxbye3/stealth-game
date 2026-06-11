import struct
import zlib


FRAME_W = 32
FRAME_H = 40
FRAMES = 4
DIRECTIONS = ["s", "se", "e", "ne", "n", "nw", "w", "sw"]
SHEET_W = FRAME_W * FRAMES
SHEET_H = FRAME_H * len(DIRECTIONS)


def rgba(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4)) + (255,)


TRANSPARENT = (0, 0, 0, 0)
OUTLINE = rgba("#17131d")
HAIR = rgba("#3a211c")
HAIR_LIGHT = rgba("#8f5140")
SKIN = rgba("#e9a878")
SKIN_SHADE = rgba("#b96d55")
SHIRT = rgba("#26364d")
VEST = rgba("#c84646")
PANTS = rgba("#131722")
SHOE = rgba("#080a10")


pixels = [TRANSPARENT] * (SHEET_W * SHEET_H)


def set_px(x, y, color):
    if 0 <= x < SHEET_W and 0 <= y < SHEET_H:
        pixels[y * SHEET_W + x] = color


def rect(x, y, w, h, color):
    for py in range(y, y + h):
        for px in range(x, x + w):
            set_px(px, py, color)


def draw_head(ox, oy, direction):
    side = 0
    if "e" in direction:
        side = 2
    elif "w" in direction:
        side = -2

    rect(ox + 10 + side, oy + 5, 12, 3, OUTLINE)
    rect(ox + 8 + side, oy + 8, 16, 12, OUTLINE)
    rect(ox + 10 + side, oy + 9, 12, 11, SKIN)

    if direction == "n":
        rect(ox + 8, oy + 7, 17, 10, HAIR)
        rect(ox + 12, oy + 6, 9, 3, HAIR_LIGHT)
    else:
        rect(ox + 8 + side, oy + 6, 16, 7, HAIR)
        rect(ox + 10 + side, oy + 5, 9, 4, HAIR)
        rect(ox + 13 + side, oy + 8, 8, 2, HAIR_LIGHT)

    if direction != "n":
        if direction in ("e", "ne", "se"):
            rect(ox + 18 + side, oy + 14, 3, 3, OUTLINE)
        elif direction in ("w", "nw", "sw"):
            rect(ox + 11 + side, oy + 14, 3, 3, OUTLINE)
        else:
            rect(ox + 11, oy + 14, 3, 3, OUTLINE)
            rect(ox + 18, oy + 14, 3, 3, OUTLINE)

    rect(ox + 9 + side, oy + 19, 14, 2, SKIN_SHADE)


def draw_body(ox, oy, direction, frame):
    side = 0
    if "e" in direction:
        side = 2
    elif "w" in direction:
        side = -2

    step = [-2, 0, 2, 0][frame]
    arm_swing = [2, 0, -2, 0][frame]

    rect(ox + 10 + side, oy + 20, 12, 3, OUTLINE)
    rect(ox + 8 + side, oy + 23, 16, 12, OUTLINE)
    rect(ox + 10 + side, oy + 23, 12, 12, SHIRT)
    rect(ox + 14 + side, oy + 23, 4, 12, VEST)

    if direction in ("e", "ne", "se"):
        rect(ox + 8 + arm_swing, oy + 24, 4, 10, OUTLINE)
        rect(ox + 20 - arm_swing, oy + 24, 4, 10, OUTLINE)
        rect(ox + 7 + arm_swing, oy + 33, 4, 3, SKIN)
        rect(ox + 21 - arm_swing, oy + 33, 4, 3, SKIN)
    elif direction in ("w", "nw", "sw"):
        rect(ox + 8 - arm_swing, oy + 24, 4, 10, OUTLINE)
        rect(ox + 20 + arm_swing, oy + 24, 4, 10, OUTLINE)
        rect(ox + 7 - arm_swing, oy + 33, 4, 3, SKIN)
        rect(ox + 21 + arm_swing, oy + 33, 4, 3, SKIN)
    else:
        rect(ox + 6 - arm_swing, oy + 24, 5, 10, OUTLINE)
        rect(ox + 21 + arm_swing, oy + 24, 5, 10, OUTLINE)
        rect(ox + 6 - arm_swing, oy + 33, 4, 3, SKIN)
        rect(ox + 22 + arm_swing, oy + 33, 4, 3, SKIN)

    rect(ox + 10 + step, oy + 34, 5, 5, PANTS)
    rect(ox + 17 - step, oy + 34, 5, 5, PANTS)
    rect(ox + 9 + step, oy + 38, 7, 2, SHOE)
    rect(ox + 16 - step, oy + 38, 7, 2, SHOE)


def draw_frame(col, row, direction, frame):
    ox = col * FRAME_W
    oy = row * FRAME_H
    rect(ox + 8, oy + 36, 16, 3, (0, 0, 0, 74))
    draw_body(ox, oy, direction, frame)
    draw_head(ox, oy, direction)


for row, direction in enumerate(DIRECTIONS):
    for frame in range(FRAMES):
        draw_frame(frame, row, direction, frame)


def png_chunk(kind, data):
    chunk = kind + data
    return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)


raw = bytearray()
for y in range(SHEET_H):
    raw.append(0)
    for x in range(SHEET_W):
        raw.extend(pixels[y * SHEET_W + x])

with open("assets/pixel-person-sheet.png", "wb") as out:
    out.write(b"\x89PNG\r\n\x1a\n")
    out.write(png_chunk(b"IHDR", struct.pack(">IIBBBBB", SHEET_W, SHEET_H, 8, 6, 0, 0, 0)))
    out.write(png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
    out.write(png_chunk(b"IEND", b""))
