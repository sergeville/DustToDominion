from copy import deepcopy
from dataclasses import FrozenInstanceError
import math

import pytest

from dtd.campaign import (Asteroid, Campaign, InputState, MINE_RANGE, Pickup,
                          STATION_X, STATION_Y, WORLD_LEFT, WORLD_TOP)
from dtd.campaign_guidance import guidance, mining_target


def flight():
    campaign = Campaign()
    return campaign, campaign.launch(1)


def test_fresh_launch_approaches_nearest_ore_instead_of_docking():
    campaign, run = flight()
    result = guidance(campaign, run)
    expected = min(run.asteroids, key=lambda r: ((r.x - run.x)**2 + (r.y - run.y)**2, r.id))
    assert run.dock_ready
    assert result.key == "approach"
    assert result.target == (expected.x, expected.y) and result.target_id == expected.id
    assert result.distance == pytest.approx(math.hypot(expected.x - run.x, expected.y - run.y))
    assert result.progress == 0


@pytest.mark.parametrize("cargo,hull", [([0], 100), ([], 99), ([0] * 12, 100), ([], 30)])
def test_loaded_or_damaged_ship_at_dock_gets_dock_priority(cargo, hull):
    campaign, run = flight()
    run.cargo, run.hull = cargo, hull
    run.pickups = [Pickup(0, run.x, run.y, 0)]
    result = guidance(campaign, run)
    assert result.key == "dock" and result.target == (STATION_X, STATION_Y)
    assert result.distance == 0 and result.progress is None


def test_dock_radius_boundary_is_not_shield_radius():
    campaign, run = flight()
    run.cargo = [0]
    run.x = STATION_X + 110
    assert guidance(campaign, run).key == "dock"
    run.x += 0.001
    assert guidance(campaign, run).key != "dock"
    run.x = STATION_X + 200
    assert guidance(campaign, run).key != "dock"


def test_full_cargo_prioritizes_return_over_pickups_and_rocks():
    campaign, run = flight()
    run.x, run.y = 350, 630
    run.cargo = [0] * campaign.capacity
    run.pickups = [Pickup(9, run.x, run.y, 0)]
    assert guidance(campaign, run).key == "return_full"
    assert mining_target(campaign, run) is None
    run.hull = 10
    assert guidance(campaign, run).key == "return_full"


def test_low_hull_threshold_uses_upgraded_maximum_and_overrides_collection():
    campaign = Campaign(credits=1000)
    assert campaign.buy("hull") and campaign.buy("hull")
    run = campaign.launch(1)
    run.x, run.y = 350, 630
    run.pickups = [Pickup(1, run.x, run.y, 0)]
    run.hull = 45
    assert guidance(campaign, run).key == "return_damaged"
    run.hull = 45.001
    assert guidance(campaign, run).key == "collect"


def test_partial_damage_far_from_dock_still_guides_mining():
    campaign, run = flight()
    run.x, run.y, run.hull = 350, 630, 99
    assert guidance(campaign, run).key == "mine"


def test_pickups_take_priority_but_do_not_change_actual_mining_target():
    campaign, run = flight()
    run.x, run.y = 350, 630
    rock = run.asteroids[0]
    run.pickups = [Pickup(8, 360, 630, 0)]
    result = guidance(campaign, run)
    assert result.key == "collect" and result.target_id == 8
    assert result.target == (360, 630) and result.distance == 10
    assert mining_target(campaign, run) is rock


def test_pickup_selection_is_distance_then_id_and_independent_of_list_order():
    campaign, run = flight()
    run.x, run.y = 500, 500
    run.pickups = [Pickup(7, 510, 500, 0), Pickup(2, 490, 500, 0), Pickup(0, 525, 500, 0)]
    assert guidance(campaign, run).target_id == 2
    run.pickups.reverse()
    assert guidance(campaign, run).target_id == 2


def test_mining_boundary_tie_break_and_target_match_model():
    campaign, run = flight()
    run.x, run.y = 500, 500
    run.asteroids = [Asteroid(7, 500 + MINE_RANGE, 500, 46, 0),
                     Asteroid(2, 500 - MINE_RANGE, 500, 46, 0)]
    target = mining_target(campaign, run)
    assert target.id == 2
    assert guidance(campaign, run).key == "mine"
    assert guidance(campaign, run).distance == MINE_RANGE
    run.step(0.001, InputState(mining=True))
    assert target.health == 2 and run.asteroids[0].health == 3
    # The ore now guides collection, but the beam retains the model's rock.
    assert guidance(campaign, run).key == "collect"
    assert mining_target(campaign, run) is target


def test_just_outside_mining_range_approaches_and_excludes_dead_rocks():
    campaign, run = flight()
    run.x, run.y = 500, 500
    live = Asteroid(2, 500 + MINE_RANGE + 0.001, 500, 46, 0, health=2)
    run.asteroids = [Asteroid(1, 500, 500, 46, 0, health=0), live]
    result = guidance(campaign, run)
    assert result.key == "approach" and result.target_id == 2
    assert result.progress == pytest.approx(1 / 3)
    assert mining_target(campaign, run) is None


def test_depleted_field_collects_remaining_ore_before_returning():
    campaign, run = flight()
    run.x, run.y = 500, 500
    run.asteroids = []
    run.pickups = [Pickup(1, 510, 500, 0)]
    assert guidance(campaign, run).key == "collect"
    run.pickups = []
    assert guidance(campaign, run).key == "return_depleted"
    run.x, run.y = STATION_X, STATION_Y
    assert guidance(campaign, run).key == "dock"


def test_edge_ore_points_to_reachable_boundary_and_remote_ore_is_ignored():
    campaign, run = flight()
    run.x, run.y = 200, 500
    run.asteroids = []
    run.pickups = [Pickup(1, WORLD_LEFT - 55, 500, 0)]
    result = guidance(campaign, run)
    assert result.key == "collect" and result.target == (WORLD_LEFT, 500)
    run.x, run.y = result.target
    run.step(0.001, InputState())
    assert run.cargo == [0] and not run.pickups  # Proposed edge target works in the real model.
    run.pickups = [Pickup(1, WORLD_LEFT - 55.001, 500, 0)]
    assert guidance(campaign, run).key == "return_depleted"
    # A diagonal corner uses circular collection distance, not a square margin.
    run.pickups = [Pickup(2, WORLD_LEFT - 40, WORLD_TOP - 40, 0)]
    assert guidance(campaign, run).key == "return_depleted"


def test_zero_distance_is_finite_and_nan_pickup_is_not_a_target():
    campaign, run = flight()
    run.x, run.y = 350, 630
    run.pickups = [Pickup(1, float("nan"), 630, 0)]
    result = guidance(campaign, run)
    assert result.key == "mine" and result.distance == 0
    assert math.isfinite(result.distance)


def test_guidance_is_deterministic_read_only_and_immutable():
    campaign, run = flight()
    run.x, run.y = 350, 630
    before_run = deepcopy(run)
    before_campaign = deepcopy(campaign)
    first = guidance(campaign, run)
    for _ in range(10):
        assert guidance(campaign, run) == first
        mining_target(campaign, run)
    assert run == before_run and campaign == before_campaign
    assert campaign._active is run
    with pytest.raises(FrozenInstanceError):
        first.key = "changed"
