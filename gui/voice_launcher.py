"""Push-to-talk application launcher using the shared local speech engine."""
import json
import logging
from pathlib import Path
import signal
import subprocess
import tempfile
import threading
import time

from launcher_match import match_apps
LOG = logging.getLogger("uconsole-voice-launcher")


class VoiceLauncher:
    def __init__(self, engine, root):
        self.engine, self.root = engine, Path(root)
        self.lock = threading.RLock()
        self.proc = None
        self.temp = None
        self.generation = 0
        self.visible = threading.Event()
        self.state = {'phase': 'idle', 'text': '', 'matches': [], 'error': None}

    def catalog(self):
        return json.loads(subprocess.check_output(['/usr/bin/python3', str(self.root/'launcher-catalog.py')], text=True, timeout=8))

    def snapshot(self, visible=False):
        with self.lock:
            if visible and self.state['phase'] == 'results': self.visible.set()
            return dict(self.state)

    def start(self):
        with self.lock:
            if self.state['phase'] in ('recording', 'transcribing', 'opening'):
                raise ValueError('Voice launcher is busy')
            status = subprocess.run(['voxtype', 'status'], capture_output=True, text=True, timeout=5)
            if status.returncode or status.stdout.strip() != 'idle':
                raise ValueError('Finish dictation first')
            self.generation += 1
            generation = self.generation
            self.temp = tempfile.TemporaryDirectory(prefix='uconsole-voice-launcher-')
            self.wav = Path(self.temp.name)/'speech.wav'
            self.proc = subprocess.Popen(['arecord', '-q', '-D', 'default', '-f', 'S16_LE', '-r', '16000',
                                          '-c', '1', '-t', 'wav', '-d', '30', str(self.wav)],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.state = {'phase': 'recording', 'text': '', 'matches': [], 'error': None}
            self.visible = threading.Event()
            LOG.info('Voice launcher recording started')
            timer = threading.Timer(30, self.stop, args=(generation,))
            timer.daemon = True; timer.start()
            subprocess.Popen([str(Path.home()/'.local/bin/uconsole-voice-launcher')],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return self.snapshot()

    def stop(self, generation=None):
        with self.lock:
            if generation is not None and generation != self.generation: return self.snapshot()
            if self.state['phase'] != 'recording': return self.snapshot()
            self.state['phase'] = 'transcribing'
            LOG.info('Voice launcher recording stopped; decoding')
            generation = self.generation
            threading.Thread(target=self.decode, args=(generation,self.proc,self.wav,self.temp,self.visible), daemon=True).start()
        return self.snapshot()

    def decode(self, generation, proc, wav, temp, visible):
        try:
            if proc.poll() is None: proc.send_signal(signal.SIGINT)
            proc.wait(timeout=5)
            result = self.engine.transcribe(str(wav))
            matches, automatic = match_apps(result['text'], self.catalog())
            LOG.info('Voice launcher decoded: chars=%d matches=%d automatic=%s',len(result['text']),len(matches),automatic)
            with self.lock:
                if generation != self.generation: return
                self.state = {'phase': 'results', 'text': result['text'], 'matches': matches,
                              'error': None, 'automatic': automatic}
            if automatic:
                visible.wait(5)
                time.sleep(.8)
                with self.lock:
                    if generation == self.generation and self.state['phase'] == 'results':
                        self.launch(automatic)
        except Exception as error:
            with self.lock:
                if generation == self.generation:
                    self.state.update(phase='error', error=str(error)[:200])
        finally:
            if proc.poll() is None:
                proc.kill();proc.wait(timeout=2)
            temp.cleanup()

    def search(self, text):
        if not isinstance(text, str) or len(text) > 160: raise ValueError('Search is too long')
        with self.lock:
            if self.state['phase'] in ('recording','transcribing','opening'):
                raise ValueError('Wait for the current recording')
            self.generation += 1  # Cancel any pending automatic launch when editing.
            matches, _ = match_apps(text, self.catalog())
            self.state = {'phase':'results','text':text,'matches':matches,'error':None,'automatic':None}
        return self.snapshot()

    def launch(self, app_id):
        with self.lock:
            if self.state['phase'] != 'results' or app_id not in [a['id'] for a in self.state['matches']]:
                raise ValueError('Choose an app from the current results')
            self.state['phase'] = 'opening'
            try:
                subprocess.run(['/usr/bin/python3',str(self.root/'launcher-catalog.py'),'--launch',app_id],
                               check=True, timeout=10, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.state.update(phase='launched', launched=app_id)
                LOG.info('Voice launcher opened %s',app_id)
            except Exception:
                self.state.update(phase='error',error='Could not launch the selected app')
                raise
        return self.snapshot()

    def cancel(self):
        with self.lock:
            was_recording = self.state['phase'] == 'recording'
            self.generation += 1
            if self.proc and self.proc.poll() is None:
                self.proc.send_signal(signal.SIGINT)
                if was_recording:
                    self.proc.wait(timeout=5)
                    self.temp.cleanup()
            self.state.update(phase='idle', automatic=None)
        return self.snapshot()
