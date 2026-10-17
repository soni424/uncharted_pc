import ast
import sys
import unittest
from unittest.mock import patch

from paths import ROOT

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_i18n
import uncharted_launcher


class LauncherTranslationTests(unittest.TestCase):
    def test_each_language_translates_play(self):
        expected = {
            'es': 'Jugar', 'pt': 'Jogar', 'fr': 'Jouer', 'de': 'Spielen',
            'it': 'Gioca', 'ja': 'プレイ',
        }
        for language, translation in expected.items():
            with self.subTest(language=language):
                self.assertEqual(uncharted_i18n.translate(language, 'Play'), translation)

    def test_missing_text_falls_back_to_english(self):
        self.assertEqual(uncharted_i18n.translate('es', 'Untranslated text'), 'Untranslated text')
        self.assertEqual(uncharted_i18n.translate('en', 'Play'), 'Play')

    def test_automatic_language_uses_windows_locale(self):
        for language in ('es', 'pt', 'fr', 'de', 'it', 'ja'):
            with self.subTest(language=language), patch.object(
                    uncharted_i18n.locale, 'getlocale', return_value=(f'{language}_XX', 'UTF-8')):
                self.assertEqual(uncharted_i18n.language_code(''), language)
        with patch.object(uncharted_i18n.locale, 'getlocale', return_value=('ko_KR', 'UTF-8')):
            self.assertEqual(uncharted_i18n.language_code(''), 'en')

    def test_launcher_offers_selected_languages(self):
        self.assertEqual(
            [code for code, _name in uncharted_i18n.LANGUAGES],
            ['', 'en', 'es', 'pt', 'fr', 'de', 'it', 'ja'],
        )

    def test_interface_language_help_is_translated(self):
        text = 'This changes only the launcher. The game language is selected on the Game page.'
        self.assertNotEqual(uncharted_i18n.translate('es', text), text)

    def test_each_translation_covers_every_launcher_text(self):
        tree = ast.parse((ROOT / 'launcher' / 'uncharted_launcher.py').read_text(encoding='utf-8'))
        texts = {node.args[0].value for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id == '_' and node.args
                 and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)}
        for language in ('es', 'pt', 'fr', 'de', 'it', 'ja'):
            with self.subTest(language=language):
                self.assertEqual(texts - set(uncharted_i18n.TRANSLATIONS[language]), set())

    def test_display_choice_options_are_translated(self):
        option_sets = (
            uncharted_launcher.GAME_SOURCES,
            uncharted_launcher.PRESENT_MODES,
            uncharted_launcher.FRAME_RATES,
            uncharted_launcher.WINDOW_SIZES,
            uncharted_launcher.SCALERS,
            uncharted_launcher.SHARPENING,
            uncharted_launcher.ANTI_ALIASING,
            (uncharted_launcher.FSR411,),
            uncharted_launcher.AA_SHARPNESS,
            uncharted_launcher.FRAME_GENERATION,
            uncharted_launcher.FRAME_GEN_MULTIPLIERS,
        )
        labels = {label for options in option_sets for _value, label in options}
        technical_labels = {
            'FIFO (VSync)', 'FIFO Relaxed', '120 FPS', '240 FPS',
            '1280 × 720', '1600 × 900', '2560 × 1440', '3840 × 2160 (4K)',
            'TAA', 'NVIDIA DLSS (DLAA, GeForce RTX)',
        }
        for language in ('es', 'pt', 'fr', 'de', 'it', 'ja'):
            for label in labels - technical_labels:
                with self.subTest(language=language, label=label):
                    self.assertNotEqual(uncharted_i18n.translate(language, label), label)


if __name__ == '__main__':
    unittest.main()
