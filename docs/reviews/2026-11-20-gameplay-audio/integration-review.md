# Gameplay audio integration review

Status: implementation frozen for independent QA; listening acceptance pending.
Baseline: `844ad1d` (artwork/camera pass). Owner: renderer/integration agent.

## Implementation

`CampaignAudio` is a screen-owned, read-only observer. `snapshot(run)` freezes
values and retains references to pre-step rivals; `after_step(snapshot, run,
controls, dt)` observes actual model changes. Retained references let the
observer recognize a rival that fired and died in the same tick, even when its
projectile was also consumed. No model event instrumentation was needed.

`cue(name)` delegates a one-shot to AudioManager. `stop()` clears loops, stops
all eight campaign sound IDs, and discards transient timing history. There is
no backlog. Requests are limited to two desired loops and one one-shot per
category per 0.08 simulation seconds; simultaneous events share one cue.
Movement audio requires actual displacement. Mining audio requires held mining,
a live reachable asteroid and spare capacity. Cargo, firing cooldown resets,
hull changes, and destroyed objects produce their corresponding cues.

Successful docking and actual defeat acknowledge after transient cleanup;
abandon does not produce a destruction cue. A nonzero completed sale produces
the selling cue. `_clear_input` stops campaign audio across pause/focus loss,
dock, abandonment, defeat and restart. `Screen.close()` is a no-op base lifecycle
hook; CampaignScreen overrides it. Main calls close on transitions and every
loop exit, covering one-shots as well as loops. Successful title navigation
also stops immediately.

## Unavailable audio and settings

Missing mixer/device initialization warns and permits silent play. Display and
font failures remain fatal. AudioManager exposes `available`; playback, stop,
channel and volume operations safely no-op for audio when unavailable, while
settings validation and persistence continue. No fake output is enabled.
External mixer shutdown is also safe; hot-plug/reinitialization recovery is not
supported—restart with a working device.

ResourceLoader explicitly opts into `allow_unavailable_audio` in the common
resource/package decoder. Without a mixer, sound IDs have unavailable (`None`)
values and music bytes are retained without decoding. Directory reads and
package structure/manifest/hash validation still run. Audio decode is deferred
until restart. Enabled-device decoding remains strict, and standalone/package
validation defaults remain strict unless explicitly opted into silent runtime
behavior.

Game-sfx volume zero is a hard mute: existing game voices stop and new requests
are suppressed. Raising volume alone cannot expose an old one-shot tail. Loops
restart only when the caller supplies a current valid desired loop set. Existing
UI, speech and music category behavior and channel budgets are preserved.

## Validation performed

All commands used the canonical repository's `.venv/bin/python`, hermetic SDL
and temporary persistence fixtures; no user save was accessed.

- Before the zero-volume refinement: campaign audio, legacy AudioManager,
  main/startup, ResourceLoader and pak suites: **292 passed in 17.33s**.
- After the refinement: campaign audio, legacy AudioManager and campaign screen
  suites: **168 passed in 8.33s**. This includes 14 new integration-owner tests.
- Meaningful new cases cover same-tick fire/hit/removal, a firing rival removed
  with no surviving projectile, rejected firing, actual movement/mining contact,
  simultaneous pickup/destruction, bounded requests, pause/resume/dock/sell/exit,
  defeat versus abandon, real mixer loop identity, mute/unmute, zero-volume tails
  and UI independence, unavailable mixer/settings, external mixer shutdown, and
  strict versus explicitly deferred decode.
- `git diff --check` passed. Read-only baseline comparison found no changes in
  campaign rules, campaign store, camera, sprites, effects, indicators or guidance.
  Campaign screen changes are audio/lifecycle hooks only.

Independent acceptance, full-suite results and final source hashes belong to
QA/lead reports. These focused counts overlap and must not be added together.

## Limits

No physical listening or human controls acceptance has been performed by this
owner. Generated waveform/seam metrics do not establish subjective mix quality.
Immediate channel stop can cut a waveform away from zero; click-free interactive
release remains a listening check, not a claimed result. Native 4K world rendering
remains deferred. No commits or publication were performed by this owner.
