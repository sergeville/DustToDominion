# Application icon integration — 2026-11-21

## Result

Selected **01-original**, original mining perspective. Imported the complete v1
package unchanged; retained all five alternatives. Runtime uses only its 256px
PNG through ResourceLoader before the first window mode. Missing icon/SDL refusal
warns without blocking play. No gameplay, camera, audio, economy, launcher,
resource-loader algorithm, dependency pin or saved-game changes.

Repository: the Drive `Dev Project Archives - 2026-10-30/DustToDominion` checkout.
Branch: `feature/complete-small-game`; starting HEAD `e26d621`. Existing untracked
Finder metadata, drafts and prior deliverables were preserved. Work stays local;
no push or PR to the upstream author's repository.

## Saved files

| Purpose | Location from project root |
| --- | --- |
| Complete original pack, all views, provenance/tools | `assets/source/icons/DustToDominion-Icon-Pack-v1/` |
| Selected PNG sizes, ICNS, ICO and selection record | `assets/icons/ready-to-use/` |
| Only runtime icon resource | `resources/graphics/app-icon.png` |
| Runtime wiring | `src/dtd/main.py`, `src/dtd/game_constants.py` |
| Six regression cases | `tests/test_application_icon.py` |
| Specification and switching | `docs/23-application-icon.md`, root `README.md` |
| Updated related specs/index | `docs/02-window-handling.md`, `docs/03-resource-packaging.md`, `docs/README.md` |
| Evidence and reproducible native probe | this directory |
| Verified resource build (not an installer) | `deliverables/application-icon-verification/resources.pak` |

The original Downloads ZIP remains in place. The extracted source package is
complete and its original README, manifest and integration prompt were read.
No archive instructions were applied as executable code without inspection.

## Verification

- ZIP CRC passed; `tools/verify_package.py` passed all **74 payload hashes**.
- Selected PNG/ICNS/ICO exports match their retained source. The 256px image was
  visually inspected; it shows the original Prospector mining perspective.
- **144 focused tests passed**, then **2,067 full-suite tests passed in 108.05s**.
  One existing dummy-SDL `no fast renderer available` warning; no test failures.
- Existing packager built and inspected **40 resources**, all hashes/decodes valid.
  ZIP member inspection confirms `graphics/app-icon.png` and excludes source
  variants. `.DS_Store` files were skipped with the existing extension warning.
  [Package identity and member list](package-verification.json).
- Two independent native Cocoa process runs used real production startup and
  title rendering with a bounded application-API smoke loop. Source launch then
  `.pak`-only restart ran from unrelated working directories, with temporary
  persistence and dummy audio. Both applied the same 256×256 icon pixels before
  the first display mode, with no SDL exception.
- Both runs passed 1920×1080 window → 3440×1440 fullscreen (2560×1440 drawing
  surface) → 1920×1080 window. Desktop modes unchanged; both processes closed
  normally. No physical keyboard/mouse or listening claim is made.
- [Preservation comparison](preservation.json) confirms existing runtime resources,
  launchers and user saves/settings are unchanged. Python bytecode caches were
  excluded. Both launcher scripts pass `zsh -n`; `git diff --check` passes.

Logs: [focused](focused-tests.log), [full suite](full-suite.log),
[resource build](package-build.log), [native source](native-source.json),
[native pak/restart](native-pak-restart.json).

## Native-platform limits

No `.app`, Info.plist, PyInstaller spec or Windows executable build configuration
exists in this project. No Dust to Dominion `.app` was found at the project root,
Desktop, /Applications or ~/Applications. The existing `.command` launcher stays
unchanged. Copying the ICNS does **not** brand Terminal or the installed Python app.

The computer-use tool could not attach to the uv Python executable (`Invalid app`)
and Dock inspection timed out. Therefore **visible window/Dock icon appearance,
including small/large OS sizes and icon retention after transitions, remains
unverified**. Successful set_icon calls and image decoding do not establish that
visual result. Finder branding is not applicable without a game `.app`. Windows
Explorer/taskbar behavior and native Windows/Linux launches remain unverified.

A future branded macOS app needs an explicitly chosen bundling/build flow, the
selected `assets/icons/ready-to-use/app-icon.icns` in Contents/Resources with a
CFBundleIconFile reference, inclusion of the runtime PNG (or configured `.pak`),
and validation of that bundler's resource layout, launch, signing and Finder/Dock
appearance. Windows packaging would consume the prepared ICO. No new packaging
system was added merely for this icon. Existing `.pak` resource packaging is
verified; frozen executable layouts are not claimed to work.

## Reproduce / use

Double-click **~/Desktop/Open Dust to Dominion.command** or the identically named
project launcher. To launch from a terminal:

```sh
"$HOME/Desktop/Open Dust to Dominion.command"
```

Use Control+Command+F on macOS for fullscreen. Close an older game before reopening.
For another view, follow [the switching steps](../../../README.md#switch-to-another-view).
The source package stays immutable; update selected assets and rebuild resources.

From the project root:

```sh
python3 assets/source/icons/DustToDominion-Icon-Pack-v1/tools/verify_package.py
.venv/bin/python -m pytest -q
.venv/bin/python tools/packager create --source resources --output /tmp/dtd-icon-resources.pak
.venv/bin/python tools/packager inspect --source /tmp/dtd-icon-resources.pak
.venv/bin/python docs/reviews/2026-11-21-application-icon/native_probe.py --name native-source
.venv/bin/python docs/reviews/2026-11-21-application-icon/native_probe.py --name native-pak-restart --pak /tmp/dtd-icon-resources.pak
```

The native probe overwrites its named report/log only when the invoking command
redirects logs; use a new --name to retain previous JSON evidence. Tests/probes
never use the player's saved campaign as fixtures.

## Desktop icon follow-up — 2026-11-21

Serge's 08:18 screenshot showed the unchanged generic `.command` file icon,
which is separate from the pygame runtime icon. Applied the selected 1024px
PNG through Preview copy → Finder Get Info → icon paste to the exact Desktop
launcher. Finder screenshot showed the ship, and Serge's 08:21:10 screenshot
confirmed it. **Desktop Finder file-icon appearance is now verified.** This does
not resolve the remaining running-game Dock/window or native-bundle checks above.

The launcher data fork remains exactly 431 bytes with the same SHA-256; only
macOS custom-icon metadata/resource fork was added (Finder includes that extra
data in its displayed file size). [Verification](desktop-icon.json). No code,
save, setting or launcher logic changed; no test suite rerun was necessary.
Root README explains reapplication/removal; the custom Desktop metadata itself
is not tracked by Git. No native application bundle was created.
