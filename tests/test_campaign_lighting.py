"""Bounded additive lighting and event-derived debris, independent of gameplay."""
import copy
import random
from types import SimpleNamespace

import pygame
import pytest

from dtd.campaign import Asteroid, Enemy
from dtd.campaign_camera import Camera
from dtd.campaign_effects import EffectLights, MiningFragments, DamageFlashes, mining_beam
from dtd.campaign_sprites import CampaignSprites


def pixels(surface):
    return pygame.image.tobytes(surface, 'RGBA')


def test_additive_contact_preserves_background_and_cache_is_bounded():
    lights = EffectLights()
    surface = pygame.Surface((180, 180)); surface.fill((23, 39, 51))
    lights.add(surface, (90, 90), 26, (88, 194, 213))
    assert surface.get_at((90, 90)).r > 23
    assert surface.get_at((90, 90)).g > 39
    assert surface.get_at((117, 90))[:3] == (23, 39, 51)
    assert surface.get_at((65, 65))[:3] == (23, 39, 51)
    first = lights.cache_info.copy()
    lights.add(surface, (90, 90), 26, (88, 194, 213))
    assert lights.cache_info == first
    for index in range(250):
        lights.add(surface, (90, 90), 10000, (index, 180, 70))
        info = lights.cache_info
        assert info['entries'] <= 64 and info['bytes'] <= 2*1024*1024
    # Radius requests are capped; light cannot erase or blanket the framebuffer.
    assert surface.get_at((0, 0))[:3] == (23, 39, 51)


def test_fragments_require_mining_damage_and_expire_without_affecting_model():
    rock = Asteroid(1, 400, 400, 46, 0)
    run = SimpleNamespace(x=400, y=320, asteroids=[rock], cargo=[])
    fragments = MiningFragments()
    before = fragments.snapshot(run)
    fragments.advance(1/60, before, run, mining=True)
    assert not fragments.items
    rock.health -= 1
    fragments.advance(1/60, before, run, mining=False)
    assert not fragments.items
    snapshot = copy.deepcopy(run)
    rng = random.getstate()
    fragments.advance(1/60, before, run, mining=True)
    assert len(fragments.items) == 5
    assert run == snapshot and random.getstate() == rng
    before = fragments.snapshot(run)
    run.asteroids.clear()
    fragments.advance(1/60, before, run, mining=True)
    assert len(fragments.items) == 17
    assert run.cargo == []
    fragments.advance(1.01, {}, run)
    assert fragments.items == []


def test_fragment_storm_cap_and_deterministic_camera_projection(monkeypatch):
    def make():
        effect = MiningFragments()
        run = SimpleNamespace(x=400, y=320, asteroids=[])
        before = {i: (400., 400., 46., i%3, 3) for i in range(30)}
        effect.advance(.01, before, run, mining=True)
        return effect
    a, b = make(), make()
    assert len(a.items) == len(b.items) == 96
    assert a.items == b.items
    before = copy.deepcopy(a.items)
    rng = random.getstate()
    polygons = []
    monkeypatch.setattr(pygame.draw, 'polygon', lambda surf, color, points: polygons.append(points))
    surface = pygame.Surface((1920, 1080))
    a.draw(surface)
    identity = polygons[:]
    polygons.clear()
    camera = Camera(2); camera.follow(700, 500)
    a.draw(surface, camera)
    assert len(polygons) == 96
    for plain, projected in zip(identity, polygons):
        for world, actual in zip(plain, projected):
            assert actual == pytest.approx(camera.world_to_screen(world))
    assert a.items == before and random.getstate() == rng


def test_destroyed_rival_bursts_are_bounded_and_do_not_change_flash_contract():
    effects = DamageFlashes()
    run = SimpleNamespace(x=500, y=500, hull=100, enemies=[Enemy(i, i*10, 200) for i in range(40)])
    before = effects.snapshot(run)
    run.enemies.clear()
    effects.advance(1/60, before, run)
    assert len(effects.items) == 32
    assert all(len(item) == 4 for item in effects.items)
    assert len(effects.bursts) == 8
    effects.advance(.33, effects.snapshot(run), run)
    assert not effects.items and effects.bursts
    effects.advance(.33, effects.snapshot(run), run)
    assert effects.bursts == []


def test_lit_beam_redraw_is_deterministic_and_leaves_model_unchanged():
    ship = SimpleNamespace(x=300, y=300, heading=0)
    rock = Asteroid(1, 410, 300, 46, 2)
    camera = Camera(1.5); camera.follow(400, 300)
    lights = EffectLights()
    before = copy.deepcopy((ship, rock))
    rng = random.getstate()
    frames = []
    for _ in range(2):
        surface = pygame.Surface((1920, 1080)); surface.fill((20, 30, 40))
        mining_beam(surface, ship, rock, .4, camera, lights=lights)
        frames.append(pixels(surface))
    assert frames[0] == frames[1]
    assert (ship, rock) == before and random.getstate() == rng


def save_shape(root, name, color, shape='bars'):
    surface = pygame.Surface((100, 100), pygame.SRCALPHA)
    if shape == 'bars':
        pygame.draw.rect(surface, color, (15, 20, 20, 60))
        pygame.draw.rect(surface, color, (65, 20, 20, 60))
    else:
        pygame.draw.polygon(surface, color, [(50, 10), (85, 80), (15, 80)])
    pygame.image.save(surface, str(root/(name+'.png')))


def test_player_contour_preserves_hull_gap_and_outside_scenery(tmp_path):
    save_shape(tmp_path, 'prospector', (190, 190, 190, 255))
    renderer = CampaignSprites(tmp_path)
    surface = pygame.Surface((220, 220)); surface.fill((56, 77, 92))
    renderer.draw_ship(surface, 110, 110, -1.5707963267948966, size=50)
    # Empty hull center and external corners stay actual scenery, not backing.
    assert surface.get_at((110, 110))[:3] == (56, 77, 92)
    assert surface.get_at((60, 60))[:3] == (56, 77, 92)
    assert any(surface.get_at((x, 110))[:3] != (56, 77, 92) for x in range(65, 155))


def test_sibling_preference_and_missing_variant_fallback(tmp_path):
    save_shape(tmp_path, 'prospector', (200, 40, 40, 255))
    save_shape(tmp_path, 'prospector_v2', (40, 200, 40, 255), 'triangle')
    for name, color in [('asteroid_iron', (170, 40, 40, 255)),
                        ('asteroid_iron_b', (40, 170, 40, 255)),
                        ('asteroid_iron_c', (40, 40, 170, 255))]:
        save_shape(tmp_path, name, color, 'triangle')
    renderer = CampaignSprites(tmp_path)
    surface = pygame.Surface((220, 220), pygame.SRCALPHA)
    renderer.draw_ship(surface, 110, 110, 0, size=50)
    assert any(surface.get_at((x, 110)).g > 150 for x in range(65, 155))
    frames = []
    for identity in (0, 1, 2):
        surface.fill((0, 0, 0, 0))
        renderer.draw_asteroid(surface, Asteroid(identity, 110, 110, 46, 0))
        frames.append(pixels(surface))
    assert len(set(frames)) == 3
    # Original files remain usable if sibling exports are absent.
    (tmp_path/'prospector_v2.png').unlink()
    renderer = CampaignSprites(tmp_path)
    surface.fill((0, 0, 0, 0))
    renderer.draw_ship(surface, 110, 110, 0, size=50)
    assert any(surface.get_at((x, y)).r > 150
               for x in range(65, 155) for y in range(65, 155))


@pytest.mark.parametrize('zoom', [1, 1.5, 2])
@pytest.mark.parametrize('identity', [0, 5])
def test_mining_contact_lands_on_displayed_irregular_alpha(tmp_path, zoom, identity, monkeypatch):
    # A deep open crescent: geometric near-edge and center can both be empty.
    shape = pygame.Surface((100, 100), pygame.SRCALPHA)
    pygame.draw.circle(shape, (190, 170, 90, 255), (50, 50), 43)
    pygame.draw.circle(shape, (0, 0, 0, 0), (34, 50), 35)
    pygame.image.save(shape, str(tmp_path/'asteroid_gold_b.png'))
    renderer = CampaignSprites(tmp_path)
    ship = SimpleNamespace(x=730., y=500., heading=0.)
    rock = Asteroid(identity, 850, 500, 46, 1)
    camera = Camera(zoom); camera.follow(800, 500)
    before = copy.deepcopy((ship, rock))
    source_before = pixels(renderer._sources['asteroid_gold_b'])
    surface = pygame.Surface((1920, 1080), pygame.SRCALPHA)
    renderer.draw_asteroid(surface, rock, camera)
    point = renderer.mining_contact(ship, rock, camera)
    assert point is not None
    screen = tuple(round(v) for v in camera.world_to_screen(point))
    assert surface.get_at(screen).a >= 96
    mount = camera.world_to_screen((ship.x+27, ship.y))
    # All preceding ray pixels up to contact are transparent at the same cutoff.
    assert all(surface.get_at((x, screen[1])).a < 96
               for x in range(round(mount[0]), screen[0]))
    lines = []
    monkeypatch.setattr(pygame.draw, 'line', lambda s, c, a, b, w: lines.append((a, b)))
    mining_beam(surface, ship, rock, .1, camera, contact=point)
    assert lines[0][1] == pytest.approx(camera.world_to_screen(point))
    assert (ship, rock) == before
    assert pixels(renderer._sources['asteroid_gold_b']) == source_before
    assert renderer.cache_info['entries'] == 1


def test_mining_contact_missing_art_falls_back_without_error(tmp_path):
    renderer = CampaignSprites(tmp_path)
    ship = SimpleNamespace(x=300., y=300., heading=0.)
    rock = Asteroid(0, 327, 300, 46, 0)
    assert renderer.mining_contact(ship, rock) is None
    mining_beam(pygame.Surface((600, 600)), ship, rock, 0,
                contact=renderer.mining_contact(ship, rock))
