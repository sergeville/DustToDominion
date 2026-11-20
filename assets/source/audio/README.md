# Original campaign audio

Eight original procedurally synthesized effects for Dust to Dominion, created
for the gameplay audio milestone on 2026-11-20. No external recording, sample
library, model output, remote service or third-party sound is used. The editable
source is `generate.py`, including every oscillator, envelope, seed and gain.
These original contributions and the generated WAV assets are distributed under
the repository's MIT license (`../../../LICENSE`). Retain that license with
redistributions. No ownership claim is made over pre-existing project material.

Run from the project root:

```sh
.venv/bin/python assets/source/audio/generate.py
.venv/bin/python assets/source/audio/generate.py --check
.venv/bin/python -m pytest tests/test_campaign_audio_assets.py -q
```

Generation writes only `resources/audio/campaign/*.wav` and the adjacent
`manifest.json`. Check mode does not write. Supported Python 3.12 regenerates
identical PCM bytes; platform math-library rounding differences are possible,
so the committed SHA-256 values remain the export identity.

## Sound design

All exports are 44.1 kHz mono signed 16-bit little-endian PCM WAV. Shared
74/148/222/296 Hz harmonic families connect machinery and confirmations. The
thrust bed includes low-mid harmonics rather than sub-bass alone. Mining uses
brighter modulated harmonics and band-limited texture. Pickup is a short upward
glass tone; weapons sweep downward; impact is a short metallic thud; destruction
adds a longer noise/rumble tail; docking combines a latch and machine hum; selling
uses three related rising notes. These are intended timbres, not listening claims.

The two 2-second loops use integral-cycle spectral components, so amplitude and
slope continue across the seam without a periodic crossfade dip. One-shots have
smooth attacks and releases reaching zero at both endpoints. Playback start/stop
and mixing behavior belong to the AudioManager/integration, not these exports.

## Measured quality and limits

`manifest.json` records SHA-256, export bytes, duration, sample peak, RMS, DC,
endpoint samples, maximum adjacent step, seam step and seam slope change for each
asset. Peaks are bounded at 0.035/0.045 FS for thrust/mining, 0.065 FS for
pickup/docking/selling and 0.075 FS for weapon/impact/destruction. Quantization is
rounded within these caps. Even twelve peak-aligned campaign clips at full
category volume remain below 0.9 FS. This is a conservative campaign-only bound;
it does not cover external replacement assets, UI, speech or music mixed in.

Automated checks verify PCM decoding, identity, deterministic regeneration,
non-silence, DC, peak/concurrency bounds and loop seam continuity. No compressor
or runtime processing dependency is required. Human loudness, timbre, fatigue,
laptop-speaker balance, device output and subjective acceptance remain
**unverified until actually listened to**. Dummy mixer decoding is not listening.
