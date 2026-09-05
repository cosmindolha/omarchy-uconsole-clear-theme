#!/usr/bin/env python3
"""Loopback-only faster-whisper adapter for Voxtype. No cloud audio transport."""
import argparse
import hmac
import io
import json
import logging
from pathlib import Path
import secrets
import subprocess

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
import uvicorn
from dictation_models import Engine
from voice_launcher import VoiceLauncher

ROOT = Path.home()/'.local/share/uconsole'
SETTINGS = Path.home()/'.config/uconsole/dictation.json'
TOKEN = SETTINGS.with_name('dictation-settings.token')
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('uconsole-dictation')
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
engine = None
launcher = None


@app.get('/health')
def health():
    return engine.state()


@app.get('/launcher')
def launcher_state(visible: bool = False):
    return launcher.snapshot(visible)


@app.post('/launcher')
def launcher_action(data: dict, x_uconsole_settings: str = Header(default='')):
    if not hmac.compare_digest(x_uconsole_settings, TOKEN.read_text().strip()):
        raise HTTPException(403, 'Local launcher only')
    try:
        action = data.get('action')
        if action == 'start': return launcher.start()
        if action == 'stop': return launcher.stop()
        if action == 'cancel': return launcher.cancel()
        if action == 'search': return launcher.search(data.get('text'))
        if action == 'launch': return launcher.launch(data.get('id'))
        raise ValueError('Unknown launcher action')
    except (ValueError, subprocess.SubprocessError) as error:
        raise HTTPException(400, str(error))


@app.post('/settings')
def settings(data: dict, x_uconsole_settings: str = Header(default='')):
    if not hmac.compare_digest(x_uconsole_settings, TOKEN.read_text().strip()):
        raise HTTPException(403, 'Local settings only')
    try:
        if launcher.snapshot()['phase'] in ('recording', 'transcribing'):
            raise ValueError('Finish voice launch before changing settings')
        status = subprocess.run(['voxtype', 'status'], capture_output=True, text=True, timeout=5)
        if status.returncode or status.stdout.strip() != 'idle':
            raise ValueError('Finish dictation, then change settings')
        if set(data) == {'language'}:
            return engine.set_language(data['language'])
        if set(data) == {'model'}:
            return engine.select(data['model'])
        raise ValueError('Choose a language or model')
    except ValueError as error:
        raise HTTPException(400, str(error))


@app.post('/v1/audio/transcriptions')
def transcription(file: UploadFile = File(...)):
    try:
        audio = file.file.read(8*1024*1024+1)
        if len(audio) > 8*1024*1024:
            raise HTTPException(413, 'Recording is too large')
        result = engine.transcribe(io.BytesIO(audio))
        LOG.info('Transcription complete: model=%s language=%s audio=%.2fs elapsed=%.2fs chars=%d',
                 result['model'], result['language'], result['audio_seconds'], result['seconds'], len(result['text']))
        return result
    except HTTPException:
        raise
    except Exception:
        LOG.exception('Transcription failed')
        raise HTTPException(500, 'Transcription failed; see uconsole-dictation service logs')
    finally:
        file.file.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help='Transcribe a WAV without typing')
    parser.add_argument('--language', choices=['en', 'ro'])
    args = parser.parse_args()
    engine = Engine(ROOT, SETTINGS)
    engine.start()
    launcher = VoiceLauncher(engine, ROOT)
    if args.file:
        print(json.dumps(engine.transcribe(args.file, args.language), ensure_ascii=False))
    else:
        if not TOKEN.exists():
            with TOKEN.open('x') as f:
                f.write(secrets.token_urlsafe(32))
            TOKEN.chmod(0o600)
        uvicorn.run(app, host='127.0.0.1', port=8769, access_log=False)
