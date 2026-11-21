# Dust to Dominion — app icon pack v1

Six views of the Prospector, ready to integrate into the game application.
Created 2026-11-21. The original mining perspective is the default.

## Use it

1. Open `preview/index.html` to compare all six designs and their small-size appearance.
2. Use the files in `ready-to-use/` for the default design, or select another view with the command below.
3. Give `INTEGRATION_PROMPT.md` and this package to your development agent.

| View | Identifier | Description |
| --- | --- | --- |
| 01 | `01-original` | Original mining perspective; default |
| 02 | `02-front` | Symmetric front view with mining beam |
| 03 | `03-overhead` | Direct overhead view |
| 04 | `04-side` | Shallow side perspective |
| 05 | `05-rear` | Rear perspective with twin engines |
| 06 | `06-docking` | Arrival in the station docking bay |

Every view has PNG exports at **1024, 512, 256, 128, 64 and 32 pixels square**.
Each also has a macOS ICNS and a Windows ICO container. ICOs contain 16, 24, 32,
48, 64, 128 and 256 pixel images. ICNS files contain the six PNG pixel sizes,
including Retina representations, up to 1024 pixels.

The six unchanged generated originals are **1254 × 1254**. Exports are downsampled
from those originals, not newly generated at each size. These are opaque square
artwork assets with navy backgrounds, not transparent sprites or 3D models.
The camera variations are individually generated illustrations, not an exact
turntable render of a shared 3D mesh. This pack does not contain native 4K images.

## Select another default

Run with Python 3 from this package directory:

```bash
python3 tools/select_icon.py 02-front --output selected-front
```

This creates a new directory containing `app-icon-32.png` through
`app-icon-1024.png`, `app-icon.icns`, `app-icon.ico`, and `selection.json`.
The destination must not already exist. The script verifies the chosen source
assets against the package hashes and does not modify the game or this package.
Copy the selected files into the game's existing asset structure during integration.

| Purpose | File in `ready-to-use/` or selected output |
| --- | --- |
| macOS application bundle | `app-icon.icns` |
| Windows executable | `app-icon.ico` |
| Runtime window icon | `app-icon-32.png` (larger sizes are also supplied) |
| Large launcher/menu artwork | `app-icon-512.png` or `app-icon-1024.png` |

## Contents

- `originals/`: six unchanged generated PNGs.
- `png/<view>/`: the six standard PNG sizes for each view (36 files).
- `macos/` and `windows/`: six platform icons each.
- `ready-to-use/`: default icon files with stable application filenames.
- `preview/`: overview PNG and an offline HTML selector.
- `manifest.json`: paths, dimensions, formats and default selection.
- `provenance/`: generation prompts and origins.
- `tools/`: selection and package verification scripts; Python standard library only.
- `integration/`: a pygame window-icon adapter and setup notes.
- `VALIDATION.json`: recorded file-format verification and remaining native checks.
- `SHA256SUMS.txt`: payload checksums, excluding this checksum file itself.

Verify after extraction:

```bash
python3 tools/verify_package.py
```

This is an integration asset pack, not a game installer. The current game repository
and packaged application were not modified. File formats and embedded sizes were
checked here; Finder/Dock and Windows Explorer appearance must be checked in the
actual built application. Fine texture detail naturally becomes less visible at
32 pixels; use the preview to choose the best small-size composition.
