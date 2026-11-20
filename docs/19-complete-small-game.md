---
description: Defines a finite local mining campaign with trading, upgrades, rival combat, fleet growth, recoverable defeat, saved progress and a visible victory.
status: proposed
---

# Complete small game

Serge selected this scope on 2026-11-20: mine, trade, upgrade, fight, save/load,
and reach a clear end goal. This is a local continuation of upstream 68e5e62.
It expands the untracked first-run draft 18; that draft remains preserved as
historical input and is not implemented as a competing game mode.

## Configuration and scope

Keep Python 3.12 and all existing dependency pins. Reuse the current pygame
window, resource loader, themes, localization, UI and audio. Draw coherent
vector ships, station, rocks, pickups, lasers and rivals in code: no external
image generation, network calls or required new media. Preserve font licenses.
All player text is localized through English and German language resources.
Gameplay balance lives in a small pure-Python model module; settings remain in
game.json and campaign progress in separate campaign.json.

The campaign is single-player and offline. There is one station, three sectors,
three ore grades and two support ships. Support ships confer sale bonuses;
they are not individually piloted or simulated. Two crew hires give defined
bonuses. There is no open world, multiplayer, procedural narrative or voice
acting in this scope. Runtime gameplay must not depend on the ship/NPC editors.

## Player flow and completion

Title offers New Game, Continue, Options and Exit. New Game requires explicit
confirmation if it would replace saved progress. Continue reports absent,
invalid or unsupported saves without deleting them. Failed writes are visible.
The station shows credits, hull, cargo, fleet, crew and the exact victory goal.
Players launch into a sector, mine rocks, collect ore, fight or avoid rivals,
and return to the station beacon to dock. Docking retains cargo for explicit
sale. Purchases cannot overspend. Player actions and resulting prices are visible.

Victory requires three owned ships (including the starter), both crew hires,
and at least 1,200 banked credits. Show a victory panel once reached, with
Continue Playing and Title actions. A completed campaign remains playable.
Defeat discards unsold cargo and returns the player to the station with half
maximum hull for free. Safe-sector mining permits recovery without spending.
Abandoning an expedition has the same loss/recovery rule and requires confirmation.

## Default balance

Start with 80 credits, 100 hull and capacity 12. Ore sells for 10/20/35 credits.
Sectors contain 18/24/30 ore units; sector 1 is safe, sectors 2/3 have rivals.
Unlock sectors 2/3 after lifetime sales of 300/1,000 credits respectively.
Cargo upgrades add six capacity and cost 100 then 180; laser upgrades improve
mining speed by 25% per level and cost 120 then 220; hull upgrades add 25 maximum
hull and cost 100 then 180. Each upgrade has two levels. Support ships cost 350
then 650 and add 10% then 20% of base sale value (30% total). Miner crew costs
150 and increases mining speed 15%; engineer costs 200 and reduces damage 15%.
Repairs cost one credit per two hull, bounded by affordable missing hull.
Combat must be avoidable: no rivals spawn on the station and the station region
is safe. Destroyed rivals award credits once. Projectiles and entities are bounded.
Balance is an initial choice, to be checked by complete simulation and real play.

## Controls, timing and coordinates

WASD/arrows move, normalized diagonally; Space mines the nearest in-range rock.
Mouse aims and left button fires; E docks within the visible station radius.
The on-screen control strip documents these controls. ESC pauses; focus loss
also pauses and clears held input. Paused screens consume no world time and
do not pass clicks through to underlying controls. Resume clears held input.
Window close exits. F11 stays app-owned.

Use existing 1920x1080 logical coordinates consistently, with HUD bounds
excluded from the playfield. Scale rendering and pointer input together.
The app supplies elapsed seconds through Screen.advance(dt), a default no-op
for existing screens. Gameplay clamps elapsed time to 0.25s and consumes fixed
1/60s steps with a bounded accumulator. Reset accumulator on pause/transition.
This explicitly amends spec 00's test-harness-only accumulator restriction.
Simulation accepts explicit time and input, has no pygame/file I/O and no wall
clock. Campaign state belongs to the application session, not transient screens.

## Save and recovery contract

Save only at the station: after docking/defeat, selling/purchases and explicit
Save, plus before returning to title. Exiting an expedition leaves the previous
station checkpoint; the pause screen explains this. An atomic same-directory
temporary write plus replacement prevents partial saves. A versioned, strictly
validated JSON payload rejects malformed, unsupported, negative, nonfinite and
out-of-bounds state. A valid older checkpoint is never silently overwritten by
an invalid load. Preserve invalid bytes and present the error before New Game
can replace them. Save failures leave the live session usable and are visible.
No autosave when merely previewing a fresh campaign before confirmation.

## Module contracts for the team

- `dtd/campaign.py`: pure Campaign, Expedition, InputState dataclasses; campaign
  owns credits/hull/cargo/upgrades/support_ships/miner/engineer/lifetime_sales/
  won flag; properties capacity/max_hull/ship_count/victory.
  Methods launch(sector)->Expedition, sell()->int, buy(item)->bool,
  repair()->int, finish_run(expedition, defeated=False), to_dict(), from_dict(data).
  `buy` keys: cargo, laser, hull, ship, miner, engineer. Invalid actions return
  failure without mutation. Campaign.from_dict validates all persisted state.
- Expedition exposes x/y/heading, asteroids, pickups, enemies, projectiles,
  hull, cargo, sector, finished, defeated and dock_ready. Methods
  step(dt, InputState), request_dock()->bool. InputState contains move_x/move_y,
  mining/firing and aim_x/aim_y. The model owner publishes exact API before UI work.
- `dtd/campaign_store.py`: CampaignStore(path=None), exists(), load()->Campaign,
  save(campaign), with SaveError for recoverable failures. Default path uses
  persistence.resolve_persistence_dir()/campaign.json. Store owns JSON version.
- `dtd/screens/campaign.py`: CampaignScreen(theme, loader, campaign, store),
  implements update/advance/draw/handle; owns station/flight/pause/result panels.
  Title passes Campaign and store to the campaign screen; subsequent Continue reloads the saved station checkpoint. UI agent owns new
  campaign language keys only and its own UI tests.
- Root owns title/main/base integration, specs, existing title test updates,
  packaging/launcher, complete-suite and real-window checks.

## Testing and acceptance criteria

1. Real title -> New Game -> station -> launch -> mine -> collect -> dock -> sell
   -> upgrade -> launch a dangerous sector -> fight -> return succeeds.
2. Deterministic model tests cover movement bounds, cooldowns, cargo limits,
   one-time collection/rewards, docking range, death, purchases and victory.
3. Save/reload restores all station progress; malformed/versioned/nonfinite
   saves and failed writes preserve the last valid checkpoint.
4. An ordinary sequence of reachable actions can attain victory; an empty
   wallet and defeat do not strand the player. Test a full campaign progression.
5. Pausing/focus loss freezes gameplay; input resets; F11/Options/localization
   and music cleanup remain compatible. No real user save is used by tests.
6. Full existing and new hermetic tests pass. Real-window inspection checks
   legible controls and station/flight/results at 1280x720; higher modes are
   reported separately. Automated tests do not certify fun or final balance.

## Dev plan

1. Amend specs 00/08/16 for timing, menu and new localized campaign UI before code. **Completed 2026-11-20.**
2. Implement pure model and independently test combat/economy/progression; implement
   validated store and recovery tests in parallel using the agreed model API.
3. Implement campaign UI and connect the app session, title menu and elapsed time.
4. Run focused/full suites and deterministic full progression; inspect real game,
   fix integration defects, then record acceptance evidence. Activate only after
   acceptance; preserve any explicit unverified platform/balance limits.

## Implementation evidence — 2026-11-20

Stages 1–3 are implemented. The model, checkpoint store, UI and integration
have automated coverage, including a complete campaign through reachable
actions. See [review report](reviews/2026-11-20-playable-game.md) for results.
Stage 4 remains open for a human native-window playthrough and balance review;
this spec intentionally stays proposed until that acceptance is recorded.
The ship drawings use simple vector outlines. Passive support ships have
distinct silhouettes in the Fleet roster, but are not simulated in flight.
The standalone ship editor is not wired into campaign rendering.

## Validation amendments — 2026-11-20

Independent play probes found a risk-free bounty farm: the player could shoot
from station safety and outrange inactive rivals. The station safe region now
locks the player's weapons and absorbs every projectile crossing it, friendly
or hostile. Player shots travel for 0.75 seconds at 780 units/second (585 units),
within rivals' 680-unit detection range. The visible station hint explains the
weapons lock. Combat remains available outside the safe region. Tests cover
station farming, attacks from beyond detection, shield crossing and legitimate
combat/docking rewards. This changes balance, not saved-state format.

A station Fleet button opens a read-only roster: the starter and two support
vessels have distinguishable vector silhouettes, owned/available status and
individual benefits. Show the currently earned total ore-sale bonus, not just
incremental purchase bonuses. Support vessels remain passive and unpiloted;
this panel does not imply flying escorts. Back/Esc returns to the station,
with no purchase or world simulation behind the overlay. Text stays localized
in English and German; verify both locales and all supported resolutions.

Continue without a checkpoint explicitly says there is no saved campaign and
suggests New Game. A corrupt/inaccessible save still reports a load error
without altering it. Replacement confirmation buttons use a consistent font.

Dev plan stage 5: record these validation findings before code, implement the
combat guard and fleet/save-message clarity, add focused regressions and event-
driven acceptance tests, then rerun the full suite and render the changed views.

Stage 5 completed for automated acceptance: 1,730 full-suite tests passed,
including event-driven victory/combat/checkpoint cases, model stress probes,
and bilingual roster rendering/click validation at all supported resolutions.
Native-window acceptance, subjective difficulty and comparison against a
running reference game remain unverified; see the review report.

## Presentation follow-up — 2026-11-20

[Spec 20](20-flight-readability-and-feedback.md) extends the campaign with
procedural vessel detail, mining feedback and contextual navigation guidance.
The campaign rules, support-ship behavior and checkpoint schema remain unchanged.

### Additional dev plan stage

Implement and validate spec 20's rendering/guidance layer while retaining the
existing complete earned-progression and persistence regression coverage.


## Readability geometry amendment — 2026-11-20

Spec 20's follow-up moves the station center to (960, 750), with unchanged
110-unit docking and 220-unit safety radii. A launch starts at (960, 595):
clearly separated from station art, protected, and outside docking range.
Returning inside the ring is required before E docks. The complete safe region
fits above the flight controls. Economy, combat rules and save schema remain
unchanged. Tests cover launch safety, travel back to dock and earned progression.

### Additional dev stage

Implement this geometry alongside spec 20's readability amendment, then run
campaign/model/UI/acceptance tests and visual layout checks.


## Firing input correction — 2026-11-20

A complete left-button click can arrive before a fixed simulation step. Retain
one pending fire attempt (with click aim) until the next consumed step, even if
the button has been released. Coalesce multiple taps before a step; do not bypass
the existing fire cooldown. Holding left click continues automatic fire.

Clear pending input on pause/focus loss, launch, docking and overlays. Consume
blocked attempts at the next step rather than deferring them past the shield or
cooldown. Shield protection and station-sniping prevention remain unchanged.

### Testing and acceptance

Reproduce a press/release in one event batch and across batches before a step;
both must fire once outside the shield. Check click aim, held fire/release,
cooldown, safe-zone blocking, pause/focus clearing and earned combat acceptance.
Tests isolate settings and saves.

### Additional dev stage

8. Fix lost quick-click input, clarify the localized safe-zone hint, run focused
   and full regression checks, document results and commit locally.
