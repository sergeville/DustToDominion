"""Native desktop smoke test; uses temporary settings and never loads a real save.

Run with the project interpreter from the repo root. Opens a synthetic station,
toggles fullscreen twice, writes size evidence/screenshots, then closes itself.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src'))
os.chdir(REPO)

with tempfile.TemporaryDirectory(prefix='dtd-native-display-') as scratch:
    os.environ['DUST_TO_DOMINION_HOME'] = scratch
    os.environ['DUST_TO_DOMINION_CONFIG'] = str(Path(scratch) / 'game.json')
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    import pygame
    from dtd.main import _init_pygame, _pump_app_events
    from dtd.main_window import MainWindow
    from dtd.resource_loader import ResourceLoader
    from dtd.audio import init_audio_manager
    from dtd.language import init_language_manager
    from dtd.ui import Theme
    from dtd.campaign import Campaign
    from dtd.campaign_store import CampaignStore
    from dtd.screens.campaign import CampaignScreen

    output = REPO / 'docs/reviews/2026-11-20-display'
    output.mkdir(exist_ok=True)
    _init_pygame()
    desktop = pygame.display.get_desktop_sizes()
    loader = ResourceLoader()
    loader.load(None)
    init_audio_manager(loader, None)
    init_language_manager(loader, 'en-us')
    window = MainWindow()
    screen = CampaignScreen(Theme('default', 'fonts/Aldrich-Regular.ttf', loader),
                            loader, Campaign(), CampaignStore(Path(scratch) / 'campaign.json'))
    report = {'desktop_before': desktop, 'phases': []}

    def observe(label):
        deadline = time.monotonic() + 1.2
        while time.monotonic() < deadline:
            pygame.event.get()
            screen.draw(pygame.display.get_surface())
            pygame.display.flip()
            time.sleep(0.02)
        row = {'phase': label, 'window': pygame.display.get_window_size(),
               'surface': pygame.display.get_surface().get_size(),
               'fullscreen': pygame.display.is_fullscreen(),
               'desktop': pygame.display.get_desktop_sizes()}
        report['phases'].append(row)
        pygame.image.save(pygame.display.get_surface(), str(output / (label + '.png')))
        print(json.dumps(row), flush=True)
        assert row['desktop'] == desktop, 'Monitor resolution changed'
        return row

    try:
        window.open()
        initial = observe('windowed')
        assert initial['window'] == (1920, 1080)
        for cycle in range(2):
            assert window.on_f11()
            full = observe(f'fullscreen-{cycle}')
            assert full['fullscreen']
            assert full['window'] == desktop[0]
            assert full['surface'] == (1920, 1080)
            # SDL scales mouse coordinates into the same logical UI space.
            button = screen._ui.widgets[-1]  # View fleet
            pygame.mouse.set_pos(button.rect.center)
            pygame.event.pump()
            pos = pygame.mouse.get_pos()
            assert abs(pos[0] - button.rect.centerx) <= 1
            assert abs(pos[1] - button.rect.centery) <= 1
            screen.update([pygame.event.Event(t, pos=pos, button=1)
                           for t in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)])
            assert screen.mode == 'fleet'
            screen._station()
            _pump_app_events(window, [pygame.event.Event(
                pygame.KEYDOWN, key=pygame.K_f, mod=pygame.KMOD_CTRL | pygame.KMOD_GUI)])
            back = observe(f'returned-{cycle}')
            assert not back['fullscreen']
            assert back['window'] == (1920, 1080)
        report['mouse_logical_position_and_fleet_click'] = True
        report['passed'] = True
    finally:
        window.close()
        (output / 'native-display.json').write_text(json.dumps(report, indent=2) + '\n')
