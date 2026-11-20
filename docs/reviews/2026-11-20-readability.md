---
description: Validation of flight identification, station placement and compact HUD.
status: active
---

# Flight readability — 2026-11-20

## 1. Changes

The native screenshots showed the player overlapping the station, a subtle target
circle and a clipped station safety ring. Specs 19/20 were amended before code.

- Station center is now (960,750). Its full 220-unit safety ring fits above controls.
- Launch is (960,595), protected but outside the 110-unit docking radius.
  Fly back into the ring and press E to dock.
- Player has a dark backing, bright corner marker and a localized label for the
  first six seconds of simulated flight. Pause freezes the timer; launch resets it.
- Gold brackets identify the guidance destination, sized outside a rock or around
  the docking ring. Approach has an ore/distance label; cyan remains the laser.
- HUD padding is reduced while retaining font selection and point sizes.
  Bottom-edge ships remain above the controls.
- Economy, combat rules, mining selection, settings and save schema are unchanged.
  Station/launch geometry is an intentional gameplay change.

## 2. Validation

Final full suite: **1,793 passed in 36.66s**, one expected dummy-renderer warning.
Final focused screen suite: **40 passed in 2.23s** before the full run.

Regression coverage includes protected launch/out-of-dock range, movement home,
station fire lock, earned campaign victory, combat, checkpoints, marker geometry,
HUD clearance at all four world corners, EN/DE labels, pause/reset/expiry and
return/ore brackets. Self-review caught an arrow overlapping the temporary player
label at the bottom edge; label placement now avoids the arrow, with a regression.

Thirty real-font fixtures cover EN/DE at 1280x720, 1920x1080 and 2560x1440:
fresh launch, mining, full-cargo return, bottom edge and fleet. All were inspected
through six contact sheets; corrected label placement was re-rendered and checked.
These are synthetic rendering fixtures, not human playthrough evidence.

- [Fresh flight](2026-11-20-readability/en-us-1920-fresh.png)
- [Bottom-edge ship](2026-11-20-readability/en-us-1280-bottom-edge.png)
- [English contact sheet](2026-11-20-readability/review-en-us-1920.jpg)
- [German contact sheet](2026-11-20-readability/review-de-1920.jpg)
- [SHA-256 manifest](2026-11-20-readability/manifest.json)
- [Reproduction script](render_feedback.py)

Run from the project root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/render_feedback.py
```

## 3. Limits and next use

Serge's supplied [realistic visual target](../concepts/realistic-visual-target-2026-11-20.png)
is saved exactly as supplied. This pass improves gameplay readability; painted
ship/asteroid textures, station scenery and crew portraits are still future work.
No dependencies were added. Tests/renders isolate settings and saves. No independent
agent review was run for this amendment.

Human art approval, input feel, balance and full native campaign acceptance remain
open. Fullscreen behavior is unchanged from the [display check](2026-11-20-display.md).
Reopen `Open Dust to Dominion.command` to load source changes, then Continue and
launch Sector 1. Never close an active expedition without returning to a checkpoint.
