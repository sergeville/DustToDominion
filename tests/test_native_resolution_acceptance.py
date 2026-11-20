"""Independent direct-raster and resize/input acceptance; no native-device claim."""
import copy
import random

import pygame
import pytest

from dtd.campaign_store import CampaignStore
from test_campaign_acceptance import player_factory
from test_camera_acceptance import forward_at, inverse_at, view_event, zoom_to


def start(player_factory, size=(2560, 1440)):
    player = player_factory('en-us', size)
    player.click('new_game')
    return player


@pytest.mark.parametrize('size', [(2560, 1440), (3840, 2160)])
@pytest.mark.parametrize('mode', ['mining', 'combat', 'station', 'fleet'])
def test_every_campaign_view_rasterizes_into_native_target_without_completed_scene_upscale(
        player_factory, monkeypatch, size, mode):
    player = start(player_factory, size)
    if mode in ('mining', 'combat'):
        if mode == 'combat':
            # Explicit synthetic unlock only for this draw-purity fixture.
            player.screen.campaign.lifetime_sales = 300
            player.screen._rebuild()
        player.click('launch', sector=2 if mode == 'combat' else 1)
        if mode == 'mining':
            rock = player.screen.expedition.asteroids[0]
            player.travel(rock.x+100, rock.y)
            player.key(pygame.K_SPACE)
            player.screen.advance(1/60)
        else:
            player.travel(750, 350)
    elif mode == 'fleet':
        player.click('view_fleet')
    screen = player.screen
    target = pygame.display.get_surface()
    state = copy.deepcopy((screen.campaign, screen.expedition))
    checkpoint = CampaignStore().path.read_bytes()
    rng = random.getstate()
    upscale = pygame.transform.smoothscale
    completed_upscales = []

    def observe(source, dimensions, *args, **kwargs):
        if source is screen._canvas and tuple(dimensions) != source.get_size():
            completed_upscales.append((source.get_size(), tuple(dimensions)))
        return upscale(source, dimensions, *args, **kwargs)

    monkeypatch.setattr(pygame.transform, 'smoothscale', observe)
    screen.draw(target)
    assert screen._canvas.get_size() == size
    assert not completed_upscales, 'A completed logical canvas was enlarged'
    assert (screen.campaign, screen.expedition) == state
    assert CampaignStore().path.read_bytes() == checkpoint
    assert random.getstate() == rng


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
def test_stationary_cursor_and_pending_click_keep_logical_meaning_across_native_backings(
        player_factory, monkeypatch, zoom):
    player = start(player_factory)
    player.click('launch', sector=1)
    player.travel(960, 400)
    zoom_to(player, zoom)
    run, screen = player.screen.expedition, player.screen
    view = forward_at(run, zoom, (run.x+150, run.y+35))
    received = view_event(player, view, pygame.MOUSEBUTTONDOWN)
    view_event(player, view, pygame.MOUSEBUTTONUP)
    click_world = inverse_at(run, zoom, received)
    # SDL delivers backing-space coordinates, even with a wider native window.
    monkeypatch.setattr(pygame.display, 'get_window_size', lambda: (3440, 1440))
    monkeypatch.setattr(pygame.display, 'is_fullscreen', lambda: True)
    observed = []
    step = run.step
    def observe(dt, controls):
        observed.append(controls)
        return step(dt, controls)
    monkeypatch.setattr(run, 'step', observe)
    for size in ((3840, 2160), (1920, 1080), (2560, 1440)):
        screen.draw(pygame.display.set_mode(size))
        assert screen._cursor == pytest.approx(received)
        player.key(pygame.K_d)
        screen.advance(1/60)
        player.key(pygame.K_d, False)
        assert screen._aim == pytest.approx(inverse_at(run, zoom, received))
    assert observed[0].firing
    assert (observed[0].aim_x, observed[0].aim_y) == pytest.approx(click_world)
    assert all(not controls.firing for controls in observed[1:])
    assert len([shot for shot in run.projectiles if shot.friendly]) == 1
    # New mouse events are transformed exactly once at each new surface size.
    received = view_event(player, (1100, 500))
    assert screen._aim == pytest.approx(inverse_at(run, zoom, received))


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
def test_native_ship_draw_uses_physical_target_and_projected_footprint(player_factory, monkeypatch, zoom):
    player = start(player_factory, (3840, 2160))
    player.click('launch', sector=1)
    player.travel(960, 400)
    zoom_to(player, zoom)
    screen, run = player.screen, player.screen.expedition
    target = pygame.display.get_surface()
    calls = []
    draw = screen._art.draw_ship
    def observe(surface, x, y, heading, *args, **kwargs):
        calls.append((surface, x, y, kwargs.get('size', 26)))
        return draw(surface, x, y, heading, *args, **kwargs)
    monkeypatch.setattr(screen._art, 'draw_ship', observe)
    screen.draw(target)
    projected = forward_at(run, zoom, (run.x, run.y))
    matches = [call for call in calls if abs(call[1]-projected[0]*2)<1 and abs(call[2]-projected[1]*2)<1]
    assert matches, 'Player was not drawn at native pixel coordinates'
    assert all(call[0].get_size() == (3840, 2160) for call in matches)
    assert any(call[3] == pytest.approx(32*zoom*2) for call in matches)


def test_large_world_art_retains_source_detail_and_caches_stay_bounded_on_resize(player_factory):
    player = start(player_factory)
    player.click('launch', sector=1)
    zoom_to(player, 2)
    screen = player.screen
    # Shipped station has detail beyond512px; retaining only a512 bitmap would
    # upscale source material even after eliminating the old scene framebuffer.
    assert max(screen._art._sources['station_v2'].get_size()) > 512
    for size in ((3840, 2160), (2560, 1440), (1920, 1080), (3840, 2160)):
        screen.draw(pygame.display.set_mode(size))
        cache = screen._art.cache_info
        assert cache['entries'] <= 128 and cache['bytes'] <= 32*1024*1024
        assert screen._canvas.get_size() == size
    assert screen._camera.zoom == 2


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
def test_actual_app_toggle_hook_settles_stale_sdl_motion_and_keeps_captured_click(
        player_factory, monkeypatch, zoom):
    from dtd.main import _pump_app_events
    player=start(player_factory,(1920,1080));player.click('launch',sector=1)
    player.travel(960,400);zoom_to(player,zoom)
    screen=player.screen;run=screen.expedition
    view_event(player,(1152,486),pygame.MOUSEBUTTONDOWN)
    view_event(player,(1152,486),pygame.MOUSEBUTTONUP)
    clicked=inverse_at(run,zoom,(1152,486))
    class Window:
        def on_f11(self):
            pygame.display.set_mode((2560,1440))
            return True
    # Observed Cocoa transition: stale event retains old x1152 while SDL's
    # current backing pointer subtracts the new440px pillarbox to give x712.
    monkeypatch.setattr(pygame.mouse,'get_pos',lambda:(712,486))
    assert not _pump_app_events(Window(),[pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F11)],screen)
    screen.update([pygame.event.Event(pygame.MOUSEMOTION,pos=(1152,486))])
    correct=(534,364.5)
    assert screen._cursor==pytest.approx(correct)
    assert screen._aim==pytest.approx(inverse_at(run,zoom,correct))
    observed=[];original=run.step
    def step(dt,controls):
        observed.append(controls);return original(dt,controls)
    monkeypatch.setattr(run,'step',step)
    screen.advance(1/60)
    assert observed[0].firing
    assert (observed[0].aim_x,observed[0].aim_y)==pytest.approx(clicked)
    # This is a bounded transition refresh, never perpetual polling that
    # overrides newer event coordinates or breaks event-driven input clients.
    received=view_event(player,(1100,500))
    assert screen._cursor==pytest.approx(received)
    assert screen._aim==pytest.approx(inverse_at(run,zoom,received))


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
def test_toggle_focus_loss_then_resume_keeps_stationary_pointer_correct(player_factory,monkeypatch,zoom):
    from dtd.main import _pump_app_events
    player=start(player_factory,(1920,1080));player.click('launch',sector=1)
    player.travel(960,400);zoom_to(player,zoom)
    screen=player.screen;run=screen.expedition
    view_event(player,(1152,486))
    class Window:
        def on_f11(self):
            pygame.display.set_mode((2560,1440));return True
    monkeypatch.setattr(pygame.mouse,'get_pos',lambda:(712,486))
    _pump_app_events(Window(),[pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F11)],screen)
    screen.update([pygame.event.Event(pygame.WINDOWFOCUSLOST),
                   pygame.event.Event(pygame.MOUSEMOTION,pos=(1152,486))])
    assert screen.mode=='paused'
    player.key(pygame.K_ESCAPE)
    assert screen.mode=='flight'
    assert screen._cursor==pytest.approx((534,364.5))
    assert screen._aim==pytest.approx(inverse_at(run,zoom,(534,364.5)))
