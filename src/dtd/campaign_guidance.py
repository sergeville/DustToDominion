"""Read-only flight advice in logical world coordinates.

Guidance is advisory, not a command or a replacement for the mining selector.
In particular, loose ore may be the helpful destination while a different rock
is the model's current mining target. Keys are localization suffixes; this pure
module knows nothing about translated text, pygame, input, or animation clocks.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from dtd.campaign import (
    Asteroid, Campaign, Expedition, MINE_RANGE, STATION_X, STATION_Y,
    WORLD_BOTTOM, WORLD_LEFT, WORLD_RIGHT, WORLD_TOP,
)

# Matches the model's ore collection radius. Edge ore can be collected without
# pointing the pilot outside the flyable rectangle; remote ore is not a target.
_COLLECTION_RADIUS = 55.0


@dataclass(frozen=True)
class Guidance:
    key: str
    target: tuple[float, float] | None
    distance: float
    progress: float | None = None
    target_id: int | None = None


def _distance_squared(x: float, y: float, expedition: Expedition) -> float:
    return (x - expedition.x) ** 2 + (y - expedition.y) ** 2


def _finite_point(x: float, y: float) -> bool:
    return math.isfinite(x) and math.isfinite(y)


def mining_target(campaign: Campaign, expedition: Expedition) -> Asteroid | None:
    """Return the actual next mineable rock, or None at capacity/out of range.

    Match the simulation's distance-then-ID ordering exactly. The returned
    object belongs to the simulation and must only be read by presentation code.
    """
    if len(expedition.cargo) >= campaign.capacity:
        return None
    nearby = [rock for rock in expedition.asteroids
              if rock.health > 0 and _finite_point(rock.x, rock.y)
              and math.hypot(rock.x - expedition.x, rock.y - expedition.y) <= MINE_RANGE]
    return min(nearby, key=lambda rock: (_distance_squared(rock.x, rock.y, expedition), rock.id), default=None)


def guidance(campaign: Campaign, expedition: Expedition) -> Guidance:
    """Select one deterministic target without changing the campaign or run.

    Priority: dock with cargo/damage (or a depleted field), full-cargo return,
    hull at or below 30% return, collect ore, mine, approach a rock, empty-field
    return. Dock readiness uses the model's 110-unit radius, not the shield.
    Rock progress is the extracted fraction, not elapsed mining cooldown.
    """
    def destination(key, point, *, progress=None, target_id=None):
        return Guidance(key, point, math.hypot(point[0] - expedition.x, point[1] - expedition.y),
                        progress, target_id)

    station = (STATION_X, STATION_Y)
    rocks = [rock for rock in expedition.asteroids if rock.health > 0
             and _finite_point(rock.x, rock.y)
             and WORLD_LEFT <= rock.x <= WORLD_RIGHT and WORLD_TOP <= rock.y <= WORLD_BOTTOM]
    pickups = []
    for pickup in expedition.pickups:
        if not _finite_point(pickup.x, pickup.y):
            continue
        point = (max(WORLD_LEFT, min(WORLD_RIGHT, pickup.x)),
                 max(WORLD_TOP, min(WORLD_BOTTOM, pickup.y)))
        if math.hypot(pickup.x - point[0], pickup.y - point[1]) <= _COLLECTION_RADIUS:
            pickups.append((pickup, point))
    depleted = not rocks and not pickups
    damaged = expedition.hull < campaign.max_hull
    if expedition.dock_ready and (expedition.cargo or damaged or depleted):
        return destination("dock", station)
    if len(expedition.cargo) >= campaign.capacity:
        return destination("return_full", station)
    if expedition.hull <= campaign.max_hull * 0.3:
        return destination("return_damaged", station)
    if pickups:
        pickup, point = min(pickups, key=lambda pair: (
            _distance_squared(pair[0].x, pair[0].y, expedition), pair[0].id))
        return destination("collect", point, target_id=pickup.id)
    rock = mining_target(campaign, expedition)
    if rock is not None:
        progress = 1 - rock.health / rock.max_health if rock.max_health > 0 else 0.0
        return destination("mine", (rock.x, rock.y), progress=max(0.0, min(1.0, progress)), target_id=rock.id)
    if rocks:
        rock = min(rocks, key=lambda item: (_distance_squared(item.x, item.y, expedition), item.id))
        progress = 1 - rock.health / rock.max_health if rock.max_health > 0 else 0.0
        return destination("approach", (rock.x, rock.y), progress=max(0.0, min(1.0, progress)), target_id=rock.id)
    return destination("return_depleted", station)
