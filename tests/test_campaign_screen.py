"""Campaign UI integration boundaries: time, input, recovery and checkpoints."""
import json
from pathlib import Path

import pygame
import pytest

from dtd.campaign import Campaign, STATION_X, STATION_Y, LAUNCH_Y
from dtd.campaign_store import CampaignStore, SaveError
from dtd.language import init_language_manager
from dtd.resource_loader import ResourceLoader
from dtd.screens.base import ScreenAction
from dtd.screens.campaign import CampaignScreen
from dtd.ui import Theme


class LocaleLoader(ResourceLoader):
    def get_json_resource(self, resource_id):
        if resource_id.startswith('languages/'):
            return json.loads((Path(__file__).parents[1] / 'resources' / resource_id).read_text())
        return None


@pytest.fixture
def screen(tmp_path, silent_audio_manager):
    pygame.init()
    pygame.display.set_mode((1280, 720))
    loader = LocaleLoader()
    init_language_manager(loader)
    return CampaignScreen(Theme('', '', loader), loader, Campaign(), CampaignStore(tmp_path / 'campaign.json'))


def key(keycode, up=False):
    return pygame.event.Event(pygame.KEYUP if up else pygame.KEYDOWN, key=keycode)


def test_focus_pause_freezes_world_and_resets_input(screen):
    screen._launch(1)
    screen.update([key(pygame.K_w)])
    screen.advance(.1)
    y = screen.expedition.y
    screen.update([pygame.event.Event(pygame.WINDOWFOCUSLOST)])
    screen.advance(20)
    assert screen.mode == 'paused'
    assert screen.expedition.y == y
    screen._resume()
    screen.advance(.1)
    assert screen.expedition.y == y


def test_elapsed_time_is_bounded_and_nonfinite_ignored(screen):
    screen._launch(1)
    screen.update([key(pygame.K_w)])
    screen.advance(float('nan'))
    screen.advance(-1)
    assert screen.expedition.y == LAUNCH_Y
    screen.advance(999)
    bounded_y = screen.expedition.y
    other = Campaign().launch(1)
    from dtd.campaign import InputState
    other.step(.25, InputState(move_y=-1))
    assert bounded_y == pytest.approx(other.y)


def test_dock_sells_then_checkpoint_restores_progress(screen):
    screen._launch(1)
    screen.expedition.cargo = [0, 0]
    screen.expedition.x, screen.expedition.y = STATION_X, STATION_Y
    screen.update([key(pygame.K_e)])
    assert screen.mode == 'result'
    assert screen.store.load().cargo == [0, 0]
    screen._station()
    screen._station_action('sell')
    assert screen.campaign.credits == 100
    assert screen.store.load().credits == 100
    screen._station_action('cargo')
    assert screen.store.load().capacity == 18


def test_abandon_requires_confirmation_and_restores_recoverable_hull(screen):
    screen._launch(1)
    screen.expedition.cargo = [0]
    screen.update([key(pygame.K_ESCAPE)])
    assert screen.mode == 'paused' and screen.expedition.cargo == [0]
    screen._confirm_abandon()
    assert screen.mode == 'abandon' and screen.expedition is not None
    screen._abandon()
    assert screen.mode == 'result'
    assert screen.campaign.cargo == []
    assert screen.store.load().hull == screen.campaign.max_hull / 2


def test_save_error_prevents_title_transition_and_preserves_session(screen, monkeypatch):
    def fail(campaign):
        raise SaveError('disk full')
    monkeypatch.setattr(screen.store, 'save', fail)
    screen._title()
    assert screen.error
    assert screen.handle([]) is None
    assert screen.campaign.credits == 80


def test_successful_title_transition_saves(screen):
    screen._title()
    assert screen.handle([]) is ScreenAction.SHOW_TITLE_SCREEN
    assert screen.store.load().credits == 80


def test_victory_is_visible_and_continue_keeps_campaign(screen):
    screen.campaign.support_ships = 2
    screen.campaign.miner = screen.campaign.engineer = True
    screen.campaign.credits = 1190
    screen.campaign.cargo = [0]
    screen._station_action('sell')
    assert screen.mode == 'victory'
    assert screen.store.load().won
    screen._station()
    assert screen.campaign.victory and screen.mode == 'station'


def test_overlay_consumes_click_and_does_not_fire_on_resume(screen):
    screen._launch(1)
    screen._pause()
    # Click Resume in physical 1280x720 coordinates; trailing key/fire events
    # belong to the old overlay and must not reach the resumed expedition.
    screen.update([pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(600, 420), button=1)])
    screen.update([pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(600, 420), button=1),
                   key(pygame.K_w),
                   pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(800, 350), button=1)])
    assert screen.mode == 'flight'
    assert not screen._keys and not screen._firing


@pytest.mark.parametrize('mode', ['station', 'flight', 'paused', 'abandon', 'result', 'victory', 'fleet'])
def test_all_surfaces_render_with_both_locales(screen, mode):
    for locale in ('en-us', 'de'):
        init_language_manager(screen._loader, locale)
        if mode in ('flight', 'paused', 'abandon') and screen.expedition is None:
            screen._launch(1)
        screen.mode = mode
        screen._rebuild()
        for size in ((1280, 720), (1920, 1080), (2560, 1440)):
            target = pygame.display.set_mode(size)
            screen.draw(target)
            assert target.get_at((0, 0))[:3] != (0, 0, 0)


def test_bounty_can_trigger_victory_on_docking(screen):
    screen.campaign.support_ships = 2
    screen.campaign.miner = screen.campaign.engineer = True
    screen.campaign.credits = 1190
    screen._launch(1)
    screen.expedition.bounty = 20
    screen.expedition.x, screen.expedition.y = STATION_X, STATION_Y
    screen.update([key(pygame.K_e)])
    assert screen.mode == 'victory'
    assert screen.store.load().won


def test_focus_loss_after_resume_click_in_same_batch_stays_paused(screen):
    screen._launch(1)
    screen._pause()
    screen.update([pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(600, 420), button=1)])
    screen.update([pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(600, 420), button=1),
                   pygame.event.Event(pygame.WINDOWFOCUSLOST)])
    assert screen.mode == 'paused'
    assert not screen._keys and not screen._firing


@pytest.mark.parametrize('size', [(1280, 720), (1920, 1080), (2560, 1440)])
def test_fleet_is_read_only_and_returns_by_back_or_escape(screen, size):
    pygame.display.set_mode(size)
    screen.campaign.credits = 3000
    screen._rebuild()
    original = screen.campaign.to_dict()

    def click(button):
        point = tuple(round(v * size[0] / 1920) for v in button.rect.center)
        screen.update([pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=point, button=1)])
        screen.update([pygame.event.Event(pygame.MOUSEBUTTONUP, pos=point, button=1)])

    underlying_purchase = screen._ui.widgets[8]
    click(screen._ui.widgets[-1])
    assert screen.mode == 'fleet'
    click(underlying_purchase)
    screen.advance(100)
    assert screen.mode == 'fleet' and screen.campaign.to_dict() == original
    click(screen._ui.widgets[0])
    assert screen.mode == 'station'
    click(screen._ui.widgets[-1])
    screen.update([key(pygame.K_ESCAPE)])
    assert screen.mode == 'station' and screen.campaign.to_dict() == original


@pytest.mark.parametrize('supports,bonus', [(0, 0), (1, 10), (2, 30)])
def test_fleet_shows_actual_ownership_and_total_bonus(screen, supports, bonus, monkeypatch):
    screen.campaign.support_ships = supports
    screen._fleet()
    drawn = []
    monkeypatch.setattr(screen, '_text', lambda text, *args, **kwargs: drawn.append(text))
    screen._draw_fleet()
    assert drawn.count(screen._t('fleet_owned')) == supports + 1
    assert drawn.count(screen._t('fleet_available')) == 2 - supports
    assert screen._t('fleet_total', bonus=bonus) in drawn
    assert screen._t('support_benefit', bonus=10) in drawn
    assert screen._t('support_benefit', bonus=20) in drawn
    assert screen._t('fleet_passive') in drawn


def test_safe_zone_has_visible_weapons_lock_hint(screen, monkeypatch):
    from dtd.campaign import SAFE_RADIUS
    screen._launch(1)
    drawn = []
    monkeypatch.setattr(screen, '_text', lambda text, *args, **kwargs: drawn.append(text))
    screen._draw_flight()
    assert screen._t('weapons_locked') in drawn
    drawn.clear()
    screen.expedition.x = STATION_X + SAFE_RADIUS + 1
    screen._draw_flight()
    assert screen._t('weapons_locked') not in drawn


def test_visual_time_follows_consumed_steps_and_freezes_on_pause(screen):
    screen._launch(1)
    screen.advance(.1)
    phase = screen._visual_time
    assert phase == pytest.approx(.1)
    import copy
    before = copy.deepcopy(screen.expedition)
    screen.draw(pygame.display.get_surface())
    screen.draw(pygame.display.get_surface())
    assert screen._visual_time == phase
    assert screen.expedition == before
    screen._pause()
    screen.advance(5)
    assert screen._visual_time == phase
    screen._resume()
    screen.advance(1 / 60)
    assert screen._visual_time == pytest.approx(phase + 1 / 60)


def test_thrust_uses_net_input_and_stops_on_focus_loss(screen, monkeypatch):
    calls = []
    monkeypatch.setattr(screen._art, 'draw_ship', lambda *args, **kwargs: calls.append(kwargs))
    screen._launch(1)
    screen.update([key(pygame.K_w), key(pygame.K_s)])
    screen._draw_flight()
    assert not calls[-1]['thrust']
    screen.update([key(pygame.K_s, up=True)])
    screen._draw_flight()
    assert calls[-1]['thrust']
    screen.update([pygame.event.Event(pygame.WINDOWFOCUSLOST)])
    screen._draw_flight()
    assert not calls[-1]['thrust']


def test_actual_mining_target_feedback_is_independent_of_pickup_guidance(screen, monkeypatch):
    from dtd.campaign import Asteroid, Pickup
    screen._launch(1)
    run = screen.expedition
    run.x, run.y = 700, 500
    run.asteroids = [Asteroid(2, 800, 500, 40, 0), Asteroid(1, 600, 500, 40, 0, 1, 3)]
    run.pickups = [Pickup(1, 720, 520, 0)]
    drawn = []
    monkeypatch.setattr(screen, '_text', lambda text, *args, **kwargs: drawn.append(text))
    screen._draw_flight()
    assert screen._t('guide_collect') in drawn
    assert screen._t('cut_progress', value=67) in drawn
    run.cargo = [0] * screen.campaign.capacity
    drawn.clear()
    screen._draw_flight()
    assert screen._t('guide_return_full') in drawn
    assert not any(text.startswith('CUT ') for text in drawn)


def test_fresh_launch_guidance_invites_mining_in_both_languages(screen, monkeypatch):
    screen._launch(1)
    drawn = []
    monkeypatch.setattr(screen, '_text', lambda text, *args, **kwargs: drawn.append(text))
    for locale in ('en-us', 'de'):
        init_language_manager(screen._loader, locale)
        drawn.clear()
        screen._draw_flight()
        assert screen._t('guide_approach') in drawn
        assert screen._t('guide_dock') not in drawn
        assert not any('campaign.' in text for text in drawn)


def test_guidance_stays_in_header_and_does_not_cover_reachable_ship(screen, monkeypatch):
    from dtd.campaign import WORLD_TOP
    screen._launch(1)
    screen.expedition.y = 935
    panels, text = [], []
    monkeypatch.setattr(screen, '_panel', lambda rect: panels.append(pygame.Rect(rect)))
    monkeypatch.setattr(screen, '_text', lambda value, x, y, size=28, *args, **kwargs: text.append((value, y, size)))
    screen._draw_flight()
    ship = pygame.Rect(928, 903, 64, 64)
    assert not any(panel.colliderect(ship) for panel in panels)
    advice = [item for item in text if item[0] == screen._t('guide_approach')]
    assert advice and advice[0][1] + advice[0][2] < WORLD_TOP


def test_player_label_expires_on_simulated_time_and_resets_on_launch(screen, monkeypatch):
    drawn = []
    monkeypatch.setattr(screen, '_text', lambda text, *args, **kwargs: drawn.append(text))
    screen._launch(1)
    screen._draw_flight()
    assert screen._t('player_label') in drawn
    for _ in range(25):
        screen.advance(.25)
    drawn.clear()
    screen._draw_flight()
    assert screen._t('player_label') not in drawn
    screen.expedition.x, screen.expedition.y = STATION_X, STATION_Y
    screen.update([key(pygame.K_e)])
    screen._station()
    screen._launch(1)
    drawn.clear()
    screen._draw_flight()
    assert screen._t('player_label') in drawn


@pytest.mark.parametrize('locale', ['en-us', 'de'])
@pytest.mark.parametrize('point', [(40, 190), (1880, 190), (40, 970), (1880, 970)])
def test_hud_and_local_labels_leave_corner_ships_visible(screen, monkeypatch, point, locale):
    from dtd.campaign import SAFE_RADIUS
    screen._launch(1)
    init_language_manager(screen._loader, locale)
    screen.expedition.x, screen.expedition.y = point
    panels, labels = [], []
    original_text = screen._text
    monkeypatch.setattr(screen, '_panel', lambda rect: panels.append(pygame.Rect(rect)))
    def record(text, x, y, size=28, *args, **kwargs):
        labels.append(pygame.Rect(x, y, *screen._theme.get_font(size).size(text)))
        original_text(text, x, y, size, *args, **kwargs)
    monkeypatch.setattr(screen, '_text', record)
    screen._draw_flight()
    ship = pygame.Rect(point[0] - 37, point[1] - 37, 74, 74)
    assert pygame.Rect(0, 0, 1920, 1080).contains(ship)
    assert not any(panel.colliderect(ship) for panel in panels)
    station = pygame.Rect(STATION_X - SAFE_RADIUS, STATION_Y - SAFE_RADIUS,
                          SAFE_RADIUS * 2, SAFE_RADIUS * 2)
    assert not any(panel.colliderect(station) for panel in panels)
    assert all(pygame.Rect(0, 0, 1920, 1080).contains(rect) for rect in labels)


def test_ore_brackets_surround_rock_and_return_brackets_surround_dock(screen, monkeypatch):
    from dtd.campaign import DOCK_RADIUS
    from dtd.campaign_guidance import guidance
    screen._launch(1)
    calls = []
    monkeypatch.setattr(screen, '_brackets', lambda *args: calls.append(args))
    advice = guidance(screen.campaign, screen.expedition)
    rock = next(r for r in screen.expedition.asteroids if r.id == advice.target_id)
    screen._draw_guidance()
    x, y, radius, color = calls[-1]
    assert (x, y) == (rock.x, rock.y) and radius > rock.radius
    screen.expedition.cargo = [0] * screen.campaign.capacity
    screen._draw_guidance()
    x, y, radius, color = calls[-1]
    assert (x, y) == (STATION_X, STATION_Y) and radius > DOCK_RADIUS


def test_bottom_edge_player_label_does_not_overlap_direction_arrow(screen, monkeypatch):
    from dtd.campaign import WORLD_BOTTOM
    from dtd.campaign_guidance import guidance
    screen._launch(1)
    screen.expedition.y = WORLD_BOTTOM
    labels = []
    monkeypatch.setattr(screen, '_flight_label',
                        lambda text, x, y, color: labels.append(
                            pygame.Rect(x, y, *screen._theme.get_font(20).size(text))))
    screen._draw_player_label()
    assert len(labels) == 1
    for point in screen._direction_points(guidance(screen.campaign, screen.expedition)):
        assert not labels[0].inflate(12, 6).collidepoint(point)


@pytest.mark.parametrize('split_updates', [False, True])
@pytest.mark.parametrize('size', [(1280, 720), (1920, 1080), (2560, 1440)])
def test_quick_fire_click_survives_release_before_simulation_tick(screen, split_updates, size):
    pygame.display.set_mode(size)
    screen._launch(1)
    run = screen.expedition
    run.x, run.y = 600, 300  # Well outside the station shield.
    point = (round(900 * size[0] / 1920), round(300 * size[1] / 1080))
    down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=point, button=1)
    up = pygame.event.Event(pygame.MOUSEBUTTONUP, pos=point, button=1)
    if split_updates:
        screen.update([down])
        screen.advance(1 / 240)  # No fixed simulation tick yet.
        screen.update([up])
    else:
        screen.update([down, up])
    screen.advance(1 / 60)
    assert len(run.projectiles) == 1
    assert run.projectiles[0].friendly and run.projectiles[0].vx > 0
    screen.advance(.25)
    assert len(run.projectiles) == 1  # A tap must not become held autofire.


def fire_click(screen, held=False):
    events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(600, 200), button=1)]
    if not held:
        events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(600, 200), button=1))
    screen.update(events)


def test_held_fire_repeats_at_cooldown_and_release_stops(screen):
    screen._launch(1)
    screen.expedition.x, screen.expedition.y = 600, 300
    fire_click(screen, held=True)
    screen.advance(.25)
    assert len(screen.expedition.projectiles) == 2
    screen.update([pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(600, 200), button=1)])
    screen.advance(.25)
    assert len(screen.expedition.projectiles) == 2


def test_click_during_cooldown_does_not_fire_later_or_bypass_limit(screen):
    screen._launch(1)
    screen.expedition.x, screen.expedition.y = 600, 300
    fire_click(screen)
    screen.advance(1 / 60)
    fire_click(screen)
    screen.advance(1 / 60)
    screen.advance(.25)
    assert len(screen.expedition.projectiles) == 1


def test_click_blocked_by_shield_is_not_carried_outside(screen):
    screen._launch(1)
    fire_click(screen)
    screen.advance(1 / 60)
    assert not screen.expedition.projectiles
    screen.expedition.x, screen.expedition.y = 600, 300
    screen.advance(.25)
    assert not screen.expedition.projectiles


@pytest.mark.parametrize('event', [pygame.event.Event(pygame.WINDOWFOCUSLOST),
                                   key(pygame.K_ESCAPE)])
def test_pending_click_is_cleared_by_pause_or_focus_loss(screen, event):
    screen._launch(1)
    screen.expedition.x, screen.expedition.y = 600, 300
    fire_click(screen)
    screen.update([event])
    assert screen.mode == 'paused'
    screen._resume()
    screen.advance(.25)
    assert not screen.expedition.projectiles


def test_released_click_uses_click_aim_after_mouse_moves(screen):
    screen._launch(1)
    screen.expedition.x, screen.expedition.y = 600, 300
    fire_click(screen)
    screen.update([pygame.event.Event(pygame.MOUSEMOTION, pos=(400, 400))])
    screen.advance(1 / 60)
    shot = screen.expedition.projectiles[0]
    assert shot.vx > 0 and shot.vy == pytest.approx(0)
