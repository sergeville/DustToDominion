"""Independent presentation regressions with real assets/fonts and isolated saves.

The first route uses only player events. Boundary and rival-on-rock scenes are
explicit synthetic layout fixtures, not evidence of earned/native play.
"""
import copy
import math
import random

import pygame
import pytest

from dtd.campaign import Asteroid, Enemy
from dtd.campaign_store import CampaignStore
from test_campaign_acceptance import player_factory  # pytest fixture


def cut_bounds(player, progress=0):
    screen = player.screen
    label = player.text('cut_progress', value=progress)
    rows = [row for row in screen._text_layer if row[0] == label]
    assert len(rows) == 1, 'The actual localized cut progress must remain visible'
    text, x, y, size, _ = rows[0]
    scale_y = pygame.display.get_surface().get_height()/1080
    width, height = screen._theme.get_font(max(1, round(size*scale_y))).size(text)
    backing_width, backing_height = screen._theme.get_font(size).size(text)
    # Map actual output-rasterized glyph dimensions back into logical screen coordinates.
    return pygame.Rect(x, y, max(backing_width, math.ceil(width/scale_y)),
                       max(backing_height, math.ceil(height/scale_y))).inflate(12, 6)


def assert_clear_cut(player, progress=0):
    bounds = cut_bounds(player, progress)
    run = player.screen.expedition
    camera = player.screen._camera
    def actor_rect(x, y, radius):
        sx, sy = camera.world_to_screen((x, y))
        r = camera.scale_length(radius)
        return pygame.Rect(sx-r, sy-r, 2*r, 2*r)
    assert pygame.Rect(0, 145, 1920, 875).contains(bounds), 'Label must clear HUD and screen edges'
    assert not bounds.colliderect(actor_rect(run.x, run.y, 38)), 'Cut text/backing crosses pilot'
    for enemy in run.enemies:
        assert not bounds.colliderect(actor_rect(enemy.x, enemy.y, 30)), 'Cut text/backing crosses rival'


@pytest.mark.parametrize('locale', ['en-us', 'de'])
def test_earned_mining_above_rock_keeps_cut_clear_and_checkpoint_unchanged(player_factory, locale):
    player = player_factory(locale, (1920, 1080))
    player.click('new_game')
    player.click('launch', sector=1)
    run = player.screen.expedition
    rock = run.asteroids[0]
    player.travel(rock.x, rock.y-80)
    player.aim(rock.x, rock.y)
    player.key(pygame.K_SPACE)
    player.screen.advance(1/60)
    player.key(pygame.K_SPACE, False)
    assert rock.health == 2 and len(run.pickups) == 1
    checkpoint = CampaignStore().path.read_bytes()
    before = copy.deepcopy((player.screen.campaign, run))
    rng = random.getstate()
    for size in ((1280, 720), (1920, 1080), (3840, 2160)):
        surface = pygame.display.set_mode(size)
        player.screen.draw(surface)
        assert_clear_cut(player, 33)
    assert (player.screen.campaign, run) == before
    assert random.getstate() == rng
    assert CampaignStore().path.read_bytes() == checkpoint


@pytest.mark.parametrize('locale', ['en-us', 'de'])
@pytest.mark.parametrize('rx,ry,px,py', [(55, 185, 55, 265), (1865, 185, 1865, 265),
                                      (55, 980, 55, 900), (1865, 980, 1865, 900)])
def test_synthetic_edge_target_retains_readable_cut_without_covering_ships(player_factory, locale, rx, ry, px, py):
    player = player_factory(locale)
    player.click('new_game')
    player.click('launch', sector=1)
    run = player.screen.expedition
    run.asteroids = [Asteroid(0, rx, ry, 46, 0)]
    run.x, run.y = px, py
    ex = rx+80 if rx < 960 else rx-80
    run.enemies = [Enemy(99, ex, py)]
    player.screen.draw(pygame.display.get_surface())
    assert_clear_cut(player)


@pytest.mark.parametrize('ore', [0, 1, 2])
def test_rival_over_each_rock_material_has_visible_red_separation_without_geometry_changes(player_factory, monkeypatch, ore):
    player = player_factory(size=(1920, 1080))
    player.click('new_game')
    player.click('launch', sector=1)
    screen, surface = player.screen, pygame.display.get_surface()
    run = screen.expedition
    run.x, run.y = 900, 500
    run.asteroids = [Asteroid(0, 400, 400, 46, ore)]
    rival = Enemy(99, 400, 400, heading=-.7)
    run.enemies = []
    screen.draw(surface)
    without = surface.copy()
    run.enemies = [rival]
    before = copy.deepcopy((screen.campaign, run))
    rng = random.getstate()
    checkpoint = CampaignStore().path.read_bytes()
    health_bars = []
    draw_bar = screen._bar
    def record_bar(x, y, width, fraction, color):
        if width < 150 and color[0] > 150 and color[0] > color[1]*1.4:
            health_bars.append(pygame.Rect(x, y, width, 10))
        return draw_bar(x, y, width, fraction, color)
    monkeypatch.setattr(screen, '_bar', record_bar)
    screen.draw(surface)
    red_separation = 0
    cx, cy = map(round, screen._camera.world_to_screen((400, 400)))
    zoom = screen._camera.zoom
    for dy in range(-round(40*zoom), round(30*zoom)):  # Exclude the existing lower health-bar region.
        for dx in range(-round(40*zoom), round(40*zoom)+1):
            if not 24*zoom < math.hypot(dx, dy) <= 40*zoom:
                continue
            actual = surface.get_at((cx+dx, cy+dy))
            prior = without.get_at((cx+dx, cy+dy))
            if actual != prior and actual.r > 150 and actual.r > actual.g*1.4 and actual.r > actual.b*1.2:
                red_separation += 1
    assert red_separation >= 20, 'Rival needs a visible hostile marker around its hull, not only a health bar'
    assert len(health_bars) == 1, 'The rival health bar must remain visible'
    assert math.dist(health_bars[0].center, (cx, cy)) <= 150, 'A bar across the screen is not an understandable rival health indicator'
    assert rival.radius == 24
    assert (screen.campaign, run) == before
    assert random.getstate() == rng
    assert CampaignStore().path.read_bytes() == checkpoint
