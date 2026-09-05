#!/usr/bin/env python3
"""Loopback-only faster-whisper adapter for Voxtype. No cloud audio transport."""
import argparse
import io
import json
import logging
from pathlib import Path
import threading
import time

from faster_whisper import WhisperModel
from fastapi import FastAPI, File, HTTPException, UploadFile
import uvicorn

ROOT = Path.home() / '.local/share/uconsole'
SETTINGS = Path.home() / '.config/uconsole/dictation.json'
MODEL_DIR = ROOT / 'faster-whisper-base'
LOCK = threading.Lock()
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('uconsole-dictation')
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
model = None


def language_setting():
    language = json.loads(SETTINGS.read_text())['language']
    if language not in ('en', 'ro'):
        raise ValueError('Select English or Romanian in Dictation settings')
    return language


def transcribe(audio, language):
    if language not in ('en', 'ro'):
        raise ValueError('Language must be en or ro; detection is disabled')
    started = time.monotonic()
    with LOCK:
        segments, info = model.transcribe(audio, language=language, task='transcribe',
            beam_size=1, best_of=1, temperature=0, condition_on_previous_text=False,
            vad_filter=False)
        text = ''.join(segment.text for segment in segments).strip()
    elapsed = time.monotonic() - started
    LOG.info('Transcription complete: language=%s audio=%.2fs elapsed=%.2fs chars=%d',
             language, info.duration, elapsed, len(text))
    return {'text': text, 'language': language, 'seconds': round(elapsed, 3)}


@app.get('/health')
def health():
    return {'ready': model is not None, 'engine': 'faster-whisper',
            'model': 'base', 'compute': 'int8', 'language': language_setting()}


@app.post('/v1/audio/transcriptions')
def transcription(file: UploadFile = File(...)):
    # Language comes only from local settings, never from automatic detection
    # or Voxtype's cached language form field. Changes apply to the next clip.
    try:
        language = language_setting()
        audio = file.file.read(8 * 1024 * 1024 + 1)
        if len(audio) > 8 * 1024 * 1024:
            raise HTTPException(413, 'Recording is too large')
        return transcribe(io.BytesIO(audio), language)
    except HTTPException:
        raise
    except Exception:
        LOG.exception('Transcription failed')
        raise HTTPException(500, 'Transcription failed; see uconsole-dictation service logs')
    finally:
        file.file.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help='Transcribe a WAV through the same engine without typing')
    parser.add_argument('--language', choices=['en', 'ro'])
    args = parser.parse_args()
    model = WhisperModel(str(MODEL_DIR), device='cpu', compute_type='int8', cpu_threads=4,
                         local_files_only=True)
    if args.file:
        print(json.dumps(transcribe(args.file, args.language or language_setting()), ensure_ascii=False))
    else:
        language_setting()  # Refuse to start with an invalid language.
        uvicorn.run(app, host='127.0.0.1', port=8769, access_log=False)
