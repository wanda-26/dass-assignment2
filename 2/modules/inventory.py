"""
Inventory Module
Tracks cars, spare parts, tools and the cash balance.
No dependencies on other modules.
"""

# Cars: {car_id: {"id": int, "name": str, "speed": int, "condition": str}}
_cars: dict = {}
_car_id_counter: list = [1]

# Spare parts: {part_name: quantity}
_spare_parts: dict = {}

# Tools: {tool_name: quantity}
_tools: dict = {}

# Cash balance
_cash: list = [10_000]  # crew starts with $10,000

CAR_CONDITIONS = {"excellent", "good", "damaged", "wrecked"}


# ── Car ID ─────────────────────────────────────────────────────────────────────

def _next_car_id() -> int:
    cid = _car_id_counter[0]
    _car_id_counter[0] += 1
    return cid


# ── Cars ───────────────────────────────────────────────────────────────────────

def add_car(name: str, speed: int) -> dict:
    """Add a new car to the inventory."""
    name = name.strip()
    if not name:
        raise ValueError("Car name cannot be empty.")
    if not (1 <= speed <= 10):
        raise ValueError("Speed must be between 1 and 10.")
    cid = _next_car_id()
    record = {
        "id": cid,
        "name": name,
        "speed": speed,
        "condition": "excellent",
    }
    _cars[cid] = record
    return dict(record)


def get_car(car_id: int) -> dict:
    """Get a car by ID."""
    if car_id not in _cars:
        raise KeyError(f"No car with ID {car_id}.")
    return dict(_cars[car_id])


def get_all_cars() -> list:
    """Return all cars in inventory."""
    return [dict(c) for c in _cars.values()]


def update_car_condition(car_id: int, condition: str) -> dict:
    """Update the condition of a car."""
    condition = condition.strip().lower()
    if condition not in CAR_CONDITIONS:
        raise ValueError(f"Condition must be one of: {', '.join(CAR_CONDITIONS)}.")
    if car_id not in _cars:
        raise KeyError(f"No car with ID {car_id}.")
    _cars[car_id]["condition"] = condition
    return dict(_cars[car_id])


def remove_car(car_id: int) -> None:
    """Remove a car from the inventory."""
    if car_id not in _cars:
        raise KeyError(f"No car with ID {car_id}.")
    del _cars[car_id]


# ── Spare Parts ────────────────────────────────────────────────────────────────

def add_spare_part(part_name: str, quantity: int) -> None:
    """Add spare parts to the inventory."""
    part_name = part_name.strip().lower()
    if not part_name:
        raise ValueError("Part name cannot be empty.")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")
    _spare_parts[part_name] = _spare_parts.get(part_name, 0) + quantity


def use_spare_part(part_name: str, quantity: int) -> None:
    """Use spare parts from the inventory."""
    part_name = part_name.strip().lower()
    if _spare_parts.get(part_name, 0) < quantity:
        raise ValueError(f"Not enough '{part_name}' in stock.")
    _spare_parts[part_name] -= quantity


def get_spare_parts() -> dict:
    """Return all spare parts and their quantities."""
    return dict(_spare_parts)


# ── Tools ──────────────────────────────────────────────────────────────────────

def add_tool(tool_name: str, quantity: int) -> None:
    """Add tools to the inventory."""
    tool_name = tool_name.strip().lower()
    if not tool_name:
        raise ValueError("Tool name cannot be empty.")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")
    _tools[tool_name] = _tools.get(tool_name, 0) + quantity


def get_tools() -> dict:
    """Return all tools and their quantities."""
    return dict(_tools)


# ── Cash ───────────────────────────────────────────────────────────────────────

def get_cash() -> int:
    """Return current cash balance."""
    return _cash[0]


def add_cash(amount: int) -> None:
    """Add cash to the balance."""
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    _cash[0] += amount


def deduct_cash(amount: int) -> None:
    """Deduct cash from the balance."""
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    if _cash[0] < amount:
        raise ValueError(f"Insufficient funds. Balance: ${_cash[0]}, required: ${amount}.")
    _cash[0] -= amount


# ── Reset ──────────────────────────────────────────────────────────────────────

def clear_inventory() -> None:
    """Reset all inventory data — used in tests."""
    _cars.clear()
    _spare_parts.clear()
    _tools.clear()
    _cash[0] = 10_000
    _car_id_counter[0] = 1