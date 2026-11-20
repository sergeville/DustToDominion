"""Isolated polish captures; synthetic layouts are not native play evidence."""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import visual_upgrade_validation as qa

p = qa.pygame
OUTPUT = Path(__file__).resolve().parent


def scene(loader, view):
    screen = qa.scene(loader, view if view in ('station', 'fleet') else 'combat' if view == 'combat' else 'mining')
    if view == 'mining':
        run = screen.expedition
        rock = run.asteroids[0]
        run.x, run.y = rock.x, rock.y - 80
        screen._aim = (rock.x, rock.y)
        screen._visual_time = 10
    elif view == 'combat':
        run = screen.expedition
        rock = run.asteroids[0]
        rock.ore = 1
        run.x, run.y = rock.x + 120, rock.y - 90
        run.enemies[0].x, run.enemies[0].y = rock.x, rock.y
        run.enemies[0].heading = -.7
        run.enemies = run.enemies[:1]
        screen._visual_time = 10
    return screen


def capture(screen, surface, output, name, origin):
    before = copy.deepcopy((screen.campaign, screen.expedition))
    rng = random.getstate()
    bars = []
    draw_bar = screen._bar
    def record_bar(x, y, width, fraction, color):
        if 145 <= y < 1026 and width < 150:
            bars.append(p.Rect(x, y, width, 10))
        return draw_bar(x, y, width, fraction, color)
    screen._bar = record_bar
    try:
        item = qa.capture(screen, surface, output, name, origin)
    finally:
        screen._bar = draw_bar
    assert (screen.campaign, screen.expedition) == before
    assert random.getstate() == rng
    item['world_label_warnings'] = []
    run = screen.expedition
    if run is not None:
        labels = []
        # Match actual deferred glyph measurement, plus the six/three pixel
        # backing allowance. This does not infer absence from colors alone.
        for text, x, y, size, color in screen._text_layer:
            if not 145 <= y < 1026:
                continue
            sy = surface.get_height()/1080
            physical_width, physical_height = screen._theme.get_font(max(1, round(size*sy))).size(text)
            logical_width, logical_height = screen._theme.get_font(size).size(text)
            width = max(logical_width, math.ceil(physical_width/sy))
            height = max(logical_height, math.ceil(physical_height/sy))
            bounds = p.Rect(x, y, width, height).inflate(12, 6)
            labels.append((text, bounds))
            actors = [('player', run.x, run.y, 38)] + [
                ('rival', enemy.x, enemy.y, 30) for enemy in run.enemies]
            for kind, ax, ay, radius in actors:
                actor = p.Rect(ax-radius, ay-radius, radius*2, radius*2)
                if bounds.colliderect(actor):
                    item['world_label_warnings'].append({'text': text, 'issue': 'overlaps '+kind,
                                                       'label_rect': list(bounds), 'actor_rect': list(actor)})
            for bar in bars:
                if bounds.colliderect(bar):
                    item['world_label_warnings'].append({'text': text, 'issue': 'overlaps health bar',
                                                       'label_rect': list(bounds), 'bar_rect': list(bar)})
        for index, (text, bounds) in enumerate(labels):
            for other, other_bounds in labels[index+1:]:
                if bounds.colliderect(other_bounds):
                    item['world_label_warnings'].append({'text': text, 'issue': 'overlaps label', 'other': other})
        item['world_bar_warnings'] = [{'issue': 'overlapping health bars', 'first': list(a), 'second': list(b)}
                                     for i, a in enumerate(bars) for b in bars[i+1:] if a.colliderect(b)]
    return item


def contacts(output):
    font = p.font.Font(None, 24)
    for locale in ('en-us', 'de'):
        for width, height in qa.SIZES:
            sheet = p.Surface((1600, 948))
            sheet.fill((5, 10, 20))
            for index, view in enumerate(('mining', 'combat', 'station', 'fleet')):
                x, y = (index%2)*800, (index//2)*474
                original = p.image.load(str(output/f'{locale}-{width}-{view}.png'))
                sheet.blit(p.transform.smoothscale(original, (800, 450)), (x, y+24))
                sheet.blit(font.render(f'{locale} {width}x{height} / {view}', True, (230, 240, 245)), (x+8, y+3))
            p.image.save(sheet, str(output/f'contact-{locale}-{width}.png'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('baseline', 'final'), required=True)
    parser.add_argument('--benchmark', action='store_true')
    parser.add_argument('--trip', action='store_true')
    args = parser.parse_args()
    output = OUTPUT / args.phase
    output.mkdir(exist_ok=True)
    p.init()
    p.display.set_mode((1920, 1080))
    loader = qa.ResourceLoader()
    loader.load(None)
    qa.init_audio_manager(loader, None)
    report = {'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'phase': args.phase, 'driver': p.display.get_driver(),
              'evidence': 'Actual SDL dummy renderer; synthetic layout states; no physical native input',
              'logical_world': [1920, 1080], 'offscreen_4k_only': True,
              'source_sha256': {str(path.relative_to(qa.REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in sorted((qa.REPO/'src/dtd').rglob('*.py'))},
              'captures': []}
    for locale in ('en-us', 'de'):
        qa.init_language_manager(loader, locale)
        for size in qa.SIZES:
            surface = p.display.set_mode(size)
            for view in ('mining', 'combat', 'station', 'fleet'):
                screen = scene(loader, view)
                report['captures'].append(capture(screen, surface, output, f'{locale}-{size[0]}-{view}',
                                                   'synthetic stress layout fixture'))
    qa.init_language_manager(loader, 'en-us')
    if args.trip:
        report['trip'] = qa.player_trip(loader, output)
    if args.benchmark:
        report['benchmark'] = qa.benchmark(loader)
    contacts(output)
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'output': str(output), 'captures': len(report['captures']),
                      'layout_warnings': sum(len(item['layout_warnings']) for item in report['captures']),
                      'world_label_warnings': sum(len(item['world_label_warnings']) for item in report['captures'])}))
    p.quit()


if __name__ == '__main__':
    main()
