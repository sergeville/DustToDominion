# Independent QA: native-resolution rendering

## Outcome and identity

**PASS for the implementation and automated evidence gate.** One real native fullscreen aiming defect was found, reproduced, fixed, and rechecked before acceptance. No known implementation blocker remains in this scope. New-build human controls, listening, and visual acceptance remain separate.

Tested product commit: **696c3bc4c5f3bbb599d5b75bec0cf9518eea7c49**. Captures were made from its frozen working-tree contents before the local commit; their `base_revision` correctly remains **7a17f981ad7f491fa836fcbe6fbc5d4a7f00054e**. [source-identity.json](source-identity.json) verifies all **40** current source files against both the commit and worktree, the same source inventory in native and dummy rendering, and all **41** resource files unchanged from the before baseline.

Before evidence is eight actual old-renderer captures at matching 2560×1440 and 3840×2160 outputs, with source hashes and an immutable source archive in [baseline/report.json](baseline/report.json). The old completed world canvas was 1920×1080. New captures assert the canvas **is the supplied output surface**, not an enlarged completed scene.

## Regression validation

- **2061 tests passed, one warning, 105.53 seconds**: [full-suite.log](full-suite.log).
- Independent acceptance adds **21 cases** covering all four campaign views at both native outputs; direct target rendering; model/RNG/checkpoint purity; source detail beyond 512 pixels; bounded sprite caches through repeated size changes; projected ship position/footprint; all three zooms; stationary camera aim; quick clicks; and successful fullscreen notification followed by stale SDL motion and focus-loss/resume.
- The existing camera test migration only forwards the optional native drawing keyword through its spy; its behavioral assertions are unchanged.
- Reviewed all eight changed product modules plus `native_render.py`, including the main/base display-change hook, original-source sampling, projection boundaries, buffer replacement, and input settlement. The main hook only notifies a screen after a successful toggle.
- Campaign model, store, logical camera, campaign audio observer, audio manager, game configuration and persistence sources are byte-identical to baseline. No shipped resources or save schema changed.

Validation used the already-created disposable exact-version interpreter `/tmp/dtd-art-lighting-validation-venv/bin/python`, with `-X pycache_prefix=/tmp/dtd-native-validation-pycache`: Python 3.12.13, pygame-ce 2.5.8, SDL 2.32.10. The repository environment and dependency pins were not modified. Tests and probes used owned temporary persistence; the user's save and running game were not accessed.

## Earned play and rendering evidence

[final/report.json](final/report.json) contains **58 captures**, all with zero text-layout and world-label/bar-bound warnings:

- 32 matched synthetic views: English and German, 2560×1440 and 3840×2160; mining and combat at 1×/1.5×/2×, plus station and fleet.
- Four explicit synthetic navigation stress frames covering offscreen station/threat indicators and enlarged actor avoidance.
- 22 captures from two independent event-earned routes, one at each native output size.

Both event-driven routes completed launch → approach → mine → collect three ore → dock → sell, moving credits **80→110**. Continued earned sorties and purchases unlocked sector 2 at **330 lifetime sales**, then visible-target firing defeated a rival for a **70 CR** bounty. Docking banked **190→260 CR**, and save → title → Continue retained the checkpoint. The client uses posted pygame input events and fixed simulation steps; it does not set earned progression, `_aim`, or the player's position. Synthetic visual fixtures are labeled separately. This is automated play, not physical keyboard/mouse operation or a real-time recording.

QA inspected all four contact sheets, the full-resolution earned 4K mining frame and native fullscreen heavy frame. No misplaced native layers, lost controls, clipped HUD text, or label/bar collision was observed. The independent art reviewer covers the matched full originals and German/navigation detail separately. Finer raster detail does not make the scene match the cinematic reference's lighting, composition, effects or asset density; those remain separate visual ambitions.

## Native fullscreen and the corrected pointer defect

The first focused Cocoa replay found a genuine transition error: the SDL mouse position changed from windowed `(1152,486)` to fullscreen backing `(712,486)` after the 440-pixel pillarbox, while a queued stale motion event still carried `(1152,486)`. The stored logical pointer was wrong by **330 pixels horizontally**, and world aim by **220 units at 1.5×**. Flight remained active, so pause behavior did not explain it. Original reproduction: [interim-native-pointer-focused/report.json](interim-native-pointer-focused/report.json).

The successful-toggle hook now refreshes current SDL pointer mapping immediately and once after the next queued update, preserving an already captured click-world aim. It does not poll over normal event-driven aiming. [native-pointer-fixed/report.json](native-pointer-fixed/report.json) shows zero cursor/aim disagreement in windowed, fullscreen and returned phases, with the stale event still present. Independent regressions cover all zooms, pending quick clicks and focus-loss/resume. The first unfocused attempt is retained as inconclusive startup/warp evidence, not as proof of a product defect.

[native/report.json](native/report.json) passed all six normal/heavy windowed → fullscreen → returned phases:

| Measurement | Fullscreen result |
|---|---:|
| Desktop / actual SDL renderer output | 3440×1440 |
| Content backing / campaign canvas | 2560×1440 |
| SDL viewport | x=440, y=0, width=2560, height=1440 |
| SDL scale | 1×1 |
| Completed scene enlargement | None |

Both desktop mode lists remained `[[3440,1440],[1710,1107]]` before and after. Return restored a 1920×1080 window/backing. This establishes native 1:1 content on the measured 3440×1440 display. The 3840×2160 evidence is actual direct offscreen rasterization, **not a physical 4K display test**. No claim is made about Retina pixel ratios or other displays.

The pointer probe used SDL programmatic warping and actual Cocoa/SDL events. The graphics probe used synthetic states and real draw/flip calls with dummy audio. Neither constitutes human input or listening acceptance.

## Performance and memory

Timing ran after full tests and captures finished, without concurrent team rendering/encoding. Offscreen timing is draw-only, with 120 warm samples per scene and four output sizes; it excludes simulation, flip and frame pacing.

| Output | Normal draw median / p95 | Heavy draw median / p95 |
|---|---:|---:|
| 1280×720 | 0.506 / 0.915 ms | 0.996 / 1.418 ms |
| 1920×1080 | 0.908 / 1.698 ms | 1.375 / 2.071 ms |
| 2560×1440 | 1.445 / 2.520 ms | 2.005 / 2.917 ms |
| 3840×2160 | 3.809 / 6.776 ms | 4.560 / 6.471 ms |

No warm offscreen sample exceeded 16.67 ms. Cold 4K first draws took **36.399 / 27.987 ms**, and scene construction approximately **197–203 ms**; warm numbers do not establish hitch-free transitions. Cumulative process peak RSS reached **436.14 MiB**, not an isolated cache or GPU measurement.

Native fullscreen normal/heavy render+flip medians were **6.495 / 7.198 ms**, p95 **7.846 / 8.589 ms**, with paced medians **16.909 / 16.970 ms**. Across all six native phases, render+flip medians ranged **5.219–7.505 ms**. These short probes do not establish a locked 60 FPS or long-session performance.

The 128-entry/32 MiB sprite transform LRU remains bounded, but it is not a total-memory limit. Read-only decoded artwork is approximately **108 MiB**; a native 4K output, backdrop and optional modal shade each need approximately **31.64 MiB**, and the maximum 4K zoom shield approximately **12 MiB**. Backdrop, shade and shield replace previous-resolution buffers instead of retaining a resolution history. Effects retain their separately bounded cache. Cache/source metadata is included in captures and native reports.

## Reproduction commands

Run from the canonical repository. The exact commands used were:

```sh
/tmp/dtd-art-lighting-validation-venv/bin/python -X pycache_prefix=/tmp/dtd-native-validation-pycache -m pytest -q
/tmp/dtd-art-lighting-validation-venv/bin/python -X pycache_prefix=/tmp/dtd-native-validation-pycache docs/reviews/2026-11-20-native-resolution/validate.py
/tmp/dtd-art-lighting-validation-venv/bin/python -X pycache_prefix=/tmp/dtd-native-validation-pycache docs/reviews/2026-11-20-native-resolution/validate.py --benchmark-only
/tmp/dtd-art-lighting-validation-venv/bin/python -X pycache_prefix=/tmp/dtd-native-validation-pycache docs/reviews/2026-11-20-native-resolution/native_pointer.py
/tmp/dtd-art-lighting-validation-venv/bin/python -X pycache_prefix=/tmp/dtd-native-validation-pycache docs/reviews/2026-11-20-native-resolution/native_graphics.py
```

The final two commands open an owned native window and can briefly take focus; they were coordinated with the lead and user notice. The harnesses set isolated persistence and dummy audio internally; the capture harness additionally selects dummy video. Logs and JSON reports retain the outputs. The temporary interpreter may be removed later; the pinned project environment is the normal equivalent runner.

## Diagnostics and remaining acceptance

The one full-suite warning is the known dummy SDL `no fast renderer available` diagnostic at `main_window.py:219`. Native inspection scripts emit a pygame deprecation warning for `Window.from_display_module()` used to query renderer metrics; this is probe API usage, not a game rendering failure. Final capture/benchmark/native runs contain no exception traceback. The retained `capture-attempt1.log` records an evidence setup error: the second route reused its own first-route checkpoint and correctly opened New Game confirmation. The harness now gives each resolution a separate owned temporary persistence directory; both final routes passed.

Still unverified on this new build: human movement/aim/fullscreen/zoom/resume/reload operation, human visual acceptance, actual audio listening, volume/mute through the real options UI with app restart, a physical 4K display, and longer running performance. Previously reported human confirmation of the audio/camera baseline is useful history but does not prove this renderer revision. No additional artwork, audio, dependency or gameplay changes are inferred from this pass.
