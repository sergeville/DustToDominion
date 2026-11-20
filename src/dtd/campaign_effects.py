"""Bounded, deterministic presentation effects; never consumes gameplay RNG."""
import math

import pygame


class DamageFlashes:
    """At most 32 brief impact flashes inferred from observed hull changes."""

    def __init__(self):
        self.items = []

    @staticmethod
    def snapshot(run):
        return {"player": (run.x, run.y, run.hull),
                **{enemy.id: (enemy.x, enemy.y, enemy.hull) for enemy in run.enemies}}

    def advance(self, dt, before, run):
        self.items = [(x, y, age + dt, color) for x, y, age, color in self.items
                      if age + dt < .32]
        after = self.snapshot(run)
        for identity, (x, y, hull) in before.items():
            current = after.get(identity)
            if current is None or current[2] < hull:
                if current is not None:
                    x, y = current[:2]
                self.items.append((x, y, 0, (255, 184, 96) if identity == "player"
                                   else (249, 116, 87)))
        self.items = self.items[-32:]

    def draw(self, surface):
        for x, y, age, color in self.items:
            fade = 1 - age / .32
            tint = tuple(round(c * fade) for c in color)
            radius = 5 + age * 65
            pygame.draw.circle(surface, tint, (x, y), round(radius), 2)
            for i in range(6):
                angle = i * math.tau / 6
                a = (x + math.cos(angle) * radius, y + math.sin(angle) * radius)
                b = (x + math.cos(angle) * (radius + 5), y + math.sin(angle) * (radius + 5))
                pygame.draw.line(surface, tint, a, b, 2)


def mining_beam(surface, ship, rock, phase):
    """Beam from the forward mining mount to the visible near rock surface."""
    start = (ship.x + math.cos(ship.heading) * 27,
             ship.y + math.sin(ship.heading) * 27)
    dx, dy = rock.x - start[0], rock.y - start[1]
    length = math.hypot(dx, dy)
    inset = min(rock.radius * .78, length)
    end = (rock.x - dx / max(length, 1) * inset,
           rock.y - dy / max(length, 1) * inset)
    pygame.draw.line(surface, (17, 57, 68), start, end, 11)
    pygame.draw.line(surface, (35, 133, 151), start, end, 5)
    pygame.draw.line(surface, (161, 250, 248), start, end, 2)
    for radius, color in ((10, (57, 74, 64)), (6, (236, 180, 96)),
                          (3, (255, 251, 215))):
        pygame.draw.circle(surface, color, end, radius)
    for i in range(9):
        angle = i * 2.39996 + phase * 1.7
        distance = 8 + (phase * 42 + i * 7) % 24
        direction = (math.cos(angle), math.sin(angle))
        a = (end[0] + direction[0] * distance, end[1] + direction[1] * distance)
        b = (a[0] + direction[0] * 4, a[1] + direction[1] * 4)
        pygame.draw.line(surface, (245, 183, 89), a, b, 2 if i % 3 == 0 else 1)


def projectile(surface, shot):
    """Velocity-aligned streak, independent of collision geometry."""
    speed = max(1, math.hypot(shot.vx, shot.vy))
    tip = (shot.x, shot.y)
    tail = (shot.x - shot.vx / speed * 18, shot.y - shot.vy / speed * 18)
    color = (115, 226, 243) if shot.friendly else (249, 106, 76)
    pygame.draw.line(surface, tuple(c // 4 for c in color), tail, tip, 7)
    pygame.draw.line(surface, color, tail, tip, 3)
    pygame.draw.circle(surface, (244, 247, 222), tip, 2)


def ore_glint(surface, x, y, ore, phase, identity):
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
                        [(x + a, y + b) for a, b in points])
    pygame.draw.polygon(surface, color, [(x + a, y + b) for a, b in points], 1)
    pygame.draw.line(surface, color, (x-3,y-4), (x+3,y+4), 2)
    if math.sin(phase * 3 + identity) > .5:
        pygame.draw.line(surface, (228,245,245), (x-3,y-7), (x+3,y-7))
        pygame.draw.line(surface, (228,245,245), (x,y-10), (x,y-4))
