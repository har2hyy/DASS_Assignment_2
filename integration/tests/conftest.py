"""
Pytest configuration and shared fixtures for integration tests.
"""

import sys
from pathlib import Path
import pytest

# Add code directory to path
code_path = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_path))

from registration import RegistrationModule
from crew_management import CrewManagementModule
from inventory import InventoryModule
from race_management import RaceManagementModule
from results import ResultsModule
from mission_planning import MissionPlanningModule
from leaderboard import LeaderboardModule
from notification import NotificationModule
from streetrace_manager import StreetRaceManager


@pytest.fixture
def registration_module():
    """Create a fresh RegistrationModule instance."""
    return RegistrationModule()


@pytest.fixture
def inventory_module():
    """Create a fresh InventoryModule instance with starting cash."""
    return InventoryModule(initial_cash=5000.0)


@pytest.fixture
def crew_module(registration_module):
    """Create a CrewManagementModule with registration dependency."""
    return CrewManagementModule(registration_module)


@pytest.fixture
def race_module(registration_module, crew_module, inventory_module):
    """Create a RaceManagementModule with all dependencies."""
    return RaceManagementModule(registration_module, crew_module, inventory_module)


@pytest.fixture
def results_module(race_module, inventory_module):
    """Create a ResultsModule with required dependencies."""
    return ResultsModule(race_module, inventory_module)


@pytest.fixture
def mission_module(crew_module, inventory_module):
    """Create a MissionPlanningModule with required dependencies."""
    return MissionPlanningModule(crew_module, inventory_module)


@pytest.fixture
def leaderboard_module(results_module):
    """Create a LeaderboardModule with results dependency."""
    return LeaderboardModule(results_module)


@pytest.fixture
def notification_module():
    """Create a fresh NotificationModule instance."""
    return NotificationModule()


@pytest.fixture
def street_race_manager():
    """Create a fully integrated StreetRaceManager instance."""
    return StreetRaceManager(initial_cash=10000.0)


@pytest.fixture
def populated_manager():
    """Create a StreetRaceManager with pre-populated data."""
    manager = StreetRaceManager(initial_cash=10000.0)

    # Register crew members
    driver1 = manager.register_and_assign_driver("Speed Racer", 8)
    driver2 = manager.register_and_assign_driver("Fast Freddy", 7)
    driver3 = manager.register_and_assign_driver("Quick Quinn", 6)
    mechanic1 = manager.register_and_assign_mechanic("Wrench Wilson", 8)
    mechanic2 = manager.register_and_assign_mechanic("Fix-It Felix", 7)
    strategist1 = manager.register_and_assign_strategist("Plan Paul", 9)

    # Add cars
    car1 = manager.inventory.add_car("Toyota", "Supra", 2020, performance_rating=8)
    car2 = manager.inventory.add_car("Nissan", "GT-R", 2021, performance_rating=9)
    car3 = manager.inventory.add_car("Honda", "NSX", 2019, performance_rating=7)

    # Add spare parts
    manager.inventory.add_spare_parts("engine_parts", 10, 50.0)
    manager.inventory.add_spare_parts("tires", 20, 100.0)
    manager.inventory.add_spare_parts("brake_pads", 15, 30.0)

    # Add tools
    manager.inventory.add_tools("wrench_set", 5)
    manager.inventory.add_tools("jack", 3)

    return {
        "manager": manager,
        "drivers": [driver1, driver2, driver3],
        "mechanics": [mechanic1, mechanic2],
        "strategists": [strategist1],
        "cars": [car1, car2, car3]
    }


@pytest.fixture
def registered_member(registration_module):
    """Create a single registered member for testing."""
    return registration_module.register_member("Test Driver")


@pytest.fixture
def driver_member(registration_module, crew_module):
    """Create a registered member with driver role."""
    member = registration_module.register_member("Test Driver")
    crew_module.assign_role(member.member_id, "driver")
    return member


@pytest.fixture
def mechanic_member(registration_module, crew_module):
    """Create a registered member with mechanic role."""
    member = registration_module.register_member("Test Mechanic")
    crew_module.assign_role(member.member_id, "mechanic")
    return member


@pytest.fixture
def available_car(inventory_module):
    """Create an available car in inventory."""
    return inventory_module.add_car("Test", "Car", 2020)
