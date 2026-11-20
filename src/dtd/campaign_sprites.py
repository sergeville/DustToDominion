"""Preloaded campaign artwork with a bounded transform cache.

Only this presentation adapter understands the sprite files. World coordinates,
collision geometry and gameplay RNG remain owned by campaign.py. Source ships
point up, while the public heading convention is radians along positive X.
Missing or invalid supplied images use deterministic vector fallbacks. The
production ResourceLoader retains its strict startup policy for corrupt files.
"""
from __future__ import annotations

from collections import OrderedDict
import math
from pathlib import Path

import pygame

from dtd import campaign_art

ASSET_ROOT = Path(__file__).resolve().parents[2] / "resources/campaign/realistic"
SHIP_NAMES = ("prospector", "hauler", "refinery", "rival")
ROCK_NAMES = ("asteroid_iron", "asteroid_gold", "asteroid_crystal")
ASSET_NAMES = SHIP_NAMES + ROCK_NAMES + ("asteroid_iron_b", "station", "miner", "engineer", "dock", "background")
WORLD_NAMES = SHIP_NAMES + ROCK_NAMES + ("asteroid_iron_b", "station",)
MAX_CACHE_ENTRIES = 128
MAX_CACHE_BYTES = 32 * 1024 * 1024


class CampaignSprites:
    """Decode at construction; draw methods perform no filesystem access.

    ``loader`` preserves the application's resource overrides and decoded cache.
    Supplying it never reads files, including when an image is absent. ``root``
    is the standalone/test preload path when no loader is supplied. Read-only ``loaded_names``,
    ``issues`` and ``cache_info`` make missing art and memory limits inspectable.
    The optional legacy color argument controls exhaust only for raster hulls;
    native material colors are retained. Vector fallback retains legacy tinting.
    """

    def __init__(self, root=None, *, loader=None, cache_entries=MAX_CACHE_ENTRIES,
                 cache_bytes=MAX_CACHE_BYTES):
        self.asset_root = Path(root) if root is not None else ASSET_ROOT
        self._sources = {}
        self.issues = {}
        self._cache = OrderedDict()
        self._cache_bytes = 0
        self._entry_limit = max(0, min(MAX_CACHE_ENTRIES, cache_entries))
        self._byte_limit = max(0, min(MAX_CACHE_BYTES, cache_bytes))
        for name in ASSET_NAMES:
            path = self.asset_root / (name + ".png")
            try:
                if loader is None:
                    loaded = pygame.image.load(str(path))
                else:
                    getter = getattr(loader, "get_image_resource", None)
                    loaded = getter("campaign/realistic/"+name+".png") if callable(getter) else None
                if loaded is None:
                    raise ValueError("image absent from resource loader")
                if not isinstance(loaded, pygame.Surface):
                    raise ValueError("image resource is not a pygame.Surface")
                bounds = loaded.get_bounding_rect(min_alpha=8)
                if not bounds.width or not bounds.height:
                    raise ValueError("image has no visible pixels")
                if name in WORLD_NAMES:
                    rgba = pygame.Surface(loaded.get_size(), pygame.SRCALPHA)
                    rgba.blit(loaded, (0, 0))
                    if pygame.mask.from_surface(rgba, 0).count() == rgba.get_width()*rgba.get_height():
                        raise ValueError("world sprite has no transparent background")
                    image = self._normalize_world(rgba, bounds)
                elif loaded.get_bitsize() in (24, 32):
                    # Keep a read-only reference, not another full-size panel
                    # copy. All transforms return new surfaces.
                    image = loaded
                else:
                    image = pygame.Surface(loaded.get_size(), pygame.SRCALPHA)
                    image.blit(loaded, (0, 0))
                self._sources[name] = image
            except (OSError, pygame.error, ValueError) as error:
                self.issues[name] = str(error)

    @staticmethod
    def _normalize_world(source, bounds):
        """Center visible bounds and fit every alpha pixel inside a radius.

        Scanline extrema use Mask.overlap, in C, rather than a Python per-pixel
        scan. This happens once at preload and includes disconnected highlights.
        A 512px normalized source is ample for the largest current world/fleet
        use. Original higher-resolution exports remain on disk.
        """
        cropped = source.subsurface(bounds).copy()
        mask = pygame.mask.from_surface(cropped, 7)
        width, height = cropped.get_size()
        cx, cy = (width-1)/2, (height-1)/2
        radius_squared = 1.0
        # For each occupied row only its two extrema can be furthest from pivot.
        row = pygame.mask.Mask((width, 1), fill=True)
        flipped = pygame.mask.from_surface(pygame.transform.flip(cropped, True, False), 7)
        for y in range(height):
            left = mask.overlap(row, (0, y))
            right = flipped.overlap(row, (0, y))
            if left is not None and right is not None:
                for x in (left[0], width-1-right[0]):
                    radius_squared = max(radius_squared, (x-cx)**2+(y-cy)**2)
        # Pixel corner allowance keeps rotations/smooth filtering within bounds.
        diameter = 2*(math.sqrt(radius_squared)+1)
        scale = 510/diameter
        size = (max(1, round(width*scale)), max(1, round(height*scale)))
        normalized = pygame.Surface((512, 512), pygame.SRCALPHA)
        scaled = pygame.transform.smoothscale(cropped, size)
        normalized.blit(scaled, scaled.get_rect(center=(256, 256)))
        return normalized

    @property
    def loaded_names(self):
        return frozenset(self._sources)

    @property
    def cache_info(self):
        # source_bytes includes panel surfaces shared with ResourceLoader.
        return {"entries": len(self._cache), "bytes": self._cache_bytes,
                "entry_limit": self._entry_limit, "byte_limit": self._byte_limit,
                "source_bytes": sum(image.get_pitch()*image.get_height()
                                    for image in self._sources.values())}

    def _transformed(self, name, size, angle=0):
        width, height = size
        # Two-degree buckets avoid an unlimited heading-key space while keeping
        # maximum angular error one degree; cardinal directions remain exact.
        angle = (round(angle/2)*2) % 360
        key = (name, width, height, angle)
        cached = self._cache.get(key)
        if cached is not None:
            self._cache.move_to_end(key)
            return cached
        image = pygame.transform.smoothscale(self._sources[name], size)
        if angle:
            image = pygame.transform.rotate(image, angle)
        if name in WORLD_NAMES:
            # Guard the physical artwork footprint against antialias fringes and
            # rotation rounding; this affects presentation, never hit geometry.
            clip = pygame.Surface(image.get_size(), pygame.SRCALPHA)
            pygame.draw.circle(clip, (255, 255, 255, 255),
                               (image.get_width()//2, image.get_height()//2),
                               min(width, height)//2)
            image.blit(clip, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        cost = image.get_pitch()*image.get_height()
        if self._entry_limit and cost <= self._byte_limit:
            while self._cache and (len(self._cache) >= self._entry_limit or
                                  self._cache_bytes+cost > self._byte_limit):
                _, removed = self._cache.popitem(last=False)
                self._cache_bytes -= removed.get_pitch()*removed.get_height()
            self._cache[key] = image
            self._cache_bytes += cost
        return image

    def _world(self, surface, name, x, y, radius, angle=0):
        if name not in self._sources:
            return False
        diameter = max(1, round(radius*2))
        # Cull before obtaining a transform. The source is fitted to a circle.
        if not surface.get_rect().colliderect(
                pygame.Rect(round(x-radius)-1, round(y-radius)-1,
                            diameter+2, diameter+2)):
            return True
        image = self._transformed(name, (diameter, diameter), angle)
        surface.blit(image, image.get_rect(center=(round(x), round(y))))
        return True

    def draw_ship(self, surface, x, y, heading, kind="prospector", size=26,
                  thrust=False, phase=0.0, color=None):
        if kind not in SHIP_NAMES:
            raise ValueError(f"Unknown ship kind: {kind}")
        if size <= 0:
            return
        if kind not in self._sources:
            campaign_art.draw_ship(surface, x, y, heading, kind, size, thrust, phase, color)
            return
        if thrust:
            self._exhaust(surface, x, y, heading, size, phase,
                          color or ((242, 111, 101) if kind == "rival" else (79, 217, 228)))
        self._world(surface, kind, x, y, size, -90-math.degrees(heading))

    @staticmethod
    def _exhaust(surface, x, y, heading, size, phase, accent):
        # Fixed two jets: no particle allocation, simulation changes or wall time.
        cosine, sine = math.cos(heading), math.sin(heading)
        def point(forward, lateral):
            return (round(x+size*(forward*cosine-lateral*sine)),
                    round(y+size*(forward*sine+lateral*cosine)))
        length = .35+.12*(1+math.sin(phase*23))/2
        for side in (-.4, .4):
            pygame.draw.polygon(surface, (25, 65, 86),
                                [point(-.67, side-.11), point(-.78-length, side),
                                 point(-.67, side+.11)])
            pygame.draw.polygon(surface, accent,
                                [point(-.70, side-.055), point(-.72-length, side),
                                 point(-.70, side+.055)])
            pygame.draw.line(surface, (224, 250, 255), point(-.70, side),
                             point(-.83, side), max(1, round(size/40)))

    def draw_station(self, surface, x, y):
        if not self._world(surface, "station", x, y, 100):
            campaign_art.draw_station(surface, x, y)

    def draw_asteroid(self, surface, rock):
        if rock.radius <= 0:
            return
        name = ROCK_NAMES[rock.ore]
        if rock.ore == 0 and rock.id % 2 and "asteroid_iron_b" in self._sources:
            name = "asteroid_iron_b"
        if not self._world(surface, name, rock.x, rock.y, rock.radius,
                           (rock.id % 17)*21):
            campaign_art.draw_asteroid(surface, rock)

    def draw_image(self, surface, name, rect):
        """Fit a panel asset without distortion; return False if unavailable."""
        if name not in self._sources:
            return False
        rect = pygame.Rect(rect)
        if rect.width <= 0 or rect.height <= 0 or not surface.get_rect().colliderect(rect):
            return True
        source = self._sources[name]
        fit = source.get_rect().fit(rect)
        image = self._transformed(name, fit.size)
        surface.blit(image, fit)
        return True
