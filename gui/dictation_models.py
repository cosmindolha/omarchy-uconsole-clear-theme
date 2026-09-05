"""Transactional faster-whisper model management, shared by HTTP and WAV replay."""
import json
from pathlib import Path
import threading
import time

from faster_whisper import WhisperModel
from faster_whisper.utils import available_models, download_model


def english_only(name):
    return name.endswith('.en') or name.startswith('distil-')


class Engine:
    def __init__(self, root, settings, loader=WhisperModel, downloader=download_model):
        self.root, self.settings = Path(root), Path(settings)
        self.loader, self.downloader = loader, downloader
        self.lock = threading.RLock()
        self.inference_lock = threading.Lock()
        self.names = available_models()
        self.model = None
        self.active = None
        self.job = {'phase': 'idle', 'target': None, 'error': None}

    def config(self):
        data = json.loads(self.settings.read_text())
        name, language = data.get('model', 'base'), data['language']
        self.validate(name, language)
        return {'model': name, 'language': language}

    def validate(self, name, language):
        if name not in self.names:
            raise ValueError('Choose a model from the list')
        if language not in ('en', 'ro'):
            raise ValueError('Choose English or Romanian')
        if language == 'ro' and english_only(name):
            raise ValueError('This model is English-only; choose a multilingual model for Romanian')

    def path(self, name):
        return self.root / ('faster-whisper-base' if name == 'base' else 'faster-whisper-models/' + name)

    def installed(self, name):
        p = self.path(name)
        return all((p / f).is_file() for f in ('model.bin', 'config.json', 'tokenizer.json')) and any(p.glob('vocabulary.*'))

    def load(self, name):
        return self.loader(str(self.path(name)), device='cpu', compute_type='int8',
                           cpu_threads=4, local_files_only=True)

    def start(self):
        config = self.config()
        self.model = self.load(config['model'])
        self.active = config['model']

    def save(self, data):
        previous = json.loads(self.settings.read_text())
        previous.update(data)
        temp = self.settings.with_suffix('.json.new')
        temp.write_text(json.dumps(previous)+'\n')
        temp.replace(self.settings)

    def state(self):
        with self.lock:
            return dict(self.config(), ready=self.model is not None, engine='faster-whisper',
                        compute='int8', active_model=self.active, job=dict(self.job),
                        models=[{'name': n, 'installed': bool(self.installed(n)),
                                 'english_only': english_only(n)} for n in self.names])

    def set_language(self, language):
        with self.lock:
            if self.job['phase'] not in ('idle', 'error'):
                raise ValueError('Wait for the model change to finish')
            self.validate(self.active, language)
            self.save({'language': language})
        return self.state()

    def select(self, name):
        with self.lock:
            self.validate(name, self.config()['language'])
            if self.job['phase'] not in ('idle', 'error'):
                raise ValueError('A model change is already in progress')
            if name == self.active:
                self.job = {'phase': 'idle', 'target': None, 'error': None}
            else:
                self.job = {'phase': 'loading' if self.installed(name) else 'downloading',
                            'target': name, 'error': None}
                threading.Thread(target=self.switch, args=(name,), daemon=True).start()
        return self.state()

    def switch(self, name):
        try:
            if not self.installed(name):
                self.downloader(name, output_dir=str(self.path(name)))
            with self.lock:
                self.job['phase'] = 'loading'
            candidate = self.load(name)  # Keep working model until replacement loads successfully.
            with self.lock:
                self.save({'model': name})
                self.model, self.active = candidate, name
                self.job = {'phase': 'idle', 'target': None, 'error': None}
        except Exception as error:
            with self.lock:
                self.job = {'phase': 'error', 'target': name, 'error': str(error)[:240]}

    def transcribe(self, audio, language=None):
        started = time.monotonic()
        with self.lock:
            language = language or self.config()['language']
            self.validate(self.active, language)
            selected_model, name = self.model, self.active
        with self.inference_lock:
            segments, info = selected_model.transcribe(audio, language=language, task='transcribe',
                beam_size=1, best_of=1, temperature=0, condition_on_previous_text=False, vad_filter=False)
            text = ''.join(segment.text for segment in segments).strip()
        return {'text': text, 'language': language, 'model': name,
                'seconds': round(time.monotonic()-started, 3), 'audio_seconds': info.duration}
