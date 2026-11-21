"""Application identity through the existing loose-file and pak resource paths."""
import hashlib
import json
from pathlib import Path
import shutil

import pygame
import pytest
from loguru import logger

from dtd import game_constants, main as app_main, resource_loader
from dtd.game_config import ResourcesConfig
from dtd.pak import create_pak

ROOT = Path(__file__).resolve().parents[1]
ICON_ID = game_constants.APPLICATION_ICON_RESOURCE_ID
PACK = ROOT / 'assets/source/icons/DustToDominion-Icon-Pack-v1'


def test_selected_assets_and_runtime_pixels_match_retained_source():
    selected = ROOT / 'assets/icons/ready-to-use'
    selection = json.loads((selected / 'selection.json').read_text())
    manifest = json.loads((PACK / 'manifest.json').read_text())
    assert len(manifest['views']) == 6
    assert selection['selected_view'] in {v['id'] for v in manifest['views']}
    view = next(v for v in manifest['views'] if v['id'] == selection['selected_view'])
    for size in manifest['png_sizes']:
        assert (selected / f'app-icon-{size}.png').read_bytes() == (PACK / view['png'][str(size)]).read_bytes()
    for ext in ('icns', 'ico'):
        assert (selected / f'app-icon.{ext}').read_bytes() == (PACK / view[ext]).read_bytes()
    assert (ROOT / 'resources' / ICON_ID).read_bytes() == (selected / 'app-icon-256.png').read_bytes()
    for line in (PACK / 'SHA256SUMS.txt').read_text().splitlines():
        expected, relative = line.split('  ', 1)
        assert hashlib.sha256((PACK / relative).read_bytes()).hexdigest() == expected


@pytest.mark.parametrize('packaged', [False, True], ids=['loose', 'pak-only'])
def test_icon_resolves_from_another_cwd_before_display(tmp_path, monkeypatch, pygame_ready, packaged):
    project = tmp_path / 'game'
    source = tmp_path / 'input'
    (source / 'graphics').mkdir(parents=True)
    shutil.copy2(ROOT / 'resources' / ICON_ID, source / ICON_ID)
    project.mkdir()
    if packaged:
        create_pak(source, project / 'icons.pak')
        config = ResourcesConfig(location=['icons.pak'])
        assert not (project / 'resources').exists()
    else:
        shutil.copytree(source, project / 'resources')
        config = None
    monkeypatch.setattr(resource_loader, 'game_directory', lambda: project)
    elsewhere = tmp_path / 'elsewhere'
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    loader = resource_loader.ResourceLoader()
    loader.load(config)
    observed = []
    real_set_icon = pygame.display.set_icon

    def set_icon(surface):
        assert pygame.display.get_surface() is None
        observed.append(pygame.image.tobytes(surface, 'RGBA'))
        real_set_icon(surface)

    monkeypatch.setattr(pygame.display, 'set_icon', set_icon)
    app_main._apply_application_icon(loader)
    expected = pygame.image.load(ROOT / 'resources' / ICON_ID)
    assert observed == [pygame.image.tobytes(expected, 'RGBA')]


def test_production_startup_sets_icon_before_first_mode_on_each_restart(tmp_path, monkeypatch):
    project = tmp_path / 'game'
    (project / 'resources/graphics').mkdir(parents=True)
    shutil.copy2(ROOT / 'resources' / ICON_ID, project / 'resources' / ICON_ID)
    monkeypatch.setattr(resource_loader, 'game_directory', lambda: project)
    calls = []
    real_icon, real_mode = pygame.display.set_icon, pygame.display.set_mode

    def icon(surface):
        assert pygame.display.get_surface() is None
        calls.append('icon')
        real_icon(surface)

    def mode(*args, **kwargs):
        calls.append('mode')
        assert calls[-2] == 'icon'
        return real_mode(*args, **kwargs)

    monkeypatch.setattr(pygame.display, 'set_icon', icon)
    monkeypatch.setattr(pygame.display, 'set_mode', mode)
    monkeypatch.setattr(pygame.event, 'get', lambda: [pygame.event.Event(pygame.QUIT)])
    for _ in range(2):
        assert app_main.run() == 0
        assert not pygame.display.get_init()
    assert calls == ['icon', 'mode', 'icon', 'mode']


@pytest.mark.parametrize('missing', [True, False], ids=['missing', 'sdl-rejected'])
def test_optional_icon_failure_warns_without_aborting(monkeypatch, pygame_ready, missing):
    loader = resource_loader.ResourceLoader()
    monkeypatch.setattr(loader, 'get_image_resource', lambda key: None if missing else pygame.Surface((32, 32)))
    calls = []

    def reject(surface):
        calls.append(surface)
        raise pygame.error('test display refused icon')

    monkeypatch.setattr(pygame.display, 'set_icon', reject)
    warnings = []
    sink = logger.add(lambda msg: warnings.append(str(msg)), level='WARNING')
    try:
        app_main._apply_application_icon(loader)
    finally:
        logger.remove(sink)
    assert len(calls) == (0 if missing else 1)
    assert any('application icon' in warning for warning in warnings)
