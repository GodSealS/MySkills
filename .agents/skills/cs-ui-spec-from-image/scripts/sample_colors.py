"""Print palette candidates or original point/region RGBA samples. Requires Pillow."""
import argparse
import json
from collections import Counter


def color_hex(rgba):
    channels = rgba[:3] if rgba[3] == 255 else rgba
    return '#' + ''.join(f'{value:02X}' for value in channels)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image')
    parser.add_argument('max_colors', nargs='?', type=int, default=8)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--point', nargs=2, type=int, metavar=('X', 'Y'))
    mode.add_argument('--region', nargs=4, type=int, metavar=('X', 'Y', 'W', 'H'))
    args = parser.parse_args()
    if args.max_colors < 1:
        parser.error('max_colors must be positive')
    try:
        from PIL import Image
    except ImportError:
        print(json.dumps({
            "error": "Pillow not installed",
            "install": "pip install pillow",
        }))
        return 1

    try:
        with Image.open(args.image) as source:
            image = source.convert('RGBA')
    except (OSError, ValueError) as error:
        parser.error(str(error))
    width, height = image.size
    result = {'path': args.image, 'width': width, 'height': height}
    if args.point:
        x, y = args.point
        if not (0 <= x < width and 0 <= y < height):
            parser.error('point must be inside the original image')
        rgba = image.getpixel((x, y))
        result.update(mode='point', point=args.point, rgba=rgba, hex=color_hex(rgba),
                      note='Original stored RGBA; not composited or color-profile converted.')
    else:
        if args.region:
            x, y, w, h = args.region
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
                parser.error('region X Y W H must be positive-sized and inside the original image')
            sample = image.crop((x, y, x + w, y + h))
            counts = Counter(sample.getdata())
            result.update(mode='region', region=args.region,
                          note='Original RGBA histogram; no resizing, quantization or compositing.')
        else:
            sample = image.copy()
            sample.thumbnail((160, 160))
            counts = Counter((r // 8 * 8, g // 8 * 8, b // 8 * 8, 255)
                             for r, g, b, a in sample.getdata() if a >= 128)
            result.update(mode='palette', note='Quantized candidates only; confirm roles and sample original pixels.')
        total = sum(counts.values()) or 1
        colors = []
        for rgba, count in counts.most_common(args.max_colors):
            entry = {'hex': color_hex(rgba), 'share': round(count / total, 4)}
            if args.region:
                entry['rgba'] = rgba
            colors.append(entry)
        result['colors'] = colors
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
