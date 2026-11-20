# Dust to Dominion

A small offline asteroid-mining campaign built locally on scorbo2's
spec-first pygame-ce game. Mine and sell ore, upgrade your ship, fight rival
ships, hire two crew members and build a three-ship operation. Win with both
crew members, three ships and 1,200 credits in the bank; you can keep playing.

This local continuation includes a complete playable ruleset. Native Mac
playthrough, fullscreen behavior and final difficulty balance still need
human acceptance. See [validation and screenshots](docs/reviews/2026-11-20-playable-game.md)
and [campaign specification](docs/19-complete-small-game.md).
The [team handoff](docs/reviews/TEAM-HANDOFF.md) records the design, decisions,
validation commands, full screenshot archive and work still needing acceptance.

## Play

On this Mac, double-click **Open Dust to Dominion.command**, then choose
**New Game → Launch / Sector 1**. The launcher uses the project's existing
`.venv`; setup instructions below apply on a new installation.

- **WASD / arrows:** move. **Space:** mine nearby asteroids; fly over ore to collect it.
- **Mouse / left click:** aim / fire. **E:** dock inside the station beacon.
- **Esc:** pause during flight. Losing window focus also pauses.
- At the station, sell cargo, repair, buy upgrades, hire crew and buy support ships.
- Sector 1 has no enemies. Sectors 2 and 3 unlock after 300 and 1,000 credits in sales.
- Defeat or confirmed abandonment loses cargo and returns you with half hull for free.

Your ship has a bright segmented marker in the flight view; rivals use red accents. At the
station, choose **View fleet** to inspect all three vessel silhouettes, ownership
and bonuses. Support ships provide passive ore-sale bonuses and do not fly
alongside you. The station shield locks your weapons and absorbs all shots;
leave the blue safe area before fighting rivals.

Progress saves at the station, including after purchases and returning from
an expedition. **Continue** resumes the last station checkpoint; quitting in
flight loses that expedition's progress. Save failures are shown on screen.
New Game confirms replacement and preserves the previous save in a backup file.
Settings live in `~/.DustToDominion/game.json`; progress lives separately in
`~/.DustToDominion/campaign.json` by default.

## Setup instructions

Requires Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Testing instructions

The test suite is hermetic (spec 00): it runs under pygame's dummy video and
audio drivers and redirects all persistence to temp directories, so no
display, sound card, or write access to `~/.DustToDominion` is needed.

```bash
source .venv/bin/activate
python -m pytest
```

## Running the game

```bash
source .venv/bin/activate
python main.py
```

The game opens at 1920x1080, or 1280x720 on smaller displays, unless fullscreen is saved in your settings.
`F11` toggles windowed/fullscreen. Closing the window quits; `Esc` quits from
the title screen and pauses during an expedition.

The main configuration file is `game.json`, stored inside the persistence
directory (default: `~/.DustToDominion/`). The file is optional - if it is
missing or invalid, the game logs a warning and proceeds with default values.

Environment variables:

- `DUST_TO_DOMINION_HOME` - full path to the persistence directory
  (replaces `~/.DustToDominion`)
- `DUST_TO_DOMINION_CONFIG` - full path to the `game.json` file (takes
  precedence over the persistence-directory default)

### Window mode (spec 02)

```json
{
  "mainWindow": {
    "mode": "fullscreen",
    "display": 1
  }
}
```

| Key          | Required when `mainWindow` is present          | Description                                                        |
| ------------ | ---------------------------------------------- | ------------------------------------------------------------------ |
| `mode`       | always                                         | `windowed` (default) or `fullscreen`                               |
| `resolution` | optional legacy setting | accepted but ignored; fullscreen uses the monitor resolution |
| `display`    | never (optional)                               | numeric display index, defaults to the primary display (`0`)       |

Windowed mode prefers a fixed, non-resizable 1920x1080 window, falling back to 1280x720 on smaller displays. Fullscreen uses the current desktop resolution with proportional scaling and black bars where needed. On macOS, Ctrl+Cmd+F also toggles fullscreen. Press `F11` at
runtime to toggle between windowed and fullscreen modes; switching to
fullscreen always uses the monitor's current desktop resolution. Successful switches
are written back to `game.json`.

## Known issues

1. On a Windows system, when playing in windowed mode (not fullscreen), clicking and dragging the
  main window's title bar to move the window will cause music to pause until the mouse is released.
  This is a GIL starvation issue caused by the mechanism we use to load and play audio resources.
  This is neither SDL's fault nor Pygame's fault. On Windows, our main thread is parked during a
  window drag operation, preventing our code from keeping the audio buffer full. Note that this
  seems to only be an issue on Windows.


### Realistic visual upgrade — in progress

The [implementation prompt](docs/DustToDominion_Realistic_Visuals_Team_Prompt.md)
and [visual reference](docs/concepts/realistic-visual-target-2026-11-20.png)
define the target: textured industrial ships, mineral asteroids, Kepler Station,
crew portraits and readable dynamic UI. The reference is concept art; it is not
a screenshot of the implemented game.

The [implementation plan](docs/21-realistic-visual-upgrade.md) records asset
contracts, team ownership and staged acceptance. First, complete one playable
mining trip with the new Prospector, asteroid, station and mining effects; then
expand the artwork across the campaign. Existing gameplay and version-one saves
must remain compatible.

Baseline at local revision `97cc41a`: **1,805 tests passed**. An isolated,
input-driven trip launched, mined and collected three iron units, docked and
sold them, increasing credits from 80 to 110. The
[baseline evidence](docs/reviews/2026-11-20-realistic/baseline/report.json)
includes rendered captures and offscreen timing measurements. This verifies
the existing game before integration; the new visuals and native playthrough
are still being validated.

Earlier [presentation screenshots](docs/reviews/2026-11-20-feedback.md) show
the vector-art stage. See the [team handoff](docs/reviews/TEAM-HANDOFF.md) for
recorded implementation history and acceptance limits. Changes stay local;
the upstream repository is not being pushed or modified.
