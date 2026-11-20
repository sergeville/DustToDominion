"""Native graphics smoke probe, NOT native player-input acceptance.

Uses application window/render APIs and synthetic scenes with isolated settings.
Does not synthesize OS mouse/keyboard events or access the player's save.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'src'))
os.chdir(REPO)


def renderer_metrics():
    window=Window.from_display_module()
    lib=ctypes.CDLL(pygame.base.__file__)
    lib.SDL_GetWindowFromID.argtypes=[ctypes.c_uint32];lib.SDL_GetWindowFromID.restype=ctypes.c_void_p
    lib.SDL_GetRenderer.argtypes=[ctypes.c_void_p];lib.SDL_GetRenderer.restype=ctypes.c_void_p
    lib.SDL_GetRendererOutputSize.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int)]
    ptr=lib.SDL_GetRenderer(lib.SDL_GetWindowFromID(window.id))
    if not ptr:return {'renderer':'none (unscaled software window surface)'}
    width,height=ctypes.c_int(),ctypes.c_int()
    assert lib.SDL_GetRendererOutputSize(ptr,ctypes.byref(width),ctypes.byref(height))==0
    renderer=Renderer.from_window(window)
    return {'output_pixels':[width.value,height.value], 'logical_size':renderer.logical_size,
            'scale':renderer.scale,'viewport':list(renderer.get_viewport()),
            'content_origin_in_window':renderer.coordinates_to_window((0,0)),
            'content_end_in_window':renderer.coordinates_to_window(pygame.display.get_surface().get_size())}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=REPO / "docs/reviews/2026-11-20-native-resolution/native")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='dtd-native-graphics-') as scratch:
        os.environ['DUST_TO_DOMINION_HOME'] = scratch
        os.environ['DUST_TO_DOMINION_CONFIG'] = str(Path(scratch) / 'game.json')
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        import pygame
        from pygame._sdl2.video import Window, Renderer
        globals().update(pygame=pygame,Window=Window,Renderer=Renderer)
        from dtd.main import _init_pygame
        from dtd.main_window import MainWindow
        from dtd.resource_loader import ResourceLoader
        from dtd.audio import init_audio_manager
        from dtd.language import init_language_manager
        from dtd.ui import Theme
        from dtd.campaign import Campaign, Projectile
        from dtd.campaign_store import CampaignStore
        from dtd.screens.campaign import CampaignScreen

        _init_pygame()
        loader = ResourceLoader()
        loader.load(None)
        init_audio_manager(loader, None)
        init_language_manager(loader, 'en-us')
        window = MainWindow()
        output = args.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=True)
        report = {'kind': 'native graphics smoke; synthetic state; no OS input; audio disabled',
                  'base_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  'source_sha256': {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sorted((REPO / 'src/dtd').rglob('*.py'))},
                  'desktop_before': pygame.display.get_desktop_sizes(), 'phases': [],
                  'native_input': 'Not exercised by this probe; physical keyboard/mouse acceptance remains pending'}
        try:
            window.open()
            report['driver'] = pygame.display.get_driver()
            for mode in ('windowed', 'fullscreen', 'returned'):
                if mode != 'windowed':
                    assert window.on_f11()
                for heavy in (False, True):
                    campaign = Campaign()
                    screen = CampaignScreen(Theme('default', '', loader), loader,
                                            campaign, CampaignStore(Path(scratch) / 'campaign.json'))
                    screen._launch(1)
                    if heavy:
                        run = screen.expedition
                        rock = run.asteroids[0]
                        run.x, run.y = rock.x + 120, rock.y
                        run.heading = 3.14159265
                        screen._keys.add(pygame.K_SPACE)
                        run.projectiles = [Projectile(100 + i*17, 270+(i%8)*55,
                                           780, 0, 24, i%2 == 0) for i in range(96)]
                    surface = pygame.display.get_surface()
                    timings, intervals = [], []
                    clock = pygame.time.Clock()
                    previous = time.perf_counter()
                    for frame in range(150):
                        events = pygame.event.get()
                        if any(event.type == pygame.QUIT for event in events):
                            raise RuntimeError('Native probe closed before completion')
                        screen._visual_time = frame / 60  # animation only; fixed stress state
                        started = time.perf_counter()
                        screen.draw(surface)
                        pygame.display.flip()
                        elapsed = (time.perf_counter() - started) * 1000
                        clock.tick(60)
                        now = time.perf_counter()
                        if frame >= 30:
                            timings.append(elapsed)
                            intervals.append((now - previous) * 1000)
                        previous = now
                    timings.sort()
                    label = mode + ('-heavy' if heavy else '-normal')
                    pygame.image.save(surface, str(output / (label + '.png')))
                    row = {'phase': label, 'window_pixels': pygame.display.get_window_size(),
                           'surface_pixels': surface.get_size(),
                           'canvas_pixels': screen._canvas.get_size(),
                           'canvas_is_output': screen._canvas is surface,
                           'renderer':renderer_metrics(),
                           'fullscreen': pygame.display.is_fullscreen(),
                           'render_flip_p50_ms': statistics.median(timings),
                           'render_flip_p95_ms': timings[113],
                           'render_flip_max_ms': max(timings),
                           'paced_interval_p50_ms': statistics.median(intervals),
                           'paced_interval_max_ms': max(intervals),
                           'cache': screen._art.cache_info}
                    report['phases'].append(row)
                    print(json.dumps(row), flush=True)
            report['desktop_after'] = pygame.display.get_desktop_sizes()
            assert report['desktop_before'] == report['desktop_after']
            assert all(hashlib.sha256((REPO/name).read_bytes()).hexdigest()==value for name,value in report['source_sha256'].items())
            report['source_hashes_unchanged']=True
            report['passed'] = True
        finally:
            window.close()
            (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
