"""Presentation regressions for restrained overlays, independent of hull artwork."""
import math

import pygame
import pytest

from test_campaign_presentation import presentation


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
def test_empty_space_around_pilot_is_not_replaced_by_a_solid_disk(presentation, monkeypatch, zoom):
    screen = presentation
    screen._launch(1)
    run = screen.expedition
    run.x, run.y = 400., 300.
    run.asteroids.clear()
    screen._camera.set_zoom(zoom)
    screen._sync_camera()
    screen._visual_time = 10
    # Isolate overlay occlusion from source hull pixels and surrounding actors.
    for name in ('draw_ship', 'draw_station', 'draw_field_detail'):
        monkeypatch.setattr(screen._art, name, lambda *args, **kwargs: None)
    background = (23, 31, 46)
    screen._canvas.fill(background)
    screen._draw_flight()
    x, y = screen._camera.world_to_screen((run.x, run.y))
    # Samples in the old radius37 disk, beyond the radius32 hull; neither
    # directional guidance nor cursor intersects these lateral points.
    for angle in (-math.pi/2, math.pi):
        point = (round(x+math.cos(angle)*35*zoom), round(y+math.sin(angle)*35*zoom))
        assert screen._canvas.get_at(point)[:3] == background


def test_target_corners_remain_visible_with_less_ink_at_all_radii(presentation):
    screen = presentation
    color = (246, 106, 110)
    for radius in (24, 48, 100):
        screen._canvas.fill((0, 0, 0))
        screen._brackets(400, 400, radius, color)
        mask = pygame.mask.from_threshold(screen._canvas, color, (1, 1, 1))
        # Four open corners need visible marks, not thick panels or full rings.
        assert 40 <= mask.count() <= 100
        for sx in (-1, 1):
            for sy in (-1, 1):
                assert screen._canvas.get_at((400+sx*radius, 400+sy*radius))[:3] == color
        assert screen._canvas.get_at((400, 400-radius))[:3] == (0, 0, 0)
