"""App events must survive a same-frame screen transition."""
from types import SimpleNamespace

import pygame

from dtd import main
from dtd.resource_loader import ResourceLoader
from dtd.screens.base import Screen, ScreenAction


class TransitionScreen(Screen):
    def handle(self, events):
        return ScreenAction.SHOW_CAMPAIGN


def test_quit_wins_over_same_frame_campaign_transition(pygame_ready, silent_audio_manager, monkeypatch):
    monkeypatch.setattr(pygame.event, 'get', lambda: [pygame.event.Event(pygame.QUIT)])
    # TransitionScreen deliberately has no campaign/store: constructing the next
    # screen would fail, whereas QUIT should finish before construction.
    main._run_event_loop(SimpleNamespace(), TransitionScreen(), ResourceLoader())


def test_f11_survives_same_frame_title_transition(pygame_ready, silent_audio_manager, monkeypatch):
    calls = []
    batches = iter([[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11)],
                    [pygame.event.Event(pygame.QUIT)]])
    monkeypatch.setattr(pygame.event, 'get', lambda: next(batches))
    monkeypatch.setattr(main, '_create_screen', lambda *_: Screen())
    screen = Screen()
    screen._pending_action = ScreenAction.SHOW_TITLE_SCREEN
    main._run_event_loop(SimpleNamespace(on_f11=lambda: calls.append('F11')), screen, ResourceLoader())
    assert calls == ['F11']
