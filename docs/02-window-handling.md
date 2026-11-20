---
description: Larger windowed presentation and native desktop fullscreen with proportional scaling and persisted display mode.
status: active
---

# Window handling

## Presentation

Windowed mode defaults to a non-resizable 1920x1080 window. Use the previous
1280x720 size if the selected desktop cannot fit 1920x1080 plus 64 pixels of
horizontal and vertical room for window decorations and desktop controls, or
if desktop dimensions cannot be queried. Displays smaller than 1280x720 retain
the existing minimum-window limitation.

Fullscreen uses the monitor's current desktop resolution, including ultrawide
and Retina desktop sizes, without changing its video mode. Render a 1920x1080
logical surface with `FULLSCREEN | SCALED`: SDL scales both graphics and text
proportionally, centers the image with black bars where aspect ratios differ,
and maps mouse coordinates back into the logical surface. Font selection and
design-space point sizes remain unchanged.

F11 toggles the mode. On macOS, Ctrl+Cmd+F also toggles it. The existing window's
display is used when no display is specified. An explicit programmatic display
is validated; invalid indices fall back to display 0 with a warning. Display
placement must be verified on real hardware; SDL controls native placement.
Set SDL_VIDEO_MAC_FULLSCREEN_SPACES=0 before pygame initialization so toggles
can resize immediately instead of waiting for a macOS Space animation.

If fullscreen creation raises pygame.error, log a warning and keep the prior
mode state; a startup failure attempts windowed mode. Successful runtime mode
switches save configuration; startup does not rewrite it. ConfigError/OSError
on save is warning-only. Closing shuts down all pygame modules.

The caption is resolved from `main_window.caption` through LanguageManager,
with a best-effort warning when unavailable. Language changes refresh it.

## Configuration

`mainWindow` accepts:
- `mode`: required, `windowed` or `fullscreen`.
- `display`: optional strict integer; defaults to primary display (0).
- `resolution`: optional legacy field. Accept `1280x720`, `1920x1080`, or
  `2560x1440` for compatibility, but ignore it: fullscreen always uses desktop
  resolution. Successful mode switches omit it from saved settings.

Unknown fields and invalid values remain configuration errors. A missing
mainWindow section means windowed mode. Example:

```json
{"mainWindow": {"mode": "fullscreen", "display": 0}}
```

## Testing

Hermetic tests cover large-desktop startup, smaller/unknown-desktop fallback,
no startup save, missing/legacy/invalid configuration, native scaled fullscreen
requests on ultrawide and non-16:9 displays, F11 return to the appropriate
window size, caption resolution, full shutdown, explicit display selection,
fullscreen failure and save failure. Main-loop tests cover the macOS shortcut.
Mocks establish requested flags, not physical display mode or mouse mapping;
a native smoke test separately records actual window/surface sizes and toggles.

## Acceptance criteria

- On Serge's 3440x1440 desktop the default window is 1920x1080.
- Fullscreen occupies the current desktop; graphics and text keep proportions.
- Existing font/theme selection and campaign checkpoints are preserved.
- F11 and macOS Ctrl+Cmd+F return to windowed mode.
- Automated checks pass; native verification is reported separately.

## Dev plan

1. Amendment 2026-11-03 per spec 16 (Language support): the window title
   is no longer hard-coded to the game's full name - it is read from the
   `main_window.caption` language key, and refreshed whenever the current
   language changes (best-effort, never raising). Doc amended and marked
   `proposed`; the code half is carried out under spec 16's own dev plan
   (key lands in spec 16 stage 2, caption wiring in spec 16 stage 4).
   Flip this document back to `active` once that code lands and the full
   suite passes.
   **Completed 2026-11-04**: landed under spec 16 dev stage 4.
   `MainWindow.open` resolves the caption from `main_window.caption`
   through the `LanguageManager` (warning-logged, never raising - pinned
   in `TestOpenCaption`), and the manager re-applies the caption on every
   real language change (pinned in `TestWindowCaptionRefresh` and the
   full-game round trip in `tests/test_main.py`). Doc flipped back to
   `active`; full suite green at 1426 tests.


2. Amendment 2026-11-20: default to 1920x1080 with smaller-display fallback;
   use desktop fullscreen and proportional SDL scaling, preserve old settings,
   add the macOS shortcut, and validate requests and native toggles before
   marking active.
   **Completed 2026-11-20**: 1,781 tests passed. Native monitor stayed at
   3440x1440 during two fullscreen/1920x1080 windowed round trips; logical
   mouse position and Fleet activation passed. See the linked review below.

Evidence: [Display validation](reviews/2026-11-20-display.md).
