---
description: Coherent original campaign sounds, event-based playback and controls acceptance without gameplay changes.
status: active
---

# Gameplay audio and controls milestone

## 1. Scope

Authorized by Serge on 2026-11-20; baseline artwork/camera is local `844ad1d`.
Keep current visuals, camera/input transforms, movement, collision geometry,
mining/docking ranges, combat rules, economy, save schema and existing saves.
Native 4K is deferred until this milestone is reviewed. No new dependency.
This document governs the audio addition; specs 03 and 05 carry the startup
and AudioManager changes. Presentation must not mutate simulation state or RNG.

## 2. Sound assets

Create eight original deterministic synthesized PCM WAV assets, using no
third-party recordings. Retain generator, parameters, hashes, measurements and
license/provenance under `assets/source/audio/`; distribute under the repository
MIT terms. Use 44.1 kHz, signed 16-bit mono WAV, conservative gains and continuous
loop seams. IDs are `audio/campaign/` plus:

- `thrust_loop.wav`: low engine bed while actual player movement occurs.
- `mining_loop.wav`: textured contact sound while mining a reachable live rock
  with spare cargo capacity; no contact sound for out-of-range/full/idle input.
- `ore_pickup.wav`: short clear cue when ore enters cargo.
- `weapon.wav`: pulse only for an accepted player or rival shot; rejected
  cooldown, safety-zone or projectile-budget attempts stay silent.
- `impact.wav`: damage contact, not expired or simply departing projectiles.
- `destruction.wav`: destroyed asteroid, rival or player, once per destruction.
- `docking.wav`: successful docking only, not defeat/abandon or failed E presses.
- `selling.wav`: successful nonzero sale, not a disabled/empty transaction.

Use distinct related timbres; loop beds stay below action cues. No added music,
voice, positional-audio system or changes to mixer channel budgets in this pass.
Asset quality metrics are not a substitute for Serge's listening acceptance.

## 3. Integration and lifecycle

A screen-owned campaign audio adapter observes each fixed simulation step and
successful menu command, using the existing AudioManager exclusively. Prefer
before/after state and cooldown transitions over model edits. Accepted shots
must remain detectable when created and consumed in the same simulation step.
No mutation of simulation geometry, fields, RNG, or persistence for audio.

Loops use AudioManager.set_active_loops, with no restarting an unchanged loop
set or unbounded playback requests. One-shot requests occur on transitions and
are coalesced/rate-limited where simultaneous contacts would otherwise stack.
At most two campaign loops and one cue per category per 0.08 simulation seconds;
suppressed events are discarded, not queued. Existing 12 game-SFX channels cap
concurrency. No per-frame disk loading.

Clear loop state and transient campaign sounds on pause, focus loss, dock,
abandon, defeat, title/screen exit and restart. A docking/defeat cue may play after
cleanup. Resume starts with cleared input; loops resume only for fresh valid
input. Do not replay stale one-shots after resume or unmute. Respect existing
`game_sfx_enabled` and `game_sfx_volume`, including volume zero and persisted
settings; category independence is retained. Audio is never stored in a save.

If the mixer/device cannot initialize, log a clear warning and keep the game
playable silently. Do not enable a fake dummy output on behalf of the user or
claim audible output. Display/font failures remain fatal. Missing individual
optional sounds stay nonfatal. No hot-plug recovery requirement; restarting with
an available device is the recovery path. Resource integrity checks must not be
silently bypassed for normal audio-enabled loading.

## 4. Configuration

No new user configuration keys. Existing Options audio switches/volumes govern
these sounds. Isolated tests and capture use temporary persistence exclusively.
Internal world rendering remains 1920×1080 independently of output/window size.

## 5. Ownership and dev plan

1. Lead writes spec and amends specs 03/05 before code changes.
2. Audio owner creates assets/source/license/metrics and isolated asset tests.
3. Integration owner owns adapter, campaign integration and required audio
   startup/resource handling, with focused lifecycle/event tests. Shared-file
   work is coordinated through the lead; QA does not edit implementation.
4. Independent QA adds adversarial acceptance tests, runs earned mining and
   combat routes, validates source/save preservation and records evidence.
5. Lead integrates, runs affected/full checks, prepares manual checklist and
   audio recording where available, updates docs and marks implemented spec active.

## 6. Testing

Verify loop idempotence, valid mining contact, movement boundaries, all eight
cues, accepted/rejected/same-step shots, pickup/damage/destruction coalescing,
fixed-step catch-up, pause/focus/resume, docking, abandon, defeat, title/restart,
muting/unmuting and runtime volume changes. Verify missing resources/devices
and existing settings remain safe, with no stale loops or delayed sound backlog.
Exercise real mixer decoding with dummy audio and simulate unavailable audio.
Verify asset deterministic regeneration, duration/peak/DC/seam limits and hashes.

Run existing camera/aiming/resize/fullscreen, campaign rules and save tests.
Complete an event-driven launch→move→mine→collect→dock→sell route, then earned
combat and checkpoint reload. Confirm non-presentation simulation/store/camera
sources unchanged against baseline. Tests must use isolated persistence.

Record short audio/video evidence if supported. State whether native device
loopback, software mixer capture or offline event-driven mix; an offline mix is
not evidence of actual device output. Separate automated native graphics/input
injection from human operation and listening. No hearing or feel claims without
actual performed evidence.

## 7. Acceptance criteria

- All eight sound categories play for appropriate actual events, with bounded
  concurrency and reliable loop teardown; mute/volume settings work.
- Audio device absence does not stop play or corrupt configuration/saves.
- Relevant automated tests and earned gameplay pass, with exact revision/source
  hashes and inspected warnings reported.
- Deliver playable launcher instructions, final implementation/QA reports,
  recording if available and a concise manual checklist covering launch,
  movement, aiming at 1×/1.5×/2×, zoom, mining, collection, dock/sell, fight,
  pause/resume, mute/volume, save and reload.
- Native controls/listening and Serge's subjective acceptance remain pending
  until performed. Native 4K remains deferred, not implied by large output.

### Zero-volume mute clarification — 2026-11-20

Game-SFX volume zero is mute: stop existing game voices/loops and suppress new
game one-shots at zero volume. Restoring positive volume must not reveal old
one-shot tails. Valid desired loops can start on the next gameplay update.
This applies only to the game-SFX category; other category contracts are unchanged.
Test zero→positive during a long destruction cue and while input holds a loop,
as well as settings persistence and channel-category independence.

## 8. Implementation validation — 2026-11-20

Implemented with 2,010 automated tests passing, including 20 independent audio
acceptance cases. One known SDL dummy-display renderer warning remains. Real
unavailable-driver startup and earned mining/combat/save-reload passed silently.
Active status identifies the implemented contract; native input, listening and
Serge's subjective acceptance remain pending. See the dated gameplay-audio review
under `docs/reviews/` for recordings, exact revision and evidence limits.
