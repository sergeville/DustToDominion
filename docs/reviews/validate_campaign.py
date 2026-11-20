"""Reproducible pure-model acceptance/stress probe. No filesystem writes.

Run with the project's Python interpreter and --repo pointing at its checkout.
Uses only ordinary model commands for progression; no injected credits/cargo.
"""
import argparse
import json
import math
from pathlib import Path
import random
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
args = parser.parse_args()
sys.path.insert(0, str(Path(args.repo) / "src"))
from dtd.campaign import Campaign, InputState, STATION_X, STATION_Y, LAUNCH_Y, MAX_PROJECTILES


def sortie(campaign, sector):
    repair_paid = campaign.repair()
    run = campaign.launch(sector)
    elapsed = 0.0

    def tick(dt, controls):
        nonlocal elapsed
        run.step(dt, controls)
        elapsed += dt
        assert not run.defeated
        assert len(run.cargo) <= campaign.capacity
        assert len(run.projectiles) <= MAX_PROJECTILES

    def travel(x, y):
        for _ in range(1000):
            dx, dy = x - run.x, y - run.y
            distance = math.hypot(dx, dy)
            if distance < 0.01:
                return
            tick(min(0.1, distance / 300), InputState(dx / distance, dy / distance))
        raise AssertionError("Unable to reach waypoint")

    for _ in range(600):
        if not run.enemies:
            break
        enemy = min(run.enemies, key=lambda e: math.hypot(e.x - run.x, e.y - run.y))
        dx, dy = enemy.x - run.x, enemy.y - run.y
        distance = math.hypot(dx, dy)
        tick(0.1, InputState(dx / distance if distance > 330 else 0,
                            dy / distance if distance > 330 else 0,
                            firing=True, aim_x=enemy.x, aim_y=enemy.y))
    assert not run.enemies
    for rock in list(run.asteroids):
        if len(run.cargo) >= campaign.capacity:
            break
        travel(rock.x, rock.y)
        for _ in range(30):
            tick(0.1, InputState(mining=True))
            if rock.health == 0 or len(run.cargo) >= campaign.capacity:
                tick(0.1, InputState())
                break
    travel(STATION_X, STATION_Y)
    assert run.request_dock() and campaign.finish_run(run)
    sale = campaign.sell()
    assert Campaign.from_dict(campaign.to_dict()).to_dict() == campaign.to_dict()
    return {"sector": sector, "seconds": elapsed, "sale": sale, "bounty": run.bounty,
            "hull": campaign.hull, "repair_paid": repair_paid}


def progression(risky):
    campaign = Campaign()
    records = []
    def earn():
        records.append(sortie(campaign, campaign.unlocked_sector if risky else 1))
        assert len(records) < 50
    for item in ("cargo", "cargo", "laser", "laser", "miner", "ship", "ship", "engineer"):
        while campaign.credits < campaign.price(item):
            earn()
        assert campaign.buy(item)
    while not campaign.victory:
        earn()
    return {"expeditions": len(records), "seconds": round(sum(r["seconds"] for r in records), 2),
            "bank": campaign.credits, "fleet": campaign.ship_count, "crew": [campaign.miner, campaign.engineer],
            "hull": campaign.hull, "won": campaign.won,
            "runs": [{**r, "seconds": round(r["seconds"], 2)} for r in records]}


def earned_unlocks():
    campaign = Campaign()
    while campaign.unlocked_sector < 3:
        sortie(campaign, 1)
    return campaign


def station_exploit():
    campaign = earned_unlocks()
    results = []
    for sector in (2, 3):
        run = campaign.launch(sector)
        for _ in range(100):
            enemy = run.enemies[0]
            run.step(0.1, InputState(firing=True, aim_x=enemy.x, aim_y=enemy.y))
        assert run.bounty == 0 and not run.projectiles and len(run.enemies) == sector - 1
        assert (run.x, run.y, run.hull) == (STATION_X, LAUNCH_Y, 100)
        results.append({"sector": sector, "seconds": 10, "bounty": run.bounty,
                        "enemies_remaining": len(run.enemies), "hull": run.hull})
        # The readability update starts outside docking range, inside safety.
        for _ in range(60):
            if run.dock_ready:
                break
            run.step(1 / 60, InputState(move_y=1))
        assert run.request_dock() and campaign.finish_run(run)
    return results


def stress():
    campaign = earned_unlocks()
    rng = random.Random(20261120)
    steps = defeats = docks = abandons = maximum_projectiles = 0
    for number in range(120):
        sector = 1 + number % 3
        run = campaign.launch(sector)
        initial_ore = len(campaign.cargo) + (18, 24, 30)[sector - 1]
        for tick in range(1200):
            if run.finished:
                break
            if tick % 160 == 0:
                target = (rng.uniform(40, 1880), rng.uniform(190, 970))
            dx, dy = target[0] - run.x, target[1] - run.y
            length = max(1, math.hypot(dx, dy))
            enemy = min(run.enemies, key=lambda e: math.hypot(e.x - run.x, e.y - run.y), default=None)
            aim = (enemy.x, enemy.y) if enemy else target
            run.step(rng.choice((0, .001, 1 / 60, .05, .1, .25, 1)),
                     InputState(dx / length, dy / length, mining=True, firing=bool(number % 2),
                                aim_x=aim[0], aim_y=aim[1]))
            steps += 1
            maximum_projectiles = max(maximum_projectiles, len(run.projectiles))
            assert 40 <= run.x <= 1880 and 190 <= run.y <= 970
            assert 0 <= run.hull <= campaign.max_hull and len(run.cargo) <= campaign.capacity
            assert len(run.projectiles) <= MAX_PROJECTILES
            assert sum(a.health for a in run.asteroids) + len(run.pickups) + len(run.cargo) == initial_ore
            assert len({p.id for p in run.pickups}) == len(run.pickups)
            assert all(math.isfinite(v) for p in run.projectiles for v in (p.x, p.y, p.vx, p.vy, p.ttl))
            if tick > 600 and run.dock_ready:
                run.request_dock()
        if run.defeated:
            defeats += 1
        elif run.finished:
            docks += 1
        else:
            abandons += 1
        assert campaign.finish_run(run, defeated=not run.finished)
        campaign.sell()
        campaign.repair()
        assert Campaign.from_dict(campaign.to_dict()).to_dict() == campaign.to_dict()
    return {"expeditions": 120, "updates": steps, "defeats": defeats, "docks": docks,
            "forced_abandons": abandons, "maximum_projectiles": maximum_projectiles,
            "invariants": "passed"}


print(json.dumps({"safe_campaign": progression(False), "risky_campaign": progression(True),
                  "station_exploit_regression": station_exploit(), "stress": stress()}, indent=2))
