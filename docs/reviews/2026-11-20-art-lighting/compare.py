"""Evidence layouts: untouched game frames, equal sizing, no synthesized content."""
import hashlib
import json
import os
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

root = Path(__file__).resolve().parent
repo = root.parents[2]
pygame.init()
font = pygame.font.Font(None, 27)
small = pygame.font.Font(None, 22)
reference_path = repo/'docs/concepts/realistic-visual-target-2026-11-20.png'
reference = pygame.image.load(reference_path)
records = []
for scene, crop in (('mining', (5, 65, 1130, 497)), ('combat', (630, 574, 494, 353))):
    before_path = root/'baseline'/f'{scene}.png'
    after_path = root/'final'/f'en-us-1920-{scene}-z1.5.png'
    before, after = pygame.image.load(before_path), pygame.image.load(after_path)
    assert before.get_size() == after.get_size() == (1920, 1080)
    board = pygame.Surface((1920, 615)); board.fill((7, 13, 25))
    for x, source, label in ((0, before, 'BEFORE / camera pass'), (960, after, 'AFTER / artwork and lighting')):
        board.blit(font.render(label+' / 1.5x / identical scene state', True, (220, 237, 244)), (x+16, 10))
        board.blit(pygame.transform.smoothscale(source, (960, 540)), (x, 40))
    board.blit(small.render('Both originals 1920x1080; equally reduced. Actual renderer fixtures, not physical gameplay screenshots.', True, (139, 165, 182)), (16, 590))
    path = root/f'{scene}-before-after.png'; pygame.image.save(board, path)
    panel = reference.subsurface(crop)
    target = pygame.Rect(960, 40, 960, 540)
    fit = panel.get_rect().fit(target)
    board.fill((7, 13, 25))
    board.blit(font.render('ACTUAL GAME / artwork pass / 1.5x', True, (220, 237, 244)), (16, 10))
    board.blit(pygame.transform.smoothscale(after, (960, 540)), (0, 40))
    board.blit(font.render('REFERENCE PANEL / concept artwork', True, (220, 237, 244)), (976, 10))
    board.blit(pygame.transform.smoothscale(panel, fit.size), fit)
    board.blit(small.render('Equal comparison areas; aspect ratios preserved with letterboxing. Reference art is not a gameplay capture.', True, (139, 165, 182)), (16, 590))
    reference_out = root/f'{scene}-reference.png'; pygame.image.save(board, reference_out)
    for artifact in (before_path, after_path, path, reference_out):
        records.append({'path': str(artifact.relative_to(root)), 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(), 'pixels': list(pygame.image.load(artifact).get_size())})
(root/'comparisons.json').write_text(json.dumps({'reference':str(reference_path.relative_to(repo)), 'reference_sha256':hashlib.sha256(reference_path.read_bytes()).hexdigest(), 'artifacts':records, 'note':'Review layouts, not native game framebuffers; originals preserved.'}, indent=2)+'\n')
pygame.quit()
