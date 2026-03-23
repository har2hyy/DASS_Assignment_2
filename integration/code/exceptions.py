"""
Custom exceptions for the StreetRace Manager system.
Provides specific error handling for various business rule violations.
"""


class StreetRaceError(Exception):
    """Base exception for all StreetRace Manager errors."""
    pass


# Registration Exceptions
class MemberNotFoundError(StreetRaceError):
    """Raised when a crew member is not found in the system."""
    def __init__(self, member_id: str):
        self.member_id = member_id
        super().__init__(f"Member with ID '{member_id}' not found")


class MemberAlreadyExistsError(StreetRaceError):
    """Raised when attempting to register an already existing member."""
    def __init__(self, member_id: str):
        self.member_id = member_id
        super().__init__(f"Member with ID '{member_id}' already exists")


class InvalidMemberDataError(StreetRaceError):
    """Raised when member data is invalid."""
    pass


# Crew Management Exceptions
class InvalidRoleError(StreetRaceError):
    """Raised when an invalid role is specified."""
    def __init__(self, role: str):
        self.role = role
        super().__init__(f"Invalid role: '{role}'. Valid roles are: driver, mechanic, strategist")


class RoleNotAssignedError(StreetRaceError):
    """Raised when a member doesn't have any role assigned."""
    def __init__(self, member_id: str):
        self.member_id = member_id
        super().__init__(f"Member '{member_id}' has no role assigned")


class InvalidSkillLevelError(StreetRaceError):
    """Raised when an invalid skill level is specified."""
    def __init__(self, skill_level: int):
        self.skill_level = skill_level
        super().__init__(f"Invalid skill level: {skill_level}. Must be between 1 and 10")


# Inventory Exceptions
class CarNotFoundError(StreetRaceError):
    """Raised when a car is not found in inventory."""
    def __init__(self, car_id: str):
        self.car_id = car_id
        super().__init__(f"Car with ID '{car_id}' not found")


class CarNotAvailableError(StreetRaceError):
    """Raised when a car is not available for use."""
    def __init__(self, car_id: str, status: str):
        self.car_id = car_id
        self.status = status
        super().__init__(f"Car '{car_id}' is not available. Current status: {status}")


class InsufficientFundsError(StreetRaceError):
    """Raised when there are insufficient funds for an operation."""
    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        super().__init__(f"Insufficient funds. Required: ${required:.2f}, Available: ${available:.2f}")


class InsufficientPartsError(StreetRaceError):
    """Raised when there are insufficient spare parts."""
    def __init__(self, part_name: str, required: int, available: int):
        self.part_name = part_name
        self.required = required
        self.available = available
        super().__init__(f"Insufficient {part_name}. Required: {required}, Available: {available}")


class InvalidCarDataError(StreetRaceError):
    """Raised when car data is invalid."""
    pass


# Race Management Exceptions
class RaceNotFoundError(StreetRaceError):
    """Raised when a race is not found."""
    def __init__(self, race_id: str):
        self.race_id = race_id
        super().__init__(f"Race with ID '{race_id}' not found")


class RaceAlreadyStartedError(StreetRaceError):
    """Raised when trying to modify an already started race."""
    def __init__(self, race_id: str):
        self.race_id = race_id
        super().__init__(f"Race '{race_id}' has already started")


class RaceNotStartedError(StreetRaceError):
    """Raised when trying to complete a race that hasn't started."""
    def __init__(self, race_id: str):
        self.race_id = race_id
        super().__init__(f"Race '{race_id}' has not started yet")


class NotADriverError(StreetRaceError):
    """Raised when a non-driver member tries to enter a race."""
    def __init__(self, member_id: str, current_role: str):
        self.member_id = member_id
        self.current_role = current_role
        super().__init__(f"Member '{member_id}' cannot race. Role is '{current_role}', must be 'driver'")


class ParticipantAlreadyInRaceError(StreetRaceError):
    """Raised when a participant is already in the race."""
    def __init__(self, member_id: str, race_id: str):
        self.member_id = member_id
        self.race_id = race_id
        super().__init__(f"Member '{member_id}' is already a participant in race '{race_id}'")


class CarAlreadyInRaceError(StreetRaceError):
    """Raised when a car is already being used in the race."""
    def __init__(self, car_id: str, race_id: str):
        self.car_id = car_id
        self.race_id = race_id
        super().__init__(f"Car '{car_id}' is already being used in race '{race_id}'")


class MinimumParticipantsError(StreetRaceError):
    """Raised when a race doesn't have enough participants to start."""
    def __init__(self, race_id: str, current: int, minimum: int):
        self.race_id = race_id
        self.current = current
        self.minimum = minimum
        super().__init__(f"Race '{race_id}' needs at least {minimum} participants. Current: {current}")


# Results Exceptions
class InvalidRaceResultError(StreetRaceError):
    """Raised when race result data is invalid."""
    pass


class ResultAlreadyRecordedError(StreetRaceError):
    """Raised when a result has already been recorded for a race."""
    def __init__(self, race_id: str):
        self.race_id = race_id
        super().__init__(f"Result for race '{race_id}' has already been recorded")


# Mission Exceptions
class MissionNotFoundError(StreetRaceError):
    """Raised when a mission is not found."""
    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        super().__init__(f"Mission with ID '{mission_id}' not found")


class RequiredRoleUnavailableError(StreetRaceError):
    """Raised when a required role is unavailable for a mission."""
    def __init__(self, role: str):
        self.role = role
        super().__init__(f"Required role '{role}' is not available for this mission")


class MissionAlreadyStartedError(StreetRaceError):
    """Raised when trying to modify an already started mission."""
    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        super().__init__(f"Mission '{mission_id}' has already started")


class MissionNotStartedError(StreetRaceError):
    """Raised when trying to complete a mission that hasn't started."""
    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        super().__init__(f"Mission '{mission_id}' has not started yet")


class CrewMemberBusyError(StreetRaceError):
    """Raised when a crew member is already assigned to another active mission."""
    def __init__(self, member_id: str):
        self.member_id = member_id
        super().__init__(f"Crew member '{member_id}' is already assigned to an active mission")


class InvalidMissionTypeError(StreetRaceError):
    """Raised when an invalid mission type is specified."""
    def __init__(self, mission_type: str):
        self.mission_type = mission_type
        super().__init__(f"Invalid mission type: '{mission_type}'. Valid types are: delivery, rescue, repair, heist")
