"""Session-only camera; all model coordinates and distances remain unchanged."""
import math

import pygame

from dtd.game_constants import CAMERA_DEFAULT_ZOOM, CAMERA_ZOOM_LEVELS, CAMERA_VIEWPORT


class Camera:
    """Project the arena into the flight viewport, with an identity overview.

    Rectangles returned by properties are copies, so consumers cannot alter the
    shared framing. Following is immediate and deterministic; no clock or RNG.
    """

    def __init__(self, zoom=CAMERA_DEFAULT_ZOOM, viewport=CAMERA_VIEWPORT, world_bounds=None):
        self._viewport = pygame.FRect(viewport)
        self._bounds = pygame.FRect(world_bounds if world_bounds is not None else viewport)
        self._focus = self._bounds.center
        self.set_zoom(zoom)

    @property
    def zoom(self):
        return self._zoom

    @property
    def viewport(self):
        return pygame.Rect(self._viewport)

    @property
    def center(self):
        return self._center

    @property
    def visible_rect(self):
        width, height = self._viewport.width / self.zoom, self._viewport.height / self.zoom
        return pygame.FRect(self._center[0]-width/2, self._center[1]-height/2, width, height)

    def set_zoom(self, zoom):
        if zoom not in CAMERA_ZOOM_LEVELS:
            raise ValueError(f"Zoom must be one of {CAMERA_ZOOM_LEVELS}")
        self._zoom = float(zoom)
        self.follow(*self._focus)

    def step_zoom(self, direction):
        index = CAMERA_ZOOM_LEVELS.index(self.zoom)
        self.set_zoom(CAMERA_ZOOM_LEVELS[max(0, min(len(CAMERA_ZOOM_LEVELS)-1,
                                                  index + (1 if direction > 0 else -1 if direction < 0 else 0)))])

    def follow(self, x, y):
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("Camera focus must be finite")
        self._focus = (x, y)
        centers = []
        for focus, lower, extent, view_extent in (
                (x, self._bounds.left, self._bounds.width, self._viewport.width),
                (y, self._bounds.top, self._bounds.height, self._viewport.height)):
            half = view_extent / self.zoom / 2
            centers.append(lower+extent/2 if half*2 >= extent
                           else max(lower+half, min(lower+extent-half, focus)))
        self._center = tuple(centers)

    def world_to_screen(self, point):
        return (self._viewport.centerx + (point[0]-self._center[0])*self.zoom,
                self._viewport.centery + (point[1]-self._center[1])*self.zoom)

    def screen_to_world(self, point):
        return (self._center[0] + (point[0]-self._viewport.centerx)/self.zoom,
                self._center[1] + (point[1]-self._viewport.centery)/self.zoom)

    def scale_length(self, value):
        return value*self.zoom

    def is_visible(self, point, radius=0):
        x, y = self.world_to_screen(point)
        radius = self.scale_length(radius)
        return (x+radius >= self._viewport.left and x-radius < self._viewport.right
                and y+radius >= self._viewport.top and y-radius < self._viewport.bottom)
