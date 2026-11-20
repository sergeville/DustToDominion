# Artwork and lighting pass — 2026-11-20

Status: implementation and independent technical QA complete.
Human visual acceptance stays open. Baseline commit: `0525164` (the camera pass).

## 1. Scope and ownership

Serge authorized the existing art/rendering/QA team, with the lead acting as UI
owner. This pass changes presentation only: asteroid variation, ship/station
materials, hull separation, mining/thrust/impact effects, and range/target overlay
weight. Camera behavior, inverse aiming, movement, hitboxes, gameplay distances,
combat rules, economy and saves are preserved.

## 2. Baseline provenance

The baseline mining/combat images are retained actual renderer frames from the
validated camera pass at the exact baseline product state, each 1920×1080 and
1.5× zoom. They are not a fresh native gameplay capture. At the start of this
pass, Drive-hosted file reads and Python native imports stalled; QA preserved
those prior frames, serialized scene states and source inventory with APFS clones.
See [baseline/report.json](baseline/report.json) for exact provenance and hashes.
QA subsequently re-read all 38 baseline/current source files: only the three
presentation modules changed; the other 35 remain byte-identical. Both baseline
image hashes match. See [source-preservation.json](source-preservation.json).

## 3. Implemented changes

- Six additional 1254×1254 transparent originals: three distinct rock forms,
  improved Prospector/Rival metal and a clearer station. Original assets, prompts
  and all 19 source/export pairs are retained and hash-verified.
- Removed the opaque pilot disc and permanent white corners. Cached hull-shaped
  separation preserves transparent gaps; friendly and hostile accents remain.
- Mining contact scans the displayed rock alpha, so a concave edge does not leave
  the light hanging over empty space. Additive contact/thruster/impact light and
  short decorative chips respond to play, without changing ore pickups or damage.
- Removed redundant full mining-range and target rings; shortened corners and
  reduced shield fill. Exact safety boundary, docking, progress, health, crosshair
  and offscreen station/threat information remain.

The existing transform cache stays capped at 128 entries/32 MiB. Added light
cache: 64 entries/2 MiB, at most 64-pixel radius. Decorative mining chips: at most
96, at most one second; destruction bursts: eight groups of eight streaks for
0.65 seconds; impact flashes: 32 for 0.32 seconds. Six normalized source textures
add about 6 MiB. No per-frame disk reads or full-screen lighting buffer were added.

## 4. Matching images and reference comparison

Before/after originals use
the same 1920×1080 output, 1.5× zoom and serialized scene state. Comparison sheets
reduce both equally. Reference panels are concept targets, not game evidence.

| Scene | Matching before/after | Actual versus reference | Earned gameplay |
| --- | --- | --- | --- |
| Mining | [Pair](mining-before-after.png) | [Concept comparison](mining-reference.png) | [Mining](final/trip-mining.png), [collected](final/trip-collected.png), [sold](final/trip-sold.png) |
| Combat | [Pair](combat-before-after.png) | [Concept comparison](combat-reference.png) | [Firing](final/combat-firing.png), [rival defeated](final/combat-defeated-rival.png) |

Updated [station](final/menu-station.png) and [fleet](final/menu-fleet.png) images
come from the same earned route. [Comparison provenance](comparisons.json) retains
the original image hashes and reference crop source. [Art review](art-review.md)
and [independent QA](independent-review.md) retain their assessment and limits.

The three largest remaining gaps are distinct:

1. **Artwork:** better silhouettes and mineral faces still repeat, and small ships
   compress material detail. Source lighting rotates with each sprite. Matching
   the reference needs more deliberately authored variants and consistent material
   lighting; high-resolution raster source alone does not solve this.
2. **Rendering:** the hull rim reads as a selection outline and mining/impact light
   is still a small additive approximation. The reference has broad warm fracture
   spray, local shadows and illuminated surfaces. Closing that gap needs material
   masks/normal maps or authored effect sequences plus a measured lighting budget.
   Native 4K would sharpen output but would not create these lighting effects.
3. **Framing:** the same following camera and arena still leave large quiet areas;
   the reference tightly arranges larger rocks, ships and station in its panels.
   Asset changes do not change that composition. Further camera/layout work needs
   separate review of navigation and visibility; blindly enlarging art beyond
   collision geometry would make interactions misleading.

## 5. Validation, performance and warnings

Final full suite: **1,958 passed in 88.64s**. One known warning:
`no fast renderer available` from the dummy-display path at `main_window.py:212`.
See [full-suite.log](full-suite.log). This includes visibility, camera/input,
gameplay/save and bounded-effect regressions. Renderer-focused checks passed 53;
independent new visibility checks passed 12; these counts overlap the full suite.

Drive-hosted dependency reads repeatedly stalled during preparation. Validation
used a disposable local APFS virtual environment with the exact same Python,
pygame/SDL and all 12 installed package versions. Project dependencies and launcher
environment were not altered. [Environment record](validation-environment.json).
The source of the Drive delays was not established; validation succeeded against
the canonical project source/assets after moving only the dependency environment.

The event-driven launch → mine → collect → dock → sell trip collected three iron
and earned **80 → 110 CR**. Further earned sorties unlocked Sector 2; visible-target
combat earned a 70 CR bounty, banked **190 → 260 CR**, then verified the checkpoint.
No saved campaign was injected to unlock it. The final matrix retains 24 matched
EN/DE frames across 720p/1080p and three zooms, four navigation frames, two targeted
offscreen 4K originals and 11 earned/menu frames, with no detected layout warnings.

Short recordings: [mining trip — 6.4 seconds](final/earned-mining-trip.mp4) and
[combat — 6.7 seconds](final/earned-combat.mp4). These are actual 1920×1080 SDL
dummy framebuffers driven by automated input, 60 Hz simulation sampled at 30 fps,
with one second of final menu freeze. Audio is off. Intermediate progression
sorties are omitted between the two separate clips. They are not native desktop
video or physical controls/audio acceptance. [Full evidence record](final/report.json).

Clean offscreen draw medians (normal/heavy): 720p **4.05/4.10 ms**, 1080p
**2.47/3.09 ms**, 1440p **4.74/5.00 ms**, 4K output **6.39/7.27 ms**. The 4K normal
sample had two of 120 frames over 16.67 ms, including **103.89 ms** maximum.
The cause of that outlier is unestablished; these samples do not prove locked
60 fps. The heavy fixture includes beam/thrust and 96 projectiles; separate
transient-cap timing is reported by QA. One initial timing run overlapped a
0.35-second comparison export and was replaced by the uncontended run.

The separate [effect-cap stress](final/effect-cap-stress.json) fills 96 decorative
shards, 32 flashes and eight destruction bursts alongside 96 projectiles.
Across 480 offscreen draws none exceeded 16.67 ms; medians were **3.60 ms at
1080p**, **5.37 ms at 1440p** and **7.50 ms at 4K output**. Light cache reached
26 entries/512,584 bytes, within its cap. This is an injected stress fixture,
separate from the earned route and native performance sample.

Native Cocoa graphics passed windowed → fullscreen → returned, restoring desktop
modes. Fullscreen window: **3440×1440**; saved drawing surface: **1920×1080**.
Six normal/heavy phases measured render/flip medians **5.22–6.73 ms**; an isolated
windowed-heavy paced interval reached **81.89 ms**, while render/flip maximum in
that phase was 12.56 ms. No runtime warning/error appeared in final capture,
benchmark or native logs. [Native report](native/report.json), [native log](native.log).
The probe used isolated persistence and dummy audio, closed its own window, and
did not operate the user's physical controls or alter their running game.

## 6. Resolution and remaining acceptance

The internal world drawing surface remains **1920×1080**. Offscreen 3840×2160 output
scales that world surface; native desktop fullscreen also uses the existing SDL
backbuffer. This pass does not implement native 4K world rendering.

- Native 4K world rendering: **unimplemented**.
- Physical mouse/keyboard controls and audio acceptance: **unverified**.
- Serge's visual/artwork/lighting acceptance: **open**.
- Camera and gameplay balance acceptance are not implied by a visual review.
- New raster assets remain reusable originals, not editable layered 3D scenes.

## 7. Launch instructions

After saving at the station, close the previous game process and reopen
`Open Dust to Dominion.command` from the project folder. Select **Continue** and
**Launch / Sector 1**. Wheel or +/− selects 1×/1.5×/2×; Home selects the overview.
Space mines; left click fires outside the station shield. The existing user's
save and settings are not test fixtures.
