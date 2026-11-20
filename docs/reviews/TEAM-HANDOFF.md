---
description: Reusable handoff for the local campaign design, implementation, validation evidence and remaining acceptance work.
status: active
---

# Dust to Dominion — team handoff

## 1. Start here

This handoff records work authorized by Serge on 2026-11-20: update the requested
checkout, start the app, then build a complete small game with mining, trade,
upgrades, combat, save/load and a clear ending. He subsequently asked to see the
ships, continue, validate, explain the design method, and save the team's work
in the project documentation.

The implementation is on local branch `feature/complete-small-game`:

- Upstream baseline: `68e5e621b2bd8033b5e33aeb7e86eb84d67e0916`.
- First campaign: `fce6709`.
- Fleet view, combat correction and extended validation: `5618fba`.
- Later documentation-only commits preserve this handoff and evidence.

No push or PR was made. Do not push upstream without Serge's explicit request.
The earlier untracked `docs/18-first-playable-mining-run.md` and
`docs/DustToDominion_First_Playable_Handoff.md` remain preserved. Older local
macOS/gameplay commits mentioned in historical notes were not available in this
checkout; do not assume those changes are present.

| Need | Source |
| --- | --- |
| Rules, balance, scope and acceptance | [Campaign spec](../19-complete-small-game.md) |
| What passed and what did not | [Review report](2026-11-20-playable-game.md) |
| Executable player-input acceptance | [Acceptance tests](../../tests/test_campaign_acceptance.py) |
| Progression and stress numbers | [Probe results](campaign-validation.json) |
| Scaled bilingual UI checks | [Visual records](fleet-visual-validation.json) |
| Fleet preview | [English](campaign-fleet.png), [German](campaign-fleet-de.png) |
| All retained visual evidence | [124 screenshots ZIP](2026-11-20-evidence/screenshots.zip), [SHA-256 manifest](2026-11-20-evidence/screenshot-manifest.json) |
| Replayed draw costs | [Raw measurements](2026-11-20-evidence/draw-benchmark.txt) |
| Player controls and setup | [README](../../README.md) |

## 2. Team work and ownership

| Role | Work delivered | Independent evidence |
| --- | --- | --- |
| Root/integration | Specs before code; title/main timing and transitions; config metadata compatibility; launcher; full-suite runs; review and local branch delivery | Final full suite: 1,730 passed in 35.40s; archive commit and preserved-draft hashes checked |
| Gameplay architecture | Pure campaign/expedition model; economy, mining, combat, defeat, progression; exploit discovery/fix and stress probe | 52 model tests; both complete progression routes; 120 expeditions/93,891 updates |
| Game design/UI | Station/flight/results/pause/victory; EN/DE; distinct Fleet silhouettes, ownership and sale bonuses; scale/input/render review | 24 screen tests; six locale/resolution combinations; 66 final-pass screenshots |
| Quality/persistence | Strict versioned atomic checkpoints and backups; failure tests; independent integration review; event-driven complete play tests | Five acceptance cases; final independent focused gate: 120 tests passed |

The counts overlap and must not be added together. The full-suite total is the
regression result for the final product code, not a measure of game quality.

## 3. Design method and limitations

The design follows the existing project and Serge's selected scope, using
ordinary software architecture and simplified arcade math. **There has been no
side-by-side benchmark against a running reference game.** No external game
art, copied ship assets, generated image API or new dependencies were used.

- Architecture separates pure rules (`campaign.py`), persistence
  (`campaign_store.py`) and rendering/input (`screens/campaign.py`).
- Diagonal movement is normalized; the model accepts explicit time and input.
  The screen uses bounded 1/60-second steps and drops excessive accumulated time.
- Aiming uses the angle to the pointer. Projectiles move at fixed velocity.
  Shield collision checks the complete travel segment against a circle, so a
  grazing shot is absorbed even if both endpoints lie outside the shield.
- Player range is speed × lifetime: 780 × 0.75 = 585 logical units. Rival
  detection is 680 and firing range is 600. Station safety locks outgoing fire
  and absorbs incoming/crossing shots of either allegiance.
- Economy uses integer credits. Ore-sale value is base ore value multiplied by
  the earned support bonus and rounded down. Bonuses are +10%, then another
  +20%, for +30% total. Exact prices and upgrade/crew effects are in spec 19.

This is not realistic spacecraft physics: movement has immediate acceleration
and stopping, no inertia, orbital mechanics, fuel or conservation-of-momentum
simulation. Those omissions keep the small arcade scope manageable. A realistic
physics model would be a separate design decision, not an automatic improvement.

Tests establish rule consistency, reachable progression and checkpoint behavior.
They do **not** establish enjoyable pacing, fair human difficulty, satisfying
controls, art quality or accurate real-world physics. Optimized test players
know target positions and may avoid every shot; their elapsed simulation time
is not a human completion estimate.

## 4. Implemented player experience

Title → New Game/Continue → station → expedition → mine/collect/fight → dock →
sell/repair/upgrade → repeat → Dominion victory → continue playing.

At the station, **View fleet** shows the piloted Prospector and passive Hauler
and Refinery support ships. Ownership and availability are visible, with the
current total sale bonus. Supports have distinct vector silhouettes in this
roster; they do not accompany the player as simulated escorts.

The safe sector is always available. Defeat/confirmed abandonment loses unsold
cargo and restores half maximum hull for free. This makes recovery possible
with zero money. Dangerous sectors unlock from lifetime sales. Victory requires
three ships, both crew hires and 1,200 banked credits; it remains earned after
subsequent spending. No NPC dialogue, voice acting, multiplayer or open world.

A separate version-1 `campaign.json` stores station checkpoints. Quitting during
flight resumes the previous checkpoint. Loads reject invalid versions, fields,
nonfinite values, duplicate JSON keys and oversized files. Saving validates,
writes/flushed/fsyncs a same-directory temporary file, then replaces the target.
Explicit replacement by New Game preserves prior bytes in a uniquely named
backup, including malformed saves. Save failures are visible and do not erase
the live session. This is not a claim of verified physical power-loss durability.

## 5. Findings and corrections

| Finding | Correction and proof |
| --- | --- |
| QUIT/F11 lost during a same-frame screen transition | App events handled before transition dispatch; integration regressions |
| Focus loss dropped after Resume/Launch | Lifecycle-event precheck, cleared input and pause regression |
| Historical `_help` settings caused valid options to fall back | Explicit metadata alias; unknown keys still rejected; compatibility tests |
| Safe-station sniping allowed risk-free bounty farming | Station weapon lock, shield absorption in both directions, shorter player range; original exploit now yields zero bounty |
| Continue falsely said a nonexistent save was preserved | Distinct no-save hint; damaged-save preservation path unchanged |
| Fleet purchase gave no view of owned ships/current benefit | Read-only roster and current total bonus, bilingual/render/input tests |
| Confirmation buttons had inconsistent text sizes | Fixed shared font size, reviewed with actual EN/DE fonts |
| Benchmark retained flight state in later station samples | Fresh screen for each size/view, mode assertions, rerun raw measurements |

No open blocking code defect was found in the final independent review. That
verdict is scoped to the inspected code and tests, not a production certification.

## 6. Validation and reproduction

Run from the project folder using its installed Python 3.12 environment:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
.venv/bin/python docs/reviews/validate_campaign.py
.venv/bin/python docs/reviews/render_campaign.py
.venv/bin/python docs/reviews/benchmark_campaign.py
```

The full test suite requires ephemeral local loopback test servers. In a
restricted sandbox, that portion may need permission. It does not need Internet
services. Tests isolate persistence and use dummy SDL audio/video. Render and
benchmark scripts also isolate settings/saves; they do not drive the real Mac
window. The render script prints a fresh temporary output directory. Its injected
ownership/cargo states are layout fixtures; earned-progression proof belongs
to the separate acceptance tests and pure-model probe.

Measured results:

- Full suite: **1,730 passed in 35.40 seconds**.
- Event-driven acceptance covers actual buttons, keyboard and mouse events,
  complete earned progression/victory, combat/bounty exactly once, checkpoint
  reload and closing with uncheckpointed cargo.
- Safe route: 16 expeditions, 339.86 seconds simulated world time, 1,308 credits.
- All-sector route: 6 expeditions, 150.27 seconds simulated world time, 1,886 credits.
- Stress: 120 expeditions, 93,891 updates, 40 defeats, 34 docks, 46 forced
  abandonments; state bounds, finite values, ore conservation, pickup uniqueness,
  projectile limits and checkpoint round-trips held.
- Visual/click validation: EN/DE at 1280×720, 1920×1080 and 2560×1440.
- Screenshots: 10 initial-build, 48 before Fleet, 66 with Fleet, all retained
  with SHA-256 hashes. Earlier screenshots intentionally show superseded visuals.

## 7. Remaining acceptance and next use

1. Save at the station, close the running earlier build, and reopen
   `Open Dust to Dominion.command` to load the updated code. The existing process
   was intentionally left undisturbed; source updates do not reload Python code.
2. Play the full native loop on the Mac, checking focus loss, pause, audio,
   fullscreen, input feel and return to saved progress. The UI automation tool
   could not attach to the uv Python executable; startup logs are not proof of
   native interaction. All native checks remain explicitly unverified.
3. Compare selected aspects with two or three running reference games: mining
   feedback, targeting, readable silhouettes, upgrade decisions and progression
   pacing. Record observations before choosing changes. No reference comparison
   has been performed in this work.
4. Obtain human judgments on challenge and enjoyment. Tune from observed play,
   not only automated completion times. Record accepted scope changes in specs
   before code and rerun relevant regression cases.
5. Record native acceptance before activating spec 19. Keep the no-push boundary
   and preserved user drafts intact. Do not reconstruct old macOS patches from
   historical prose without inspecting actual source/evidence.

## 8. Flight presentation follow-up — 2026-11-20

This later iteration supersedes the earlier visual baseline, not its history.
See [spec 20](../20-flight-readability-and-feedback.md) and the
[presentation review](2026-11-20-feedback.md) for procedural ship/asteroid/station
art, contextual guidance, mining feedback, reviewers' corrections and evidence.
The [generated visual goal](../concepts/README.md) is a separate longer-term art
target requested by Serge, explicitly distinguished from actual screenshots.
The earlier validation counts above describe the previous implementation.

Latest full suite: **1,768 passed in 36.44s**; independent scoped gate: 67 passed.
Native play acceptance remains open.
