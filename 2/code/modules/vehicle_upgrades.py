"""
Vehicle Upgrades Module (Bonus Module 1)
Upgrades car speed or repairs car condition using spare parts from inventory.
Business rules:
  - A car must exist in inventory before it can be upgraded.
  - Upgrades consume spare parts from inventory.
  - Speed cannot exceed 10.
  - A wrecked car cannot be repaired — it must be replaced.
Depends on: inventory.
"""

from modules import inventory

# Each upgrade type and the spare part it consumes
UPGRADE_REQUIREMENTS = {
    "engine":  {"part": "engine part",  "speed_boost": 2},
    "tyres":   {"part": "tyre",         "speed_boost": 1},
    "nitrous": {"part": "nitrous kit",  "speed_boost": 3},
}


def upgrade_car(car_id: int, upgrade_type: str) -> dict:
    """
    Upgrade a car's speed using spare parts.
    Consumes the required spare part from inventory.
    Raises ValueError if parts are unavailable or speed is already at max.
    """
    upgrade_type = upgrade_type.strip().lower()
    if upgrade_type not in UPGRADE_REQUIREMENTS:
        raise ValueError(
            f"Unknown upgrade type '{upgrade_type}'. "
            f"Valid types: {', '.join(sorted(UPGRADE_REQUIREMENTS))}."
        )

    car = inventory.get_car(car_id)

    if car["condition"] == "wrecked":
        raise ValueError(f"Car '{car['name']}' is wrecked and cannot be upgraded.")

    if car["speed"] >= 10:
        raise ValueError(f"Car '{car['name']}' already has maximum speed of 10.")

    upgrade = UPGRADE_REQUIREMENTS[upgrade_type]
    part_needed = upgrade["part"]
    boost = upgrade["speed_boost"]

    # Check spare parts availability
    parts = inventory.get_spare_parts()
    if parts.get(part_needed, 0) < 1:
        raise ValueError(
            f"Cannot upgrade — no '{part_needed}' available in inventory."
        )

    # Consume the part
    inventory.use_spare_part(part_needed, 1)

    # Apply speed boost (cap at 10)
    new_speed = min(10, car["speed"] + boost)
    inventory._cars[car_id]["speed"] = new_speed

    return inventory.get_car(car_id)


def repair_car(car_id: int) -> dict:
    """
    Repair a damaged car back to 'good' condition.
    Consumes one 'repair kit' from spare parts.
    A wrecked car cannot be repaired.
    """
    car = inventory.get_car(car_id)

    if car["condition"] == "wrecked":
        raise ValueError(f"Car '{car['name']}' is wrecked and cannot be repaired — replace it.")

    if car["condition"] in ("excellent", "good"):
        raise ValueError(f"Car '{car['name']}' is already in '{car['condition']}' condition.")

    # Check spare parts
    parts = inventory.get_spare_parts()
    if parts.get("repair kit", 0) < 1:
        raise ValueError("Cannot repair — no 'repair kit' available in inventory.")

    # Consume the part
    inventory.use_spare_part("repair kit", 1)

    # Restore condition
    inventory.update_car_condition(car_id, "good")

    return inventory.get_car(car_id)


def get_available_upgrades(car_id: int) -> list:
    """
    Return a list of upgrades that can currently be applied to a car
    based on available spare parts.
    """
    car = inventory.get_car(car_id)
    if car["condition"] == "wrecked":
        return []

    parts = inventory.get_spare_parts()
    available = []
    for upgrade_type, details in UPGRADE_REQUIREMENTS.items():
        if parts.get(details["part"], 0) >= 1 and car["speed"] < 10:
            available.append({
                "upgrade_type": upgrade_type,
                "part_required": details["part"],
                "speed_boost": details["speed_boost"],
            })
    return available