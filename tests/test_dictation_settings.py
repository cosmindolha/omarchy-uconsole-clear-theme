import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

# Exercise lifecycle and failure behavior without downloading models in CI.
with patch.dict('sys.modules', {
    'faster_whisper': SimpleNamespace(WhisperModel=lambda *a, **k: object()),
    'faster_whisper.utils': SimpleNamespace(available_models=lambda: ['base','tiny','tiny.en','distil-large-v3'], download_model=lambda *a, **k: None),
}):
    spec = importlib.util.spec_from_file_location('dictation_models', Path(__file__).parents[1]/'gui/dictation_models.py')
    models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models)


class DictationModels(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = self.root/'settings.json'
        self.settings.write_text('{"language":"en","preserve":true}')
        self.engine = models.Engine(self.root, self.settings)
        self.engine.start()
        self.original = self.engine.model

    def wait(self):
        deadline = time.monotonic()+2
        while self.engine.state()['job']['phase'] not in ('idle','error'):
            if time.monotonic() > deadline: self.fail('Switch did not finish')
            time.sleep(.01)

    def test_download_keeps_original_then_commits(self):
        entered, release = threading.Event(), threading.Event()
        self.engine.downloader = lambda *a, **k: (entered.set(), release.wait(2))
        self.engine.select('tiny')
        self.assertTrue(entered.wait(1))
        self.assertIs(self.engine.model, self.original)
        self.assertEqual(self.engine.config()['model'], 'base')
        with self.assertRaises(ValueError): self.engine.select('tiny.en')
        release.set(); self.wait()
        self.assertEqual(self.engine.active, 'tiny')
        self.assertEqual(json.loads(self.settings.read_text()), {'language':'en','model':'tiny','preserve':True})
        restarted = models.Engine(self.root, self.settings)
        restarted.start()
        self.assertEqual(restarted.active, 'tiny')

    def test_failed_model_keeps_working_model_and_settings(self):
        before = self.settings.read_text()
        self.engine.loader = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('Broken model'))
        self.engine.select('tiny'); self.wait()
        self.assertEqual(self.engine.state()['job']['phase'], 'error')
        self.assertIs(self.engine.model, self.original)
        self.assertEqual(self.settings.read_text(), before)

    def test_romanian_rejects_english_models(self):
        self.engine.set_language('ro')
        for name in ['tiny.en','distil-large-v3']:
            with self.assertRaises(ValueError): self.engine.select(name)
        self.assertEqual(self.engine.config()['model'], 'base')

    def test_english_model_rejects_romanian_language(self):
        self.engine.select('tiny.en');self.wait()
        with self.assertRaises(ValueError): self.engine.set_language('ro')
        self.assertEqual(self.engine.config()['language'], 'en')

    def test_invalid_selection_does_not_touch_settings(self):
        before = self.settings.read_text()
        with self.assertRaises(ValueError): self.engine.select('../../bad')
        with self.assertRaises(ValueError): self.engine.set_language('auto')
        self.assertEqual(self.settings.read_text(), before)
