"""Native graphics smoke probe, NOT native player-input acceptance.

Uses application window/render APIs and synthetic scenes with isolated settings.
Does not synthesize OS mouse/keyboard events or access the player's save.
"""
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src'))
os.chdir(REPO)


def main():
    with tempfile.TemporaryDirectory(prefix='dtd-native-graphics-') as scratch:
        os.environ['DUST_TO_DOMINION_HOME'] = scratch
        os.environ['DUST_TO_DOMINION_CONFIG'] = str(Path(scratch) / 'game.json')
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        import pygame
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
        output = REPO / 'docs/reviews/2026-11-20-realistic/native'
        output.mkdir(exist_ok=True)
        report = {'kind': 'native graphics smoke; synthetic state; no OS input; audio disabled',
                  'desktop_before': pygame.display.get_desktop_sizes(), 'phases': [],
                  'native_input': 'Pending: CUA omits uv Python; direct executable getApp returned Invalid app'}
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
            report['passed'] = True
        finally:
            window.close()
            (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
