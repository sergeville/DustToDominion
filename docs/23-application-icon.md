---
description: Selected application artwork, resource-backed runtime icon, and native packaging boundaries.
status: active
---
# Application icon

## Selection and asset layout

The default is `01-original` (original mining perspective). Preserve the complete
unmodified v1 package at `assets/source/icons/DustToDominion-Icon-Pack-v1/`,
including all six originals, PNG sizes, ICNS/ICO alternatives, provenance,
manifest, preview and verification/selection tools. This tree is authoring material,
not a game resource directory or a shipping input.

Copy its `ready-to-use/` files to `assets/icons/ready-to-use/` for the selected
native packaging inputs. Copy the selected 256px PNG byte-for-byte to
`resources/graphics/app-icon.png`. Only that PNG enters the current runtime
resource tree and `.pak` builds. ICNS/ICO remain prepared inputs for future
native builds; no application bundler or dependency is introduced.

## Runtime behavior

After ResourceLoader finishes, before MainWindow opens the first display mode,
resolve `graphics/app-icon.png` with `get_image_resource` and pass the raw surface
to `pygame.display.set_icon`. Never use display conversion before a mode exists.
Use a constant in game_constants for the resource ID. Existing resource lookup
and override precedence apply equally to loose files and configured `.pak` files,
independent of the working directory. Missing optional icon or SDL rejection
warns and continues. Corrupt resources retain the loader's existing fatal policy.
The icon does not change display creation, mode transitions, gameplay or saves.

## Configuration

No settings key is added. Developers switch the selected assets using the retained
selection tool and the stable paths documented in README. The full source package
stays immutable. A configured resource directory or `.pak` may override the PNG
under the same resource ID through the existing loader.

## Native packaging boundary

The current project has a `.command`/Python launcher and a resource `.pak` tool,
not a macOS `.app` builder or Windows executable builder. The ICNS is not installed
into Python or Terminal. A future app bundle must include the selected ICNS in
Contents/Resources and reference it via CFBundleIconFile, ship the runtime PNG,
and verify resource lookup using that bundler's layout. Windows packaging must
use the selected ICO when introduced. Frozen executable lookup is unverified;
current packaged-resource lookup means the project's existing `.pak` format.

## Testing

- Verify all imported package hashes and selected files against ready-to-use.
- Exercise startup icon application before set_mode, missing icon and SDL failure.
- Load identical selected pixels through loose resources and a real `.pak` from
  another working directory, with no loose icon fallback in the `.pak` case.
- Build/inspect the normal resources with tools/packager; exclude source variants.
- Native launch/restart and windowed/fullscreen round trips with isolated saves;
  report OS appearance separately from API calls and decoded pixels.
- Run the relevant startup/resource/window tests and the full regression suite.

## Acceptance criteria

Default selection and all alternatives are retained; the runtime uses only the
selected PNG through the existing loader before first window creation. Source and
`.pak` lookup pass; launchers, existing assets and user saves remain unchanged.
Native checks distinguish runtime icon behavior from absent application bundles.
Documentation describes switching and remaining macOS/Windows packaging work.

## Verification and switching

See [README switching instructions](../README.md#switch-to-another-view) and the
[verification report](reviews/2026-11-21-application-icon/review.md). Runtime wiring
and resource packaging passed; native OS icon appearance remains unverified.
