# Serge's controls and listening check

Status: **PARTIALLY VERIFIED BY SERGE — 2026-11-20, approximately 16:42–16:46 EST.**
See [the dated human-play addendum](manual-results.md) for exact observations and
limits. These checks concern the audio/artwork baseline before the native-resolution
pass; automated results remain separate in `independent-review.md`. Native-resolution
work is now authorized, with new-build physical/visual review still open.

Save at the station and close any older game before reopening
**Open Dust to Dominion.command** in the project folder. Choose **Continue**
to preserve your current campaign. Use New Game only if you intentionally want
a new campaign (it asks for confirmation and keeps a backup).

Use your usual speakers/headphones at a comfortable system volume. In the title
screen's **Options**, enable game sound effects and choose a comfortable game
SFX volume. Music/UI/speech controls are separate; this pass adds gameplay sounds.
No need to change macOS audio routing or install capture software.

| Check | Expected behavior | Serge's result |
| --- | --- | --- |
| Launch Sector 1; move with WASD/arrows, then release | Ship responds immediately; engine bed while moving, quiet when stopped | Serge confirmed movement, engine and stopping |
| Aim at 1×, 1.5× and 2× with wheel or −/+ | Nose follows the pointer. Hold pointer still while moving: aim remains aligned | Aiming at all three zoom levels confirmed; stationary-pointer detail not separately documented |
| Click outside the blue station shield | Shot pulse accompanies accepted shots; shield/cooldown rejection does not produce false shots | Rival firing/killing and shot sound confirmed; rejection detail pending |
| Hold Space near a marked asteroid; release; try out of range | Contact texture during valid mining, quiet on release/out of range. Breaking rock has a distinct burst | Mining/contact sound confirmed; release/out-of-range/burst details pending |
| Fly over loose ore | Pickup cue accompanies cargo increasing; no repeated cue while sitting over empty space | Pickup/cargo and cue confirmed; repetition edge case pending |
| Press Esc while moving/mining; resume; switch away and back | Gameplay sounds stop on pause/focus loss; no stuck engine or delayed burst after resume. Fresh movement/mining input works | Pause silence and resumed movement/sound confirmed; focus-loss and no-input resume pending |
| Follow station indicator, approach and press E | Docking cue only for successful docking; failed distant E press stays quiet | Successful docking and cue confirmed; failed-distance cue pending |
| Continue to station and sell cargo | Short sale confirmation once; credits/cargo update as before | Confirmed;18 iron sold for234 CR,9,792→10,026 CR,18/24→0/24 cargo |
| Return to title/Options; test game SFX mute and volume; Continue | Setting is respected, no old sound backlog. Adjustments persist after restart | Pending |
| Launch Sector 2 if already unlocked; fight outside shield | Both ships' accepted shots, damage and destruction are distinct; sound does not become harsh or overpower cues | Rival killed; weapon/destruction cues confirmed. Impact distinction and mix comfort pending |
| Dock, Save checkpoint, return to title, Continue; close/reopen | Credits, hull, cargo, fleet and upgrades persist; no old loops remain | Save→title→Continue retained10,026 CR,150 hull,0 cargo,3 ships/2 crew; full app restart pending |
| F11 fullscreen then return; try aim and zoom | Correct target alignment and readable HUD in both modes | F11 did not toggle on Serge’s Mac; Control+Command+F and fullscreen aiming confirmed. New native-resolution build pending |

Space cuts asteroids; weapons damage rival ships. Sector 1 has no rivals.
Sector 2 unlocks after 300 CR in lifetime ore sales; earn this normally if needed.
This checklist does not require or authorize modifying your save to skip progression.

Please note any late/repeated sound, missing cue, uncomfortable loudness, aim
misalignment or sluggish movement. A simple result is enough:
**movement / aiming / zoom / docking / sound: good or issue**, with the issue.

A disconnected-device startup test is covered separately in automated QA;
you do not need to disturb your working audio device for this review.
