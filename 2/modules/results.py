"""
Results Module
Records race outcomes, updates driver rankings and adds prize money to inventory.
Prize split: 1st = 60%, 2nd = 30%, 3rd = 10%.
Also records which cars were damaged during the race.
Depends on: race_management, inventory.
"""

from modules import race_management, inventory

# Rankings: {driver_id: {"wins": int, "races": int, "earnings": int}}
_rankings: dict = {}

# Results: {race_id: {"winner_id": int, "placements": list, "damaged_cars": list}}
_results: dict = {}


def _ensure_ranking(driver_id: int) -> None:
    """Create a ranking entry for a driver if one doesn't exist."""
    if driver_id not in _rankings:
        _rankings[driver_id] = {"wins": 0, "races": 0, "earnings": 0}


def record_result(race_id: int, placements: list, damaged_car_ids: list = None) -> dict:
    """
    Record the finishing order of a race.
    - placements: list of driver_ids in finishing order (1st place first).
    - damaged_car_ids: list of car IDs damaged during the race (optional).
    - Updates driver rankings and adds prize money to inventory cash.
    - Marks damaged cars in inventory.
    - Marks race as completed.
    """
    if damaged_car_ids is None:
        damaged_car_ids = []

    race = race_management.get_race(race_id)

    if race["status"] != "ongoing":
        raise ValueError(f"Race must be 'ongoing' to record results (status: '{race['status']}').")

    if len(placements) == 0:
        raise ValueError("Placements list cannot be empty.")

    # Validate all placed drivers were entered in the race
    entered_driver_ids = [e["driver_id"] for e in race["entries"]]
    for driver_id in placements:
        if driver_id not in entered_driver_ids:
            raise ValueError(f"Driver ID {driver_id} was not entered in this race.")

    # Validate damaged cars were in the race
    entered_car_ids = [e["car_id"] for e in race["entries"]]
    for car_id in damaged_car_ids:
        if car_id not in entered_car_ids:
            raise ValueError(f"Car ID {car_id} was not entered in this race.")

    # Prize money split
    prize = race["prize_money"]
    prize_splits = {0: 0.60, 1: 0.30, 2: 0.10}

    for i, driver_id in enumerate(placements):
        _ensure_ranking(driver_id)
        _rankings[driver_id]["races"] += 1
        if i == 0:
            _rankings[driver_id]["wins"] += 1
        if i in prize_splits:
            earned = int(prize * prize_splits[i])
            _rankings[driver_id]["earnings"] += earned
            inventory.add_cash(earned)

    # Mark damaged cars in inventory
    for car_id in damaged_car_ids:
        inventory.update_car_condition(car_id, "damaged")

    # Store result
    result_record = {
        "race_id": race_id,
        "placements": placements,
        "winner_id": placements[0],
        "damaged_cars": damaged_car_ids,
    }
    _results[race_id] = result_record

    # Mark race as completed
    race_management.update_race_status(race_id, "completed")

    return dict(result_record)


def get_result(race_id: int) -> dict:
    """Get the recorded result for a race."""
    if race_id not in _results:
        raise KeyError(f"No result recorded for race ID {race_id}.")
    return dict(_results[race_id])


def get_rankings() -> list:
    """Return all drivers sorted by wins then earnings."""
    return sorted(
        [{"driver_id": did, **stats} for did, stats in _rankings.items()],
        key=lambda x: (x["wins"], x["earnings"]),
        reverse=True,
    )


def get_driver_stats(driver_id: int) -> dict:
    """Get stats for a specific driver."""
    if driver_id not in _rankings:
        return {"driver_id": driver_id, "wins": 0, "races": 0, "earnings": 0}
    return {"driver_id": driver_id, **_rankings[driver_id]}


def clear_results() -> None:
    """Reset all results data — used in tests."""
    _results.clear()
    _rankings.clear()