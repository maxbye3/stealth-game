import struct
import zlib


SOURCE = "oscar/oscar-sprite.png"
OUTPUT = "oscar/oscar-sprite-clean.png"
CELL_W = 128
CELL_H = 250

# Source crops: 5 animation frames across, then down/left/right/up rows.
COLS = [196, 348, 500, 652, 804]
ROWS = {
    "s": 360,
    "w": 662,
    "e": 960,
    "n": 1260,
}
ORDER = ["s", "e", "w", "n"]


def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a PNG")

    offset = 8
    width = height = color_type = None
    raw = b""
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
          width, height, bit_depth, color_type, compression, png_filter, interlace = struct.unpack(">IIBBBBB", payload)
          if bit_depth != 8 or compression != 0 or png_filter != 0 or interlace != 0:
              raise ValueError("Unsupported PNG format")
        elif kind == b"IDAT":
            raw += payload
        elif kind == b"IEND":
            break

    channels = {2: 3, 6: 4}[color_type]
    stride = width * channels
    inflated = zlib.decompress(raw)
    rows = []
    pos = 0
    previous = bytearray(stride)

    for _ in range(height):
        filter_type = inflated[pos]
        pos += 1
        scan = bytearray(inflated[pos : pos + stride])
        pos += stride
        for i in range(stride):
            left = scan[i - channels] if i >= channels else 0
            up = previous[i]
            up_left = previous[i - channels] if i >= channels else 0
            if filter_type == 1:
                scan[i] = (scan[i] + left) & 255
            elif filter_type == 2:
                scan[i] = (scan[i] + up) & 255
            elif filter_type == 3:
                scan[i] = (scan[i] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                p = left + up - up_left
                pa = abs(p - left)
                pb = abs(p - up)
                pc = abs(p - up_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
                scan[i] = (scan[i] + predictor) & 255
            elif filter_type != 0:
                raise ValueError("Unsupported PNG filter")
        rows.append(scan)
        previous = scan

    pixels = []
    for scan in rows:
        out_row = []
        for x in range(width):
            idx = x * channels
            r, g, b = scan[idx], scan[idx + 1], scan[idx + 2]
            a = scan[idx + 3] if channels == 4 else 255
            out_row.append((r, g, b, a))
        pixels.append(out_row)
    return width, height, pixels


def png_chunk(kind, payload):
    chunk = kind + payload
    return struct.pack(">I", len(payload)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)


def write_png(path, width, height, pixels):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend(pixels[y][x])
    with open(path, "wb") as out:
        out.write(b"\x89PNG\r\n\x1a\n")
        out.write(png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
        out.write(png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
        out.write(png_chunk(b"IEND", b""))


_, _, source = read_png(SOURCE)
sheet_w = CELL_W * len(COLS)
sheet_h = CELL_H * len(ORDER)
clean = [[(0, 0, 0, 0) for _ in range(sheet_w)] for _ in range(sheet_h)]

for row_index, direction in enumerate(ORDER):
    sy = ROWS[direction]
    for col_index, sx in enumerate(COLS):
        for y in range(CELL_H):
            for x in range(CELL_W):
                r, g, b, a = source[sy + y][sx + x]
                if r < 18 and g < 18 and b < 18:
                    a = 0
                clean[row_index * CELL_H + y][col_index * CELL_W + x] = (r, g, b, a)

write_png(OUTPUT, sheet_w, sheet_h, clean)
