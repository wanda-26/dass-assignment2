"""
Leaderboard Module (Bonus Module 2)
Tracks and displays driver rankings across all races.
Pulls data from results and registration to build a ranked table.
Depends on: results, registration.
"""

from modules import results, registration


def get_leaderboard() -> list:
    """
    Return a ranked list of all drivers with their stats.
    Sorted by wins first, then earnings.
    Each entry includes the driver's name from registration.
    """
    rankings = results.get_rankings()
    leaderboard = []
    for i, entry in enumerate(rankings):
        driver_id = entry["driver_id"]
        try:
            member = registration.get_member(driver_id)
            name = member["name"]
        except KeyError:
            name = "Unknown"
        leaderboard.append({
            "position": i + 1,
            "driver_id": driver_id,
            "name": name,
            "wins": entry["wins"],
            "races": entry["races"],
            "earnings": entry["earnings"],
        })
    return leaderboard


def get_top_driver() -> dict:
    """Return the driver currently in 1st place."""
    board = get_leaderboard()
    if not board:
        raise ValueError("No race results recorded yet.")
    return board[0]


def get_driver_position(driver_id: int) -> dict:
    """Return the leaderboard entry for a specific driver."""
    board = get_leaderboard()
    for entry in board:
        if entry["driver_id"] == driver_id:
            return entry
    raise ValueError(f"Driver ID {driver_id} has no recorded results yet.")


def print_leaderboard() -> None:
    """Print a formatted leaderboard table."""
    board = get_leaderboard()
    if not board:
        print("No results recorded yet.")
        return
    print(f"\n{'POS':<5} {'NAME':<20} {'WINS':<6} {'RACES':<7} {'EARNINGS':<10}")
    print("-" * 50)
    for entry in board:
        print(
            f"{entry['position']:<5} "
            f"{entry['name']:<20} "
            f"{entry['wins']:<6} "
            f"{entry['races']:<7} "
            f"${entry['earnings']:<10}"
        )


def clear_leaderboard() -> None:
    """Reset leaderboard by clearing results — used in tests."""
    results.clear_results()