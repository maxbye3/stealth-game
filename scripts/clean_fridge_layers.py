from collections import deque
from pathlib import Path

from PIL import Image


SRC_DIR = Path("fridge")
FILES = ["fridge-0.png", "fridge-1.png", "fridge-2.png", "fridge-3.png"]


def color_distance(a, b):
    return sum((int(a[i]) - int(b[i])) ** 2 for i in range(3)) ** 0.5


def clean_image(path):
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    width, height = image.size

    # The source backgrounds are a soft grey/green wash. Flood from the edges,
    # but only through pixels that look like that low-contrast background.
    background = [[False] * height for _ in range(width)]
    queue = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if background[x][y]:
            continue
        r, g, b, a = pixels[x, y]
        if a == 0:
            background[x][y] = True
        elif max(r, g, b) - min(r, g, b) > 38:
            continue
        elif not (88 <= r <= 205 and 88 <= g <= 205 and 78 <= b <= 195):
            continue
        background[x][y] = True
        base = (r, g, b)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or nx >= width or ny < 0 or ny >= height or background[nx][ny]:
                continue
            nr, ng, nb, na = pixels[nx, ny]
            if na == 0 or color_distance(base, (nr, ng, nb)) <= 46:
                queue.append((nx, ny))

    # Soften the cut by partially fading a 1px edge around removed background.
    for x in range(width):
        for y in range(height):
            if background[x][y]:
                pixels[x, y] = (0, 0, 0, 0)

    seen = [[False] * height for _ in range(width)]
    min_component_area = int(width * height * 0.005)
    for sx in range(width):
        for sy in range(height):
            if seen[sx][sy] or pixels[sx, sy][3] == 0:
                continue
            component = []
            queue = deque([(sx, sy)])
            seen[sx][sy] = True
            while queue:
                x, y = queue.popleft()
                component.append((x, y))
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if nx < 0 or nx >= width or ny < 0 or ny >= height or seen[nx][ny]:
                        continue
                    seen[nx][ny] = True
                    if pixels[nx, ny][3] == 0:
                        continue
                    queue.append((nx, ny))
            if len(component) < min_component_area:
                for x, y in component:
                    pixels[x, y] = (0, 0, 0, 0)

    out = path.with_name(path.stem + "-clean.png")
    image.save(out)
    print(out)


for name in FILES:
    clean_image(SRC_DIR / name)
