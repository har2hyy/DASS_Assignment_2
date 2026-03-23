#!/usr/bin/env python3
"""
StreetRace Manager - Command Line Interface

A comprehensive CLI for managing underground street races,
crew members, vehicles, and missions.
"""

import os
import sys
from typing import Optional, List, Callable

# Handle imports for both package and direct execution
try:
    from .streetrace_manager import StreetRaceManager
    from .models import Role, CarStatus, RaceStatus, MissionStatus, MissionType
    from .exceptions import StreetRaceError
except ImportError:
    from streetrace_manager import StreetRaceManager
    from models import Role, CarStatus, RaceStatus, MissionStatus, MissionType
    from exceptions import StreetRaceError


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @classmethod
    def disable(cls):
        """Disable colors (for non-supporting terminals)."""
        cls.HEADER = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.ENDC = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''


class CLI:
    """Main CLI class for StreetRace Manager."""

    def __init__(self):
        """Initialize the CLI with a StreetRaceManager instance."""
        self.manager = StreetRaceManager(initial_cash=10000.0)
        self.running = True

        # Check if terminal supports colors
        if not sys.stdout.isatty():
            Colors.disable()

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title: str):
        """Print a formatted header."""
        width = 60
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * width}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{title.center(width)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * width}{Colors.ENDC}\n")

    def print_subheader(self, title: str):
        """Print a formatted subheader."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}--- {title} ---{Colors.ENDC}\n")

    def print_success(self, message: str):
        """Print a success message."""
        print(f"{Colors.GREEN}[SUCCESS] {message}{Colors.ENDC}")

    def print_error(self, message: str):
        """Print an error message."""
        print(f"{Colors.RED}[ERROR] {message}{Colors.ENDC}")

    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"{Colors.YELLOW}[WARNING] {message}{Colors.ENDC}")

    def print_info(self, message: str):
        """Print an info message."""
        print(f"{Colors.BLUE}[INFO] {message}{Colors.ENDC}")

    def print_table(self, headers: List[str], rows: List[List[str]], col_widths: Optional[List[int]] = None):
        """Print a formatted table."""
        if not col_widths:
            col_widths = [max(len(str(row[i])) for row in [headers] + rows) + 2 for i in range(len(headers))]

        # Header
        header_row = "".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
        print(f"{Colors.BOLD}{header_row}{Colors.ENDC}")
        print("-" * sum(col_widths))

        # Rows
        for row in rows:
            print("".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)))

    def get_input(self, prompt: str, required: bool = True) -> str:
        """Get user input with optional validation."""
        while True:
            value = input(f"{Colors.CYAN}{prompt}: {Colors.ENDC}").strip()
            if value or not required:
                return value
            self.print_error("This field is required. Please try again.")

    def get_int_input(self, prompt: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """Get integer input with range validation."""
        while True:
            try:
                value = int(input(f"{Colors.CYAN}{prompt}: {Colors.ENDC}"))
                if min_val is not None and value < min_val:
                    self.print_error(f"Value must be at least {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    self.print_error(f"Value must be at most {max_val}")
                    continue
                return value
            except ValueError:
                self.print_error("Please enter a valid number")

    def get_float_input(self, prompt: str, min_val: Optional[float] = None) -> float:
        """Get float input with optional minimum validation."""
        while True:
            try:
                value = float(input(f"{Colors.CYAN}{prompt}: {Colors.ENDC}"))
                if min_val is not None and value < min_val:
                    self.print_error(f"Value must be at least {min_val}")
                    continue
                return value
            except ValueError:
                self.print_error("Please enter a valid number")

    def get_choice(self, prompt: str, options: List[str]) -> int:
        """Get a choice from a list of options."""
        for i, option in enumerate(options, 1):
            print(f"  {Colors.YELLOW}{i}.{Colors.ENDC} {option}")
        print()
        return self.get_int_input(prompt, 1, len(options))

    def confirm(self, prompt: str) -> bool:
        """Get a yes/no confirmation."""
        response = input(f"{Colors.CYAN}{prompt} (y/n): {Colors.ENDC}").strip().lower()
        return response in ('y', 'yes')

    def pause(self):
        """Pause and wait for user input."""
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")

    # =================== MAIN MENU ===================

    def main_menu(self):
        """Display and handle the main menu."""
        while self.running:
            self.clear_screen()
            self.print_header("STREETRACE MANAGER")

            print(f"  {Colors.YELLOW}1.{Colors.ENDC} Crew Management")
            print(f"  {Colors.YELLOW}2.{Colors.ENDC} Inventory Management")
            print(f"  {Colors.YELLOW}3.{Colors.ENDC} Race Management")
            print(f"  {Colors.YELLOW}4.{Colors.ENDC} Mission Planning")
            print(f"  {Colors.YELLOW}5.{Colors.ENDC} Leaderboard & Statistics")
            print(f"  {Colors.YELLOW}6.{Colors.ENDC} Notifications")
            print(f"  {Colors.YELLOW}7.{Colors.ENDC} System Status")
            print(f"  {Colors.YELLOW}8.{Colors.ENDC} Quick Actions")
            print(f"  {Colors.YELLOW}0.{Colors.ENDC} Exit")
            print()

            choice = self.get_int_input("Select an option", 0, 8)

            if choice == 0:
                self.exit_program()
            elif choice == 1:
                self.crew_menu()
            elif choice == 2:
                self.inventory_menu()
            elif choice == 3:
                self.race_menu()
            elif choice == 4:
                self.mission_menu()
            elif choice == 5:
                self.leaderboard_menu()
            elif choice == 6:
                self.notification_menu()
            elif choice == 7:
                self.show_system_status()
            elif choice == 8:
                self.quick_actions_menu()

    def exit_program(self):
        """Exit the program."""
        if self.confirm("Are you sure you want to exit?"):
            self.clear_screen()
            print(f"\n{Colors.GREEN}Thank you for using StreetRace Manager!{Colors.ENDC}")
            print(f"{Colors.CYAN}Stay fast, stay safe!{Colors.ENDC}\n")
            self.running = False

    # =================== CREW MANAGEMENT ===================

    def crew_menu(self):
        """Crew management submenu."""
        while True:
            self.clear_screen()
            self.print_header("CREW MANAGEMENT")

            print(f"  {Colors.YELLOW}1.{Colors.ENDC} Register New Crew Member")
            print(f"  {Colors.YELLOW}2.{Colors.ENDC} Assign Role to Member")
            print(f"  {Colors.YELLOW}3.{Colors.ENDC} Update Skill Level")
            print(f"  {Colors.YELLOW}4.{Colors.ENDC} View All Crew Members")
            print(f"  {Colors.YELLOW}5.{Colors.ENDC} View Members by Role")
            print(f"  {Colors.YELLOW}6.{Colors.ENDC} Search Crew Member")
            print(f"  {Colors.YELLOW}7.{Colors.ENDC} View Member Details")
            print(f"  {Colors.YELLOW}8.{Colors.ENDC} Remove Crew Member")
            print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back to Main Menu")
            print()

            choice = self.get_int_input("Select an option", 0, 8)

            if choice == 0:
                break
            elif choice == 1:
                self.register_crew_member()
            elif choice == 2:
                self.assign_role()
            elif choice == 3:
                self.update_skill_level()
            elif choice == 4:
                self.view_all_crew()
            elif choice == 5:
                self.view_crew_by_role()
            elif choice == 6:
                self.search_crew()
            elif choice == 7:
                self.view_member_details()
            elif choice == 8:
                self.remove_crew_member()

    def register_crew_member(self):
        """Register a new crew member."""
        self.print_subheader("Register New Crew Member")

        name = self.get_input("Enter crew member name (2-50 characters)")

        try:
            member = self.manager.registration.register_member(name)
            self.print_success(f"Crew member registered successfully!")
            print(f"  ID: {Colors.BOLD}{member.member_id}{Colors.ENDC}")
            print(f"  Name: {member.name}")

            if self.confirm("\nWould you like to assign a role now?"):
                self._assign_role_to_member(member.member_id)

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def assign_role(self):
        """Assign a role to a crew member."""
        self.print_subheader("Assign Role to Crew Member")

        self._show_members_without_role()

        member_id = self.get_input("Enter member ID")
        self._assign_role_to_member(member_id)
        self.pause()

    def _assign_role_to_member(self, member_id: str):
        """Helper to assign role to a specific member."""
        print("\nAvailable roles:")
        roles = ["Driver", "Mechanic", "Strategist"]
        choice = self.get_choice("Select role", roles)

        role_map = {1: "driver", 2: "mechanic", 3: "strategist"}
        role = role_map[choice]

        try:
            member = self.manager.crew_management.assign_role(member_id, role)
            self.print_success(f"Role '{role}' assigned to {member.name}")

            if self.confirm("Would you like to set skill level?"):
                skill = self.get_int_input("Enter skill level (1-10)", 1, 10)
                self.manager.crew_management.update_skill_level(member_id, skill)
                self.print_success(f"Skill level set to {skill}")

        except StreetRaceError as e:
            self.print_error(str(e))

    def _show_members_without_role(self):
        """Show members who don't have a role assigned."""
        members = self.manager.registration.list_active_members()
        no_role = [m for m in members if m.role is None]

        if no_role:
            print("\nMembers without roles:")
            for m in no_role:
                print(f"  - {m.member_id}: {m.name}")
            print()

    def update_skill_level(self):
        """Update a crew member's skill level."""
        self.print_subheader("Update Skill Level")

        self._show_all_members_brief()

        member_id = self.get_input("Enter member ID")
        skill = self.get_int_input("Enter new skill level (1-10)", 1, 10)

        try:
            member = self.manager.crew_management.update_skill_level(member_id, skill)
            self.print_success(f"Skill level for {member.name} updated to {skill}")
        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def view_all_crew(self):
        """View all crew members."""
        self.print_subheader("All Crew Members")

        members = self.manager.registration.list_all_members()

        if not members:
            self.print_warning("No crew members registered yet.")
        else:
            headers = ["ID", "Name", "Role", "Skill", "Status"]
            rows = []
            for m in members:
                role = m.role.value.capitalize() if m.role else "Unassigned"
                status = "Active" if m.is_active else "Inactive"
                if m.is_busy:
                    status = "Busy"
                rows.append([m.member_id, m.name, role, str(m.skill_level), status])

            self.print_table(headers, rows, [12, 25, 12, 8, 10])

        self.pause()

    def view_crew_by_role(self):
        """View crew members filtered by role."""
        self.print_subheader("View Crew by Role")

        print("Select role to filter:")
        roles = ["Driver", "Mechanic", "Strategist", "All Roles"]
        choice = self.get_choice("Select role", roles)

        if choice == 4:
            self.view_all_crew()
            return

        role_map = {1: "driver", 2: "mechanic", 3: "strategist"}
        role = role_map[choice]

        try:
            members = self.manager.crew_management.list_members_by_role(role)

            if not members:
                self.print_warning(f"No {role}s found.")
            else:
                print(f"\n{role.capitalize()}s ({len(members)} found):\n")
                headers = ["ID", "Name", "Skill Level", "Available"]
                rows = []
                for m in members:
                    available = "Yes" if not m.is_busy else "No"
                    rows.append([m.member_id, m.name, str(m.skill_level), available])
                self.print_table(headers, rows, [12, 25, 12, 12])

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def search_crew(self):
        """Search for crew members by name."""
        self.print_subheader("Search Crew Member")

        query = self.get_input("Enter search term")
        results = self.manager.registration.search_members_by_name(query)

        if not results:
            self.print_warning(f"No members found matching '{query}'")
        else:
            print(f"\nFound {len(results)} member(s):\n")
            for m in results:
                role = m.role.value.capitalize() if m.role else "Unassigned"
                print(f"  {Colors.BOLD}{m.member_id}{Colors.ENDC}: {m.name} ({role})")

        self.pause()

    def view_member_details(self):
        """View detailed information about a crew member."""
        self.print_subheader("View Member Details")

        self._show_all_members_brief()

        member_id = self.get_input("Enter member ID")

        try:
            profile = self.manager.get_member_full_profile(member_id)
            m = profile["member"]
            stats = profile["statistics"]

            print(f"\n{Colors.BOLD}=== Member Profile ==={Colors.ENDC}")
            print(f"  ID:          {m['id']}")
            print(f"  Name:        {m['name']}")
            print(f"  Role:        {m['role'] or 'Unassigned'}")
            print(f"  Skill Level: {m['skill_level']}")
            print(f"  Status:      {'Active' if m['is_active'] else 'Inactive'}")
            print(f"  Busy:        {'Yes' if m['is_busy'] else 'No'}")

            print(f"\n{Colors.BOLD}=== Statistics ==={Colors.ENDC}")
            print(f"  Races Participated: {stats['races_participated']}")
            print(f"  Races Won:          {stats['races_won']}")
            print(f"  Win Ratio:          {stats['win_ratio']:.1%}")
            print(f"  Total Earnings:     ${stats['total_earnings']:.2f}")
            print(f"  Ranking Points:     {stats['ranking_points']}")
            print(f"  Current Rank:       #{profile['current_rank'] or 'N/A'}")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def remove_crew_member(self):
        """Remove a crew member."""
        self.print_subheader("Remove Crew Member")

        self._show_all_members_brief()

        member_id = self.get_input("Enter member ID to remove")

        try:
            member = self.manager.registration.get_member(member_id)

            if self.confirm(f"Are you sure you want to remove {member.name}?"):
                self.manager.registration.remove_member(member_id)
                self.print_success(f"Member {member.name} has been deactivated")
            else:
                self.print_info("Operation cancelled")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def _show_all_members_brief(self):
        """Show a brief list of all members."""
        members = self.manager.registration.list_active_members()
        if members:
            print("\nRegistered members:")
            for m in members:
                role = f"({m.role.value})" if m.role else "(no role)"
                print(f"  - {m.member_id}: {m.name} {role}")
            print()

    # =================== INVENTORY MANAGEMENT ===================

    def inventory_menu(self):
        """Inventory management submenu."""
        while True:
            self.clear_screen()
            self.print_header("INVENTORY MANAGEMENT")

            balance = self.manager.inventory.get_cash_balance()
            print(f"  Current Cash Balance: {Colors.GREEN}${balance:,.2f}{Colors.ENDC}\n")

            print(f"  {Colors.YELLOW}1.{Colors.ENDC} Add New Car")
            print(f"  {Colors.YELLOW}2.{Colors.ENDC} View All Cars")
            print(f"  {Colors.YELLOW}3.{Colors.ENDC} View Available Cars")
            print(f"  {Colors.YELLOW}4.{Colors.ENDC} View Damaged Cars")
            print(f"  {Colors.YELLOW}5.{Colors.ENDC} Update Car Status")
            print(f"  {Colors.YELLOW}6.{Colors.ENDC} Add Spare Parts")
            print(f"  {Colors.YELLOW}7.{Colors.ENDC} View Spare Parts")
            print(f"  {Colors.YELLOW}8.{Colors.ENDC} Add Tools")
            print(f"  {Colors.YELLOW}9.{Colors.ENDC} View Tools")
            print(f"  {Colors.YELLOW}10.{Colors.ENDC} Manage Cash")
            print(f"  {Colors.YELLOW}11.{Colors.ENDC} View Inventory Summary")
            print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back to Main Menu")
            print()

            choice = self.get_int_input("Select an option", 0, 11)

            if choice == 0:
                break
            elif choice == 1:
                self.add_car()
            elif choice == 2:
                self.view_all_cars()
            elif choice == 3:
                self.view_available_cars()
            elif choice == 4:
                self.view_damaged_cars()
            elif choice == 5:
                self.update_car_status()
            elif choice == 6:
                self.add_spare_parts()
            elif choice == 7:
                self.view_spare_parts()
            elif choice == 8:
                self.add_tools()
            elif choice == 9:
                self.view_tools()
            elif choice == 10:
                self.manage_cash()
            elif choice == 11:
                self.view_inventory_summary()

    def add_car(self):
        """Add a new car to inventory."""
        self.print_subheader("Add New Car")

        make = self.get_input("Enter car make (e.g., Toyota, Nissan)")
        model = self.get_input("Enter car model (e.g., Supra, GT-R)")
        year = self.get_int_input("Enter year", 1990, 2030)
        performance = self.get_int_input("Enter performance rating (1-10)", 1, 10)

        try:
            car = self.manager.inventory.add_car(make, model, year, performance_rating=performance)
            self.print_success("Car added successfully!")
            print(f"  ID: {Colors.BOLD}{car.car_id}{Colors.ENDC}")
            print(f"  {car.year} {car.make} {car.model}")
            print(f"  Performance: {car.performance_rating}/10")
        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def view_all_cars(self):
        """View all cars in inventory."""
        self.print_subheader("All Cars")

        cars = self.manager.inventory.list_all_cars()

        if not cars:
            self.print_warning("No cars in inventory.")
        else:
            headers = ["ID", "Car", "Year", "Performance", "Status", "Damage"]
            rows = []
            for c in cars:
                car_name = f"{c.make} {c.model}"
                rows.append([
                    c.car_id,
                    car_name[:20],
                    str(c.year),
                    f"{c.performance_rating}/10",
                    c.status.value,
                    f"{c.damage_level}%"
                ])
            self.print_table(headers, rows, [10, 22, 6, 12, 12, 8])

        self.pause()

    def view_available_cars(self):
        """View available cars."""
        self.print_subheader("Available Cars")

        cars = self.manager.inventory.list_available_cars()

        if not cars:
            self.print_warning("No available cars.")
        else:
            print(f"Found {len(cars)} available car(s):\n")
            for c in cars:
                print(f"  {Colors.BOLD}{c.car_id}{Colors.ENDC}: {c.year} {c.make} {c.model} (Performance: {c.performance_rating}/10)")

        self.pause()

    def view_damaged_cars(self):
        """View damaged cars."""
        self.print_subheader("Damaged Cars")

        cars = self.manager.inventory.list_damaged_cars()

        if not cars:
            self.print_success("No damaged cars!")
        else:
            print(f"Found {len(cars)} damaged car(s):\n")
            for c in cars:
                print(f"  {Colors.RED}{c.car_id}{Colors.ENDC}: {c.year} {c.make} {c.model} (Damage: {c.damage_level}%)")

            if self.confirm("\nWould you like to create repair missions for these cars?"):
                self._create_repair_missions_for_damaged_cars(cars)

        self.pause()

    def _create_repair_missions_for_damaged_cars(self, cars):
        """Create repair missions for damaged cars."""
        for car in cars:
            try:
                mission = self.manager.mission_planning.create_repair_mission(car.car_id)
                self.print_success(f"Repair mission created for {car.make} {car.model}: {mission.mission_id}")
            except StreetRaceError as e:
                self.print_error(f"Failed to create mission for {car.car_id}: {e}")

    def update_car_status(self):
        """Update a car's status."""
        self.print_subheader("Update Car Status")

        self._show_all_cars_brief()

        car_id = self.get_input("Enter car ID")

        print("\nSelect new status:")
        statuses = ["Available", "In Race", "Damaged", "In Repair"]
        choice = self.get_choice("Select status", statuses)

        status_map = {1: "available", 2: "in_race", 3: "damaged", 4: "in_repair"}
        status = status_map[choice]

        try:
            car = self.manager.inventory.update_car_status(car_id, status)
            self.print_success(f"Car status updated to {status}")
        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def _show_all_cars_brief(self):
        """Show a brief list of all cars."""
        cars = self.manager.inventory.list_all_cars()
        if cars:
            print("\nCars in inventory:")
            for c in cars:
                print(f"  - {c.car_id}: {c.year} {c.make} {c.model} [{c.status.value}]")
            print()

    def add_spare_parts(self):
        """Add spare parts to inventory."""
        self.print_subheader("Add Spare Parts")

        part_name = self.get_input("Enter part name (e.g., engine_parts, tires)")
        quantity = self.get_int_input("Enter quantity", 1, 1000)
        cost = self.get_float_input("Enter unit cost ($)", 0)

        try:
            part = self.manager.inventory.add_spare_parts(part_name, quantity, cost)
            self.print_success(f"Added {quantity} x {part_name}")
            print(f"  Total in stock: {part.quantity}")
        except Exception as e:
            self.print_error(str(e))

        self.pause()

    def view_spare_parts(self):
        """View all spare parts."""
        self.print_subheader("Spare Parts Inventory")

        parts = self.manager.inventory.list_all_spare_parts()

        if not parts:
            self.print_warning("No spare parts in inventory.")
        else:
            headers = ["Part Name", "Quantity", "Unit Cost"]
            rows = [[p.name, str(p.quantity), f"${p.unit_cost:.2f}"] for p in parts]
            self.print_table(headers, rows, [25, 12, 12])

        self.pause()

    def add_tools(self):
        """Add tools to inventory."""
        self.print_subheader("Add Tools")

        tool_name = self.get_input("Enter tool name")
        quantity = self.get_int_input("Enter quantity", 1, 100)

        try:
            tool = self.manager.inventory.add_tools(tool_name, quantity)
            self.print_success(f"Added {quantity} x {tool_name}")
            print(f"  Total in stock: {tool.quantity}")
        except Exception as e:
            self.print_error(str(e))

        self.pause()

    def view_tools(self):
        """View all tools."""
        self.print_subheader("Tools Inventory")

        tools = self.manager.inventory.list_all_tools()

        if not tools:
            self.print_warning("No tools in inventory.")
        else:
            headers = ["Tool Name", "Quantity", "Condition"]
            rows = [[t.name, str(t.quantity), t.condition] for t in tools]
            self.print_table(headers, rows, [25, 12, 12])

        self.pause()

    def manage_cash(self):
        """Manage cash balance."""
        self.print_subheader("Cash Management")

        balance = self.manager.inventory.get_cash_balance()
        print(f"Current balance: {Colors.GREEN}${balance:,.2f}{Colors.ENDC}\n")

        print("What would you like to do?")
        options = ["Add Cash", "Deduct Cash", "Cancel"]
        choice = self.get_choice("Select action", options)

        if choice == 3:
            return

        amount = self.get_float_input("Enter amount ($)", 0.01)

        try:
            if choice == 1:
                new_balance = self.manager.inventory.add_cash(amount)
                self.print_success(f"Added ${amount:,.2f}")
            else:
                new_balance = self.manager.inventory.deduct_cash(amount)
                self.print_success(f"Deducted ${amount:,.2f}")

            print(f"New balance: {Colors.GREEN}${new_balance:,.2f}{Colors.ENDC}")
        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def view_inventory_summary(self):
        """View inventory summary."""
        self.print_subheader("Inventory Summary")

        summary = self.manager.inventory.get_inventory_summary()

        print(f"  {Colors.BOLD}Cars:{Colors.ENDC}")
        print(f"    Total:     {summary['total_cars']}")
        print(f"    Available: {summary['available_cars']}")
        print(f"    Damaged:   {summary['damaged_cars']}")

        print(f"\n  {Colors.BOLD}Parts & Tools:{Colors.ENDC}")
        print(f"    Part Types: {summary['total_spare_parts_types']}")
        print(f"    Tool Types: {summary['total_tools_types']}")

        if summary['low_stock_parts']:
            print(f"\n  {Colors.YELLOW}Low Stock Warning:{Colors.ENDC} {', '.join(summary['low_stock_parts'])}")

        print(f"\n  {Colors.BOLD}Finances:{Colors.ENDC}")
        print(f"    Cash Balance: ${summary['cash_balance']:,.2f}")
        if summary['is_low_on_cash']:
            self.print_warning("Cash balance is low!")

        self.pause()

    # =================== RACE MANAGEMENT ===================

    def race_menu(self):
        """Race management submenu."""
        while True:
            self.clear_screen()
            self.print_header("RACE MANAGEMENT")

            scheduled = len(self.manager.race_management.list_scheduled_races())
            in_progress = len(self.manager.race_management.get_races_by_status("in_progress"))
            print(f"  Scheduled Races: {scheduled}  |  In Progress: {in_progress}\n")

            print(f"  {Colors.YELLOW}1.{Colors.ENDC} Create New Race")
            print(f"  {Colors.YELLOW}2.{Colors.ENDC} View Scheduled Races")
            print(f"  {Colors.YELLOW}3.{Colors.ENDC} View All Races")
            print(f"  {Colors.YELLOW}4.{Colors.ENDC} Add Participant to Race")
            print(f"  {Colors.YELLOW}5.{Colors.ENDC} Start Race")
            print(f"  {Colors.YELLOW}6.{Colors.ENDC} Complete Race")
            print(f"  {Colors.YELLOW}7.{Colors.ENDC} Cancel Race")
            print(f"  {Colors.YELLOW}8.{Colors.ENDC} View Race Details")
            print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back to Main Menu")
            print()

            choice = self.get_int_input("Select an option", 0, 8)

            if choice == 0:
                break
            elif choice == 1:
                self.create_race()
            elif choice == 2:
                self.view_scheduled_races()
            elif choice == 3:
                self.view_all_races()
            elif choice == 4:
                self.add_race_participant()
            elif choice == 5:
                self.start_race()
            elif choice == 6:
                self.complete_race()
            elif choice == 7:
                self.cancel_race()
            elif choice == 8:
                self.view_race_details()

    def create_race(self):
        """Create a new race."""
        self.print_subheader("Create New Race")

        name = self.get_input("Enter race name")

        print("\nSelect race type:")
        types = ["Street", "Circuit", "Drag", "Drift"]
        type_choice = self.get_choice("Select type", types)
        race_type = types[type_choice - 1].lower()

        prize_pool = self.get_float_input("Enter prize pool ($)", 0)
        min_participants = self.get_int_input("Minimum participants", 2, 20)

        try:
            race = self.manager.race_management.create_race(
                name, race_type, prize_pool, min_participants=min_participants
            )
            self.print_success("Race created successfully!")
            print(f"  Race ID: {Colors.BOLD}{race.race_id}{Colors.ENDC}")
            print(f"  Name: {race.name}")
            print(f"  Type: {race.race_type}")
            print(f"  Prize Pool: ${race.prize_pool:,.2f}")

            if self.confirm("\nWould you like to add participants now?"):
                self._add_participants_to_race(race.race_id)

        except Exception as e:
            self.print_error(str(e))

        self.pause()

    def _add_participants_to_race(self, race_id: str):
        """Helper to add multiple participants to a race."""
        while True:
            self._show_available_drivers()
            driver_id = self.get_input("Enter driver ID (or 'done' to finish)")

            if driver_id.lower() == 'done':
                break

            self._show_available_cars()
            car_id = self.get_input("Enter car ID")

            try:
                self.manager.race_management.add_participant(race_id, driver_id, car_id)
                self.print_success("Participant added!")

                count = self.manager.race_management.get_participant_count(race_id)
                print(f"  Total participants: {count}")
            except StreetRaceError as e:
                self.print_error(str(e))

            if not self.confirm("\nAdd another participant?"):
                break

    def _show_available_drivers(self):
        """Show available drivers."""
        try:
            drivers = self.manager.crew_management.list_available_members_by_role("driver")
            if drivers:
                print("\nAvailable Drivers:")
                for d in drivers:
                    print(f"  - {d.member_id}: {d.name} (Skill: {d.skill_level})")
            else:
                self.print_warning("No available drivers!")
        except StreetRaceError:
            pass
        print()

    def _show_available_cars(self):
        """Show available cars."""
        cars = self.manager.inventory.list_available_cars()
        if cars:
            print("\nAvailable Cars:")
            for c in cars:
                print(f"  - {c.car_id}: {c.year} {c.make} {c.model}")
        else:
            self.print_warning("No available cars!")
        print()

    def view_scheduled_races(self):
        """View scheduled races."""
        self.print_subheader("Scheduled Races")

        races = self.manager.race_management.list_scheduled_races()

        if not races:
            self.print_warning("No scheduled races.")
        else:
            headers = ["Race ID", "Name", "Type", "Prize Pool", "Participants"]
            rows = []
            for r in races:
                rows.append([
                    r.race_id,
                    r.name[:20],
                    r.race_type,
                    f"${r.prize_pool:,.2f}",
                    f"{len(r.participants)}/{r.min_participants}"
                ])
            self.print_table(headers, rows, [10, 22, 10, 14, 12])

        self.pause()

    def view_all_races(self):
        """View all races."""
        self.print_subheader("All Races")

        races = self.manager.race_management.list_all_races()

        if not races:
            self.print_warning("No races found.")
        else:
            headers = ["Race ID", "Name", "Type", "Prize", "Status", "Participants"]
            rows = []
            for r in races:
                rows.append([
                    r.race_id,
                    r.name[:18],
                    r.race_type,
                    f"${r.prize_pool:,.0f}",
                    r.status.value,
                    str(len(r.participants))
                ])
            self.print_table(headers, rows, [10, 20, 10, 12, 12, 12])

        self.pause()

    def add_race_participant(self):
        """Add a participant to a race."""
        self.print_subheader("Add Race Participant")

        self._show_scheduled_races_brief()

        race_id = self.get_input("Enter race ID")

        self._show_available_drivers()
        driver_id = self.get_input("Enter driver ID")

        self._show_available_cars()
        car_id = self.get_input("Enter car ID")

        try:
            self.manager.race_management.add_participant(race_id, driver_id, car_id)
            self.print_success("Participant added successfully!")

            count = self.manager.race_management.get_participant_count(race_id)
            race = self.manager.race_management.get_race_details(race_id)
            print(f"  Total participants: {count}/{race.min_participants}")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def _show_scheduled_races_brief(self):
        """Show brief list of scheduled races."""
        races = self.manager.race_management.list_scheduled_races()
        if races:
            print("\nScheduled Races:")
            for r in races:
                print(f"  - {r.race_id}: {r.name} ({len(r.participants)} participants)")
            print()

    def start_race(self):
        """Start a race."""
        self.print_subheader("Start Race")

        self._show_scheduled_races_brief()

        race_id = self.get_input("Enter race ID to start")

        try:
            race = self.manager.race_management.get_race_details(race_id)

            print(f"\nRace: {race.name}")
            print(f"Participants: {len(race.participants)}")
            print(f"Prize Pool: ${race.prize_pool:,.2f}")

            if self.confirm("\nStart this race?"):
                started_race = self.manager.race_management.start_race(race_id)
                self.print_success(f"Race '{started_race.name}' has started!")
                print(f"  Started at: {started_race.started_at}")
            else:
                self.print_info("Race start cancelled")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def complete_race(self):
        """Complete a race with results."""
        self.print_subheader("Complete Race")

        in_progress = self.manager.race_management.get_races_by_status("in_progress")

        if not in_progress:
            self.print_warning("No races in progress.")
            self.pause()
            return

        print("Races in progress:")
        for r in in_progress:
            print(f"  - {r.race_id}: {r.name} ({len(r.participants)} participants)")
        print()

        race_id = self.get_input("Enter race ID to complete")

        try:
            race = self.manager.race_management.get_race_details(race_id)

            print(f"\nEnter finishing positions for {race.name}:\n")

            positions = {}
            damaged_cars = []

            for i, participant in enumerate(race.participants):
                driver = self.manager.registration.get_member(participant.driver_id)
                car = self.manager.inventory.get_car(participant.car_id)

                position = self.get_int_input(
                    f"Position for {driver.name} ({car.make} {car.model})",
                    1, len(race.participants)
                )
                positions[position] = participant.driver_id

                if self.confirm(f"  Was {car.make} {car.model} damaged?"):
                    damaged_cars.append(participant.car_id)

            completed_race = self.manager.race_management.complete_race(race_id, positions, damaged_cars)

            self.print_success(f"Race '{completed_race.name}' completed!")

            # Show results
            print("\n--- Race Results ---")
            for pos in sorted(positions.keys()):
                driver = self.manager.registration.get_member(positions[pos])
                prize = self.manager.results.calculate_prize_money(pos, race.prize_pool)
                print(f"  {pos}. {driver.name} - ${prize:,.2f}")

            if damaged_cars:
                print(f"\n  Damaged cars: {len(damaged_cars)}")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def cancel_race(self):
        """Cancel a scheduled race."""
        self.print_subheader("Cancel Race")

        self._show_scheduled_races_brief()

        race_id = self.get_input("Enter race ID to cancel")

        try:
            race = self.manager.race_management.get_race_details(race_id)

            if self.confirm(f"Are you sure you want to cancel '{race.name}'?"):
                self.manager.race_management.cancel_race(race_id)
                self.print_success(f"Race '{race.name}' has been cancelled")
            else:
                self.print_info("Operation cancelled")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def view_race_details(self):
        """View detailed race information."""
        self.print_subheader("Race Details")

        races = self.manager.race_management.list_all_races()
        if races:
            print("All Races:")
            for r in races:
                print(f"  - {r.race_id}: {r.name} [{r.status.value}]")
            print()

        race_id = self.get_input("Enter race ID")

        try:
            race = self.manager.race_management.get_race_details(race_id)

            print(f"\n{Colors.BOLD}=== Race Details ==={Colors.ENDC}")
            print(f"  ID:         {race.race_id}")
            print(f"  Name:       {race.name}")
            print(f"  Type:       {race.race_type}")
            print(f"  Prize Pool: ${race.prize_pool:,.2f}")
            print(f"  Status:     {race.status.value}")
            print(f"  Min Participants: {race.min_participants}")

            print(f"\n{Colors.BOLD}Participants ({len(race.participants)}):{Colors.ENDC}")
            for p in race.participants:
                driver = self.manager.registration.get_member(p.driver_id)
                car = self.manager.inventory.get_car(p.car_id)
                position = f" - Position: {p.position}" if p.position else ""
                damaged = " [DAMAGED]" if p.is_damaged else ""
                print(f"  - {driver.name} driving {car.make} {car.model}{position}{damaged}")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    # =================== MISSION PLANNING ===================

    def mission_menu(self):
        """Mission planning submenu."""
        while True:
            self.clear_screen()
            self.print_header("MISSION PLANNING")

            pending = len(self.manager.mission_planning.list_pending_missions())
            active = len(self.manager.mission_planning.list_active_missions())
            print(f"  Pending: {pending}  |  Active: {active}\n")

            print(f"  {Colors.YELLOW}1.{Colors.ENDC} Create New Mission")
            print(f"  {Colors.YELLOW}2.{Colors.ENDC} Create Repair Mission")
            print(f"  {Colors.YELLOW}3.{Colors.ENDC} View Pending Missions")
            print(f"  {Colors.YELLOW}4.{Colors.ENDC} View Active Missions")
            print(f"  {Colors.YELLOW}5.{Colors.ENDC} View All Missions")
            print(f"  {Colors.YELLOW}6.{Colors.ENDC} Assign Crew to Mission")
            print(f"  {Colors.YELLOW}7.{Colors.ENDC} Start Mission")
            print(f"  {Colors.YELLOW}8.{Colors.ENDC} Complete Mission")
            print(f"  {Colors.YELLOW}9.{Colors.ENDC} Check Role Availability")
            print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back to Main Menu")
            print()

            choice = self.get_int_input("Select an option", 0, 9)

            if choice == 0:
                break
            elif choice == 1:
                self.create_mission()
            elif choice == 2:
                self.create_repair_mission()
            elif choice == 3:
                self.view_pending_missions()
            elif choice == 4:
                self.view_active_missions()
            elif choice == 5:
                self.view_all_missions()
            elif choice == 6:
                self.assign_crew_to_mission()
            elif choice == 7:
                self.start_mission()
            elif choice == 8:
                self.complete_mission()
            elif choice == 9:
                self.check_role_availability()

    def create_mission(self):
        """Create a new mission."""
        self.print_subheader("Create New Mission")

        name = self.get_input("Enter mission name")

        print("\nSelect mission type:")
        types = ["Delivery", "Rescue", "Repair", "Heist"]
        type_choice = self.get_choice("Select type", types)
        mission_type = types[type_choice - 1].lower()

        reward = self.get_float_input("Enter reward ($)", 0)

        try:
            mission = self.manager.mission_planning.create_mission(name, mission_type, reward)
            self.print_success("Mission created successfully!")
            print(f"  Mission ID: {Colors.BOLD}{mission.mission_id}{Colors.ENDC}")
            print(f"  Name: {mission.name}")
            print(f"  Type: {mission.mission_type.value}")
            print(f"  Required Roles: {', '.join(r.value for r in mission.required_roles)}")
            print(f"  Reward: ${mission.reward:,.2f}")

            # Check role availability
            validation = self.manager.mission_planning.validate_required_roles(mission.mission_id)
            if not validation["all_roles_available"]:
                self.print_warning(f"Missing roles: {', '.join(validation['missing_roles'])}")
            elif self.confirm("\nWould you like to assign crew now?"):
                self._assign_crew_to_mission(mission.mission_id)

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def create_repair_mission(self):
        """Create a repair mission for a damaged car."""
        self.print_subheader("Create Repair Mission")

        damaged_cars = self.manager.inventory.list_damaged_cars()

        if not damaged_cars:
            self.print_warning("No damaged cars to repair!")
            self.pause()
            return

        print("Damaged cars:")
        for c in damaged_cars:
            print(f"  - {c.car_id}: {c.year} {c.make} {c.model} (Damage: {c.damage_level}%)")
        print()

        car_id = self.get_input("Enter car ID to repair")

        try:
            mission = self.manager.mission_planning.create_repair_mission(car_id)
            self.print_success("Repair mission created!")
            print(f"  Mission ID: {mission.mission_id}")
            print(f"  Name: {mission.name}")
            print(f"  Required: Mechanic")
            print(f"  Reward: ${mission.reward:,.2f}")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def view_pending_missions(self):
        """View pending missions."""
        self.print_subheader("Pending Missions")

        missions = self.manager.mission_planning.list_pending_missions()

        if not missions:
            self.print_warning("No pending missions.")
        else:
            headers = ["Mission ID", "Name", "Type", "Reward", "Crew Assigned"]
            rows = []
            for m in missions:
                rows.append([
                    m.mission_id,
                    m.name[:20],
                    m.mission_type.value,
                    f"${m.reward:,.2f}",
                    "Yes" if m.assigned_crew else "No"
                ])
            self.print_table(headers, rows, [12, 22, 10, 12, 14])

        self.pause()

    def view_active_missions(self):
        """View active missions."""
        self.print_subheader("Active Missions")

        missions = self.manager.mission_planning.list_active_missions()

        if not missions:
            self.print_warning("No active missions.")
        else:
            headers = ["Mission ID", "Name", "Type", "Crew"]
            rows = []
            for m in missions:
                rows.append([
                    m.mission_id,
                    m.name[:20],
                    m.mission_type.value,
                    str(len(m.assigned_crew))
                ])
            self.print_table(headers, rows, [12, 22, 10, 10])

        self.pause()

    def view_all_missions(self):
        """View all missions."""
        self.print_subheader("All Missions")

        missions = self.manager.mission_planning.list_all_missions()

        if not missions:
            self.print_warning("No missions found.")
        else:
            headers = ["Mission ID", "Name", "Type", "Status", "Reward"]
            rows = []
            for m in missions:
                rows.append([
                    m.mission_id,
                    m.name[:18],
                    m.mission_type.value,
                    m.status.value,
                    f"${m.reward:,.2f}"
                ])
            self.print_table(headers, rows, [12, 20, 10, 12, 12])

        self.pause()

    def assign_crew_to_mission(self):
        """Assign crew to a mission."""
        self.print_subheader("Assign Crew to Mission")

        pending = self.manager.mission_planning.list_pending_missions()
        unassigned = [m for m in pending if not m.assigned_crew]

        if not unassigned:
            self.print_warning("No unassigned missions.")
            self.pause()
            return

        print("Unassigned missions:")
        for m in unassigned:
            required = ', '.join(r.value for r in m.required_roles)
            print(f"  - {m.mission_id}: {m.name} (Requires: {required})")
        print()

        mission_id = self.get_input("Enter mission ID")
        self._assign_crew_to_mission(mission_id)
        self.pause()

    def _assign_crew_to_mission(self, mission_id: str):
        """Helper to assign crew to a mission."""
        try:
            mission = self.manager.mission_planning.get_mission(mission_id)
            print(f"\nRequired roles: {', '.join(r.value for r in mission.required_roles)}")

            crew_ids = []
            for role in mission.required_roles:
                available = self.manager.crew_management.list_available_members_by_role(role.value)
                if available:
                    print(f"\nAvailable {role.value}s:")
                    for m in available:
                        print(f"  - {m.member_id}: {m.name} (Skill: {m.skill_level})")

                    member_id = self.get_input(f"Select {role.value} ID")
                    crew_ids.append(member_id)
                else:
                    self.print_error(f"No available {role.value}s!")
                    return

            self.manager.mission_planning.assign_mission(mission_id, crew_ids)
            self.print_success("Crew assigned successfully!")

        except StreetRaceError as e:
            self.print_error(str(e))

    def start_mission(self):
        """Start a mission."""
        self.print_subheader("Start Mission")

        pending = self.manager.mission_planning.list_pending_missions()
        ready = [m for m in pending if m.assigned_crew]

        if not ready:
            self.print_warning("No missions ready to start (need crew assigned).")
            self.pause()
            return

        print("Missions ready to start:")
        for m in ready:
            print(f"  - {m.mission_id}: {m.name} (Crew: {len(m.assigned_crew)})")
        print()

        mission_id = self.get_input("Enter mission ID to start")

        try:
            mission = self.manager.mission_planning.start_mission(mission_id)
            self.print_success(f"Mission '{mission.name}' has started!")
        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def complete_mission(self):
        """Complete a mission."""
        self.print_subheader("Complete Mission")

        active = self.manager.mission_planning.list_active_missions()

        if not active:
            self.print_warning("No active missions.")
            self.pause()
            return

        print("Active missions:")
        for m in active:
            print(f"  - {m.mission_id}: {m.name} ({m.mission_type.value})")
        print()

        mission_id = self.get_input("Enter mission ID to complete")

        success = self.confirm("Was the mission successful?")

        try:
            mission = self.manager.mission_planning.complete_mission(mission_id, success)

            if success:
                self.print_success(f"Mission '{mission.name}' completed successfully!")
                print(f"  Reward: ${mission.reward:,.2f}")
            else:
                self.print_warning(f"Mission '{mission.name}' failed.")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def check_role_availability(self):
        """Check crew role availability."""
        self.print_subheader("Role Availability")

        roles = ["driver", "mechanic", "strategist"]

        print("Current crew availability:\n")
        for role in roles:
            total = self.manager.crew_management.get_role_count(role)
            available = self.manager.crew_management.get_available_role_count(role)
            busy = total - available

            color = Colors.GREEN if available > 0 else Colors.RED
            print(f"  {role.capitalize():12} - Total: {total}, Available: {color}{available}{Colors.ENDC}, Busy: {busy}")

        self.pause()

    # =================== LEADERBOARD ===================

    def leaderboard_menu(self):
        """Leaderboard and statistics submenu."""
        while True:
            self.clear_screen()
            self.print_header("LEADERBOARD & STATISTICS")

            print(f"  {Colors.YELLOW}1.{Colors.ENDC} View Leaderboard")
            print(f"  {Colors.YELLOW}2.{Colors.ENDC} View Top Earners")
            print(f"  {Colors.YELLOW}3.{Colors.ENDC} View Most Wins")
            print(f"  {Colors.YELLOW}4.{Colors.ENDC} View Member Statistics")
            print(f"  {Colors.YELLOW}5.{Colors.ENDC} Compare Members")
            print(f"  {Colors.YELLOW}6.{Colors.ENDC} View Race History")
            print(f"  {Colors.YELLOW}7.{Colors.ENDC} Overall Statistics")
            print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back to Main Menu")
            print()

            choice = self.get_int_input("Select an option", 0, 7)

            if choice == 0:
                break
            elif choice == 1:
                self.view_leaderboard()
            elif choice == 2:
                self.view_top_earners()
            elif choice == 3:
                self.view_most_wins()
            elif choice == 4:
                self.view_member_statistics()
            elif choice == 5:
                self.compare_members()
            elif choice == 6:
                self.view_race_history()
            elif choice == 7:
                self.view_overall_statistics()

    def view_leaderboard(self):
        """View the leaderboard."""
        self.print_subheader("Leaderboard")

        print("Sort by:")
        options = ["Ranking Points", "Total Earnings", "Races Won", "Win Ratio"]
        choice = self.get_choice("Select sorting", options)

        sort_map = {1: "ranking_points", 2: "total_earnings", 3: "races_won", 4: "win_ratio"}
        sort_by = sort_map[choice]

        leaderboard = self.manager.leaderboard.get_leaderboard(sort_by=sort_by)

        if not leaderboard:
            self.print_warning("No rankings yet. Complete some races first!")
        else:
            headers = ["Rank", "Member", "Wins", "Races", "Win %", "Earnings", "Points"]
            rows = []
            for entry in leaderboard[:10]:
                member = self.manager.registration.get_member(entry["member_id"])
                rows.append([
                    f"#{entry['rank']}",
                    member.name[:15],
                    str(entry["races_won"]),
                    str(entry["races_participated"]),
                    f"{entry['win_ratio']:.0%}",
                    f"${entry['total_earnings']:,.0f}",
                    str(entry["ranking_points"])
                ])
            self.print_table(headers, rows, [6, 17, 6, 6, 8, 12, 8])

        self.pause()

    def view_top_earners(self):
        """View top earners."""
        self.print_subheader("Top Earners")

        top_earners = self.manager.results.get_top_earners(10)

        if not top_earners:
            self.print_warning("No earnings recorded yet.")
        else:
            print("Top 10 Earners:\n")
            for i, stats in enumerate(top_earners, 1):
                try:
                    member = self.manager.registration.get_member(stats.member_id)
                    print(f"  {i}. {member.name}: ${stats.total_earnings:,.2f}")
                except StreetRaceError:
                    pass

        self.pause()

    def view_most_wins(self):
        """View members with most wins."""
        self.print_subheader("Most Race Wins")

        top_winners = self.manager.results.get_top_winners(10)

        if not top_winners:
            self.print_warning("No race wins recorded yet.")
        else:
            print("Top 10 Winners:\n")
            for i, stats in enumerate(top_winners, 1):
                try:
                    member = self.manager.registration.get_member(stats.member_id)
                    print(f"  {i}. {member.name}: {stats.races_won} wins")
                except StreetRaceError:
                    pass

        self.pause()

    def view_member_statistics(self):
        """View detailed statistics for a member."""
        self.print_subheader("Member Statistics")

        self._show_all_members_brief()

        member_id = self.get_input("Enter member ID")

        try:
            stats = self.manager.leaderboard.get_member_stats(member_id)
            member = self.manager.registration.get_member(member_id)
            win_ratio = self.manager.leaderboard.calculate_win_ratio(member_id)
            rank = self.manager.leaderboard.get_member_rank(member_id)

            print(f"\n{Colors.BOLD}Statistics for {member.name}{Colors.ENDC}\n")
            print(f"  Races Participated: {stats.races_participated}")
            print(f"  Races Won:          {stats.races_won}")
            print(f"  Win Ratio:          {win_ratio:.1%}")
            print(f"  Total Earnings:     ${stats.total_earnings:,.2f}")
            print(f"  Ranking Points:     {stats.ranking_points}")
            print(f"  Current Rank:       #{rank or 'N/A'}")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def compare_members(self):
        """Compare two members."""
        self.print_subheader("Compare Members")

        self._show_all_members_brief()

        member1_id = self.get_input("Enter first member ID")
        member2_id = self.get_input("Enter second member ID")

        try:
            comparison = self.manager.leaderboard.compare_members(member1_id, member2_id)
            m1 = self.manager.registration.get_member(member1_id)
            m2 = self.manager.registration.get_member(member2_id)

            c1 = comparison["member_1"]
            c2 = comparison["member_2"]

            print(f"\n{Colors.BOLD}Comparison: {m1.name} vs {m2.name}{Colors.ENDC}\n")

            headers = ["Stat", m1.name[:15], m2.name[:15]]
            rows = [
                ["Races Won", str(c1["races_won"]), str(c2["races_won"])],
                ["Win Ratio", f"{c1['win_ratio']:.1%}", f"{c2['win_ratio']:.1%}"],
                ["Earnings", f"${c1['total_earnings']:,.0f}", f"${c2['total_earnings']:,.0f}"],
                ["Points", str(c1["ranking_points"]), str(c2["ranking_points"])]
            ]
            self.print_table(headers, rows, [12, 17, 17])

            print(f"\n{Colors.BOLD}Winner by Category:{Colors.ENDC}")
            for category, winner_id in comparison["comparison"].items():
                winner = m1.name if winner_id == member1_id else m2.name
                print(f"  {category.replace('_', ' ').title()}: {winner}")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def view_race_history(self):
        """View race history for a member."""
        self.print_subheader("Race History")

        self._show_all_members_brief()

        member_id = self.get_input("Enter member ID")

        try:
            history = self.manager.results.get_race_history(member_id)
            member = self.manager.registration.get_member(member_id)

            if not history:
                self.print_warning(f"No race history for {member.name}")
            else:
                print(f"\nRace history for {member.name}:\n")
                for result in history:
                    # Find this member's position
                    for pos, driver_id in result.positions.items():
                        if driver_id == member_id:
                            prize = result.prize_distribution.get(member_id, 0)
                            print(f"  Race {result.race_id}: Position #{pos}, Prize: ${prize:,.2f}")
                            break

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def view_overall_statistics(self):
        """View overall system statistics."""
        self.print_subheader("Overall Statistics")

        summary = self.manager.leaderboard.get_statistics_summary()

        print(f"  {Colors.BOLD}Racing Statistics{Colors.ENDC}")
        print(f"    Total Racers:         {summary['total_racers']}")
        print(f"    Total Races:          {summary['total_races_completed']}")
        print(f"    Prize Distributed:    ${summary['total_prize_distributed']:,.2f}")
        print(f"    Average Earnings:     ${summary['average_earnings']:,.2f}")

        if summary["top_earner"]:
            try:
                top = self.manager.registration.get_member(summary["top_earner"]["member_id"])
                print(f"\n    Top Earner: {top.name} (${summary['top_earner']['earnings']:,.2f})")
            except StreetRaceError:
                pass

        if summary["most_wins"]:
            try:
                winner = self.manager.registration.get_member(summary["most_wins"]["member_id"])
                print(f"    Most Wins:  {winner.name} ({summary['most_wins']['wins']} wins)")
            except StreetRaceError:
                pass

        self.pause()

    # =================== NOTIFICATIONS ===================

    def notification_menu(self):
        """Notifications submenu."""
        while True:
            self.clear_screen()
            self.print_header("NOTIFICATIONS")

            all_notifs = self.manager.notification.get_all_notifications()
            print(f"  Total Notifications: {len(all_notifs)}\n")

            print(f"  {Colors.YELLOW}1.{Colors.ENDC} View All Notifications")
            print(f"  {Colors.YELLOW}2.{Colors.ENDC} View Notifications by Member")
            print(f"  {Colors.YELLOW}3.{Colors.ENDC} Mark Notifications as Read")
            print(f"  {Colors.YELLOW}4.{Colors.ENDC} Clear Notifications")
            print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back to Main Menu")
            print()

            choice = self.get_int_input("Select an option", 0, 4)

            if choice == 0:
                break
            elif choice == 1:
                self.view_all_notifications()
            elif choice == 2:
                self.view_member_notifications()
            elif choice == 3:
                self.mark_notifications_read()
            elif choice == 4:
                self.clear_notifications()

    def view_all_notifications(self):
        """View all notifications."""
        self.print_subheader("All Notifications")

        notifications = self.manager.notification.get_all_notifications()

        if not notifications:
            self.print_warning("No notifications.")
        else:
            for n in notifications[-20:]:  # Show last 20
                status = "" if n.is_read else f"{Colors.YELLOW}[NEW]{Colors.ENDC} "
                print(f"  {status}{n.notification_type.value}: {n.message}")
                print(f"    To: {n.recipient_id} | {n.created_at.strftime('%Y-%m-%d %H:%M')}")
                print()

        self.pause()

    def view_member_notifications(self):
        """View notifications for a specific member."""
        self.print_subheader("Member Notifications")

        self._show_all_members_brief()

        member_id = self.get_input("Enter member ID")

        notifications = self.manager.notification.get_notifications(member_id)
        counts = self.manager.notification.get_notification_count(member_id)

        print(f"\nNotifications for {member_id}:")
        print(f"  Total: {counts['total']}, Unread: {counts['unread']}\n")

        if not notifications:
            self.print_warning("No notifications for this member.")
        else:
            for n in notifications:
                status = "" if n.is_read else f"{Colors.YELLOW}[NEW]{Colors.ENDC} "
                print(f"  {status}{n.message}")

        self.pause()

    def mark_notifications_read(self):
        """Mark notifications as read."""
        self.print_subheader("Mark as Read")

        self._show_all_members_brief()

        member_id = self.get_input("Enter member ID")

        count = self.manager.notification.mark_all_as_read(member_id)
        self.print_success(f"Marked {count} notifications as read")

        self.pause()

    def clear_notifications(self):
        """Clear notifications for a member."""
        self.print_subheader("Clear Notifications")

        self._show_all_members_brief()

        member_id = self.get_input("Enter member ID")

        if self.confirm(f"Clear all notifications for {member_id}?"):
            count = self.manager.notification.clear_notifications(member_id)
            self.print_success(f"Cleared {count} notifications")
        else:
            self.print_info("Operation cancelled")

        self.pause()

    # =================== SYSTEM STATUS ===================

    def show_system_status(self):
        """Show overall system status."""
        self.clear_screen()
        self.print_header("SYSTEM STATUS")

        status = self.manager.get_system_status()

        print(f"{Colors.BOLD}Registration{Colors.ENDC}")
        print(f"  Total Members:  {status['registration']['total_members']}")
        print(f"  Active Members: {status['registration']['active_members']}")

        print(f"\n{Colors.BOLD}Crew Roles{Colors.ENDC}")
        print(f"  Drivers:     {status['crew']['drivers']}")
        print(f"  Mechanics:   {status['crew']['mechanics']}")
        print(f"  Strategists: {status['crew']['strategists']}")

        print(f"\n{Colors.BOLD}Inventory{Colors.ENDC}")
        inv = status['inventory']
        print(f"  Cars:        {inv['total_cars']} ({inv['available_cars']} available)")
        print(f"  Cash:        ${inv['cash_balance']:,.2f}")
        if inv['is_low_on_cash']:
            self.print_warning("Low cash warning!")

        print(f"\n{Colors.BOLD}Races{Colors.ENDC}")
        print(f"  Scheduled:   {status['races']['scheduled']}")
        print(f"  In Progress: {status['races']['in_progress']}")
        print(f"  Completed:   {status['races']['completed']}")

        print(f"\n{Colors.BOLD}Missions{Colors.ENDC}")
        print(f"  Pending:     {status['missions']['pending']}")
        print(f"  Active:      {status['missions']['active']}")

        self.pause()

    # =================== QUICK ACTIONS ===================

    def quick_actions_menu(self):
        """Quick actions submenu."""
        while True:
            self.clear_screen()
            self.print_header("QUICK ACTIONS")

            print(f"  {Colors.YELLOW}1.{Colors.ENDC} Quick Setup (Add Demo Data)")
            print(f"  {Colors.YELLOW}2.{Colors.ENDC} Register Driver with Car")
            print(f"  {Colors.YELLOW}3.{Colors.ENDC} Run Quick Race")
            print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back to Main Menu")
            print()

            choice = self.get_int_input("Select an option", 0, 3)

            if choice == 0:
                break
            elif choice == 1:
                self.quick_setup()
            elif choice == 2:
                self.quick_register_driver_with_car()
            elif choice == 3:
                self.quick_race()

    def quick_setup(self):
        """Set up demo data quickly."""
        self.print_subheader("Quick Setup")

        if self.confirm("This will add demo crew members, cars, and parts. Continue?"):
            try:
                # Add drivers
                d1 = self.manager.register_and_assign_driver("Speed Racer", 8)
                d2 = self.manager.register_and_assign_driver("Fast Freddy", 7)
                d3 = self.manager.register_and_assign_driver("Quick Quinn", 6)

                # Add mechanics
                m1 = self.manager.register_and_assign_mechanic("Wrench Wilson", 8)
                m2 = self.manager.register_and_assign_mechanic("Fix-It Felix", 7)

                # Add strategist
                s1 = self.manager.register_and_assign_strategist("Plan Master", 9)

                # Add cars
                self.manager.inventory.add_car("Toyota", "Supra MK4", 1998, performance_rating=8)
                self.manager.inventory.add_car("Nissan", "GT-R R35", 2020, performance_rating=9)
                self.manager.inventory.add_car("Honda", "NSX", 2019, performance_rating=7)
                self.manager.inventory.add_car("Mazda", "RX-7 FD", 1995, performance_rating=7)

                # Add parts
                self.manager.inventory.add_spare_parts("engine_parts", 10, 50.0)
                self.manager.inventory.add_spare_parts("tires", 20, 100.0)
                self.manager.inventory.add_spare_parts("brake_pads", 15, 30.0)
                self.manager.inventory.add_spare_parts("oil_filter", 25, 15.0)

                # Add tools
                self.manager.inventory.add_tools("wrench_set", 5)
                self.manager.inventory.add_tools("jack", 3)
                self.manager.inventory.add_tools("diagnostic_scanner", 2)

                self.print_success("Demo data added successfully!")
                print(f"  - 3 Drivers")
                print(f"  - 2 Mechanics")
                print(f"  - 1 Strategist")
                print(f"  - 4 Cars")
                print(f"  - Various spare parts and tools")

            except StreetRaceError as e:
                self.print_error(str(e))

        self.pause()

    def quick_register_driver_with_car(self):
        """Quickly register a driver and add a car."""
        self.print_subheader("Quick Driver + Car Setup")

        name = self.get_input("Enter driver name")
        skill = self.get_int_input("Enter skill level (1-10)", 1, 10)

        print("\nCar details:")
        make = self.get_input("Enter car make")
        model = self.get_input("Enter car model")
        year = self.get_int_input("Enter year", 1990, 2030)

        try:
            driver = self.manager.register_and_assign_driver(name, skill)
            car = self.manager.inventory.add_car(make, model, year)

            self.print_success("Driver and car registered!")
            print(f"  Driver: {driver.name} (ID: {driver.member_id})")
            print(f"  Car: {car.year} {car.make} {car.model} (ID: {car.car_id})")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()

    def quick_race(self):
        """Quickly set up and run a race."""
        self.print_subheader("Quick Race")

        drivers = self.manager.crew_management.list_available_members_by_role("driver")
        cars = self.manager.inventory.list_available_cars()

        if len(drivers) < 2:
            self.print_error("Need at least 2 available drivers!")
            self.pause()
            return

        if len(cars) < 2:
            self.print_error("Need at least 2 available cars!")
            self.pause()
            return

        print(f"Available: {len(drivers)} drivers, {len(cars)} cars")

        if not self.confirm("Set up a quick 2-driver race?"):
            self.pause()
            return

        try:
            # Create race
            race = self.manager.race_management.create_race(
                "Quick Race", "street", 1000.0
            )

            # Add first 2 drivers with first 2 cars
            self.manager.race_management.add_participant(
                race.race_id, drivers[0].member_id, cars[0].car_id
            )
            self.manager.race_management.add_participant(
                race.race_id, drivers[1].member_id, cars[1].car_id
            )

            print(f"\nRace: {race.name}")
            print(f"  {drivers[0].name} vs {drivers[1].name}")

            # Start race
            self.manager.race_management.start_race(race.race_id)
            self.print_success("Race started!")

            # Get winner
            print("\nWho won?")
            options = [drivers[0].name, drivers[1].name]
            winner_choice = self.get_choice("Select winner", options)

            if winner_choice == 1:
                positions = {1: drivers[0].member_id, 2: drivers[1].member_id}
            else:
                positions = {1: drivers[1].member_id, 2: drivers[0].member_id}

            # Complete race
            self.manager.race_management.complete_race(race.race_id, positions)

            # Get result
            result = self.manager.results.get_race_result(race.race_id)
            winner = self.manager.registration.get_member(positions[1])

            self.print_success(f"Race completed! Winner: {winner.name}")
            print(f"  1st place prize: ${result.prize_distribution[positions[1]]:,.2f}")

        except StreetRaceError as e:
            self.print_error(str(e))

        self.pause()


def main():
    """Main entry point for the CLI."""
    cli = CLI()

    try:
        cli.main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted. Goodbye!{Colors.ENDC}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
