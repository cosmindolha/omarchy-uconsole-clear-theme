import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).resolve().parents[1]/'gui/theme-editor.py'
spec = importlib.util.spec_from_file_location('editor', path)
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)

class PaletteTests(unittest.TestCase):
    def test_presets_and_custom_accents_remain_readable(self):
        for value in [*editor.PRESETS.values(), '#000000', '#100010', '#E879E8', '#FF0000', '#0000FF']:
            with self.subTest(value=value):
                accent, ink, changed = editor.readable(value)
                self.assertGreaterEqual(editor.contrast(accent, '#060709'), 4.5)
                self.assertGreaterEqual(editor.contrast(accent, ink), 4.5)
        self.assertEqual(editor.readable('#E879E8')[0], '#E879E8')

    def test_invalid_color_is_rejected(self):
        for value in ['', 'red', '#FFF', '#1234567', '#GGGGGG', '../theme', None, 123]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError): editor.readable(value)

if __name__ == '__main__': unittest.main()
