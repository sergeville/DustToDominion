"""Observed campaign events and unavailable-device behavior (spec 22)."""
import copy
import random
from types import SimpleNamespace

import pygame
import pytest

from dtd import audio, game_config, pak
from dtd.campaign import Campaign, InputState, Enemy, Projectile, Pickup, WORLD_LEFT
from dtd.campaign_audio import CampaignAudio, SOUNDS
from dtd.errors import ResourceLoadError
from test_campaign_screen import screen, key


class Recorder:
    def __init__(self):
        self.played = []
        self.loops = frozenset()
        self.stopped = []
    def play_game_sfx(self, name):
        self.played.append(name)
    def set_active_loops(self, names):
        self.loops = names
    def stop_sfx(self, name):
        self.stopped.append(name)


def step(observer, run, controls=InputState(), dt=1/60):
    before = observer.snapshot(run)
    run.step(dt, controls)
    observer.after_step(before, run, controls, dt)


def test_thrust_requires_displacement_and_mining_requires_real_contact():
    recorder = Recorder(); observer = CampaignAudio(recorder)
    run = Campaign().launch(1)
    step(observer, run, InputState(move_y=-1))
    assert recorder.loops == {SOUNDS['thrust_loop']}
    run.x = WORLD_LEFT
    step(observer, run, InputState(move_x=-1, mining=True))
    assert recorder.loops == set()
    run.x, run.y = 350, 550
    step(observer, run, InputState(mining=True))
    assert recorder.loops == {SOUNDS['mining_loop']}
    run.cargo = [0]*run.campaign.capacity
    step(observer, run, InputState(mining=True))
    assert recorder.loops == set()


def test_same_tick_fire_hit_destroy_and_removed_enemy_fire_are_observed():
    recorder = Recorder(); observer = CampaignAudio(recorder)
    run = Campaign().launch(1)
    run.x, run.y = 300., 300.
    enemy = Enemy(7, 315., 300., hull=24., cooldown=0.)
    run.enemies = [enemy]
    step(observer, run, InputState(firing=True, aim_x=500, aim_y=300))
    assert run.enemies == []  # Friendly shot is created and consumed this tick.
    assert enemy.cooldown > 1  # Rival also fired before dying.
    assert recorder.played.count(SOUNDS['weapon']) == 1  # simultaneous coalesce
    assert SOUNDS['impact'] in recorder.played
    assert SOUNDS['destruction'] in recorder.played
    assert not any(shot.friendly for shot in run.projectiles)


def test_only_removed_rival_shot_still_counts_without_surviving_projectile():
    recorder = Recorder(); observer = CampaignAudio(recorder)
    run = Campaign().launch(1); run.x, run.y = 300., 300.
    enemy = Enemy(7, 315., 300., hull=24., cooldown=0.)
    run.enemies = [enemy]
    run.projectiles = [Projectile(302., 300., 780., 0., 24., True)]
    step(observer, run)
    assert not run.enemies and not run.projectiles
    assert recorder.played.count(SOUNDS['weapon']) == 1


def test_rejected_fire_and_expired_projectiles_are_silent():
    recorder = Recorder(); observer = CampaignAudio(recorder)
    run = Campaign().launch(1)
    step(observer, run, InputState(firing=True))  # sheltered launch
    assert not recorder.played
    run.x, run.y = 300., 300.; run._fire_cooldown = .2
    run.projectiles = [Projectile(300., 300., 10., 0., 24., True, ttl=.001)]
    step(observer, run, InputState(firing=True))
    assert not recorder.played


def test_multiple_pickups_and_depleted_rock_coalesce_without_mutation():
    recorder = Recorder(); observer = CampaignAudio(recorder)
    run = Campaign().launch(1); run.x, run.y = 350., 600.
    run.asteroids[0].health = 1
    run.pickups = [Pickup(i, run.x, run.y, 0) for i in range(3)]
    before = observer.snapshot(run)
    run.step(1/60, InputState(mining=True))
    state = copy.deepcopy((run.x, run.y, run.cargo, run.asteroids, run.pickups))
    rng = random.getstate()
    observer.after_step(before, run, InputState(mining=True), 1/60)
    assert recorder.played.count(SOUNDS['ore_pickup']) == 1
    assert recorder.played.count(SOUNDS['destruction']) == 1
    assert state == (run.x, run.y, run.cargo, run.asteroids, run.pickups)
    assert random.getstate() == rng


def test_cues_have_no_backlog_and_bounded_simultaneous_requests():
    recorder = Recorder(); observer = CampaignAudio(recorder)
    run = Campaign().launch(1)
    for _ in range(60):
        step(observer, run)
        for _ in range(30):
            observer.cue('impact')
    assert len(recorder.played) == 12  # at most once every five60Hz ticks
    observer.stop()
    assert recorder.loops == set() and set(recorder.stopped) == set(SOUNDS.values())
    step(observer, run)
    assert len(recorder.played) == 12


def test_screen_pause_resume_dock_sell_and_exit_clean_transients(screen):
    recorder = Recorder(); screen._sound = CampaignAudio(recorder)
    screen._launch(1); run = screen.expedition
    screen.update([key(pygame.K_w)]); screen.advance(1/60)
    assert SOUNDS['thrust_loop'] in recorder.loops
    screen._pause(); assert not recorder.loops
    screen._resume(); screen.advance(1/60); assert not recorder.loops
    run.x, run.y = 960, 750; run.cargo = [0]
    screen.update([key(pygame.K_e)])
    assert recorder.played == [SOUNDS['docking']]
    screen._station(); screen._station_action('sell'); screen._station_action('sell')
    assert recorder.played.count(SOUNDS['selling']) == 1
    screen.close()
    assert set(SOUNDS.values()) <= set(recorder.stopped)


def test_defeat_cues_once_after_cleanup_but_abandon_is_silent(screen):
    recorder = Recorder(); screen._sound = CampaignAudio(recorder)
    screen._launch(1); run = screen.expedition
    run.hull = 0; screen.advance(1/60)
    assert recorder.played == [SOUNDS['destruction']]
    screen._station(); screen._launch(1); screen._abandon()
    assert recorder.played == [SOUNDS['destruction']]


def test_real_mixer_loops_do_not_restart_and_mute_has_no_backlog(mixer_ready, bootstrapped_persistence):
    sound = pygame.mixer.Sound(buffer=b'\0\0'*44100)
    loader = SimpleNamespace(get_sfx_resource=lambda name: sound, get_music_resource=lambda name: None)
    manager = audio.AudioManager(loader)
    observer = CampaignAudio(manager); run = Campaign().launch(1)
    step(observer, run, InputState(move_y=-1))
    channel = manager._loops._channels[SOUNDS['thrust_loop']]
    step(observer, run, InputState(move_y=-1))
    assert manager._loops._channels[SOUNDS['thrust_loop']] is channel
    manager.game_sfx_enabled = False
    step(observer, run, InputState(move_y=-1))
    assert not manager._loops.active_ids()
    observer.cue('impact')
    manager.game_sfx_enabled = True
    step(observer, run)
    assert not manager._loops.active_ids()
    assert all(not pygame.mixer.Channel(i).get_busy() for i in range(12))


def test_unavailable_manager_preserves_settings_and_all_operations_are_safe(bootstrapped_persistence):
    pygame.mixer.quit()
    loader = SimpleNamespace(get_sfx_resource=lambda name: None, get_music_resource=lambda name: b'inert')
    manager = audio.AudioManager(loader)
    assert not manager.available
    for call in (manager.play_game_sfx, manager.play_ui_sfx, manager.play_speech,
                 manager.play_music, manager.stop_sfx):
        call('absent')
    manager.play_music_first_match(['absent'])
    manager.set_active_loops(frozenset(['absent'])); manager.stop_loops(); manager.stop_music()
    for category in ('game_sfx', 'ui_sfx', 'speech', 'music'):
        setattr(manager, category+'_volume', 37)
        setattr(manager, category+'_enabled', False)
        assert getattr(manager, category+'_volume') == 37
    restored = game_config.load_game_config().audio
    assert restored.game_sfx_volume == 37 and not restored.game_sfx_enabled


def test_mixer_shutdown_after_startup_has_safe_noops(mixer_ready, bootstrapped_persistence):
    manager = audio.AudioManager(SimpleNamespace(get_sfx_resource=lambda name: None))
    pygame.mixer.quit()
    manager.play_game_sfx('x'); manager.play_ui_sfx('x'); manager.play_speech('x')
    manager.play_music('x'); manager.stop_music(); manager.stop_sfx('x'); manager.stop_loops()
    manager.game_sfx_volume = 5; manager.music_volume = 5
    manager.game_sfx_enabled = False
    assert not manager.available


def test_no_device_decode_requires_explicit_runtime_opt_in():
    pygame.mixer.quit()
    assert pak.load_resource_from_bytes('audio/a.wav', b'deferred', allow_unavailable_audio=True) == ('sfx', None)
    assert pak.load_resource_from_bytes('audio/music/a.wav', b'deferred', allow_unavailable_audio=True) == ('music', b'deferred')
    with pytest.raises(ResourceLoadError):
        pak.load_resource_from_bytes('audio/a.wav', b'deferred')


def test_enabled_device_still_rejects_bad_audio(mixer_ready):
    with pytest.raises(ResourceLoadError):
        pak.load_resource_from_bytes('audio/a.wav', b'corrupt', allow_unavailable_audio=True)


def test_zero_game_volume_stops_old_tails_suppresses_new_and_preserves_ui(mixer_ready, bootstrapped_persistence):
    sound = pygame.mixer.Sound(buffer=b'\0\0'*44100)
    manager = audio.AudioManager(SimpleNamespace(get_sfx_resource=lambda name: sound))
    manager.play_game_sfx(SOUNDS['destruction'])
    manager.play_ui_sfx('ui')
    assert pygame.mixer.Channel(0).get_busy() and pygame.mixer.Channel(12).get_busy()
    manager.game_sfx_volume = 0
    assert not pygame.mixer.Channel(0).get_busy()
    assert pygame.mixer.Channel(12).get_busy()
    manager.play_game_sfx(SOUNDS['destruction'])
    manager.set_active_loops(frozenset([SOUNDS['thrust_loop']]))
    manager.game_sfx_volume = 60
    assert not manager._loops.active_ids()
    assert all(not pygame.mixer.Channel(i).get_busy() for i in range(12))
    manager.set_active_loops(frozenset([SOUNDS['thrust_loop']]))
    assert manager._loops.active_ids() == {SOUNDS['thrust_loop']}
