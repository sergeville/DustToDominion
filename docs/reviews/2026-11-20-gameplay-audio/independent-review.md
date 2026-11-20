# Independent gameplay audio acceptance

Implementation tested at product commit `e46970fd4958580b6e237cad584a15be488bb4ca`.
The automated implementation and retained-media gates pass. Native controls, physical device sound
and subjective listening remain unverified; this is not final human acceptance.

## Coverage and result

The full suite passed **2010 tests, 1 warning in 91.49 s**. The warning is the
existing SDL dummy-display `no fast renderer available` case at
`src/dtd/main_window.py:212`. The 20 independent audio acceptance cases also
passed separately in 11.78 s using the project interpreter. They exercise real
manager/mixer state, movement and quick-tap firing at all three zooms, pause and
focus-loss teardown, fresh-input resume, real mining contact, full cargo,
world-boundary thrust, expired projectiles, pickup/dock/sale/save reload,
missing resources and audio devices, runtime category independence, mute and
volume zero. A synthetic adversarial frame makes a rival fire and die with no
surviving projectile; accepted shot, impact and destruction are still detected.

Independent review found a real zero-volume defect: silent one-shots could keep
running and reveal their old tail when volume increased. The corrected game-SFX
hard mute stops existing voices and rejects new ones; the new regression proves
raising volume alone replays nothing. Other audio categories are preserved.

`unavailable.py` ran production `main.run` in a separate process with an invalid
SDL audio driver, injecting only the startup QUIT event. Startup returned zero,
then the original initialization/loader completed an earned trip, combat and
checkpoint reload with no initialized mixer and no dummy-audio fallback.
Expected absent-device and empty-isolated-config warnings are retained in
`unavailable.log`. This tests actual device initialization failure, not just a
mocked availability flag. Display/font failures remain covered by existing tests.

## Preservation

`baseline.json` retains the original `844ad1d` source/resource hashes.
`preservation.json` shows exactly six intended existing Python files changed;
the new observer is separate. The simulation, stores, camera, rendering helpers,
input geometry and all 33 preexisting resource files are unchanged. The 11
unavailable-device earned screenshots are byte-identical to the preceding art
pass's same earned route. No user saves or active game processes were accessed.

The earned route starts at 80 CR, mines and collects three iron, docks and sells
for 110 CR. Further earned mining/upgrades reach 330 lifetime sales; sector-2
combat earns a 70 CR bounty, docks with 260 CR and successfully reloads the
checkpoint. Firing targets were inside the visible viewport. Synthetic boundary
and same-frame fixtures are explicitly separate from this earned progression.

## Runtime and reproducibility

Commands run from the repository:

```sh
.venv/bin/python -m pytest -q tests/test_campaign_audio_acceptance.py
.venv/bin/python docs/reviews/2026-11-20-gameplay-audio/unavailable.py
/tmp/dtd-art-lighting-validation-venv/bin/python -X pycache_prefix=/tmp/dtd-audio-validation-pycache -m pytest -q
/tmp/dtd-art-lighting-validation-venv/bin/python -X pycache_prefix=/tmp/dtd-audio-validation-pycache docs/reviews/2026-11-20-gameplay-audio/capture.py --phase final
```

Two initial full-suite attempts stalled during Drive file reads, before test
execution: first `tools/__pycache__/ship_editor_lib...pyc`, then a pytest source
file after moving bytecode caching. Only owned processes were interrupted;
both logs are retained. The successful suite used the previously created
local temporary environment with the same exact project pins: Python 3.12.13,
pygame-ce 2.5.8, SDL 2.32.10, pytest 9.1.1 and pydantic 2.13.5. No project
requirements or installed project environment were changed. Evidence scripts
use isolated temporary persistence and explicit dummy video; normal launcher
drivers are unchanged.

## Actual mixed audio/video evidence

`final/report.json` records exact source/resource hashes before capture and
verifies they did not change. Both earned clips contain actual SDL **disk-driver
software mixer** output, not reconstructed events, native device loopback or
microphone audio. Retained raw PCM and WAV are signed 16-bit stereo at 44.1 kHz;
MP4 contains H264 1920×1080/30 fps and AAC stereo. `verify_media.py` fully decoded
both streams with no errors and verified every source video frame was retained.
Decoded mining-contact and rival-destruction samples were visually inspected:
beam/fragments, destruction feedback and readable HUD are present. These are
sampled visual checks, not continuous human play or listening.

| Clip | PCM duration | Video frames | Peak FS | RMS FS | Clipped samples |
| --- | ---: | ---: | ---: | ---: | ---: |
| Earned mining trip | 8.4521 s | 253 | 0.118378 | 0.014563 | 0 |
| Earned combat | 7.9180 s | 237 | 0.124542 | 0.013239 | 0 |

Video follows the observed emitted-PCM sample clock, holding the most recent
frame between observations. Video ends 18.73/18.00 ms before PCM ends; neither
audio nor video was stretched or cut. The disk driver's sample clock lagged
wall time by **0.791/0.871 s** across the two clips. This is not native A/V sync,
full-speed play or an FPS benchmark. Buffer writes/render polling also limit
event-to-frame alignment. Actual loop-registry transitions and one-shot request
byte offsets are retained; a request log alone is not proof a channel accepted it.

A 200 ms stationary pre-roll follows existing launch cleanup before each clip;
the trip docking result is held 850 ms and final menus 1.1 s so actual cues can
finish. Intervening earned progression sorties are omitted between the two
clips, not fabricated or replaced by seeded unlocks. `capture.log` contains
SDL's expected two **CRITICAL** disk-driver diagnostic notices (driver enabled
and output file), not an application fault. Encoder logs are empty; each mux log reports the
expected inferred stereo channel layout, which matches the validated stream.

The first recording exposed a capture-boundary problem: queued disk audio from
fast intervening progression contaminated combat's first buffer. Its report,
combat WAV and log remain under `superseded-initial-capture/`. The stationary
pre-roll eliminated this transient. Initial `ffmpeg -shortest` muxing also
removed final held video frames; the final harness omits that option and checks
all frames survived. Neither correction changed the product or gameplay.

## Remaining acceptance limits

The separate lead-owned native launch check establishes startup with the real
default SDL drivers, not exercised controls or physical sound. Computer-control
attachment failed for the unbundled Python app, so no OS keyboard/mouse input or
listening acceptance is claimed. The manual checklist remains necessary.

Final integrity verified all 39 Python sources against the exact product commit
and all 41 inventoried resource files against capture hashes. All 11 final earned
PNGs also match the pre-audio route byte for byte. The independent signal review
found no clipping or persistent capture-boundary anomaly; its human listening
limitations remain explicit.

All world/video rendering here is 1920×1080. Native 4K world detail is deferred.
Loop seam measurements do not prove click-free runtime stops; laptop-speaker
thrust audibility, impact masking, repeated weapon fatigue and subjective level
balance require listening. No new performance/FPS guarantee is made by these
recordings, whose encoding and capture run alongside the game.
