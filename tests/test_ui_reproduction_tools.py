"""Exercise screenshot tooling through its public CLI with small image fixtures."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    from PIL import Image
except ImportError:
    Image = None

ROOT = Path(__file__).resolve().parents[1]
SAMPLER = ROOT / '.codebuddy/skills/cs-ui-spec-from-image/scripts/sample_colors.py'
COMPARE = ROOT / '.codebuddy/skills/cs-ui-generator/scripts/compare_ui.py'


@unittest.skipUnless(Image is not None, 'Pillow is required for image-tool fixtures')
class UiReproductionTools(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ui-reproduction-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def image(self, name, color, size=(8, 6)):
        path = self.directory / name
        Image.new('RGBA', size, color).save(path)
        return path

    def run_cli(self, script, *args):
        self.assertTrue(script.is_file(), f'Missing packaged CLI: {script}')
        return subprocess.run(
            [sys.executable, '-B', str(script), *map(str, args)],
            capture_output=True, text=True, encoding='utf-8', timeout=20,
        )

    def compare(self, reference, actual, *options):
        output = self.directory / 'comparison'
        result = self.run_cli(COMPARE, reference, actual, '--out-dir', output, *options)
        self.assertTrue((output / 'comparison.json').is_file(), result.stderr)
        return result, json.loads((output / 'comparison.json').read_text(encoding='utf-8'))

    def test_default_palette_remains_a_quantized_candidate_list(self):
        path = self.image('white.png', '#FFFFFF')
        result = self.run_cli(SAMPLER, path, 1)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['colors'], [{'hex': '#F8F8F8', 'share': 1.0}])
        self.assertEqual(payload['mode'], 'palette')

    def test_point_preserves_original_color_and_alpha(self):
        path = self.image('alpha.png', (255, 253, 129, 64))
        result = self.run_cli(SAMPLER, path, '--point', 2, 3)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['rgba'], [255, 253, 129, 64])
        self.assertEqual(payload['hex'], '#FFFD8140')
        self.assertEqual(payload['point'], [2, 3])

    def test_region_excludes_surroundings_without_resizing_or_quantization(self):
        path = self.image('region.png', '#000000')
        with Image.open(path) as image:
            image.paste('#FFFFFF', (1, 1, 3, 3))
            image.save(path)
        result = self.run_cli(SAMPLER, path, '--region', 1, 1, 2, 2)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['region'], [1, 1, 2, 2])
        self.assertEqual(payload['colors'][0]['hex'], '#FFFFFF')
        self.assertEqual(payload['colors'][0]['share'], 1.0)
        self.assertEqual([payload['width'], payload['height']], [8, 6])

    def test_sampler_rejects_invalid_bounds_and_counts(self):
        path = self.image('reference.png', '#FFFFFF')
        for options in [('--point', 8, 0), ('--point', -1, 0),
                        ('--region', 0, 0, 9, 1), ('--region', 0, 0, 0, 1), (0,)]:
            with self.subTest(options=options):
                result = self.run_cli(SAMPLER, path, *options)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_equal_screenshots_emit_review_artifacts_and_source_hashes(self):
        reference = self.image('reference.png', '#FAFAFA')
        actual = self.image('actual.png', '#FAFAFA')
        result, report = self.compare(reference, actual)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report['pixel_gate'], 'PASS')
        self.assertEqual(report['changed_pixels'], 0)
        self.assertEqual(report['reference']['sha256'], hashlib.sha256(reference.read_bytes()).hexdigest())
        for name in ('overlay.png', 'diff.png', 'side-by-side.png'):
            with Image.open(self.directory / 'comparison' / name) as artifact:
                self.assertEqual(artifact.height, 6)

    def test_visible_change_fails_the_pixel_gate(self):
        reference = self.image('reference.png', '#FFFFFF')
        actual = self.image('actual.png', '#FFFFFF')
        with Image.open(actual) as image:
            image.putpixel((3, 2), (0, 0, 0, 255))
            image.save(actual)
        result, report = self.compare(reference, actual, '--pixel-tolerance', 0,
                                      '--max-changed-ratio', 0)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report['pixel_gate'], 'FAIL')
        self.assertEqual(report['changed_pixels'], 1)
        self.assertEqual(report['max_channel_delta'], 255)

    def test_threshold_is_applied_per_pixel_inclusively(self):
        reference = self.image('reference.png', '#FFFFFF')
        actual = self.image('actual.png', '#FDFDFD')
        result, report = self.compare(reference, actual, '--pixel-tolerance', 2)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report['changed_pixels'], 0)
        self.assertEqual(report['max_channel_delta'], 2)

    def test_size_mismatch_is_reported_without_resizing(self):
        reference = self.image('reference.png', '#FFFFFF')
        actual = self.image('actual.png', '#FFFFFF', size=(9, 6))
        result, report = self.compare(reference, actual)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report['pixel_gate'], 'FAIL')
        self.assertEqual(report['reason'], 'size-mismatch')
        self.assertEqual(report['actual']['size'], [9, 6])

    def test_only_explicit_rectangles_are_masked(self):
        reference = self.image('reference.png', '#FFFFFF')
        actual = self.image('actual.png', '#FFFFFF')
        with Image.open(actual) as image:
            image.putpixel((3, 2), (0, 0, 0, 255))
            image.save(actual)
        result, report = self.compare(reference, actual, '--mask', 3, 2, 1, 1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report['masked_pixels'], 1)
        self.assertEqual(report['compared_pixels'], 47)
        self.assertEqual(report['masks'], [[3, 2, 1, 1]])

    def test_empty_comparison_and_invalid_thresholds_are_errors(self):
        reference = self.image('reference.png', '#FFFFFF')
        actual = self.image('actual.png', '#FFFFFF')
        for options in [('--mask', 0, 0, 8, 6), ('--mask', 8, 0, 1, 1),
                        ('--pixel-tolerance', 256), ('--max-changed-ratio', 'nan'),
                        ('--max-changed-ratio', -0.1)]:
            with self.subTest(options=options):
                result = self.run_cli(COMPARE, reference, actual, '--out-dir',
                                      self.directory / 'invalid', *options)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_alpha_difference_counts_even_with_identical_rgb(self):
        reference = self.image('reference.png', (255, 255, 255, 255))
        actual = self.image('actual.png', (255, 255, 255, 0))
        result, report = self.compare(reference, actual)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report['changed_pixels'], 48)

    def test_output_cannot_overwrite_an_input(self):
        reference = self.image('overlay.png', '#FFFFFF')
        actual = self.image('actual.png', '#FFFFFF')
        before = reference.read_bytes()
        result = self.run_cli(COMPARE, reference, actual, '--out-dir', self.directory)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(reference.read_bytes(), before)

    def test_previous_iteration_evidence_is_preserved(self):
        reference = self.image('reference.png', '#FFFFFF')
        actual = self.image('actual.png', '#FFFFFF')
        result, _ = self.compare(reference, actual)
        self.assertEqual(result.returncode, 0, result.stderr)
        report_path = self.directory / 'comparison/comparison.json'
        before = report_path.read_bytes()
        Image.new('RGBA', (9, 6), '#000000').save(actual)
        result = self.run_cli(COMPARE, reference, actual, '--out-dir', report_path.parent)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(report_path.read_bytes(), before)

    def test_reference_itself_is_not_a_render_capture(self):
        reference = self.image('reference.png', '#FFFFFF')
        result = self.run_cli(COMPARE, reference, reference, '--out-dir', self.directory / 'self')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
