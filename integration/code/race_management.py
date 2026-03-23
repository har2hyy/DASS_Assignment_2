"""
Race Management Module - Creates and manages races.

Responsibilities:
- Create races with prize pools
- Add participants (driver + car combinations)
- Validate driver eligibility
- Start and complete races
- Track race status
"""

from datetime import datetime
from typing import Dict, List, Optional

try:
    from .models import (
        Race, RaceStatus, RaceParticipant, Role, CarStatus, generate_id
    )
    from .registration import RegistrationModule
    from .crew_management import CrewManagementModule
    from .inventory import InventoryModule
    from .exceptions import (
        RaceNotFoundError,
        RaceAlreadyStartedError,
        RaceNotStartedError,
        NotADriverError,
        ParticipantAlreadyInRaceError,
        CarAlreadyInRaceError,
        CarNotAvailableError,
        MinimumParticipantsError,
        MemberNotFoundError,
        CarNotFoundError
    )
except ImportError:
    from models import (
        Race, RaceStatus, RaceParticipant, Role, CarStatus, generate_id
    )
    from registration import RegistrationModule
    from crew_management import CrewManagementModule
    from inventory import InventoryModule
    from exceptions import (
        RaceNotFoundError,
        RaceAlreadyStartedError,
        RaceNotStartedError,
        NotADriverError,
        ParticipantAlreadyInRaceError,
        CarAlreadyInRaceError,
        CarNotAvailableError,
        MinimumParticipantsError,
        MemberNotFoundError,
        CarNotFoundError
    )


class RaceManagementModule:
    """
    Manages the creation and execution of races.

    Dependencies:
    - RegistrationModule: To validate members exist
    - CrewManagementModule: To validate driver roles
    - InventoryModule: To get and update car status
    """

    def __init__(
        self,
        registration_module: RegistrationModule,
        crew_management_module: CrewManagementModule,
        inventory_module: InventoryModule
    ):
        """
        Initialize race management with required dependencies.

        Args:
            registration_module: For member validation.
            crew_management_module: For role validation.
            inventory_module: For car management.
        """
        self._registration = registration_module
        self._crew = crew_management_module
        self._inventory = inventory_module
        self._races: Dict[str, Race] = {}
        self._race_completed_callback = None

    def set_race_completed_callback(self, callback):
        """Set a callback function for when a race is completed."""
        self._race_completed_callback = callback

    def create_race(
        self,
        name: str,
        race_type: str,
        prize_pool: float,
        race_id: Optional[str] = None,
        min_participants: int = 2
    ) -> Race:
        """
        Create a new race.

        Args:
            name: Name of the race.
            race_type: Type of race (street, circuit, drag, drift).
            prize_pool: Total prize money.
            race_id: Optional custom ID.
            min_participants: Minimum participants required to start.

        Returns:
            The newly created Race object.

        Raises:
            ValueError: If inputs are invalid.
        """
        if not name or not isinstance(name, str):
            raise ValueError("Race name must be a non-empty string")
        if not race_type or not isinstance(race_type, str):
            raise ValueError("Race type must be a non-empty string")
        if not isinstance(prize_pool, (int, float)) or prize_pool < 0:
            raise ValueError("Prize pool must be a non-negative number")
        if not isinstance(min_participants, int) or min_participants < 2:
            raise ValueError("Minimum participants must be at least 2")

        if race_id is None:
            race_id = generate_id()

        race = Race(
            race_id=race_id,
            name=name.strip(),
            race_type=race_type.lower().strip(),
            prize_pool=float(prize_pool),
            min_participants=min_participants,
            status=RaceStatus.SCHEDULED
        )

        self._races[race_id] = race
        return race

    def get_race_details(self, race_id: str) -> Race:
        """
        Get details of a specific race.

        Args:
            race_id: The unique identifier of the race.

        Returns:
            The Race object.

        Raises:
            RaceNotFoundError: If race doesn't exist.
        """
        if race_id not in self._races:
            raise RaceNotFoundError(race_id)
        return self._races[race_id]

    def list_scheduled_races(self) -> List[Race]:
        """
        Get all scheduled (not yet started) races.

        Returns:
            List of scheduled Race objects.
        """
        return [r for r in self._races.values() if r.status == RaceStatus.SCHEDULED]

    def list_all_races(self) -> List[Race]:
        """
        Get all races.

        Returns:
            List of all Race objects.
        """
        return list(self._races.values())

    def add_participant(
        self,
        race_id: str,
        driver_id: str,
        car_id: str
    ) -> RaceParticipant:
        """
        Add a participant to a race.

        Business Rules:
        - Driver must be registered
        - Driver must have the 'driver' role
        - Car must be available in inventory
        - Driver cannot be added twice to same race
        - Car cannot be used twice in same race

        Args:
            race_id: The race to join.
            driver_id: The driver's member ID.
            car_id: The car's ID from inventory.

        Returns:
            The created RaceParticipant object.

        Raises:
            RaceNotFoundError: If race doesn't exist.
            RaceAlreadyStartedError: If race has already started.
            MemberNotFoundError: If driver is not registered.
            NotADriverError: If member doesn't have driver role.
            CarNotFoundError: If car doesn't exist.
            CarNotAvailableError: If car is not available.
            ParticipantAlreadyInRaceError: If driver is already in race.
            CarAlreadyInRaceError: If car is already in race.
        """
        # Validate race exists and is scheduled
        if race_id not in self._races:
            raise RaceNotFoundError(race_id)

        race = self._races[race_id]
        if race.status != RaceStatus.SCHEDULED:
            raise RaceAlreadyStartedError(race_id)

        # Validate driver is registered (Business Rule)
        if not self._registration.validate_member_exists(driver_id):
            raise MemberNotFoundError(driver_id)

        # Validate driver has driver role (Business Rule)
        member_role = self._crew.get_member_role(driver_id)
        if member_role != Role.DRIVER:
            role_str = member_role.value if member_role else "none"
            raise NotADriverError(driver_id, role_str)

        # Validate car exists and is available (Business Rule)
        car = self._inventory.get_car(car_id)
        if car.status != CarStatus.AVAILABLE:
            raise CarNotAvailableError(car_id, car.status.value)

        # Check driver not already in race
        for participant in race.participants:
            if participant.driver_id == driver_id:
                raise ParticipantAlreadyInRaceError(driver_id, race_id)
            if participant.car_id == car_id:
                raise CarAlreadyInRaceError(car_id, race_id)

        # Create participant and add to race
        participant = RaceParticipant(
            driver_id=driver_id,
            car_id=car_id
        )
        race.participants.append(participant)

        return participant

    def remove_participant(self, race_id: str, driver_id: str) -> bool:
        """
        Remove a participant from a race.

        Args:
            race_id: The race ID.
            driver_id: The driver to remove.

        Returns:
            True if successfully removed.

        Raises:
            RaceNotFoundError: If race doesn't exist.
            RaceAlreadyStartedError: If race has already started.
            ValueError: If driver is not in the race.
        """
        if race_id not in self._races:
            raise RaceNotFoundError(race_id)

        race = self._races[race_id]
        if race.status != RaceStatus.SCHEDULED:
            raise RaceAlreadyStartedError(race_id)

        for i, participant in enumerate(race.participants):
            if participant.driver_id == driver_id:
                race.participants.pop(i)
                return True

        raise ValueError(f"Driver '{driver_id}' is not in race '{race_id}'")

    def validate_participant(self, driver_id: str, car_id: str) -> dict:
        """
        Validate if a driver-car combination is valid for racing.

        Args:
            driver_id: The driver's member ID.
            car_id: The car's ID.

        Returns:
            Dictionary with validation results.
        """
        result = {
            "driver_valid": False,
            "car_valid": False,
            "errors": []
        }

        # Check driver
        try:
            if not self._registration.validate_member_exists(driver_id):
                result["errors"].append("Driver not registered")
            elif self._crew.get_member_role(driver_id) != Role.DRIVER:
                result["errors"].append("Member is not a driver")
            else:
                result["driver_valid"] = True
        except Exception as e:
            result["errors"].append(str(e))

        # Check car
        try:
            car = self._inventory.get_car(car_id)
            if car.status != CarStatus.AVAILABLE:
                result["errors"].append(f"Car not available: {car.status.value}")
            else:
                result["car_valid"] = True
        except CarNotFoundError:
            result["errors"].append("Car not found")
        except Exception as e:
            result["errors"].append(str(e))

        return result

    def start_race(self, race_id: str) -> Race:
        """
        Start a scheduled race.

        Business Rules:
        - Race must have minimum participants
        - All cars are marked as 'in_race'

        Args:
            race_id: The race to start.

        Returns:
            The updated Race object.

        Raises:
            RaceNotFoundError: If race doesn't exist.
            RaceAlreadyStartedError: If race has already started.
            MinimumParticipantsError: If not enough participants.
        """
        if race_id not in self._races:
            raise RaceNotFoundError(race_id)

        race = self._races[race_id]

        if race.status != RaceStatus.SCHEDULED:
            raise RaceAlreadyStartedError(race_id)

        if len(race.participants) < race.min_participants:
            raise MinimumParticipantsError(
                race_id,
                len(race.participants),
                race.min_participants
            )

        # Mark all cars as in_race
        for participant in race.participants:
            self._inventory.update_car_status(participant.car_id, "in_race")

        race.status = RaceStatus.IN_PROGRESS
        race.started_at = datetime.now()

        return race

    def complete_race(
        self,
        race_id: str,
        positions: Dict[int, str],
        damaged_cars: Optional[List[str]] = None
    ) -> Race:
        """
        Complete a race with results.

        Business Rules:
        - Race results update inventory (via callback)
        - Damaged cars are marked in inventory

        Args:
            race_id: The race to complete.
            positions: Dictionary mapping position (1, 2, 3...) to driver_id.
            damaged_cars: Optional list of car IDs that were damaged.

        Returns:
            The updated Race object.

        Raises:
            RaceNotFoundError: If race doesn't exist.
            RaceNotStartedError: If race hasn't started.
        """
        if race_id not in self._races:
            raise RaceNotFoundError(race_id)

        race = self._races[race_id]

        if race.status != RaceStatus.IN_PROGRESS:
            raise RaceNotStartedError(race_id)

        damaged_cars = damaged_cars or []

        # Update participant positions and damage status
        for participant in race.participants:
            for pos, driver_id in positions.items():
                if participant.driver_id == driver_id:
                    participant.position = pos
                    break
            if participant.car_id in damaged_cars:
                participant.is_damaged = True

        # Update car statuses in inventory
        for participant in race.participants:
            if participant.car_id in damaged_cars:
                self._inventory.update_car_status(participant.car_id, "damaged")
                self._inventory.set_car_damage_level(participant.car_id, 60)
            else:
                self._inventory.update_car_status(participant.car_id, "available")

        race.status = RaceStatus.COMPLETED
        race.completed_at = datetime.now()

        # Trigger callback to Results module
        if self._race_completed_callback:
            self._race_completed_callback(race_id, positions, damaged_cars)

        return race

    def cancel_race(self, race_id: str) -> Race:
        """
        Cancel a scheduled race.

        Args:
            race_id: The race to cancel.

        Returns:
            The updated Race object.

        Raises:
            RaceNotFoundError: If race doesn't exist.
            RaceAlreadyStartedError: If race has already started.
        """
        if race_id not in self._races:
            raise RaceNotFoundError(race_id)

        race = self._races[race_id]

        if race.status == RaceStatus.IN_PROGRESS:
            raise RaceAlreadyStartedError(race_id)

        race.status = RaceStatus.CANCELLED
        return race

    def get_race_participants(self, race_id: str) -> List[RaceParticipant]:
        """
        Get all participants in a race.

        Args:
            race_id: The race ID.

        Returns:
            List of RaceParticipant objects.

        Raises:
            RaceNotFoundError: If race doesn't exist.
        """
        if race_id not in self._races:
            raise RaceNotFoundError(race_id)
        return self._races[race_id].participants

    def get_participant_count(self, race_id: str) -> int:
        """
        Get the number of participants in a race.

        Args:
            race_id: The race ID.

        Returns:
            Number of participants.

        Raises:
            RaceNotFoundError: If race doesn't exist.
        """
        if race_id not in self._races:
            raise RaceNotFoundError(race_id)
        return len(self._races[race_id].participants)

    def get_races_by_status(self, status: str) -> List[Race]:
        """
        Get all races with a specific status.

        Args:
            status: The status to filter by.

        Returns:
            List of Race objects with the specified status.
        """
        try:
            status_enum = RaceStatus(status.lower().strip())
        except ValueError:
            return []

        return [r for r in self._races.values() if r.status == status_enum]
