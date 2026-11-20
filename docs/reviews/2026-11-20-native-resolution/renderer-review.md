# Native campaign renderer implementation review

## 1. Scope and coordinate contract

The campaign now draws into the supplied output surface itself. There is no
completed 1920×1080 world image enlarged to the output. `NativeDraw` converts
logical UI positions, panels, brackets, markers, clipping and stroke widths at
the drawing boundary. `RenderCamera` composes the same output factor with the
existing logical camera for asteroid art, mineral pickups, mining contact,
projectiles, fragments and damage effects. Ships, station and fleet previews
receive final native positions and sizes. The native text layer still wraps and
places labels in logical coordinates, then rasterizes at output font size.

The lead's display change provides exact 16:9 backing sizes; on a 3440×1440
desktop this is 2560×1440 content with aspect bars. Model coordinates, hitboxes,
ordinary input conversion, pending click-world aim, camera framing, economy, audio and
save data are unchanged. No assets or dependencies changed.

## 2. Source detail and fallback

World artwork retains original source surfaces shared with ResourceLoader.
Preload computes visible bounds and a circle-fit diameter, rather than making
a fixed 512px normalized bitmap. Each cached transformation samples the original
crop directly at its final display size. Rotation still uses bounded two-degree
buckets; contour widths use output scale, and the same circular visual footprint
is enforced. Distant decorative pieces also sample the original source at their
native target size. Station vector fallback now accepts a radius and draws
geometry directly; it no longer enlarges a 200px fallback bitmap.

This preserves available detail; it does not create additional material detail,
remove baked lighting or turn the raster artwork into a 3D renderer.

## 3. Memory bounds

- World/panel transform LRU: at most 128 entries and 33,554,432 bytes (32 MiB).
- Effect lights: at most 64 entries and 2 MiB. The prior 64-design-pixel footprint
  cap becomes 128 output pixels at 4K, with an absolute 256px allocation cap.
- Separate single native backdrop: 33,177,600 bytes at 3840×2160. This prevents
  one full-size background from evicting the world transform cache every frame.
- Separate optional modal shade: another 33,177,600 bytes at 4K.
- Single current-zoom shield: at most 1762×1762×4 = 12,418,576 bytes at 4K/2×.
- These buffers are replaced on output-size changes; shield changes replace its
  previous zoom allocation. The output display surface is additional memory.
- Measured 19 decoded source surfaces total 113,228,712 bytes, shared with the
  loader in production. Tiny overview debris thumbnails total 6,200 bytes.

The 32 MiB figure is a transform-cache budget, not total process memory. Native
fonts, widgets, asset decoding temporaries and SDL resources are additional.

## 4. Verification at renderer freeze

185 focused cases passed in 30.91 seconds across native rendering, sprite,
lighting, presentation, indicators, camera acceptance, campaign screen and
art/lighting acceptance suites. New native tests cover four output factors and
three zooms; original-source-to-native sampling; stable cached output and source
purity; native vector fallback; direct primitive positions/stroke widths;
current-size buffer replacement; and equivalent light footprint at 4K.

One pre-existing indicator spy needed to forward the new optional `draw` keyword.
Its behavior assertions remain unchanged. The rival contour witness now compares
identical artwork through the unoutlined hauler path, avoiding assumptions about
how source images are stored.

Independent final images, earned routes, full-suite results and normal/heavy
frame timings belong to the QA report. They were pending when this note was
written. Physical 4K hardware and new-build visual acceptance are not implied by
offscreen 3840×2160 output. A native probe subsequently reproduced a stationary-pointer transition defect:
queued motion retained old backing coordinates after SDL applied the new aspect
bars. The active screen now receives `display_changed()` after a successful
app-level toggle. Campaign refreshes the current cursor/aim from SDL immediately
and once after the next event batch (including early-return paths). It does not
change captured pending click-world aim, and ordinary frames remain event-driven.
Three added regressions cover the observed stale motion, pending-click preservation,
no ordinary polling, and escape/focus-loss settlement. Independent native confirmation
of this correction remains part of the final QA gate.
