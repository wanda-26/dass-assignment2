"""
Registration Module
Registers new crew members, storing name and role.
"""

# In-memory store: {member_id: {"id": int, "name": str, "role": str}}
_registry: dict = {}
_id_counter: list = [1]


def _next_id() -> int:
    mid = _id_counter[0]
    _id_counter[0] += 1
    return mid


def register_member(name: str, role: str) -> dict:
    """Register a new crew member with name and role. Returns the created record."""
    name = name.strip()
    role = role.strip().lower()
    if not name:
        raise ValueError("Name cannot be empty.")
    if not role:
        raise ValueError("Role cannot be empty.")
    mid = _next_id()
    record = {"id": mid, "name": name, "role": role}
    _registry[mid] = record
    return dict(record)


def get_member(member_id: int) -> dict:
    """Retrieve a member by ID. Raises KeyError if not found."""
    if member_id not in _registry:
        raise KeyError(f"No member with ID {member_id}.")
    return dict(_registry[member_id])


def get_all_members() -> list:
    """Return a list of all registered members."""
    return [dict(m) for m in _registry.values()]


def member_exists(member_id: int) -> bool:
    """Check if a member ID exists in the registry."""
    return member_id in _registry


def remove_member(member_id: int) -> None:
    """Remove a member from the registry."""
    if member_id not in _registry:
        raise KeyError(f"No member with ID {member_id}.")
    del _registry[member_id]


def clear_registry() -> None:
    """Reset all data — used in tests."""
    _registry.clear()
    _id_counter[0] = 1