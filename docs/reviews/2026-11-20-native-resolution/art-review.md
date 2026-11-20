# Native-resolution visual review

## 1. Verdict and scope

**Pass for the scoped still-image visual review.** No material new layout, sprite, indicator or clipping regression was observed. Human visual acceptance remains open; this is not a claim of visual parity with the concept reference.

Reviewed all four final EN/DE contact sheets covering mining/combat at three zooms, station, fleet and navigation at 2560 and 3840 widths; all eight matched English before/after originals; the German menu and navigation originals; all 22 event-earned originals in `final/earned-2560/` and `final/earned-3840/`; and `native/fullscreen-heavy.png`. Compared those with `../../concepts/realistic-visual-target-2026-11-20.png`. Capture provenance and source identity are recorded separately in `final/report.json` and the QA review.

## 2. Observed improvements and preservation

Native rasterization produces a visible detail improvement at both output sizes. Station braces and panel seams, asteroid facets and cavities, cockpit edges and fleet hull materials are crisper than the matched baseline. The dock panorama and portrait texture also retain more detail. Framing, relative actor size and the menu hierarchy remain stable; sharper assets do not create a new composition.

The reviewed English and German labels fit their panels. Navigation markers remain readable: the displaced station chip clears the nearby rival, and the right-edge threat chip stays within the flight area. Station and asteroid cropping at higher zoom is consistent with the camera framing. The mining beam reaches the target surface with visible contact chips. Earned frames show the cargo increase, docking result and sale feedback clearly; combat frames keep hostile markers and projectile colors distinguishable. Station feedback and fleet cards remain legible after those earned transitions.

The native heavy-effects capture retains sharp hull/rock detail and readable HUD text. Its regular projectile grid is a synthetic stress fixture, not an assessment of normal encounter composition.

## 3. Remaining differences from the reference

- The world still has broad empty areas, repeated rock forms and less foreground/background depth than the reference. Higher resolution exposes existing detail but does not solve sparse composition.
- Cyan and red contours still read primarily as identification outlines. Sprite highlights are baked into the artwork; the result does not reproduce the reference's directional material lighting.
- Projectiles, contact spray and destruction flashes remain visibly stylized. Their bars, bright tips and geometric burst shapes differ from the reference's cinematic sparks and debris.
- The station's shallow panorama retains its cropped foreground ship. Increased sharpness does not change that crop or provide the reference's expansive dock composition.

These are continuing art-direction limits, not blockers introduced by this native-resolution pass. The next useful visual step is user review of the running game at the preferred fullscreen size, before further composition or lighting changes.

## 4. Evidence limits

This review inspected saved images, not physical input, audio or motion on a 4K monitor. Native graphics execution, source identity, timing and gameplay assertions belong to the separate QA evidence. The reviewed 3840 images demonstrate that output raster; they do not establish a physical 4K display test or user acceptance.
