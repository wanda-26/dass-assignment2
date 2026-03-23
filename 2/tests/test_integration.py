"""
Integration Tests — StreetRace Manager
Tests cross-module interactions based on the call graph.
Run with: pytest tests/test_integration.py -v
"""

import pytest
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

code_dir = os.path.join(project_root, 'code')
sys.path.insert(0, code_dir)

from modules import (
    registration,
    crew_management,
    inventory,
    race_management,
    results,
    mission_planning,
    vehicle_upgrades,
    leaderboard,
)


# ── Reset all module state before every test ──────────────────────────────────

@pytest.fixture(autouse=True)
def reset_all():
    registration.clear_registry()
    crew_management.clear_crew()
    inventory.clear_inventory()
    race_management.clear_races()
    results.clear_results()
    mission_planning.clear_missions()
    yield


# =============================================================================
# TC-01
# Scenario : Register a member then assign a role via crew management.
# Modules  : Registration → Crew Management
# Why      : Verifies that crew management correctly reads from the registration
#            registry when assigning a role.
# =============================================================================

def test_tc01_register_then_assign_role():
    m = registration.register_member("Dom Toretto")
    assert m["role"] == "unassigned"
    assert m["skill_level"] is None

    updated = crew_management.assign_role_and_skill(m["id"], "driver", 9)
    assert updated["role"] == "driver"
    assert updated["skill_level"] == 9


# =============================================================================
# TC-02
# Scenario : Assign a role to a member who is NOT registered.
# Modules  : Registration → Crew Management
# Why      : Verifies the business rule that a member must be registered before
#            a role can be assigned.
# =============================================================================

def test_tc02_assign_role_without_registration():
    with pytest.raises(ValueError, match="not registered"):
        crew_management.assign_role_and_skill(999, "driver", 8)


# =============================================================================
# TC-03
# Scenario : Register a driver, add a car, create a race, enter the driver.
# Modules  : Registration, Crew Management, Inventory, Race Management
# Why      : Verifies the full entry flow — the most common admin workflow.
# =============================================================================

def test_tc03_register_driver_and_enter_race():
    m = registration.register_member("Brian OConner")
    crew_management.assign_role_and_skill(m["id"], "driver", 8)
    car = inventory.add_car("Supra", 8)
    race = race_management.create_race("Midnight Mile", "LA", 10000)

    entry = race_management.enter_race(race["id"], m["id"], car["id"])
    assert entry["driver_id"] == m["id"]
    assert entry["car_id"] == car["id"]


# =============================================================================
# TC-04
# Scenario : Attempt to enter a race with an unregistered driver.
# Modules  : Registration, Race Management
# Why      : Verifies that race management blocks unregistered members.
# =============================================================================

def test_tc04_unregistered_driver_cannot_enter_race():
    car = inventory.add_car("Charger", 9)
    race = race_management.create_race("Dawn Drag", "Miami", 5000)

    with pytest.raises(ValueError, match="not registered"):
        race_management.enter_race(race["id"], 999, car["id"])


# =============================================================================
# TC-05
# Scenario : Attempt to enter a race with a member who is not a driver.
# Modules  : Registration, Crew Management, Race Management
# Why      : Verifies that only members with the driver role can enter a race.
# =============================================================================

def test_tc05_non_driver_cannot_enter_race():
    m = registration.register_member("Tej Parker")
    crew_management.assign_role_and_skill(m["id"], "mechanic", 9)
    car = inventory.add_car("Van", 5)
    race = race_management.create_race("Street Race", "NYC", 3000)

    with pytest.raises(ValueError, match="only drivers"):
        race_management.enter_race(race["id"], m["id"], car["id"])


# =============================================================================
# TC-06
# Scenario : Complete a race and verify prize money is added to cash balance.
# Modules  : Race Management, Results, Inventory
# Why      : Verifies that results.record_result correctly calls
#            inventory.add_cash after a race.
# =============================================================================

def test_tc06_race_result_updates_cash_balance():
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)
    m2 = registration.register_member("Brian")
    crew_management.assign_role_and_skill(m2["id"], "driver", 8)

    car1 = inventory.add_car("Charger", 9)
    car2 = inventory.add_car("Supra", 8)

    race = race_management.create_race("Final Race", "Nevada", 10000)
    race_management.enter_race(race["id"], m1["id"], car1["id"])
    race_management.enter_race(race["id"], m2["id"], car2["id"])
    race_management.update_race_status(race["id"], "ongoing")

    cash_before = inventory.get_cash()
    results.record_result(race["id"], [m1["id"], m2["id"]])
    cash_after = inventory.get_cash()

    assert cash_after > cash_before


# =============================================================================
# TC-07
# Scenario : Complete a race and verify driver rankings are updated.
# Modules  : Race Management, Results
# Why      : Verifies that record_result updates wins and races for each driver.
# =============================================================================

def test_tc07_race_result_updates_rankings():
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)
    m2 = registration.register_member("Brian")
    crew_management.assign_role_and_skill(m2["id"], "driver", 8)

    car1 = inventory.add_car("Charger", 9)
    car2 = inventory.add_car("Supra", 8)

    race = race_management.create_race("Night Race", "LA", 10000)
    race_management.enter_race(race["id"], m1["id"], car1["id"])
    race_management.enter_race(race["id"], m2["id"], car2["id"])
    race_management.update_race_status(race["id"], "ongoing")

    results.record_result(race["id"], [m1["id"], m2["id"]])

    stats_winner = results.get_driver_stats(m1["id"])
    stats_second = results.get_driver_stats(m2["id"])

    assert stats_winner["wins"] == 1
    assert stats_winner["races"] == 1
    assert stats_second["wins"] == 0
    assert stats_second["races"] == 1


# =============================================================================
# TC-08
# Scenario : Record a result for a race that is not ongoing.
# Modules  : Race Management, Results
# Why      : Verifies that results cannot be recorded for a race that has not
#            been started.
# =============================================================================

def test_tc08_cannot_record_result_for_planned_race():
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)
    m2 = registration.register_member("Brian")
    crew_management.assign_role_and_skill(m2["id"], "driver", 8)

    car1 = inventory.add_car("Charger", 9)
    car2 = inventory.add_car("Supra", 8)

    race = race_management.create_race("Unstarted Race", "LA", 5000)
    race_management.enter_race(race["id"], m1["id"], car1["id"])
    race_management.enter_race(race["id"], m2["id"], car2["id"])
    # Race stays in planned status — not set to ongoing

    with pytest.raises(ValueError, match="ongoing"):
        results.record_result(race["id"], [m1["id"], m2["id"]])


# =============================================================================
# TC-09
# Scenario : Create a mission and assign crew with correct roles.
# Modules  : Registration, Crew Management, Mission Planning
# Why      : Verifies that mission planning correctly validates crew roles
#            against the mission requirements.
# =============================================================================

def test_tc09_assign_correct_crew_to_mission():
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)
    m2 = registration.register_member("Ramsey")
    crew_management.assign_role_and_skill(m2["id"], "medic", 7)

    mission = mission_planning.create_mission("rescue", "Extract VIP")
    result = mission_planning.assign_crew(mission["id"], [m1["id"], m2["id"]])

    assert result["status"] == "planned"
    assert m1["id"] in result["assigned_crew"]
    assert m2["id"] in result["assigned_crew"]


# =============================================================================
# TC-10
# Scenario : Assign crew to a mission where roles do not cover requirements.
# Modules  : Registration, Crew Management, Mission Planning
# Why      : Verifies that a mission blocks crew assignment if required roles
#            are not covered by the assigned members.
# =============================================================================

def test_tc10_mission_rejects_wrong_crew_roles():
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)

    mission = mission_planning.create_mission("rescue", "Extract VIP")

    with pytest.raises(ValueError, match="medic"):
        mission_planning.assign_crew(mission["id"], [m1["id"]])


# =============================================================================
# TC-11
# Scenario : Start a mission when the required role does not exist in the crew.
# Modules  : Crew Management, Mission Planning
# Why      : Verifies the business rule that missions cannot start if required
#            roles are unavailable in the crew.
# =============================================================================

def test_tc11_mission_cannot_start_without_required_role():
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)

    # Create a recon mission — requires scout
    mission = mission_planning.create_mission("recon", "Scout the route")

    # Try to assign a driver to a recon mission
    with pytest.raises(ValueError, match="scout"):
        mission_planning.assign_crew(mission["id"], [m1["id"]])


# =============================================================================
# TC-12
# Scenario : Race result marks a car as damaged, then repair mission checks
#            for damaged cars before starting.
# Modules  : Race Management, Results, Inventory, Mission Planning
# Why      : Verifies the business rule that a repair mission requires at least
#            one damaged car to exist before it can proceed.
# =============================================================================

def test_tc12_damaged_car_enables_repair_mission():
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)
    m2 = registration.register_member("Brian")
    crew_management.assign_role_and_skill(m2["id"], "driver", 8)
    mech = registration.register_member("Tej")
    crew_management.assign_role_and_skill(mech["id"], "mechanic", 9)

    car1 = inventory.add_car("Charger", 9)
    car2 = inventory.add_car("Supra", 7)

    race = race_management.create_race("Street Race", "LA", 10000)
    race_management.enter_race(race["id"], m1["id"], car1["id"])
    race_management.enter_race(race["id"], m2["id"], car2["id"])
    race_management.update_race_status(race["id"], "ongoing")

    # Supra gets damaged during the race
    results.record_result(race["id"], [m1["id"], m2["id"]], damaged_car_ids=[car2["id"]])

    # Verify car is marked as damaged in inventory
    assert inventory.get_car(car2["id"])["condition"] == "damaged"

    # Repair mission should now be startable
    mission = mission_planning.create_mission("repair", "Fix the Supra")
    mission_planning.assign_crew(mission["id"], [mech["id"]])
    started = mission_planning.start_mission(mission["id"])
    assert started["status"] == "ongoing"


# =============================================================================
# TC-13
# Scenario : Attempt to start a repair mission when no cars are damaged.
# Modules  : Inventory, Mission Planning
# Why      : Verifies that a repair mission is blocked when there are no
#            damaged cars in inventory.
# =============================================================================

def test_tc13_repair_mission_blocked_without_damaged_car():
    mech = registration.register_member("Tej")
    crew_management.assign_role_and_skill(mech["id"], "mechanic", 9)
    inventory.add_car("Charger", 9)  # car is in excellent condition

    mission = mission_planning.create_mission("repair", "Nothing to fix")
    mission_planning.assign_crew(mission["id"], [mech["id"]])

    with pytest.raises(ValueError, match="no damaged cars"):
        mission_planning.start_mission(mission["id"])


# =============================================================================
# TC-14
# Scenario : Upgrade a car and verify spare parts are consumed from inventory.
# Modules  : Inventory, Vehicle Upgrades
# Why      : Verifies that vehicle_upgrades correctly calls inventory functions
#            to consume parts and update car speed.
# =============================================================================

def test_tc14_upgrade_car_consumes_spare_parts():
    car = inventory.add_car("Skyline", 7)
    inventory.add_spare_part("engine part", 2)

    upgraded = vehicle_upgrades.upgrade_car(car["id"], "engine")

    assert upgraded["speed"] == 9
    assert inventory.get_spare_parts()["engine part"] == 1


# =============================================================================
# TC-15
# Scenario : Attempt to upgrade a car with no spare parts available.
# Modules  : Inventory, Vehicle Upgrades
# Why      : Verifies that upgrades are blocked when required parts are missing.
# =============================================================================

def test_tc15_upgrade_blocked_without_spare_parts():
    car = inventory.add_car("Skyline", 7)
    # No spare parts added

    with pytest.raises(ValueError, match="no 'engine part'"):
        vehicle_upgrades.upgrade_car(car["id"], "engine")


# =============================================================================
# TC-16
# Scenario : Complete a race and verify leaderboard reflects updated results.
# Modules  : Race Management, Results, Registration, Leaderboard
# Why      : Verifies that leaderboard correctly pulls data from results and
#            registration after a race is completed.
# =============================================================================

def test_tc16_leaderboard_reflects_race_results():
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)
    m2 = registration.register_member("Brian")
    crew_management.assign_role_and_skill(m2["id"], "driver", 8)

    car1 = inventory.add_car("Charger", 9)
    car2 = inventory.add_car("Supra", 8)

    race = race_management.create_race("Grand Prix", "Rio", 10000)
    race_management.enter_race(race["id"], m1["id"], car1["id"])
    race_management.enter_race(race["id"], m2["id"], car2["id"])
    race_management.update_race_status(race["id"], "ongoing")
    results.record_result(race["id"], [m1["id"], m2["id"]])

    board = leaderboard.get_leaderboard()

    assert board[0]["name"] == "Dom"
    assert board[0]["wins"] == 1
    assert board[1]["name"] == "Brian"
    assert board[1]["wins"] == 0


# =============================================================================
# TC-17
# Scenario : Update the role of a member who already has one assigned.
# Modules  : Registration, Crew Management
# Why      : Verifies that update_role correctly calls back into registration
#            to update the shared registry.
# =============================================================================

def test_tc17_update_role():
    m = registration.register_member("Letty")
    crew_management.assign_role_and_skill(m["id"], "driver", 8)

    updated = crew_management.update_role(m["id"], "strategist")
    assert updated["role"] == "strategist"
    assert registration.get_member(m["id"])["role"] == "strategist"


# =============================================================================
# TC-18
# Scenario : Update the skill level of a member who already has a role.
# Modules  : Registration, Crew Management
# Why      : Verifies that update_skill correctly calls back into registration
#            to update the shared registry.
# =============================================================================

def test_tc18_update_skill():
    m = registration.register_member("Hobbs")
    crew_management.assign_role_and_skill(m["id"], "driver", 5)

    updated = crew_management.update_skill(m["id"], 9)
    assert updated["skill_level"] == 9
    assert registration.get_member(m["id"])["skill_level"] == 9


# =============================================================================
# TC-19
# Scenario : Filter crew members by role.
# Modules  : Registration, Crew Management
# Why      : Verifies that get_members_by_role correctly reads from the
#            registration registry to filter by role.
# =============================================================================

def test_tc19_get_members_by_role():
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)
    m2 = registration.register_member("Tej")
    crew_management.assign_role_and_skill(m2["id"], "mechanic", 8)
    m3 = registration.register_member("Brian")
    crew_management.assign_role_and_skill(m3["id"], "driver", 7)

    drivers = crew_management.get_members_by_role("driver")
    assert len(drivers) == 2
    mechanics = crew_management.get_members_by_role("mechanic")
    assert len(mechanics) == 1


# =============================================================================
# TC-20
# Scenario : Repair a damaged car using a repair kit from inventory.
# Modules  : Inventory, Vehicle Upgrades
# Why      : Verifies that repair_car correctly calls inventory functions to
#            consume a repair kit and update the car condition.
# =============================================================================

def test_tc20_repair_car_consumes_repair_kit():
    car = inventory.add_car("Supra", 8)
    inventory.update_car_condition(car["id"], "damaged")
    inventory.add_spare_part("repair kit", 1)

    repaired = vehicle_upgrades.repair_car(car["id"])

    assert repaired["condition"] == "good"
    assert inventory.get_spare_parts()["repair kit"] == 0


# =============================================================================
# TC-21
# Scenario : Check available upgrades for a car based on spare parts.
# Modules  : Inventory, Vehicle Upgrades
# Why      : Verifies that get_available_upgrades correctly reads car data
#            and spare parts from inventory.
# =============================================================================

def test_tc21_get_available_upgrades():
    car = inventory.add_car("Skyline", 6)
    inventory.add_spare_part("engine part", 1)
    inventory.add_spare_part("tyre", 2)

    upgrades = vehicle_upgrades.get_available_upgrades(car["id"])
    upgrade_types = [u["upgrade_type"] for u in upgrades]

    assert "engine" in upgrade_types
    assert "tyres" in upgrade_types
    assert "nitrous" not in upgrade_types  # no nitrous kit in stock


# =============================================================================
# TC-22
# Scenario : Get all races — internally calls get_race for each race.
# Modules  : Race Management (internal)
# Why      : Verifies that get_all_races correctly calls get_race internally
#            and returns complete race data.
# =============================================================================

def test_tc22_get_all_races_calls_get_race():
    race_management.create_race("Race 1", "LA", 5000)
    race_management.create_race("Race 2", "Miami", 8000)

    all_races = race_management.get_all_races()

    assert len(all_races) == 2
    assert all_races[0]["name"] == "Race 1"
    assert all_races[1]["name"] == "Race 2"


# =============================================================================
# TC-23
# Scenario : Get the top driver from the leaderboard.
# Modules  : Results, Registration, Leaderboard
# Why      : Verifies that get_top_driver correctly calls get_leaderboard
#            internally and returns the driver with the most wins.
# =============================================================================

def test_tc23_get_top_driver():
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)
    m2 = registration.register_member("Brian")
    crew_management.assign_role_and_skill(m2["id"], "driver", 8)

    car1 = inventory.add_car("Charger", 9)
    car2 = inventory.add_car("Supra", 8)

    race = race_management.create_race("Race", "LA", 10000)
    race_management.enter_race(race["id"], m1["id"], car1["id"])
    race_management.enter_race(race["id"], m2["id"], car2["id"])
    race_management.update_race_status(race["id"], "ongoing")
    results.record_result(race["id"], [m1["id"], m2["id"]])

    top = leaderboard.get_top_driver()
    assert top["name"] == "Dom"
    assert top["wins"] == 1


# =============================================================================
# TC-24
# Scenario : Get a specific driver's position on the leaderboard.
# Modules  : Results, Registration, Leaderboard
# Why      : Verifies that get_driver_position correctly calls get_leaderboard
#            internally and returns the right entry for the given driver.
# =============================================================================

def test_tc24_get_driver_position():
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)
    m2 = registration.register_member("Brian")
    crew_management.assign_role_and_skill(m2["id"], "driver", 8)

    car1 = inventory.add_car("Charger", 9)
    car2 = inventory.add_car("Supra", 8)

    race = race_management.create_race("Race", "LA", 10000)
    race_management.enter_race(race["id"], m1["id"], car1["id"])
    race_management.enter_race(race["id"], m2["id"], car2["id"])
    race_management.update_race_status(race["id"], "ongoing")
    results.record_result(race["id"], [m1["id"], m2["id"]])

    entry = leaderboard.get_driver_position(m2["id"])
    assert entry["name"] == "Brian"
    assert entry["position"] == 2


# =============================================================================
# TC-25
# Scenario : Print the leaderboard — internally calls get_leaderboard.
# Modules  : Results, Registration, Leaderboard
# Why      : Verifies that print_leaderboard correctly calls get_leaderboard
#            internally and produces output without errors.
# =============================================================================

def test_tc25_print_leaderboard(capsys):
    m1 = registration.register_member("Dom")
    crew_management.assign_role_and_skill(m1["id"], "driver", 9)
    m2 = registration.register_member("Brian")
    crew_management.assign_role_and_skill(m2["id"], "driver", 8)

    car1 = inventory.add_car("Charger", 9)
    car2 = inventory.add_car("Supra", 8)

    race = race_management.create_race("Race", "LA", 10000)
    race_management.enter_race(race["id"], m1["id"], car1["id"])
    race_management.enter_race(race["id"], m2["id"], car2["id"])
    race_management.update_race_status(race["id"], "ongoing")
    results.record_result(race["id"], [m1["id"], m2["id"]])

    leaderboard.print_leaderboard()
    captured = capsys.readouterr()

    assert "Dom" in captured.out
    assert "Brian" in captured.out