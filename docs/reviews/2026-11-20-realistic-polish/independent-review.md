# Independent QA — realistic presentation polish

Review owner: QA, separate from the shared-screen and renderer implementers.
Status: scoped polish accepted after independent regression, visual and rendering
validation. Physical native input, audio and user art acceptance remain unverified.

## Baseline and regression proof

Baseline revision: `c991a1a` (product source inherited from `6566c42`).
The user's saves, active game and unrelated drafts are not test fixtures.

- [Baseline report](baseline/report.json): 32 actual renderer captures, four
  synthetic stress views (mining above a rock, rival over gold, station, fleet),
  English/German at 720p, 1080p, 1440p and offscreen 2160p.
- The existing framebuffer/button detector reported zero warnings. New
  actor-overlap detection found eight CUT/player collisions: both languages
  at all four sizes. The original 1080p mining image visibly confirms the issue.
- [Baseline regression log](baseline-regressions.log): **8 failed, 5 passed in
  5.66s**. Both earned mining routes fail, three localized corner cases fail,
  and all three rival-on-ore visibility cases fail. This demonstrates the new
  tests detect the preceding defects. Subsequent test refinement measures the
  actual output-sized glyphs rather than only logical-size glyphs.
- The prior full suite at identical product source passed 1,841 tests. Its
  single `no fast renderer available` warning occurred in an SDL dummy display
  test; this is not evidence of a Cocoa renderer failure. No warning is hidden
  or used as proof that physical native play works.

Baseline visual observations from original images: the dock illustration is a
small thumbnail; fleet cards leave substantial empty space around their hulls;
the opaque station disk flattens the scene; a rival directly on gold has weak
separation. These are presentation findings, not requests to alter hitboxes,
ore placement, enemy behavior or progression.

## Independent coverage

`tests/test_visual_polish_acceptance.py` checks earned mining from above a rock,
localized actual font bounds at multiple outputs, corner stress layouts,
hostile markers around rival hulls over each ore material, and unchanged
campaign/run state, save bytes, RNG and collision radius. Corner/overlap scenes
are explicitly synthetic; the mining route uses normal pygame events.

`validate.py` retains source hashes and actual PNGs. Final warning checks include
framebuffer/button, label/actor, label/healthbar, label/label and healthbar/healthbar
intersections. Visual inspection remains necessary: rectangles and color counts
cannot establish human readability or whether the style matches the reference.

## Finding caught during polish

The first revised collision-avoidance placement put a rival's health bar near
the upper-left HUD when its four local candidates overlapped the rock. This
produced a long leader across the field despite zero collision warnings:
[retained reproduction](interim-distant-rival-bar.png). QA added an independent
requirement that this ordinary rival-over-rock fixture keep its visible bar
within 150 logical pixels of the rival. All three ore-material cases failed
before the correction ([interim log](interim-regressions.log): three failed,
ten passed in 5.08s).

The lead changed fallback search to nearby rings followed by distance-ranked
free positions. Refreshed EN 1080p and DE 720p original combat captures show the
bar immediately below the rock/rival, with a short leader. All 32 refreshed
captures have zero measured layout, world-label and bar/bar collisions. This
finding is resolved in the frozen-source captures and full regression suite below.

## Frozen-source validation

Product revision: `957e96b8c4ddf99a59bcfb308dcdeb7d73761ce9`.
Final test-helper refinement and full-suite revision:
`a61e8d6a078ae05306d0e74ac262e9a742d42f2f`. This second commit changes test
measurement only. All 36 product source hashes match across the final matrix,
current checkout and native report.

- [Full suite](final-pytest.log): **1,860 passed, 1 warning in 48.45s**, including
  the 13 new acceptance cases. The warning is `no fast renderer available` in
  `TestProgrammaticSwitch::test_config_save_failure_should_not_prevent_switch`,
  at `src/dtd/main_window.py:212`, under SDL dummy. It is retained, not suppressed.
- [Final renderer evidence](final/report.json): 32 four-view captures covering
  English/German and 720p, 1080p, 1440p and offscreen 2160p. Zero measured
  framebuffer/button, world-label or healthbar collision warnings. All views
  were inspected through eight contact sheets, with original-size checks of
  the mining/combat associations and the smaller German station/fleet layouts.
- Five additional original captures record an earned pygame-event-driven trip:
  launch, mine, collect, dock, sell. Three ore yielded 30 CR (**80 → 110 CR**),
  and the isolated checkpoint was persisted. This was automated input through
  the game, not physical keyboard/mouse play. All five images were inspected.
- The report retains hashes for the 37 original PNGs; eight contact sheets are
  review aids. Synthetic overlap fixtures are separate from earned progression.

## Rendering measurements

The same normal/effect-heavy fixtures used in the prior realistic pass ran ten
warm-up and 120 measured frames per row. SDL dummy measurements exclude display
flip and pacing; all 960 measured draws were below 16.67 ms (worst 7.895 ms).

| Offscreen output | Normal median, ms | Heavy median, ms | Heavy p95, ms |
| --- | ---: | ---: | ---: |
| 1280×720 | 3.645 | 3.973 | 4.261 |
| 1920×1080 | 2.357 | 2.788 | 3.229 |
| 2560×1440 | 4.395 | 4.535 | 4.939 |
| 3840×2160 | 6.219 | 6.447 | 6.775 |

This shows no material draw-time regression in these fixtures, not a universal
frame-rate guarantee. Cumulative process peak RSS was 618.06 MiB. The preceding
pass recorded 460.19 MiB but used a different capture/trip order and matrix
size; those process high-water marks do not isolate a product memory regression.
The sprite cache remains bounded at 128 entries/32 MiB; the static decorative
detail buffer is a separately reported 6,200 bytes.

The lead's [native Cocoa graphics probe](native/report.json), independently
reviewed here, passed windowed → fullscreen → windowed rendering with synthetic
normal/heavy scenes. The fullscreen window was **3440×1440**, while its render
surface remained **1920×1080**. Both desktop sizes were unchanged after exit.
Render-plus-flip medians were 6.89–8.27 ms, p95 8.88–9.95 ms; paced intervals
had 17.36–17.79 ms medians (roughly 56–58 fps). Thus native 60 fps is not proven.
The eight-line [native log](native-probe.log) contains no warnings or errors.
The probe disables audio and does not exercise physical input.

## Independent visual verdict

The targeted defects are fixed in the reviewed cases. CUT text clears the pilot
with readable backing and a short leader when displaced. Rivals retain visible
red silhouette cues and open brackets over iron, gold and crystal; their bars
remain locally associated. The wider dock image and larger fleet hulls make
the existing art substantially easier to see. The translucent station field
preserves background depth and the faint edge debris modestly reduces emptiness.

This remains a restrained 2D adaptation of the reference, not a visual match.
The world is still sparse, flight ships remain small, and rim/bracket overlays
are diagrammatic. The larger dock is a crop of existing art; it does not create
a new cinematic scene. Dynamic relighting, volumetric effects, cinematic camera
work and native 4K world detail remain absent. This pass introduces no new assets.
The scoped fixes are acceptable without changing gameplay geometry or saves;
the reference's overall cinematic fidelity remains future art/rendering work.

## Evidence limits

Offscreen 3840×2160 output is distinct from native display resolution. The world
canvas remains 1920×1080; direct offscreen output can rasterize text at 4K while
the native SDL scaled backbuffer may remain 1920×1080. Record native window and
backbuffer dimensions separately. A native graphics probe is not physical
keyboard/mouse, audio, balance or user art acceptance.
