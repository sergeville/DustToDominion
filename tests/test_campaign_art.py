"""Read-only rendering contracts and recognizable geometry at gameplay scale."""
import copy
import math
import random

import pygame
import pytest

from dtd.campaign import Asteroid
from dtd.campaign_art import draw_asteroid, draw_ship, draw_station


def canvas():
    return pygame.Surface((400, 400), pygame.SRCALPHA)


def pixels(surface):
    return pygame.image.tobytes(surface, 'RGBA')


@pytest.mark.parametrize('kind', ['prospector', 'hauler', 'refinery', 'rival'])
@pytest.mark.parametrize('size', [24, 90])
def test_ship_draw_is_deterministic_and_has_solid_hull(kind, size):
    a, b = canvas(), canvas()
    random_state = random.getstate()
    draw_ship(a, 200, 200, .71, kind, size, True, 1.25)
    draw_ship(b, 200, 200, .71, kind, size, True, 1.25)
    assert pixels(a) == pixels(b)
    assert random.getstate() == random_state
    mask = pygame.mask.from_surface(a)
    assert mask.count() > size * size * .65
    assert mask.get_at((200, 200))
    assert a.get_bounding_rect().width < size * 3.3
    assert a.get_bounding_rect().height < size * 3.3


def test_ship_silhouettes_are_distinct_not_only_colors():
    masks = []
    for kind in ('prospector', 'hauler', 'refinery', 'rival'):
        surface = canvas()
        draw_ship(surface, 200, 200, 0, kind, 70)
        masks.append(pygame.mask.from_surface(surface))
    for i, a in enumerate(masks):
        for b in masks[i + 1:]:
            difference = a.count() + b.count() - 2*a.overlap_area(b, (0, 0))
            assert difference > 500


def test_heading_rotates_geometry_and_thrust_stays_aft():
    right, down, idle = canvas(), canvas(), canvas()
    draw_ship(right, 200, 200, 0, thrust=True, size=70)
    draw_ship(down, 200, 200, math.pi/2, thrust=True, size=70)
    draw_ship(idle, 200, 200, 0, size=70)
    assert right.get_bounding_rect().left < idle.get_bounding_rect().left
    assert right.get_bounding_rect().right == idle.get_bounding_rect().right
    assert abs(right.get_bounding_rect().width-down.get_bounding_rect().height) <= 2
    assert abs(right.get_bounding_rect().height-down.get_bounding_rect().width) <= 2
    assert down.get_bounding_rect().top < 200 - 70


def test_phase_changes_only_active_thrust():
    idle_a, idle_b, burning_a, burning_b = [canvas() for _ in range(4)]
    draw_ship(idle_a, 200, 200, 0, size=90, phase=0)
    draw_ship(idle_b, 200, 200, 0, size=90, phase=.1)
    draw_ship(burning_a, 200, 200, 0, size=90, thrust=True, phase=0)
    draw_ship(burning_b, 200, 200, 0, size=90, thrust=True, phase=.1)
    assert pixels(idle_a) == pixels(idle_b)
    assert pixels(burning_a) != pixels(burning_b)


@pytest.mark.parametrize('ore', [0, 1, 2])
def test_rock_draw_preserves_model_rng_and_modeled_radius(ore):
    rock = Asteroid(19, 200, 200, 48, ore, 2, 4)
    original = copy.deepcopy(rock)
    state = random.getstate()
    a, b = canvas(), canvas()
    draw_asteroid(a, rock)
    draw_asteroid(b, rock)
    assert rock == original
    assert random.getstate() == state
    assert pixels(a) == pixels(b)
    assert pygame.Rect(151, 151, 99, 99).contains(a.get_bounding_rect())
    assert pygame.mask.from_surface(a).count() > 4000


def test_station_is_repeatable_inside_dock_geometry():
    a, b = canvas(), canvas()
    draw_station(a, 200, 200)
    draw_station(b, 200, 200)
    assert pixels(a) == pixels(b)
    assert pygame.Rect(100, 100, 201, 201).contains(a.get_bounding_rect())
    assert pygame.mask.from_surface(a).count() > 10000


def test_empty_size_and_unknown_kind_contract():
    surface = canvas()
    draw_ship(surface, 200, 200, 0, size=0)
    draw_asteroid(surface, Asteroid(1, 200, 200, 0, 0))
    assert pygame.mask.from_surface(surface).count() == 0
    with pytest.raises(ValueError, match='Unknown ship kind'):
        draw_ship(surface, 200, 200, 0, 'missing')
