"""Independent spec21 checks: rendered state purity and earned recovery.

Use the shipped-resource event client, isolated persistence and dummy display.
These are functional integration checks, not native desktop play acceptance.
"""
import copy
import random

import pygame

from dtd.campaign_store import CampaignStore
from test_campaign_acceptance import player_factory  # pytest fixture


def test_repeated_output_resolution_changes_preserve_flight_aim_and_state(player_factory):
    player = player_factory()
    player.click('new_game')
    player.click('launch', sector=1)
    player.travel(450, 510)
    run = player.screen.expedition
    checkpoint = CampaignStore().path.read_bytes()
    for size in ((3840, 2160), (1280, 720), (2560, 1440), (1920, 1080)):
        surface = pygame.display.set_mode(size)
        before = copy.deepcopy(run)
        random_before = random.getstate()
        player.screen.draw(surface)
        player.screen.draw(surface)
        assert run == before, 'Presentation must not modify the expedition or campaign'
        assert random.getstate() == random_before, 'Presentation must not consume shared RNG'
        player.aim(810, 510, pressed=True)
        player.aim(810, 510, pressed=False)
        assert player.screen._aim == (810, 510)
        player.screen.advance(1 / 60)
        friendly = [shot for shot in run.projectiles if shot.friendly]
        assert friendly and abs(friendly[-1].vy) < 1e-6 and friendly[-1].vx > 0
        # Let the firing cooldown expire through normal updates before resizing.
        for _ in range(15):
            player.screen.advance(1 / 60)
        assert CampaignStore().path.read_bytes() == checkpoint


def test_earned_dangerous_sector_defeat_recovers_and_relaunches_with_real_art(player_factory):
    player = player_factory('de', (1920, 1080))
    player.click('new_game')
    player.mine_and_sell_sortie()
    player.purchase('cargo')
    player.mine_and_sell_sortie()
    assert player.screen.campaign.lifetime_sales == 300
    banked = player.screen.campaign.credits
    player.click('launch', sector=2)
    player.travel(350, 540)
    # Deliberately do not shoot or retreat. All damage is earned enemy fire;
    # no hull, position, cargo, credits or progression values are injected.
    for frame in range(1800):
        player.screen.advance(1 / 60)
        if frame % 60 == 0:
            player.screen.draw(pygame.display.get_surface())
        if player.screen.mode == 'result':
            break
    else:
        raise AssertionError('Enemy did not defeat an exposed stationary player in 30 seconds')
    campaign = player.screen.campaign
    assert campaign.hull == campaign.max_hull / 2
    assert campaign.credits == banked and campaign.cargo == []
    assert CampaignStore().load().to_dict() == campaign.to_dict()
    player.click('continue')
    player.click('title')
    player.click('continue')
    assert player.screen.campaign.hull == 50
    player.click('launch', sector=1)
    assert player.screen.mode == 'flight' and player.screen.expedition.hull == 50
