---
description: Improve campaign ship detail, mining feedback and contextual flight guidance without changing the economy or save format.
status: proposed
---
# Flight readability and feedback

## Scope

This iteration follows Serge's request to continue improving and show the game.
The existing complete small campaign is retained. Improve the player's ability
to identify ships, see mining activity and know what to do next. Use original
procedural vector drawing and existing fonts; no new dependencies or art assets.
This is an arcade presentation improvement, not realistic spacecraft physics.

## Design

- Use consistent detailed hulls for the Prospector, Hauler, Refinery and hostile
  ship. Distinguish silhouette, hull plates, cockpit and engine assemblies.
  Reuse the Prospector design in flight and the Fleet view. Supports remain passive.
- Give the station recognizable docking architecture and asteroids internal
  facets/craters/ore markings while preserving the modeled positions and radii.
- Show engine thrust only for movement input during active flight. Show the
  actual nearest mining target within range, its range ring/beam while mining,
  and visible mining progress. Animation follows simulation time and freezes on
  pause; drawing must not change model state or consume gameplay randomness.
- Contextual flight guidance distinguishes docking a loaded/damaged ship,
  returning with full cargo, collecting loose ore, mining an in-range rock,
  approaching the nearest rock, and returning when the field is depleted.
  A fresh launch must guide the player toward mining instead of immediately
  encouraging docking. Controls remain visible and messages are localized EN/DE.
- Display a direction/distance cue to the current helpful target, avoiding HUD
  overlaps. Guidance is advisory and must not alter movement, rewards or saves.

## Configuration

No new settings. Existing resolutions, fonts, localization and campaign.json v1
remain supported. Visuals use the existing 1920x1080 logical coordinate space.

## Acceptance criteria

- Ships have distinct visible hull/cockpit/engine details in flight and Fleet.
- Mining target, progress and movement feedback reflect actual model/input state.
- A fresh launch points toward ore; full cargo directs the player to dock;
  depleted fields do not leave the player looking for nonexistent asteroids.
- Context selection is deterministic, read-only and covered at boundary cases.
- EN/DE layouts work at 1280x720, 1920x1080 and 2560x1440.
- Existing earned progression/save/combat tests continue to pass.
- Save screenshots and a review report; open updated build for Serge. Native
  interaction and human enjoyment are only claimed when actually observed.

## Testing

Test guidance priority and empty/in-range/full-cargo/damaged states, target
selection, pure drawing, pause animation and reused vessel rendering. Render
all supported sizes/locales with real fonts and review screenshots. Run full
suite and independent review before local commit. Preserve user drafts/saves.

## Dev plan

1. Add this spec before product edits; extend spec 19 with reference to this
   presentation iteration.
2. Implement reusable procedural art and contextual feedback, then tests.
3. Render/check layouts, run regression suite and independent review.
4. Save evidence and update team handoff; commit locally only. Keep proposed
   until native visual/play acceptance has been recorded.
