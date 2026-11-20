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
The ship drawings are simple vector outlines. Passive support ships have no
separate visual model, and the existing standalone ship editor is not wired
into campaign ship rendering.
