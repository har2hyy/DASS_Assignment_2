"""
Data models for the StreetRace Manager system.
Contains dataclasses representing core entities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class Role(Enum):
    """Valid crew member roles."""
    DRIVER = "driver"
    MECHANIC = "mechanic"
    STRATEGIST = "strategist"


class CarStatus(Enum):
    """Valid car statuses."""
    AVAILABLE = "available"
    IN_RACE = "in_race"
    DAMAGED = "damaged"
    IN_REPAIR = "in_repair"


class RaceStatus(Enum):
    """Valid race statuses."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MissionStatus(Enum):
    """Valid mission statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class MissionType(Enum):
    """Valid mission types."""
    DELIVERY = "delivery"
    RESCUE = "rescue"
    REPAIR = "repair"
    HEIST = "heist"


class NotificationType(Enum):
    """Valid notification types."""
    RACE_SCHEDULED = "race_scheduled"
    RACE_STARTED = "race_started"
    RACE_COMPLETED = "race_completed"
    MISSION_ASSIGNED = "mission_assigned"
    MISSION_COMPLETED = "mission_completed"
    LOW_INVENTORY = "low_inventory"
    LOW_CASH = "low_cash"
    RANKING_UPDATE = "ranking_update"


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())[:8]


@dataclass
class CrewMember:
    """Represents a crew member in the system."""
    member_id: str
    name: str
    role: Optional[Role] = None
    skill_level: int = 1
    registered_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    is_busy: bool = False

    def __post_init__(self):
        if not self.member_id:
            self.member_id = generate_id()


@dataclass
class Car:
    """Represents a car in the inventory."""
    car_id: str
    make: str
    model: str
    year: int
    status: CarStatus = CarStatus.AVAILABLE
    performance_rating: int = 5
    damage_level: int = 0

    def __post_init__(self):
        if not self.car_id:
            self.car_id = generate_id()


@dataclass
class SparePart:
    """Represents a spare part in inventory."""
    name: str
    quantity: int
    unit_cost: float


@dataclass
class Tool:
    """Represents a tool in inventory."""
    name: str
    quantity: int
    condition: str = "good"


@dataclass
class RaceParticipant:
    """Represents a participant in a race."""
    driver_id: str
    car_id: str
    position: Optional[int] = None
    is_damaged: bool = False


@dataclass
class Race:
    """Represents a race."""
    race_id: str
    name: str
    race_type: str
    prize_pool: float
    status: RaceStatus = RaceStatus.SCHEDULED
    participants: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    min_participants: int = 2

    def __post_init__(self):
        if not self.race_id:
            self.race_id = generate_id()


@dataclass
class RaceResult:
    """Represents the result of a race."""
    race_id: str
    positions: dict  # {position: driver_id}
    prize_distribution: dict  # {driver_id: amount}
    damaged_cars: list  # [car_id, ...]
    recorded_at: datetime = field(default_factory=datetime.now)


@dataclass
class Mission:
    """Represents a mission."""
    mission_id: str
    name: str
    mission_type: MissionType
    required_roles: list  # [Role, ...]
    assigned_crew: list = field(default_factory=list)  # [member_id, ...]
    status: MissionStatus = MissionStatus.PENDING
    reward: float = 0.0
    car_to_repair: Optional[str] = None  # For repair missions
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.mission_id:
            self.mission_id = generate_id()


@dataclass
class MemberStats:
    """Represents statistics for a crew member."""
    member_id: str
    races_participated: int = 0
    races_won: int = 0
    total_earnings: float = 0.0
    missions_completed: int = 0
    ranking_points: int = 0


@dataclass
class Notification:
    """Represents a notification."""
    notification_id: str
    notification_type: NotificationType
    recipient_id: str
    message: str
    created_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False

    def __post_init__(self):
        if not self.notification_id:
            self.notification_id = generate_id()
