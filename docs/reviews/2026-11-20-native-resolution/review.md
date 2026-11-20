# Native-resolution rendering review — 2026-11-20

Implemented and locally committed as **`696c3bc4c5f3bbb599d5b75bec0cf9518eea7c49`**.
Baseline: `7a17f98` (audio product `e46970f`, artwork `844ad1d`). Independent QA
approved the frozen code before commit. Capture reports retain their recording-time
base revision plus exact source hashes; those hashes match this product commit.
All 40 Python source hashes and 41 resource-file hashes were verified. Artwork,
model, store, camera, audio, configuration and persistence sources are unchanged
from the baseline. Nothing was pushed.

## What changed

The campaign draws world objects, effects, panels and text directly into its
output surface. Fullscreen requests the largest exact 16:9 surface fitting the
current desktop; SDL preserves aspect bars. The simulation and camera retain
1920×1080 logical coordinates. No completed 1080p world image is enlarged.

| Evidence | Window / output | Internal campaign raster | Status |
| --- | --- | --- | --- |
| Native Cocoa fullscreen | 3440×1440 | 2560×1440 | Measured 1:1 pixels, 440-pixel side bars |
| Native returned window | 1920×1080 | 1920×1080 | Measured |
| Offscreen 4K target | 3840×2160 | 3840×2160 | Separate automated path; physical 4K unverified |

Original artwork is sampled directly at projected native size, removing the
previous 512-pixel world-source normalization. This preserves available detail;
it adds no new artwork or physical lighting. Source detail and baked shading
remain limits. World geometry, hitboxes, ranges, rules, economy, zoom and saves
are unchanged.

## Input correction

QA reproduced a 330-logical-pixel aiming error when a stationary pointer crossed
a fullscreen transition. SDL queued a motion event using old coordinates after
changing the content position. The application now notifies the active screen
on a successful toggle. Campaign refreshes the current SDL pointer immediately
and once after the following event batch, including focus-loss/early-return paths.
It preserves pending click-time world aim and does not poll ordinary frames.

Native Cocoa replay passed with zero stored-cursor error and correct inverse
aim in fullscreen and after return. SDL maps window coordinates into content;
the UI converts content to logical coordinates once, followed by the camera
inverse. The monitor's desktop mode remained unchanged.

## Evidence and validation

Independent capture validation passed at both 2560×1440 and 3840×2160:
launch → mine → collect → dock → sell earned 3 iron and raised credits from
80 to 110. Further earned sales unlocked Sector 2; aimed fire defeated a rival,
banked its 70-credit bounty on docking (190 → 260), and title → Continue restored
the checkpoint. No user save was used.

The matrix contains **58 actual game frames**, including English/German,
all three zooms, navigation stress, station/fleet and 22 earned-route captures.
Automated text-layout and world-label/bar-bound checks reported zero warnings.

| Scene | Before, same 2560×1440 output | After, direct 2560×1440 raster |
| --- | --- | --- |
| Mining, 1.5× | [Before](baseline/en-us-2560-mining.png) | [After](final/en-us-2560-mining-z1.5.png) |
| Combat, 1.5× | [Before](baseline/en-us-2560-combat.png) | [After](final/en-us-2560-combat-z1.5.png) |
| Station | [Before](baseline/en-us-2560-station.png) | [After](final/en-us-2560-station.png) |
| Fleet | [Before](baseline/en-us-2560-fleet.png) | [After](final/en-us-2560-fleet.png) |

[English overview](final/contact-en-us-2560.png) ·
[German overview](final/contact-de-2560.png) ·
[4K overview](final/contact-en-us-3840.png) ·
[Earned mining](final/earned-2560/trip-mining.png) ·
[Earned combat](final/earned-2560/combat-firing.png).
**Full suite: 2,061 passed in 105.53 seconds.** One known warning in the dummy-display
configuration-save failure test: `no fast renderer available`. This does not
indicate a native-renderer failure. Native Cocoa graphics and pointer probes also passed. [Independent QA](independent-review.md)
contains the full commands, preservation checks and evidence limitations.

- Matched before/after views use synthetic fixtures drawn by actual game code.
  They are not generated concept art and do not prove earned gameplay.
- Earned-route evidence uses automated input with isolated persistence.
- Native graphics probes measure an actual Cocoa window and SDL renderer;
  injected/warped input is not physical mouse/keyboard acceptance.
- Offscreen 3840×2160 verifies a direct 4K drawing path, not a physical 4K monitor.
- [Serge’s baseline human results](../2026-11-20-gameplay-audio/manual-results.md)
  concern the prior build. New-build physical/visual review remains open.

## Memory and performance

The transform LRU remains bounded at 128 entries / 32 MiB. Effect lights are
bounded at 64 entries / 2 MiB. Separate single backdrop, optional modal shade
and current-zoom shield buffers are replaced when sizes change. At 4K each
full-screen 32-bit buffer costs 31.64 MiB; the shield can add about 12 MiB.
Decoded sources total about 108 MiB shared with the loader. Native text, widgets,
target surfaces and SDL allocations are additional. Total process memory is
not limited to the 32 MiB transform budget.

Measured on this Mac, without concurrent capture/test workloads:

| Path / scene | Median | p95 | Notes |
| --- | --- | --- | --- |
| Native fullscreen normal, draw + flip | 6.50 ms | 7.85 ms | 2560×1440 internal |
| Native fullscreen effects, draw + flip | 7.20 ms | 8.59 ms | 2560×1440 internal |
| Offscreen 4K normal draw | 3.81 ms | 6.78 ms | No native display presentation |
| Offscreen 4K effects draw | 4.56 ms | 6.47 ms | No native display presentation |

These are different measurement paths, not a native-versus-offscreen speed
comparison. Native paced intervals had medians 16.91–16.97 ms; no locked-60-fps
claim is made. First 4K frames took 36.40 / 27.99 ms and scene construction about
200 ms, so initial entry/resize can hitch. Short warm samples do not establish
long-session or arbitrary worst-case performance. Peak RSS in the combined
benchmark process reached 436 MiB; this is not per-scene incremental memory.

The native probes used dummy audio and emitted a deprecation warning for the
inspection helper `Window.from_display_module()`. This is probe API usage, not a
game rendering failure. No physical listening test is implied. See the
[renderer review](renderer-review.md), [native report](native/report.json) and
[offscreen timings](final/report.json).

## Launch and remaining acceptance

The [independent visual review](art-review.md) found no material new regression
in the inspected captures. Three larger differences from the reference remain:
sparse composition and repeated forms need scene/art direction; baked highlights
and colored outlines need a separate material/lighting pass; stylized impacts
and debris need revised effect artwork and rendering. More pixels alone cannot
resolve these differences. The station panorama also retains its tight crop.

Save at the station and close your current game, then reopen
**Open Dust to Dominion.command → Continue → Launch / Sector 1**.
A double-click wrapper was created on Serge’s Desktop; it executes the existing
canonical project launcher. Both scripts passed `zsh -n`; the interpreter and
entry point exist. The wrapper itself was not run, to preserve the active game.
On this Mac use **Control+Command+F** for fullscreen; Serge reported F11 did not
work on his keyboard. Zoom uses wheel / − / +; Home returns to overview.

Check fullscreen sharpness, mouse alignment at all three zoom levels, and return
to windowed mode. The game keeps its 16:9 composition and side bars on ultrawide.
Physical 4K and Retina pixel density remain unverified. Higher pixel count does
not close the reference’s artwork, lighting or composition gaps.

Volume already lives under Title screen → Options → Audio options, beside game
sound effects. Volume/mute UI and persistence, full app restart, focus loss,
individual impact/rejected-action cues and overall listening comfort still need
human acceptance. No new audio recording or physical listening test was made
for this rendering pass. Serge’s visual acceptance remains open.

The running user game is not automatically restarted by this implementation.
