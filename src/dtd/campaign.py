"""Finite mining campaign. Pure simulation: no display, clock, filesystem or RNG.

The application owns a Campaign and finishes its active Expedition before saving.
Coordinates are the same 1920 x 1080 logical units used by the existing UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any

STATION_X, STATION_Y = 960.0, 870.0
DOCK_RADIUS, SAFE_RADIUS = 110.0, 220.0
WORLD_LEFT, WORLD_RIGHT = 40.0, 1880.0
WORLD_TOP, WORLD_BOTTOM = 190.0, 970.0
MINE_RANGE = 175.0
ORE_PRICES = (10, 20, 35)
MAX_PROJECTILES = 96
_UPGRADE_PRICES = {"cargo": (100, 180), "laser": (120, 220), "hull": (100, 180)}


@dataclass(frozen=True)
class InputState:
    move_x: float = 0.0
    move_y: float = 0.0
    mining: bool = False
    firing: bool = False
    aim_x: float = STATION_X
    aim_y: float = 0.0


@dataclass
class Asteroid:
    id: int
    x: float
    y: float
    radius: float
    ore: int
    health: int = 3
    max_health: int = 3


@dataclass
class Pickup:
    id: int
    x: float
    y: float
    ore: int
    radius: float = 12.0


@dataclass
class Enemy:
    id: int
    x: float
    y: float
    hull: float = 75.0
    heading: float = 0.0
    radius: float = 24.0
    cooldown: float = 1.0


@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    damage: float
    friendly: bool
    ttl: float = 2.0
    radius: float = 5.0


@dataclass
class Campaign:
    credits: int = 80
    hull: float = 100.0
    cargo: list[int] = field(default_factory=list)
    upgrades: dict[str, int] = field(default_factory=lambda: {"cargo": 0, "laser": 0, "hull": 0})
    support_ships: int = 0
    miner: bool = False
    engineer: bool = False
    lifetime_sales: int = 0
    won: bool = False
    _active: Expedition | None = field(default=None, init=False, repr=False, compare=False)

    @property
    def capacity(self) -> int:
        return 12 + 6 * self.upgrades["cargo"]

    @property
    def max_hull(self) -> int:
        return 100 + 25 * self.upgrades["hull"]

    @property
    def ship_count(self) -> int:
        return 1 + self.support_ships

    @property
    def unlocked_sector(self) -> int:
        return 3 if self.lifetime_sales >= 1000 else 2 if self.lifetime_sales >= 300 else 1

    @property
    def victory(self) -> bool:
        return self.won or (self.support_ships == 2 and self.miner and self.engineer and self.credits >= 1200)

    def _check_victory(self) -> None:
        self.won = self.victory

    def price(self, item: str) -> int | None:
        if item in _UPGRADE_PRICES:
            level = self.upgrades[item]
            return _UPGRADE_PRICES[item][level] if level < 2 else None
        if item == "ship":
            return (350, 650)[self.support_ships] if self.support_ships < 2 else None
        if item == "miner":
            return None if self.miner else 150
        if item == "engineer":
            return None if self.engineer else 200
        return None

    def cargo_value(self) -> int:
        base = sum(ORE_PRICES[grade] for grade in self.cargo)
        bonus = (0, 10, 30)[self.support_ships]
        return base * (100 + bonus) // 100

    def sell(self) -> int:
        if self._active is not None:
            return 0
        proceeds = self.cargo_value()
        self.credits += proceeds
        self.lifetime_sales += proceeds
        self.cargo.clear()
        self._check_victory()
        return proceeds

    def buy(self, item: str) -> bool:
        price = self.price(item)
        if self._active is not None or price is None or self.credits < price:
            return False
        self.credits -= price
        if item in _UPGRADE_PRICES:
            self.upgrades[item] += 1
            if item == "hull":
                self.hull += 25
        elif item == "ship":
            self.support_ships += 1
        else:
            setattr(self, item, True)
        self._check_victory()
        return True

    def repair(self) -> int:
        if self._active is not None:
            return 0
        cost = min(self.credits, math.ceil(max(0, self.max_hull - self.hull) / 2))
        self.credits -= cost
        self.hull = min(self.max_hull, self.hull + cost * 2)
        return cost

    def launch(self, sector: int) -> Expedition:
        if type(sector) is not int or not 1 <= sector <= self.unlocked_sector or self._active is not None:
            raise ValueError("Sector unavailable or an expedition is already active")
        self._active = Expedition(self, sector)
        return self._active

    def finish_run(self, expedition: Expedition, defeated: bool = False) -> bool:
        if expedition is not self._active or (not expedition.finished and not defeated):
            return False
        lost = defeated or expedition.defeated
        if lost:
            expedition.defeated = True
            expedition.finished = True
            self.hull = self.max_hull / 2
            self.cargo = []
        else:
            self.hull = expedition.hull
            self.cargo = list(expedition.cargo)
        self.credits += expedition.bounty
        self._active = None
        self._check_victory()
        return True

    def to_dict(self) -> dict[str, Any]:
        if self._active is not None:
            raise ValueError("Only station checkpoints can be saved")
        self._check_victory()
        return {"credits": self.credits, "hull": self.hull, "cargo": list(self.cargo),
                "upgrades": dict(self.upgrades), "support_ships": self.support_ships,
                "miner": self.miner, "engineer": self.engineer,
                "lifetime_sales": self.lifetime_sales, "won": self.won}

    @classmethod
    def from_dict(cls, data: Any) -> Campaign:
        keys = {"credits", "hull", "cargo", "upgrades", "support_ships", "miner", "engineer", "lifetime_sales", "won"}
        if type(data) is not dict or set(data) != keys:
            raise ValueError("Invalid campaign fields")

        def integer(value: Any, low: int, high: int) -> bool:
            return type(value) is int and low <= value <= high

        if not integer(data["credits"], 0, 10**12) or not integer(data["lifetime_sales"], 0, 10**12):
            raise ValueError("Invalid campaign credits or sales")
        upgrades = data["upgrades"]
        if type(upgrades) is not dict or set(upgrades) != set(_UPGRADE_PRICES) or not all(integer(v, 0, 2) for v in upgrades.values()):
            raise ValueError("Invalid upgrades")
        if not integer(data["support_ships"], 0, 2) or any(type(data[k]) is not bool for k in ("miner", "engineer", "won")):
            raise ValueError("Invalid fleet or crew")
        hull = data["hull"]
        if type(hull) not in (int, float) or not 0 < hull <= 100 + upgrades["hull"] * 25:
            raise ValueError("Invalid hull")
        cargo = data["cargo"]
        if type(cargo) is not list or len(cargo) > 12 + upgrades["cargo"] * 6 or not all(integer(v, 0, 2) for v in cargo):
            raise ValueError("Invalid cargo")
        if data["won"] and not (data["support_ships"] == 2 and data["miner"] and data["engineer"]):
            raise ValueError("Invalid victory state")
        result = cls(**{**data, "hull": float(hull), "cargo": list(cargo), "upgrades": dict(upgrades)})
        result._check_victory()
        return result


@dataclass
class Expedition:
    campaign: Campaign = field(repr=False)
    sector: int
    x: float = STATION_X
    y: float = STATION_Y
    heading: float = -math.pi / 2
    asteroids: list[Asteroid] = field(default_factory=list)
    pickups: list[Pickup] = field(default_factory=list)
    enemies: list[Enemy] = field(default_factory=list)
    projectiles: list[Projectile] = field(default_factory=list)
    hull: float = field(init=False)
    cargo: list[int] = field(init=False)
    finished: bool = False
    defeated: bool = False
    bounty: int = 0
    _mine_cooldown: float = field(default=0, init=False, repr=False)
    _fire_cooldown: float = field(default=0, init=False, repr=False)
    _pickup_id: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.hull = self.campaign.hull
        self.cargo = list(self.campaign.cargo)
        positions = [(350, 630), (660, 570), (1230, 570), (1550, 630), (430, 330), (1430, 330),
                     (850, 350), (1080, 350), (180, 450), (1730, 450)]
        self.asteroids = [Asteroid(i, x, y, 46, self.sector - 1) for i, (x, y) in enumerate(positions[:4 + self.sector * 2])]
        if self.sector > 1:
            self.enemies = [Enemy(i, x, 240.0) for i, x in enumerate((350.0, 1550.0, 960.0)[:self.sector - 1])]

    @property
    def dock_ready(self) -> bool:
        return not self.defeated and math.hypot(self.x - STATION_X, self.y - STATION_Y) <= DOCK_RADIUS

    def request_dock(self) -> bool:
        if self.finished or not self.dock_ready:
            return False
        self.finished = True
        return True

    def step(self, dt: float, controls: InputState) -> None:
        if not isinstance(dt, (int, float)) or not math.isfinite(dt) or dt < 0:
            raise ValueError("Simulation time must be finite and nonnegative")
        if self.finished:
            return
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (controls.move_x, controls.move_y, controls.aim_x, controls.aim_y)):
            raise ValueError("Input coordinates must be finite")
        remaining = min(dt, 0.25)
        while remaining > 1e-10 and not self.finished:
            elapsed = min(remaining, 1 / 60)
            self._tick(elapsed, controls)
            remaining -= elapsed

    def _tick(self, dt: float, controls: InputState) -> None:
        dx, dy = max(-1, min(1, controls.move_x)), max(-1, min(1, controls.move_y))
        length = max(1.0, math.hypot(dx, dy))
        self.x = max(WORLD_LEFT, min(WORLD_RIGHT, self.x + dx / length * 300 * dt))
        self.y = max(WORLD_TOP, min(WORLD_BOTTOM, self.y + dy / length * 300 * dt))
        self.heading = math.atan2(controls.aim_y - self.y, controls.aim_x - self.x)
        self._mine_cooldown = max(0, self._mine_cooldown - dt)
        self._fire_cooldown = max(0, self._fire_cooldown - dt)
        uncollected = []
        for pickup in self.pickups:
            if len(self.cargo) < self.campaign.capacity and math.hypot(pickup.x - self.x, pickup.y - self.y) <= 55:
                self.cargo.append(pickup.ore)
            else:
                uncollected.append(pickup)
        self.pickups = uncollected
        if controls.mining and self._mine_cooldown <= 1e-9 and len(self.cargo) < self.campaign.capacity:
            nearby = [rock for rock in self.asteroids if math.hypot(rock.x - self.x, rock.y - self.y) <= MINE_RANGE]
            if nearby:
                rock = min(nearby, key=lambda item: ((item.x - self.x)**2 + (item.y - self.y)**2, item.id))
                rock.health -= 1
                self._pickup_id += 1
                self.pickups.append(Pickup(self._pickup_id, rock.x, rock.y, rock.ore))
                self._mine_cooldown = 0.6 / (1 + 0.25 * self.campaign.upgrades["laser"] + 0.15 * self.campaign.miner)
                self.asteroids = [item for item in self.asteroids if item.health > 0]
        if controls.firing and self._fire_cooldown <= 1e-9 and len(self.projectiles) < MAX_PROJECTILES:
            self.projectiles.append(Projectile(self.x, self.y, math.cos(self.heading) * 780, math.sin(self.heading) * 780,
                                               24 * (1 + 0.25 * self.campaign.upgrades["laser"]), True))
            self._fire_cooldown = 0.22
        safe = math.hypot(self.x - STATION_X, self.y - STATION_Y) <= SAFE_RADIUS
        for enemy in self.enemies:
            enemy.cooldown = max(0, enemy.cooldown - dt)
            distance = math.hypot(self.x - enemy.x, self.y - enemy.y)
            if safe or distance > 680:
                continue
            enemy.heading = math.atan2(self.y - enemy.y, self.x - enemy.x)
            if distance > 310:
                nx = enemy.x + math.cos(enemy.heading) * 95 * dt
                ny = enemy.y + math.sin(enemy.heading) * 95 * dt
                if math.hypot(nx - STATION_X, ny - STATION_Y) > SAFE_RADIUS:
                    enemy.x, enemy.y = nx, ny
            if distance <= 600 and enemy.cooldown <= 1e-9 and len(self.projectiles) < MAX_PROJECTILES:
                self.projectiles.append(Projectile(enemy.x, enemy.y, math.cos(enemy.heading) * 330,
                                                   math.sin(enemy.heading) * 330, 10 + self.sector * 2, False))
                enemy.cooldown = 1.3
        surviving = []
        for shot in self.projectiles:
            shot.x += shot.vx * dt
            shot.y += shot.vy * dt
            shot.ttl -= dt
            if shot.ttl <= 0 or not WORLD_LEFT <= shot.x <= WORLD_RIGHT or not WORLD_TOP <= shot.y <= WORLD_BOTTOM:
                continue
            hit = False
            if shot.friendly:
                for enemy in self.enemies:
                    if enemy.hull > 0 and math.hypot(shot.x - enemy.x, shot.y - enemy.y) <= enemy.radius + shot.radius:
                        enemy.hull -= shot.damage
                        hit = True
                        if enemy.hull <= 0:
                            self.bounty += 30 + self.sector * 20
                        break
            elif math.hypot(shot.x - STATION_X, shot.y - STATION_Y) <= SAFE_RADIUS:
                hit = True
            elif not safe and math.hypot(shot.x - self.x, shot.y - self.y) <= 23 + shot.radius:
                self.hull = max(0, self.hull - shot.damage * (0.85 if self.campaign.engineer else 1.0))
                hit = True
            if not hit:
                surviving.append(shot)
        self.projectiles = surviving
        self.enemies = [enemy for enemy in self.enemies if enemy.hull > 0]
        if self.hull <= 0:
            self.defeated = self.finished = True
