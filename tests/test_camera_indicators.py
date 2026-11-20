from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import math
from pathlib import Path

import pygame
import pytest

from dtd.camera_indicators import offscreen_indicators, draw_indicators


VIEW = pygame.Rect(0, 145, 1920, 875)
PLAYER = (960, 580)


def markers(station=PLAYER, threats=(), **kwargs):
    return offscreen_indicators(player=PLAYER, station=station, threats=threats,
                                project=kwargs.pop('project', lambda p: p),
                                viewport=VIEW, **kwargs)


def test_visible_centers_and_exact_view_edges_need_no_markers():
    for point in ((0, 145), (1920, 145), (0, 1020), (1920, 1020), PLAYER):
        assert markers(station=point, threats=[(1, *point)]) == ()


@pytest.mark.parametrize('point,axis,sign', [((-100, 580), 0, -1), ((2100, 580), 0, 1),
                                          ((960, 0), 1, -1), ((960, 1200), 1, 1)])
def test_cardinal_arrows_point_outward_and_stay_clear_of_hud(point, axis, sign):
    marker, = markers(station=point)
    assert marker.direction[axis] == sign
    assert VIEW.contains(marker.bounds)
    assert VIEW.contains(marker.label_rect)
    assert marker.distance == pytest.approx(math.dist(PLAYER, point))


def test_true_world_distance_does_not_change_with_projection_scale():
    world_target = (1400, 580)
    assert not markers(station=world_target)
    marker, = markers(station=world_target, project=lambda p: (960+3*(p[0]-960), 580+3*(p[1]-580)))
    assert marker.distance == 440
    assert marker.position[0] < 1920


def test_station_priority_nearest_two_threats_and_explicit_extra_count():
    rivals = [(8, 2300, 580), (4, 2200, 580), (7, 2000, 580), (1, 2000, 580)]
    before = deepcopy(rivals)
    result = markers(station=(2400, 580), threats=rivals)
    assert [(m.kind, m.target_id) for m in result] == [('station', None), ('threat', 1), ('threat', 7)]
    assert [m.extra_threats for m in result] == [0, 0, 2]
    assert result == markers(station=(2400, 580), threats=reversed(rivals))
    assert rivals == before
    with pytest.raises(FrozenInstanceError):
        result[0].distance = 1


@pytest.mark.parametrize('target', [(-100, -100), (2200, -100), (-100, 1300), (2200, 1300),
                                  (-100, 580), (2200, 580), (960, -100), (960, 1300)])
def test_coincident_bearings_keep_three_chips_and_arrows_separate(target):
    result = markers(station=target, threats=[(1, *target), (2, *target)])
    assert len(result) == 3
    for index, marker in enumerate(result):
        assert VIEW.contains(marker.bounds)
        assert all(not pygame.Rect(marker.bounds).colliderect(other.bounds)
                   for other in result[index+1:])


def test_adjacent_corner_edges_do_not_collide():
    result = markers(station=(1900, -100), threats=[(1, 2200, 155), (2, 2100, -20)])
    assert len(result) == 3
    for index, marker in enumerate(result):
        assert all(not pygame.Rect(marker.bounds).colliderect(other.bounds)
                   for other in result[index+1:])


def test_invalid_points_cannot_poison_navigation():
    assert markers(station=(math.nan, 0), threats=[(1, math.inf, 0)]) == ()
    assert offscreen_indicators(player=(math.nan, 1), station=(0, 0), threats=[], project=lambda p:p) == ()
    assert markers(station=(0, 0), project=lambda p:(math.nan, 0)) == ()


def test_station_chip_does_not_cover_enlarged_rival_at_bottom_edge():
    from dtd.campaign_camera import Camera
    camera = Camera(2)
    camera.follow(960, 190)
    x, y = camera.world_to_screen((960, 520))
    hull = pygame.Rect(x-58, y-58, 116, 116)
    options = dict(player=(960, 190), station=(960, 750), threats=[(1, 960, 520)],
                   project=camera.world_to_screen, viewport=camera.viewport)
    old, = offscreen_indicators(**options)
    assert pygame.Rect(old.label_rect).colliderect(hull)
    corrected, = offscreen_indicators(**options, obstacles=[hull])
    assert not pygame.Rect(corrected.bounds).colliderect(hull)
    assert corrected.distance == old.distance
    assert corrected.direction == old.direction
    assert VIEW.contains(corrected.bounds)


@pytest.mark.parametrize('language', ['en-us', 'de'])
def test_localized_draw_uses_screen_font_hook_and_bounded_text(font_ready, language):
    root = Path(__file__).resolve().parents[1]
    strings = json.loads((root/'resources/languages'/f'{language}.json').read_text())['campaign']
    font = pygame.font.Font(str(root/'resources/fonts/Audiowide-Regular.ttf'), 18)
    surface = pygame.Surface((1920, 1080))
    records = markers(station=(2400, 580), threats=[(i, 2500+i*10, 580) for i in range(8)])
    calls = []
    reservations = draw_indicators(surface, records, lambda *args, **kwargs:calls.append((args, kwargs)),
                                   lambda key, **values:strings[key].format(**values))
    assert reservations == tuple(m.bounds for m in records)
    assert len(calls) == 3
    assert '+6' in calls[-1][0][0]
    for record, (args, kwargs) in zip(records, calls):
        text, x, y = args
        assert pygame.Rect(record.label_rect).contains(pygame.Rect(x, y, *font.size(text)))
        assert kwargs['size'] == 18
    assert '1.5' in strings['camera_zoom'].format(value='1.5')
