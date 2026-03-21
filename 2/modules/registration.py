"""
Registration Module
Registers new crew members.
All member data lives here — role, skill level and availability
are updated later by the Crew Management module.
"""

# In-memory store: {member_id: {"id": int, "name": str, "role": str, "skill_level": int|None, "available": bool}}
_registry: dict = {}
_id_counter: list = [1]


def _next_id() -> int:
    mid = _id_counter[0]
    _id_counter[0] += 1
    return mid


def register_member(name: str) -> dict:
    """Register a new crew member. Role and skill start as unassigned."""
    name = name.strip()
    if not name:
        raise ValueError("Name cannot be empty.")
    mid = _next_id()
    record = {
        "id": mid,
        "name": name,
        "role": "unassigned",
        "skill_level": None,
        "available": True,
    }
    _registry[mid] = record
    return dict(record)


def get_member(member_id: int) -> dict:
    """Retrieve a member by ID."""
    if member_id not in _registry:
        raise KeyError(f"No member with ID {member_id}.")
    return dict(_registry[member_id])


def get_all_members() -> list:
    """Return a list of all registered members."""
    return [dict(m) for m in _registry.values()]


def member_exists(member_id: int) -> bool:
    """Check if a member ID exists in the registry."""
    return member_id in _registry


def update_role(member_id: int, role: str) -> None:
    """Update a member's role — called by crew management."""
    if member_id not in _registry:
        raise KeyError(f"No member with ID {member_id}.")
    _registry[member_id]["role"] = role


def update_skill_level(member_id: int, skill_level: int) -> None:
    """Update a member's skill level — called by crew management."""
    if member_id not in _registry:
        raise KeyError(f"No member with ID {member_id}.")
    _registry[member_id]["skill_level"] = skill_level


def update_availability(member_id: int, available: bool) -> None:
    """Update a member's availability — called by crew management."""
    if member_id not in _registry:
        raise KeyError(f"No member with ID {member_id}.")
    _registry[member_id]["available"] = available


def remove_member(member_id: int) -> None:
    """Remove a member from the registry."""
    if member_id not in _registry:
        raise KeyError(f"No member with ID {member_id}.")
    del _registry[member_id]


def clear_registry() -> None:
    """Reset all data — used in tests."""
    _registry.clear()
    _id_counter[0] = 1