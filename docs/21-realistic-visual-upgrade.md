---
description: Replace campaign presentation with reusable textured assets while preserving the tested simulation and version-one saves.
status: proposed
---
# Realistic visual upgrade

## Baseline and scope

Baseline local revision: 97cc41a, feature/complete-small-game. No tracked dirty
files; existing untracked drafts and screenshots are excluded from this work.
Source request: [team prompt](DustToDominion_Realistic_Visuals_Team_Prompt.md),
supplied 2026-11-20 and moved into docs by Serge during implementation.
Visual reference: concepts/realistic-visual-target-2026-11-20.png (1672x941).
The reference is direction, never a flattened runtime scene or sprite source.
Supersedes spec20's vector-only presentation restriction, retaining its guidance.
Gameplay, prices, shield, mining selection, hitboxes, passive support bonuses,
crew effects, progression and campaign.json v1 remain unchanged.

## Asset and renderer contract

- Existing pygame engine; 1920x1080 logical world, near-overhead orthographic
  sprites. Ship source points UP; public drawing heading remains radians along
  +X, adapted only by renderer. Center pivot, no baked exhaust or HUD text.
- Standalone square transparent PNGs, isolated centered subjects and transparent
  margins. Sources retained in assets/source/realistic; runtime exports in
  resources/campaign/realistic. Record generation prompts, source hashes,
  export dimensions and provenance in assets/source/realistic/manifest.json.
  Do not claim layered or 3D sources where only raster originals exist.
- Names: prospector, hauler, refinery, rival, station, asteroid_iron,
  asteroid_gold, asteroid_crystal, miner, engineer, dock, background,
  asteroid_iron_b. PNG suffix. Alternate iron form is selected by stable ID;
  it changes no rock radius or simulation state.
- World sizes: ships diameter 2*existing size; station diameter200; rocks
  diameter2*modeled radius. Portraits/dock only in panels. Sprite silhouette
  never changes simulation collision/range. Center is origin; ship muzzle
  forward at size*.85; engines aft at -.7*size with lateral .4*size offsets.
- Restrained neutral overhead fill and local ambient occlusion; mild baked
  highlights rotate with hulls, an explicit 2D compromise. Worn steel,
  cyan friendly lights, amber industry and ore, red rival accents.
- Reuse ResourceLoader decoded images and configured overrides; prepare
  presentation copies during screen construction, never during draw. Missing or
  unusable surfaces fall back to existing vectors. Spec03 still rejects corrupt
  PNG/package data at startup, before screen creation; the renderer cannot
  bypass that application-wide rule. Direct-file renderer tests also exercise
  corrupt-file fallback. Bounded transform cache (128
  entries, 32MiB maximum); quantized angles and sizes. No model mutation or
  shared gameplay RNG use; time comes from simulation-owned visual clock.
- Effects are bounded analytic draws: narrow cyan mining core/contact sparks,
  exhaust, ore glints and projectile streaks; no unbounded particle population.
- HUD remains dynamic/localized with existing selected fonts, meaningful disabled
  states, real values, and ship/target markers. COLLECT ORE may coincide with
  cutting because loose fragments exist; explain next action rather than change
  selection or suppress truthful progress.

## Ownership

Lead: this plan, shared screens/campaign.py, campaign_effects.py, integration,
UI tests, locale strings and handoff.
Art agent: assets/source/realistic and resources/campaign/realistic only.
Renderer agent: src/dtd/campaign_sprites.py and tests/test_campaign_sprites.py.
Independent QA: docs/reviews/visual_upgrade_validation.py,
tests/test_visual_upgrade_acceptance.py and docs/reviews/2026-11-20-realistic/.
No agent writes another owner's files; no pushes or user-save mutations.

## Dev plan

1. Record baseline, inspect instructions/runtime, settle this contract.
2. Generate Prospector, iron asteroid and station first; integrate renderer,
   effects and HUD. Complete input-driven launch/mine/collect/dock/sell with
   isolated persistence and actual rendered captures before expansion.
3. After slice passes, create remaining ships/materials, portraits and dock
   artwork; improve station/fleet UI without changing mechanics.
4. Capture EN/DE states at 720p/1080p/1440p and offscreen2160p. Compare normal
   and effect-heavy timings, cache bounds and memory against baseline.
5. Independent review, full regression, native attempt, exact evidence and
   remaining limitations, local commit and launch instructions.

## Configuration

No dependencies, settings, save migration or engine change. Native fullscreen
continues to use desktop resolution with proportional letterboxing. Offscreen
4K captures are not proof of a native 4K display or 4K source detail.
Campaign labels render at the supplied output surface resolution, retaining
logical sizes/wrapping and selected fonts. A transient text layer is cleared
under modal overlays; widgets already render at output scale. SDL's fullscreen
logical backbuffer remains1920x1080, so native fullscreen still scales that
backbuffer; this differs from a direct3840x2160 offscreen render.

## Acceptance criteria

One earned mining trip precedes expansion. All four ships have readable distinct
textured silhouettes; all mineral types differ in form; station has an industrial
bay and four modules; crew/dock art appears in real UI. Dynamic values remain
readable EN/DE and source assets are retained. Existing earned campaign victory,
combat, defeat, saves, focus/pause, clicks and display behavior continue to pass.
Independent fidelity assessment classifies each target met/partial/missing.
Native interaction and performance remain unverified unless actually exercised.

## Testing

Run full pytest baseline/final, renderer tests for fallbacks, heading, bounds,
cache ceiling, purity, missing resources and no disk IO during drawing.
Run input-driven mining and earned progression acceptance, save/error routes,
resolution/localization capture matrix and offscreen timing distributions.
Use only isolated persistence. Keep actual-runtime and synthetic-state evidence
distinct; measure startup/cache warmup separately from steady frames. Document
hardware, driver, resolution, p50/p95/max, memory and limitations. Keep proposed
until native play and visual acceptance are recorded.

## Implementation evidence — 2026-11-20

Implemented locally at `6566c42`; kept proposed until the native play and human
visual acceptance criteria above are satisfied. All 13 assets, bounded rendering,
effects and station/fleet integration are present. The first textured three-asset
mining trip passed before expansion; the final trip passed again. Independent
regression: 1,841 passed. All 64 bilingual layout captures were reviewed.
Native Cocoa rendering switched 1920x1080 windowed to 3440x1440 fullscreen and
back without changing monitor modes. Physical input and audio remain unverified.

See the [current report](reviews/2026-11-20-realistic.md) for evidence, source
provenance, performance costs and exact remaining visual compromises.

## Amendment — 2026-11-20: readability and reference comparison

User authorized continuing with the same team, preserving gameplay and saves.
Baseline is product `6566c42` with documentation `c991a1a`. Existing raster assets are
retained; this pass improves their presentation rather than changing the engine.

### Dev plan

1. Retain four-view EN/DE baseline captures and inspect the actual screenshots
   against the supplied reference before product edits.
2. Place localized world labels outside player/rival hulls, visible health bars,
   HUD and other labels. Keep CUT progress visible; use backed text and a leader
   when moved. Prefer nearby placements before a distance-ordered field search;
   bars must remain associated with their ships in ordinary scenes. Add a dark separation edge, red rim and open brackets to rival
   presentation, without enlarging hitboxes or changing targeting.
3. Replace the opaque station shield disk with a faint transparent field and
   readable boundaries. Add restrained distant debris/depth without introducing
   mineable-looking large objects. Make docking art a broad shared station panel
   and enlarge fleet display hulls within their cards; keep all actions accessible.
4. Test real font bounds, ship/rock overlap, edges, no model/RNG/save mutation,
   resource fallback, bounded caches and draw determinism. Capture mining,
   combat, station and fleet at 720p/1080p/1440p/offscreen 3840x2160 in EN/DE.
5. Independent QA reviews changes and reference fidelity; run affected and full
   regression checks once stable. Repeat native graphics probe separately from
   offscreen rendering, retaining warnings and exact framebuffer/window sizes.

### Acceptance and limits

Label/bar placement and rival silhouettes must be readable in the reproduced
problem scenes and edge fixtures. The shield must retain its exact safety radius
while allowing the backdrop to show through. Decorative debris has no collision,
pickups or gameplay state. Fleet display size changes do not affect flight size.
Station layout may move widgets but not change callbacks/prices/save behavior.
All source artwork remains unmodified and provenance stays accurate.

The world canvas remains 1920x1080: 3840x2160 captures verify output, font rendering
and layout, not native 4K world detail. Native main-monitor fullscreen must report
window and backbuffer separately. Physical input, audio, balance and final art
acceptance remain separate from automated and native graphics evidence.


### Polish validation — 2026-11-20

Local product `957e96b`, test refinement `a61e8d6`: 1,860 tests passed. Independent
QA reproduced the original collisions/contrast failures, caught and verified the
nearby-bar correction, and reviewed all 32 updated EN/DE four-view captures.
The earned trip again sold three iron (80→110 credits). Art review passed this
scoped comparison; distant framing, baked lighting and prominent HUD remain.
Native Cocoa graphics passed 3440×1440 fullscreen with a 1920×1080 backbuffer;
offscreen 3840×2160 checks verify output-size fonts and layout with scaled world
art. Physical input/audio/human acceptance and native 4K remain unverified.
See the [polish report](reviews/2026-11-20-realistic-polish.md) for warnings,
timings, screenshots, source hashes and reproduction commands. Proposed status
is retained pending the original native play and human acceptance criteria.

## Amendment — 2026-11-20: gameplay camera and navigation

Serge authorized implementation of the [camera review](reviews/2026-11-20-reference-comparison/review.md)
using the existing team. Baseline product is `957e96b`; current HEAD `b268b1a`
contains documentation only after the polish/test refinements. Prior uncommitted
comparison documents are preserved and may be included in this local handoff.
This amendment replaces the identity-only flight presentation; the simulation,
asset originals, economy, combat rules and campaign v1 serialization stay intact.

### Configuration and interaction

- Session-only zoom levels **1× overview, 1.5× default, 2× close**. New campaign
  screens start at 1.5×. Retain the selected level across trips in that screen;
  no save/config migration and no dependency changes.
- Mouse wheel and `-` / `=` (including shifted plus/keypad equivalents) step zoom;
  `Home` selects 1× overview. Controls apply only in flight. Existing arrows,
  WASD, Space, mouse fire, E and Escape keep their meanings. Show localized zoom
  instructions/current level in screen space without covering the world or HUD.
- Camera follows the player without interpolation lag and clamps to the existing
  arena presentation bounds. At 1× it is an identity overview. Reachable world
  edges remain inside the flight viewport; HUD occupies its existing margins.
  Do not move world entities to improve their composition.

### Transform and input contract

One camera owns forward and inverse mappings:
`view = viewport_center + zoom * (world - camera_center)`;
`world = camera_center + (view - viewport_center) / zoom`.
Use it consistently for ships, rocks, station, projectiles, pickups, mining beam,
thrust/impact effects, safe/dock/mining circles and target/direction anchors.
World extents/radii scale with zoom; labels, health bars and UI retain readable
screen sizes after projecting their anchors. Cull/clip world drawing at the
flight viewport. Sprite sources are sampled at projected size, not by enlarging
a finished world framebuffer. Decorative world debris uses the same projection;
background atmosphere may remain screen-aligned. No model/RNG mutation by drawing.

`current_scale().mouse()` converts incoming window coordinates into logical view
space once. SDL `SCALED` already supplies logical display coordinates in desktop
fullscreen; no second physical-window inverse is permitted. Store cursor in view
space and recompute world aim whenever the camera/zoom changes, including every
simulation step with a stationary cursor. An already released quick tap retains
its click-time world aim until consumed; held firing uses current cursor aim.
Preserve cooldown, focus/pause and pending-shot clearing. Menus remain screen space.

### Navigation and visibility

Offscreen station and live rival centers receive bounded, localized directional
edge indicators and true world distances. Prioritize the station and nearest
threats, with an explicit extra-threat count if any are aggregated. Distinguish
friendly cyan from hostile red; prevent marker/label collisions and HUD clipping.
Suppress edge markers for on-screen centers. Keep the existing next-action/mining
and docking guidance meaningful after transformation; a closer camera must not
hide how to return home. No enemy/weapon range change to compensate for cropping.

### Ownership and shared-file rule

This amendment supersedes the earlier pass ownership during camera work:
renderer owns `campaign_camera.py`, world/effect/sprite projection and exclusive
`screens/campaign.py` integration plus its camera tests. UI (existing art agent)
owns separate `camera_indicators.py`, its tests and locale keys. UI communicates
an explicit call contract to renderer and does not edit the shared screen.
Lead owns the canonical plan, documentation, integration review and handoff;
independent QA owns separate acceptance tests and camera evidence scripts.
Any shared-file handoff must be explicit before another agent writes it.

### Dev plan — camera pass

1. Record baseline source/image hashes and matching-output mining/combat captures;
   review the camera/UI API and this amendment before product edits. **Completed 2026-11-20.**
2. Implement camera, consistent world projection and inverse cursor mapping;
   integrate UI-owned navigation indicators and zoom instructions. **Completed 2026-11-20.**
3. Complete an isolated input-driven launch → mine → collect → dock → sell trip,
   then earned combat validation. Do not seed cargo/credits to claim earned play. **Completed 2026-11-20.**
4. Independent QA checks transforms, stationary aiming, taps/held fire,
   output resizing, fullscreen scaling, all zooms, boundaries, docking, combat,
   save/model invariants and readable EN/DE layouts. Run affected and full tests. **Completed 2026-11-20.**
5. Capture matched before/after gameplay views, inspect actual images, run a
   separate native window/fullscreen graphics probe and record warnings and
   performance. Review before local commit; provide launch/zoom instructions.
   Human visual acceptance stays open, so spec status remains proposed. **Completed 2026-11-20 (camera implementation and evidence only).**

### Testing and acceptance criteria

Camera round trips and visible bounds must hold at each level and arena edge.
Aiming must align with projected targets at 720p/1080p/1440p/offscreen2160p, after
window/fullscreen transitions and during player motion without mouse motion.
Effects/markers track the same actors; screen-space controls remain usable.
Tests must demonstrate no gameplay geometry/model/save changes and preserve
existing earned campaign, safety, quick-click, pause/focus and serialization tests.
Independent regression includes a full event-driven mining trip and earned combat,
with actual captures, exact source hashes and synthetic versus native provenance.
No user save is a fixture. A native graphics probe does not establish physical
mouse/audio acceptance. Report failures and unverified behavior explicitly.

### Internal rendering resolution and remaining scope

The logical world drawing target remains **1920×1080**, now drawing projected
sprites directly for the selected camera zoom. Offscreen 3840×2160 output still
scales that world canvas, with output-size text; native SDL fullscreen still
scales its 1920×1080 display backbuffer to the desktop window. **Native 4K world
rendering remains a separate task.** This pass does not replace artwork or claim
the reference's lighting, fracture effects or cinematic station-menu composition.

### Camera verification checkpoint — 2026-11-20

Full suite: **1,928 passed, one known dummy-renderer warning**. Independent camera
math/aim checks and the continuous earned mining-trip/combat route passed. Saved
48 matching mining/combat, eight navigation and 11 earned/menu originals, with
source/image hashes and separate native Cocoa window/fullscreen/window evidence.
Native desktop window 3440×1440 still uses a 1920×1080 backbuffer. Model, save
serialization, world ranges and dependencies remain unchanged.

[Camera report and launch instructions](reviews/2026-11-20-camera/review.md),
[QA review](reviews/2026-11-20-camera/independent-review.md) and
[UI/art review](reviews/2026-11-20-camera/art-review.md) distinguish completed
camera work from physical input/audio, artwork/lighting judgment, human visual
acceptance and native 4K world rendering. Serge explicitly separated framing
improvement from artwork/lighting acceptance; neither is implicitly approved by
this camera pass. Specification status remains proposed for those open gates.

## Amendment — 2026-11-20: artwork, lighting and restrained targeting

Serge authorized the existing team to implement an artwork/lighting pass after
camera commit `0525164`. This is a presentation-only amendment. The implemented
camera and inverse input mapping, model geometry/ranges/collisions, economy,
combat/safety rules, save schema and user saves remain unchanged. Native 4K world
rendering is **unimplemented** and physical controls/audio acceptance is
**unverified**; neither is closed by this pass or by an automated recording.

### Asset and rendering contract

- Create varied, identifiable asteroid silhouettes with readable iron/gold/crystal
  materials inspired by the supplied realistic reference. Stable identity chooses
  variants without consuming simulation randomness. Render inside existing bounds;
  decorative irregularity never changes collision geometry.
- Improve the prospector/rival and station metal, panel separation and emissive
  accents at actual gameplay sizes. Preserve overhead orientation, friendly/hostile
  distinction and clear silhouettes. Retain reusable originals, generated alpha,
  prompts, hashes and derivation steps. No generated screenshot substitutes for
  actual game evidence; no source assets discarded.
- Replace the opaque circular player backing with a subtle hull-shaped readability
  treatment. Preserve readability against rocks/station without a solid disc or
  bright full-body flash. Missing-asset fallback must remain usable.
- Improve mining contact light, bounded fragments, thrusters and hit/destruction
  effects. Effects use supplied simulation time, project through the existing camera,
  do not mutate models/RNG, and remain capped in lifetime, count and cache memory.
  Transient illumination is a 2D approximation; do not claim dynamic physical lighting.
  Contact follows the actual transformed rock alpha (at most 512 samples), with a
  geometric fallback for missing artwork. Light cache ≤64 entries/2 MiB; mining
  fragments ≤96/one-second lifetime; destruction bursts ≤8 groups/0.65 seconds.
  Existing transform cache remains ≤128 entries/32 MiB and hit flashes ≤32/0.32 seconds.
- Reduce redundant full range rings and repeated brackets. Preserve exact safe-zone
  boundary information, docking cues, current mining target/progress, rival identity,
  mouse crosshair and offscreen station/threat navigation. HUD remains screen space.

### Configuration and ownership

No new dependencies, persistent settings or save fields. Presentation constants
remain centralized where practical. Retain the 1×/1.5×/2× camera and 1.5× default.
Art agent owns new asset/source files and provenance; renderer owns sprite/effects
modules and their tests. Lead acts as UI owner for `screens/campaign.py`, range and
bracket treatment, resource integration, canonical docs and handoff. Shared-file
handoffs are explicit. Independent QA owns separate acceptance/evidence files.

### Dev plan — artwork and lighting pass

1. Save matching baseline mining/combat frames and source hashes; agree ownership
   and amend this canonical plan before modifying consumed assets/product code.
   **Completed:** preserved exact prior-camera frames and source inventory before
   edits; later re-read of all 38 files verified only the three intended presentation
   modules changed.
2. Generate and inspect reusable art, integrate bounded sprite/effects improvements,
   then reduce UI visual weight while keeping navigation and target information.
   **Completed:** six additional source/export pairs, alpha-shaped hull separation,
   alpha-aware mining contact, bounded effects and restrained overlays.
3. Run an isolated earned launch → mine → collect → dock → sell trip, then combat.
   Capture actual renderer before/after frames at matching sizes and compare with
   corresponding reference panels. Produce a short actual gameplay recording if
   an available encoder permits it; label automation, output/internal resolution,
   frame cadence and audio honestly.
   **Completed:** earned 80→110 CR trip and 70 CR combat bounty, matched comparison
   sheets and two silent 1080p/30fps automated gameplay clips retained.
4. Independently verify visibility, camera/input invariants, affected gameplay,
   bounded effects and performance; run affected and full checks. Review source
   hashes, warnings and evidence before local commit/handoff. Keep visual acceptance
   open for Serge and list unfinished work explicitly.
   **Completed:** independent QA passed 1,958 tests, earned routes, 41 final image
   originals and two decoded recordings; native graphics and separate effect-cap
   timing passed. All final source/resource/evidence hashes were verified.

### Testing and acceptance criteria

- Original model/store/camera/input math and gameplay values are unchanged; existing
  mining, combat, quick-tap, stationary-cursor, zoom/resize/fullscreen and save
  regressions pass. Tests use isolated persistence only.
- Representative asteroid variants have distinct silhouettes and readable ore
  materials at 1×/1.5×/2×. Ship contour treatment follows alpha rather than painting
  a filled circle; friendly and rival ships remain visible against rock/station.
- Range/target cues retain correct projected positions and essential meanings with
  less visual clutter; labels/bars/edge chips remain unobscured in EN/DE fixtures.
- Effects are deterministic presentation data, bounded under sustained use, correctly
  camera-mapped and isolated from gameplay. Missing artwork remains nonfatal.
- Compare actual renderer output to baseline/reference, review the largest remaining
  gaps and report normal/heavy frame timings and warnings. Native window dimensions,
  internal 1920×1080 world drawing and offscreen output dimensions remain distinct.
- A short event-driven recording demonstrates the running renderer but cannot prove
  physical controls, audio quality or human visual acceptance. Do not mark the spec
  active while those applicable human acceptance gates remain open.

### Artwork and lighting result — 2026-11-20

Implementation and independent technical QA are complete for this pass. See the
[current report](reviews/2026-11-20-art-lighting/review.md) for matching before/after
and reference panels, earned recordings, exact provenance, performance outliers
and launch instructions. The internal world remains 1920×1080; native fullscreen
was verified at a 3440×1440 window using that backbuffer. Offscreen 3840×2160 images
are scaled-world evidence. Native 4K world rendering is unimplemented, physical
controls/audio are unverified and Serge's visual acceptance remains open. Sparse
composition, prominent hull contours, repeated/baked materials and stylized effects
remain visible differences from the target. This spec remains proposed for those
human acceptance gates; no reference-fidelity approval is implied.


## Amendment — 2026-11-20: native-resolution drawing

Serge authorized this milestone after confirming baseline native controls and
several audio cues. This amendment supersedes earlier fixed-1080p rendering
limitations, not their historical evidence. Visual acceptance remains open.

### Configuration and rendering contract

Keep the 1920x1080 logical layout, camera and simulation geometry. Fullscreen
uses spec 02's largest exact 16:9 backing fitting the desktop, with SDL retaining
aspect bars and mapping mouse events to backing pixels. Render world sprites,
primitives, lights, effects, indicators, station/fleet art and text directly at
that target resolution; do not upscale a completed 1080p scene. Compose one
output scale at the drawing boundary with the existing logical camera. Input
uses current_scale().mouse once, then the logical camera inverse. Recompute
stationary aiming on camera movement; retain correct cursor position across
mode changes without reinterpreting old pixel coordinates. A successful app-level
fullscreen toggle notifies the active screen. Campaign refreshes from SDL current
mouse state immediately and once after the next queued event batch, because native
SDL can deliver stale motion coordinates during the transition. This transition-only
refresh preserves any pending click-time world aim; ordinary frames remain event-driven. Preserve pending
click-time world aim. Preserve original source detail where available; raster
sources and baked lighting still limit fidelity. All caches remain bounded.
The sprite transform LRU remains at most 128 entries / 32 MiB. Separately retain
one native backdrop, one optional modal shade and one current-zoom shield,
replacing them on size changes rather than accumulating resolutions. At 4K each
full-screen 32-bit buffer is 31.64 MiB; the shield may add roughly 12 MiB. These
buffers and decoded source images are additional to the 32 MiB transform budget.

No new setting, dependency, save field or gameplay change. The native 3440x1440
window contains a 2560x1440 game area; it does not widen the world or stretch
hulls. A 3840x2160 surface can be tested offscreen but is not evidence of a
physical 4K monitor. Do not imply Retina pixel density without measuring it.

### Ownership and Dev plan

1. Lead amends specs 02/21 before code, retains frozen baseline evidence and owns
   main_window plus its tests. Renderer owns campaign drawing, sprite/effect
   projection, optional indicator draw boundary and renderer tests. QA owns
   independent acceptance/capture files. Shared-file handoffs are explicit.
2. Implement native backing selection, native campaign rasterization and
   source-resolution transforms. Keep gameplay/input/audio/model/save semantics.
3. QA verifies all zooms, stationary aim, mode transitions, earned mining trip,
   docking/selling/combat/reload, native graphics and performance. Capture
   matched baseline/final mining/combat and current station/fleet at native
   content dimensions and offscreen 4K. Run affected tests then full regression.
4. Record exact sizes, driver, warnings, timings, source revision and remaining
   limitations. Update manual acceptance with Serge's reported baseline checks;
   new-build physical input/listening and visual review remain separate.

### Testing and acceptance criteria

Tests must detect a hidden 1080p intermediate or fixed 512 source bottleneck;
verify native target sizes and correct primitive/sprite/effect projection,
clipping, logical layout, input inverse, bounded caches and draw purity. Existing
safety/ranges/economy/save/audio behavior must pass. Native probes use isolated
persistence and must not close or change Serge's running game. Report normal
and effect-heavy frame timings rather than assuming 4K meets 60 fps. Spec21 stays
proposed until Serge accepts the visuals.


### Implementation outcome

Native campaign drawing, original-source transforms, bounded buffers and
transition-safe pointer mapping are implemented. Independent regression passed
2,061 tests with one known dummy-display renderer warning. Both 2560×1440 and
3840×2160 automated earned mining/combat/checkpoint routes passed. Native Cocoa
measured 2560×1440 internal content at 1:1 pixels within the unchanged 3440×1440
desktop. The fixed stationary-pointer defect and complete evidence are recorded
in the [native review](reviews/2026-11-20-native-resolution/review.md).
Physical 4K/Retina checks and Serge’s new-build visual acceptance remain open;
this specification stays proposed for those broader visual acceptance gates.
