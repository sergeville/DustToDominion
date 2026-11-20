"""Campaign menu behavior through real store and isolated persistence."""
import pygame
import pytest

from dtd.campaign import Campaign
from dtd.campaign_store import CampaignStore
from dtd.resource_loader import ResourceLoader
from dtd.screens.base import ScreenAction
from dtd.screens.title import TitleScreen
from dtd.ui import Theme


@pytest.fixture
def title(font_ready, silent_audio_manager, silent_language_manager, bootstrapped_persistence):
    loader = ResourceLoader()
    return TitleScreen(Theme('', '', loader), loader)


def test_new_game_creates_checkpoint_and_enters_campaign(title):
    title._request_new()
    assert title.handle([]) is ScreenAction.SHOW_CAMPAIGN
    assert title.store.load().to_dict() == title.campaign.to_dict()


def test_replacement_requires_confirmation_and_preserves_old_bytes(title):
    prior = Campaign()
    prior.credits = 432
    title.store.save(prior)
    title._request_new()
    assert title._confirming
    assert title.handle([]) is None
    assert title.store.load().credits == 432
    title._cancel_new()
    assert title.handle([]) is None
    assert title.store.load().credits == 432
    title._request_new()
    title._start_new()
    assert title.handle([]) is ScreenAction.SHOW_CAMPAIGN
    assert title.store.load().credits == 80


def test_escape_cancels_confirmation_without_quitting(title):
    title.store.save(Campaign())
    title._request_new()
    events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]
    title.update(events)
    assert title.handle(events) is None
    assert not title._confirming


def test_continue_restores_campaign_and_missing_save_stays_on_title(title):
    title._request_continue()
    assert title.handle([]) is None
    assert title._message
    prior = Campaign()
    prior.credits = 421
    title.store.save(prior)
    title._request_continue()
    assert title.handle([]) is ScreenAction.SHOW_CAMPAIGN
    assert title.campaign.credits == 421


def test_load_error_does_not_overwrite_corrupt_save(title, bootstrapped_persistence):
    path = bootstrapped_persistence / 'campaign.json'
    path.write_bytes(b'broken checkpoint')
    title._request_continue()
    assert title.handle([]) is None
    assert title._message
    assert path.read_bytes() == b'broken checkpoint'
