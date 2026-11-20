"""Behavioral regressions for the finite campaign, independent of rendering."""
from copy import deepcopy
import math

import pytest

from dtd.campaign import (
    Campaign, InputState, Projectile, MAX_PROJECTILES, STATION_X, STATION_Y,
    WORLD_LEFT, WORLD_TOP, WORLD_RIGHT, WORLD_BOTTOM, SAFE_RADIUS,
)


def travel(run, x, y):
    """Reach a coordinate using ordinary movement, without teleporting state."""
    for _ in range(1000):
        dx, dy = x - run.x, y - run.y
        distance = math.hypot(dx, dy)
        if distance < 0.01:
            return
        assert not run.finished, "Travel unexpectedly ended in defeat"
        run.step(min(0.1, distance / 300), InputState(dx / distance, dy / distance))
    pytest.fail("Movement did not reach destination")


def mine_safe_sortie(campaign):
    run = campaign.launch(1)
    for rock in list(run.asteroids):
        if len(run.cargo) >= campaign.capacity:
            break
        travel(run, rock.x, rock.y)
        for _ in range(30):
            run.step(0.1, InputState(mining=True))
            if rock.health == 0 or len(run.cargo) >= campaign.capacity:
                # Collection happens after ore has spawned, on the next tick.
                run.step(0.1, InputState())
                break
    travel(run, STATION_X, STATION_Y)
    assert run.request_dock()
    assert campaign.finish_run(run)
    return campaign.sell()


def test_new_campaign_and_prices():
    campaign = Campaign()
    assert (campaign.credits, campaign.hull, campaign.capacity, campaign.ship_count) == (80, 100, 12, 1)
    assert campaign.price("cargo") == 100
    assert not campaign.buy("cargo")
    assert campaign.price("invalid") is None
    assert not campaign.buy("invalid")
    assert campaign.sell() == campaign.repair() == 0
    assert not campaign.victory
    with pytest.raises(ValueError):
        campaign.launch(2)
    with pytest.raises(ValueError):
        campaign.launch(True)


def test_movement_normalization_bounds_and_stall_clamp():
    run = Campaign().launch(1)
    run.step(20, InputState(1, -1))
    assert math.hypot(run.x - STATION_X, run.y - STATION_Y) == pytest.approx(75)
    for _ in range(40):
        run.step(0.25, InputState(-1, -1))
    assert (run.x, run.y) == (WORLD_LEFT, WORLD_TOP)
    for bad in (-1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            run.step(bad, InputState())
    with pytest.raises(ValueError):
        run.step(0.1, InputState(move_x=float("nan")))


def test_zero_time_and_finished_expedition_do_not_advance():
    run = Campaign().launch(1)
    run.step(0, InputState(1, 1, True, True))
    assert run.x == STATION_X and not run.projectiles
    assert run.request_dock()
    run.step(0.25, InputState(1, 1, True, True))
    assert run.x == STATION_X and not run.projectiles
    assert not run.request_dock()


def test_mining_range_cooldown_collect_once_and_conservation():
    campaign = Campaign()
    run = campaign.launch(1)
    run.step(0.25, InputState(mining=True))
    assert not run.pickups and sum(r.health for r in run.asteroids) == 18
    rock = run.asteroids[0]
    travel(run, rock.x, rock.y)
    run.step(0.001, InputState(mining=True))
    assert rock.health == 2 and len(run.pickups) == 1 and not run.cargo
    run.step(0.1, InputState(mining=True))
    assert rock.health == 2 and run.cargo == [0] and not run.pickups
    for _ in range(20):
        run.step(0.1, InputState(mining=True))
    assert rock not in run.asteroids
    assert len(run.cargo) == 3 and not run.pickups
    assert sum(r.health for r in run.asteroids) + len(run.cargo) == 18
    for _ in range(5):
        run.step(0.1, InputState())
    assert len(run.cargo) == 3


def test_cargo_capacity_and_station_actions_cannot_change_active_run():
    campaign = Campaign(credits=1000, cargo=[0] * 12)
    run = campaign.launch(1)
    rock = run.asteroids[0]
    travel(run, rock.x, rock.y)
    run.step(0.25, InputState(mining=True))
    assert rock.health == 3 and len(run.cargo) == 12
    assert not campaign.buy("cargo")
    assert campaign.sell() == campaign.repair() == 0
    with pytest.raises(ValueError):
        campaign.launch(1)
    with pytest.raises(ValueError):
        campaign.to_dict()
    assert not campaign.finish_run(run)
    assert not run.request_dock()


def test_mining_upgrades_and_crew_reduce_cooldown():
    def mined(campaign):
        run = campaign.launch(1)
        rock = run.asteroids[0]
        travel(run, rock.x, rock.y)
        for _ in range(5):
            run.step(0.1, InputState(mining=True))
        return 3 - rock.health
    assert mined(Campaign()) == 1
    upgraded = Campaign(credits=1000)
    assert upgraded.buy("laser") and upgraded.buy("laser") and upgraded.buy("miner")
    assert mined(upgraded) == 2


def test_upgrades_prices_limits_and_sale_bonuses():
    campaign = Campaign(credits=10000)
    for item in ("cargo", "laser", "hull", "ship"):
        first = campaign.price(item)
        before = campaign.credits
        assert campaign.buy(item)
        assert campaign.credits == before - first
        assert campaign.buy(item)
        assert campaign.price(item) is None
        assert not campaign.buy(item)
    assert campaign.capacity == 24 and campaign.max_hull == campaign.hull == 150
    assert campaign.ship_count == 3
    for item in ("miner", "engineer"):
        assert campaign.buy(item)
        assert not campaign.buy(item)
    campaign.cargo = [0, 1, 2]
    assert campaign.cargo_value() == 84  # floor((10 + 20 + 35) * 1.3)
    assert campaign.sell() == 84
    assert campaign.lifetime_sales == 84 and campaign.cargo == []
    assert campaign.sell() == 0


def test_repair_is_affordable_and_never_overheals():
    campaign = Campaign(credits=3, hull=90)
    assert campaign.repair() == 3
    assert campaign.hull == 96 and campaign.credits == 0
    assert campaign.repair() == 0
    campaign.credits = 10
    campaign.hull = 99.5
    assert campaign.repair() == 1
    assert campaign.hull == 100 and campaign.credits == 9


def test_sector_content_and_unlock_thresholds():
    for sales, sector, total, enemies in ((0, 1, 18, 0), (300, 2, 24, 1), (1000, 3, 30, 2)):
        campaign = Campaign(lifetime_sales=sales)
        assert campaign.unlocked_sector == sector
        run = campaign.launch(sector)
        assert sum(rock.health for rock in run.asteroids) == total
        assert len(run.enemies) == enemies
        assert all(rock.ore == sector - 1 for rock in run.asteroids)
    assert Campaign(lifetime_sales=299).unlocked_sector == 1
    assert Campaign(lifetime_sales=999).unlocked_sector == 2


def test_player_can_fight_a_rival_and_collect_bounty_once():
    campaign = Campaign(lifetime_sales=300)
    run = campaign.launch(2)
    enemy = run.enemies[0]
    travel(run, enemy.x, enemy.y + 300)
    for _ in range(60):
        run.step(0.1, InputState(firing=True, aim_x=enemy.x, aim_y=enemy.y))
        if not run.enemies:
            break
    assert not run.enemies and run.bounty == 70 and run.hull > 0
    for _ in range(30):
        run.step(0.1, InputState(firing=True, aim_x=enemy.x, aim_y=enemy.y))
    assert run.bounty == 70
    travel(run, STATION_X, STATION_Y)
    assert run.request_dock() and campaign.finish_run(run)
    assert campaign.credits == 150
    assert not campaign.finish_run(run)
    assert campaign.credits == 150


def test_station_protects_player_and_projectiles_stay_bounded():
    campaign = Campaign(lifetime_sales=1000)
    run = campaign.launch(3)
    run.projectiles.append(Projectile(run.x, run.y, 0, 0, 500, False))
    for _ in range(100):
        run.step(0.25, InputState(firing=True))
        assert len(run.projectiles) <= MAX_PROJECTILES
        assert all(WORLD_LEFT <= shot.x <= WORLD_RIGHT and WORLD_TOP <= shot.y <= WORLD_BOTTOM
                   for shot in run.projectiles)
    assert run.hull == 100 and len(run.enemies) == 2


def test_rival_cannot_chase_or_shoot_through_station_safe_region():
    run = Campaign(lifetime_sales=300).launch(2)
    # Put a pursuer opposite a player outside the safe region. The direct
    # pursuit path crosses the station, so the enemy must stop at its boundary.
    run.x, run.y = STATION_X + 350, STATION_Y
    enemy = run.enemies[0]
    enemy.x, enemy.y = STATION_X - 230, STATION_Y
    for _ in range(80):
        run.step(0.1, InputState())
        assert math.hypot(enemy.x - STATION_X, enemy.y - STATION_Y) > SAFE_RADIUS
        assert WORLD_LEFT <= enemy.x <= WORLD_RIGHT
        assert WORLD_TOP <= enemy.y <= WORLD_BOTTOM
    assert run.hull == 100  # Incoming shots are absorbed by the safe region.


def test_station_cannot_be_used_to_farm_bounties_without_launching_into_danger():
    campaign = Campaign()
    while campaign.unlocked_sector < 3:
        mine_safe_sortie(campaign)
    for sector in (2, 3):
        run = campaign.launch(sector)
        for _ in range(100):
            enemy = run.enemies[0]
            run.step(0.1, InputState(firing=True, aim_x=enemy.x, aim_y=enemy.y))
        assert (run.x, run.y, run.hull) == (STATION_X, STATION_Y, 100)
        assert len(run.enemies) == sector - 1 and run.bounty == 0
        assert not run.projectiles
        assert run.request_dock() and campaign.finish_run(run)


@pytest.mark.parametrize("friendly", [False, True])
def test_station_shield_absorbs_all_crossing_projectiles_including_grazes(friendly):
    run = Campaign().launch(1)
    # Both endpoints lie outside the shield, but the middle of this short
    # segment passes through its top edge: endpoint-only collision misses it.
    start_x, y = STATION_X - 6, STATION_Y - SAFE_RADIUS + 0.01
    assert math.hypot(start_x - STATION_X, y - STATION_Y) > SAFE_RADIUS
    assert math.hypot(start_x + 13 - STATION_X, y - STATION_Y) > SAFE_RADIUS
    run.projectiles.append(Projectile(start_x, y, 780, 0, 30, friendly))
    run.step(1 / 60, InputState())
    assert not run.projectiles and run.hull == 100


def test_player_cannot_snipe_beyond_rival_detection_range():
    campaign = Campaign()
    while campaign.unlocked_sector < 2:
        mine_safe_sortie(campaign)
    run = campaign.launch(2)
    travel(run, 1500, 500)
    enemy = run.enemies[0]
    assert math.hypot(enemy.x - run.x, enemy.y - run.y) > 680
    for _ in range(80):
        run.step(0.1, InputState(firing=True, aim_x=enemy.x, aim_y=enemy.y))
        assert all(math.hypot(shot.x - run.x, shot.y - run.y) <= 585
                   for shot in run.projectiles if shot.friendly)
    assert enemy.hull == 75 and run.bounty == 0
    assert run.hull == 100


def test_complete_campaign_through_dangerous_sectors_requires_and_survives_combat():
    campaign = Campaign()
    sectors, bounties = [], []

    def expedition():
        campaign.repair()
        sector = campaign.unlocked_sector
        run = campaign.launch(sector)
        # Approach a visible rival and aim continuously, using normal movement
        # and firing. The station shield must be left before a shot can fire.
        for _ in range(600):
            if not run.enemies:
                break
            enemy = min(run.enemies, key=lambda e: math.hypot(e.x - run.x, e.y - run.y))
            dx, dy = enemy.x - run.x, enemy.y - run.y
            distance = math.hypot(dx, dy)
            run.step(0.1, InputState(dx / distance if distance > 330 else 0,
                                    dy / distance if distance > 330 else 0,
                                    firing=True, aim_x=enemy.x, aim_y=enemy.y))
            assert not run.finished
        assert not run.enemies
        for rock in list(run.asteroids):
            if len(run.cargo) >= campaign.capacity:
                break
            travel(run, rock.x, rock.y)
            for _ in range(30):
                run.step(0.1, InputState(mining=True))
                if rock.health == 0 or len(run.cargo) >= campaign.capacity:
                    run.step(0.1, InputState())
                    break
        travel(run, STATION_X, STATION_Y)
        assert run.request_dock() and campaign.finish_run(run)
        assert campaign.sell() > 0
        assert Campaign.from_dict(campaign.to_dict()).to_dict() == campaign.to_dict()
        sectors.append(sector)
        bounties.append(run.bounty)

    for item in ("cargo", "cargo", "laser", "laser", "miner", "ship", "ship", "engineer"):
        while campaign.credits < campaign.price(item):
            expedition()
        assert campaign.buy(item)
    while not campaign.victory:
        expedition()
        assert len(sectors) < 20
    assert {1, 2, 3} == set(sectors)
    assert 70 in bounties and 180 in bounties
    assert campaign.won and campaign.ship_count == 3 and campaign.miner and campaign.engineer


def test_exposed_pilot_takes_real_rival_damage_and_can_retreat_and_repair():
    campaign = Campaign()
    while campaign.unlocked_sector < 2:
        mine_safe_sortie(campaign)
    run = campaign.launch(2)
    enemy = run.enemies[0]
    travel(run, enemy.x, enemy.y + 300)
    for _ in range(40):
        run.step(0.1, InputState())
        if run.hull < campaign.max_hull:
            break
    assert 0 < run.hull < campaign.max_hull
    travel(run, STATION_X, STATION_Y)
    assert run.request_dock() and campaign.finish_run(run)
    before = campaign.credits
    assert campaign.repair() > 0
    assert campaign.credits < before and campaign.hull == campaign.max_hull


def test_engineer_reduces_damage_and_defeat_recovers_free():
    campaign = Campaign(credits=0, cargo=[2], engineer=True)
    run = campaign.launch(1)
    travel(run, 350, 500)
    run.projectiles.append(Projectile(run.x, run.y, 0, 0, 20, False))
    run.step(0.01, InputState())
    assert run.hull == 83
    run.projectiles.append(Projectile(run.x, run.y, 0, 0, 1000, False))
    run.step(0.01, InputState())
    assert run.finished and run.defeated and run.hull == 0
    assert campaign.finish_run(run)
    assert campaign.hull == 50 and campaign.credits == 0 and campaign.cargo == []
    assert mine_safe_sortie(campaign) == 120
    assert campaign.credits == 120


def test_abandon_discards_cargo_and_repeated_finish_is_noop():
    campaign = Campaign(cargo=[2], hull=80)
    run = campaign.launch(1)
    assert campaign.finish_run(run, defeated=True)
    assert campaign.hull == 50 and campaign.cargo == []
    assert run.finished and run.defeated
    assert not campaign.finish_run(run, defeated=True)


def test_complete_campaign_victory_with_only_reachable_actions():
    campaign = Campaign()
    sorties = 0
    # No injected cargo, currency, position or unlocks: every credit is mined,
    # physically collected, carried home, and explicitly sold.
    for item in ("cargo", "cargo", "laser", "laser", "miner", "ship", "ship", "engineer"):
        while campaign.credits < campaign.price(item):
            assert mine_safe_sortie(campaign) > 0
            sorties += 1
        assert campaign.buy(item)
    while not campaign.victory:
        assert mine_safe_sortie(campaign) > 0
        sorties += 1
        assert sorties < 50
    assert campaign.won and campaign.ship_count == 3
    assert campaign.miner and campaign.engineer and campaign.credits >= 1200
    assert campaign.unlocked_sector == 3
    checkpoint = Campaign.from_dict(campaign.to_dict())
    assert checkpoint.victory
    assert checkpoint.buy("hull")  # Victory remains earned after spending.
    assert checkpoint.victory
    assert mine_safe_sortie(checkpoint) > 0


def test_checkpoint_roundtrip_copies_mutable_state():
    original = Campaign(credits=1300, hull=75, cargo=[0, 1, 2], support_ships=2,
                        miner=True, engineer=True, lifetime_sales=1900)
    payload = original.to_dict()
    restored = Campaign.from_dict(payload)
    assert restored.to_dict() == payload
    assert restored.won
    payload["cargo"].clear()
    payload["upgrades"]["cargo"] = 2
    assert original.cargo == restored.cargo == [0, 1, 2]
    assert original.capacity == restored.capacity == 12


@pytest.mark.parametrize("field,value", [
    ("credits", -1), ("credits", True), ("credits", 1.5), ("credits", 10**13),
    ("lifetime_sales", -1), ("hull", 0), ("hull", 101), ("hull", True),
    ("hull", float("nan")), ("hull", float("inf")), ("hull", "100"),
    ("cargo", [3]), ("cargo", [-1]), ("cargo", [True]), ("cargo", [0] * 13),
    ("cargo", {}), ("support_ships", 3), ("support_ships", True),
    ("miner", 1), ("engineer", "false"), ("won", True), ("won", 0),
    ("upgrades", {"cargo": 3, "laser": 0, "hull": 0}),
    ("upgrades", {"cargo": True, "laser": 0, "hull": 0}),
    ("upgrades", {"cargo": 0, "laser": 0}),
])
def test_checkpoint_rejects_invalid_state(field, value):
    payload = Campaign().to_dict()
    payload[field] = value
    with pytest.raises(ValueError):
        Campaign.from_dict(payload)


@pytest.mark.parametrize("payload", [None, [], {}, {"unexpected": 1}])
def test_checkpoint_rejects_wrong_shape(payload):
    with pytest.raises(ValueError):
        Campaign.from_dict(payload)


def test_checkpoint_rejects_unknown_fields_without_mutation():
    payload = Campaign().to_dict()
    payload["extra"] = 3
    before = deepcopy(payload)
    with pytest.raises(ValueError):
        Campaign.from_dict(payload)
    assert payload == before
