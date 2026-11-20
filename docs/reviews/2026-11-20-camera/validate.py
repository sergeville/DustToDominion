"""Camera evidence: exact matched fixtures plus an event-earned trip/combat.

SDL dummy output is actual renderer output, not physical desktop interaction.
Baseline state files were captured before camera product changes at b268b1a.
"""
from __future__ import annotations
import argparse
import copy
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import visual_upgrade_validation as qa
from dtd.campaign import Asteroid, Enemy, Pickup, Projectile

p = qa.pygame
OUTPUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('camera_acceptance_client', qa.REPO/'tests/test_campaign_acceptance.py')
acceptance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acceptance)


def plain(obj):
    if dataclasses.is_dataclass(obj):
        return {f.name: plain(getattr(obj, f.name)) for f in dataclasses.fields(obj)
                if f.name not in ('campaign', '_active')}
    if isinstance(obj, (list, tuple)):
        return [plain(item) for item in obj]
    if isinstance(obj, dict):
        return {key: plain(value) for key, value in obj.items()}
    return obj


def projected_view(run, zoom, world):
    # Independent forward reference for the event client, not direct _aim writes.
    cx = max(960/zoom, min(1920-960/zoom, run.x))
    cy = max(145+437.5/zoom, min(1020-437.5/zoom, run.y))
    return 960+(world[0]-cx)*zoom, 582.5+(world[1]-cy)*zoom


class CameraPlayer(acceptance.PlayerClient):
    def __init__(self, loader):
        super().__init__(loader)
        self.firing_view_samples = []

    def aim(self, x, y, pressed=None):
        view = projected_view(self.screen.expedition, self.screen._camera.zoom, (x, y))
        scale = p.display.get_surface().get_width()/1920
        pos = tuple(round(v*scale) for v in view)
        if pressed is True or (pressed is None and self.screen._firing):
            received_view = tuple(v/scale for v in pos)
            assert p.Rect(0, 145, 1920, 875).collidepoint(received_view), 'Earned fire must aim at a visible target'
            self.firing_view_samples.append(received_view)
        self.events(p.event.Event(p.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0)))
        if pressed is not None:
            self.events(p.event.Event(p.MOUSEBUTTONDOWN if pressed else p.MOUSEBUTTONUP,
                                      pos=pos, button=1))


def zoom_events(screen, zoom):
    screen.update([p.event.Event(p.KEYDOWN, key=p.K_HOME)])
    for _ in range({1: 0, 1.5: 1, 2: 2}[zoom]):
        screen.update([p.event.Event(p.KEYDOWN, key=p.K_EQUALS)])
    assert screen._camera.zoom == zoom


def matched_scene(loader, view, zoom):
    state = json.loads((OUTPUT/'baseline'/f'{view}-state.json').read_text())
    campaign = qa.Campaign(**state['campaign'])
    screen = qa.CampaignScreen(qa.Theme('default', '', loader), loader, campaign,
                               qa.CampaignStore(qa.HOME/'synthetic.json'))
    screen._launch(state['run']['sector'])
    classes = {'asteroids': Asteroid, 'enemies': Enemy, 'pickups': Pickup, 'projectiles': Projectile}
    for name, value in state['run'].items():
        setattr(screen.expedition, name, [classes[name](**item) for item in value] if name in classes else value)
    zoom_events(screen, zoom)
    screen._keys = set(state['keys'])
    screen._visual_time = state['visual_time']
    view_aim = projected_view(screen.expedition, zoom, state['aim'])
    scale = p.display.get_surface().get_width()/1920
    screen.update([p.event.Event(p.MOUSEMOTION, pos=tuple(round(v*scale) for v in view_aim))])
    assert plain(campaign) == state['campaign']
    assert plain(screen.expedition) == state['run']
    return screen


def capture(screen, surface, output, name, origin):
    before = copy.deepcopy((screen.campaign, screen.expedition))
    rng = random.getstate()
    item = qa.capture(screen, surface, output, name, origin)
    assert (screen.campaign, screen.expedition) == before
    assert random.getstate() == rng
    item['zoom'] = screen._camera.zoom
    item['world_bounds_warnings'] = []
    if screen.expedition is not None:
        # Actual label backing/bar rectangles are screen-space after projection.
        labels = list(screen._world_labels)
        bars = list(screen._world_bars)
        viewport = p.Rect(0, 145, 1920, 875)
        for kind, bounds in [('label', b) for b in labels]+[('bar', b) for b in bars]:
            if not viewport.contains(bounds):
                item['world_bounds_warnings'].append({'kind': kind, 'issue': 'outside flight viewport', 'rect': list(bounds)})
        for index, a in enumerate(labels):
            for b in labels[index+1:]+bars:
                if a.colliderect(b):
                    item['world_bounds_warnings'].append({'issue': 'label overlaps label/bar', 'a': list(a), 'b': list(b)})
    return item


def earned_play(loader, output):
    p.display.set_mode((1920, 1080))
    qa.init_language_manager(loader, 'en-us')
    p.event.clear()
    player = CameraPlayer(loader)
    player.click('new_game')
    captures = []
    def snap(name):
        captures.append(capture(player.screen, p.display.get_surface(), output, name,
                                'pygame-event-earned progression; no injected game state'))
    player.click('launch', sector=1)
    assert player.screen._camera.zoom == 1.5
    snap('trip-fresh')
    run = player.screen.expedition
    rock = run.asteroids[0]
    player.travel(rock.x+120, rock.y)
    player.aim(rock.x, rock.y)
    player.key(p.K_SPACE)
    player.screen.advance(1/60)
    assert rock.health == 2 and len(run.pickups) == 1
    snap('trip-mining')
    player.key(p.K_SPACE, False)
    player.travel(rock.x, rock.y)
    player.key(p.K_SPACE)
    for _ in range(180):
        player.screen.advance(1/60)
        if rock not in run.asteroids and len(run.cargo) == 3:
            break
    else:
        raise AssertionError('Event-earned mining/collection failed')
    player.key(p.K_SPACE, False)
    snap('trip-collected')
    player.travel(qa.STATION_X, qa.STATION_Y)
    player.key(p.K_e)
    assert player.screen.mode == 'result' and qa.CampaignStore().load().cargo == [0, 0, 0]
    snap('trip-docked')
    player.click('continue')
    player.click('sell', value=30)
    assert player.screen.campaign.credits == 110 and qa.CampaignStore().load().credits == 110
    snap('trip-sold')
    trip = {'passed': True, 'ore': 3, 'credits_before': 80, 'credits_after': 110}
    # Continue the same earned campaign; two full sorties unlock the fringe.
    player.mine_and_sell_sortie()
    player.purchase('cargo')
    player.mine_and_sell_sortie()
    assert player.screen.campaign.lifetime_sales == 330
    player.purchase('laser')
    banked = player.screen.campaign.credits
    player.click('launch', sector=2)
    player.travel(350, 540)
    run = player.screen.expedition
    snap('combat-approach')
    enemy = run.enemies[0]
    player.aim(enemy.x, enemy.y, pressed=True)
    for frame in range(300):
        if not run.enemies:
            break
        enemy = run.enemies[0]
        player.aim(enemy.x, enemy.y)
        player.screen.advance(1/60)
        assert player.screen.mode == 'flight', player.diagnostic()
        if frame == 5:
            snap('combat-firing')
    else:
        raise AssertionError('Earned rival did not fall to aimed fire')
    player.aim(enemy.x, enemy.y, pressed=False)
    assert run.bounty == 70 and run.hull > 0
    assert player.screen.campaign.credits == banked
    snap('combat-defeated-rival')
    player.dock()
    assert player.screen.campaign.credits == banked+70
    assert qa.CampaignStore().load().credits == banked+70
    snap('combat-docked')
    player.click('title')
    player.click('continue')
    assert player.screen.campaign.credits == banked+70
    snap('menu-station')
    player.click('view_fleet')
    snap('menu-fleet')
    player.click('fleet_back')
    return {'trip': trip, 'combat': {'passed': True, 'earned_lifetime_sales': 330,
            'bounty': 70, 'banked_before': banked, 'banked_after': banked+70,
            'continued_checkpoint_verified': True,
            'visible_target_firing_samples': len(player.firing_view_samples),
            'firing_view_min': [min(v[i] for v in player.firing_view_samples) for i in (0, 1)],
            'firing_view_max': [max(v[i] for v in player.firing_view_samples) for i in (0, 1)]},
            'captures': captures, 'native_input': False}


def contacts(output):
    font = p.font.Font(None, 24)
    for locale in ('en-us', 'de'):
        for width, height in qa.SIZES:
            sheet = p.Surface((1800, 724))
            sheet.fill((5, 10, 20))
            for row, view in enumerate(('mining', 'combat')):
                for column, zoom in enumerate((1, 1.5, 2)):
                    x, y = column*600, row*362
                    source = p.image.load(str(output/f'{locale}-{width}-{view}-z{zoom}.png'))
                    sheet.blit(p.transform.smoothscale(source, (600, 338)), (x, y+24))
                    sheet.blit(font.render(f'{locale} {width} {view} zoom {zoom}', True, (230, 240, 245)), (x+5, y+3))
            p.image.save(sheet, str(output/f'contact-{locale}-{width}.png'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('interim', 'final'), required=True)
    parser.add_argument('--earned', action='store_true')
    parser.add_argument('--benchmark', action='store_true')
    parser.add_argument('--benchmark-only', action='store_true', help='append timing to an existing same-source report')
    args = parser.parse_args()
    output = OUTPUT/args.phase
    output.mkdir(parents=True, exist_ok=True)
    p.init()
    p.display.set_mode((1920, 1080))
    loader = qa.ResourceLoader()
    loader.load(None)
    qa.init_audio_manager(loader, None)
    if args.benchmark_only:
        report_path = output/'report.json'
        report = json.loads(report_path.read_text())
        assert all(hashlib.sha256((qa.REPO/name).read_bytes()).hexdigest() == value
                   for name, value in report['source_sha256'].items())
        qa.init_language_manager(loader, 'en-us')
        report['benchmark'] = qa.benchmark(loader)
        report_path.write_text(json.dumps(report, indent=2)+'\n')
        p.quit()
        print('Benchmark appended to same-source report')
        return
    report = {'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'driver': p.display.get_driver(), 'phase': args.phase,
              'source_sha256': {str(f.relative_to(qa.REPO)): hashlib.sha256(f.read_bytes()).hexdigest()
                                for f in sorted((qa.REPO/'src/dtd').rglob('*.py'))},
              'provenance': 'actual SDL dummy renderer; synthetic matched fixtures separate from event-earned play',
              'world_canvas': [1920, 1080], 'offscreen_4k_only': True,
              'captures': [], 'navigation_captures': []}
    if args.earned:
        report['earned'] = earned_play(loader, output)
        print('Event-earned mining trip and combat passed', flush=True)
    for locale in ('en-us', 'de'):
        qa.init_language_manager(loader, locale)
        for size in qa.SIZES:
            surface = p.display.set_mode(size)
            for zoom in (1, 1.5, 2):
                for view in ('mining', 'combat'):
                    screen = matched_scene(loader, view, zoom)
                    report['captures'].append(capture(screen, surface, output,
                        f'{locale}-{size[0]}-{view}-z{zoom}', 'exact serialized baseline model fixture; synthetic'))
            screen = matched_scene(loader, 'combat', 2)
            run = screen.expedition
            run.x, run.y = 960, 190
            run.enemies = [Enemy(42, 960, 520), Enemy(43, 1550, 240)]
            run.projectiles = []
            screen._keys.clear()
            screen._visual_time = 10
            report['navigation_captures'].append(capture(screen, surface, output,
                f'{locale}-{size[0]}-navigation-z2',
                'synthetic legal actor positions: offscreen station/rival plus formerly overlapping enlarged rival'))
    contacts(output)
    if args.benchmark:
        qa.init_language_manager(loader, 'en-us')
        report['benchmark'] = qa.benchmark(loader)
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'output': str(output), 'captures': len(report['captures']),
                      'layout_warnings': sum(len(i['layout_warnings']) for i in report['captures']),
                      'world_bounds_warnings': sum(len(i['world_bounds_warnings']) for i in report['captures'])}))
    p.quit()


if __name__ == '__main__':
    main()
