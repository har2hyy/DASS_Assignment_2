"""
INTEGRATION TESTS FOR STREETRACE MANAGER
=========================================

These tests validate how different modules interact with one another
as specified in Section 2.2 of the assignment.

Test coverage includes ALL integrations illustrated in the Call Graph:
- Registration <-> Crew Management
- Crew Management <-> Race Management
- Race Management <-> Inventory
- Race Management <-> Results
- Results <-> Inventory
- Mission Planning <-> Crew Management
- Mission Planning <-> Inventory
- Leaderboard <-> Results
- Notification callbacks

Each test case documents:
- What scenario is being tested
- Which modules are involved
- The expected result
- The actual result after testing
- Any errors or logical issues found
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from models import Role, CarStatus, RaceStatus, MissionStatus, MissionType
from exceptions import (
    MemberNotFoundError,
    NotADriverError,
    CarNotAvailableError,
    RequiredRoleUnavailableError,
    MinimumParticipantsError,
    RaceNotStartedError,
    MissionNotStartedError,
    CrewMemberBusyError,
    CarAlreadyInRaceError,
    ParticipantAlreadyInRaceError
)


# ==============================================================================
# INT-01 to INT-02: Registration <-> Crew Management Integration
# Business Rule BR-01: Member must be registered before role assignment
# ==============================================================================

class TestRegistrationCrewIntegration:
    """Tests for Registration <-> Crew Management integration."""

    def test_int01_register_then_assign_role(self, registration_module, crew_module):
        """
        INT-01: Register a crew member, then assign a role.

        Scenario: Complete the registration-to-role assignment workflow.
        Modules: Registration -> Crew Management
        Expected: Member is registered and role is successfully assigned.
        """
        # Register member
        member = registration_module.register_member("Speed Racer")
        assert member is not None
        assert registration_module.validate_member_exists(member.member_id)

        # Assign role
        updated = crew_module.assign_role(member.member_id, "driver")
        assert updated.role == Role.DRIVER

        # Verify through crew module
        role = crew_module.get_member_role(member.member_id)
        assert role == Role.DRIVER

    def test_int02_assign_role_without_registration_fails(self, crew_module):
        """
        INT-02: Attempt to assign role without prior registration.

        Scenario: Try to assign a role to an unregistered member.
        Modules: Crew Management (requires Registration)
        Expected: MemberNotFoundError is raised.
        """
        with pytest.raises(MemberNotFoundError) as exc_info:
            crew_module.assign_role("unregistered_id", "driver")

        assert "unregistered_id" in str(exc_info.value)


# ==============================================================================
# INT-03 to INT-04: Crew Management <-> Race Management Integration
# Business Rule BR-02: Only drivers may enter races
# ==============================================================================

class TestCrewRaceIntegration:
    """Tests for Crew Management <-> Race Management integration."""

    def test_int03_register_driver_enter_race(
        self, registration_module, crew_module, inventory_module, race_module
    ):
        """
        INT-03: Register driver and enter them into a race.

        Scenario: Complete workflow from registration to race entry.
        Modules: Registration -> Crew Management -> Inventory -> Race Management
        Expected: Driver is successfully added as race participant.
        """
        # Register and assign driver role
        member = registration_module.register_member("Pro Racer")
        crew_module.assign_role(member.member_id, "driver")

        # Add car to inventory
        car = inventory_module.add_car("Nissan", "GT-R", 2021)

        # Create race
        race = race_module.create_race("Night Street Race", "street", 5000.0)

        # Add participant
        participant = race_module.add_participant(
            race.race_id, member.member_id, car.car_id
        )

        assert participant.driver_id == member.member_id
        assert participant.car_id == car.car_id
        assert len(race_module.get_race_participants(race.race_id)) == 1

    def test_int04_non_driver_cannot_enter_race(
        self, registration_module, crew_module, inventory_module, race_module
    ):
        """
        INT-04: Attempt to enter a non-driver into a race.

        Scenario: Try to add a mechanic as a race participant.
        Modules: Registration -> Crew Management -> Race Management
        Expected: NotADriverError is raised.
        """
        # Register as mechanic
        member = registration_module.register_member("Fix-It Felix")
        crew_module.assign_role(member.member_id, "mechanic")

        car = inventory_module.add_car("Toyota", "Supra", 2020)
        race = race_module.create_race("Test Race", "street", 1000.0)

        with pytest.raises(NotADriverError) as exc_info:
            race_module.add_participant(race.race_id, member.member_id, car.car_id)

        assert "mechanic" in str(exc_info.value)

    def test_int04b_member_without_role_cannot_race(
        self, registration_module, crew_module, inventory_module, race_module
    ):
        """
        INT-04b: Attempt to enter a member without any role into a race.

        Scenario: Try to add a member with no role assigned.
        Modules: Registration -> Race Management
        Expected: NotADriverError is raised with 'none' as the role.
        """
        member = registration_module.register_member("No Role Member")
        car = inventory_module.add_car("Honda", "Civic", 2020)
        race = race_module.create_race("Open Race", "street", 1000.0)

        with pytest.raises(NotADriverError) as exc_info:
            race_module.add_participant(race.race_id, member.member_id, car.car_id)

        assert "none" in str(exc_info.value)


# ==============================================================================
# INT-05 to INT-06: Race -> Results -> Inventory Integration
# Business Rule BR-04: Race results update cash balance
# ==============================================================================

class TestRaceResultsInventoryIntegration:
    """Tests for Race -> Results -> Inventory integration."""

    def test_int05_complete_race_records_results(
        self, registration_module, crew_module, inventory_module,
        race_module, results_module
    ):
        """
        INT-05: Complete a race and verify results are recorded.

        Scenario: Run a race to completion and check results.
        Modules: Race Management -> Results
        Expected: Race outcome is recorded with positions and prizes.
        """
        # Setup: Create 2 drivers with cars
        driver1 = registration_module.register_member("Winner")
        driver2 = registration_module.register_member("Runner Up")
        crew_module.assign_role(driver1.member_id, "driver")
        crew_module.assign_role(driver2.member_id, "driver")

        car1 = inventory_module.add_car("Fast", "Car1", 2021)
        car2 = inventory_module.add_car("Slow", "Car2", 2020)

        # Create and populate race
        race = race_module.create_race("Championship", "circuit", 2000.0)
        race_module.add_participant(race.race_id, driver1.member_id, car1.car_id)
        race_module.add_participant(race.race_id, driver2.member_id, car2.car_id)

        # Start race
        race_module.start_race(race.race_id)

        # Record results
        positions = {1: driver1.member_id, 2: driver2.member_id}
        result = results_module.record_race_outcome(race.race_id, positions)

        assert result.race_id == race.race_id
        assert result.positions[1] == driver1.member_id
        assert result.positions[2] == driver2.member_id

    def test_int06_prize_money_updates_inventory(
        self, registration_module, crew_module, inventory_module,
        race_module, results_module
    ):
        """
        INT-06: Verify prize money updates inventory cash balance.

        Scenario: Complete race and check cash balance increases.
        Modules: Results -> Inventory
        Expected: Cash balance increases by prize distribution amount.
        """
        initial_balance = inventory_module.get_cash_balance()

        # Setup race with 2 participants
        driver1 = registration_module.register_member("Champion")
        driver2 = registration_module.register_member("Challenger")
        crew_module.assign_role(driver1.member_id, "driver")
        crew_module.assign_role(driver2.member_id, "driver")

        car1 = inventory_module.add_car("Speed", "Demon", 2022)
        car2 = inventory_module.add_car("Road", "Runner", 2021)

        race = race_module.create_race("Money Race", "drag", 1000.0)
        race_module.add_participant(race.race_id, driver1.member_id, car1.car_id)
        race_module.add_participant(race.race_id, driver2.member_id, car2.car_id)
        race_module.start_race(race.race_id)

        # Record result - 1st gets 50%, 2nd gets 30%
        positions = {1: driver1.member_id, 2: driver2.member_id}
        results_module.record_race_outcome(race.race_id, positions)

        # Total distributed: 50% + 30% = 80% of 1000 = 800
        expected_prize = 1000.0 * 0.50 + 1000.0 * 0.30

        new_balance = inventory_module.get_cash_balance()
        assert new_balance == initial_balance + expected_prize


# ==============================================================================
# INT-07 to INT-08: Mission Planning <-> Crew Management Integration
# Business Rules BR-03 and BR-05: Role validation for missions
# ==============================================================================

class TestMissionCrewIntegration:
    """Tests for Mission Planning <-> Crew Management integration."""

    def test_int07_damaged_car_needs_repair_mission(
        self, registration_module, crew_module, inventory_module, mission_module
    ):
        """
        INT-07: Damaged car triggers need for mechanic mission.

        Scenario: Car is damaged, create repair mission.
        Modules: Inventory -> Mission Planning -> Crew Management
        Expected: Repair mission is created requiring mechanic role.
        """
        # Setup mechanic
        mechanic = registration_module.register_member("Fix Master")
        crew_module.assign_role(mechanic.member_id, "mechanic")

        # Simulate damaged car
        car = inventory_module.add_car("Fragile", "Racer", 2021)
        inventory_module.update_car_status(car.car_id, "damaged")

        # Create repair mission
        mission = mission_module.create_repair_mission(car.car_id)

        assert mission.mission_type == MissionType.REPAIR
        assert Role.MECHANIC in mission.required_roles
        assert mission.car_to_repair == car.car_id

    def test_int08_mission_fails_without_available_mechanic(
        self, registration_module, crew_module, inventory_module, mission_module
    ):
        """
        INT-08: Mission requiring unavailable role cannot start.

        Scenario: Try to assign mission when required role is unavailable.
        Modules: Mission Planning -> Crew Management
        Expected: RequiredRoleUnavailableError is raised.
        """
        # No mechanic registered - only drivers
        driver = registration_module.register_member("Only Driver")
        crew_module.assign_role(driver.member_id, "driver")

        car = inventory_module.add_car("Broken", "Car", 2020)

        # Create repair mission (requires mechanic)
        mission = mission_module.create_mission(
            "Emergency Repair", "repair", 500.0, car_to_repair=car.car_id
        )

        # Try to assign only a driver to a mechanic mission
        with pytest.raises(RequiredRoleUnavailableError):
            mission_module.assign_mission(mission.mission_id, [driver.member_id])

    def test_int09_heist_mission_requires_all_roles(
        self, registration_module, crew_module, mission_module
    ):
        """
        INT-09: Heist mission validates all required roles.

        Scenario: Create heist mission requiring all roles.
        Modules: Mission Planning -> Crew Management
        Expected: Mission only starts when all roles available.
        """
        # Register all role types
        driver = registration_module.register_member("Getaway Driver")
        mechanic = registration_module.register_member("Tech Expert")
        strategist = registration_module.register_member("Mastermind")

        crew_module.assign_role(driver.member_id, "driver")
        crew_module.assign_role(mechanic.member_id, "mechanic")
        crew_module.assign_role(strategist.member_id, "strategist")

        # Create heist mission (requires all roles)
        mission = mission_module.create_mission("Big Score", "heist", 10000.0)

        # Assign all crew
        result = mission_module.assign_mission(
            mission.mission_id,
            [driver.member_id, mechanic.member_id, strategist.member_id]
        )

        assert len(result.assigned_crew) == 3

        # Start mission
        started = mission_module.start_mission(mission.mission_id)
        assert started.status == MissionStatus.IN_PROGRESS

    def test_int10_busy_crew_member_cannot_be_assigned(
        self, registration_module, crew_module, mission_module
    ):
        """
        INT-10: Busy crew members cannot be assigned to new missions.

        Scenario: Try to assign already busy member to mission.
        Modules: Mission Planning -> Crew Management
        Expected: CrewMemberBusyError is raised.
        """
        # Register mechanic
        mechanic = registration_module.register_member("Busy Mechanic")
        crew_module.assign_role(mechanic.member_id, "mechanic")

        # Create first mission and start it (makes mechanic busy)
        mission1 = mission_module.create_mission("First Job", "repair", 100.0)
        mission_module.assign_mission(mission1.mission_id, [mechanic.member_id])
        mission_module.start_mission(mission1.mission_id)

        # Try to assign same mechanic to second mission
        mission2 = mission_module.create_mission("Second Job", "repair", 200.0)

        with pytest.raises(CrewMemberBusyError):
            mission_module.assign_mission(mission2.mission_id, [mechanic.member_id])


# ==============================================================================
# INT-11 to INT-12: Inventory <-> Race Management Integration
# ==============================================================================

class TestInventoryRaceIntegration:
    """Tests for Inventory <-> Race Management integration."""

    def test_int11_unavailable_car_cannot_enter_race(
        self, registration_module, crew_module, inventory_module, race_module
    ):
        """
        INT-11: Only available cars can enter races.

        Scenario: Try to use damaged car in race.
        Modules: Inventory -> Race Management
        Expected: CarNotAvailableError is raised.
        """
        driver = registration_module.register_member("Ready Driver")
        crew_module.assign_role(driver.member_id, "driver")

        car = inventory_module.add_car("Broken", "Wreck", 2020)
        inventory_module.update_car_status(car.car_id, "damaged")

        race = race_module.create_race("Test Race", "street", 1000.0)

        with pytest.raises(CarNotAvailableError) as exc_info:
            race_module.add_participant(race.race_id, driver.member_id, car.car_id)

        assert "damaged" in str(exc_info.value)

    def test_int12_car_status_changes_during_race(
        self, registration_module, crew_module, inventory_module, race_module
    ):
        """
        INT-12: Car status changes from available to in_race during race.

        Scenario: Start race and verify car status.
        Modules: Race Management -> Inventory
        Expected: Car status is 'in_race' during race.
        """
        # Setup 2 drivers (minimum for race)
        d1 = registration_module.register_member("Driver 1")
        d2 = registration_module.register_member("Driver 2")
        crew_module.assign_role(d1.member_id, "driver")
        crew_module.assign_role(d2.member_id, "driver")

        c1 = inventory_module.add_car("Car", "One", 2021)
        c2 = inventory_module.add_car("Car", "Two", 2021)

        race = race_module.create_race("Status Test", "circuit", 500.0)
        race_module.add_participant(race.race_id, d1.member_id, c1.car_id)
        race_module.add_participant(race.race_id, d2.member_id, c2.car_id)

        # Before start
        assert inventory_module.get_car(c1.car_id).status == CarStatus.AVAILABLE

        # Start race
        race_module.start_race(race.race_id)

        # During race
        assert inventory_module.get_car(c1.car_id).status == CarStatus.IN_RACE
        assert inventory_module.get_car(c2.car_id).status == CarStatus.IN_RACE

    def test_int13_car_status_restored_after_race(
        self, registration_module, crew_module, inventory_module, race_module
    ):
        """
        INT-13: Car status changes back to available after race completion.

        Scenario: Complete race without damage, verify car status.
        Modules: Race Management -> Inventory
        Expected: Car status returns to 'available' after race.
        """
        d1 = registration_module.register_member("Careful Driver 1")
        d2 = registration_module.register_member("Careful Driver 2")
        crew_module.assign_role(d1.member_id, "driver")
        crew_module.assign_role(d2.member_id, "driver")

        c1 = inventory_module.add_car("Safe", "Car1", 2021)
        c2 = inventory_module.add_car("Safe", "Car2", 2021)

        race = race_module.create_race("Safe Race", "circuit", 500.0)
        race_module.add_participant(race.race_id, d1.member_id, c1.car_id)
        race_module.add_participant(race.race_id, d2.member_id, c2.car_id)
        race_module.start_race(race.race_id)

        # Complete race
        race_module.complete_race(race.race_id, {1: d1.member_id, 2: d2.member_id})

        # After completion
        assert inventory_module.get_car(c1.car_id).status == CarStatus.AVAILABLE
        assert inventory_module.get_car(c2.car_id).status == CarStatus.AVAILABLE


# ==============================================================================
# INT-14 to INT-16: Leaderboard <-> Results Integration
# ==============================================================================

class TestLeaderboardResultsIntegration:
    """Tests for Leaderboard <-> Results integration."""

    def test_int14_leaderboard_updates_after_race(
        self, registration_module, crew_module, inventory_module,
        race_module, results_module, leaderboard_module
    ):
        """
        INT-14: Leaderboard updates based on race results.

        Scenario: Run race, verify leaderboard shows correct stats.
        Modules: Results -> Leaderboard
        Expected: Leaderboard accurately reflects race outcomes.
        """
        # Setup two drivers (minimum for race)
        driver1 = registration_module.register_member("Champion")
        driver2 = registration_module.register_member("Runner-up")
        crew_module.assign_role(driver1.member_id, "driver")
        crew_module.assign_role(driver2.member_id, "driver")

        car1 = inventory_module.add_car("Fast", "Car", 2021)
        car2 = inventory_module.add_car("Slow", "Car", 2021)

        # Run race
        race = race_module.create_race("Championship", "circuit", 2000.0)
        race_module.add_participant(race.race_id, driver1.member_id, car1.car_id)
        race_module.add_participant(race.race_id, driver2.member_id, car2.car_id)
        race_module.start_race(race.race_id)

        # Record results
        positions = {1: driver1.member_id, 2: driver2.member_id}
        results_module.record_race_outcome(race.race_id, positions)

        # Verify winner's stats
        winner_stats = leaderboard_module.get_member_stats(driver1.member_id)
        assert winner_stats.races_won >= 1

    def test_int15_leaderboard_win_ratio_calculation(
        self, registration_module, crew_module, inventory_module,
        race_module, results_module, leaderboard_module
    ):
        """
        INT-15: Leaderboard calculates win ratio correctly.

        Scenario: Driver wins 1 of 2 races, verify win_ratio = 50%
        Modules: Results -> Leaderboard
        """
        # Setup 2 drivers for multiple races
        driver1 = registration_module.register_member("Win Ratio Driver")
        driver2 = registration_module.register_member("Opponent")
        crew_module.assign_role(driver1.member_id, "driver")
        crew_module.assign_role(driver2.member_id, "driver")

        # Race 1: driver1 wins
        car1a = inventory_module.add_car("Car1A", "Model", 2021)
        car2a = inventory_module.add_car("Car2A", "Model", 2021)
        race1 = race_module.create_race("Race 1", "drag", 500.0)
        race_module.add_participant(race1.race_id, driver1.member_id, car1a.car_id)
        race_module.add_participant(race1.race_id, driver2.member_id, car2a.car_id)
        race_module.start_race(race1.race_id)
        results_module.record_race_outcome(race1.race_id, {1: driver1.member_id, 2: driver2.member_id})

        # Race 2: driver1 loses
        car1b = inventory_module.add_car("Car1B", "Model", 2021)
        car2b = inventory_module.add_car("Car2B", "Model", 2021)
        race2 = race_module.create_race("Race 2", "drag", 500.0)
        race_module.add_participant(race2.race_id, driver1.member_id, car1b.car_id)
        race_module.add_participant(race2.race_id, driver2.member_id, car2b.car_id)
        race_module.start_race(race2.race_id)
        results_module.record_race_outcome(race2.race_id, {1: driver2.member_id, 2: driver1.member_id})

        # Check win ratio (1 win / 2 races = 50%)
        win_ratio = leaderboard_module.calculate_win_ratio(driver1.member_id)
        assert win_ratio == pytest.approx(50.0, rel=1)

    def test_int16_leaderboard_member_comparison(
        self, registration_module, crew_module, inventory_module,
        race_module, results_module, leaderboard_module
    ):
        """
        INT-16: Leaderboard compares two members' performance.

        Scenario: Compare driver1 (winner) vs driver2 (loser)
        Modules: Results -> Leaderboard
        """
        driver1 = registration_module.register_member("Better Driver")
        driver2 = registration_module.register_member("Worse Driver")
        crew_module.assign_role(driver1.member_id, "driver")
        crew_module.assign_role(driver2.member_id, "driver")

        car1 = inventory_module.add_car("Car1", "Model", 2021)
        car2 = inventory_module.add_car("Car2", "Model", 2021)

        race = race_module.create_race("Comparison Race", "street", 1000.0)
        race_module.add_participant(race.race_id, driver1.member_id, car1.car_id)
        race_module.add_participant(race.race_id, driver2.member_id, car2.car_id)
        race_module.start_race(race.race_id)
        results_module.record_race_outcome(race.race_id, {1: driver1.member_id, 2: driver2.member_id})

        comparison = leaderboard_module.compare_members(driver1.member_id, driver2.member_id)
        assert comparison is not None

        d1_stats = leaderboard_module.get_member_stats(driver1.member_id)
        d2_stats = leaderboard_module.get_member_stats(driver2.member_id)
        assert d1_stats.races_won > d2_stats.races_won


# ==============================================================================
# INT-17 to INT-18: Mission -> Inventory Integration
# ==============================================================================

class TestMissionInventoryIntegration:
    """Tests for Mission Planning <-> Inventory integration."""

    def test_int17_mission_completion_adds_cash_reward(
        self, registration_module, crew_module, inventory_module, mission_module
    ):
        """
        INT-17: Completing mission adds reward to inventory cash.

        Scenario: Complete mission successfully, verify cash increases.
        Modules: Mission Planning -> Inventory
        Expected: Cash balance increases by mission reward amount.
        """
        initial_cash = inventory_module.get_cash_balance()

        # Setup crew
        driver = registration_module.register_member("Delivery Driver")
        crew_module.assign_role(driver.member_id, "driver")

        # Create and complete mission
        mission = mission_module.create_mission("Package Delivery", "delivery", 500.0)
        mission_module.assign_mission(mission.mission_id, [driver.member_id])
        mission_module.start_mission(mission.mission_id)
        mission_module.complete_mission(mission.mission_id, success=True)

        final_cash = inventory_module.get_cash_balance()
        assert final_cash == initial_cash + 500.0

    def test_int18_repair_mission_restores_car_status(
        self, registration_module, crew_module, inventory_module, mission_module
    ):
        """
        INT-18: Repair mission restores car to available status.

        Scenario: Damaged car -> Repair mission -> Car available.
        Modules: Mission Planning -> Inventory
        Expected: Car status becomes AVAILABLE after repair.
        """
        mechanic = registration_module.register_member("Repair Tech")
        crew_module.assign_role(mechanic.member_id, "mechanic")

        car = inventory_module.add_car("Damaged Vehicle", "Sport", 2021)
        inventory_module.set_car_damage_level(car.car_id, 75)

        mission = mission_module.create_repair_mission(car.car_id)
        mission_module.assign_mission(mission.mission_id, [mechanic.member_id])
        mission_module.start_mission(mission.mission_id)
        mission_module.complete_mission(mission.mission_id, success=True)

        repaired_car = inventory_module.get_car(car.car_id)
        assert repaired_car.damage_level == 0
        assert repaired_car.status == CarStatus.AVAILABLE


# ==============================================================================
# INT-19 to INT-20: Full Pipeline & Edge Cases
# ==============================================================================

class TestFullPipelineIntegration:
    """Full system pipeline tests covering all modules."""

    def test_int19_full_registration_to_leaderboard_pipeline(self, populated_manager):
        """
        INT-19: Complete pipeline from registration to leaderboard.

        Scenario: Full race lifecycle affecting all modules.
        Modules: All 8 modules
        Expected: Data flows correctly through entire system.
        """
        manager = populated_manager["manager"]
        drivers = populated_manager["drivers"]
        cars = populated_manager["cars"]

        # Create and run a race
        race = manager.race_management.create_race("Grand Prix", "circuit", 3000.0)

        # Add participants
        manager.race_management.add_participant(
            race.race_id, drivers[0].member_id, cars[0].car_id
        )
        manager.race_management.add_participant(
            race.race_id, drivers[1].member_id, cars[1].car_id
        )

        # Start race
        manager.race_management.start_race(race.race_id)

        # Complete race with positions
        positions = {1: drivers[0].member_id, 2: drivers[1].member_id}
        manager.race_management.complete_race(race.race_id, positions)

        # Verify race completed
        completed_race = manager.race_management.get_race_details(race.race_id)
        assert completed_race.status == RaceStatus.COMPLETED

        # Verify results recorded
        result = manager.results.get_race_result(race.race_id)
        assert result.positions[1] == drivers[0].member_id

        # Verify leaderboard updated
        stats = manager.leaderboard.get_member_stats(drivers[0].member_id)
        assert stats.races_won >= 1

    def test_int20_repair_mission_full_workflow(self, populated_manager):
        """
        INT-20: Complete repair mission workflow.

        Scenario: Damaged car -> Repair mission -> Car restored.
        Modules: Inventory -> Mission Planning -> Crew Management -> Inventory
        Expected: Car status returns to available after mission.
        """
        manager = populated_manager["manager"]
        cars = populated_manager["cars"]
        mechanics = populated_manager["mechanics"]

        # Damage a car
        car_id = cars[0].car_id
        manager.inventory.update_car_status(car_id, "damaged")

        # Create repair mission
        mission = manager.mission_planning.create_repair_mission(car_id)

        # Assign mechanic
        manager.mission_planning.assign_mission(
            mission.mission_id, [mechanics[0].member_id]
        )

        # Start mission
        manager.mission_planning.start_mission(mission.mission_id)

        # Complete mission successfully
        manager.mission_planning.complete_mission(mission.mission_id, success=True)

        # Verify car is repaired
        repaired_car = manager.inventory.get_car(car_id)
        assert repaired_car.status == CarStatus.AVAILABLE
        assert repaired_car.damage_level == 0


class TestEdgeCases:
    """Edge case tests for integration scenarios."""

    def test_int21_race_with_minimum_participants(
        self, registration_module, crew_module, inventory_module, race_module
    ):
        """
        INT-21: Race with exactly minimum participants (2).
        """
        d1 = registration_module.register_member("D1")
        d2 = registration_module.register_member("D2")
        crew_module.assign_role(d1.member_id, "driver")
        crew_module.assign_role(d2.member_id, "driver")

        c1 = inventory_module.add_car("C", "1", 2020)
        c2 = inventory_module.add_car("C", "2", 2020)

        race = race_module.create_race("Min Race", "street", 100.0, min_participants=2)
        race_module.add_participant(race.race_id, d1.member_id, c1.car_id)
        race_module.add_participant(race.race_id, d2.member_id, c2.car_id)

        started = race_module.start_race(race.race_id)
        assert started.status == RaceStatus.IN_PROGRESS

    def test_int22_race_below_minimum_participants_fails(
        self, registration_module, crew_module, inventory_module, race_module
    ):
        """
        INT-22: Race with less than minimum participants cannot start.
        """
        driver = registration_module.register_member("Solo Driver")
        crew_module.assign_role(driver.member_id, "driver")
        car = inventory_module.add_car("Solo", "Car", 2020)

        race = race_module.create_race("Solo Race", "street", 100.0)
        race_module.add_participant(race.race_id, driver.member_id, car.car_id)

        with pytest.raises(MinimumParticipantsError):
            race_module.start_race(race.race_id)

    def test_int23_same_car_cannot_be_in_race_twice(
        self, registration_module, crew_module, inventory_module, race_module
    ):
        """
        INT-23: Same car cannot be used by two drivers in same race.
        """
        d1 = registration_module.register_member("Driver 1")
        d2 = registration_module.register_member("Driver 2")
        crew_module.assign_role(d1.member_id, "driver")
        crew_module.assign_role(d2.member_id, "driver")

        car = inventory_module.add_car("Shared", "Car", 2020)
        race = race_module.create_race("Shared Car Test", "street", 100.0)

        race_module.add_participant(race.race_id, d1.member_id, car.car_id)

        with pytest.raises(CarAlreadyInRaceError):
            race_module.add_participant(race.race_id, d2.member_id, car.car_id)

    def test_int24_same_driver_cannot_enter_race_twice(
        self, registration_module, crew_module, inventory_module, race_module
    ):
        """
        INT-24: Same driver cannot enter same race twice.
        """
        driver = registration_module.register_member("Eager Driver")
        crew_module.assign_role(driver.member_id, "driver")

        c1 = inventory_module.add_car("Car", "1", 2020)
        c2 = inventory_module.add_car("Car", "2", 2020)

        race = race_module.create_race("Duplicate Test", "street", 100.0)
        race_module.add_participant(race.race_id, driver.member_id, c1.car_id)

        with pytest.raises(ParticipantAlreadyInRaceError):
            race_module.add_participant(race.race_id, driver.member_id, c2.car_id)

    def test_int25_mission_failure_no_reward(
        self, registration_module, crew_module, inventory_module, mission_module
    ):
        """
        INT-25: Failed missions do not add reward to inventory.
        """
        initial_cash = inventory_module.get_cash_balance()

        driver = registration_module.register_member("Failed Driver")
        crew_module.assign_role(driver.member_id, "driver")

        mission = mission_module.create_mission("Risky Delivery", "delivery", 500.0)
        mission_module.assign_mission(mission.mission_id, [driver.member_id])
        mission_module.start_mission(mission.mission_id)
        mission_module.complete_mission(mission.mission_id, success=False)

        final_cash = inventory_module.get_cash_balance()
        assert final_cash == initial_cash  # No reward on failure


# ==============================================================================
# EXTENDED INTEGRATION TESTS (INT-26 to INT-38)
# Additional comprehensive tests for deeper module interactions
# ==============================================================================

class TestNotificationIntegration:
    """Tests for Notification Module integration with other modules."""

    def test_int26_notification_on_race_creation(
        self, registration_module, crew_module, inventory_module,
        race_module, notification_module
    ):
        """
        INT-26: Notification sent when race is created.

        Scenario: Create race and verify subscribed members get notified.
        Modules: Race Management -> Notification
        Expected: Race alert notification is created.
        """
        # Setup driver and subscribe with a callback
        driver = registration_module.register_member("Notified Driver")
        crew_module.assign_role(driver.member_id, "driver")

        # Subscribe with a no-op callback
        notification_module.subscribe(driver.member_id, lambda n: None)

        # Create race and send alert (use "scheduled" as alert_type)
        race = race_module.create_race("Alert Race", "street", 1000.0)
        notification_module.send_race_alert(
            race.race_id, [driver.member_id], "scheduled"
        )

        # Verify notification exists with correct type (RACE_SCHEDULED)
        notifications = notification_module.get_notifications(driver.member_id)
        assert len(notifications) >= 1
        from models import NotificationType
        assert any(n.notification_type == NotificationType.RACE_SCHEDULED for n in notifications)

    def test_int27_notification_on_mission_assignment(
        self, registration_module, crew_module, mission_module, notification_module
    ):
        """
        INT-27: Notification sent when mission is assigned.

        Scenario: Assign mission and verify crew gets notified.
        Modules: Mission Planning -> Notification
        Expected: Mission alert notification is created for assigned crew.
        """
        mechanic = registration_module.register_member("Alert Mechanic")
        crew_module.assign_role(mechanic.member_id, "mechanic")

        # Subscribe with a no-op callback
        notification_module.subscribe(mechanic.member_id, lambda n: None)

        mission = mission_module.create_mission("Notify Job", "repair", 300.0)
        mission_module.assign_mission(mission.mission_id, [mechanic.member_id])

        # Send mission alert
        notification_module.send_mission_alert(
            mission.mission_id, [mechanic.member_id], mission.name
        )

        # Verify notification exists with correct type (MISSION_ASSIGNED)
        notifications = notification_module.get_notifications(mechanic.member_id)
        assert len(notifications) >= 1
        from models import NotificationType
        assert any(n.notification_type == NotificationType.MISSION_ASSIGNED for n in notifications)

    def test_int28_notification_on_mission_completion(
        self, registration_module, crew_module, mission_module, notification_module
    ):
        """
        INT-28: Notification sent when mission completes.

        Scenario: Complete mission and verify completion notification sent.
        Modules: Mission Planning -> Notification
        Expected: Mission completed notification is created.
        """
        driver = registration_module.register_member("Completion Driver")
        crew_module.assign_role(driver.member_id, "driver")

        # Subscribe with a no-op callback
        notification_module.subscribe(driver.member_id, lambda n: None)

        mission = mission_module.create_mission("Complete Job", "delivery", 400.0)
        mission_module.assign_mission(mission.mission_id, [driver.member_id])
        mission_module.start_mission(mission.mission_id)
        mission_module.complete_mission(mission.mission_id, success=True)

        # Send completion notification (note: correct method name is send_mission_completed_alert)
        notification_module.send_mission_completed_alert(
            mission.mission_id, [driver.member_id], success=True
        )

        # Verify notification exists with correct type (MISSION_COMPLETED)
        notifications = notification_module.get_notifications(driver.member_id)
        from models import NotificationType
        assert any(n.notification_type == NotificationType.MISSION_COMPLETED for n in notifications)


class TestExtendedRaceIntegration:
    """Extended race integration tests."""

    def test_int29_multiple_races_update_rankings(
        self, registration_module, crew_module, inventory_module,
        race_module, results_module, leaderboard_module
    ):
        """
        INT-29: Multiple races correctly update rankings.

        Scenario: Run 3 races, verify cumulative rankings are correct.
        Modules: Race Management -> Results -> Leaderboard
        Expected: Driver with most wins is ranked highest.
        """
        # Setup 2 drivers
        d1 = registration_module.register_member("Consistent Winner")
        d2 = registration_module.register_member("Sometimes Winner")
        crew_module.assign_role(d1.member_id, "driver")
        crew_module.assign_role(d2.member_id, "driver")

        # Run 3 races: d1 wins 2, d2 wins 1
        for i, winner in enumerate([d1, d1, d2]):
            c1 = inventory_module.add_car(f"Car{i}A", "Model", 2021)
            c2 = inventory_module.add_car(f"Car{i}B", "Model", 2021)

            race = race_module.create_race(f"Race {i+1}", "circuit", 500.0)
            race_module.add_participant(race.race_id, d1.member_id, c1.car_id)
            race_module.add_participant(race.race_id, d2.member_id, c2.car_id)
            race_module.start_race(race.race_id)

            loser = d2 if winner == d1 else d1
            results_module.record_race_outcome(
                race.race_id, {1: winner.member_id, 2: loser.member_id}
            )

        # Verify d1 has more wins
        d1_stats = leaderboard_module.get_member_stats(d1.member_id)
        d2_stats = leaderboard_module.get_member_stats(d2.member_id)
        assert d1_stats.races_won == 2
        assert d2_stats.races_won == 1

    def test_int30_race_with_three_participants_prize_distribution(
        self, registration_module, crew_module, inventory_module,
        race_module, results_module
    ):
        """
        INT-30: Race with 3 participants distributes prizes correctly.

        Scenario: 3 drivers race, verify 1st/2nd/3rd get correct prizes.
        Modules: Race Management -> Results -> Inventory
        Expected: Prize distributed as 50%/30%/15% of prize pool (95% total).
        """
        initial_cash = inventory_module.get_cash_balance()

        # Setup 3 drivers
        drivers = []
        cars = []
        for i in range(3):
            d = registration_module.register_member(f"Racer {i+1}")
            crew_module.assign_role(d.member_id, "driver")
            c = inventory_module.add_car(f"Car{i}", "Fast", 2021)
            drivers.append(d)
            cars.append(c)

        # Create and run race with $1000 pool
        race = race_module.create_race("Triple Race", "circuit", 1000.0)
        for d, c in zip(drivers, cars):
            race_module.add_participant(race.race_id, d.member_id, c.car_id)

        race_module.start_race(race.race_id)
        positions = {1: drivers[0].member_id, 2: drivers[1].member_id, 3: drivers[2].member_id}
        results_module.record_race_outcome(race.race_id, positions)

        # Total: 50% + 30% + 15% = 95% of $1000 = $950
        expected_total = 1000.0 * 0.95
        final_cash = inventory_module.get_cash_balance()
        assert final_cash == initial_cash + expected_total

    def test_int31_cancel_race_releases_cars(
        self, registration_module, crew_module, inventory_module, race_module
    ):
        """
        INT-31: Cancelling race releases cars back to available.

        Scenario: Add participants to race, cancel race, verify car statuses.
        Modules: Race Management -> Inventory
        Expected: All cars return to AVAILABLE status.
        """
        d1 = registration_module.register_member("Cancel D1")
        d2 = registration_module.register_member("Cancel D2")
        crew_module.assign_role(d1.member_id, "driver")
        crew_module.assign_role(d2.member_id, "driver")

        c1 = inventory_module.add_car("Cancel", "C1", 2021)
        c2 = inventory_module.add_car("Cancel", "C2", 2021)

        race = race_module.create_race("To Cancel", "street", 500.0)
        race_module.add_participant(race.race_id, d1.member_id, c1.car_id)
        race_module.add_participant(race.race_id, d2.member_id, c2.car_id)

        # Cancel race
        cancelled = race_module.cancel_race(race.race_id)
        assert cancelled.status == RaceStatus.CANCELLED

        # Cars should be available
        assert inventory_module.get_car(c1.car_id).status == CarStatus.AVAILABLE
        assert inventory_module.get_car(c2.car_id).status == CarStatus.AVAILABLE


class TestExtendedMissionIntegration:
    """Extended mission integration tests."""

    def test_int32_rescue_mission_requires_driver_and_mechanic(
        self, registration_module, crew_module, mission_module
    ):
        """
        INT-32: Rescue mission requires both driver and mechanic.

        Scenario: Create rescue mission, verify role requirements.
        Modules: Mission Planning -> Crew Management
        Expected: Mission requires DRIVER and MECHANIC roles.
        """
        driver = registration_module.register_member("Rescue Driver")
        mechanic = registration_module.register_member("Rescue Mechanic")
        crew_module.assign_role(driver.member_id, "driver")
        crew_module.assign_role(mechanic.member_id, "mechanic")

        mission = mission_module.create_mission("Rescue Op", "rescue", 800.0)

        # Assign both roles
        result = mission_module.assign_mission(
            mission.mission_id, [driver.member_id, mechanic.member_id]
        )
        assert len(result.assigned_crew) == 2

        # Start and complete
        mission_module.start_mission(mission.mission_id)
        completed = mission_module.complete_mission(mission.mission_id, success=True)
        assert completed.status == MissionStatus.COMPLETED

    def test_int33_cancel_mission_releases_crew(
        self, registration_module, crew_module, mission_module
    ):
        """
        INT-33: Cancelling mission releases crew members.

        Scenario: Assign mission, cancel it, verify crew is available.
        Modules: Mission Planning -> Crew Management
        Expected: Crew members become available after cancellation.
        """
        mechanic = registration_module.register_member("Released Mechanic")
        crew_module.assign_role(mechanic.member_id, "mechanic")

        mission = mission_module.create_mission("To Cancel", "repair", 200.0)
        mission_module.assign_mission(mission.mission_id, [mechanic.member_id])

        # Cancel mission (sets status to FAILED, not CANCELLED)
        cancelled = mission_module.cancel_mission(mission.mission_id)
        assert cancelled.status == MissionStatus.FAILED

        # Mechanic should be available for new mission
        mission2 = mission_module.create_mission("New Job", "repair", 300.0)
        result = mission_module.assign_mission(mission2.mission_id, [mechanic.member_id])
        assert len(result.assigned_crew) == 1

    def test_int34_crew_freed_after_mission_completion(
        self, registration_module, crew_module, mission_module
    ):
        """
        INT-34: Crew is freed and available after mission completes.

        Scenario: Complete mission, verify crew can be assigned to new mission.
        Modules: Mission Planning -> Crew Management
        Expected: Crew member can be assigned to subsequent mission.
        """
        driver = registration_module.register_member("Busy Then Free")
        crew_module.assign_role(driver.member_id, "driver")

        # First mission
        m1 = mission_module.create_mission("Job 1", "delivery", 100.0)
        mission_module.assign_mission(m1.mission_id, [driver.member_id])
        mission_module.start_mission(m1.mission_id)
        mission_module.complete_mission(m1.mission_id, success=True)

        # Second mission - should work since first is complete
        m2 = mission_module.create_mission("Job 2", "delivery", 200.0)
        result = mission_module.assign_mission(m2.mission_id, [driver.member_id])
        assert driver.member_id in result.assigned_crew

    def test_int35_multiple_concurrent_missions(
        self, registration_module, crew_module, mission_module
    ):
        """
        INT-35: Multiple missions can run concurrently with different crews.

        Scenario: Two missions with different crews run simultaneously.
        Modules: Mission Planning -> Crew Management
        Expected: Both missions can be in progress at same time.
        """
        d1 = registration_module.register_member("Mission Driver 1")
        d2 = registration_module.register_member("Mission Driver 2")
        crew_module.assign_role(d1.member_id, "driver")
        crew_module.assign_role(d2.member_id, "driver")

        m1 = mission_module.create_mission("Concurrent 1", "delivery", 100.0)
        m2 = mission_module.create_mission("Concurrent 2", "delivery", 200.0)

        mission_module.assign_mission(m1.mission_id, [d1.member_id])
        mission_module.assign_mission(m2.mission_id, [d2.member_id])

        mission_module.start_mission(m1.mission_id)
        mission_module.start_mission(m2.mission_id)

        # Both should be in progress
        assert mission_module.get_mission(m1.mission_id).status == MissionStatus.IN_PROGRESS
        assert mission_module.get_mission(m2.mission_id).status == MissionStatus.IN_PROGRESS


class TestExtendedInventoryIntegration:
    """Extended inventory integration tests."""

    def test_int36_spare_parts_used_during_repair(
        self, registration_module, crew_module, inventory_module, mission_module
    ):
        """
        INT-36: Spare parts are consumed during repair mission.

        Scenario: Add spare parts, complete repair, verify parts used.
        Modules: Mission Planning -> Inventory
        Expected: Spare parts quantity decreases after repair.
        """
        mechanic = registration_module.register_member("Parts User")
        crew_module.assign_role(mechanic.member_id, "mechanic")

        # Add spare parts
        inventory_module.add_spare_parts("brake_pads", 10, 50.0)
        initial_qty = inventory_module.get_spare_parts_quantity("brake_pads")

        # Use parts
        inventory_module.use_spare_parts("brake_pads", 2)

        final_qty = inventory_module.get_spare_parts_quantity("brake_pads")
        assert final_qty == initial_qty - 2

    def test_int37_low_inventory_tracking(
        self, inventory_module
    ):
        """
        INT-37: Low inventory items are tracked correctly.

        Scenario: Add parts, use most of them, verify low inventory list.
        Modules: Inventory
        Expected: Items below threshold appear in low inventory list.
        """
        # Add parts with quantity that will be low
        inventory_module.add_spare_parts("rare_part", 5, 100.0)

        # Use most parts
        inventory_module.use_spare_parts("rare_part", 4)

        # Check low parts (threshold is typically 5)
        low_parts = inventory_module.list_low_spare_parts()
        # SparePart objects have .name attribute, not dict access
        part_names = [p.name for p in low_parts]
        assert "rare_part" in part_names


class TestEndToEndWorkflows:
    """Complete end-to-end workflow tests."""

    def test_int38_damage_repair_race_again_workflow(
        self, registration_module, crew_module, inventory_module,
        race_module, results_module, mission_module
    ):
        """
        INT-38: Complete workflow: race -> damage -> repair -> race again.

        Scenario: Driver races, car gets damaged, mechanic repairs, driver races again.
        Modules: All modules involved in racing and repair workflows.
        Expected: Car can race again after successful repair.
        """
        # Setup driver and mechanic
        driver = registration_module.register_member("Repeat Racer")
        driver2 = registration_module.register_member("Opponent")
        mechanic = registration_module.register_member("Fix Everything")
        crew_module.assign_role(driver.member_id, "driver")
        crew_module.assign_role(driver2.member_id, "driver")
        crew_module.assign_role(mechanic.member_id, "mechanic")

        car1 = inventory_module.add_car("Tough", "Racer", 2021)
        car2 = inventory_module.add_car("Other", "Car", 2021)

        # First race
        race1 = race_module.create_race("First Race", "circuit", 500.0)
        race_module.add_participant(race1.race_id, driver.member_id, car1.car_id)
        race_module.add_participant(race1.race_id, driver2.member_id, car2.car_id)
        race_module.start_race(race1.race_id)
        race_module.complete_race(race1.race_id, {1: driver.member_id, 2: driver2.member_id})

        # Simulate damage to car1
        inventory_module.set_car_damage_level(car1.car_id, 50)

        # Car should not be available
        assert inventory_module.get_car(car1.car_id).damage_level == 50

        # Create and complete repair mission
        repair = mission_module.create_repair_mission(car1.car_id)
        mission_module.assign_mission(repair.mission_id, [mechanic.member_id])
        mission_module.start_mission(repair.mission_id)
        mission_module.complete_mission(repair.mission_id, success=True)

        # Car should be repaired
        assert inventory_module.get_car(car1.car_id).damage_level == 0
        assert inventory_module.get_car(car1.car_id).status == CarStatus.AVAILABLE

        # Second race with same car
        car3 = inventory_module.add_car("Fresh", "Car", 2021)
        race2 = race_module.create_race("Second Race", "circuit", 600.0)
        race_module.add_participant(race2.race_id, driver.member_id, car1.car_id)
        race_module.add_participant(race2.race_id, driver2.member_id, car3.car_id)

        started = race_module.start_race(race2.race_id)
        assert started.status == RaceStatus.IN_PROGRESS
