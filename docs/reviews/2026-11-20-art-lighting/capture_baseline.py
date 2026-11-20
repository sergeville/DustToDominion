"""Immutable before-art/lighting evidence at matched camera fixture states."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent / 'baseline'
spec = importlib.util.spec_from_file_location('camera_evidence', ROOT/'docs/reviews/2026-11-20-camera/validate.py')
camera = importlib.util.module_from_spec(spec)
spec.loader.exec_module(camera)
qa, p = camera.qa, camera.p

def hashes(paths):
    return {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(paths)}

def main():
    if (OUTPUT/'report.json').exists():
        raise SystemExit('Baseline already frozen; refusing overwrite')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    sources = list((ROOT/'src/dtd').rglob('*.py'))
    source_hashes = hashes(sources)
    resources = hashes(f for f in (ROOT/'resources').rglob('*') if f.is_file())
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=10).strip()
    for source in sources:
        target = OUTPUT/'sources'/source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    p.init()
    surface = p.display.set_mode((1920, 1080))
    loader = qa.ResourceLoader()
    loader.load(None)
    qa.init_audio_manager(loader, None)
    qa.init_language_manager(loader, 'en-us')
    captures = []
    for view in ('mining', 'combat'):
        source = camera.OUTPUT/'baseline'/f'{view}-state.json'
        shutil.copyfile(source, OUTPUT/source.name)
        screen = camera.matched_scene(loader, view, 1.5)
        captures.append(camera.capture(screen, surface, OUTPUT, view,
            'synthetic exact camera fixture, default 1.5x, before artwork/lighting changes'))
    assert hashes(sources) == source_hashes, 'Product mutated during baseline capture'
    report = {'revision': revision, 'driver': p.display.get_driver(),
              'source_sha256': source_hashes, 'resource_sha256': resources,
              'captures': captures, 'zoom': 1.5, 'pixels': [1920, 1080],
              'world_canvas': [1920, 1080], 'native_input': False,
              'provenance': 'actual SDL dummy framebuffer before source changes; exact prior camera matched states'}
    (OUTPUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    p.quit()
    print(json.dumps({'revision': revision, 'sources': len(sources), 'resources': len(resources), 'captures': captures}))

if __name__ == '__main__':
    main()
