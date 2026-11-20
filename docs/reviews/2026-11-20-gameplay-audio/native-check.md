# Native launch check — 2026-11-20

A separate process launched the frozen audio implementation using the project
`.venv/bin/python main.py`, default native SDL video/audio drivers and isolated
persistence at `/tmp/dtd-audio-native-check`. No dummy-driver override, system
audio routing change, microphone capture or user save access was used.

`native-launch.log` records 39 loaded resources and no audio-device failure.
The two missing-config warnings are expected for this empty isolated home.
This establishes startup only, not physical sound output or controls quality.

The computer-control inventory did not expose the unbundled Python game as a
running application. Selecting its actual uv Python executable returned
`Invalid app`. No native keyboard or mouse action was performed, and no audio
was listened to. The owned process (PID 71247) was stopped; its shell reported
exit 0. No test game was left open.

**Native movement, aiming, zoom, docking, fullscreen input and listening remain
pending.** Automated event-driven coverage and software mixer recordings are
reported separately. Use `MANUAL-CHECKLIST.md` for Serge's acceptance session.
