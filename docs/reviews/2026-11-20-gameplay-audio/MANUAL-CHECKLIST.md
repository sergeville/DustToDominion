# Serge's controls and listening check

Status: **PENDING — to be filled after actual play/listening.** Automated results
are recorded separately in `independent-review.md`. Native 4K is deferred;
the world still renders internally at 1920×1080.

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
| Launch Sector 1; move with WASD/arrows, then release | Ship responds immediately; engine bed while moving, quiet when stopped | Pending |
| Aim at 1×, 1.5× and 2× with wheel or −/+ | Nose follows the pointer. Hold pointer still while moving: aim remains aligned | Pending |
| Click outside the blue station shield | Shot pulse accompanies accepted shots; shield/cooldown rejection does not produce false shots | Pending |
| Hold Space near a marked asteroid; release; try out of range | Contact texture during valid mining, quiet on release/out of range. Breaking rock has a distinct burst | Pending |
| Fly over loose ore | Pickup cue accompanies cargo increasing; no repeated cue while sitting over empty space | Pending |
| Press Esc while moving/mining; resume; switch away and back | Gameplay sounds stop on pause/focus loss; no stuck engine or delayed burst after resume. Fresh movement/mining input works | Pending |
| Follow station indicator, approach and press E | Docking cue only for successful docking; failed distant E press stays quiet | Pending |
| Continue to station and sell cargo | Short sale confirmation once; credits/cargo update as before | Pending |
| Return to title/Options; test game SFX mute and volume; Continue | Setting is respected, no old sound backlog. Adjustments persist after restart | Pending |
| Launch Sector 2 if already unlocked; fight outside shield | Both ships' accepted shots, damage and destruction are distinct; sound does not become harsh or overpower cues | Pending if Sector 2 locked |
| Dock, Save checkpoint, return to title, Continue; close/reopen | Credits, hull, cargo, fleet and upgrades persist; no old loops remain | Pending |
| F11 fullscreen then return; try aim and zoom | Correct target alignment and readable HUD in both modes | Pending |

Space cuts asteroids; weapons damage rival ships. Sector 1 has no rivals.
Sector 2 unlocks after 300 CR in lifetime ore sales; earn this normally if needed.
This checklist does not require or authorize modifying your save to skip progression.

Please note any late/repeated sound, missing cue, uncomfortable loudness, aim
misalignment or sluggish movement. A simple result is enough:
**movement / aiming / zoom / docking / sound: good or issue**, with the issue.

A disconnected-device startup test is covered separately in automated QA;
you do not need to disturb your working audio device for this review.
