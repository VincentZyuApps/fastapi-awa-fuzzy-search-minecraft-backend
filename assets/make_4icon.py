from pathlib import Path
from PIL import Image

ASSETS = Path(__file__).parent

FILES = [
    ("fastapi.png",             0, 0),
    ("huggingface.png",         1, 0),
    ("minecraft-creeper.png",   0, 1),
    ("pytorch.png",             1, 1),
]

CW = CH = 1000
CELL_W = CELL_H = CW // 2
TARGET = int(CELL_W * 0.8)

canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))

for fname, col, row in FILES:
    img = Image.open(ASSETS / fname).convert("RGBA")
    img.thumbnail((TARGET, TARGET), Image.LANCZOS)
    x = col * CELL_W + (CELL_W - img.width) // 2
    y = row * CELL_H + (CELL_H - img.height) // 2
    canvas.paste(img, (x, y), img)

output = ASSETS / "4icon.png"
canvas.save(output)
print(f"✅ 已生成 {output} ({CW}×{CH})")
