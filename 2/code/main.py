"""
StreetRace Manager — Command Line Interface
The admin uses this to manage the entire crew, races and missions.
Run with: python3 main.py
"""

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


def print_header(title: str) -> None:
    print(f"\n{'═' * 45}")
    print(f"  {title}")
    print(f"{'═' * 45}")


def print_ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def print_err(msg: str) -> None:
    print(f"  ✗ ERROR: {msg}")


def prompt(msg: str) -> str:
    return input(f"  {msg}: ").strip()


# ── Registration ───────────────────────────────────────────────────────────────

def menu_registration():
    print_header("REGISTRATION")
    print("  [1] Register new member")
    print("  [2] View all members")
    print("  [0] Back")
    choice = prompt("Choice")

    if choice == "1":
        name = prompt("Member name")
        try:
            m = registration.register_member(name)
            print_ok(f"Registered '{m['name']}' with ID {m['id']}")
        except ValueError as e:
            print_err(str(e))

    elif choice == "2":
        members = registration.get_all_members()
        if not members:
            print("  No members registered yet.")
        else:
            print(f"\n  {'ID':<5} {'NAME':<20} {'ROLE':<15} {'SKILL':<6}")
            print("  " + "-" * 48)
            for m in members:
                print(f"  {m['id']:<5} {m['name']:<20} {m['role']:<15} {str(m['skill_level']):<6}")


# ── Crew Management ────────────────────────────────────────────────────────────

def menu_crew():
    print_header("CREW MANAGEMENT")
    print("  [1] Assign role and skill to member")
    print("  [2] Update role")
    print("  [3] Update skill level")
    print("  [0] Back")
    choice = prompt("Choice")

    if choice == "1":
        try:
            mid = int(prompt("Member ID"))
            role = prompt("Role (driver/mechanic/strategist/scout/medic)")
            skill = int(prompt("Skill level (1-10)"))
            m = crew_management.assign_role_and_skill(mid, role, skill)
            print_ok(f"Assigned role '{m['role']}' and skill {m['skill_level']} to '{m['name']}'")
        except (ValueError, KeyError) as e:
            print_err(str(e))

    elif choice == "2":
        try:
            mid = int(prompt("Member ID"))
            role = prompt("New role (driver/mechanic/strategist/scout/medic)")
            m = crew_management.update_role(mid, role)
            print_ok(f"Updated role to '{m['role']}' for '{m['name']}'")
        except (ValueError, KeyError) as e:
            print_err(str(e))

    elif choice == "3":
        try:
            mid = int(prompt("Member ID"))
            skill = int(prompt("New skill level (1-10)"))
            m = crew_management.update_skill(mid, skill)
            print_ok(f"Updated skill to {m['skill_level']} for '{m['name']}'")
        except (ValueError, KeyError) as e:
            print_err(str(e))


# ── Inventory ──────────────────────────────────────────────────────────────────

def menu_inventory():
    print_header("INVENTORY")
    print("  [1] Add car")
    print("  [2] View all cars")
    print("  [3] Update car condition")
    print("  [4] Add spare part")
    print("  [5] View spare parts")
    print("  [6] Add tool")
    print("  [7] View tools")
    print("  [8] View cash balance")
    print("  [0] Back")
    choice = prompt("Choice")

    if choice == "1":
        try:
            name = prompt("Car name")
            speed = int(prompt("Speed (1-10)"))
            car = inventory.add_car(name, speed)
            print_ok(f"Added '{car['name']}' (ID {car['id']}) with speed {car['speed']}")
        except ValueError as e:
            print_err(str(e))

    elif choice == "2":
        cars = inventory.get_all_cars()
        if not cars:
            print("  No cars in inventory.")
        else:
            print(f"\n  {'ID':<5} {'NAME':<20} {'SPEED':<7} {'CONDITION':<12}")
            print("  " + "-" * 46)
            for c in cars:
                print(f"  {c['id']:<5} {c['name']:<20} {c['speed']:<7} {c['condition']:<12}")

    elif choice == "3":
        try:
            cid = int(prompt("Car ID"))
            condition = prompt("Condition (excellent/good/damaged/wrecked)")
            inventory.update_car_condition(cid, condition)
            print_ok(f"Car {cid} condition updated to '{condition}'")
        except (ValueError, KeyError) as e:
            print_err(str(e))

    elif choice == "4":
        try:
            part = prompt("Part name")
            qty = int(prompt("Quantity"))
            inventory.add_spare_part(part, qty)
            print_ok(f"Added {qty}x '{part}'")
        except ValueError as e:
            print_err(str(e))

    elif choice == "5":
        parts = inventory.get_spare_parts()
        if not parts:
            print("  No spare parts in inventory.")
        else:
            for part, qty in parts.items():
                print(f"  {part}: {qty}")

    elif choice == "6":
        try:
            tool = prompt("Tool name")
            qty = int(prompt("Quantity"))
            inventory.add_tool(tool, qty)
            print_ok(f"Added {qty}x '{tool}'")
        except ValueError as e:
            print_err(str(e))

    elif choice == "7":
        tools = inventory.get_tools()
        if not tools:
            print("  No tools in inventory.")
        else:
            for tool, qty in tools.items():
                print(f"  {tool}: {qty}")

    elif choice == "8":
        print(f"  Cash balance: ${inventory.get_cash():,}")


# ── Race Management ────────────────────────────────────────────────────────────

def menu_race():
    print_header("RACE MANAGEMENT")
    print("  [1] Create race")
    print("  [2] Enter driver into race")
    print("  [3] Update race status")
    print("  [4] View all races")
    print("  [0] Back")
    choice = prompt("Choice")

    if choice == "1":
        try:
            name = prompt("Race name")
            location = prompt("Location")
            prize = int(prompt("Prize money ($)"))
            race = race_management.create_race(name, location, prize)
            print_ok(f"Created race '{race['name']}' (ID {race['id']}) at {race['location']}, prize ${race['prize_money']:,}")
        except ValueError as e:
            print_err(str(e))

    elif choice == "2":
        try:
            rid = int(prompt("Race ID"))
            did = int(prompt("Driver member ID"))
            cid = int(prompt("Car ID"))
            race_management.enter_race(rid, did, cid)
            print_ok(f"Driver {did} entered race {rid} with car {cid}")
        except (ValueError, KeyError) as e:
            print_err(str(e))

    elif choice == "3":
        try:
            rid = int(prompt("Race ID"))
            status = prompt("Status (planned/ongoing/completed/cancelled)")
            race_management.update_race_status(rid, status)
            print_ok(f"Race {rid} status updated to '{status}'")
        except (ValueError, KeyError) as e:
            print_err(str(e))

    elif choice == "4":
        races = race_management.get_all_races()
        if not races:
            print("  No races created yet.")
        else:
            print(f"\n  {'ID':<5} {'NAME':<20} {'LOCATION':<15} {'PRIZE':<10} {'STATUS':<12} {'ENTRIES'}")
            print("  " + "-" * 70)
            for r in races:
                entries = len(r['entries'])
                print(f"  {r['id']:<5} {r['name']:<20} {r['location']:<15} ${r['prize_money']:<9} {r['status']:<12} {entries}")


# ── Results ────────────────────────────────────────────────────────────────────

def menu_results():
    print_header("RESULTS")
    print("  [1] Record race result")
    print("  [2] View race result")
    print("  [3] View driver stats")
    print("  [0] Back")
    choice = prompt("Choice")

    if choice == "1":
        try:
            rid = int(prompt("Race ID"))
            raw = prompt("Driver IDs in finishing order (comma separated)")
            placements = [int(x.strip()) for x in raw.split(",")]
            result = results.record_result(rid, placements)
            print_ok(f"Result recorded. Winner: driver ID {result['winner_id']}")
            print(f"  Cash balance now: ${inventory.get_cash():,}")
        except (ValueError, KeyError) as e:
            print_err(str(e))

    elif choice == "2":
        try:
            rid = int(prompt("Race ID"))
            result = results.get_result(rid)
            print(f"  Race {rid} — Winner: {result['winner_id']}, Placements: {result['placements']}")
        except KeyError as e:
            print_err(str(e))

    elif choice == "3":
        try:
            did = int(prompt("Driver member ID"))
            stats = results.get_driver_stats(did)
            print(f"  Driver {did} — Wins: {stats['wins']}, Races: {stats['races']}, Earnings: ${stats['earnings']:,}")
        except (ValueError, KeyError) as e:
            print_err(str(e))


# ── Mission Planning ───────────────────────────────────────────────────────────

def menu_mission():
    print_header("MISSION PLANNING")
    print("  [1] Create mission")
    print("  [2] Assign crew to mission")
    print("  [3] Start mission")
    print("  [4] Complete mission")
    print("  [5] View all missions")
    print("  [0] Back")
    choice = prompt("Choice")

    if choice == "1":
        try:
            mtype = prompt("Mission type (delivery/rescue/recon/repair/heist)")
            desc = prompt("Description")
            m = mission_planning.create_mission(mtype, desc)
            print_ok(f"Mission '{m['type']}' created (ID {m['id']}). Requires: {m['required_roles']}")
        except ValueError as e:
            print_err(str(e))

    elif choice == "2":
        try:
            mid = int(prompt("Mission ID"))
            raw = prompt("Crew member IDs (comma separated)")
            crew_ids = [int(x.strip()) for x in raw.split(",")]
            mission_planning.assign_crew(mid, crew_ids)
            print_ok(f"Crew assigned to mission {mid}")
        except (ValueError, KeyError) as e:
            print_err(str(e))

    elif choice == "3":
        try:
            mid = int(prompt("Mission ID"))
            mission_planning.start_mission(mid)
            print_ok(f"Mission {mid} started!")
        except (ValueError, KeyError) as e:
            print_err(str(e))

    elif choice == "4":
        try:
            mid = int(prompt("Mission ID"))
            success = prompt("Successful? (y/n)").lower() == "y"
            m = mission_planning.complete_mission(mid, success)
            print_ok(f"Mission {mid} marked as '{m['status']}'")
        except (ValueError, KeyError) as e:
            print_err(str(e))

    elif choice == "5":
        missions = mission_planning.get_all_missions()
        if not missions:
            print("  No missions created yet.")
        else:
            print(f"\n  {'ID':<5} {'TYPE':<12} {'STATUS':<12} {'CREW'}")
            print("  " + "-" * 45)
            for m in missions:
                print(f"  {m['id']:<5} {m['type']:<12} {m['status']:<12} {m['assigned_crew']}")


# ── Vehicle Upgrades ───────────────────────────────────────────────────────────

def menu_upgrades():
    print_header("VEHICLE UPGRADES")
    print("  [1] Upgrade car speed")
    print("  [2] Repair damaged car")
    print("  [3] View available upgrades for a car")
    print("  [0] Back")
    choice = prompt("Choice")

    if choice == "1":
        try:
            cid = int(prompt("Car ID"))
            utype = prompt("Upgrade type (engine/tyres/nitrous)")
            car = vehicle_upgrades.upgrade_car(cid, utype)
            print_ok(f"'{car['name']}' upgraded — new speed: {car['speed']}")
        except (ValueError, KeyError) as e:
            print_err(str(e))

    elif choice == "2":
        try:
            cid = int(prompt("Car ID"))
            car = vehicle_upgrades.repair_car(cid)
            print_ok(f"'{car['name']}' repaired — condition: {car['condition']}")
        except (ValueError, KeyError) as e:
            print_err(str(e))

    elif choice == "3":
        try:
            cid = int(prompt("Car ID"))
            upgrades = vehicle_upgrades.get_available_upgrades(cid)
            if not upgrades:
                print("  No upgrades currently available for this car.")
            else:
                for u in upgrades:
                    print(f"  {u['upgrade_type']:<10} requires '{u['part_required']}', gives +{u['speed_boost']} speed")
        except (ValueError, KeyError) as e:
            print_err(str(e))


# ── Leaderboard ────────────────────────────────────────────────────────────────

def menu_leaderboard():
    print_header("LEADERBOARD")
    print("  [1] View full leaderboard")
    print("  [2] View top driver")
    print("  [3] View specific driver position")
    print("  [0] Back")
    choice = prompt("Choice")

    if choice == "1":
        leaderboard.print_leaderboard()

    elif choice == "2":
        try:
            top = leaderboard.get_top_driver()
            print(f"  🏆 {top['name']} — {top['wins']} wins, ${top['earnings']:,} earned")
        except ValueError as e:
            print_err(str(e))

    elif choice == "3":
        try:
            did = int(prompt("Driver member ID"))
            entry = leaderboard.get_driver_position(did)
            print(f"  Position {entry['position']}: {entry['name']} — {entry['wins']} wins, ${entry['earnings']:,} earned")
        except (ValueError, KeyError) as e:
            print_err(str(e))


# ── Main Menu ──────────────────────────────────────────────────────────────────

MENU = {
    "1": ("Registration",     menu_registration),
    "2": ("Crew Management",  menu_crew),
    "3": ("Inventory",        menu_inventory),
    "4": ("Race Management",  menu_race),
    "5": ("Results",          menu_results),
    "6": ("Mission Planning", menu_mission),
    "7": ("Vehicle Upgrades", menu_upgrades),
    "8": ("Leaderboard",      menu_leaderboard),
    "0": ("Exit",             None),
}


def main():
    print("\n" + "█" * 45)
    print("    🏎  STREETRACE MANAGER  🏎")
    print("█" * 45)

    while True:
        print("\n  MAIN MENU")
        for key, (label, _) in MENU.items():
            print(f"  [{key}] {label}")

        choice = prompt("Select")

        if choice == "0":
            print("\n  Goodbye. Stay fast.\n")
            break
        elif choice in MENU:
            _, handler = MENU[choice]
            handler()
        else:
            print("  Invalid choice. Try again.")


if __name__ == "__main__":
    main()