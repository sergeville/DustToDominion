"""Original industrial spacecraft art in logical screen coordinates.

Drawing changes only the destination surface. Geometry is deterministic; headings
are radians pointing along +X. ``size`` is the ship hull's approximate radius,
with animated exhaust extending aft to 1.6 times that radius. No fonts, assets,
display initialization, gameplay randomness or model mutation are required.
"""
from __future__ import annotations

import math
from typing import Protocol

import pygame

_DARK = (20, 30, 42)
_EDGE = (116, 145, 161)
_METAL = (65, 85, 103)
_LIGHT = (151, 172, 182)
_CYAN = (79, 217, 228)
_ORE = ((103, 188, 214), (212, 172, 94), (174, 129, 231))


class Rock(Protocol):
    id: int
    x: float
    y: float
    radius: float
    ore: int


class _Hull:
    """Local geometry painter, avoiding intermediate rotated raster surfaces."""

    def __init__(self, surface, x, y, heading, size):
        self.surface, self.x, self.y, self.size = surface, x, y, size
        self.cos, self.sin = math.cos(heading), math.sin(heading)

    def point(self, x, y):
        return (round(self.x + self.size * (x * self.cos - y * self.sin)),
                round(self.y + self.size * (x * self.sin + y * self.cos)))

    def plate(self, points, fill=_METAL, edge=_EDGE):
        pixels = [self.point(*p) for p in points]
        pygame.draw.polygon(self.surface, fill, pixels)
        if edge is not None:
            pygame.draw.aalines(self.surface, edge, True, pixels)

    def line(self, points, color=_DARK, width=1):
        pygame.draw.lines(self.surface, color, False,
                          [self.point(*p) for p in points], max(1, round(width * self.size / 26)))

    def dot(self, x, y, radius, color):
        pygame.draw.circle(self.surface, color, self.point(x, y), max(1, round(radius * self.size)))


def draw_ship(surface: pygame.Surface, x: float, y: float, heading: float,
              kind: str = "prospector", size: float = 26, thrust: bool = False,
              phase: float = 0.0, color=None) -> None:
    """Draw Prospector, Hauler, Refinery or rival; ``color`` overrides trim.

    Phase is supplied simulation time, never wall time. Unknown kinds raise
    ValueError; nonpositive sizes are empty drawings. Supports are presentation
    only: drawing them implies no change to their passive gameplay role.
    """
    if kind not in ("prospector", "hauler", "refinery", "rival"):
        raise ValueError(f"Unknown ship kind: {kind}")
    if size <= 0:
        return
    h = _Hull(surface, x, y, heading, size)
    accent = color if color is not None else ((242, 111, 101) if kind == "rival" else _CYAN)
    engines = ((-.64, -.43), (-.64, .43)) if kind in ("prospector", "rival") else ((-.78, -.53), (-.78, .53))
    if thrust:
        length = .32 + .15 * (1 + math.sin(phase * 23)) / 2
        for ex, ey in engines:
            h.plate([(ex, ey-.12), (ex-length-.20, ey), (ex, ey+.12)], (29, 87, 117), None)
            h.plate([(ex, ey-.07), (ex-length, ey), (ex, ey+.07)], accent, None)
            h.line([(ex, ey), (ex-length*.55, ey)], (218, 248, 246))
    # Engine bodies are shared industrial equipment across all friendly hulls.
    for ex, ey in engines:
        h.plate([(ex-.12, ey-.14), (ex+.37, ey-.14), (ex+.43, ey),
                 (ex+.37, ey+.14), (ex-.12, ey+.14)], _DARK)
        h.line([(ex-.09, ey-.08), (ex-.09, ey+.08)], accent, 2)
        h.line([(ex+.03, ey-.09), (ex+.27, ey-.09)], _LIGHT)

    if kind == "prospector":
        # Narrow bridge, two mining outriggers, and a segmented arrowhead hull.
        h.plate([(-.55,-.40), (.25,-.66), (.47,-.50), (-.06,-.24),
                 (.95,0), (-.06,.24), (.47,.50), (.25,.66), (-.55,.40), (-.72,0)])
        h.plate([(-.45,-.23), (.08,-.27), (.95,0), (.08,.27), (-.45,.23)], (92,112,127))
        h.plate([(-.38,-.19), (.13,-.20), (.61,0), (.13,.20), (-.38,.19)], (45,62,77), None)
        h.plate([(.07,-.13), (.50,0), (.07,.13), (-.07,.08), (-.07,-.08)], accent, _LIGHT)
        for side in (-1, 1):
            h.line([(-.32,side*.37), (.20,side*.54)], _LIGHT)
            h.line([(.35,side*.49), (.58,side*.40)], accent, 2)
        h.plate([(-.42,-.12), (-.18,-.12), (-.18,.12), (-.42,.12)], _LIGHT, None)
        h.line([(-.39,0), (-.22,0)], _DARK)
    elif kind == "hauler":
        h.plate([(-.72,-.33), (.60,-.33), (.90,0), (.60,.33), (-.72,.33)])
        h.plate([(-.45,-.24), (.35,-.24), (.51,0), (.35,.24), (-.45,.24)], (100,120,132))
        for side in (-1, 1):
            h.plate([(-.57,side*.32), (.40,side*.32), (.50,side*.63),
                     (-.57,side*.63)], (57,77,94))
            for xx in (-.37, -.10, .17):
                h.line([(xx,side*.35), (xx,side*.60)], _LIGHT)
            h.line([(-.45,side*.65), (.22,side*.65)], accent, 2)
        h.plate([(.45,-.17), (.72,0), (.45,.17), (.31,0)], accent, _LIGHT)
        h.line([(-.34,0), (.15,0)], _DARK, 3)
    elif kind == "refinery":
        h.plate([(-.67,-.47), (.30,-.56), (.70,-.27), (.85,0),
                 (.70,.27), (.30,.56), (-.67,.47)], (73,93,106))
        for side in (-1, 1):
            h.plate([(-.57,side*.32), (.12,side*.32), (.35,side*.55),
                     (.15,side*.78), (-.57,side*.71)], (49,66,83))
            h.line([(-.40,side*.40), (-.40,side*.65)], accent, 2)
            h.line([(-.14,side*.40), (-.14,side*.68)], _LIGHT, 2)
        h.dot(-.20, 0, .30, _DARK)
        h.dot(-.20, 0, .22, _EDGE)
        h.dot(-.20, 0, .14, (42,67,78))
        h.dot(-.20, 0, .06, accent)
        h.plate([(.31,-.19), (.66,0), (.31,.19), (.18,0)], accent, _LIGHT)
    else:
        # Angular split wings and forward weapons keep enemies recognizable.
        h.plate([(-.68,-.39), (-.15,-.78), (.65,-.50), (.29,-.27),
                 (.97,0), (.29,.27), (.65,.50), (-.15,.78), (-.68,.39), (-.42,0)], (83,65,75))
        for side in (-1, 1):
            h.plate([(-.42,side*.38), (-.10,side*.61), (.40,side*.48),
                     (.03,side*.34)], (123,100,106), None)
            h.line([(.33,side*.46), (.74,side*.38)], accent, 2)
        h.plate([(-.23,-.18), (.65,0), (-.23,.18), (-.39,0)], _DARK)
        h.plate([(.05,-.10), (.40,0), (.05,.10), (-.09,0)], accent, None)
    h.dot(-.50, 0, .035, accent)


def draw_station(surface: pygame.Surface, x: float, y: float) -> None:
    """Draw the dock inside a 100-pixel radius; safe/dock rings belong to HUD."""
    h = _Hull(surface, x, y, 0, 100)
    pygame.draw.circle(surface, (24,42,54), (round(x),round(y)), 78, 12)
    pygame.draw.circle(surface, (88,120,135), (round(x),round(y)), 78, 2)
    for angle in (math.pi/4, 3*math.pi/4, 5*math.pi/4, 7*math.pi/4):
        arm = _Hull(surface, x, y, angle, 100)
        arm.plate([(.20,-.12),(.85,-.12),(.94,0),(.85,.12),(.20,.12)], (43,64,80))
        arm.plate([(.60,-.18),(.83,-.18),(.83,.18),(.60,.18)], (89,109,122))
        arm.line([(.69,-.12),(.69,.12)], _CYAN, 2)
    h.plate([(-.40,-.32),(.40,-.32),(.47,-.15),(.47,.30),(.33,.40),
             (-.33,.40),(-.47,.30),(-.47,-.15)], (83,103,117), _LIGHT)
    h.plate([(-.29,-.23),(.29,-.23),(.29,.25),(-.29,.25)], _DARK, _CYAN)
    for xx in (-.19, 0, .19):
        h.line([(xx,-.16),(xx,.14)], (40,67,80))
    h.line([(-.34,.33),(.34,.33)], (232,189,91), 3)
    for xx in (-.32, .32):
        h.dot(xx,-.30,.025,_CYAN)
    # Open docking approach and fixed chevrons convey the bay entrance.
    for yy in (.53, .69, .85):
        h.line([(-.10,yy+.06),(0,yy),(.10,yy+.06)], _CYAN)


def draw_asteroid(surface: pygame.Surface, rock: Rock) -> None:
    """Faceted rock with stable identity-dependent geometry and ore veins.

    All marks remain inside the modeled radius. Health/progress is a HUD concern.
    """
    if rock.radius <= 0:
        return
    h = _Hull(surface, rock.x, rock.y, (rock.id % 17)*.37, rock.radius)
    points = []
    for i in range(11):
        angle = math.tau*i/11
        radius = .83 + .15*(.5+.5*math.sin(rock.id*1.73+i*2.37))
        points.append((math.cos(angle)*radius, math.sin(angle)*radius))
    h.plate(points, (64,72,82), (113,126,139))
    center = (-.15,.09)
    for i in range(11):
        shade = 52 + ((i*13+rock.id*7) % 29)
        h.plate([center,points[i],points[(i+1)%11]], (shade,shade+8,shade+17), None)
    h.line([points[6],center,points[2]], (104,117,129))
    h.dot(-.34,-.25,.18,(43,51,63))
    h.dot(-.31,-.21,.13,(57,66,77))
    h.dot(.35,.25,.12,(45,54,65))
    ore = _ORE[rock.ore]
    h.line([(-.50,.30),(-.20,.20),(.02,.37),(.29,.15),(.48,.20)], ore, 2)
    h.line([(.02,.37),(.11,.60)], ore)
    h.plate([(.22,-.37),(.38,-.44),(.43,-.28),(.31,-.19)], ore, None)
