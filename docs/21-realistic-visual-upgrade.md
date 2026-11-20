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
