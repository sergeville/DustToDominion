"""Spec21 isolated evidence: event-driven slice, synthetic layouts and draw timing.

Run .venv/bin/python docs/reviews/visual_upgrade_validation.py --phase baseline
or --phase slice --slice (then --phase final for the full final matrix).
SDL dummy screenshots are real renderer output, never native play evidence.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src'))
os.chdir(REPO)
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
HOME = Path(tempfile.mkdtemp(prefix='dtd-visual-qa-'))
os.environ['DUST_TO_DOMINION_HOME'] = str(HOME)
os.environ['DUST_TO_DOMINION_CONFIG'] = str(HOME / 'game.json')

import pygame
from dtd.audio import init_audio_manager
from dtd.campaign import Campaign, Pickup, Projectile, STATION_X, STATION_Y, WORLD_BOTTOM
from dtd.campaign_guidance import guidance
from dtd.campaign_store import CampaignStore
from dtd.language import init_language_manager
from dtd.resource_loader import ResourceLoader
from dtd.screens.campaign import CampaignScreen
from dtd.ui import Theme, current_scale

SIZES = ((1280, 720), (1920, 1080), (2560, 1440), (3840, 2160))
VIEWS = ('fresh', 'mining', 'return', 'bottom-edge', 'fleet', 'station', 'combat', 'victory')


def capture(screen, surface, output, name, origin):
    before = copy.deepcopy(screen.campaign)
    before_run = copy.deepcopy(screen.expedition)
    screen.draw(surface)
    # Deep equality ignores Campaign._active, so independently compare the run.
    assert screen.campaign == before and screen.expedition == before_run
    path = output / (name + '.png')
    pygame.image.save(surface, str(path))
    warnings = []
    sx, sy = surface.get_width()/1920, surface.get_height()/1080
    for text, x, y, size, color in getattr(screen, '_text_layer', []):
        font = screen._theme.get_font(max(1, round(size * sy)))
        width, height = font.size(text)
        bounds = pygame.Rect(round(x*sx), round(y*sy), round(width*sx/sy), height)
        if not surface.get_rect().contains(bounds):
            warnings.append({'text': text, 'issue': 'outside framebuffer', 'rect': list(bounds)})
        for button in screen._ui.widgets:
            if bounds.colliderect(current_scale().rect(*button.rect)):
                warnings.append({'text': text, 'issue': 'overlaps button', 'button': button.text})
    return {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'layout_warnings': warnings,
            'pixels': list(surface.get_size()), 'origin': origin,
            'mode': screen.mode}


def player_trip(loader, output):
    module_spec = importlib.util.spec_from_file_location('acceptance_client', REPO / 'tests/test_campaign_acceptance.py')
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    surface = pygame.display.set_mode((1920, 1080))
    init_language_manager(loader, 'en-us')
    pygame.event.clear()
    player = module.PlayerClient(loader)
    player.click('new_game')
    assert CampaignStore().load().credits == 80
    captures = []
    def snap(name):
        captures.append(capture(player.screen, surface, output, 'trip-' + name, 'pygame-event-driven earned mining trip'))
    player.click('launch', sector=1)
    snap('fresh')
    run = player.screen.expedition
    rock = run.asteroids[0]
    # Stand off the rock: a mined fragment remains loose, reproducing the
    # simultaneous collection advice and partial-cut display from user feedback.
    player.travel(rock.x + 120, rock.y)
    player.aim(rock.x, rock.y)
    player.key(pygame.K_SPACE)
    player.screen.advance(1 / 60)
    assert rock.health == 2 and len(run.pickups) == 1
    assert guidance(player.screen.campaign, run).key == 'collect'
    snap('mining')
    player.key(pygame.K_SPACE, False)
    player.travel(rock.x, rock.y)
    player.key(pygame.K_SPACE)
    for _ in range(180):
        player.screen.advance(1 / 60)
        if rock not in run.asteroids and len(run.cargo) == 3:
            break
    else:
        raise AssertionError('Event-driven mining/collection did not finish')
    player.key(pygame.K_SPACE, False)
    assert len(run.cargo) == 3 and not run.pickups
    snap('collected')
    player.travel(STATION_X, STATION_Y)
    player.key(pygame.K_e)
    assert player.screen.mode == 'result' and CampaignStore().load().cargo == [0, 0, 0]
    snap('docked')
    player.click('continue')
    player.click('sell', value=30)
    assert player.screen.campaign.credits == 110 and not player.screen.campaign.cargo
    assert CampaignStore().load().credits == 110
    snap('sold')
    return {'passed': True, 'credits_before': 80, 'credits_after': 110,
            'ore_mined_collected_sold': 3, 'checkpoint_after_dock': [0, 0, 0],
            'collect_and_cut_reproduced': True, 'captures': captures,
            'native_input': False}


def scene(loader, view):
    campaign = Campaign(lifetime_sales=1000 if view == 'combat' else 0)
    screen = CampaignScreen(Theme('default', '', loader), loader, campaign, CampaignStore(HOME / 'fixture.json'))
    if view == 'fleet':
        screen._fleet()
    elif view == 'victory':
        campaign.support_ships = 2
        campaign.miner = campaign.engineer = True
        campaign.credits = 1200
        campaign.won = True
        screen.mode = 'victory'
        screen._rebuild()
    elif view != 'station':
        screen._launch(3 if view == 'combat' else 1)
        run = screen.expedition
        if view == 'mining':
            rock = run.asteroids[0]
            run.x, run.y = rock.x + 120, rock.y + 60
            screen._aim = (rock.x, rock.y)
            screen.update([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE),
                           pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w)])
            screen.advance(.1)
        elif view == 'return':
            run.x, run.y = 1000, 500
            run.cargo = [0] * campaign.capacity
        elif view == 'bottom-edge':
            run.x, run.y = STATION_X, WORLD_BOTTOM
        elif view == 'combat':
            run.x, run.y = 450, 500
            screen._aim = (300, 340)
            run.projectiles = [Projectile(500+i*38, 350+(i%4)*48, -650, 50, 24, i%2 == 0) for i in range(20)]
    return screen


def heavy_scene(loader):
    screen = scene(loader, 'combat')
    run = screen.expedition
    rock = run.asteroids[0]
    run.x, run.y = rock.x + 120, rock.y + 60
    screen._aim = (rock.x, rock.y)
    screen._keys.add(pygame.K_SPACE)
    screen._keys.add(pygame.K_d)
    run.pickups = [Pickup(i, 300+i*90, 530+(i%4)*40, i%3) for i in range(16)]
    run.projectiles = [Projectile(100+(i%16)*108, 240+(i//16)*110, -650, 50, 24, i%2 == 0) for i in range(96)]
    return screen


def rss_mib():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(value / (1024**2 if sys.platform == 'darwin' else 1024), 2)


def benchmark(loader):
    results = []
    for size in SIZES:
        surface = pygame.display.set_mode(size)
        for kind in ('normal', 'effect-heavy'):
            start = time.perf_counter()
            screen = scene(loader, 'fresh') if kind == 'normal' else heavy_scene(loader)
            construction = (time.perf_counter() - start) * 1000
            start = time.perf_counter()
            screen.draw(surface)
            first = (time.perf_counter() - start) * 1000
            for i in range(10):
                screen._visual_time = i/60
                screen.draw(surface)
            memory_before = rss_mib()
            timings = []
            for i in range(120):
                # Same deterministic visual animation/cache workload for both
                # revisions, with no simulation or wall-clock advance.
                screen._visual_time = (i+10)/60
                screen.expedition.heading = -math.pi/2 + math.sin(i/15)*.6
                start = time.perf_counter()
                screen.draw(surface)
                timings.append((time.perf_counter() - start) * 1000)
            ordered = sorted(timings)
            results.append({'pixels': size, 'scene': kind, 'frames': len(timings),
                            'construction_ms': round(construction, 3), 'first_frame_ms': round(first, 3),
                            'median_ms': round(statistics.median(timings), 3),
                            'p95_ms': round(ordered[113], 3), 'p99_ms': round(ordered[118], 3),
                            'max_ms': round(max(timings), 3),
                            'over_16_67_ms': sum(t > 1000/60 for t in timings),
                            'process_peak_rss_before_mib': memory_before, 'process_peak_rss_after_mib': rss_mib()})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('baseline', 'slice', 'final'), required=True)
    parser.add_argument('--slice', action='store_true', help='only the event-driven first-trip acceptance')
    args = parser.parse_args()
    output = REPO / 'docs/reviews/2026-11-20-realistic' / args.phase
    output.mkdir(parents=True, exist_ok=True)
    pygame.init()
    pygame.display.set_mode((1920, 1080))
    loader = ResourceLoader()
    loader.load(None)
    init_audio_manager(loader, None)
    init_language_manager(loader, 'en-us')
    report = {'phase': args.phase,
              'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'tracked_diff': subprocess.check_output(['git', 'diff', '--stat'], text=True),
              'source_sha256': {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted((REPO / 'src/dtd').rglob('*.py'))},
              'platform': platform.platform(), 'machine': platform.machine(),
              'python': platform.python_version(), 'pygame': pygame.version.ver,
              'sdl': pygame.get_sdl_version(), 'driver': pygame.display.get_driver(),
              'evidence': 'SDL dummy offscreen actual renderer; synthetic matrix separate from earned event-driven trip; not native FPS/input',
              'logical_world': [1920, 1080], 'user_persistence_touched': False,
              'memory_note': 'process cumulative peak RSS; includes loaded source art and transforms, not isolated GPU allocation',
              'trip': player_trip(loader, output)}
    print('Event-driven trip passed', flush=True)
    if not args.slice:
        report['captures'] = []
        for locale in ('en-us', 'de'):
            init_language_manager(loader, locale)
            for size in SIZES:
                surface = pygame.display.set_mode(size)
                for view in VIEWS:
                    screen = scene(loader, view)
                    report['captures'].append(capture(screen, surface, output, f'{locale}-{size[0]}-{view}', 'synthetic layout fixture'))
        print('64 layout captures complete', flush=True)
        init_language_manager(loader, 'en-us')
        report['benchmark'] = benchmark(loader)
        # Contact sheets are review aids only; original full-resolution captures
        # above remain the evidence. Labels identify every view and output size.
        label_font = pygame.font.Font(None, 24)
        for locale in ('en-us', 'de'):
            for width, height in SIZES:
                for part in range(2):
                    contact = pygame.Surface((1600, 948))
                    contact.fill((5, 10, 20))
                    for index, view in enumerate(VIEWS[part*4:part*4+4]):
                        x, y = (index % 2)*800, (index // 2)*474
                        original = pygame.image.load(str(output / f'{locale}-{width}-{view}.png'))
                        contact.blit(pygame.transform.smoothscale(original, (800, 450)), (x, y+24))
                        contact.blit(label_font.render(f'{locale} {width}x{height} / {view}', True, (230, 240, 245)), (x+8, y+3))
                    pygame.image.save(contact, str(output / f'contact-{locale}-{width}-{part+1}.png'))
    pygame.quit()
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(output, flush=True)


if __name__ == '__main__':
    main()
