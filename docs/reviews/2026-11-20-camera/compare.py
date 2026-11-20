"""Compose equal-scale comparison sheets from untouched game captures.

The originals are1920x1080; both halves below are reduced equally to960x540.
No image synthesis, artwork replacement or selective cropping is involved.
"""
import os
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

root = Path(__file__).resolve().parent
pygame.init()
font = pygame.font.Font(None, 27)
for scene in ('mining', 'combat'):
    board = pygame.Surface((1920, 580))
    board.fill((7, 13, 25))
    for x, path, label in (
        (0, root/'baseline'/f'{scene}.png', 'BEFORE / 1x fixed view'),
        (960, root/'final'/f'en-us-1920-{scene}-z1.5.png', 'AFTER / 1.5x following camera'),
    ):
        source = pygame.image.load(path)
        assert source.get_size() == (1920, 1080)
        board.blit(pygame.transform.smoothscale(source, (960, 540)), (x, 40))
        board.blit(font.render(label+' / same game state', True, (220, 237, 244)), (x+16, 9))
    pygame.image.save(board, root/f'{scene}-before-after.png')
pygame.quit()
