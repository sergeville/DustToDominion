"""Actual separate-process no-device startup plus isolated earned gameplay."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / 'unavailable'
OUT.mkdir(exist_ok=True)
spec = importlib.util.spec_from_file_location('camera_evidence', ROOT/'docs/reviews/2026-11-20-camera/validate.py')
camera = importlib.util.module_from_spec(spec)
spec.loader.exec_module(camera)
# The old evidence helper defaults to dummy; override before pygame initializes.
os.environ['SDL_AUDIODRIVER'] = 'dtd-deliberately-unavailable-driver'
from dtd import audio, main

original_get = camera.p.event.get
camera.p.event.get = lambda: [camera.p.event.Event(camera.p.QUIT)]
try:
    startup_exit = main.run()
finally:
    camera.p.event.get = original_get
assert startup_exit == 0
assert not audio.get_audio_manager().available
assert os.environ['SDL_AUDIODRIVER'] == 'dtd-deliberately-unavailable-driver'

main._init_pygame()
assert camera.p.mixer.get_init() is None
camera.p.display.set_mode((1920, 1080))
loader = camera.qa.ResourceLoader()
loader.load(None)
camera.qa.init_audio_manager(loader, None)
result = camera.earned_play(loader, OUT)
assert not audio.get_audio_manager().available
report = {'production_startup_exit': startup_exit,
          'startup_event': 'injected SDL QUIT; original main.run and event loop',
          'driver': os.environ['SDL_AUDIODRIVER'], 'mixer_initialized': False,
          'earned': result, 'physical_input': False, 'audio_output': False,
          'source_sha256': {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
                            for f in sorted((ROOT/'src/dtd').rglob('*.py'))}}
(OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
camera.p.quit()
print('Actual unavailable-driver startup, earned trip/combat/reload passed')
