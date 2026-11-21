# Application integration

## pygame window icon

`pygame_icon.py` accepts a resolved path to the chosen PNG. Call its function
before the first `pygame.display.set_mode()` when possible. Supply an absolute
path from the game's existing resource resolution mechanism; do not depend on
the shell's working directory. The adapter does not create a display mode or
change fullscreen behavior. It intentionally avoids `convert_alpha()`, which
would require a display mode to be established first.

Example call in the application's existing initialization flow:

```python
set_game_window_icon(resolved_icon_path)
```

The pygame documentation identifies this as a runtime window icon and notes that
some systems require it to be set before the window is shown. Test the result on
the actual target platform.

## Packaged applications

Use the existing packaging tool. For a project already using PyInstaller, its
icon option accepts an ICNS for a macOS .app and an ICO for a Windows executable.
When building from an existing .spec file, update that file's icon setting;
do not assume extra command-line options will override it. Include the selected
runtime PNG in the existing packaged data resources as well.

The pack does not supply a replacement .spec, Info.plist, launcher or .app because
the current application build configuration was not available for modification.

## Primary references

- [pygame-ce display.set_icon](https://pyga.me/docs/ref/display.html#pygame.display.set_icon)
- [PyInstaller usage and icon option](https://pyinstaller.org/en/stable/usage.html)

References checked 2026-11-21. Use the game's pinned dependencies and build process;
this package requires no game dependency upgrade.
