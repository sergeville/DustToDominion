"""Optional adapter; integrate through the game's existing resource resolver."""

from pathlib import Path


def set_game_window_icon(resolved_png_path: str | Path) -> None:
    """Set the selected runtime window icon without creating a display mode.

    Call before the first pygame.display.set_mode() where possible. The caller
    provides a path that works in both development and packaged deployments.
    """
    import pygame

    icon_path = Path(resolved_png_path)
    if not icon_path.is_file():
        raise FileNotFoundError(f"Game icon is missing: {icon_path}")
    pygame.display.set_icon(pygame.image.load(str(icon_path)))
