# Gameplay audio design review

Status: **final signal/code review; software-mixer capture accepted with the limits below**.
No human or agent listening has been performed. Signal measurements do not
establish device output, pleasantness, fatigue or subjective acceptance.

## Scope and observations

Read the campaign sound adapter, AudioManager playback/loop paths and campaign
lifecycle calls. The adapter observes fixed simulation steps, coalesces cues by
category with an 80 ms simulation-time interval, and keeps at most two loop IDs.
Unchanged loops are not restarted. Pause/exit cleanup stops campaign sounds;
docking/defeat acknowledgement follows cleanup. These are code observations;
independent acceptance tests are reported by QA separately.

All eight original PCM exports reproduce exactly from retained source. Eighteen
asset tests passed, including real dummy-mixer decoding. Peak limits preserve a
campaign-only worst-case twelve-channel sum below 0.9 FS. This bound excludes
external replacement assets and simultaneous UI/speech/music. Loop seam steps
are 0.000244/0.001190 FS with zero measured seam slope change; every one-shot
starts and ends at zero. Hard runtime stops can nevertheless cut a loop at a
nonzero sample, so file continuity does not prove click-free key releases.

## Relative levels and timbre separation

Measured from decoded PCM at full category gain. Maximum RMS uses a 50 ms window
with 10 ms stride. Spectral centroid uses a Hann-windowed 4096-sample high-energy
segment, so it describes one representative segment, not perceived brightness.

| Cue | Duration | Max 50 ms RMS, dBFS | Spectral centroid, Hz |
| --- | ---: | ---: | ---: |
| Thrust | 2 s loop | -36.8 | 106 |
| Mining | 2 s loop | -36.0 | 447 |
| Pickup | 0.24 s | -29.5 | 840 |
| Weapon | 0.18 s | -30.3 | 824 |
| Impact | 0.28 s | -35.6 | 849 |
| Destruction | 0.90 s | -32.8 | 1479 |
| Docking | 0.72 s | -30.6 | 222 |
| Selling | 0.54 s | -30.7 | 873 |

Thrust and mining occupy different bands; rising pickup, descending weapon and
three-note selling have different pitch/time patterns despite overlapping
centroids. This supports designed separation but does not prove audible
recognition. Confirmation/weapon windows sit roughly 5-7 dB above the loops.
Impact is only 0.4 dB above mining on this measure, creating a plausible masking
risk. Thrust has 95.3% of measured spectral energy below 200 Hz, so laptop-speaker
presence may be weak despite its low-mid harmonics. Conservative gains may sound
too quiet on some devices; do not increase them blindly before listening.

## Final actual-mixer evidence

Independently decoded both final WAV files and matched their SHA-256 values to
`final/report.json` for source revision
`e46970fd4958580b6e237cad584a15be488bb4ca`. The report records unchanged sources
during capture. These are actual SDL disk-driver output, 44.1 kHz stereo 16-bit
PCM, with real campaign events; they are not microphone or native loopback
recordings. No physical listening was performed.

| Continuous earned clip | PCM duration | Peak, FS | RMS, FS | Clipped samples |
| --- | ---: | ---: | ---: | ---: |
| Mining trip | 8.4521 s | 0.118378 | 0.014563 | 0 |
| Combat | 7.9180 s | 0.124542 | 0.013239 | 0 |

Both clips begin and end at zero. Their peaks retain approximately 18 dB of
headroom. First-50-ms peaks are 0.02948/0.03192 FS; the anomalous initial combat
buffer is gone. The superseded initial capture had a 0.61694 FS spike within
7 ms, consistent with queued audio from uncaptured progression. QA retained that
diagnostic separately and recaptured after normal lifecycle cleanup and 200 ms
of stationary pre-roll. No product, source sound or final PCM editing was
required to fix this capture boundary.

The event log covers all eight cue IDs across the two clips. In the mining trip,
mining begins around PCM time 2.206 s, ore pickup requests occur at 2.531/2.995 s,
rock destruction at 3.622 s, docking at 6.455 s and selling at 7.291 s. Combat
includes weapon requests from 1.184 s and clustered impacts/destruction around
3.042–3.576 s. These are coarse request/loop-transition timestamps tied to raw
output byte offsets; they do not prove sample-exact cue onset or that every
request obtained a free channel. Measured mixed output is nonzero and bounded;
perceptual cue recognition remains unverified.

Video follows observed PCM file output without audio stretching. Its final
frames end 18.73/18.00 ms before the corresponding PCM ends, within one 30 fps
frame. Disk output falls behind wall time by 0.791/0.871 s over these captures.
Consequently these files support software mixing and event-sequence review,
**not native audio latency or exact audiovisual synchronization acceptance**.
Full H.264/AAC decoding and preservation of source video frames were checked by
QA, not independently repeated in this sound-design review.

## Verdict and remaining acceptance

No clipping or persistent capture-boundary anomaly blocks this software audio
milestone. The initial zero-volume stale-tail concern was corrected: final
source skips new game cues at zero volume and stops the game category when
volume becomes zero. The lead reports regression checks passed; this review
confirmed the source change without rerunning those checks.

Human listening remains necessary for thrust on laptop speakers, impact masking,
loop release/pause clicks, repeated weapon fatigue and overall volume. The
conservative levels and spectral distinctions are measurable, but pleasantness,
audibility and native device behavior cannot be accepted from those numbers.
No product or asset edits were made during this review.
