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
from dtd.campaign_effects import light_sprite

ASSET_ROOT = Path(__file__).resolve().parents[2] / "resources/campaign/realistic"
SHIP_NAMES = ("prospector", "hauler", "refinery", "rival")
ROCK_NAMES = ("asteroid_iron", "asteroid_gold", "asteroid_crystal")
ART_VARIANTS = ("asteroid_iron_c", "asteroid_gold_b", "asteroid_crystal_b",
                "prospector_v2", "rival_v2", "station_v2")
ASSET_NAMES = SHIP_NAMES + ROCK_NAMES + ("asteroid_iron_b", "station", "miner", "engineer", "dock", "background") + ART_VARIANTS
WORLD_NAMES = SHIP_NAMES + ROCK_NAMES + ("asteroid_iron_b", "station",) + ART_VARIANTS
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
        self._field_details = self._prepare_field_details()

    def _prepare_field_details(self):
        """At most 24 tiny, faint, static pieces; no resemblance to mineable rocks."""
        names = [name for name in ("asteroid_iron", "asteroid_iron_b")
                 if name in self._sources]
        if not names:
            return ()
        pieces = []
        for i in range(24):
            side = i % 4
            if side == 0:
                x, y = 55+(i*37)%115, 185+(i*97)%800
            elif side == 1:
                x, y = 1750+(i*29)%115, 185+(i*83)%800
            elif side == 2:
                x, y = 190+(i*137)%1530, 170+(i*19)%70
            else:
                x, y = 190+(i*113)%1530, 935+(i*13)%65
            size = 6+i%5
            image = pygame.transform.smoothscale(self._sources[names[i%len(names)]],
                                                 (size, size))
            image.set_alpha(55+(i%3)*8)
            pieces.append((x, y, image))
        return tuple(pieces)

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
                                    for image in self._sources.values()),
                "field_detail_bytes": sum(image.get_pitch()*image.get_height()
                                          for _, _, image in self._field_details)}

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
        if name in ("rival", "rival_v2"):
            image = self._separate_rival(image)
        elif name in ("prospector", "prospector_v2"):
            image = self._separate_hull(image, (84, 178, 192, 110))
        if name in WORLD_NAMES:
            # Guard the physical artwork footprint against antialias fringes and
            # rotation rounding; this affects presentation, never hit geometry.
            clip = pygame.Surface(image.get_size(), pygame.SRCALPHA)
            pygame.draw.circle(clip, (255, 255, 255, 255),
                               (image.get_width()//2, image.get_height()//2),
                               min(width, height)//2)
            image.blit(clip, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return self._remember(key, image)

    def _remember(self, key, image):
        cost = image.get_pitch()*image.get_height()
        if self._entry_limit and cost <= self._byte_limit:
            while self._cache and (len(self._cache) >= self._entry_limit or
                                  self._cache_bytes+cost > self._byte_limit):
                _, removed = self._cache.popitem(last=False)
                self._cache_bytes -= removed.get_pitch()*removed.get_height()
            self._cache[key] = image
            self._cache_bytes += cost
        return image

    @staticmethod
    def _separate_rival(image):
        """Cached two-pixel dark separation and restrained one-pixel red rim.

        Stroke pixels remain within the original transform canvas and the
        normal circular footprint guard; gameplay size is not enlarged.
        """
        return CampaignSprites._separate_hull(image, (235, 116, 111, 210))

    @staticmethod
    def _separate_hull(image, rim):
        # Follow actual alpha, preserving transparent hull gaps and the scenery.
        mask = pygame.mask.from_surface(image, 32)
        separated = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        for distance, color in ((2, (4, 9, 16, 220)), (1, rim)):
            silhouette = mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))
            for dx, dy in ((-distance, 0), (distance, 0), (0, -distance), (0, distance),
                           (-distance, -distance), (-distance, distance),
                           (distance, -distance), (distance, distance)):
                separated.blit(silhouette, (dx, dy))
        separated.blit(image, (0, 0))
        return separated

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
        name = kind+"_v2" if kind+"_v2" in self._sources else kind
        if name not in self._sources:
            campaign_art.draw_ship(surface, x, y, heading, kind, size, thrust, phase, color)
            return
        if thrust:
            self._exhaust(surface, x, y, heading, size, phase,
                          color or ((242, 111, 101) if kind == "rival" else (79, 217, 228)))
        self._world(surface, name, x, y, size, -90-math.degrees(heading))

    def _exhaust(self, surface, x, y, heading, size, phase, accent):
        # Fixed two jets: no particle allocation, simulation changes or wall time.
        cosine, sine = math.cos(heading), math.sin(heading)
        def point(forward, lateral):
            return (round(x+size*(forward*cosine-lateral*sine)),
                    round(y+size*(forward*sine+lateral*cosine)))
        length = .35+.12*(1+math.sin(phase*23))/2
        glow_radius = max(1, min(64, round(size*.25)))
        key = ("exhaust:"+str(tuple(accent)), glow_radius, glow_radius, 0)
        glow = self._cache.get(key)
        if glow is None:
            glow = self._remember(key, light_sprite(glow_radius, accent))
        for side in (-.4, .4):
            surface.blit(glow, glow.get_rect(center=point(-.82, side)),
                         special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.polygon(surface, (43, 148, 181),
                                [point(-.67, side-.11), point(-.78-length, side),
                                 point(-.67, side+.11)])
            pygame.draw.polygon(surface, accent,
                                [point(-.70, side-.055), point(-.72-length, side),
                                 point(-.70, side+.055)])
            pygame.draw.line(surface, (224, 250, 255), point(-.70, side),
                             point(-.83, side), max(1, round(size/40)))

    def draw_station(self, surface, x, y, size=100):
        name = "station_v2" if "station_v2" in self._sources else "station"
        if not self._world(surface, name, x, y, size):
            if size == 100:
                campaign_art.draw_station(surface, x, y)
            elif size > 0:
                diameter = max(1, round(size*2))
                key = ("vector_station", diameter, diameter, 0)
                image = self._cache.get(key)
                if image is None:
                    source = pygame.Surface((200, 200), pygame.SRCALPHA)
                    campaign_art.draw_station(source, 100, 100)
                    image = self._remember(key, pygame.transform.smoothscale(source, (diameter, diameter)))
                surface.blit(image, image.get_rect(center=(round(x), round(y))))

    def _rock_name(self, rock):
        name = ROCK_NAMES[rock.ore]
        newest = ("asteroid_iron_c", "asteroid_gold_b", "asteroid_crystal_b")[rock.ore]
        if newest in self._sources:
            variants = [newest]
            if rock.ore == 0 and "asteroid_iron_b" in self._sources:
                variants.append("asteroid_iron_b")
            if name in self._sources:
                variants.append(name)
            name = variants[rock.id % len(variants)]
        elif rock.ore == 0 and rock.id % 2 and "asteroid_iron_b" in self._sources:
            name = "asteroid_iron_b"
        return name

    def draw_asteroid(self, surface, rock, camera=None):
        if rock.radius <= 0:
            return
        name = self._rock_name(rock)
        x, y = camera.world_to_screen((rock.x, rock.y)) if camera is not None else (rock.x, rock.y)
        radius = camera.scale_length(rock.radius) if camera is not None else rock.radius
        if not self._world(surface, name, x, y, radius, (rock.id % 17)*21):
            if camera is None:
                campaign_art.draw_asteroid(surface, rock)
            else:
                from types import SimpleNamespace
                campaign_art.draw_asteroid(surface, SimpleNamespace(
                    x=x, y=y, radius=radius, id=rock.id, ore=rock.ore))

    def mining_contact(self, ship, rock, camera=None):
        """First solid artwork pixel on the beam ray, in world coordinates.

        Uses the exact displayed variant/rotation; a concave edge or central
        transparent hole cannot become a false contact. The scan is capped at
        512 samples and uses cached transforms, with no pixel array allocation.
        Missing artwork or a ray through empty space returns None for the
        caller's ordinary geometric fallback. This never alters collision data.
        """
        name = self._rock_name(rock)
        if name not in self._sources or rock.radius <= 0:
            return None
        project = camera.world_to_screen if camera is not None else lambda p: p
        origin = project((ship.x+math.cos(ship.heading)*27,
                          ship.y+math.sin(ship.heading)*27))
        center = project((rock.x, rock.y))
        radius = camera.scale_length(rock.radius) if camera is not None else rock.radius
        diameter = max(1, round(radius*2))
        image = self._transformed(name, (diameter, diameter), (rock.id % 17)*21)
        bounds = image.get_rect(center=(round(center[0]), round(center[1])))
        dx, dy = center[0]-origin[0], center[1]-origin[1]
        distance = math.hypot(dx, dy)
        if distance < 1e-6:
            dx, dy, distance = math.cos(ship.heading), math.sin(ship.heading), 1.
        dx, dy = dx/distance, dy/distance
        start = max(0., distance-radius-2)
        end = distance+radius+2
        steps = max(1, min(511, math.ceil((end-start)*2)))
        for index in range(steps+1):
            along = start+(end-start)*index/steps
            x, y = round(origin[0]+dx*along), round(origin[1]+dy*along)
            local = (x-bounds.x, y-bounds.y)
            if (0 <= local[0] < image.get_width() and
                    0 <= local[1] < image.get_height() and
                    image.get_at(local).a >= 96):
                return camera.screen_to_world((x, y)) if camera is not None else (x, y)
        return None

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

    def draw_image_cover(self, surface, name, rect):
        """Fill a panel by center-cropping, without stretching source geometry."""
        if name not in self._sources:
            return False
        rect = pygame.Rect(rect)
        if rect.width <= 0 or rect.height <= 0 or not surface.get_rect().colliderect(rect):
            return True
        key = ("cover:"+name, rect.width, rect.height, 0)
        image = self._cache.get(key)
        if image is not None:
            self._cache.move_to_end(key)
        else:
            source = self._sources[name]
            crop = source.get_rect()
            if crop.width*rect.height > crop.height*rect.width:
                crop.width = max(1, round(crop.height*rect.width/rect.height))
            else:
                crop.height = max(1, round(crop.width*rect.height/rect.width))
            crop.center = source.get_rect().center
            image = pygame.transform.smoothscale(source.subsurface(crop), rect.size)
            self._remember(key, image)
        surface.blit(image, rect)
        return True

    def draw_field_detail(self, surface, camera=None):
        """Draw static distant debris behind the world, in logical 1920x1080 space.

        Exactly 24 precomputed 6–10px images at most (<10KiB) are shared across
        frames. Missing rock artwork simply omits this decorative layer.
        """
        for index, (x, y, image) in enumerate(self._field_details):
            if camera is None:
                surface.blit(image, (x, y))
                continue
            if not camera.is_visible((x, y), 10):
                continue
            point = camera.world_to_screen((x, y))
            size = tuple(max(1, round(camera.scale_length(v))) for v in image.get_size())
            key = ("debris:"+str(index), *size, 0)
            scaled = self._cache.get(key)
            if scaled is None:
                scaled = self._remember(key, pygame.transform.smoothscale(image, size))
            surface.blit(scaled, point)
        return bool(self._field_details)
