import sys
import unittest

from paths import ROOT

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_launcher as launcher


class WindowLayoutTests(unittest.TestCase):
    def test_high_dpi_1440p_fits_the_available_work_area(self):
        fit = launcher.fit_scale((0, 0, 2560, 1400), (32, 80))
        self.assertEqual(launcher.ui_scale_for(2.25, fit), 1.45)

    def test_small_work_area_clamps_size_and_minimum(self):
        size, minimum = launcher.fit_to_area((1180, 860), (1040, 760), (0, 0, 1000, 700), (20, 60))
        self.assertEqual(size, (980, 640))
        self.assertEqual(minimum, (980, 640))

    def test_minimizing_preserves_the_last_maximized_setting(self):
        self.assertTrue(launcher.maximized_after(True, 'iconic'))
        self.assertFalse(launcher.maximized_after(False, 'iconic'))
        self.assertFalse(launcher.maximized_after(True, 'normal'))


if __name__ == '__main__':
    unittest.main()
