"""Compare equal-sized UI screenshots and save review evidence. Requires Pillow."""
import argparse
from functools import reduce
import hashlib
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('actual', type=Path)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--pixel-tolerance', type=int, default=8,
                        help='maximum allowed per-channel delta (0-255), default 8')
    parser.add_argument('--max-changed-ratio', type=float, default=0.01,
                        help='allowed fraction of pixels beyond tolerance, default 0.01')
    parser.add_argument('--mask', nargs=4, type=int, action='append', default=[],
                        metavar=('X', 'Y', 'W', 'H'), help='exclude an explicitly documented dynamic rectangle')
    args = parser.parse_args()
    if not 0 <= args.pixel_tolerance <= 255:
        parser.error('pixel-tolerance must be between 0 and 255')
    if not math.isfinite(args.max_changed_ratio) or not 0 <= args.max_changed_ratio <= 1:
        parser.error('max-changed-ratio must be finite and between 0 and 1')
    try:
        from PIL import Image, ImageChops, ImageDraw
    except ImportError:
        parser.error('Pillow not installed; install with: pip install pillow')

    outputs = {name: args.out_dir / name for name in
               ('comparison.json', 'overlay.png', 'diff.png', 'side-by-side.png')}
    inputs = {args.reference.resolve(), args.actual.resolve()}
    if len(inputs) < 2:
        parser.error('reference and actual must be separate captures, not the same file')
    if any(path.resolve() in inputs for path in outputs.values()):
        parser.error('output files must not overwrite either input image')
    if any(path.exists() for path in outputs.values()):
        parser.error('evidence already exists; use a new out-dir for each iteration')

    try:
        with Image.open(args.reference) as source:
            reference = source.convert('RGBA')
        with Image.open(args.actual) as source:
            actual = source.convert('RGBA')
    except (OSError, ValueError) as error:
        parser.error(str(error))
    report = {
        'pixel_gate': 'FAIL',
        'reference': {'path': str(args.reference.resolve()), 'size': list(reference.size),
                      'sha256': hashlib.sha256(args.reference.read_bytes()).hexdigest()},
        'actual': {'path': str(args.actual.resolve()), 'size': list(actual.size),
                   'sha256': hashlib.sha256(args.actual.read_bytes()).hexdigest()},
        'pixel_tolerance': args.pixel_tolerance,
        'max_changed_ratio': args.max_changed_ratio,
        'masks': args.mask,
        'note': 'Pixel screening only; inspect layout, text, assets and behavior separately.',
    }
    if reference.size != actual.size:
        report['reason'] = 'size-mismatch'
    else:
        width, height = reference.size
        mask = Image.new('L', reference.size, 255)
        draw = ImageDraw.Draw(mask)
        for x, y, w, h in args.mask:
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
                parser.error('mask X Y W H must be positive-sized and inside both images')
            draw.rectangle((x, y, x + w - 1, y + h - 1), fill=0)
        compared = mask.histogram()[255]
        if not compared:
            parser.error('masks exclude the entire image; nothing remains to compare')
        difference = ImageChops.difference(reference, actual)
        magnitude = reduce(ImageChops.lighter, difference.split())
        histogram = magnitude.histogram(mask=mask)
        changed = sum(histogram[args.pixel_tolerance + 1:])
        mean_error = sum(sum(value * count for value, count in enumerate(channel.histogram(mask=mask)))
                         for channel in difference.split()) / (compared * 4)
        ratio = changed / compared
        report.update(
            pixel_gate='PASS' if ratio <= args.max_changed_ratio else 'FAIL',
            compared_pixels=compared, masked_pixels=width * height - compared,
            changed_pixels=changed, changed_ratio=ratio, mean_absolute_error=mean_error,
            max_channel_delta=max(value for value, count in enumerate(histogram) if count),
        )
        args.out_dir.mkdir(parents=True, exist_ok=True)
        Image.blend(reference, actual, 0.5).save(outputs['overlay.png'])
        visible_delta = ImageChops.multiply(magnitude, mask).point(lambda value: min(255, value * 4))
        black = Image.new('L', reference.size, 0)
        Image.merge('RGB', (visible_delta, black, black)).save(outputs['diff.png'])
        side_by_side = Image.new('RGBA', (width * 2, height))
        side_by_side.paste(reference, (0, 0))
        side_by_side.paste(actual, (width, 0))
        side_by_side.save(outputs['side-by-side.png'])

    args.out_dir.mkdir(parents=True, exist_ok=True)
    outputs['comparison.json'].write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'pixel_gate': report['pixel_gate'], 'report': str(outputs['comparison.json'].resolve())}))
    return 0 if report['pixel_gate'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
