"""Read-only, screen-space navigation for the flight camera.

Distances are world units. Projection and live-threat filtering belong to the
caller; nothing here knows about or changes campaign state or camera settings.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Iterable

import pygame

Point = tuple[float, float]
Bounds = tuple[int, int, int, int]


@dataclass(frozen=True)
class EdgeIndicator:
    kind: str
    target_id: int | None
    position: Point
    direction: Point
    distance: float
    label_rect: Bounds
    bounds: Bounds
    extra_threats: int = 0


def _finite(point: Point) -> bool:
    return all(math.isfinite(value) for value in point)


def _layout(position: Point, edge: str,
            viewport: pygame.Rect) -> tuple[Bounds, Bounds]:
    x, y = position
    width, height = 250, 32
    if edge == "left":
        left, top = x + 18, y - height / 2
    elif edge == "right":
        left, top = x - 18 - width, y - height / 2
    elif edge == "top":
        left, top = x - width / 2, y + 18
    else:
        left, top = x - width / 2, y - 18 - height
    label = pygame.Rect(round(left), round(top), width, height)
    label.clamp_ip(viewport.inflate(-16, -16))
    arrow = pygame.Rect(round(x) - 12, round(y) - 12, 25, 25)
    bounds = label.union(arrow).inflate(8, 8)
    return tuple(label), tuple(bounds)


def offscreen_indicators(*, player: Point, station: Point,
                         threats: Iterable[tuple[int, float, float]],
                         project: Callable[[Point], Point],
                         viewport=(0, 145, 1920, 875),
                         obstacles: Iterable[Bounds] = ()) -> tuple[EdgeIndicator, ...]:
    """Place the station and nearest two offscreen threats without overlap.

    The final threat reports any additional offscreen threats. The supplied
    threats must already exclude defeated actors. Target centers on the view
    boundary count as visible. Station wins placement priority; enemies are
    ordered by world distance then ID, independent of input iteration order.
    Optional obstacles are projected player/rival bounds, in screen units.
    """
    view = pygame.Rect(viewport)
    if view.width < 600 or view.height < 240:
        raise ValueError("indicators require a logical viewport at least 600x240")
    if not _finite(player):
        return ()
    origin = project(player)
    if not _finite(origin):
        return ()

    def candidate(kind, target_id, point):
        if not _finite(point):
            return None
        screen = project(point)
        if not _finite(screen):
            return None
        if view.left <= screen[0] <= view.right and view.top <= screen[1] <= view.bottom:
            return None
        distance = math.dist(player, point)
        if not math.isfinite(distance):
            return None
        return kind, target_id, screen, distance

    candidates = []
    home = candidate("station", None, station)
    if home:
        candidates.append(home)
    rivals = [item for ident, x, y in threats
              if (item := candidate("threat", ident, (x, y))) is not None]
    rivals.sort(key=lambda item: (item[3], item[1]))
    candidates.extend(rivals[:2])
    extra = max(0, len(rivals) - 2)
    inset = view.inflate(-56, -56)
    ox = max(inset.left, min(inset.right, origin[0]))
    oy = max(inset.top, min(inset.bottom, origin[1]))
    placed = []
    blocked = tuple(pygame.Rect(rect) for rect in obstacles)
    for index, (kind, target_id, screen, distance) in enumerate(candidates):
        dx, dy = screen[0] - ox, screen[1] - oy
        length = math.hypot(dx, dy)
        if not length:
            continue
        direction = dx / length, dy / length
        intersections = []
        if dx < 0:
            intersections.append(((inset.left - ox) / dx, "left"))
        elif dx > 0:
            intersections.append(((inset.right - ox) / dx, "right"))
        if dy < 0:
            intersections.append(((inset.top - oy) / dy, "top"))
        elif dy > 0:
            intersections.append(((inset.bottom - oy) / dy, "bottom"))
        fraction, edge = min(intersections)
        initial = ox + fraction * dx, oy + fraction * dy
        # Slide only along the chosen edge. Dense coincident bearings remain
        # readable, while each arrow still points along its target's bearing.
        horizontal = edge in ("top", "bottom")
        offsets = [0] + [sign * step for step in range(48, max(view.size), 48)
                         for sign in (-1, 1)]
        for offset in offsets:
            x = max(inset.left, min(inset.right, initial[0] + (offset if horizontal else 0)))
            y = max(inset.top, min(inset.bottom, initial[1] + (0 if horizontal else offset)))
            label, bounds = _layout((x, y), edge, view)
            if (any(pygame.Rect(bounds).colliderect(rect) for rect in blocked)
                    or any(pygame.Rect(bounds).colliderect(item.bounds) for item in placed)):
                continue
            placed.append(EdgeIndicator(kind, target_id, (x, y), direction,
                                        distance, label, bounds,
                                        extra if kind == "threat" and index == len(candidates) - 1 else 0))
            break
    return tuple(placed)


def draw_indicators(surface: pygame.Surface, indicators: Iterable[EdgeIndicator],
                    text: Callable, translate: Callable) -> tuple[Bounds, ...]:
    """Draw chips/arrows with CampaignScreen-compatible text/localization hooks.

    Reserve each indicator.bounds before placing ordinary world annotations.
    Text is queued through the caller, retaining native output font rendering.
    """
    reservations = []
    for marker in indicators:
        color = (85, 220, 220) if marker.kind == "station" else (246, 106, 110)
        x, y = marker.position
        dx, dy = marker.direction
        tip = x + dx * 10, y + dy * 10
        back = x - dx * 7, y - dy * 7
        pygame.draw.polygon(surface, color, [tip, (back[0] - dy * 6, back[1] + dx * 6),
                                             (back[0] + dy * 6, back[1] - dx * 6)])
        pygame.draw.rect(surface, (7, 16, 28), marker.label_rect, border_radius=5)
        pygame.draw.rect(surface, color, marker.label_rect, 1, border_radius=5)
        label = translate("camera_" + marker.kind, value=round(marker.distance))
        if marker.extra_threats:
            label += translate("camera_extra_threats", count=marker.extra_threats)
        text(label, marker.label_rect[0] + 9, marker.label_rect[1] + 5,
             size=18, color=color)
        reservations.append(marker.bounds)
    return tuple(reservations)
