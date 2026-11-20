"""Player-input acceptance paths with shipped resources and isolated saves.

The client inspects button labels/rectangles and observed flight state, but all
gameplay changes originate from pygame events. No action callback, cargo,
credit, position or progression state is injected.
"""
from pathlib import Path
from types import SimpleNamespace

import pygame
import pytest

from dtd import main
from dtd.campaign import STATION_X, STATION_Y
from dtd.campaign_store import CampaignStore
from dtd.language import get_language_manager, init_language_manager
from dtd.resource_loader import ResourceLoader
from dtd.screens.base import ScreenAction
from dtd.screens.campaign import CampaignScreen
from dtd.screens.title import TitleScreen
from dtd.ui import Theme, current_scale


class PlayerClient:
    def __init__(self, loader):
        self.loader = loader
        self.screen = self.fresh_title()

    def theme(self):
        return Theme("default", "", self.loader)

    def fresh_title(self):
        return TitleScreen(self.theme(), self.loader)

    def text(self, key, **values):
        return get_language_manager().get_string("campaign." + key).format(**values)

    def events(self, *events):
        for event in events:
            pygame.event.post(event)
        batch = pygame.event.get()
        self.screen.update(batch)
        action = self.screen.handle(batch)
        if action is ScreenAction.SHOW_CAMPAIGN:
            title = self.screen
            self.screen = CampaignScreen(self.theme(), self.loader, title.campaign, title.store)
        elif action is ScreenAction.SHOW_TITLE_SCREEN:
            self.screen = self.fresh_title()
        else:
            assert action is None

    def click(self, key, **values):
        label = self.text(key, **values)
        buttons = [button for button in self.screen._ui.widgets if button.text == label]
        assert len(buttons) == 1, label
        button = buttons[0]
        assert button.enabled, label
        pos = current_scale().rect(*button.rect).center
        self.events(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
        self.events(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))
        self.screen.draw(pygame.display.get_surface())

    def key(self, key, pressed=True):
        self.events(pygame.event.Event(pygame.KEYDOWN if pressed else pygame.KEYUP, key=key))

    def diagnostic(self):
        run = self.screen.expedition
        campaign = self.screen.campaign
        return (f"mode={self.screen.mode}, credits={campaign.credits}, "
                f"sales={campaign.lifetime_sales}, cargo={campaign.cargo}, "
                f"flight={None if run is None else (run.x, run.y, run.hull, len(run.cargo), len(run.enemies))}")

    def travel(self, x, y):
        # Cardinal movement is five logical units per fixed frame. Observe the
        # target until reached; never set the ship position or model inputs.
        for axis, target, negative, positive in (
            ("x", x, pygame.K_a, pygame.K_d),
            ("y", y, pygame.K_w, pygame.K_s),
        ):
            start = getattr(self.screen.expedition, axis)
            direction = positive if target > start else negative
            self.key(direction)
            for _ in range(500):
                if abs(getattr(self.screen.expedition, axis) - target) <= 2.5:
                    break
                self.screen.advance(1 / 60)
                assert self.screen.mode == "flight", self.diagnostic()
            else:
                pytest.fail(f"Ship did not reach {axis}={target}: {self.diagnostic()}")
            self.key(direction, False)

    def mine_one_rock(self):
        run = self.screen.expedition
        rock = run.asteroids[0]
        self.travel(rock.x, rock.y)
        before = len(run.cargo)
        self.key(pygame.K_SPACE)
        for _ in range(180):
            self.screen.advance(1 / 60)
            if rock not in run.asteroids and len(run.cargo) == before + 3:
                break
        else:
            pytest.fail(f"Mining did not destroy/collect rock {rock.id}: {self.diagnostic()}")
        self.key(pygame.K_SPACE, False)
        assert not run.pickups
        return before + 3

    def dock(self):
        self.travel(STATION_X, STATION_Y)
        self.key(pygame.K_e)
        assert self.screen.mode == "result", self.diagnostic()
        self.click("continue")
        assert self.screen.mode == "station"

    def mine_and_sell_sortie(self):
        before = self.screen.campaign.credits
        self.click("launch", sector=1)
        # Six rocks is the entire safe sector; this bound also prevents a
        # broken pickup/cargo condition from hanging full-campaign acceptance.
        for _ in range(6):
            run = self.screen.expedition
            if not run.asteroids or len(run.cargo) >= self.screen.campaign.capacity:
                break
            self.mine_one_rock()
        assert self.screen.expedition.cargo, self.diagnostic()
        self.dock()
        self.click("sell", value=self.screen.campaign.cargo_value())
        assert self.screen.campaign.credits > before, self.diagnostic()

    def purchase(self, item):
        self.click("purchase", item=self.text(item), price=self.screen.campaign.price(item))

    def aim(self, x, y, pressed=None):
        factor = current_scale().scale
        pos = (int(x * factor), int(y * factor))
        self.events(pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0)))
        if pressed is not None:
            self.events(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN if pressed else pygame.MOUSEBUTTONUP,
                pos=pos, button=1))


@pytest.fixture
def player_factory(monkeypatch, silent_audio_manager, bootstrapped_persistence):
    monkeypatch.chdir(Path(__file__).parents[1])
    pygame.init()

    def create(locale="en-us", size=(1280, 720)):
        pygame.display.set_mode(size)
        loader = ResourceLoader()
        loader.load(None)
        init_language_manager(loader, locale)
        pygame.event.clear()
        return PlayerClient(loader)

    return create


@pytest.mark.parametrize("locale,size", [("en-us", (1280, 720)), ("de", (1920, 1080))])
def test_title_mine_trade_upgrade_and_continue_through_player_events(player_factory, locale, size):
    player = player_factory(locale, size)
    player.click("new_game")
    assert isinstance(player.screen, CampaignScreen)
    store = CampaignStore()
    assert store.load().credits == 80

    player.click("launch", sector=1)
    assert player.mine_one_rock() == 3
    assert store.load().cargo == []  # In-flight ore is not a checkpoint.
    player.travel(STATION_X, STATION_Y)
    player.key(pygame.K_e)
    assert player.screen.mode == "result"
    assert store.load().cargo == [0, 0, 0]

    player.click("continue")
    player.click("sell", value=30)
    assert player.screen.campaign.credits == 110
    player.click("purchase", item=player.text("cargo"), price=100)
    assert player.screen.campaign.capacity == 18
    assert player.screen.campaign.credits == 10
    expected = player.screen.campaign.to_dict()
    assert expected["lifetime_sales"] == 30
    assert store.load().to_dict() == expected

    player.click("save")
    saved_bytes = store.path.read_bytes()
    player.click("title")
    assert isinstance(player.screen, TitleScreen)
    player.click("continue")
    assert isinstance(player.screen, CampaignScreen)
    assert player.screen.mode == "station"
    assert player.screen.campaign.to_dict() == expected
    assert store.path.read_bytes() == saved_bytes


def test_window_close_mid_expedition_then_fresh_continue_uses_station_checkpoint(player_factory):
    player = player_factory()
    player.click("new_game")
    store = CampaignStore()
    saved_bytes = store.path.read_bytes()
    checkpoint = store.load().to_dict()
    player.click("launch", sector=1)
    assert player.mine_one_rock() == 3
    player.key(pygame.K_ESCAPE)
    assert player.screen.mode == "paused"

    # The production main loop, rather than a test substitute for its close
    # handling, receives the window event and exits without writing the flight.
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    main._run_event_loop(SimpleNamespace(), player.screen, player.loader)
    assert store.path.read_bytes() == saved_bytes

    restarted = player_factory()
    restarted.click("continue")
    assert restarted.screen.campaign.to_dict() == checkpoint
    assert restarted.screen.campaign.cargo == []
    assert restarted.screen.mode == "station"
    assert store.path.read_bytes() == saved_bytes


def test_full_victory_from_new_game_through_mined_and_purchased_progress(player_factory):
    player = player_factory()
    player.click("new_game")
    sorties = 0
    # Every credit is earned in the flight UI, then sold through Dock Services.
    # Upgrade twice, hire both crew, and acquire the two support ships using
    # their real button prices; neither progress nor unlocked sectors is seeded.
    for item in ("cargo", "cargo", "laser", "laser", "miner", "ship", "ship", "engineer"):
        for _ in range(10):
            if player.screen.campaign.credits >= player.screen.campaign.price(item):
                break
            player.mine_and_sell_sortie()
            sorties += 1
        else:
            pytest.fail(f"Could not afford {item}: {player.diagnostic()}")
        player.purchase(item)

    for _ in range(20):
        if player.screen.mode == "victory":
            break
        player.mine_and_sell_sortie()
        sorties += 1
    else:
        pytest.fail(f"Victory panel never appeared after {sorties} sorties: {player.diagnostic()}")

    campaign = player.screen.campaign
    assert campaign.won and campaign.ship_count == 3
    assert campaign.miner and campaign.engineer and campaign.credits >= 1200
    assert campaign.unlocked_sector == 3
    expected = campaign.to_dict()
    assert CampaignStore().load().to_dict() == expected
    player.click("continue")
    assert player.screen.mode == "station"
    player.click("title")
    player.click("continue")
    assert player.screen.mode == "station"
    assert player.screen.campaign.to_dict() == expected
    # The ending is latched and the completed campaign remains playable.
    player.click("launch", sector=1)
    assert player.screen.mode == "flight" and player.screen.campaign.won


def test_earned_unlock_mouse_combat_docking_and_one_bounty(player_factory):
    player = player_factory()
    player.click("new_game")
    player.mine_and_sell_sortie()  # 120 sold; 200 banked.
    player.purchase("cargo")
    player.mine_and_sell_sortie()  # 180 more sold unlocks the fringe.
    assert player.screen.campaign.lifetime_sales == 300
    assert player.screen.campaign.unlocked_sector == 2
    player.purchase("laser")
    banked = player.screen.campaign.credits
    player.click("launch", sector=2)
    run = player.screen.expedition
    assert len(run.enemies) == 1
    player.travel(350, 540)  # Leave the station shield and enter weapon range.
    enemy = run.enemies[0]
    player.aim(enemy.x, enemy.y, pressed=True)
    for _ in range(300):
        if not run.enemies:
            break
        enemy = run.enemies[0]
        player.aim(enemy.x, enemy.y)
        player.screen.advance(1 / 60)
        assert player.screen.mode == "flight", f"Defeated before rival: {player.diagnostic()}"
    else:
        pytest.fail(f"Rival survived five seconds of aimed fire: {player.diagnostic()}")
    player.aim(enemy.x, enemy.y, pressed=False)
    assert run.bounty == 70 and run.hull > 0
    assert player.screen.campaign.credits == banked
    player.dock()
    assert player.screen.campaign.credits == banked + 70
    assert CampaignStore().load().credits == banked + 70
    player.click("title")
    player.click("continue")
    assert player.screen.campaign.credits == banked + 70
    # Repeated dock/continue cannot award the completed expedition again.
    player.click("launch", sector=1)
    player.dock()
    assert player.screen.campaign.credits == banked + 70
