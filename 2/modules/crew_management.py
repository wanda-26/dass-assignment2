"""
Crew Management Module
Manages roles and skill levels for registered members.
All data is stored in the registration registry — this module only updates it.
A member must be registered before a role can be assigned.
Depends on: registration module.
"""

from modules import registration

VALID_ROLES = {"driver", "mechanic", "strategist", "scout", "medic"}


def assign_role_and_skill(member_id: int, role: str, skill_level: int) -> dict:
    """
    Assign a role and skill level to a registered member for the first time.
    Raises ValueError if member already has a role assigned.
    """
    if not registration.member_exists(member_id):
        raise ValueError(f"Member ID {member_id} is not registered. Register first.")

    member = registration.get_member(member_id)
    if member["role"] != "unassigned":
        raise ValueError(f"Member ID {member_id} already has role '{member['role']}'. Use update_role or update_skill instead.")

    role = role.strip().lower()
    if role not in VALID_ROLES:
        raise ValueError(f"'{role}' is not a valid role. Choose from: {', '.join(sorted(VALID_ROLES))}.")
    if not (1 <= skill_level <= 10):
        raise ValueError("Skill level must be between 1 and 10.")

    registration.update_role(member_id, role)
    registration.update_skill_level(member_id, skill_level)

    return registration.get_member(member_id)


def update_role(member_id: int, role: str) -> dict:
    """
    Change the role of a member who already has one assigned.
    Raises ValueError if member has no role assigned yet.
    """
    if not registration.member_exists(member_id):
        raise ValueError(f"Member ID {member_id} is not registered.")

    member = registration.get_member(member_id)
    if member["role"] == "unassigned":
        raise ValueError(f"Member ID {member_id} has no role yet. Use assign_role_and_skill first.")

    role = role.strip().lower()
    if role not in VALID_ROLES:
        raise ValueError(f"'{role}' is not a valid role. Choose from: {', '.join(sorted(VALID_ROLES))}.")

    registration.update_role(member_id, role)
    return registration.get_member(member_id)


def update_skill(member_id: int, skill_level: int) -> dict:
    """
    Update the skill level of a member who already has a role assigned.
    Raises ValueError if member has no role assigned yet.
    """
    if not registration.member_exists(member_id):
        raise ValueError(f"Member ID {member_id} is not registered.")

    member = registration.get_member(member_id)
    if member["role"] == "unassigned":
        raise ValueError(f"Member ID {member_id} has no role yet. Use assign_role_and_skill first.")

    if not (1 <= skill_level <= 10):
        raise ValueError("Skill level must be between 1 and 10.")

    registration.update_skill_level(member_id, skill_level)
    return registration.get_member(member_id)


def get_members_by_role(role: str) -> list:
    """Return all members with the given role."""
    role = role.strip().lower()
    return [m for m in registration.get_all_members() if m["role"] == role]


def role_exists_in_crew(role: str) -> bool:
    """Check if at least one crew member has the given role."""
    role = role.strip().lower()
    return any(m["role"] == role for m in registration.get_all_members())


def clear_crew() -> None:
    """Reset all crew-related fields — used in tests."""
    for member_id in registration._registry:
        registration._registry[member_id]["role"] = "unassigned"
        registration._registry[member_id]["skill_level"] = None