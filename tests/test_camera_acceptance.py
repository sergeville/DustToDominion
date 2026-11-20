"""Independent camera/input acceptance with shipped art and isolated saves.

Reference arithmetic here deliberately does not call the production camera's
inverse mapping. Physical desktop input is not represented by SDL dummy tests.
"""
import copy
import math
import random

import pygame
import pytest

from dtd.campaign import WORLD_BOTTOM, WORLD_LEFT, WORLD_RIGHT, WORLD_TOP
from dtd.campaign_store import CampaignStore
from test_campaign_acceptance import player_factory  # pytest fixture


def center_at(run, zoom):
    half_width, half_height = 960 / zoom, 437.5 / zoom
    return (max(half_width, min(1920 - half_width, run.x)),
            max(145 + half_height, min(1020 - half_height, run.y)))


def inverse_at(run, zoom, view):
    cx, cy = center_at(run, zoom)
    return cx + (view[0] - 960) / zoom, cy + (view[1] - 582.5) / zoom


def forward_at(run, zoom, world):
    cx, cy = center_at(run, zoom)
    return 960 + (world[0] - cx) * zoom, 582.5 + (world[1] - cy) * zoom


def zoom_to(player, zoom):
    player.key(pygame.K_HOME)
    for _ in range({1: 0, 1.5: 1, 2: 2}[zoom]):
        player.key(pygame.K_EQUALS)
    assert player.screen._camera.zoom == zoom


def view_event(player, view, event_type=pygame.MOUSEMOTION):
    factor = pygame.display.get_surface().get_width() / 1920
    pos = tuple(round(v * factor) for v in view)
    values = {'pos': pos}
    if event_type != pygame.MOUSEMOTION:
        values['button'] = 1
    player.events(pygame.event.Event(event_type, **values))
    return tuple(v / factor for v in pos)


def flight(player_factory, size=(1920, 1080)):
    player = player_factory('en-us', size)
    player.click('new_game')
    player.click('launch', sector=1)
    assert player.screen._camera.zoom == 1.5
    player.travel(750, 350)
    return player


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
@pytest.mark.parametrize('size', [(1280, 720), (1920, 1080), (2560, 1440), (3840, 2160)])
def test_rendered_target_inverse_aim_and_projectile_direction(player_factory, zoom, size):
    player = flight(player_factory, size)
    zoom_to(player, zoom)
    run = player.screen.expedition
    target = (run.x + 150, run.y + 70)
    view = forward_at(run, zoom, target)
    received = view_event(player, view, pygame.MOUSEBUTTONDOWN)
    view_event(player, view, pygame.MOUSEBUTTONUP)
    expected = inverse_at(run, zoom, received)
    assert player.screen._aim == pytest.approx(expected)
    player.screen.advance(1 / 60)
    shot = next(shot for shot in run.projectiles if shot.friendly)
    angle = math.atan2(expected[1] - run.y, expected[0] - run.x)
    assert (shot.vx, shot.vy) == pytest.approx((780 * math.cos(angle), 780 * math.sin(angle)))


@pytest.mark.parametrize('held', [False, True])
def test_stationary_view_cursor_tracks_camera_during_each_step(player_factory, monkeypatch, held):
    player = flight(player_factory)
    player.travel(960, 400)
    run = player.screen.expedition
    view = (1130, 430)
    received = view_event(player, view, pygame.MOUSEBUTTONDOWN if held else pygame.MOUSEMOTION)
    observed = []
    step = run.step
    def observe(dt, controls):
        expected = inverse_at(run, 1.5, received)
        assert (controls.aim_x, controls.aim_y) == pytest.approx(expected)
        assert controls.firing is held
        observed.append((controls.aim_x, controls.aim_y))
        return step(dt, controls)
    monkeypatch.setattr(run, 'step', observe)
    player.key(pygame.K_d)
    for _ in range(12):
        player.screen.advance(1 / 60)
    player.key(pygame.K_d, False)
    assert len(observed) == 12 and observed[-1][0] - observed[0][0] == pytest.approx(55)


def test_released_tap_keeps_click_world_target_after_zoom_motion_and_cursor_move(player_factory, monkeypatch):
    player = flight(player_factory)
    run = player.screen.expedition
    view = forward_at(run, 1.5, (run.x + 200, run.y))
    received = view_event(player, view, pygame.MOUSEBUTTONDOWN)
    view_event(player, view, pygame.MOUSEBUTTONUP)
    click_world = inverse_at(run, 1.5, received)
    player.events(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=1))
    assert player.screen._camera.zoom == 2
    view_event(player, (400, 700))
    inputs = []
    step = run.step
    def observe(dt, controls):
        inputs.append(controls)
        return step(dt, controls)
    monkeypatch.setattr(run, 'step', observe)
    player.key(pygame.K_d)
    player.screen.advance(1 / 60)
    player.key(pygame.K_d, False)
    assert inputs[0].firing and (inputs[0].aim_x, inputs[0].aim_y) == pytest.approx(click_world)
    assert len([shot for shot in run.projectiles if shot.friendly]) == 1
    player.screen.advance(1 / 60)
    assert not inputs[-1].firing


def test_scaled_fullscreen_logical_events_are_not_divided_by_desktop_dimensions(player_factory, monkeypatch):
    player = flight(player_factory)
    run = player.screen.expedition
    monkeypatch.setattr(pygame.display, 'get_window_size', lambda: (3440, 1440))
    monkeypatch.setattr(pygame.display, 'is_fullscreen', lambda: True)
    # This is SDL's logical event contract, not a physical/fullscreen smoke test.
    view = (1170, 510)
    view_event(player, view)
    assert player.screen._aim == pytest.approx(inverse_at(run, 1.5, view))
    for size in ((1280, 720), (3840, 2160), (1920, 1080)):
        surface = pygame.display.set_mode(size)
        player.screen.draw(surface)
        received = view_event(player, view)
        assert player.screen._aim == pytest.approx(inverse_at(run, 1.5, received))


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
@pytest.mark.parametrize('corner', [(WORLD_LEFT, WORLD_TOP), (WORLD_RIGHT, WORLD_TOP),
                                   (WORLD_LEFT, WORLD_BOTTOM), (WORLD_RIGHT, WORLD_BOTTOM)])
def test_reachable_arena_corners_stay_visible_and_drawing_preserves_model_save_rng(player_factory, zoom, corner):
    player = flight(player_factory)
    player.travel(*corner)
    zoom_to(player, zoom)
    screen, run = player.screen, player.screen.expedition
    assert (run.x, run.y) == pytest.approx(corner)
    state = copy.deepcopy((screen.campaign, run))
    rng = random.getstate()
    checkpoint = CampaignStore().path.read_bytes()
    for size in ((1280, 720), (1920, 1080), (3840, 2160)):
        screen.draw(pygame.display.set_mode(size))
        projected = screen._camera.world_to_screen((run.x, run.y))
        assert projected == pytest.approx(forward_at(run, zoom, corner))
        radius = 23 * zoom
        assert radius <= projected[0] <= 1920 - radius
        assert 145 + radius <= projected[1] <= 1020 - radius
    assert (screen.campaign, run) == state
    assert random.getstate() == rng
    assert CampaignStore().path.read_bytes() == checkpoint


def test_zoom_is_session_only_and_retained_between_trips(player_factory):
    player = flight(player_factory)
    zoom_to(player, 2)
    player.dock()
    saved = CampaignStore().path.read_bytes()
    player.key(pygame.K_HOME)
    player.events(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=-1))
    assert player.screen._camera.zoom == 2, 'Station controls must not change flight zoom'
    assert CampaignStore().path.read_bytes() == saved
    player.click('launch', sector=1)
    assert player.screen._camera.zoom == 2
    player.dock()
    player.click('title')
    player.click('continue')
    assert player.screen._camera.zoom == 1.5, 'Zoom is not a new persisted campaign field'


def test_integrated_offscreen_station_chip_clears_enlarged_rival(player_factory, monkeypatch):
    """Synthetic legal positions reproduce the pre-fix bottom-chip overlap."""
    import dtd.screens.campaign as presentation
    from dtd.campaign import Enemy
    player = flight(player_factory)
    screen, run = player.screen, player.screen.expedition
    run.x, run.y = 960, 190
    run.enemies = [Enemy(42, 960, 520)]
    zoom_to(player, 2)
    recorded = []
    original = presentation.draw_indicators
    def observe(surface, markers, *args):
        recorded.extend(markers)
        return original(surface, markers, *args)
    monkeypatch.setattr(presentation, 'draw_indicators', observe)
    before = copy.deepcopy(run)
    screen.draw(pygame.display.get_surface())
    station = next(marker for marker in recorded if marker.kind == 'station')
    ex, ey = forward_at(run, 2, (960, 520))
    hull = pygame.Rect(ex-58, ey-58, 116, 116)
    assert not hull.colliderect(station.bounds), 'Navigation chip covers enlarged live rival'
    assert station.distance == 560
    assert run == before
