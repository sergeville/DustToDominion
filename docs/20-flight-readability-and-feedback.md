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


## Readability amendment — 2026-11-20

Serge approved a focused pass after reviewing native screenshots, then supplied
`goals.png` as the visual reference: industrial hulls, cyan lighting, a readable
docking bay and compact HUD. This pass improves identification and composition;
it does not claim to deliver the reference's painted textures or crew portraits.

- Move the modeled station center to (960, 750), so its 220-unit safety ring fits
  above the controls. Launch at (960, 595), outside the 110-unit docking circle
  but within the protected region. Docking now requires flying back to the ring.
  Model and rendering use the same positions; saves remain station-only v1.
- Draw a dark backing and bright segmented marker around the player, plus a
  localized YOUR SHIP label for the first six seconds of each expedition.
  The label timer resets per launch and pauses with the simulation.
- Replace the tiny target circle with clearly visible corner brackets outside
  the target silhouette. Gold identifies the guidance destination; cyan remains
  the mining beam. Approach guidance includes a local target/distance label and
  a directional arrow beside the ship. Return guidance marks the docking ring.
- Keep the established readable HUD fonts; remove excess panel padding. Header
  ends above the reachable ship, controls begin below its bottom-edge hull.
  Guidance/labels must stay outside the HUD and inside the canvas.
- Preserve progression, prices, mining selection, damage rules and save schema.
  The station/spawn geometry change is intentional and receives gameplay tests.

### Amendment testing and acceptance

Cover safe spawn outside docking range, visible station safety ring, actual
movement back to dock, harmless launch firing, player marker visibility at all
world corners, timer reset/pause, target bracket size/placement and guide text
in both locales. Re-run earned victory/combat/save acceptance. Render fresh,
mining, return and edge states at all three resolutions with real fonts; inspect
every generated fixture. Preserve the user's running session/checkpoint.

### Additional dev stages

5. Amend specs 19/20 before edits; implement station/spawn geometry, player
   identification, target guidance and compact HUD.
6. Validate gameplay regressions and rendered fixtures; save review/evidence,
   commit locally, and provide the updated build without discarding live play.
