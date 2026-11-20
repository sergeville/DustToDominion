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
4K captures are not proof of a native4K display or 4K source detail.
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
