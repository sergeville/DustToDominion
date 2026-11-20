"""Independent presentation acceptance: visible output and simulation isolation."""
import copy
import math
import random
from types import SimpleNamespace

import pygame
import pytest

from dtd.campaign import Asteroid, Campaign, Enemy, Projectile
from dtd.campaign_effects import DamageFlashes, mining_beam, projectile, ore_glint
from dtd.campaign_store import CampaignStore
from dtd.language import init_language_manager
from dtd.screens.campaign import CampaignScreen
from dtd.ui import Theme
from test_campaign_screen import LocaleLoader


@pytest.fixture
def presentation(tmp_path, silent_audio_manager):
    pygame.init()
    pygame.display.set_mode((1920, 1080))
    loader = LocaleLoader()
    init_language_manager(loader)
    return CampaignScreen(Theme('', '', loader), loader, Campaign(),
                          CampaignStore(tmp_path/'presentation-save.json'))


def rgba(surface):
    return pygame.image.tobytes(surface, 'RGBA')


def target(size=(1920, 1080)):
    return pygame.Surface(size)


def isolate_text(screen, monkeypatch, painter):
    screen._stars = []
    monkeypatch.setattr(screen, '_draw_station', painter)
    monkeypatch.setattr(screen._ui, 'draw', lambda surface: None)


def test_output_glyphs_are_rasterized_at_4k_not_enlarged_1080_pixels(presentation, monkeypatch):
    screen = presentation
    text, color = 'Mining operation 0123', (225, 238, 242)
    isolate_text(screen, monkeypatch, lambda: screen._text(text, 100, 100, 28, color))
    surface = target((3840, 2160))
    screen.draw(surface)
    glyphs = screen._theme.get_font(56).render(text, True, color)
    expected = pygame.Surface(glyphs.get_size())
    expected.fill((7, 13, 25)); expected.blit(glyphs, (0, 0))
    actual = surface.subsurface((200, 200, *glyphs.get_size()))
    assert rgba(actual) == rgba(expected)


def test_wrapping_stays_logical_across_output_sizes(presentation, monkeypatch):
    screen = presentation
    words = 'Fly over loose ore then return to the station and sell cargo'
    isolate_text(screen, monkeypatch,
                 lambda: screen._text(words, 100, 100, 28, width=220))
    rows = []
    for size in ((1280, 720), (1920, 1080), (3840, 2160)):
        screen.draw(target(size))
        rows.append([(line, x, y) for line, x, y, _, _ in screen._text_layer])
    assert rows[0] == rows[1] == rows[2]
    assert len(rows[0]) > 1
    assert ' '.join(line for line, _, _ in rows[0]) == words
    assert all(screen._theme.get_font(28).size(line)[0] <= 220
               for line, _, _ in rows[0])


def test_later_opaque_panel_hides_earlier_text_but_keeps_other_labels(presentation, monkeypatch):
    screen = presentation
    def paint():
        screen._text('COVERED LABEL', 80, 100, 28)
        screen._text('VISIBLE LABEL', 600, 100, 28)
        screen._panel((50, 90, 450, 70))
    isolate_text(screen, monkeypatch, paint)
    surface = target()
    screen.draw(surface)
    hidden = pygame.mask.from_threshold(surface.subsurface((80, 100, 350, 40)),
                                        (225, 238, 242), (3, 3, 3))
    visible = pygame.mask.from_threshold(surface.subsurface((600, 100, 350, 40)),
                                         (225, 238, 242), (3, 3, 3))
    assert hidden.count() == 0
    assert visible.count() > 100


@pytest.mark.parametrize('mode', ['paused', 'abandon', 'result', 'victory', 'fleet'])
def test_modal_does_not_repaint_underlying_labels_on_top(presentation, monkeypatch, mode):
    screen = presentation
    if mode in ('paused', 'abandon'):
        screen._launch(1)
        monkeypatch.setattr(screen, '_draw_flight',
                            lambda: screen._text('UNDERLYING FLIGHT', 100, 100, 28))
    else:
        monkeypatch.setattr(screen, '_draw_station',
                            lambda: screen._text('UNDERLYING STATION', 100, 100, 28))
    screen.mode = mode; screen._rebuild()
    surface = target((2560, 1440))
    screen.draw(surface)
    leaked = pygame.mask.from_threshold(surface.subsurface((133, 133, 500, 50)),
                                        (225, 238, 242), (3, 3, 3))
    assert leaked.count() == 0
    assert not any('UNDERLYING' in line for line, *_ in screen._text_layer)


def test_resizing_releases_obsolete_output_font_entries(presentation, monkeypatch):
    screen = presentation
    isolate_text(screen, monkeypatch, lambda: screen._text('Cargo', 100, 100, 28))
    screen.draw(target((3840, 2160)))
    assert set(screen._output_fonts) == {56}
    screen.draw(target((1920, 1080)))
    assert set(screen._output_fonts) == {28}
    current = screen._output_fonts[28]
    screen.draw(target((1920, 1080)))
    assert screen._output_fonts[28] is current


def test_effect_drawing_is_repeatable_and_preserves_models_rng_and_effect_ages():
    ship = SimpleNamespace(x=60., y=160., heading=0.)
    rock = Asteroid(4, 220, 160, 46, 0)
    shot = Projectile(200, 300, 700, 100, 24, True)
    flashes = DamageFlashes()
    flashes.items = [(300, 280, .15, (255, 184, 96))]
    original = copy.deepcopy((ship, rock, shot, flashes.items))
    rng = random.getstate()
    a, b = [pygame.Surface((400, 400), pygame.SRCALPHA) for _ in range(2)]
    for surface in (a, b):
        mining_beam(surface, ship, rock, .4)
        projectile(surface, shot)
        for ore in range(3):
            ore_glint(surface, 80+ore*90, 50, ore, .4, ore)
        flashes.draw(surface)
    assert rgba(a) == rgba(b)
    assert (ship, rock, shot, flashes.items) == original
    assert random.getstate() == rng
    assert pygame.mask.from_surface(a).count() > 100


def test_damage_flashes_are_bounded_and_expire_without_mutating_run():
    run = SimpleNamespace(x=200., y=200., hull=100.,
                          enemies=[Enemy(i, 50+i*5, 100) for i in range(60)])
    flashes = DamageFlashes()
    before = flashes.snapshot(run)
    for enemy in run.enemies:
        enemy.hull -= 1
    original = copy.deepcopy(run)
    flashes.advance(1/60, before, run)
    assert len(flashes.items) == 32
    assert run == original
    flashes.advance(.33, flashes.snapshot(run), run)
    assert flashes.items == []
    assert run == original


def test_actual_projectile_damage_emits_flash_and_pause_freezes_it(presentation):
    screen = presentation
    screen._launch(1)
    run = screen.expedition
    run.x, run.y = 400., 300.
    run.projectiles.append(Projectile(400, 300, 0, 0, 8, False))
    screen.advance(1/60)
    assert run.hull == 92
    assert len(screen._impacts.items) == 1
    assert screen._impacts.items[0][:2] == (400., 300.)
    screen._pause()
    previous = copy.deepcopy((screen._impacts.items, screen._visual_time, run))
    first, second = target(), target()
    screen.draw(first); screen.advance(10); screen.draw(second)
    assert rgba(first) == rgba(second)
    assert (screen._impacts.items, screen._visual_time, run) == previous
    screen._resume()
    screen.advance(.25); screen.advance(.1)
    assert screen._impacts.items == []


@pytest.mark.parametrize('heading', [0, math.pi/2, math.pi, -math.pi/2])
def test_mining_beam_begins_at_rotated_mount_and_has_bounded_sparks(heading, monkeypatch):
    ship = SimpleNamespace(x=150., y=150., heading=heading)
    rock = Asteroid(3, 260, 270, 40, 0)
    lines = []
    original = pygame.draw.line
    def record(surface, color, start, end, width=1):
        lines.append((start, end))
        return original(surface, color, start, end, width)
    monkeypatch.setattr(pygame.draw, 'line', record)
    mining_beam(pygame.Surface((400, 400)), ship, rock, 10000.)
    start, end = lines[0]
    expected = (ship.x+math.cos(heading)*27, ship.y+math.sin(heading)*27)
    assert start == pytest.approx(expected)
    assert math.dist(end, (rock.x, rock.y)) == pytest.approx(rock.radius*.78)
    assert len(lines) == 12  # Three beam strokes and nine bounded spark strokes.


def test_zero_distance_beam_and_stationary_projectile_draw_safely():
    ship = SimpleNamespace(x=100., y=100., heading=0.)
    rock = Asteroid(3, 127, 100, 40, 0)
    surface = pygame.Surface((300, 300), pygame.SRCALPHA)
    mining_beam(surface, ship, rock, 0)
    projectile(surface, Projectile(200, 200, 0, 0, 24, True))
    assert pygame.mask.from_surface(surface).count() > 100


def test_player_backing_does_not_erase_mining_mount_connection(presentation, monkeypatch):
    screen = presentation
    screen._launch(1)
    run = screen.expedition
    run.x, run.y, run.heading = 400., 300., 0.
    run.asteroids = [Asteroid(0, 550, 300, 46, 0)]
    screen._keys.add(pygame.K_SPACE)
    # Isolate the beam/backing ordering from the shape of a particular hull.
    monkeypatch.setattr(screen._art, 'draw_ship', lambda *args, **kwargs: None)
    screen._draw_flight()
    assert screen._canvas.get_at((428, 300))[:3] != (7, 13, 25)


def test_station_shield_keeps_background_detail_visible(presentation):
    """Safety remains legible without replacing the sky with an opaque disk."""
    from dtd.campaign import STATION_X, STATION_Y, SAFE_RADIUS
    screen = presentation
    screen._launch(1)
    screen._canvas.fill((20, 30, 70))
    point = (STATION_X + SAFE_RADIUS - 40, STATION_Y)
    screen._canvas.set_at(point, (120, 140, 200))
    screen._draw_flight()
    color = screen._canvas.get_at(point)
    assert color.r > 100 and color.g > 120 and color.b > 170
    # The exact outer boundary is still drawn at the model's safe radius.
    assert screen._canvas.get_at((STATION_X + SAFE_RADIUS - 1, STATION_Y))[:3] != (20, 30, 70)
