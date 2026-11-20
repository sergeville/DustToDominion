---
description: Readability fixes, reference comparison, final screenshots and separate offscreen/native evidence for the realistic polish pass.
status: active
---
# Realistic presentation polish — 2026-11-20

## 1. Result and scope

Product changes are local commit **957e96b**; the final test-bound measurement
refinement is **a61e8d6** on `feature/complete-small-game`. This continues the
[previous artwork implementation](2026-11-20-realistic.md). Nothing was pushed.
Only the campaign presentation and sprite adapter changed under `src/`.
The model, hitboxes, safety/docking radii, economy, controls, display code and
version-one save format are unchanged. All 13 source/runtime asset hashes still
match the retained [provenance manifest](../../assets/source/realistic/manifest.json).

The existing team completed the scoped polish: root owned UI/indicators and
integration, renderer owned cached outlines/debris/panel cropping, art compared
actual screenshots with the reference, and independent QA reproduced defects,
reviewed captures and ran acceptance checks. No new artwork or dependencies were
needed. [Independent QA](2026-11-20-realistic-polish/independent-review.md) records
the baseline failures, interim correction and final verdict.

## 2. Fixes and reference comparison

| Area | Previous gap | Implemented result | Still different from reference |
| --- | --- | --- | --- |
| Flight labels | CUT could cover the player; bars competed with labels | Backed localized labels and bars seek nearby clear space around actors, HUD and each other | Extremely crowded leaders can cross visual marks; placement is bounded, not a global line router |
| Rivals | Hull blended into iron/gold/crystal | Cached dark separation, red rim and open brackets; nearby distinct red health bar | A ship directly over ore is still a dense composition, but identifiable |
| Station field | Opaque safe disk flattened scenery; every rock showed a bar | Faint transparent shield with unchanged boundaries; only targeted/damaged rocks show health | Fixed distant framing still makes flight art smaller than the concept close-up |
| Depth | Background was visually sparse | 24 tiny, faint static debris images at the edges; no fake mineable foreground objects | Lighting is baked and impact effects remain restrained |
| Station UI | Dock art was a small thumbnail | Broad undistorted dock panorama above expedition/services controls; support-hull preview | UI remains more prominent and opaque than the cinematic reference |
| Fleet | Small hulls left large empty card areas | 220-pixel artwork slots, readable ownership and bonuses | Static previews, not animated 3D hangars |

Art review passed mining, combat, station and fleet, including German 720p
originals. The larger dock and fleet images are materially closer to the
[reference](../concepts/realistic-visual-target-2026-11-20.png). This is a partial
style match, not a claim to reproduce the reference's camera, lighting or detail.
Changing physical sprite size alone would misrepresent unchanged collision bounds.

QA caught a new issue during implementation: an overlap-free health bar could
be placed far across the screen. The retained
[interim capture](2026-11-20-realistic-polish/interim-distant-rival-bar.png)
demonstrates it. Local placement rings and a distance-ordered fallback corrected
it; a locality regression now guards the rival/ore fixtures. The fallback grid is
lazy, so ordinary labels do not sort the field every frame.

## 3. Updated actual game captures

These are actual renderer outputs from labeled synthetic stress states, not
painted mockups or proof of physical play. The mining trip below is separate,
earned event-driven evidence. Each matrix contains four views × two languages ×
four sizes: 1280×720, 1920×1080, 2560×1440 and 3840×2160.

| View | 1920×1080 | 3840×2160 offscreen |
| --- | --- | --- |
| Mining above a rock | [Mining](2026-11-20-realistic-polish/final/en-us-1920-mining.png) | [Mining 4K output](2026-11-20-realistic-polish/final/en-us-3840-mining.png) |
| Rival over ore | [Combat](2026-11-20-realistic-polish/final/en-us-1920-combat.png) | [Combat 4K output](2026-11-20-realistic-polish/final/en-us-3840-combat.png) |
| Kepler Station | [Station](2026-11-20-realistic-polish/final/en-us-1920-station.png) | [Station 4K output](2026-11-20-realistic-polish/final/en-us-3840-station.png) |
| Fleet | [Fleet](2026-11-20-realistic-polish/final/en-us-1920-fleet.png) | [Fleet 4K output](2026-11-20-realistic-polish/final/en-us-3840-fleet.png) |

[Final report and image/source hashes](2026-11-20-realistic-polish/final/report.json)
contains all 32 final matrix captures and five earned-trip captures. Eight contact
sheets supplement the original images. The separate
[baseline](2026-11-20-realistic-polish/baseline/report.json) retains all 32 earlier
captures. Final matrix checks found zero framebuffer/button, label/actor,
label/bar, label/label or bar/bar overlaps. Glyph bounds use the actual output
font size plus the backing rectangle. Reviewers also inspected the images:
rectangle tests alone missed the distant-bar issue.

## 4. Playable regression and preservation

**1,860 tests passed in 48.45 seconds**, with one dummy-renderer warning. See
the [full test log](2026-11-20-realistic-polish/final-pytest.log). Captures identify
product revision `957e96b`; the full suite includes the test-only glyph/backing
refinement at `a61e8d6`. Source hashes match both revisions.

The repeated event-driven trip launched Sector 1, mined and collected three iron,
docked and sold: **80 → 110 credits**, with isolated checkpoints. Five screenshots
show fresh flight, mining, collection, docking and sale. This uses pygame player
events; it is not native OS keyboard/mouse input. Earlier first-slice sequencing
remains documented in the preceding report.

New tests reproduced the original defects before changes: **8 failed, 5 passed**.
The revised locality check subsequently caught three distant-bar cases. Final
checks cover localized actual glyph bounds, corners, all three ore materials,
immutable model/RNG/save bytes, unchanged geometry, transparent shield detail,
cache reuse/limits, undistorted crops and no per-frame debris IO/transforms.
The broader suite covers earned combat and victory, quick clicks, shield/cooldown,
focus/pause, defeat, purchase and save/error paths. No user save was used as a
fixture. Unrelated drafts and Finder metadata were preserved.

## 5. Resolution and performance evidence

The isolated [native Cocoa probe](2026-11-20-realistic-polish/native/report.json)
passed windowed → fullscreen → windowed, with normal and 96-projectile stress
scenes. Actual fullscreen window: **3440×1440**; backbuffer: **1920×1080**.
Windowed/returned dimensions were 1920×1080. Desktop modes before and after were
unchanged: 3440×1440 and 1710×1107. The probe window closed normally. Captures and
source hashes identify revision `a61e8d6`.

Native render/flip medians across six phases were **6.89–8.27 ms**, p95
**8.88–9.95 ms**, maximum **12.01 ms**. Paced frame intervals were around
**17.36–17.79 ms** (roughly 56–58 fps), so this does not establish locked 60 fps.
Each phase discarded 30 warm-up frames and measured 120 frames. Source art
allocation was 28,314,936 bytes, transformed cache 6,698,644 bytes in nine entries,
and debris 6,200 bytes. These numbers are not whole-process memory.

Offscreen 3840×2160 PNGs were drawn directly to a 3840×2160 SDL dummy surface.
They are not externally enlarged screenshots: text is rasterized at output
resolution. However, the world/art canvas remains **1920×1080** and is scaled to
fit. Thus these images verify 4K output/layout, not native 4K world detail.
The source backdrop is also below 4K. Native fullscreen on a physical 4K display
has not been verified.

Offscreen draw-only timings (120 steady frames per case; dummy driver, no present,
no simulation) are retained in the final JSON. At 1080p, normal/effect-heavy medians
were **2.36/2.79 ms**, p95 **2.55/3.23 ms**. At 4K, medians were **6.22/6.45 ms**,
p95 **6.76/6.78 ms**, maxima **6.92/7.30 ms**. No measured steady frame exceeded
16.67 ms. Construction took about 128–134 ms; first frames were measured separately.
These are measurements, not guaranteed gameplay frame rates. Process cumulative
peak RSS was 618 MiB after the capture matrix and remained stable during timing;
it is not isolated GPU memory. The preceding run used a different capture/order
workload, so its lower peak cannot establish a leak or a controlled memory delta. Transform cache limits remain 128 entries/32 MiB,
and precomputed debris adds only 6,200 bytes.

## 6. Warnings and unfinished acceptance

The [full suite](2026-11-20-realistic-polish/final-pytest.log) emitted one warning:
`pygame: no fast renderer available` at `src/dtd/main_window.py:212`, in
`test_config_save_failure_should_not_prevent_switch`. It occurs under SDL's dummy
test display and also existed before this pass. It is not a native Cocoa failure.
The [capture log](2026-11-20-realistic-polish/final-capture.log) and
[native probe log](2026-11-20-realistic-polish/native-probe.log) contain resource
load information and measurements, with no warning/error messages. The known
Windows window-drag/audio issue in the README was not retested on this Mac.
Git's whitespace check flags trailing spaces in the retained raw baseline pytest
failure log. Those original diagnostic bytes are preserved; the check passes
for source, tests and documentation when raw `.log` evidence is excluded.

Completed: scoped visual fixes, reference comparison, all four capture types,
offscreen 4K output, automated playable regression, independent QA and art review,
and the separately recorded native graphics probe.

Still pending: physical mouse/keyboard campaign play on Serge's Mac, audible sound
acceptance, human difficulty/art approval, other monitors/platforms, and physical
3840×2160 fullscreen. The native probe disables audio and drives render/window
APIs with synthetic scenes; it cannot certify those items. Specs remain proposed
pending their human/native acceptance. Sparse distant framing, baked rotating
lighting and larger opaque HUD treatment remain explicit fidelity compromises.

Reopen **Open Dust to Dominion.command** to load the updated code. Nothing is
left running by this validation. No upstream push or PR was made.

## 7. Reproduction and evidence

Run from the repository with isolated persistence configured by the scripts:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/2026-11-20-realistic-polish/validate.py --phase final --trip --benchmark
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/native_visual_upgrade.py --output-dir docs/reviews/2026-11-20-realistic-polish/native
```

Timing probes must run separately. Capture scripts overwrite their named output
directory; choose a new evidence location for a future iteration. Native saved
PNGs are backbuffer captures, not OS desktop screenshots. See the
[evidence manifest](2026-11-20-realistic-polish/evidence-manifest.json) for retained
file hashes and the [team handoff](TEAM-HANDOFF.md) for project history.
