import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('dictation_editor', Path(__file__).parents[1]/'gui/theme-editor.py')
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)


class DictationSettings(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.path = self.home/'.config/uconsole/dictation.json'
        self.path.parent.mkdir(parents=True)
        self.path.write_text('{"language":"en","preserve":true}')
        self.patch = patch.object(editor, 'HOME', self.home)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_language_persists_without_service_restart(self):
        with patch.object(editor, 'run', return_value='idle') as run:
            self.assertEqual(editor.set_dictation_language('ro'), {'language':'ro'})
            run.assert_called_once_with(['voxtype', 'status'])
        self.assertEqual(json.loads(self.path.read_text()), {'language':'ro','preserve':True})

    def test_busy_recording_keeps_language(self):
        before = self.path.read_text()
        with patch.object(editor, 'run', return_value='recording'):
            with self.assertRaises(ValueError): editor.set_dictation_language('ro')
        self.assertEqual(self.path.read_text(), before)

    def test_auto_detection_is_rejected(self):
        before = self.path.read_text()
        with self.assertRaises(ValueError): editor.set_dictation_language('auto')
        self.assertEqual(self.path.read_text(), before)
