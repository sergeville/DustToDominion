"""Campaign UI integration boundaries: time, input, recovery and checkpoints."""
import json
from pathlib import Path

import pygame
import pytest

from dtd.campaign import Campaign, STATION_X, STATION_Y
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
    assert screen.expedition.y == STATION_Y
    screen.advance(999)
    bounded_y = screen.expedition.y
    other = Campaign().launch(1)
    from dtd.campaign import InputState
    other.step(.25, InputState(move_y=-1))
    assert bounded_y == pytest.approx(other.y)


def test_dock_sells_then_checkpoint_restores_progress(screen):
    screen._launch(1)
    screen.expedition.cargo = [0, 0]
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
