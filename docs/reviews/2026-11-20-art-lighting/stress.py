"""Synthetic simultaneous effect-cap draw timing; not an earned gameplay claim."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('art_evidence', HERE/'validate.py')
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)
qa = evidence.camera.qa
p = qa.pygame
p.init()
p.display.set_mode((1920, 1080))
loader = qa.ResourceLoader()
loader.load(None)
qa.init_audio_manager(loader, None)
qa.init_language_manager(loader, 'en-us')
results = []
for size in qa.SIZES:
    output = p.display.set_mode(size)
    screen = qa.heavy_scene(loader)
    run = screen.expedition
    # Emit through production observation APIs, then hold maximum overlapping
    # presentation counts for every measured frame. This is deliberately harsher
    # than the short, naturally decaying effects in the earned route.
    rocks = {i: (350+i*60, 500, 44, i%3, 3) for i in range(9)}
    screen._fragments.advance(0, rocks, SimpleNamespace(asteroids=[], x=600, y=600), mining=True)
    enemies = {i: (320+(i%10)*70, 350+(i//10)*80, 50) for i in range(40)}
    empty = SimpleNamespace(x=run.x, y=run.y, hull=run.hull, enemies=[])
    screen._impacts.advance(0, enemies, empty)
    assert len(screen._fragments.items) == 96
    assert len(screen._impacts.items) == 32
    assert len(screen._impacts.bursts) == 8
    times = []
    for i in range(130):
        phase = (i%20)/100
        screen._visual_time = i/60
        run.heading = -math.pi/2+math.sin(i/15)*.6
        for shard in screen._fragments.items:
            shard.age = phase
        screen._impacts.items = [(x,y,phase,c) for x,y,_,c in screen._impacts.items]
        screen._impacts.bursts = [(x,y,phase,s) for x,y,_,s in screen._impacts.bursts]
        start = time.perf_counter()
        screen.draw(output)
        elapsed = (time.perf_counter()-start)*1000
        if i >= 10:
            times.append(elapsed)
    ordered = sorted(times)
    results.append({'pixels': size, 'frames': len(times), 'median_ms': round(statistics.median(times),3),
                    'p95_ms': round(ordered[113],3), 'max_ms': round(max(times),3),
                    'over_16_67_ms': sum(t>1000/60 for t in times),
                    'light_cache': screen._lights.cache_info})
p.quit()
report = {'provenance': 'synthetic simultaneous cap stress; actual SDL dummy draw-only timing, no simulation/presentation/native FPS claim',
          'world_canvas': [1920,1080], 'counts': {'shards':96,'impact_flashes':32,'destruction_bursts':8,'projectiles':96},
          'source_sha256': {str(f.relative_to(qa.REPO)):hashlib.sha256(f.read_bytes()).hexdigest()
                            for f in sorted((qa.REPO/'src/dtd').rglob('*.py'))}, 'results':results}
(HERE/'final/effect-cap-stress.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(results,indent=2))
