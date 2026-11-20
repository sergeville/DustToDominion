"""Independent visual invariants; synthetic geometry, never user persistence."""
import copy
import math
import random

import pygame
import pytest

from dtd.campaign import SAFE_RADIUS, STATION_X, STATION_Y
from dtd.campaign_store import CampaignStore
from test_campaign_acceptance import player_factory  # pytest fixture


def scene(player, zoom, position):
    player.click('new_game')
    player.click('launch', sector=1)
    screen, run = player.screen, player.screen.expedition
    run.x, run.y = position
    run.asteroids, run.enemies, run.pickups, run.projectiles = [], [], [], []
    screen._camera.set_zoom(zoom)
    screen._visual_time = 10
    screen._cursor = (1800, 180)
    screen._sync_camera()
    screen._text_layer.clear()
    return screen, run


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
@pytest.mark.parametrize('heading', [0, math.pi/2, math.pi])
def test_pilot_remains_visible_without_obscuring_background_outside_hull(player_factory, zoom, heading):
    player = player_factory(size=(1920, 1080))
    screen, run = scene(player, zoom, (600, 400))
    run.heading = heading
    before = copy.deepcopy((screen.campaign, run))
    rng = random.getstate()
    checkpoint = CampaignStore().path.read_bytes()
    background = (72, 84, 96)
    screen._canvas.fill(background)
    screen._draw_flight()
    cx, cy = screen._camera.world_to_screen((run.x, run.y))
    # The actual hull fits radius32. The former opaque backing filled radius37.
    # Sample the intervening annulus; tiny antialias fringes are tolerated.
    points = [(round(cx+35.5*zoom*math.cos(a*math.tau/72)),
               round(cy+35.5*zoom*math.sin(a*math.tau/72))) for a in range(72)]
    unchanged = sum(tuple(screen._canvas.get_at(point))[:3] == background for point in points)
    assert unchanged >= 68, 'A solid pilot disc or permanent brackets still cover the surrounding background'
    radius = round(32*zoom)
    visible = sum(tuple(screen._canvas.get_at((round(cx)+x, round(cy)+y)))[:3] != background
                  for y in range(-radius, radius+1) for x in range(-radius, radius+1)
                  if x*x+y*y < radius*radius)
    assert visible >= 100*zoom*zoom, 'Removing the backing must not remove the pilot'
    assert (screen.campaign, run) == before
    assert random.getstate() == rng
    assert CampaignStore().path.read_bytes() == checkpoint


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
def test_translucent_shield_keeps_exact_visible_safety_boundary(player_factory, zoom):
    player = player_factory(size=(1920, 1080))
    screen, run = scene(player, zoom, (STATION_X, STATION_Y))
    background = (72, 84, 96)
    screen._canvas.fill(background)
    screen._draw_flight()
    sx, sy = screen._camera.world_to_screen((STATION_X, STATION_Y))
    inside = (round(sx+170*zoom), round(sy))
    color = screen._canvas.get_at(inside)
    assert max(abs(color[i]-background[i]) for i in range(3)) <= 8, 'Shield fill hides the underlying field'
    boundary_x = round(sx)+round(SAFE_RADIUS*zoom)
    boundary_pixels = [screen._canvas.get_at((boundary_x+dx, round(sy)+dy))
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    assert any(max(abs(c[i]-background[i]) for i in range(3)) > 12 for c in boundary_pixels), 'Exact safe boundary disappeared'
    locked = player.text('weapons_locked')
    assert any(row[0] == locked for row in screen._text_layer), 'Safety meaning must remain explicit in HUD'
