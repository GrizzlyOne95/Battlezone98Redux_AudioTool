from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def _font(size: int):
    candidates = [
        Path(r"C:\Windows\Fonts\ariblk.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _parse_text(svg: str):
    pattern = re.compile(r'<text\s+x="([\d.]+)"\s+y="([\d.]+)"\s+font-size="([\d.]+)"([^>]*)>(.*?)</text>')
    for match in pattern.finditer(svg):
        yield float(match.group(1)), float(match.group(2)), int(float(match.group(3))), html.unescape(match.group(5))


def render(svg_path: Path) -> Image.Image:
    svg = svg_path.read_text(encoding="utf-8")
    accent_match = re.search(r'<circle[^>]*fill="(#[0-9A-Fa-f]{6})"', svg)
    accent = accent_match.group(1) if accent_match else "#7e57c2"
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    ImageDraw.Draw(image).rounded_rectangle((10, 10, 502, 502), radius=78, fill="#0b0d10", outline="#34373b", width=3)
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((51, 51, 461, 461), fill=accent + "B0")
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
    draw = ImageDraw.Draw(image)
    draw.ellipse((51, 51, 461, 461), fill=accent)
    for x, y, size, text in _parse_text(svg):
        draw.text((x, y - size * 0.34), text, font=_font(size), fill="white", anchor="mm")
    line = re.search(r'<path\s+d="M([\d.]+)\s+([\d.]+)H([\d.]+)"[^>]*stroke-width="([\d.]+)"', svg)
    if line:
        x1, y, x2 = map(float, line.group(1, 2, 3))
        draw.line((x1, y, x2, y), fill="white", width=int(float(line.group(4))))
    return image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_svg", type=Path)
    parser.add_argument("output_ico", type=Path)
    args = parser.parse_args()
    render(args.source_svg).save(args.output_ico, format="ICO", sizes=SIZES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
