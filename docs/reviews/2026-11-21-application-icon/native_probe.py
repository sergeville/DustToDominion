"""Real production startup with isolated persistence and native display smoke.

Automates application APIs, not physical input. No native bundle is built.
Run twice to check independent process restarts; --pak tests pak-only resources.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--pak', type=Path)
    parser.add_argument('--hold', type=float, default=1)
    args = parser.parse_args()
    output = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='dtd-icon-native-') as scratch:
        scratch = Path(scratch)
        os.environ['DUST_TO_DOMINION_HOME'] = str(scratch)
        os.environ['DUST_TO_DOMINION_CONFIG'] = str(scratch / 'game.json')
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        config = {'mainWindow': {'mode': 'windowed'}}
        if args.pak:
            config['resources'] = {'location': [str(args.pak.resolve())]}
        (scratch / 'game.json').write_text(json.dumps(config))
        os.chdir(scratch)
        import pygame
        from dtd import main as app, resource_loader
        if args.pak:
            resource_loader.game_directory = lambda: scratch
        report = {'name': args.name, 'resource_mode': 'pak-only' if args.pak else 'source',
                  'isolated_persistence': True, 'foreign_cwd': True,
                  'physical_input': False, 'audio_driver': 'dummy', 'phases': []}
        real_set_icon = pygame.display.set_icon

        def observe_icon(surface):
            report['icon_before_window'] = pygame.display.get_surface() is None
            assert report['icon_before_window']
            report['icon_size'] = list(surface.get_size())
            report['icon_rgba_sha256'] = hashlib.sha256(pygame.image.tobytes(surface, 'RGBA')).hexdigest()
            real_set_icon(surface)
            report['set_icon_returned'] = True

        pygame.display.set_icon = observe_icon

        def smoke_loop(window, screen, loader):
            report['driver'] = pygame.display.get_driver()
            assert report['driver'] == 'cocoa'
            report['desktop_before'] = pygame.display.get_desktop_sizes()
            try:
                for phase in ('windowed', 'fullscreen', 'returned'):
                    if phase != 'windowed':
                        app._pump_app_events(window, [pygame.event.Event(
                            pygame.KEYDOWN, key=pygame.K_f,
                            mod=pygame.KMOD_CTRL | pygame.KMOD_GUI)], screen)
                    deadline = time.monotonic() + args.hold
                    while time.monotonic() < deadline:
                        events = pygame.event.get()
                        screen.update(events)
                        screen.draw(pygame.display.get_surface())
                        pygame.display.flip()
                        pygame.time.wait(16)
                    report['phases'].append({'phase': phase,
                        'window': list(pygame.display.get_window_size()),
                        'surface': list(pygame.display.get_surface().get_size()),
                        'fullscreen': window._is_fullscreen})
                    assert window._is_fullscreen == (phase == 'fullscreen')
                report['desktop_after'] = pygame.display.get_desktop_sizes()
                assert report['desktop_before'] == report['desktop_after']
            finally:
                screen.close()

        app._run_event_loop = smoke_loop
        code = app.run()
        assert code == 0
        assert not pygame.display.get_init()
        report['exit_code'] = code
        report['display_closed'] = True
        (output / f'{args.name}.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
