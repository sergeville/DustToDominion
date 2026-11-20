"""Original campaign PCM quality/provenance checks, spec22; no real audio device."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import struct
import wave

import pygame
import pytest

from dtd.game_constants import GAME_SFX_CHANNEL_COUNT

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/source/audio"
MANIFEST = json.loads((SOURCE / "manifest.json").read_text())
ASSETS = MANIFEST["assets"]


def read_pcm(entry):
    payload = (ROOT / "resources" / entry["id"]).read_bytes()
    with wave.open(io.BytesIO(payload), "rb") as handle:
        assert (handle.getframerate(), handle.getnchannels(), handle.getsampwidth()) == (44100, 1, 2)
        assert handle.getcomptype() == "NONE"
        count = handle.getnframes()
        pcm = struct.unpack(f"<{count}h", handle.readframes(count))
    return payload, pcm


def test_eight_distinct_original_assets_and_source_provenance():
    assert {entry["id"].split("/")[-1] for entry in ASSETS} == {
        "thrust_loop.wav", "mining_loop.wav", "ore_pickup.wav", "weapon.wav",
        "impact.wav", "destruction.wav", "docking.wav", "selling.wav",
    }
    assert len({entry["sha256"] for entry in ASSETS}) == 8
    assert MANIFEST["license"].startswith("MIT")
    assert "no external recordings" in MANIFEST["origin"]
    assert (SOURCE / MANIFEST["source"]).is_file()


@pytest.mark.parametrize("entry", ASSETS, ids=lambda e: e["id"])
def test_export_identity_format_and_signal_bounds(entry):
    payload, pcm = read_pcm(entry)
    n = len(pcm)
    assert hashlib.sha256(payload).hexdigest() == entry["sha256"]
    assert len(payload) == entry["bytes"]
    assert n / 44100 == entry["parameters"]["seconds"]
    peak = max(abs(x) for x in pcm) / 32768
    rms = math.sqrt(sum(x*x for x in pcm) / n) / 32768
    assert .025 < peak <= entry["parameters"]["peak"]
    assert .005 < rms < .025
    assert abs(sum(pcm) / n / 32768) < .00001
    assert round(peak, 8) == entry["measurements"]["peak_fs"]
    assert round(rms, 8) == entry["measurements"]["rms_fs"]
    # All 12 game channels may legally contain the same loudest clip.
    assert peak * GAME_SFX_CHANNEL_COUNT < .9
    if entry["parameters"]["loop"]:
        assert n == 88200
        seam = abs(pcm[0] - pcm[-1]) / 32768
        normal_step = max(abs(b-a) for a, b in zip(pcm, pcm[1:])) / 32768
        assert seam < .002
        assert seam <= normal_step
        assert abs((pcm[1]-pcm[0]) - (pcm[0]-pcm[-1])) <= 2
    else:
        assert pcm[0] == pcm[-1] == 0
        assert max(abs(x) for x in pcm[:10] + pcm[-10:]) < 64


@pytest.mark.parametrize("entry", ASSETS, ids=lambda e: e["id"])
def test_real_mixer_decodes_original_export(mixer_ready, entry):
    payload, _ = read_pcm(entry)
    sound = pygame.mixer.Sound(io.BytesIO(payload))
    assert sound.get_length() == pytest.approx(entry["parameters"]["seconds"], abs=.001)


def test_deterministic_regeneration_matches_all_exports_and_measurements():
    spec = importlib.util.spec_from_file_location("campaign_original_audio_generator", SOURCE / "generate.py")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    exports, manifest = generator.build()
    assert manifest == MANIFEST
    for filename, payload in exports.items():
        assert payload == (ROOT / "resources/audio/campaign" / filename).read_bytes()
