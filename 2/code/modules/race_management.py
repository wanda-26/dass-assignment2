"""
Race Management Module
Creates races and manages driver/car entries.
Business rules:
  - Driver must be registered.
  - Driver must have the 'driver' role.
  - Car must exist in inventory.
  - A driver or car can only be entered once per race.
Depends on: registration, crew_management, inventory.
"""

from modules import registration, crew_management, inventory

# {race_id: {"id": int, "name": str, "location": str, "prize_money": int,
#             "entries": [{"driver_id": int, "car_id": int}], "status": str}}
_races: dict = {}
_race_id_counter: list = [1]

RACE_STATUSES = {"planned", "ongoing", "completed", "cancelled"}


def _next_race_id() -> int:
    rid = _race_id_counter[0]
    _race_id_counter[0] += 1
    return rid


def create_race(name: str, location: str, prize_money: int) -> dict:
    """Create a new race."""
    name = name.strip()
    location = location.strip()
    if not name:
        raise ValueError("Race name cannot be empty.")
    if not location:
        raise ValueError("Race location cannot be empty.")
    if prize_money <= 0:
        raise ValueError("Prize money must be positive.")
    rid = _next_race_id()
    record = {
        "id": rid,
        "name": name,
        "location": location,
        "prize_money": prize_money,
        "entries": [],
        "status": "planned",
    }
    _races[rid] = record
    return dict(record)


def get_race(race_id: int) -> dict:
    """Get a race by ID."""
    if race_id not in _races:
        raise KeyError(f"No race with ID {race_id}.")
    r = dict(_races[race_id])
    r["entries"] = list(r["entries"])
    return r


def get_all_races() -> list:
    """Return all races."""
    return [get_race(rid) for rid in _races]


def enter_race(race_id: int, driver_id: int, car_id: int) -> dict:
    """
    Enter a driver and car into a race.
    Rules:
      - Race must be planned.
      - Driver must be registered.
      - Driver must have the 'driver' role.
      - Car must exist in inventory.
      - Same driver or car cannot be entered twice in the same race.
    """
    if race_id not in _races:
        raise KeyError(f"No race with ID {race_id}.")

    race = _races[race_id]

    if race["status"] != "planned":
        raise ValueError(f"Race is '{race['status']}' — can only enter a planned race.")

    # Validate driver is registered
    if not registration.member_exists(driver_id):
        raise ValueError(f"Member ID {driver_id} is not registered.")

    # Validate driver has driver role
    member = registration.get_member(driver_id)
    if member["role"] != "driver":
        raise ValueError(f"'{member['name']}' has role '{member['role']}' — only drivers can enter a race.")

    # Validate car exists
    inventory.get_car(car_id)  # raises KeyError if not found

    # Check for duplicates
    for entry in race["entries"]:
        if entry["driver_id"] == driver_id:
            raise ValueError(f"Driver ID {driver_id} is already entered in this race.")
        if entry["car_id"] == car_id:
            raise ValueError(f"Car ID {car_id} is already entered in this race.")

    entry = {"driver_id": driver_id, "car_id": car_id}
    race["entries"].append(entry)
    return entry


def update_race_status(race_id: int, status: str) -> dict:
    """Update the status of a race."""
    if race_id not in _races:
        raise KeyError(f"No race with ID {race_id}.")
    status = status.strip().lower()
    if status not in RACE_STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(RACE_STATUSES)}.")
    _races[race_id]["status"] = status
    return get_race(race_id)


def clear_races() -> None:
    """Reset all race data — used in tests."""
    _races.clear()
    _race_id_counter[0] = 1