"""Checkpoint round trips and failure recovery without real user state."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dtd.campaign import Campaign
from dtd import campaign_store
from dtd.campaign_store import CampaignStore, MAX_SAVE_BYTES, SaveError


def test_default_store_uses_campaign_file_in_isolated_persistence(hermetic_persistence):
    store = CampaignStore()
    assert store.path == hermetic_persistence / "campaign.json"
    assert not store.exists()
    store.save(Campaign())
    assert store.exists()
    assert not (hermetic_persistence / "game.json").exists()


def test_station_progress_round_trip_is_independent_and_preserves_settings(tmp_path):
    store = CampaignStore(tmp_path / "campaign.json")
    settings = tmp_path / "game.json"
    settings.write_bytes(b'{"custom": "settings are not campaign state"}')
    campaign = Campaign()
    campaign.credits = 850
    campaign.hull = 67.5
    campaign.cargo = [0, 1, 2]
    campaign.upgrades = {"cargo": 1, "laser": 2, "hull": 1}
    campaign.support_ships = 1
    campaign.miner = True
    campaign.engineer = True
    campaign.lifetime_sales = 2400
    store.save(campaign)
    restored = store.load()
    assert restored.to_dict() == campaign.to_dict()
    restored.cargo.append(0)
    assert campaign.cargo == [0, 1, 2]
    envelope = json.loads(store.path.read_text())
    assert envelope == {"version": 1, "campaign": campaign.to_dict()}
    assert settings.read_bytes() == b'{"custom": "settings are not campaign state"}'


@pytest.mark.parametrize("raw", [
    b"", b"not json", b"\xff", b"[]", b"null", b"{}",
    b'{"version":true,"campaign":{}}',
    b'{"version":2,"campaign":{}}',
    b'{"version":1,"campaign":{},"unexpected":0}',
    b'{"version":1,"campaign":[]}',
    b'{"version":1,"campaign":{"credits":NaN}}',
    b'{"version":1,"campaign":{"credits":Infinity}}',
    b'{"version":1,"version":1,"campaign":{}}',
    b'{"version":1,"campaign":{"credits":1,"credits":2}}',
    b" " * (MAX_SAVE_BYTES + 1),
    b"[" * 1100 + b"]" * 1100,
])
def test_invalid_save_is_rejected_without_changing_its_bytes(tmp_path, raw):
    store = CampaignStore(tmp_path / "campaign.json")
    store.path.write_bytes(raw)
    with pytest.raises(SaveError):
        store.load()
    assert store.path.read_bytes() == raw
    assert list(tmp_path.iterdir()) == [store.path]


@pytest.mark.parametrize("field,value", [
    ("credits", -1), ("hull", float("nan")), ("hull", float("inf")),
    ("cargo", [3]), ("support_ships", 3), ("miner", 1),
    ("lifetime_sales", -1),
])
def test_invalid_domain_payload_is_rejected_without_replacing_checkpoint(tmp_path, field, value):
    store = CampaignStore(tmp_path / "campaign.json")
    store.save(Campaign())
    before = store.path.read_bytes()
    broken = Campaign()
    setattr(broken, field, value)
    with pytest.raises(SaveError):
        store.save(broken)
    assert store.path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [store.path]


def test_missing_save_is_reported_without_creating_files(tmp_path):
    store = CampaignStore(tmp_path / "absent" / "campaign.json")
    assert not store.exists()
    with pytest.raises(SaveError):
        store.load()
    assert not store.path.parent.exists()


def test_active_expedition_cannot_overwrite_station_checkpoint(tmp_path):
    store = CampaignStore(tmp_path / "campaign.json")
    campaign = Campaign()
    store.save(campaign)
    previous = store.path.read_bytes()
    campaign.launch(1)
    with pytest.raises(SaveError):
        store.save(campaign)
    assert store.path.read_bytes() == previous
    assert list(tmp_path.iterdir()) == [store.path]


@pytest.mark.parametrize("operation", ["replace", "fsync"])
def test_write_failure_keeps_previous_checkpoint_and_cleans_temporary(tmp_path, monkeypatch, operation):
    store = CampaignStore(tmp_path / "campaign.json")
    store.save(Campaign())
    before = store.path.read_bytes()
    changed = Campaign()
    changed.credits = 900

    def fail(*args, **kwargs):
        raise OSError("simulated unavailable storage")

    monkeypatch.setattr(campaign_store.os, operation, fail)
    with pytest.raises(SaveError):
        store.save(changed)
    assert store.path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [store.path]


def test_atomic_replacement_uses_complete_sibling_file(tmp_path, monkeypatch):
    store = CampaignStore(tmp_path / "campaign.json")
    store.save(Campaign())
    previous = store.path.read_bytes()
    changed = Campaign()
    changed.credits = 900
    real_replace = campaign_store.os.replace
    observations = []

    def inspect_replace(source, destination):
        assert Path(source).parent == store.path.parent
        assert Path(destination) == store.path
        assert store.path.read_bytes() == previous
        observations.append(json.loads(Path(source).read_text())["campaign"]["credits"])
        real_replace(source, destination)

    monkeypatch.setattr(campaign_store.os, "replace", inspect_replace)
    store.save(changed)
    assert observations == [900]
    assert store.load().credits == 900
    assert list(tmp_path.iterdir()) == [store.path]


def test_backup_preserves_invalid_bytes_uniquely_before_replacement(tmp_path):
    store = CampaignStore(tmp_path / "campaign.json")
    original = b"\xff invalid checkpoint\x00"
    store.path.write_bytes(original)
    first = store.preserve_existing()
    second = store.preserve_existing()
    assert first != second
    assert first.parent == second.parent == store.path.parent
    assert first.read_bytes() == second.read_bytes() == store.path.read_bytes() == original
    store.save(Campaign())
    assert first.read_bytes() == second.read_bytes() == original
    assert store.load().to_dict() == Campaign().to_dict()


def test_backup_of_absent_checkpoint_creates_nothing(tmp_path):
    store = CampaignStore(tmp_path / "campaign.json")
    assert store.preserve_existing() is None
    assert list(tmp_path.iterdir()) == []


def test_backup_failure_removes_partial_copy_but_keeps_original(tmp_path, monkeypatch):
    store = CampaignStore(tmp_path / "campaign.json")
    original = b"precious original bytes"
    store.path.write_bytes(original)

    def fail(source, destination):
        destination.write(b"partial")
        raise OSError("disk full")

    monkeypatch.setattr(campaign_store.shutil, "copyfileobj", fail)
    with pytest.raises(SaveError):
        store.preserve_existing()
    assert store.path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [store.path]


def test_directory_checkpoint_reports_recoverable_error(tmp_path):
    store = CampaignStore(tmp_path / "campaign.json")
    store.path.mkdir()
    assert store.exists()
    with pytest.raises(SaveError):
        store.load()
    with pytest.raises(SaveError):
        store.preserve_existing()
    assert store.path.is_dir()
