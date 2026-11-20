# Artwork and lighting review

Status: **final still-image review passed for this incremental upgrade**. No
blocking visual regression was found in the inspected evidence. This is the art
agent's read-only assessment, not independent gameplay or human acceptance.

## Inspected evidence

Compared retained `baseline/mining.png` and `baseline/combat.png` with final
English 1920×1080 mining/combat frames at default 1.5× zoom and the corresponding
areas of `../../concepts/realistic-visual-target-2026-11-20.png`. Reviewed the four
before/after and reference comparison boards. The baseline is retained prior
camera evidence, not a newly executed baseline.

Reviewed all four final EN/DE 720p/1080p contact sheets, covering 24 matched
mining/combat views at 1×, 1.5× and 2×; all four navigation stress originals;
both targeted English 3840×2160 default-zoom originals; and all eleven earned
trip/combat/menu originals in `final/`. The two MP4s were not watched in this
review, so motion smoothness and effect timing are not visually accepted here.

## Findings

Asteroid silhouette variety and broad mineral faces are a clear improvement.
Iron, gold and crystal now have more distinct shapes and material groups.
Station steel, cyan glazing and dark recesses remain separated at actual play
size. Removing the player's dark disk and repeated mining-range circles reduces
clutter. The Prospector material improvement itself is modest.

The earned `trip-mining.png` shows the beam terminating on the visible right
edge of the rock, with a local glow and small warm chips. The matched final iron
frames also place the contact on the silhouette. `combat-firing.png` visibly
shows player and hostile projectiles; `combat-defeated-rival.png` shows a warm
destruction flash after the rival disappears. These are useful visual cues.
The reviewed stills do not independently establish contact accuracy across every
concave gold rotation; that remains the renderer's automated-test evidence.

No clear new clipping, label collision or localization regression was visible.
Navigation chips clear the player and visible rival in all four stress captures.
Station and fleet menus remain readable. The dock banner remains a shallow crop
of the ship and bay, an existing composition limitation rather than a new fault.

## Largest remaining differences from the reference

1. **Composition and scale:** the playable scene has much more empty space and
   proportionally smaller actors than the reference. Decorative depth is subtle,
   and repeated silhouettes remain visible. The current geometry and camera
   contract intentionally constrain this pass.
2. **Lighting and ship treatment:** cyan/red contours improve identification but
   read as selection outlines rather than natural illumination, especially over
   rocks. Hull highlights are baked and rotate with sprites; the result is not
   physically relit material. The original reference has stronger directional
   metal reflections and brighter cockpit/exhaust contrast.
3. **Effects and detail:** mining spray remains sparse and destruction uses a
   visibly stylized ring/starburst. Projectiles are clear but less luminous and
   less integrated into the scene than the reference. At 4K output, enlarged
   edges and texture softness remain visible because the world is drawn at
   logical 1080p; this is not native 4K world detail.

## Acceptance boundary

Keep the source freeze: the inspected final stills support shipping this scoped
visual improvement, not claiming reference parity. Performance, physical
input/audio, save preservation, native fullscreen and human artistic acceptance
require their own evidence. This review neither reran those checks nor changed
product code or artwork.
