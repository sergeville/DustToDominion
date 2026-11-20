#!/usr/bin/env python3
"""Original Dust to Dominion sound synthesis; MIT, see repository LICENSE.

Pure Python standard library, deterministic integer PCM; no recordings or models.
Run from any directory. --check compares bytes and measurements without writing.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import random
import struct
import wave

RATE = 44100
TAU = 2 * math.pi
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "resources/audio/campaign"
SOURCE = Path(__file__).resolve().parent
SPECS = {
    "thrust_loop": {"seconds": 2.0, "peak": .035, "seed": 2201, "loop": True},
    "mining_loop": {"seconds": 2.0, "peak": .045, "seed": 2202, "loop": True},
    "ore_pickup": {"seconds": .24, "peak": .065, "seed": 2203, "loop": False},
    "weapon": {"seconds": .18, "peak": .075, "seed": 2204, "loop": False},
    "impact": {"seconds": .28, "peak": .075, "seed": 2205, "loop": False},
    "destruction": {"seconds": .90, "peak": .075, "seed": 2206, "loop": False},
    "docking": {"seconds": .72, "peak": .065, "seed": 2207, "loop": False},
    "selling": {"seconds": .54, "peak": .065, "seed": 2208, "loop": False},
}


def synthesize(name: str) -> list[int]:
    """Return mono signed16 PCM. Loops use integral cycles over exactly 2s."""
    spec = SPECS[name]
    duration = spec["seconds"]
    count = round(RATE * duration)
    rng = random.Random(spec["seed"])
    samples = []
    if spec["loop"]:
        # Random signed spectral components produce band-limited mechanical
        # texture. Every phase starts at zero: zero DC and a continuous seam.
        low, high, bands = (180, 1600, 24) if name == "thrust_loop" else (500, 4200, 36)
        spectrum = [(rng.randrange(low, high), rng.uniform(-1, 1) / bands)
                    for _ in range(bands)]
        for i in range(count):
            phase = TAU * i / count
            texture = sum(gain * math.sin(cycles * phase) for cycles, gain in spectrum)
            if name == "thrust_loop":
                body = (.52 * math.sin(148 * phase) + .28 * math.sin(222 * phase)
                        + .24 * math.sin(296 * phase) + .10 * math.sin(444 * phase))
                signal = (.92 + .08 * math.cos(4 * phase)) * (body + texture)
            else:
                drill = (.42 * math.sin(592 * phase + .32 * math.sin(6 * phase))
                         + .20 * math.sin(888 * phase) + .12 * math.sin(1184 * phase))
                signal = (.85 + .15 * math.cos(10 * phase)) * (drill + 1.8 * texture)
            samples.append(signal)
    else:
        noise_low = 0.0
        for i in range(count):
            t = i / RATE
            noise_low += .19 * (rng.uniform(-1, 1) - noise_low)
            # Smooth attack and tail reach zero exactly; no hard PCM cut.
            attack = math.sin(min(1, t / .007) * math.pi / 2) ** 2
            tail = math.sin(min(1, (count - 1 - i) / (RATE * .035)) * math.pi / 2) ** 2
            if name == "ore_pickup":
                phase = TAU * (740 * t + 740 * t * t)
                signal = (math.sin(phase) + .22 * math.sin(2 * phase)) * math.exp(-12 * t)
            elif name == "weapon":
                phase = TAU * (920 * t - 1750 * t * t)
                signal = (.75 * math.sin(phase) + .22 * math.sin(1.5 * phase)
                          + .20 * noise_low) * math.exp(-21 * t)
            elif name == "impact":
                signal = (.65 * noise_low + .32 * math.sin(TAU * 148 * t)
                          + .16 * math.sin(TAU * 389 * t)) * math.exp(-19 * t)
            elif name == "destruction":
                rumble = math.sin(TAU * (95 * t - 24 * t * t))
                signal = (1.4 * noise_low + .35 * rumble
                          + .14 * math.sin(TAU * 148 * t)) * math.exp(-5.5 * t)
            elif name == "docking":
                latch = .40 * noise_low * math.exp(-22 * t)
                hum = sum(math.sin(TAU * f * t) for f in (148, 222, 296)) / 3
                signal = latch + .40 * hum * math.sin(math.pi * t / duration) ** 2
            else:  # Three related, overlapping upward confirmation notes.
                signal = 0.0
                for onset, frequency in ((0.0, 592), (.10, 740), (.20, 888)):
                    age = t - onset
                    if age >= 0:
                        onset_env = math.sin(min(1, age / .008) * math.pi / 2) ** 2
                        signal += .42 * onset_env * math.exp(-12 * age) * math.sin(TAU * frequency * age)
            samples.append(signal * attack * tail)
    # Remove one-shot DC without altering exact silent endpoints. Periodic loop
    # sums are already zero within float error; a constant correction preserves seam.
    if spec["loop"]:
        mean = sum(samples) / count
        samples = [x - mean for x in samples]
    else:
        window = [math.sin(math.pi * i / (count - 1)) ** 2 for i in range(count)]
        correction = sum(samples) / sum(window)
        samples = [x - correction * w for x, w in zip(samples, window)]
    gain = math.floor(spec["peak"] * 32768) / max(abs(x) for x in samples)
    return [round(x * gain) for x in samples]


def wav_bytes(samples: list[int]) -> bytes:
    stream = io.BytesIO()
    with wave.open(stream, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return stream.getvalue()


def measurements(samples: list[int]) -> dict:
    n = len(samples)
    return {
        "frames": n, "duration_seconds": n / RATE,
        "peak_fs": round(max(abs(x) for x in samples) / 32768, 8),
        "rms_fs": round(math.sqrt(sum(x * x for x in samples) / n) / 32768, 8),
        "dc_fs": round(sum(samples) / n / 32768, 10),
        "first_sample": samples[0], "last_sample": samples[-1],
        "seam_step_fs": round(abs(samples[0] - samples[-1]) / 32768, 8),
        "max_adjacent_step_fs": round(max(abs(b - a) for a, b in zip(samples, samples[1:])) / 32768, 8),
        "seam_slope_change_fs": round(abs((samples[1] - samples[0]) - (samples[0] - samples[-1])) / 32768, 8),
    }


def build() -> tuple[dict[str, bytes], dict]:
    exports = {}
    entries = []
    for name, spec in SPECS.items():
        samples = synthesize(name)
        payload = wav_bytes(samples)
        filename = name + ".wav"
        exports[filename] = payload
        entries.append({"id": "audio/campaign/" + filename, "parameters": spec,
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "bytes": len(payload), "measurements": measurements(samples)})
    return exports, {
        "schema_version": 1, "sample_rate": RATE, "channels": 1,
        "sample_width_bytes": 2, "encoding": "signed16 little-endian PCM WAV",
        "license": "MIT; repository LICENSE", "source": "generate.py",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "origin": "Original procedural synthesis for Dust to Dominion; no external recordings, samples, models or services.",
        "listening_status": "Unverified: metrics and dummy-mixer decoding are not human listening.",
        "reproducibility": "Python standard library; fixed seeds and parameters. SHA comparison is authoritative on supported Python 3.12 environment; libm rounding can vary across platforms.",
        "assets": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    exports, manifest = build()
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()
    expected = {OUT / name: payload for name, payload in exports.items()}
    expected[SOURCE / "manifest.json"] = manifest_bytes
    if args.check:
        mismatches = [str(path) for path, payload in expected.items()
                      if not path.exists() or path.read_bytes() != payload]
        if mismatches:
            raise SystemExit("Regeneration mismatch: " + ", ".join(mismatches))
        print("All eight WAV files and measurements reproduce exactly.")
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for path, payload in expected.items():
            path.write_bytes(payload)
        print("Generated eight original campaign WAV files and manifest.")


if __name__ == "__main__":
    main()
