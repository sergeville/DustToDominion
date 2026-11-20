"""Bitmap adapter contracts, using hermetic generated fixture pixels."""
import copy
import math
import random

import pygame
import pytest

from dtd.campaign import Asteroid
from dtd import campaign_art
from dtd.campaign_sprites import CampaignSprites, ASSET_ROOT


def arrow(root, name="prospector"):
    image = pygame.Surface((100, 100), pygame.SRCALPHA)
    pygame.draw.polygon(image, (220, 220, 220), [(50, 5), (80, 85), (20, 85)])
    pygame.draw.circle(image, (255, 0, 0), (50, 20), 6)
    pygame.image.save(image, str(root/(name+".png")))
    return image


def canvas():
    return pygame.Surface((400, 400), pygame.SRCALPHA)


def pixels(surface):
    return pygame.image.tobytes(surface, "RGBA")


def test_default_asset_path_does_not_depend_on_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    renderer = CampaignSprites()
    assert renderer.asset_root == ASSET_ROOT
    assert ASSET_ROOT.is_absolute()
    assert ASSET_ROOT.parts[-3:] == ("resources", "campaign", "realistic")


def test_missing_corrupt_empty_and_opaque_world_files_use_vectors(tmp_path):
    (tmp_path/"prospector.png").write_text("broken PNG")
    empty = pygame.Surface((20, 20), pygame.SRCALPHA)
    pygame.image.save(empty, str(tmp_path/"station.png"))
    opaque = pygame.Surface((20, 20)); opaque.fill("white")
    pygame.image.save(opaque, str(tmp_path/"hauler.png"))
    renderer = CampaignSprites(tmp_path)
    assert not renderer.loaded_names
    assert {"prospector", "station", "hauler"} <= renderer.issues.keys()
    a, b = canvas(), canvas()
    renderer.draw_ship(a, 200, 200, .7, thrust=True, phase=.3)
    campaign_art.draw_ship(b, 200, 200, .7, thrust=True, phase=.3)
    assert pixels(a) == pixels(b)
    a, b = canvas(), canvas()
    renderer.draw_station(a, 200, 200)
    campaign_art.draw_station(b, 200, 200)
    assert pixels(a) == pixels(b)
    a, b = canvas(), canvas()
    rock = Asteroid(10, 200, 200, 46, 1)
    renderer.draw_asteroid(a, rock); campaign_art.draw_asteroid(b, rock)
    assert pixels(a) == pixels(b)
    assert renderer.draw_image(a, "miner", (10, 10, 40, 40)) is False


@pytest.mark.parametrize("heading, expected", [(0, (1, 0)), (math.pi/2, (0, 1)),
                                               (-math.pi/2, (0, -1)), (math.pi, (-1, 0))])
def test_upward_source_rotates_red_nose_into_heading(tmp_path, heading, expected):
    arrow(tmp_path)
    renderer = CampaignSprites(tmp_path)
    surface = canvas()
    renderer.draw_ship(surface, 200, 200, heading, size=70)
    red = pygame.mask.from_threshold(surface, (255, 0, 0, 255), (30, 30, 30, 30))
    cx, cy = red.centroid()
    assert red.count() > 10
    dx, dy = cx-200, cy-200
    assert dx*expected[0]+dy*expected[1] > 20
    assert abs(dx*expected[1]-dy*expected[0]) <= 2


def test_all_world_pixels_stay_in_circle_even_with_disconnected_mark(tmp_path):
    image = arrow(tmp_path, "asteroid_iron")
    pygame.draw.circle(image, "white", (96, 96), 2)
    pygame.image.save(image, str(tmp_path/"asteroid_iron.png"))
    renderer = CampaignSprites(tmp_path)
    for index in range(17):
        surface = canvas()
        renderer.draw_asteroid(surface, Asteroid(index, 200, 200, 46, 0))
        mask = pygame.mask.from_surface(surface, 0)
        disk = pygame.Surface((400, 400), pygame.SRCALPHA)
        pygame.draw.circle(disk, "white", (200, 200), 47)
        boundary = pygame.mask.from_surface(disk)
        assert mask.overlap_area(boundary, (0, 0)) == mask.count()


def test_draw_is_pure_and_reads_no_assets_after_preload(tmp_path, monkeypatch):
    for name in ("prospector", "station", "asteroid_iron", "miner"):
        arrow(tmp_path, name)
    renderer = CampaignSprites(tmp_path)
    def no_load(*args, **kwargs):
        raise AssertionError("asset decoded during drawing")
    monkeypatch.setattr(pygame.image, "load", no_load)
    rock = Asteroid(19, 200, 200, 46, 0)
    original = copy.deepcopy(rock)
    state = random.getstate()
    a, b = canvas(), canvas()
    for surface in (a, b):
        renderer.draw_ship(surface, 80, 80, .73, thrust=True, phase=.8)
        renderer.draw_station(surface, 200, 200)
        renderer.draw_asteroid(surface, rock)
        renderer.draw_image(surface, "miner", (290, 10, 80, 130))
    assert pixels(a) == pixels(b)
    assert rock == original
    assert random.getstate() == state


def test_exhaust_only_changes_with_thrust_and_phase(tmp_path):
    arrow(tmp_path)
    renderer = CampaignSprites(tmp_path)
    surfaces = [canvas() for _ in range(4)]
    for surface, thrust, phase in zip(surfaces, [False, False, True, True], [0, .1, 0, .1]):
        renderer.draw_ship(surface, 200, 200, 0, size=70, thrust=thrust, phase=phase)
    assert pixels(surfaces[0]) == pixels(surfaces[1])
    assert pixels(surfaces[2]) != pixels(surfaces[3])
    assert surfaces[2].get_bounding_rect().left < surfaces[0].get_bounding_rect().left
    assert surfaces[2].get_bounding_rect().right == surfaces[0].get_bounding_rect().right


def test_cache_is_bounded_by_bytes_and_entries_and_uses_hits(tmp_path, monkeypatch):
    arrow(tmp_path)
    renderer = CampaignSprites(tmp_path, cache_entries=3, cache_bytes=100_000)
    surface = canvas()
    renderer.draw_ship(surface, 200, 200, 0, size=50)
    info = renderer.cache_info.copy()
    original = pygame.transform.smoothscale
    def no_scale(*args, **kwargs):
        raise AssertionError("identical transformed image should be cached")
    monkeypatch.setattr(pygame.transform, "smoothscale", no_scale)
    renderer.draw_ship(surface, 200, 200, 0, size=50)
    assert renderer.cache_info == info
    monkeypatch.setattr(pygame.transform, "smoothscale", original)
    for i in range(100):
        renderer.draw_ship(surface, 200, 200, i*.07, size=30+i%30)
        assert renderer.cache_info["entries"] <= 3
        assert renderer.cache_info["bytes"] <= 100_000
    # A transform larger than the budget is usable but never retained.
    renderer.draw_ship(surface, 200, 200, 0, size=180)
    assert renderer.cache_info["bytes"] <= 100_000


def test_offscreen_and_nonpositive_draws_do_not_fill_cache(tmp_path):
    arrow(tmp_path)
    renderer = CampaignSprites(tmp_path)
    surface = canvas()
    renderer.draw_ship(surface, -500, -500, 0)
    renderer.draw_ship(surface, 200, 200, 0, size=0)
    renderer.draw_image(surface, "prospector", (-100, -100, 20, 20))
    assert renderer.cache_info["entries"] == 0
    assert not surface.get_bounding_rect().width
    with pytest.raises(ValueError, match="Unknown ship kind"):
        renderer.draw_ship(surface, 200, 200, 0, kind="invalid")


def test_panel_image_preserves_aspect_and_transparency(tmp_path):
    image = pygame.Surface((100, 50), pygame.SRCALPHA)
    image.fill((160, 100, 40, 255)); image.set_at((0, 0), (0, 0, 0, 0))
    pygame.image.save(image, str(tmp_path/"dock.png"))
    renderer = CampaignSprites(tmp_path)
    surface = canvas()
    assert renderer.draw_image(surface, "dock", (100, 100, 200, 200))
    assert surface.get_bounding_rect() == pygame.Rect(100, 150, 200, 100)
    assert surface.get_at((100, 150)).a == 0


def test_background_accepts_opaque_rectangle_without_world_normalization(tmp_path):
    background = pygame.Surface((160, 90))
    background.fill((14, 24, 38))
    pygame.image.save(background, str(tmp_path/"background.png"))
    renderer = CampaignSprites(tmp_path)
    assert "background" in renderer.loaded_names
    surface = pygame.Surface((320, 180))
    assert renderer.draw_image(surface, "background", surface.get_rect())
    assert surface.get_at((0, 0))[:3] == (14, 24, 38)
    assert surface.get_at((319, 179))[:3] == (14, 24, 38)
    assert 160*90*3 <= renderer.cache_info["source_bytes"] <= 160*90*4


def test_loader_override_is_used_without_disk_reads_or_surface_mutation(tmp_path, monkeypatch):
    arrow(tmp_path)  # A different shipped file must not override the loader.
    supplied = pygame.Surface((100, 100), pygame.SRCALPHA)
    pygame.draw.polygon(supplied, (0, 220, 0), [(50, 5), (80, 85), (20, 85)])
    panel = pygame.Surface((100, 50), pygame.SRCALPHA)
    panel.fill((14, 24, 38, 255))
    originals = (pixels(supplied), pixels(panel))
    class Loader:
        def get_image_resource(self, resource_id):
            return {"campaign/realistic/prospector.png": supplied,
                    "campaign/realistic/background.png": panel}.get(resource_id)
    def no_disk(*args, **kwargs):
        raise AssertionError("loader mode must not decode files")
    monkeypatch.setattr(pygame.image, "load", no_disk)
    renderer = CampaignSprites(tmp_path, loader=Loader())
    surface = canvas()
    renderer.draw_ship(surface, 200, 200, 0, size=70, thrust=True)
    green = pygame.mask.from_threshold(surface, (0, 220, 0, 255), (5, 5, 5, 5))
    assert green.count() > 100
    renderer.draw_image(surface, "background", (10, 10, 60, 30))
    assert pixels(supplied) == originals[0]
    assert pixels(panel) == originals[1]
    assert renderer._sources["background"] is panel
    assert renderer.loaded_names == {"prospector", "background"}


def test_missing_invalid_or_no_image_api_loader_uses_vectors_not_shipped_files(tmp_path, monkeypatch):
    arrow(tmp_path)
    class InvalidLoader:
        def get_image_resource(self, resource_id):
            return "invalid surface" if resource_id.endswith("prospector.png") else None
    def no_disk(*args, **kwargs):
        raise AssertionError("loader mode must not fall back to file paths")
    monkeypatch.setattr(pygame.image, "load", no_disk)
    for loader in (object(), InvalidLoader()):
        renderer = CampaignSprites(tmp_path, loader=loader)
        assert not renderer.loaded_names
        a, b = canvas(), canvas()
        renderer.draw_ship(a, 200, 200, .7)
        campaign_art.draw_ship(b, 200, 200, .7)
        assert pixels(a) == pixels(b)


def test_iron_variant_is_stable_by_identity_and_missing_variant_uses_primary(tmp_path):
    arrow(tmp_path, "asteroid_iron")
    primary_only = CampaignSprites(tmp_path)
    alternate = pygame.Surface((100, 100), pygame.SRCALPHA)
    pygame.draw.ellipse(alternate, (80, 150, 190), (10, 30, 80, 40))
    pygame.image.save(alternate, str(tmp_path/"asteroid_iron_b.png"))
    variants = CampaignSprites(tmp_path)
    first, second, repeated, missing = [canvas() for _ in range(4)]
    # 0 and17 share the rotation bucket, so difference demonstrates selection,
    # not merely the pre-existing identity-based rotation of one image.
    primary = Asteroid(0, 200, 200, 46, 0)
    odd = Asteroid(17, 200, 200, 46, 0)
    variants.draw_asteroid(first, primary)
    variants.draw_asteroid(second, odd)
    variants.draw_asteroid(repeated, odd)
    primary_only.draw_asteroid(missing, odd)
    assert pixels(first) != pixels(second)
    assert pixels(second) == pixels(repeated)
    assert pixels(first) == pixels(missing)
    assert "asteroid_iron_b" in variants.loaded_names
    assert pygame.Rect(153, 153, 94, 94).contains(second.get_bounding_rect())


def test_rival_has_cached_separation_outside_hull_without_expanding_radius(tmp_path, monkeypatch):
    arrow(tmp_path, 'rival')
    arrow(tmp_path, 'prospector')
    renderer = CampaignSprites(tmp_path)
    original = pixels(renderer._sources['rival'])
    plain, rival = canvas(), canvas()
    renderer.draw_ship(plain, 200, 200, .7, kind='prospector', size=24)
    renderer.draw_ship(rival, 200, 200, .7, kind='rival', size=24)
    body = pygame.mask.from_surface(plain, 32)
    red_rim = pygame.mask.from_threshold(rival, (235, 116, 111, 210), (8, 8, 8, 48))
    dark_edge = pygame.mask.from_threshold(rival, (4, 9, 16, 255), (3, 3, 3, 3))
    assert red_rim.count() > red_rim.overlap_area(body, (0, 0)) + 10
    assert dark_edge.count() > dark_edge.overlap_area(body, (0, 0)) + 10
    assert pygame.Rect(175, 175, 50, 50).contains(rival.get_bounding_rect())
    assert pixels(renderer._sources['rival']) == original
    def no_stroke(*args):
        raise AssertionError('rival stroke must use the transform cache')
    monkeypatch.setattr(renderer, '_separate_rival', no_stroke)
    repeated = canvas()
    renderer.draw_ship(repeated, 200, 200, .7, kind='rival', size=24)
    assert pixels(repeated) == pixels(rival)


def test_cover_fills_panel_without_distortion_and_keeps_fit_api(tmp_path, monkeypatch):
    image = pygame.Surface((200, 100), pygame.SRCALPHA)
    image.fill((25, 40, 60, 255))
    pygame.draw.circle(image, (220, 180, 100, 255), (100, 50), 20)
    pygame.image.save(image, str(tmp_path/'dock.png'))
    renderer = CampaignSprites(tmp_path)
    original = pixels(renderer._sources['dock'])
    covered, fitted = canvas(), canvas()
    assert renderer.draw_image_cover(covered, 'dock', (100, 100, 100, 100))
    assert renderer.draw_image(fitted, 'dock', (100, 100, 100, 100))
    assert covered.get_bounding_rect() == pygame.Rect(100, 100, 100, 100)
    assert fitted.get_bounding_rect() == pygame.Rect(100, 125, 100, 50)
    circle = pygame.mask.from_threshold(covered, (220, 180, 100, 255), (1, 1, 1, 1))
    bounds = circle.get_bounding_rects()[0]
    assert bounds.width == bounds.height == 40
    assert pixels(renderer._sources['dock']) == original
    def no_scale(*args):
        raise AssertionError('identical cover must reuse its transform')
    monkeypatch.setattr(pygame.transform, 'smoothscale', no_scale)
    again = canvas()
    renderer.draw_image_cover(again, 'dock', (100, 100, 100, 100))
    assert pixels(again) == pixels(covered)


def test_cover_cache_remains_bounded_and_missing_art_is_optional(tmp_path):
    arrow(tmp_path, 'dock')
    renderer = CampaignSprites(tmp_path, cache_entries=3, cache_bytes=50_000)
    surface = canvas()
    for size in range(30, 180, 3):
        renderer.draw_image_cover(surface, 'dock', (20, 20, size, size//2))
        assert renderer.cache_info['entries'] <= 3
        assert renderer.cache_info['bytes'] <= 50_000
    before = pixels(surface)
    assert renderer.draw_image_cover(surface, 'unknown', (10, 10, 20, 20)) is False
    assert pixels(surface) == before


def test_distant_debris_is_sparse_faint_static_read_only_and_off_center(tmp_path, monkeypatch):
    arrow(tmp_path, 'asteroid_iron')
    state = random.getstate()
    renderer = CampaignSprites(tmp_path)
    original = pixels(renderer._sources['asteroid_iron'])
    a, b = [pygame.Surface((1920, 1080), pygame.SRCALPHA) for _ in range(2)]
    def no_transform(*args, **kwargs):
        raise AssertionError('debris is precomputed, not transformed per frame')
    monkeypatch.setattr(pygame.transform, 'smoothscale', no_transform)
    monkeypatch.setattr(pygame.image, 'load', no_transform)
    assert renderer.draw_field_detail(a)
    assert renderer.draw_field_detail(b)
    assert pixels(a) == pixels(b)
    assert pygame.mask.from_surface(a, 0).count() > 0
    assert pygame.mask.from_surface(a, 80).count() == 0
    assert pygame.mask.from_surface(a.subsurface((200, 250, 1500, 650)), 0).count() == 0
    assert len(renderer._field_details) == 24
    assert all(image.get_width() <= 10 and image.get_height() <= 10
               for _, _, image in renderer._field_details)
    assert renderer.cache_info['field_detail_bytes'] <= 24*10*10*4
    assert pixels(renderer._sources['asteroid_iron']) == original
    assert random.getstate() == state


def test_missing_debris_textures_omit_decorative_layer(tmp_path):
    renderer = CampaignSprites(tmp_path)
    surface = canvas()
    assert renderer.draw_field_detail(surface) is False
    assert not surface.get_bounding_rect().width
    assert renderer.cache_info['field_detail_bytes'] == 0
