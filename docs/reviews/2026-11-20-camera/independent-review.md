# Independent camera validation — 2026-11-20

## 1. Verdict and provenance

**Pass for the scoped camera implementation and automated regression gate. Human visual and physical-input acceptance remains open.** No blocking defect remains in the inspected evidence. This is a closer, following view of the same simulation, not a new rendering engine or a claim that the reference's cinematic appearance has been reached.

The baseline was captured before camera source edits at `b268b1a979e38d6afe8920f4c3f5803152fe1049`. Its [report](baseline/report.json) records 36 source hashes and two actual 1920×1080 framebuffers. The [final report](final/report.json) records the same pre-commit Git HEAD and 38 hashes identifying the tested working tree, including the new camera and indicator modules. All 38 hashes were independently rechecked after the full suite and capture run. The Git HEAD alone does not identify this uncommitted implementation.

Matched mining/combat scenes restore the exact serialized baseline campaign and expedition values and assert equality. These are synthetic stress fixtures, including the rival over ore and stress projectiles. No actor was repositioned for the after image. The earned route below is separate and uses no injected progression. All drivers isolate persistence and leave the user's save and running game alone.

## 2. Independent functional and source review

The full suite passed **1,928 tests with one warning in 64.67 seconds**, as recorded in [full-suite.log](full-suite.log). The new independent acceptance file contains 30 cases. It derives the expected camera transform and inverse separately instead of validating the production inverse against itself.

- All three zoom levels at 1280×720, 1920×1080, 2560×1440 and offscreen 3840×2160: incoming pixel mapping, world aim and actual projectile direction.
- Stationary cursor while the player/camera moves, with held and unheld fire: actual per-step input uses the changing inverse transform.
- A released quick tap keeps its click-time world target after cursor, camera and zoom changes; it fires once. Held fire uses current cursor aim.
- Simulated SDL logical fullscreen mapping, followed by output changes, applies the inverse output scale once. This is a controlled test, not OS mouse-event verification.
- Earned travel to all four reachable corners at all zooms: visible pilot bounds, drawing purity, RNG purity and unchanged saved bytes.
- Session zoom survives docking and a later trip, does not operate on station menus, and resets with a new screen without entering the save schema.
- Integrated 2× station marker placement avoids the enlarged visible rival near the bottom edge.

Review covered the changed camera, screen input/update/draw, effect and sprite projection, indicator module and locale/control integration. The mathematical camera changes presentation; model positions, ranges, collision and progression remain in world units. Core model, store, guidance, display implementation and dependencies remain unchanged. Existing tests were migrated to projected geometry; the independently inspected migrations retain exact geometry checks or explicitly bounded pixel-quantization tolerances. The quick-click direction assertion now checks the recorded click target exactly rather than assuming rounded output pixels produce an exactly horizontal shot.

The UI reviewer found a real indicator defect during implementation: with player `(960,190)`, rival `(960,520)` and zoom 2×, the original station chip overlapped the projected rival by 11 pixels. Actor obstacles and final overlay ordering corrected it. The final integration test and [navigation fixture](final/en-us-1920-navigation-z2.png) verify the correction. The regression was added after the fix; it is not represented as an independently observed failing pre-fix test run.

## 3. Earned playable route

One continuous fresh campaign was operated through pygame events, including mouse aiming inside the visible flight viewport. The driver never assigned cargo, credits, unlocks or player positions to claim earned play.

1. Launch Sector 1, travel to ore, hold Space, collect three iron, return, dock and sell. Credits changed **80→110**, and checkpoint cargo/sale values matched.
2. Complete two more mining sorties, buy cargo and mining upgrades, earn **330 lifetime sales**, and unlock Sector 2.
3. Launch Sector 2, travel outside the shield, aim and fire at a visible rival, defeat it and dock. The bounty was **70 CR**, with banked credits **190→260**. Continue restored that checkpoint.

All 46 pressed/held firing aim samples were inside the viewport at logical `(609,234)`. The actual defeated-rival capture shows hull **86/100**, demonstrating that combat and damage continued while firing. Eleven retained originals include the complete first trip, combat approach/firing/defeat/docking, and station/fleet menus after Continue. See the `earned` section of [final/report.json](final/report.json) for hashes and values.

This proves the automated event route, not physical keyboard/mouse play or audio quality.

## 4. Visual inspection and resolution limits

The final matrix contains **48** matched originals (two scenes × three zoom levels × two languages × four outputs), **8** synthetic 2× navigation originals and **11** earned/menu originals. Eight contact sheets cover the matched matrix. The bounds scanner reported zero framebuffer, button or world-label/bar bounds/overlap warnings for the checked frames. This is finite fixture coverage, not proof that every possible composition is collision-free.

QA inspected all eight matrix contact sheets and targeted original text/readability frames. All 48 final matched PNGs were verified byte-identical to those inspected interim originals. QA also inspected every final earned/menu original, the final EN 1920 and DE 1280 navigation originals, and both before/after comparison sheets. The navigation fixture deliberately includes an offscreen station, an offscreen hostile and the visible rival that exposed the chip collision.

The default 1.5× view visibly increases ship, station, ore and effect size while keeping HUD text size stable. The 2× view provides closer detail; the 1× view restores the full arena. Fixed framing near arena edges and reduced peripheral view are expected trade-offs. Text and relocated labels remain readable in the reviewed outputs. Menus retain their existing structure and callbacks.

Remaining visual gaps are material: sparse composition, repeated ore shapes, baked lighting, conspicuous rings/brackets and the dark circular pilot backing. The shallow station panorama remains unchanged. These do not block the scoped camera work but prevent claiming parity with the reference.

The world canvas remains **1920×1080**. Zoom samples sprites directly at their projected sizes within that canvas; output resizing subsequently scales the canvas. Offscreen 3840×2160 captures have output-resolution text and enlarged world pixels. They are neither native 4K world rendering nor proof of physical 4K fullscreen. The rendered comparison sheets reduce both 1920×1080 originals equally and add headings; they are not native game framebuffers.

## 5. Performance and warnings

The separate dummy-renderer timing run began after the full suite finished. Each row measures 120 steady-state draws; construction and first-frame costs are recorded separately in the JSON.

| Output | Normal median | Heavy median | Heavy p95 | Heavy maximum |
| --- | ---: | ---: | ---: | ---: |
| 1280×720 | 4.353 ms | 4.526 ms | 5.867 ms | 8.019 ms |
| 1920×1080 | 2.927 ms | 3.402 ms | 5.412 ms | 11.793 ms |
| 2560×1440 | 5.007 ms | 5.330 ms | 6.239 ms | 7.471 ms |
| 3840×2160 | 6.879 ms | 7.180 ms | 8.116 ms | 18.381 ms |

Two of the 960 measured draws exceeded 16.67 ms, both in 4K-heavy; its p99 was 16.832 ms. These measurements do not guarantee 60 fps or native rendering performance. The fresh timing-only process reached 265.73 MiB peak RSS; that high-water mark is not comparable to earlier combined matrix/capture-process peaks.

The full-suite warning is `no fast renderer available` from the dummy display exercise in `test_config_save_failure_should_not_prevent_switch`, at `main_window.py:212`. It is not hidden or counted as a source failure. Native graphics evidence is assessed separately below.

## 6. Native graphics and remaining acceptance

The lead's [native Cocoa probe](native/report.json) passed windowed → fullscreen → returned-windowed, with normal and 96-projectile synthetic scenes in each phase. QA inspected its report, log and fullscreen-heavy backbuffer image. All 38 native source hashes equal the final capture hashes and current files. Fullscreen used a **3440×1440 window with a 1920×1080 surface/backbuffer**. The two desktop sizes were unchanged afterward: 3440×1440 and 1710×1107. Retained PNGs are backbuffer captures, not physical desktop screenshots.

Across these short native phases, render-plus-flip medians ranged 7.04–16.47 ms, including presentation waiting. Paced median intervals ranged 16.59–16.83 ms, with a maximum interval of 20.52 ms. No warning, error or traceback appeared in the native log. Capture and benchmark logs likewise contained no runtime warning/error; the capture summary explicitly reports zero layout/bounds warnings. No missing-asset fallback was reported. These results do not guarantee a continuous frame rate.

The native probe used synthetic state, disabled audio and no OS keyboard/mouse events. Physical keyboard/mouse behavior, audio, subjective zoom/difficulty preference and human visual approval remain unverified. Native 4K world rendering remains unimplemented. No source assets or save schema were replaced, and this review does not authorize publishing or upstream changes.

## 7. Pre-commit documentation gate

The camera amendment and lead's [review](review.md) agree with the inspected implementation and retained evidence. They separate zoom/framing from artwork/lighting quality and distinguish offscreen output, the logical world canvas, native fullscreen window dimensions and physical-input acceptance. Minor revision/test-count/key-name spacing errors in the draft were corrected. No material factual blocker remains for the scoped local commit; broader human acceptance remains open.
