"""
Mission Planning Module
Creates missions and assigns crew members to them.
Validates that required roles exist in the crew before a mission can start.
Business rules:
  - Mission cannot start if no crew member with the required role exists.
  - Each mission type has a set of required roles.
Depends on: crew_management, registration.
"""

from modules import crew_management, registration

# Mission type → list of required roles
MISSION_REQUIREMENTS = {
    "delivery": ["driver"],
    "rescue":   ["driver", "medic"],
    "recon":    ["scout"],
    "repair":   ["mechanic"],
    "heist":    ["driver", "strategist"],
}

# {mission_id: {"id": int, "type": str, "description": str,
#               "required_roles": list, "assigned_crew": list, "status": str}}
_missions: dict = {}
_mission_id_counter: list = [1]


def _next_mission_id() -> int:
    mid = _mission_id_counter[0]
    _mission_id_counter[0] += 1
    return mid


def create_mission(mission_type: str, description: str) -> dict:
    """
    Create a new mission of the given type.
    Raises ValueError if mission type is not recognised.
    """
    mission_type = mission_type.strip().lower()
    if mission_type not in MISSION_REQUIREMENTS:
        raise ValueError(
            f"Unknown mission type '{mission_type}'. "
            f"Valid types: {', '.join(sorted(MISSION_REQUIREMENTS))}."
        )
    mid = _next_mission_id()
    record = {
        "id": mid,
        "type": mission_type,
        "description": description.strip(),
        "required_roles": list(MISSION_REQUIREMENTS[mission_type]),
        "assigned_crew": [],
        "status": "planned",
    }
    _missions[mid] = record
    return dict(record)


def assign_crew(mission_id: int, member_ids: list) -> dict:
    """
    Assign crew members to a mission.
    Validates that the assigned crew collectively covers all required roles.
    Raises ValueError if roles are not covered.
    """
    if mission_id not in _missions:
        raise KeyError(f"No mission with ID {mission_id}.")

    mission = _missions[mission_id]

    if mission["status"] != "planned":
        raise ValueError(f"Can only assign crew to a planned mission (status: '{mission['status']}').")

    # Get each member's role
    provided_roles = []
    for member_id in member_ids:
        if not registration.member_exists(member_id):
            raise ValueError(f"Member ID {member_id} is not registered.")
        member = registration.get_member(member_id)
        if member["role"] == "unassigned":
            raise ValueError(f"Member ID {member_id} has no role assigned yet.")
        provided_roles.append(member["role"])

    # Check all required roles are covered
    required = list(mission["required_roles"])
    remaining = list(provided_roles)
    unmet = []
    for req_role in required:
        if req_role in remaining:
            remaining.remove(req_role)
        else:
            unmet.append(req_role)

    if unmet:
        raise ValueError(
            f"Mission requires roles not covered: {', '.join(unmet)}. "
            f"Provided roles: {', '.join(provided_roles)}."
        )

    mission["assigned_crew"] = list(member_ids)
    return dict(mission)


def start_mission(mission_id: int) -> dict:
    """
    Start a mission.
    Validates that required roles exist in the crew before starting.
    """
    if mission_id not in _missions:
        raise KeyError(f"No mission with ID {mission_id}.")

    mission = _missions[mission_id]

    if mission["status"] != "planned":
        raise ValueError(f"Mission must be 'planned' to start (status: '{mission['status']}').")

    if not mission["assigned_crew"]:
        raise ValueError("Cannot start a mission with no crew assigned.")

    # Check all required roles exist somewhere in the crew
    for role in mission["required_roles"]:
        if not crew_management.role_exists_in_crew(role):
            raise ValueError(
                f"Cannot start mission — no crew member with role '{role}' exists."
            )

    mission["status"] = "ongoing"
    return dict(mission)


def complete_mission(mission_id: int, success: bool = True) -> dict:
    """Complete or fail a mission."""
    if mission_id not in _missions:
        raise KeyError(f"No mission with ID {mission_id}.")

    mission = _missions[mission_id]

    if mission["status"] != "ongoing":
        raise ValueError(f"Mission must be 'ongoing' to complete (status: '{mission['status']}').")

    mission["status"] = "completed" if success else "failed"
    return dict(mission)


def get_mission(mission_id: int) -> dict:
    """Get a mission by ID."""
    if mission_id not in _missions:
        raise KeyError(f"No mission with ID {mission_id}.")
    return dict(_missions[mission_id])


def get_all_missions() -> list:
    """Return all missions."""
    return [dict(m) for m in _missions.values()]


def clear_missions() -> None:
    """Reset all mission data — used in tests."""
    _missions.clear()
    _mission_id_counter[0] = 1