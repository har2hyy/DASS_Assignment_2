"""
Mission Planning Module - Assigns and validates missions.

Responsibilities:
- Create missions (delivery, rescue, repair, heist)
- Assign crew members to missions
- Validate required roles are available
- Start and complete missions
- Handle repair missions for damaged cars
"""

from datetime import datetime
from typing import Dict, List, Optional

try:
    from .models import (
        Mission, MissionStatus, MissionType, Role, CarStatus, generate_id
    )
    from .crew_management import CrewManagementModule
    from .inventory import InventoryModule
    from .exceptions import (
        MissionNotFoundError,
        RequiredRoleUnavailableError,
        MissionAlreadyStartedError,
        MissionNotStartedError,
        CrewMemberBusyError,
        InvalidMissionTypeError,
        MemberNotFoundError
    )
except ImportError:
    from models import (
        Mission, MissionStatus, MissionType, Role, CarStatus, generate_id
    )
    from crew_management import CrewManagementModule
    from inventory import InventoryModule
    from exceptions import (
        MissionNotFoundError,
        RequiredRoleUnavailableError,
        MissionAlreadyStartedError,
        MissionNotStartedError,
        CrewMemberBusyError,
        InvalidMissionTypeError,
        MemberNotFoundError
    )


class MissionPlanningModule:
    """
    Manages mission creation, assignment, and execution.

    Dependencies:
    - CrewManagementModule: To validate roles and availability
    - InventoryModule: For repair missions and rewards

    Business Rules:
    - Missions cannot start if required roles are unavailable
    - If a car is damaged, a repair mission requires a mechanic
    """

    # Default required roles for each mission type
    DEFAULT_REQUIRED_ROLES = {
        MissionType.DELIVERY: [Role.DRIVER],
        MissionType.RESCUE: [Role.DRIVER, Role.MECHANIC],
        MissionType.REPAIR: [Role.MECHANIC],
        MissionType.HEIST: [Role.DRIVER, Role.MECHANIC, Role.STRATEGIST]
    }

    def __init__(
        self,
        crew_management_module: CrewManagementModule,
        inventory_module: InventoryModule
    ):
        """
        Initialize mission planning with required dependencies.

        Args:
            crew_management_module: For role validation.
            inventory_module: For car repair and rewards.
        """
        self._crew = crew_management_module
        self._inventory = inventory_module
        self._missions: Dict[str, Mission] = {}
        self._notification_callback = None

    def set_notification_callback(self, callback):
        """Set callback for mission notifications."""
        self._notification_callback = callback

    def create_mission(
        self,
        name: str,
        mission_type: str,
        reward: float = 0.0,
        required_roles: Optional[List[str]] = None,
        mission_id: Optional[str] = None,
        car_to_repair: Optional[str] = None
    ) -> Mission:
        """
        Create a new mission.

        Args:
            name: Name of the mission.
            mission_type: Type (delivery, rescue, repair, heist).
            reward: Reward amount for completion.
            required_roles: Custom required roles (uses defaults if None).
            mission_id: Optional custom ID.
            car_to_repair: For repair missions, the car ID to repair.

        Returns:
            The created Mission object.

        Raises:
            InvalidMissionTypeError: If mission type is invalid.
            ValueError: If inputs are invalid.
        """
        if not name or not isinstance(name, str):
            raise ValueError("Mission name must be a non-empty string")

        # Validate mission type
        mission_type_enum = self._validate_and_get_mission_type(mission_type)

        # Get required roles (use defaults if not provided)
        if required_roles is None:
            roles = self.DEFAULT_REQUIRED_ROLES.get(mission_type_enum, [])
        else:
            roles = []
            for role_str in required_roles:
                try:
                    roles.append(Role(role_str.lower().strip()))
                except ValueError:
                    raise ValueError(f"Invalid role: {role_str}")

        if mission_id is None:
            mission_id = generate_id()

        mission = Mission(
            mission_id=mission_id,
            name=name.strip(),
            mission_type=mission_type_enum,
            required_roles=roles,
            reward=max(0.0, float(reward)),
            car_to_repair=car_to_repair,
            status=MissionStatus.PENDING
        )

        self._missions[mission_id] = mission
        return mission

    def get_mission(self, mission_id: str) -> Mission:
        """
        Get mission details.

        Args:
            mission_id: The mission ID.

        Returns:
            The Mission object.

        Raises:
            MissionNotFoundError: If mission doesn't exist.
        """
        if mission_id not in self._missions:
            raise MissionNotFoundError(mission_id)
        return self._missions[mission_id]

    def assign_mission(
        self,
        mission_id: str,
        crew_member_ids: List[str]
    ) -> Mission:
        """
        Assign crew members to a mission.

        Business Rules:
        - All required roles must be covered
        - Crew members must not be busy

        Args:
            mission_id: The mission to assign.
            crew_member_ids: List of member IDs to assign.

        Returns:
            The updated Mission object.

        Raises:
            MissionNotFoundError: If mission doesn't exist.
            MissionAlreadyStartedError: If mission already started.
            MemberNotFoundError: If any member doesn't exist.
            RequiredRoleUnavailableError: If required roles not covered.
            CrewMemberBusyError: If any member is busy.
        """
        if mission_id not in self._missions:
            raise MissionNotFoundError(mission_id)

        mission = self._missions[mission_id]

        if mission.status != MissionStatus.PENDING:
            raise MissionAlreadyStartedError(mission_id)

        # Validate all crew members and check they're not busy
        assigned_roles = []
        for member_id in crew_member_ids:
            # Check member exists
            if not self._crew._registration.validate_member_exists(member_id):
                raise MemberNotFoundError(member_id)

            # Check member is available
            if not self._crew.is_member_available(member_id):
                raise CrewMemberBusyError(member_id)

            # Get member's role
            role = self._crew.get_member_role(member_id)
            if role:
                assigned_roles.append(role)

        # Validate required roles are covered
        self._validate_required_roles(mission.required_roles, assigned_roles)

        # Assign crew to mission
        mission.assigned_crew = list(crew_member_ids)

        # Trigger notification callback
        if self._notification_callback:
            for member_id in crew_member_ids:
                self._notification_callback(
                    member_id,
                    f"You have been assigned to mission: {mission.name}"
                )

        return mission

    def validate_required_roles(self, mission_id: str) -> dict:
        """
        Check if all required roles are available for a mission.

        Args:
            mission_id: The mission to check.

        Returns:
            Dictionary with validation results.

        Raises:
            MissionNotFoundError: If mission doesn't exist.
        """
        if mission_id not in self._missions:
            raise MissionNotFoundError(mission_id)

        mission = self._missions[mission_id]
        result = {
            "mission_id": mission_id,
            "required_roles": [r.value for r in mission.required_roles],
            "available_roles": {},
            "all_roles_available": True,
            "missing_roles": []
        }

        for role in mission.required_roles:
            available_count = self._crew.get_available_role_count(role.value)
            result["available_roles"][role.value] = available_count

            if available_count == 0:
                result["all_roles_available"] = False
                result["missing_roles"].append(role.value)

        return result

    def _validate_required_roles(
        self,
        required_roles: List[Role],
        assigned_roles: List[Role]
    ) -> bool:
        """
        Validate that assigned roles cover all required roles.

        Args:
            required_roles: List of required Role enums.
            assigned_roles: List of assigned Role enums.

        Returns:
            True if all roles covered.

        Raises:
            RequiredRoleUnavailableError: If a required role is missing.
        """
        for required in required_roles:
            if required not in assigned_roles:
                raise RequiredRoleUnavailableError(required.value)
        return True

    def check_crew_availability(self, role_list: List[str]) -> dict:
        """
        Check availability of crew members for specific roles.

        Args:
            role_list: List of role strings to check.

        Returns:
            Dictionary with availability information.
        """
        result = {
            "roles_checked": role_list,
            "availability": {},
            "all_available": True
        }

        for role_str in role_list:
            try:
                count = self._crew.get_available_role_count(role_str)
                result["availability"][role_str] = count
                if count == 0:
                    result["all_available"] = False
            except Exception:
                result["availability"][role_str] = 0
                result["all_available"] = False

        return result

    def start_mission(self, mission_id: str) -> Mission:
        """
        Start a mission.

        Business Rule: Missions cannot start if required roles are unavailable.

        Args:
            mission_id: The mission to start.

        Returns:
            The updated Mission object.

        Raises:
            MissionNotFoundError: If mission doesn't exist.
            MissionAlreadyStartedError: If already started.
            RequiredRoleUnavailableError: If crew not assigned properly.
        """
        if mission_id not in self._missions:
            raise MissionNotFoundError(mission_id)

        mission = self._missions[mission_id]

        if mission.status != MissionStatus.PENDING:
            raise MissionAlreadyStartedError(mission_id)

        # Check crew is assigned
        if not mission.assigned_crew:
            raise RequiredRoleUnavailableError("No crew assigned")

        # Mark all assigned crew as busy
        for member_id in mission.assigned_crew:
            self._crew.set_member_busy(member_id, True)

        mission.status = MissionStatus.IN_PROGRESS
        mission.started_at = datetime.now()

        return mission

    def complete_mission(
        self,
        mission_id: str,
        success: bool = True
    ) -> Mission:
        """
        Complete a mission.

        Business Rules:
        - Successful missions add reward to inventory
        - Repair missions fix the damaged car

        Args:
            mission_id: The mission to complete.
            success: Whether the mission succeeded.

        Returns:
            The updated Mission object.

        Raises:
            MissionNotFoundError: If mission doesn't exist.
            MissionNotStartedError: If mission hasn't started.
        """
        if mission_id not in self._missions:
            raise MissionNotFoundError(mission_id)

        mission = self._missions[mission_id]

        if mission.status != MissionStatus.IN_PROGRESS:
            raise MissionNotStartedError(mission_id)

        # Mark all assigned crew as available
        for member_id in mission.assigned_crew:
            self._crew.set_member_busy(member_id, False)
            # Update mission count in stats
            self._update_member_mission_stats(member_id)

        if success:
            mission.status = MissionStatus.COMPLETED

            # Add reward to inventory
            if mission.reward > 0:
                self._inventory.add_cash(mission.reward)

            # Handle repair mission - fix the car
            if mission.mission_type == MissionType.REPAIR and mission.car_to_repair:
                self._inventory.update_car_status(mission.car_to_repair, "available")
                self._inventory.set_car_damage_level(mission.car_to_repair, 0)

                # Use spare parts for repair
                try:
                    self._inventory.use_spare_parts("engine_parts", 1)
                except Exception:
                    pass  # Continue even if no parts available
        else:
            mission.status = MissionStatus.FAILED

        mission.completed_at = datetime.now()

        # Trigger notification callback
        if self._notification_callback:
            status_text = "completed successfully" if success else "failed"
            for member_id in mission.assigned_crew:
                self._notification_callback(
                    member_id,
                    f"Mission '{mission.name}' {status_text}"
                )

        return mission

    def _update_member_mission_stats(self, member_id: str):
        """Update member's mission completion statistics."""
        # This could integrate with a stats tracking system
        pass

    def list_active_missions(self) -> List[Mission]:
        """
        Get all active (in-progress) missions.

        Returns:
            List of in-progress Mission objects.
        """
        return [
            m for m in self._missions.values()
            if m.status == MissionStatus.IN_PROGRESS
        ]

    def list_pending_missions(self) -> List[Mission]:
        """
        Get all pending missions.

        Returns:
            List of pending Mission objects.
        """
        return [
            m for m in self._missions.values()
            if m.status == MissionStatus.PENDING
        ]

    def list_all_missions(self) -> List[Mission]:
        """
        Get all missions.

        Returns:
            List of all Mission objects.
        """
        return list(self._missions.values())

    def get_missions_by_type(self, mission_type: str) -> List[Mission]:
        """
        Get all missions of a specific type.

        Args:
            mission_type: The mission type to filter by.

        Returns:
            List of Mission objects of the specified type.
        """
        mission_type_enum = self._validate_and_get_mission_type(mission_type)
        return [
            m for m in self._missions.values()
            if m.mission_type == mission_type_enum
        ]

    def create_repair_mission(
        self,
        car_id: str,
        name: Optional[str] = None
    ) -> Mission:
        """
        Create a repair mission for a damaged car.

        Business Rule: Repair missions require a mechanic.

        Args:
            car_id: The car to repair.
            name: Optional mission name.

        Returns:
            The created Mission object.

        Raises:
            CarNotFoundError: If car doesn't exist.
        """
        # Verify car exists
        car = self._inventory.get_car(car_id)

        if name is None:
            name = f"Repair {car.make} {car.model}"

        return self.create_mission(
            name=name,
            mission_type="repair",
            reward=100.0,  # Base repair reward
            car_to_repair=car_id
        )

    def cancel_mission(self, mission_id: str) -> Mission:
        """
        Cancel a pending mission.

        Args:
            mission_id: The mission to cancel.

        Returns:
            The cancelled Mission object.

        Raises:
            MissionNotFoundError: If mission doesn't exist.
            MissionAlreadyStartedError: If mission already started.
        """
        if mission_id not in self._missions:
            raise MissionNotFoundError(mission_id)

        mission = self._missions[mission_id]

        if mission.status == MissionStatus.IN_PROGRESS:
            raise MissionAlreadyStartedError(mission_id)

        mission.status = MissionStatus.FAILED
        return mission

    def _validate_and_get_mission_type(self, mission_type: str) -> MissionType:
        """
        Validate a mission type string.

        Args:
            mission_type: The type string to validate.

        Returns:
            The corresponding MissionType enum.

        Raises:
            InvalidMissionTypeError: If type is invalid.
        """
        if not mission_type or not isinstance(mission_type, str):
            raise InvalidMissionTypeError(str(mission_type))

        try:
            return MissionType(mission_type.lower().strip())
        except ValueError:
            raise InvalidMissionTypeError(mission_type)
