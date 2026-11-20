"""Bounded, deterministic presentation effects; never consumes gameplay RNG."""
import math
from collections import OrderedDict
from dataclasses import dataclass

import pygame


def _point(camera, point):
    return camera.world_to_screen(point) if camera is not None else point


def _length(camera, value):
    return max(1, round(camera.scale_length(value) if camera is not None else value))


def light_sprite(radius, color, level=7):
    """Build a tiny black-backed additive pool; callers cache this result."""
    radius = max(1, min(256, round(radius)))
    image = pygame.Surface((radius*2+1, radius*2+1), depth=32)
    image.fill((0, 0, 0))
    for step in range(8, 0, -1):
        gain = ((9-step)/8)**2 * .38 * level/7
        tint = tuple(round(value*gain) for value in color)
        pygame.draw.circle(image, tint, (radius, radius), max(1, round(radius*step/8)))
    return image


class EffectLights:
    """Small additive light approximations, capped at 64 sprites and 2 MiB.

    All sizes are projected screen pixels. Black surroundings contribute zero,
    so the light preserves the scenery instead of painting an opaque disc.
    No asset IO, full-screen intermediate surface, or clock is used.
    """

    def __init__(self):
        self._cache = OrderedDict()
        self._bytes = 0

    @property
    def cache_info(self):
        return {"entries": len(self._cache), "bytes": self._bytes,
                "entry_limit": 64, "byte_limit": 2 * 1024 * 1024}

    def add(self, surface, point, radius, color, strength=1):
        # Preserve the established 64-design-pixel light cap at native output.
        # Absolute 256px cap still bounds individual allocations above 4K.
        limit = min(256, round(64*max(1, surface.get_width()/1920)))
        radius = max(1, min(limit, round(radius)))
        level = max(0, min(7, round(strength * 7)))
        if not level or not surface.get_clip().colliderect(
                pygame.Rect(point[0]-radius, point[1]-radius, radius*2+1, radius*2+1)):
            return
        key = (radius, tuple(color), level)
        image = self._cache.get(key)
        if image is None:
            image = light_sprite(radius, color, level)
            cost = image.get_pitch()*image.get_height()
            while self._cache and (len(self._cache) >= 64 or self._bytes+cost > 2*1024*1024):
                _, old = self._cache.popitem(last=False)
                self._bytes -= old.get_pitch()*old.get_height()
            self._cache[key] = image
            self._bytes += cost
        else:
            self._cache.move_to_end(key)
        surface.blit(image, image.get_rect(center=(round(point[0]), round(point[1]))),
                     special_flags=pygame.BLEND_RGB_ADD)


@dataclass
class _MiningShard:
    x: float
    y: float
    vx: float
    vy: float
    age: float
    lifetime: float
    size: float
    color: tuple
    angle: float


class MiningFragments:
    """At most 96 decorative shards, emitted only by observed mining damage.

    Five chips accompany a hit; twelve accompany depletion. Maximum lifetime is
    one simulation second. These are not ore pickups and cannot affect cargo.
    """

    def __init__(self):
        self.items = []

    @staticmethod
    def snapshot(run):
        return {rock.id: (rock.x, rock.y, rock.radius, rock.ore, rock.health)
                for rock in run.asteroids}

    def advance(self, dt, before, run, *, mining=False):
        for shard in self.items:
            shard.age += dt
        self.items = [shard for shard in self.items if shard.age < shard.lifetime]
        if not mining:
            return
        after = {rock.id: rock.health for rock in run.asteroids}
        colors = ((131, 181, 187), (224, 169, 78), (95, 205, 230))
        for identity, (x, y, radius, ore, health) in before.items():
            remaining = after.get(identity, 0)
            if remaining >= health or health <= 0:
                continue
            depleted = remaining <= 0
            angle = math.atan2(run.y-y, run.x-x)
            origin = (x+math.cos(angle)*radius*.72, y+math.sin(angle)*radius*.72)
            for i in range(12 if depleted else 5):
                direction = angle + (i*2.39996 + identity*.73) % math.tau
                speed = 25+(i*13+identity*7) % 45
                self.items.append(_MiningShard(*origin, math.cos(direction)*speed,
                    math.sin(direction)*speed, 0., 1. if depleted else .55,
                    1.4+(i%3)*.8, colors[ore], direction))
        self.items = self.items[-96:]

    def draw(self, surface, camera=None):
        for shard in self.items:
            x, y = shard.x+shard.vx*shard.age, shard.y+shard.vy*shard.age
            angle = shard.angle+shard.age*3
            points = [(x+math.cos(angle+a)*shard.size,
                       y+math.sin(angle+a)*shard.size) for a in (0, 2.3, 4.4)]
            fade = max(0, 1-shard.age/shard.lifetime)
            color = tuple(round(c*fade) for c in shard.color)
            pygame.draw.polygon(surface, color, [_point(camera, p) for p in points])


class DamageFlashes:
    """At most 32 brief impact flashes inferred from observed hull changes."""

    def __init__(self):
        self.items = []
        self.bursts = []

    @staticmethod
    def snapshot(run):
        return {"player": (run.x, run.y, run.hull),
                **{enemy.id: (enemy.x, enemy.y, enemy.hull) for enemy in run.enemies}}

    def advance(self, dt, before, run):
        self.items = [(x, y, age + dt, color) for x, y, age, color in self.items
                      if age + dt < .32]
        self.bursts = [(x, y, age+dt, seed) for x, y, age, seed in self.bursts
                       if age+dt < .65]
        after = self.snapshot(run)
        for identity, (x, y, hull) in before.items():
            current = after.get(identity)
            if current is None or current[2] < hull:
                if current is None and identity != "player":
                    self.bursts.append((x, y, 0., identity))
                if current is not None:
                    x, y = current[:2]
                self.items.append((x, y, 0, (255, 184, 96) if identity == "player"
                                   else (249, 116, 87)))
        self.items = self.items[-32:]
        self.bursts = self.bursts[-8:]

    def draw(self, surface, camera=None, lights=None):
        for x, y, age, color in self.items:
            fade = 1 - age / .32
            tint = tuple(round(c * fade) for c in color)
            radius = 5 + age * 65
            if lights is not None:
                lights.add(surface, _point(camera, (x, y)), _length(camera, radius+10), color, fade)
            pygame.draw.circle(surface, tint, _point(camera, (x, y)), _length(camera, radius), _length(camera, 2))
            for i in range(6):
                angle = i * math.tau / 6
                a = (x + math.cos(angle) * radius, y + math.sin(angle) * radius)
                b = (x + math.cos(angle) * (radius + 5), y + math.sin(angle) * (radius + 5))
                pygame.draw.line(surface, tint, _point(camera, a), _point(camera, b), _length(camera, 2))
        for x, y, age, seed in self.bursts:
            fade = max(0, 1-age/.65)
            if lights is not None:
                lights.add(surface, _point(camera, (x, y)), _length(camera, 30),
                           (255, 157, 77), fade)
            for i in range(8):
                angle = seed*.71+i*math.tau/8
                radius = 10+age*(35+i*7)
                a = (x+math.cos(angle)*radius, y+math.sin(angle)*radius)
                b = (a[0]+math.cos(angle)*5, a[1]+math.sin(angle)*5)
                pygame.draw.line(surface, tuple(round(c*fade) for c in (237, 159, 89)),
                                 _point(camera, a), _point(camera, b), _length(camera, 2))


def mining_beam(surface, ship, rock, phase, camera=None, lights=None, contact=None):
    """Beam from the forward mining mount to the visible near rock surface."""
    start = (ship.x + math.cos(ship.heading) * 27,
             ship.y + math.sin(ship.heading) * 27)
    dx, dy = rock.x - start[0], rock.y - start[1]
    length = math.hypot(dx, dy)
    inset = min(rock.radius * .78, length)
    end = (rock.x - dx / max(length, 1) * inset,
           rock.y - dy / max(length, 1) * inset)
    if contact is not None:
        end = contact
    if lights is not None:
        tint = ((88, 194, 213), (247, 178, 68), (93, 202, 247))[rock.ore]
        lights.add(surface, _point(camera, end), _length(camera, 26), tint,
                   .85+.15*math.sin(phase*19))
    pygame.draw.line(surface, (17, 57, 68), _point(camera, start), _point(camera, end), _length(camera, 11))
    pygame.draw.line(surface, (35, 133, 151), _point(camera, start), _point(camera, end), _length(camera, 5))
    pygame.draw.line(surface, (161, 250, 248), _point(camera, start), _point(camera, end), _length(camera, 2))
    contact = ((3, (245, 214, 139)), (1, (255, 253, 230))) if lights is not None else (
        (10, (57, 74, 64)), (6, (236, 180, 96)), (3, (255, 251, 215)))
    for radius, color in contact:
        pygame.draw.circle(surface, color, _point(camera, end), _length(camera, radius))
    for i in range(9):
        angle = i * 2.39996 + phase * 1.7
        distance = 8 + (phase * 42 + i * 7) % 24
        direction = (math.cos(angle), math.sin(angle))
        a = (end[0] + direction[0] * distance, end[1] + direction[1] * distance)
        b = (a[0] + direction[0] * 4, a[1] + direction[1] * 4)
        pygame.draw.line(surface, (245, 183, 89), _point(camera, a), _point(camera, b), _length(camera, 2 if i % 3 == 0 else 1))


def projectile(surface, shot, camera=None):
    """Velocity-aligned streak, independent of collision geometry."""
    speed = max(1, math.hypot(shot.vx, shot.vy))
    tip = (shot.x, shot.y)
    tail = (shot.x - shot.vx / speed * 18, shot.y - shot.vy / speed * 18)
    color = (115, 226, 243) if shot.friendly else (249, 106, 76)
    pygame.draw.line(surface, tuple(c // 4 for c in color), _point(camera, tail), _point(camera, tip), _length(camera, 7))
    pygame.draw.line(surface, color, _point(camera, tail), _point(camera, tip), _length(camera, 3))
    pygame.draw.circle(surface, (244, 247, 222), _point(camera, tip), _length(camera, 2))


def ore_glint(surface, x, y, ore, phase, identity, camera=None):
    """Three mineral silhouettes, with a gentle time-driven sparkle."""
    colors = ((137, 188, 199), (238, 187, 96), (93, 220, 245))
    color = colors[ore]
    if ore == 0:
        points = [(-7,-6),(2,-9),(8,-3),(6,7),(-4,9),(-9,2)]
    elif ore == 1:
        points = [(-8,-4),(-1,-9),(5,-5),(9,3),(2,8),(-7,5)]
    else:
        points = [(-5,-5),(0,-13),(5,-5),(8,4),(0,11),(-7,4)]
    pygame.draw.polygon(surface, tuple(c // 3 for c in color),
                        [_point(camera, (x + a, y + b)) for a, b in points])
    pygame.draw.polygon(surface, color, [_point(camera, (x + a, y + b)) for a, b in points], _length(camera, 1))
    pygame.draw.line(surface, color, _point(camera, (x-3,y-4)), _point(camera, (x+3,y+4)), _length(camera, 2))
    if math.sin(phase * 3 + identity) > .5:
        pygame.draw.line(surface, (228,245,245), _point(camera, (x-3,y-7)), _point(camera, (x+3,y-7)), _length(camera, 1))
        pygame.draw.line(surface, (228,245,245), _point(camera, (x,y-10)), _point(camera, (x,y-4)), _length(camera, 1))
