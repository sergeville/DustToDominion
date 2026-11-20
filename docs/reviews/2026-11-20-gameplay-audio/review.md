# Gameplay sound milestone — 2026-11-20

Playable implementation committed locally as **`e46970f`**, based on reviewed
artwork/camera **`844ad1d`**. **2,010 automated tests passed.** Human controls,
listening and visual acceptance remain open. Native 4K is deferred.

## Implemented

Eight original, MIT-licensed synthesized WAVs now accompany actual thrust,
mining contact, pickup, accepted shots, damage, destruction, docking and selling.
The reusable generator, seeds, parameters, hashes and level/seam measurements
are in [audio sources](../../../assets/source/audio/README.md).

A read-only campaign observer routes events through the existing AudioManager.
It does not alter the model or RNG. Two activity loops and rate-limited one-shots
use the existing 12-channel game budget. Invalid mining/firing/docking and empty
sales do not produce false cues. Pause, focus loss, docking, defeat, abandonment,
screen exit and restart clear transient audio. Game-SFX mute and zero volume
stop current sounds and discard new cues; unmuting cannot reveal stale tails.

Unavailable audio-device startup warns and continues silently. Resource integrity
validation remains intact; runtime audio decoding waits until a restart with an
available device. No fake audio device is selected for the user. Automatic
hot-plug recovery is outside this pass. Display/font failures remain fatal.

The artwork/camera baseline is `844ad1d`. Rules, geometry, economy, camera,
artwork and save schema remain unchanged. Tests and probes use isolated homes;
they do not exercise Serge's actual save as a fixture.

## Validation and evidence

Independent QA: **2,010 passed in 91.49 seconds**, including 20 independent
adversarial audio acceptance cases. The suite covers existing camera/inverse
mouse mapping, resize/fullscreen handling, campaign rules and persistence.
Focused suites overlap the full suite; their totals must not be added.

An actual invalid SDL audio driver exercised `main.run()` startup/quit and an
earned launch→mine→collect→dock→sell, progression, combat and checkpoint reload
with no initialized mixer. The eleven matched PNGs were byte-identical to the
artwork baseline's earned route. All 33 pre-existing resource files are unchanged;
only the six intended existing Python modules plus the new audio adapter changed.
The model, store, camera and presentation assets/modules are unchanged.

Recorded product revision: **`e46970fd4958580b6e237cad584a15be488bb4ca`**.

- [Mining, collection, docking and sale with audio](final/earned-mining-trip.mp4)
  — approximately 8.5 seconds; three iron sold, 80→110 CR.
- [Earned combat and docking with audio](final/earned-combat.mp4)
  — approximately 7.9 seconds; earned Sector 2, defeated a rival and banked
  70 CR (190→260), then verified the checkpoint reload.
- [Capture report and hashes](final/report.json); original WAVs, raw mixed PCM,
  eleven PNGs and video-only streams are retained beside the recordings.

These are **automated pygame-event gameplay** with SDL dummy framebuffers and
**actual SDL disk-driver software mixer output**. They are not native screen
recordings, speaker/device loopback or human play. Both video output and internal
world canvas are 1920×1080; encoded video is 30 fps. Intermediate earned
progression sorties are omitted; docking and final menus have documented holds
so their cues can finish. A 200 ms stationary pre-roll after existing launch
cleanup drains driver buffers before each clip. No gameplay state was injected
to grant progression.

Video follows the emitted PCM sample clock, holding the previous rendered frame
between observations. The video is 18.73 ms shorter than audio for mining
and 18.00 ms shorter for combat (both less than one frame). The disk sample
clock lagged wall time by 791/871 ms over
the respective clips; this is not a native latency or full-speed performance
measurement. No audio was stretched or reconstructed from event logs. Buffer
writes, render polling and AAC padding limit synchronization precision.
Both raw PCM clips are non-silent with **zero clipped samples**, peaks of
0.1184/0.1245 full scale. An initial capture had accelerated setup audio left in
the combat boundary buffer; QA retained it as superseded diagnostics and
recaptured after the documented pre-roll. The game implementation was unchanged.
Subjective mix
quality and physical playback remain pending.
See [independent QA](independent-review.md), [integration review](integration-review.md),
[audio review](audio-review.md) and [native startup attempt](native-check.md).

The native launch loaded all 39 resources without an audio-device failure.
Computer control could not attach to the unbundled Python window, so no native
input or listening test was performed. The owned test process was closed.

## Inspected warnings and environment

- Full suite: one existing `no fast renderer available` warning in the dummy
  display save-failure test. This is not a new native-renderer failure.
- Missing-device probe: expected SDL initialization/silent AudioManager warnings;
  the game stayed playable and the earned route/save reload succeeded.
- Capture: SDL labels its intentionally selected disk-I/O audio driver with a
  `CRITICAL` diagnostic; ffmpeg reports an inferred stereo channel layout. These
  describe the capture setup, not a native game crash.
- Native startup: two expected missing-config warnings in the fresh temporary
  home; no mixer failure. No user config was overwritten.
- Full-suite attempts stalled on Google Drive dependency/bytecode reads before
  executing tests. QA stopped only its stalled processes and ran the final suite
  against canonical sources using the prior exact-version local environment.
  Dependency pins and the project environment were not changed. The filesystem
  delay remains unexplained; interrupted logs are retained.

## Remaining review

Native movement, mouse aiming at all zoom levels, docking feel and actual-device
listening are **pending**, not implied by automated events or waveform metrics.
The deliberately conservative synthesized mix needs listening on Serge's usual
speakers/headphones. Bass may be weak on small speakers; impacts may be masked
by mining; abrupt interactive stops need a click check. These are measured or
implementation-based risks, not heard defects. No other-platform/device claim.

Output size and internal world resolution are separate: the world canvas remains
**1920×1080**, regardless of fullscreen monitor dimensions. Native 4K world
rendering remains unimplemented and deferred until this milestone is reviewed.
No artwork or lighting acceptance is implied by the sound update.

## Launch and review

Save at the station and close any older game. Reopen
**Open Dust to Dominion.command → Continue → Launch / Sector 1**.
Set game SFX volume in title-screen Options. Space mines asteroids; left click
fires at rival ships outside the shield. Sector 1 intentionally has no rivals.

Follow [Serge's short manual checklist](MANUAL-CHECKLIST.md): move/release,
aim at 1×/1.5×/2× while moving, mine/collect, pause/resume, dock/sell,
fight in earned Sector 2, save/reload, and mute/volume/fullscreen checks.
Mark actual results before deciding whether native higher resolution is next.
