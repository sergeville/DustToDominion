"""Camera math and projected rendering preserve the world contract."""
import copy
import math
import random
from types import SimpleNamespace

import pygame
import pytest

from dtd.campaign_camera import Camera
from dtd.campaign_effects import DamageFlashes, mining_beam, projectile, ore_glint
from dtd.campaign_sprites import CampaignSprites
from dtd.campaign import Asteroid


@pytest.mark.parametrize('zoom', (1, 1.5, 2))
@pytest.mark.parametrize('focus', ((40, 190), (1880, 970), (960, 580), (-100, 3000)))
def test_round_trip_and_world_clamp(zoom, focus):
    camera = Camera(zoom)
    camera.follow(*focus)
    view = camera.visible_rect
    assert view.left >= -.0001 and view.right <= 1920.0001
    assert view.top >= 144.9999 and view.bottom <= 1020.0001
    assert view.width == pytest.approx(1920/zoom)
    assert view.height == pytest.approx(875/zoom)
    for point in ((0, 145), (1880, 970), (647.25, 400.125), (-10, 1100)):
        assert camera.screen_to_world(camera.world_to_screen(point)) == pytest.approx(point)
    assert camera.scale_length(180) == 180*zoom


def test_overview_identity_and_session_controls_are_bounded():
    camera = Camera(1)
    for focus in ((40, 190), (1880, 970)):
        camera.follow(*focus)
        assert camera.world_to_screen((430, 330)) == (430, 330)
    camera.step_zoom(10)
    assert camera.zoom == 1.5
    camera.step_zoom(1)
    camera.step_zoom(1)
    assert camera.zoom == 2
    camera.step_zoom(-1)
    assert camera.zoom == 1.5
    original = camera.viewport
    returned = camera.viewport
    returned.x = -50
    assert camera.viewport == original
    for bad in (0, 1.25, float('nan'), float('inf')):
        with pytest.raises(ValueError):
            camera.set_zoom(bad)
    with pytest.raises(ValueError):
        camera.follow(float('nan'), 20)


def test_smaller_world_is_centered_in_padded_viewport():
    camera = Camera(1, world_bounds=(100, 200, 400, 300))
    camera.follow(1000, -100)
    assert camera.center == (300, 350)
    assert camera.world_to_screen(camera.center) == (960, 582.5)
    assert camera.is_visible((300, 350))
    assert not camera.is_visible((10000, 10000), 40)


@pytest.mark.parametrize('zoom', (1, 1.5, 2))
def test_beam_projectile_flash_and_pickup_project_without_state_changes(monkeypatch, zoom):
    camera = Camera(zoom)
    camera.follow(700, 500)
    ship = SimpleNamespace(x=700, y=500, heading=.6)
    rock = Asteroid(2, 800, 530, 46, 1)
    shot = SimpleNamespace(x=850, y=550, vx=780, vy=0, friendly=True)
    flashes = DamageFlashes()
    flashes.items = [(760, 520, .1, (255, 184, 96))]
    before = copy.deepcopy((ship, rock, shot, flashes.items))
    rng = random.getstate()
    lines, circles, polygons = [], [], []
    monkeypatch.setattr(pygame.draw, 'line', lambda *a: lines.append(a))
    monkeypatch.setattr(pygame.draw, 'circle', lambda *a: circles.append(a))
    monkeypatch.setattr(pygame.draw, 'polygon', lambda *a: polygons.append(a))
    surface = pygame.Surface((1920, 1080))
    mining_beam(surface, ship, rock, .4, camera)
    mount = (ship.x+27*math.cos(ship.heading), ship.y+27*math.sin(ship.heading))
    assert lines[0][2] == pytest.approx(camera.world_to_screen(mount))
    assert lines[0][4] == round(11*zoom)
    # Exact near-contact point must use the same transform as the hull.
    delta = (rock.x-mount[0], rock.y-mount[1])
    distance = math.hypot(*delta)
    contact = (rock.x-delta[0]/distance*rock.radius*.78,
               rock.y-delta[1]/distance*rock.radius*.78)
    assert lines[0][3] == pytest.approx(camera.world_to_screen(contact))
    lines.clear()
    projectile(surface, shot, camera)
    assert lines[0][2] == camera.world_to_screen((shot.x-18, shot.y))
    assert lines[0][3] == camera.world_to_screen((shot.x, shot.y))
    circles.clear()
    flashes.draw(surface, camera)
    assert circles[0][2] == camera.world_to_screen((760, 520))
    assert circles[0][3] == round((5+.1*65)*zoom)
    ore_glint(surface, 600, 400, 2, .4, 1, camera)
    assert polygons[0][2][0] == camera.world_to_screen((595, 395))
    assert (ship, rock, shot, flashes.items) == before
    assert random.getstate() == rng


def test_projected_rock_and_station_fallbacks_keep_sources_and_cache_bounded(tmp_path):
    renderer = CampaignSprites(tmp_path)
    camera = Camera(2)
    camera.follow(960, 580)
    rock = Asteroid(1, 900, 500, 46, 0)
    before = copy.deepcopy(rock)
    surface = pygame.Surface((1920, 1080), pygame.SRCALPHA)
    renderer.draw_asteroid(surface, rock, camera)
    bounds = surface.get_bounding_rect()
    center = camera.world_to_screen((rock.x, rock.y))
    assert bounds.colliderect(pygame.Rect(center[0]-46, center[1]-46, 92, 92))
    assert bounds.width > 100  # fallback actually enlarged with the same camera
    renderer.draw_station(surface, 800, 600, size=200)
    first = renderer.cache_info.copy()
    renderer.draw_station(surface, 800, 600, size=200)
    assert renderer.cache_info == first
    assert first['entries'] <= first['entry_limit']
    assert first['bytes'] <= first['byte_limit']
    assert rock == before
