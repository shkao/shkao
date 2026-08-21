import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "trim_holds.py"
SPEC = importlib.util.spec_from_file_location("trim_holds", SCRIPT)
trim = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trim)

SIZE = 64 * 132


def frame(value: int) -> bytes:
    return bytes([value]) * SIZE


def checkerboard() -> bytes:
    return bytes([0 if i % 2 else 255 for i in range(SIZE)])


class SplashTests(unittest.TestCase):
    def test_a_full_screen_repaint_in_the_opening_second_is_a_splash(self):
        frames = [frame(255), frame(255), frame(0)] + [frame(0)] * 40

        self.assertEqual(trim.splash_end(frames), 2)

    def test_a_recording_that_opens_on_content_is_left_alone(self):
        frames = [checkerboard()] * 40

        self.assertEqual(trim.splash_end(frames), 0)

    def test_a_partial_repaint_is_not_a_splash(self):
        half = bytes([0] * (SIZE // 2) + [255] * (SIZE - SIZE // 2))
        frames = [frame(255), half] + [half] * 40

        self.assertEqual(trim.splash_end(frames), 0)

    def test_a_late_cut_is_not_a_splash(self):
        frames = [frame(255)] * 30 + [frame(0)] * 30

        self.assertEqual(trim.splash_end(frames), 0)


class HoldTests(unittest.TestCase):
    def test_long_holds_are_capped_and_motion_is_untouched(self):
        moving = [50.0] * 5
        deltas = [999.0] + moving + [0.0] * 40 + moving

        ranges = trim.keep_ranges(deltas, 0)
        kept = sum(end - start + 1 for start, end in ranges)

        self.assertEqual(kept, 1 + len(moving) + trim.MAX_HOLD + len(moving))

    def test_a_hold_shorter_than_the_cap_survives_whole(self):
        deltas = [999.0] + [50.0] + [0.0] * (trim.MAX_HOLD - 2) + [50.0]

        self.assertEqual(trim.keep_ranges(deltas, 0), [(0, len(deltas) - 1)])

    def test_output_starts_at_the_splash_cut(self):
        deltas = [999.0, 0.0, 0.0, 170.0] + [50.0] * 10

        ranges = trim.keep_ranges(deltas, 3)

        self.assertEqual(ranges[0][0], 3)

    def test_ranges_are_contiguous_and_ordered(self):
        deltas = [999.0] + [50.0, 0.0, 0.0] * 30

        ranges = trim.keep_ranges(deltas, 0)

        for (_, end), (start, _) in zip(ranges, ranges[1:]):
            self.assertLess(end, start)


if __name__ == "__main__":
    unittest.main()
