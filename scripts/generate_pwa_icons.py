"""Generate 192x192 and 512x512 PWA icons matching ward-icon.svg."""
from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Install Pillow: pip install pillow")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "static" / "images"


def _font(size: int):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_icon(size: int) -> Image.Image:
    scale = size / 128
    img = Image.new("RGBA", (size, size), (10, 15, 26, 255))
    draw = ImageDraw.Draw(img)

    margin = int(8 * scale)
    radius = int(24 * scale)
    inner_radius = int(20 * scale)
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=radius,
        fill=(30, 41, 59, 255),
        outline=(56, 189, 248, 255),
        width=max(2, int(2 * scale)),
    )

    font = _font(int(56 * scale))
    w_text = "W"
    bbox = draw.textbbox((0, 0), w_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = int(78 * scale) - th // 2 - int(8 * scale)
    draw.text((tx, ty), w_text, fill=(56, 189, 248, 255), font=font)

    line_y = int(96 * scale)
    line_w = int(64 * scale)
    line_x = (size - line_w) // 2
    draw.line(
        (line_x, line_y, line_x + line_w, line_y),
        fill=(167, 139, 250, 255),
        width=max(3, int(3 * scale)),
    )

    return img


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for dim in (192, 512):
        icon = draw_icon(dim)
        path = OUT_DIR / f"ward-icon-{dim}.png"
        icon.save(path, "PNG", optimize=True)
        print(f"Wrote {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()