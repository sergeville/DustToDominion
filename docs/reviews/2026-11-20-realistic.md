---
description: Implemented realistic artwork, independent playable validation, rendering costs and remaining native acceptance.
status: active
---
# Realistic visual upgrade — 2026-11-20

## 1. Result and boundaries

Implemented locally at **6566c42** on `feature/complete-small-game`. The final
independent suite passed **1,841 tests in 42.88 seconds**, with one expected SDL
dummy-renderer warning. All 13 artwork assets are integrated. Existing model,
economy, hitboxes, controls, display configuration and version-one saves are
unchanged from the firing-fix baseline `97cc41a`.

The first three-asset mining trip passed before expansion; the final trip passed
again. Native graphics rendering passed on the main Mac monitor. Physical native
input, audio, human balance and visual acceptance remain unverified. The result
is a substantial material/detail upgrade, but only a partial match to the
cinematic reference. Specs 19–21 retain their pending acceptance status.

[Independent review](2026-11-20-realistic/independent-review.md) provides the
fidelity table, findings and detailed evidence. The
[supplied prompt](../DustToDominion_Realistic_Visuals_Team_Prompt.md) and
[reference](../concepts/realistic-visual-target-2026-11-20.png) define the target;
the reference is not implemented-game evidence.

## 2. Implementation and ownership

| Owner | Delivered |
| --- | --- |
| Lead/integration | Spec before code, shared campaign UI, output-scale text, bounded effects, integration tests, native probe and documentation |
| Art | 13 individual assets, source originals, exact prompts, hashes and export manifest |
| Renderer | ResourceLoader integration, immutable preloaded art, heading/pivot adapter, bounded transform cache, vector fallbacks and renderer/presentation tests |
| Independent QA | Baseline, earned trip and combat evidence, 64-view matrix, performance comparison, acceptance tests and final regression/review |

Artwork includes Prospector, Hauler, Refinery and Rival; the four-module station;
two iron shapes, gold and crystal; mining specialist and engineer portraits;
dock panorama and starfield. See [asset provenance](../../assets/source/realistic/README.md)
and [manifest](../../assets/source/realistic/manifest.json). Runtime exports match
the source PNG hashes. Original raster art and prompts are retained, with no
claim of layered or 3D sources. Runtime PNGs total approximately 30.3 MB.

The renderer shares decoded ResourceLoader assets, preserves resource overrides,
and performs no disk reads during drawing. World transforms are capped at 128
cache entries and 32 MiB. Missing/unusable images have vector fallbacks, but the
existing application loader still rejects corrupt PNGs at startup. This is not
end-to-end corrupt-resource recovery.

Mining beams/contact sparks, two exhaust jets, ore glints, projectile streaks and
hit flashes use bounded presentation logic. They do not mutate the model or its
random generator. Portraits and dock art fit the existing station columns;
Fleet shows textured hulls with real ownership and passive bonuses. Text uses
the selected fonts and proportional sizes, rendered at the output surface size.
Covered text is removed under modal panels.

## 3. Playable and visual validation

| Evidence | Outcome and scope |
| --- | --- |
| [Baseline](2026-11-20-realistic/baseline/report.json) | `97cc41a`, 1,805 tests, original renderer and comparable fixtures |
| [First slice](2026-11-20-realistic/slice/report.json) | Prospector/iron/station trip before expansion: launched, mined, collected three ore, docked, sold; 80 → 110 credits |
| [Final report and hashes](2026-11-20-realistic/final/report.json) | Same earned trip with all assets; source hashes identify exact tested product |
| [Earned combat](2026-11-20-realistic/final/combat-earned-report.json) | Earned Sector 2 unlock; firing damaged and defeated a rival; dock banked 70-credit bounty, 160 → 230 credits |
| [Full test log](2026-11-20-realistic/final-pytest.log) | 1,841 passed; earned victory, defeat/recovery, persistence/errors, focus/pause/quit, quick clicks and display regressions included |
| [Model stress](2026-11-20-realistic/model-validation.json) | 120 expeditions, 91,400 updates; safe/risky victories and invariants passed |

QA reviewed all 64 final captures: English/German × 1280×720, 1920×1080,
2560×1440, 3840×2160 × fresh flight, mining, return, bottom edge, fleet,
station, combat and victory. Sixteen contact sheets and all original renders
are retained. Targeted full-size inspection supplemented the contact sheets.
No layout-bound/button warnings, text-layer leaks or bottom-edge obstruction
were found in those fixtures. They are synthetic layout states, separate from
the earned trip/combat captures.

Selected actual renders: [mining](2026-11-20-realistic/final/en-us-1920-mining.png),
[station](2026-11-20-realistic/final/en-us-1920-station.png),
[fleet](2026-11-20-realistic/final/en-us-1920-fleet.png),
[earned hit](2026-11-20-realistic/final/combat-earned-hit.png).

`COLLECT ORE` with `CUT 33%` was reproduced: a loose fragment exists while the
rock remains partially cut. Both messages are truthful. Minor visual polish
remains: CUT text can cross the player hull directly above a rock, and a rival
can blend into a rock despite its red health bar. A suspected missing-rock
problem was retracted after separate reviewers and byte-identical pixel patches
confirmed all remaining rocks were rendered; no source change was needed.

## 4. Rendering costs and native evidence

Observed hardware: MacBook Air M3, 24 GB RAM, ten-core GPU; main monitor
3440×1440 at 60 Hz. Python 3.12.13, pygame-ce 2.5.8, SDL 2.32.10.

Comparable SDL dummy draw medians, milliseconds, 120 measured frames per case:

| Output | Baseline normal / heavy | Final normal / heavy |
| --- | --- | --- |
| 720p | 2.809 / 3.048 | 3.707 / 3.731 |
| 1080p | 1.333 / 1.674 | 2.285 / 2.511 |
| 1440p | 3.367 / 3.637 | 4.442 / 4.586 |
| 2160p | 5.179 / 5.453 | 6.230 / 6.718 |

Final heavy 4K p95: 7.251 ms. One 1440p heavy sample reached 24.501 ms; the
other 959 samples stayed below 16.67 ms. This short sample does not establish
long-session frame pacing. Construction was approximately 123–133 ms and first
draw 5.8–10.7 ms. Cumulative process peak RSS after the capture matrix increased
from 253.73 to 460.19 MiB; this includes decoded artwork, cached transforms and
capture activity, not isolated GPU allocation or a measured memory leak.

[Native Cocoa probe](2026-11-20-realistic/native/report.json) rendered normal and
96-projectile heavy fixtures in windowed, fullscreen and returned-windowed
phases. Window pixels changed 1920×1080 → 3440×1440 → 1920×1080; desktop modes
were unchanged. The logical surface stayed 1920×1080. Render-plus-flip medians
were 6.89–7.50 ms, p95 at most 10.04 ms, maximum 13.92 ms. Paced frame medians
were approximately 16.76–16.90 ms. These are synthetic native graphics samples,
not a native campaign playthrough or a claim about all frames/devices. Captures
show the logical backbuffer, not a physical fullscreen screenshot.

The actual `main.py` application also started with isolated persistence at
approximately 11:49 EST. CUA omitted the running uv Python app; selecting its
exact executable returned `Invalid app`. Only the owned test process was
closed. That block prevented native mouse/keyboard automation. The later
internal graphics probe used application APIs, not physical input, and disabled
audio. No user's save/config files were used by validation.

## 5. Remaining acceptance and fidelity limits

- Physical native movement, quick and held fire outside the shield, mining,
  collection, docking, focus loss, pause/resume, audio and saved continuation.
- Human art, challenge and enjoyment judgment; no side-by-side comparison with a
  running reference game was performed.
- Combat label avoidance and stronger rival separation when overlapping rocks.
- Original gameplay geometry keeps ships/station smaller than the reference.
  Lighting is baked and rotates with sprites. The dock illustration's ship is
  related art rather than the identical gameplay sprite.
- Background is 1672×941; world sprites are normalized to 512 px and drawn on
  the 1920×1080 world canvas. Offscreen 4K text is output-resolution text, but
  world detail is scaled. Native fullscreen also scales its 1080p backbuffer.
  No native 4K monitor, multi-monitor movement or other-platform test occurred.

Next human route: reopen **Open Dust to Dominion.command**, choose Continue or
New Game, launch Sector 1, hold Space near a rock, fly over fragments, return and
press E, sell and save. Toggle F11, test focus/pause, then leave the shield and
try quick/held firing. Continue into unlocked sectors for combat and balance.
Tests prove reachability and consistency, not human play quality.

## 6. Reproduction and delivery

Run from the project folder:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/visual_upgrade_validation.py --phase final
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/validate_campaign.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/native_visual_upgrade.py
```

The native script opens an owned window; all probes isolate persistence. Reruns
replace named evidence outputs. Do not run benchmarks concurrently with other
heavy checks. Product sources match the hashes in the final report; subsequent
documentation/evidence commits do not change the tested code.

README, moved-prompt links, source provenance, spec and team handoff are updated.
Changes are committed locally; no push or PR. Unrelated user drafts and Finder
metadata remain untouched. To roll back the artwork, first close the game and
use a reviewed local revert of product commit `6566c42`; this retains the prior
firing fix and save schema. No rollback was performed.
