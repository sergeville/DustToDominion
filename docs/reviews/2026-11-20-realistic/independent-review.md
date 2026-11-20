# Independent QA — realistic visual upgrade

Review owner: QA agent, separate from art, renderer and shared-screen implementers.
Status: final automated review complete; see final result below. Native physical input and user visual approval remain unverified.

## Baseline independently observed

- Revision `97cc41afae03c6ca2f4c4c63aa8883e50a765910`.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`: **1,805 passed**, one dummy-renderer warning, **37.05 s**.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/visual_upgrade_validation.py --phase baseline`: passed an earned pygame-event-driven mining trip, 64 synthetic layout captures, and eight repeatable draw benchmarks. See [baseline/report.json](baseline/report.json).
- Test persistence is a dedicated temporary directory. The user's checkpoint and running application were not touched.
- Hardware observed: MacBook Air, Apple M3, 24 GB RAM, ten-core GPU. Main C34J79x display: 3440×1440 at 60 Hz; internal panel: 2880×1864 Retina. 3840×2160 evidence in this report is offscreen, not native 4K.
- Baseline normal/heavy median draw times, milliseconds: 720p **2.809 / 3.048**; 1080p **1.333 / 1.674**; 1440p **3.367 / 3.637**; 2160p **5.179 / 5.453**. Worst sampled frame **5.926 ms**. Cumulative process peak RSS after the capture matrix **253.73 MiB**. These are SDL dummy rendering measurements, not presented native frame rates.

## First playable slice review

The lead ran the QA-authored event-driven script after integrating Prospector, iron asteroid and station assets. QA independently inspected all five resulting images:

- [Fresh flight](slice/trip-fresh.png): actual textured hull, cratered rocks and four-module station; ship marker remains visible above the station.
- [Mining](slice/trip-mining.png): beam, contact spark, partial cut and loose fragment are visible, with clear next-action guidance.
- [Collected](slice/trip-collected.png): cargo reads 3/12 and guidance selects the next rock.
- [Docked](slice/trip-docked.png): result modal is legible; background text does not leak over it.
- [Sold](slice/trip-sold.png): station shows 110 credits, empty cargo and a 30-credit sale message; affordable upgrades enable correctly.

The script's [slice report](slice/report.json) verifies 80→110 credits, three ore collected and sold, and the docking checkpoint. This is automated pygame-event input and actual renderer output, not human/native playtesting.

`COLLECT ORE` alongside `CUT 33%` was reproduced by standing 120 units from a rock and mining once. A loose fragment exists while the rock has two of three health remaining. Guidance correctly says to fly close to the glowing fragment. The model's selection is not a defect.

Slice fidelity is substantially improved in material texture and station detail. It remains less cinematic than the reference: ship/station sizes retain gameplay geometry, the iron rocks reuse a rotated form, and space remains sparse. Expansion can proceed; the slice is not final visual acceptance.

## Independent integration tests

`tests/test_visual_upgrade_acceptance.py` adds two meaningful acceptance paths:

1. Repeated 2160p→720p→1440p→1080p output changes, aimed quick-fire, renderer state/RNG purity and unchanged in-flight checkpoint.
2. Earned sector-two unlock, enemy-fire defeat, 50% hull recovery, saved checkpoint, title/Continue and relaunch through real UI events, without injecting progression or damage.

Both passed against the baseline (0.73 s). They must also pass in the final integrated suite.

## Findings raised during implementation (dispositions below)

- Renderer preload currently bypasses the existing ResourceLoader and rereads default paths. This duplicates decoding and bypasses configured resource overrides/packages. Reported to lead and renderer owner.
- Corrupt PNGs can be rejected by the production ResourceLoader before CampaignSprites fallback is reached. Do not claim end-to-end corrupt-art recovery based solely on a renderer-unit test. Reported to lead.
- Historical `docs/reviews/validate_campaign.py` has a stale station-exploit assertion expecting launch at `STATION_Y`; current launch is `LAUNCH_Y`. It was not modified or represented as passing. Current event-driven acceptance tests are the validation authority for this pass.

## Initial pending scope

The final section records completion of resource-loading review, all final views, benchmarks, full suite and fidelity assessment. Native physical input and user visual acceptance remain pending.

## Native automation limitation reported by lead

At approximately 11:49 Toronto time, the lead launched an owned real-main application process with isolated persistence. Startup succeeded. CUA's app inventory omitted the running uv Python application, and selecting the exact Python executable returned `Invalid app`. The lead closed only that owned probe process; no user game was restarted. QA did not independently operate that desktop session. Therefore movement, aiming, mining, docking and combat through physical native input remain unverified. Any subsequent internal native-window graphics probe is separate evidence and does not substitute for those interactions.

## Final independent result — 2026-11-20

**Automated functional and offscreen layout acceptance passed at product revision `6566c42c8fb3b5cb7208f9f9faae48cbc1f365dd`. Visual fidelity is improved but partial against the reference. Hands-on native input and user visual approval remain unverified.** No product files were changed by QA. The supplemental combat script and this report were added after the source commit; all recorded `src/dtd` hashes still match the final matrix.

### Functional evidence

- [Final full-suite log](final-pytest.log): **1,841 passed, one expected SDL dummy fast-renderer warning, 42.88 seconds**. Command: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`.
- [Final renderer report](final/report.json): another complete event-driven mining trip with all thirteen assets loaded. Three ore mined, collected, docked, persisted and sold; credits **80→110**. All five final trip captures were visually inspected at their original output size.
- [Earned combat report](final/combat-earned-report.json): ordinary UI events earned 300 sales, unlocked sector two and purchased a laser upgrade. Mouse-held aimed fire reduced rival hull **75→45**, defeated the rival and deposited exactly **70 CR**, bank **160→230**, after docking. [First hit](final/combat-earned-hit.png) and [defeated rival](final/combat-earned-defeated.png) show the actual impact effects. Reproduce with `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/2026-11-20-realistic/combat_capture.py`.
- Existing event-driven acceptance covers full earned victory, every upgrade category, both crew, support fleet, save/title/Continue, mid-flight QUIT checkpoint protection and one-time bounty. The independent tests add repeated resolution/aim checks and an earned enemy-fire defeat/recovery/relaunch path. These passed in the final suite.
- The lead corrected the historical station-exploit probe to enter the actual dock area from `LAUNCH_Y`. QA inspected [model-validation.json](model-validation.json): 120 stress expeditions, 91,400 updates, all invariants passed; both safe and risky model campaigns reach victory. This helper is now resolved, rather than an outstanding failed validation.
- Git comparison confirms no changes in `campaign.py`, `campaign_store.py`, `main_window.py` or `config.py` between baseline and the product revision. Save/economy/display behavior is preserved; the user's real save was not used as a test fixture.

### Full matrix review

All **64** final captures were visually inspected through the **16 contact sheets**: English and German; 1280×720, 1920×1080, 2560×1440 and 3840×2160; fresh flight, mining, cargo return, bottom edge, fleet, station, combat and victory. In addition, original-size German 720p station/fleet and German 4K station were inspected for actual glyph readability and wrapping. All five final event-trip originals and both earned combat originals were inspected separately.

There were **zero automated framebuffer or label/button-overlap warnings**. This check does not detect every world-object/text overlap. Across the matrix, controls remain reachable, the ship stays above the bottom strip, German fleet ownership/benefits fit, and modal backgrounds do not leak their underlying text. Examples: [German 720p station](final/de-1280-station.png), [German 720p fleet](final/de-1280-fleet.png), [German 4K station](final/de-3840-station.png), [English 4K flight/edge contact sheet](final/contact-en-us-3840-1.png).

### Reference fidelity assessment

| Area | Assessment | Evidence and limits |
|---|---|---|
| Distinct ships | Met at asset/fleet scale; partial in flight | Prospector, rectangular Hauler, radial Refinery and angular red Rival are distinct. [Fleet](final/en-us-1920-fleet.png). Flight hulls remain small to preserve geometry. |
| Material depth | Met | Worn panels, piping, recesses and cratered rock replace flat polygons. Texture detail is clearly visible in fleet and dock; less prominent at gameplay sprite sizes. |
| Lighting | Partial | Baked overhead shading and cyan/amber details add depth. Lighting rotates with sprites; there is no dynamic scene relighting or 3D shading. |
| Asteroid variety | Met for this scope | Two iron silhouettes plus distinct gold veins and crystal forms, with varied rotations. [Fresh](final/trip-fresh.png), [gold combat](final/combat-earned-hit.png), [crystal combat](final/en-us-1920-combat.png). The field retains its existing count and spacing. |
| Kepler station/dock | Partial | Detailed ring station and warm illustrated hangar delivered. [Dock services](final/trip-sold.png). Dock art occupies a modest panel rather than the board's large cinematic bay; its illustrated ship is not pixel-identical to the playable sprite. |
| Mining/combat effects | Met functionally; partial stylistically | Beam/contact sparks, moving exhaust, ore glints, projectile streaks and observed damage flashes are implemented. [Mining](final/trip-mining.png), [earned hit](final/combat-earned-hit.png). Effects remain inexpensive 2D marks, not the reference's rich volumetric glow. |
| UI/readability | Met for tested layouts, with polish noted below | Cyan/amber hierarchy, restrained frames, actual separately rendered text, clearer fleet identities and correct EN/DE wrapping. Output glyphs are rasterized to the supplied framebuffer size. |
| Crew/progression | Met | Two distinct portraits, separate hire controls and bonuses, readable charter and earned victory. [Station](final/en-us-1920-station.png), [victory](final/en-us-1920-victory.png). |
| Atmosphere/composition | Partial | Dark starfield/nebula adds atmosphere without masking targets. The live scene remains much sparser and more diagrammatic than the reference board. |
| 4K presentation | Partial | 3840×2160 offscreen layout and crisp text verified. World is still a 1920×1080 logical canvas scaled to output; backdrop source is 1672×941. No claim of native 4K world detail or testing on a physical 4K display. |
| Editable source/provenance | Met as raster sources | Thirteen originals, thirteen exact prompts and manifest. QA independently verified every source/runtime SHA-256 and prompt path. No layered painting files, rigs, meshes or 3D sources exist. |

### Comparable rendering cost

Same deterministic scenes, ten warmup frames and 120 measured draws per row; SDL dummy, no display flip. Measurements were completed before concurrent test/native-probe work.

| Output | Baseline normal/heavy median ms | Final normal/heavy median ms | Final heavy p95 ms |
|---|---:|---:|---:|
| 1280×720 | 2.809 / 3.048 | 3.707 / 3.731 | 4.097 |
| 1920×1080 | 1.333 / 1.674 | 2.285 / 2.511 | 2.963 |
| 2560×1440 | 3.367 / 3.637 | 4.442 / 4.586 | 5.114 |
| 3840×2160 | 5.179 / 5.453 | 6.230 / 6.718 | 7.251 |

Final maximum was **24.501 ms**, one 1440p-heavy frame out of 120; the other **959 of 960** measured frames were below 16.67 ms. 4K-heavy maximum was 9.138 ms. New screen construction costs approximately 123–133 ms, including sprite normalization; first draws 5.808–10.715 ms. Cumulative process peak RSS rose **253.73→460.19 MiB** after rendering the full matrix. This is a real memory cost, though it includes loaded art and prior capture allocations; it is not a GPU measurement or per-scene retained-memory estimate. Transform caches are bounded; native report observes 6.70 MB of cached transforms in its fixtures.

### Native evidence and unresolved acceptance

The lead's [native/report.json](native/report.json), inspected by QA, records Cocoa windowed→fullscreen→windowed graphics rendering with isolated persistence and disabled audio. Fullscreen window dimensions matched the main desktop **3440×1440**, while the SDL backbuffer stayed **1920×1080**. Normal/heavy render-and-flip medians were approximately **6.9–7.5 ms**. Desktop sizes before/after match. This confirms a native graphics transition, **not physical keyboard/mouse input or native 4K framebuffer rendering**.

CUA did not expose the owned uv Python application, so hands-on movement, aiming, mining, docking, combat and fullscreen interaction remain unverified. QA did not operate the user's active game. Final human route: launch a separate temporary-save profile, launch sector one, fly out of the shield, verify click-fire, mine/collect ore, return/E-dock/sell, switch fullscreen and back, then Continue from the station checkpoint. Also review a dangerous-sector rival encounter and approve the visual style. Do not replace or clear an existing checkpoint to perform this route.

Remaining visual polish: in [earned combat hit](final/combat-earned-hit.png), `CUT 0%` can cross the player's hull when the ship is directly above a nearby rock; a rival flying over a gold rock has weak silhouette contrast despite its red health bar. These are presentation issues, not firing failures. A future small pass should avoid labels over the player and strengthen rival separation. No product-source changes were made for these findings in this pass.

### Resolved review findings

ResourceLoader reuse was fixed and tested: configured/predecoded resources are respected, no duplicate file decoding in loader mode, source surfaces remain unmodified, and missing assets use vector fallback. Malformed PNGs can still fail strict production ResourceLoader startup before renderer fallback; that existing policy is explicitly documented, and end-to-end corrupt-art recovery is not claimed.

A temporary QA concern that rocks disappeared in `trip-collected.png` was disproved before any source edit. Reopening the exact PNG and two other independent reviewers showed all five remaining rocks; QA additionally verified each remaining rock's 80×80 pixel patch is byte-identical to its fresh-flight patch and cache alpha/mask counts are unchanged. SHA-256: `ca15d370e37fb86b3ced3b15111527eaf88c89bfaf8b0fdbdae95aaf856da257`. The misleading earlier batched image presentation was not a game defect.
