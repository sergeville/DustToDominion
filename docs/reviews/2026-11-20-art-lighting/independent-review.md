# Independent artwork and lighting QA

Verdict: **pass for this scoped implementation; no blocking regression found**.
This does not close Serge's visual acceptance, physical controls/audio acceptance,
or native 4K world rendering. Reviewed against baseline product `0525164` and
the final source hashes in [final/report.json](final/report.json).

## 1. Preservation and test evidence

The retained before images are actual prior-camera frames with identical matched
scene state, not fresh captures from this pass. Drive-hosted dependency/file reads
stalled during preparation. The immutable baseline inventory was preserved before
product changes; the later recovered read verified all 38 source files. Only
`campaign_effects.py`, `campaign_sprites.py` and `screens/campaign.py` changed;
the other 35, including model/store/camera/window input code, are byte-identical.
Both retained baseline PNG hashes match. See [source preservation](source-preservation.json).

Full suite: **1,958 passed, one warning in 88.64 seconds**. The warning is the
known dummy-display `no fast renderer available` path at `main_window.py:212`.
The independent 12 new acceptance cases cover hull-shaped separation, transparent
surroundings, variant identity and model/RNG/save purity. Renderer tests also
exercise alpha-aware beam contact, fallback behavior, deterministic effects and
count/lifetime/cache caps. Existing camera, stationary-pointer aiming, quick-click,
save and earned gameplay regressions pass. An interim rim test compared against
the now-contoured friendly sprite; its witness was corrected to raw normalized
artwork, retaining the hostile separation assertion. The final suite has no failure.

Validation used an isolated `/tmp` virtual environment installed with the exact
same 12 distribution versions and Python 3.12.13 / pygame-ce 2.5.8 / SDL 2.32.10.
It ran canonical project source/assets. The project's environment/dependencies
were not modified. The underlying Drive delay remains unexplained.

Final integrity checks re-read **38 source, 33 resource and 14 source-art/provenance
hashes**, plus all **43 original capture/recording hashes**. Native and cap-stress
source inventories match the final capture. [Integrity record](final-integrity.json).

## 2. Play and visual review

An isolated event-driven new game completed launch → mine → collect → dock → sell:
three iron sold, **80 → 110 CR**. Continued earned sorties/upgrades reached 330 CR
lifetime sales and unlocked Sector 2. Forty-six visible-target firing samples
defeated a rival, earned a 70 CR bounty and banked **190 → 260 CR** with hull 86.
Returning to title and Continue verified the checkpoint. No injected unlock,
credits or cargo were used for this route. Matched and navigation fixtures are
separately labelled synthetic evidence.

The 41 final originals comprise 24 matched EN/DE mining/combat views at
720p/1080p and 1×/1.5×/2×, four navigation fixtures, two targeted 4K output images
and eleven earned/menu images. Automated layout/world-bound scans found zero
warnings. QA inspected all four final contact sheets, both 4K originals, all eleven
earned/menu originals and representative EN1080/DE720 navigation originals.
The art reviewer separately inspected all four navigation originals and the full
still-image scope. No new clipping, hidden actor, label collision or unreadable
menu was found in this evidence.

Rock forms and mineral faces are more distinct; the station's metal/glazing read
more clearly. Background remains visible around the hull without the old opaque
disc. Rival red separation remains visible over gold, and navigation chips clear
the enlarged actors. The earned beam meets the visible iron edge with small warm
chips; the rival disappears into an actual short destruction burst.

## 3. Recording review

Both MP4 streams were fully decoded: mining **192 frames / 6.4 s**, combat
**201 frames / 6.7 s**, 1920×1080 at 30 fps, video only. The route advances at
60 Hz and records alternate steps, with one second of final menu freeze. Separate
clips omit the intervening progression sorties. These are actual automated SDL
framebuffers, not desktop video or generated animation.

QA visually inspected chronological decoded samples at 5 fps in
[mining](recording-mining-samples.png) and [combat](recording-combat-samples.png),
then opened full-size decoded [mining at 1.733333 s](recording-mining-trip-1.733333s.png)
and [combat at 3.0 s](recording-combat-3.0s.png). The mining sample visibly contains
the contacting beam, local glow and warm chips. The combat sample contains the
orange destruction burst at the departed rival's position. Adjacent sampled frames
show progression, return and the resulting station balances. This is decoded-frame
review, not full-speed playback or human judgment of motion smoothness.

## 4. Performance and native limits

Clean standard offscreen draw medians, normal/heavy, were **4.05/4.10 ms at 720p,
2.47/3.09 ms at 1080p, 4.74/5.00 ms at 1440p and 6.39/7.27 ms at 4K output**.
The 4K normal sample had two of 120 frames over 16.67 ms, including a 103.89 ms
maximum. The cause is unestablished. An initial overlapping comparison export was
discarded and timing rerun without another team render/encode process.

The separate synthetic cap-stress populated 96 shards, 32 flashes, eight burst
groups and 96 projectiles. Medians were 4.61/3.60/5.37/7.50 ms across the four output
sizes; zero of 480 measured draws exceeded 16.67 ms. Light cache held 26 entries /
512,584 bytes within its 64-entry / 2 MiB cap. This draw-only stress supplements
the earned route; it is not a native frame-rate guarantee.

The native Cocoa graphics report passed six normal/heavy phases across windowed,
fullscreen and returned windowed modes, restoring desktop modes. Fullscreen window
was **3440×1440**, drawing surface **1920×1080**. Render/flip medians were
5.22–6.73 ms; one paced interval was 81.89 ms with that phase's render maximum
12.56 ms. Native/final-capture/benchmark/encoder logs contain no runtime warning,
error or traceback. This isolated probe used dummy audio and did not verify
physical mouse/keyboard play. Neither native probe nor offscreen 4K output is
native 4K world rendering; the world canvas remains 1080p.

## 5. Remaining gaps and documentation gate

The improvement is incremental. Cyan/red contours still read as selection outlines;
mining spray is sparse and impact light is a small additive approximation. Baked
highlights rotate with sprites. Quiet arena composition and compressed small-ship
detail remain far from the reference's large actors, broad warm fracture spray,
surface illumination and local shadows. Higher output resolution alone cannot
close those gaps. Physical controls/audio, other displays/platforms, balance and
Serge's art/lighting acceptance remain open.

Reviewed the current README, artwork report, specification amendment, docs index
links and historical handoff tail against this evidence. One wording correction
was requested to distinguish preserved pre-edit baseline inventory from the later
38-file re-read. No implementation blocker or other material factual mismatch was
found. Product/source freeze should remain; no further test rerun is warranted
for documentation-only changes.
