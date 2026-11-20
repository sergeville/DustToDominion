"""Independent event, lifecycle and silent-device acceptance for spec 22.

Earned cases never seed progression. Explicit synthetic edge cases isolate
same-step shot consumption and movement boundaries. No physical audio claim.
"""
from pathlib import Path
from types import SimpleNamespace

import pygame
import pytest

from dtd import audio, game_config, main
from dtd.campaign import Enemy, Projectile, WORLD_LEFT
from dtd.campaign_store import CampaignStore
from dtd.language import init_language_manager
from dtd.resource_loader import ResourceLoader
from dtd.game_config import AudioConfig
from test_campaign_acceptance import PlayerClient
from test_camera_acceptance import zoom_to


PREFIX = 'audio/campaign/'


def sound(name):
    return PREFIX + name + '.wav'


@pytest.fixture
def audible_player(monkeypatch, bootstrapped_persistence):
    monkeypatch.chdir(Path(__file__).parents[1])
    pygame.init()
    pygame.display.set_mode((1920, 1080))
    loader = ResourceLoader()
    loader.load(None)
    audio.init_audio_manager(loader, None)
    manager = audio.get_audio_manager()
    init_language_manager(loader, 'en-us')
    calls = []
    original = manager.play_game_sfx

    def observe(resource_id):
        calls.append(resource_id)
        return original(resource_id)

    monkeypatch.setattr(manager, 'play_game_sfx', observe)
    player = PlayerClient(loader)
    player.click('new_game')
    return player, manager, calls


def active(manager):
    return manager._loops.active_ids()


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
@pytest.mark.parametrize('pause_event', ['escape', 'focus'])
def test_movement_loop_stops_on_pause_and_requires_fresh_resume_input(audible_player, zoom, pause_event):
    player, manager, calls = audible_player
    player.click('launch', sector=1)
    zoom_to(player, zoom)
    player.key(pygame.K_d)
    player.screen.advance(1 / 60)
    assert sound('thrust_loop') in active(manager)
    if pause_event == 'escape':
        player.key(pygame.K_ESCAPE)
    else:
        player.events(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert player.screen.mode == 'paused' and not active(manager)
    prior = list(calls)
    player.screen.advance(.25)
    assert calls == prior
    player.click('resume')
    player.screen.advance(1 / 60)
    assert not active(manager)
    player.key(pygame.K_d)
    player.screen.advance(1 / 60)
    assert active(manager) == {sound('thrust_loop')}
    player.key(pygame.K_d, False)
    player.screen.advance(1 / 60)
    assert not active(manager)


def test_mining_loop_requires_real_contact_and_stops_when_released(audible_player):
    player, manager, calls = audible_player
    player.click('launch', sector=1)
    player.key(pygame.K_SPACE)
    player.screen.advance(1 / 60)
    assert sound('mining_loop') not in active(manager)
    player.key(pygame.K_SPACE, False)
    rock = player.screen.expedition.asteroids[0]
    player.travel(rock.x + 100, rock.y)
    player.key(pygame.K_SPACE)
    player.screen.advance(1 / 60)
    assert rock.health == 2
    assert sound('mining_loop') in active(manager)
    player.key(pygame.K_SPACE, False)
    player.screen.advance(1 / 60)
    assert sound('mining_loop') not in active(manager)


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
def test_quick_click_sound_only_for_accepted_shot_at_each_zoom(audible_player, zoom):
    player, manager, calls = audible_player
    player.click('launch', sector=1)
    zoom_to(player, zoom)
    run = player.screen.expedition
    player.aim(run.x + 50, run.y, pressed=True)
    player.aim(run.x + 50, run.y, pressed=False)
    player.screen.advance(1 / 60)
    assert calls.count(sound('weapon')) == 0
    player.travel(750, 350)
    player.aim(run.x + 120, run.y + 30, pressed=True)
    player.aim(run.x + 120, run.y + 30, pressed=False)
    player.screen.advance(1 / 60)
    assert len(run.projectiles) == 1
    assert calls.count(sound('weapon')) == 1
    player.aim(run.x + 120, run.y + 30, pressed=True)
    player.aim(run.x + 120, run.y + 30, pressed=False)
    player.screen.advance(1 / 60)
    assert calls.count(sound('weapon')) == 1  # Rejected cooldown attempt.


def test_same_step_fired_and_destroyed_enemy_still_produces_weapon_cue(audible_player):
    player, manager, calls = audible_player
    player.click('launch', sector=1)
    player.travel(750, 350)
    run = player.screen.expedition
    # Synthetic contact fixture: enemy fires before an existing shot kills it.
    enemy = Enemy(99, run.x + 15, run.y, hull=1, cooldown=0)
    run.enemies = [enemy]
    run.projectiles = [Projectile(enemy.x, enemy.y, 0, 0, 2, True)]
    calls.clear()
    player.screen.advance(1 / 60)
    assert not run.enemies and not run.projectiles
    assert run.hull < 100 and enemy.cooldown > 1
    assert calls.count(sound('weapon')) == 1
    assert calls.count(sound('impact')) == 1
    assert calls.count(sound('destruction')) == 1


def test_holding_into_world_boundary_does_not_play_thrust(audible_player):
    player, manager, calls = audible_player
    player.click('launch', sector=1)
    player.travel(WORLD_LEFT, 350)
    player.key(pygame.K_a)
    player.screen.advance(1 / 60)
    assert player.screen.expedition.x == WORLD_LEFT
    assert sound('thrust_loop') not in active(manager)


def test_earned_trip_dock_sell_and_reload_preserve_save_schema(audible_player):
    player, manager, calls = audible_player
    before_keys = set(player.screen.campaign.to_dict())
    player.click('launch', sector=1)
    player.key(pygame.K_e)  # Launch position is outside docking range.
    assert calls.count(sound('docking')) == 0
    assert player.mine_one_rock() == 3
    assert sound('ore_pickup') in calls and sound('destruction') in calls
    player.dock()
    assert not active(manager)
    assert calls.count(sound('docking')) == 1
    player.click('sell', value=30)
    assert calls.count(sound('selling')) == 1
    assert player.screen.campaign.credits == 110
    store = CampaignStore()
    checkpoint = store.path.read_bytes()
    player.click('title')
    assert not active(manager)
    player.click('continue')
    assert player.screen.campaign.credits == 110
    assert set(player.screen.campaign.to_dict()) == before_keys
    assert store.path.read_bytes() == checkpoint
    assert calls.count(sound('selling')) == calls.count(sound('docking')) == 1


def test_runtime_mute_volume_and_exit_are_category_safe(audible_player):
    player, manager, calls = audible_player
    player.click('launch', sector=1)
    player.key(pygame.K_d)
    player.screen.advance(1 / 60)
    manager.game_sfx_volume = 23
    channel = manager._loops._channels[sound('thrust_loop')]
    assert channel.get_volume() == pytest.approx(.23, abs=1 / 128)
    manager.game_sfx_enabled = False
    assert not active(manager)
    player.screen.advance(1 / 60)
    assert not active(manager)
    player.key(pygame.K_d, False)
    manager.game_sfx_enabled = True
    player.screen.advance(1 / 60)
    assert not active(manager)
    player.key(pygame.K_d)
    player.screen.advance(1 / 60)
    assert active(manager)
    saved = CampaignStore().path.read_bytes()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    main._run_event_loop(SimpleNamespace(), player.screen, player.loader)
    assert not active(manager)
    assert CampaignStore().path.read_bytes() == saved


def test_zero_game_volume_does_not_change_ui_category(audible_player):
    player, manager, calls = audible_player
    manager.ui_sfx_volume = 71
    manager.play_ui_sfx(sound('docking'))
    from dtd.game_constants import AUDIO_CHANNEL_RANGES
    ui_channel = pygame.mixer.Channel(AUDIO_CHANNEL_RANGES['ui_sfx'].start)
    assert ui_channel.get_busy()
    player.click('launch', sector=1)
    player.key(pygame.K_d)
    player.screen.advance(1 / 60)
    manager.game_sfx_volume = 0
    assert not active(manager)
    assert ui_channel.get_volume() == pytest.approx(.71, abs=1 / 128)
    assert game_config.load_game_config().audio.game_sfx_volume == 0


def test_zero_volume_discards_old_and_new_action_cues_without_replay(audible_player):
    player, manager, calls = audible_player
    from dtd.game_constants import AUDIO_CHANNEL_RANGES
    channels = [pygame.mixer.Channel(index) for index in AUDIO_CHANNEL_RANGES['game_sfx']]
    manager.play_game_sfx(sound('destruction'))
    assert any(channel.get_busy() for channel in channels)
    manager.game_sfx_volume = 0
    assert not any(channel.get_busy() for channel in channels)
    manager.play_game_sfx(sound('weapon'))
    manager.play_game_sfx(sound('destruction'))
    assert not any(channel.get_busy() for channel in channels)
    manager.game_sfx_volume = 50
    assert not any(channel.get_busy() for channel in channels)


def test_no_device_allows_earned_trip_and_preserves_audio_preferences(monkeypatch, bootstrapped_persistence):
    monkeypatch.chdir(Path(__file__).parents[1])
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((1280, 720))
    # Exercise the production startup check after a simulated mixer-init failure.
    monkeypatch.setattr(pygame, 'init', lambda: (2, 1))
    main._init_pygame()
    assert pygame.mixer.get_init() is None
    loader = ResourceLoader()
    loader.load(None)
    preferences = AudioConfig(game_sfx_enabled=True, game_sfx_volume=37,
                              ui_sfx_enabled=False, music_volume=19)
    audio.init_audio_manager(loader, preferences)
    manager = audio.get_audio_manager()
    assert not manager.available
    assert preferences.game_sfx_enabled and preferences.game_sfx_volume == 37
    init_language_manager(loader, 'en-us')
    player = PlayerClient(loader)
    player.click('new_game')
    player.click('launch', sector=1)
    player.mine_one_rock()
    player.dock()
    player.click('sell', value=30)
    assert CampaignStore().load().credits == 110
    assert not active(manager) and pygame.mixer.get_init() is None
    assert preferences.game_sfx_enabled and preferences.game_sfx_volume == 37
    assert preferences.music_volume == 19 and not preferences.ui_sfx_enabled


def test_missing_optional_samples_do_not_interrupt_gameplay(audible_player, monkeypatch):
    player, manager, calls = audible_player
    monkeypatch.setattr(player.loader, 'get_sfx_resource', lambda resource_id: None)
    player.click('launch', sector=1)
    player.mine_one_rock()
    player.dock()
    player.click('sell', value=30)
    assert CampaignStore().load().credits == 110 and not active(manager)


def test_expired_projectile_does_not_create_impact_or_destruction_sound(audible_player):
    player, manager, calls = audible_player
    player.click('launch', sector=1)
    player.travel(750, 350)
    run = player.screen.expedition
    run.projectiles = [Projectile(500, 350, 0, 0, 24, True, ttl=.001)]
    calls.clear()
    player.screen.advance(1 / 60)
    assert not run.projectiles
    assert calls == []


def test_full_cargo_has_no_mining_loop_or_damage(audible_player):
    player, manager, calls = audible_player
    player.click('launch', sector=1)
    rock = player.screen.expedition.asteroids[0]
    player.travel(rock.x, rock.y)
    # Explicit capacity fixture, separate from earned-trip proof.
    player.screen.expedition.cargo = [0] * player.screen.campaign.capacity
    player.key(pygame.K_SPACE)
    player.screen.advance(.25)
    assert rock.health == 3 and sound('mining_loop') not in active(manager)
