"""Native rasterization witnesses with logical model/layout coordinates."""
import copy

import pygame
import pytest

from dtd.campaign_camera import Camera
from dtd.campaign_effects import EffectLights
from dtd.campaign_sprites import CampaignSprites
from dtd.native_render import NativeDraw, RenderCamera
from test_campaign_presentation import presentation


@pytest.mark.parametrize('scale', [2/3, 1, 4/3, 2])
@pytest.mark.parametrize('zoom', [1, 1.5, 2])
def test_render_camera_composes_only_output_projection(scale, zoom):
    camera = Camera(zoom)
    camera.follow(1400, 670)
    before = copy.deepcopy(camera.__dict__)
    render = RenderCamera(camera, scale)
    for point in ((0, 145), (400, 420), (1800, 970)):
        expected = tuple(value*scale for value in camera.world_to_screen(point))
        assert render.world_to_screen(point) == expected
        assert render.screen_to_world(expected) == pytest.approx(point)
        assert render.is_visible(point, 34) == camera.is_visible(point, 34)
    assert render.scale_length(24) == pytest.approx(24*zoom*scale)
    assert camera.__dict__ == before


def test_native_primitives_draw_at_output_positions_and_widths():
    surface = pygame.Surface((3840, 2160)); surface.fill('black')
    draw = NativeDraw(surface.get_size())
    draw.line(surface, 'white', (100, 100), (150, 100), 3)
    assert surface.get_at((250, 200))[:3] == (255, 255, 255)
    assert surface.get_at((100, 100))[:3] == (0, 0, 0)
    occupied = sum(surface.get_at((250, y))[:3] != (0, 0, 0) for y in range(190, 210))
    assert occupied == 6
    draw.rect(surface, 'red', (300, 200, 40, 30), 2)
    assert surface.get_at((600, 400)).r == 255
    assert surface.get_at((603, 420)).r == 255
    assert surface.get_at((604, 420)).r == 0
    assert draw.bounds((0, 145, 1920, 875)) == pygame.Rect(0, 290, 3840, 1750)


def test_station_samples_full_source_at_native_size_and_caches(tmp_path, monkeypatch):
    source = pygame.Surface((1200, 1200), pygame.SRCALPHA)
    pygame.draw.circle(source, 'white', (600, 600), 570)
    for x in range(100, 1100, 3):
        pygame.draw.line(source, (20, 30, 45), (x, 400), (x, 800))
    pygame.image.save(source, str(tmp_path/'station.png'))
    art = CampaignSprites(tmp_path)
    original = pygame.image.tobytes(art._sources['station'], 'RGBA')
    scales = []
    smoothscale = pygame.transform.smoothscale
    def record(image, size, *args):
        scales.append((image.get_size(), size))
        return smoothscale(image, size, *args)
    monkeypatch.setattr(pygame.transform, 'smoothscale', record)
    surface = pygame.Surface((1000, 1000), pygame.SRCALPHA)
    art.draw_station(surface, 500, 500, size=400)
    assert any(min(src) > 1000 and min(dst) > 700 for src, dst in scales)
    assert all(src != (512, 512) for src, _ in scales)
    first = pygame.image.tobytes(surface, 'RGBA')
    scales.clear(); surface.fill((0, 0, 0, 0))
    art.draw_station(surface, 500, 500, size=400)
    assert not scales
    assert pygame.image.tobytes(surface, 'RGBA') == first
    assert pygame.image.tobytes(art._sources['station'], 'RGBA') == original


def test_missing_station_draws_native_vectors_without_bitmap_upscale(tmp_path, monkeypatch):
    art = CampaignSprites(tmp_path)
    def forbidden(*args):
        raise AssertionError('fallback station must draw native geometry')
    monkeypatch.setattr(pygame.transform, 'smoothscale', forbidden)
    target = pygame.Surface((1000, 1000), pygame.SRCALPHA)
    art.draw_station(target, 500, 500, size=400)
    bounds = target.get_bounding_rect()
    assert bounds.width > 500 and bounds.height > 650
    assert pygame.Rect(99, 99, 802, 802).contains(bounds)


def test_native_buffers_replace_size_instead_of_retaining_old_resolutions(presentation):
    screen = presentation
    for size in ((1920, 1080), (3840, 2160), (2560, 1440), (1920, 1080)):
        screen._launch(1)
        output = pygame.Surface(size)
        screen.draw(output)
        assert screen._canvas is output
        assert screen._backdrop.get_size() == size
        backdrop = screen._backdrop
        shield = screen._shield
        screen._pause(); screen.draw(output)
        assert screen._shade.get_size() == size
        shade = screen._shade
        screen.draw(output)
        assert screen._backdrop is backdrop
        assert screen._shield is shield
        assert screen._shade is shade
        expected = round(220*screen._camera.zoom*size[0]/1920)*2+2
        assert shield.get_size() == (expected, expected)
        assert screen._art.cache_info['bytes'] <= 32*1024*1024
        screen._abandon()


def test_light_radius_preserves_footprint_at_native_4k():
    lights = EffectLights()
    for scale in (1, 2):
        target = pygame.Surface((1920*scale, 1080*scale)); target.fill((10, 20, 30))
        lights.add(target, (200*scale, 200*scale), 64*scale, (255, 180, 70))
        assert target.get_at((220*scale, 200*scale)).r > 10
        assert target.get_at((265*scale, 200*scale)).r == 10
    assert any(key[0] == 128 for key in lights._cache)
    assert lights.cache_info['bytes'] <= 2*1024*1024


def test_display_transition_refreshes_current_pointer_and_preserves_pending_click(presentation, monkeypatch):
    screen = presentation
    screen._launch(1)
    screen.expedition.x, screen.expedition.y = 1400, 500
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1450, 450))
    release = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(1450, 450))
    screen.update([click, release])
    captured = screen._pending_shot
    assert captured is not None
    pygame.display.set_mode((2560, 1440))
    physical = [712, 486]
    reads = []
    def position():
        reads.append(tuple(physical))
        return tuple(physical)
    monkeypatch.setattr(pygame.mouse, 'get_pos', position)
    screen.display_changed()
    assert screen._cursor == pytest.approx((534, 364.5))
    assert screen._pending_shot == captured
    # Observed Cocoa transition queues this obsolete position after the toggle.
    screen.update([pygame.event.Event(pygame.MOUSEMOTION, pos=(1152, 486), rel=(0, 0), buttons=(0, 0, 0))])
    assert screen._cursor == pytest.approx((534, 364.5))
    assert screen._aim == pytest.approx(screen._camera.screen_to_world((534, 364.5)))
    assert screen._pending_shot == captured
    assert len(reads) == 2
    # Ordinary synthetic/genuine motion remains authoritative after settlement.
    screen.update([pygame.event.Event(pygame.MOUSEMOTION, pos=(1000, 500), rel=(0, 0), buttons=(0, 0, 0))])
    assert screen._cursor == pytest.approx((750, 375))
    screen.update([])
    assert len(reads) == 2


@pytest.mark.parametrize('early_event', ['escape', 'focus_loss'])
def test_display_pointer_settlement_runs_after_early_event_return(presentation, monkeypatch, early_event):
    screen = presentation
    screen._launch(1)
    pointer = [800, 500]
    monkeypatch.setattr(pygame.mouse, 'get_pos', lambda: tuple(pointer))
    screen.display_changed()
    pointer[:] = [900, 600]
    event = (pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
             if early_event == 'escape' else pygame.event.Event(pygame.WINDOWFOCUSLOST))
    screen.update([event])
    assert screen._cursor == (900, 600)
    assert screen.mode == 'paused'
    assert screen._display_refresh_pending is False
