"""
StreetRace Manager - Main system orchestrator.

This module provides the main StreetRaceManager class that integrates
all modules and provides a unified interface for the system.
"""

from typing import Dict, List, Optional

try:
    from .models import (
        CrewMember, Car, Race, Mission, RaceResult, MemberStats,
        Role, CarStatus, RaceStatus, MissionStatus, MissionType
    )
    from .registration import RegistrationModule
    from .crew_management import CrewManagementModule
    from .inventory import InventoryModule
    from .race_management import RaceManagementModule
    from .results import ResultsModule
    from .mission_planning import MissionPlanningModule
    from .leaderboard import LeaderboardModule
    from .notification import NotificationModule
except ImportError:
    from models import (
        CrewMember, Car, Race, Mission, RaceResult, MemberStats,
        Role, CarStatus, RaceStatus, MissionStatus, MissionType
    )
    from registration import RegistrationModule
    from crew_management import CrewManagementModule
    from inventory import InventoryModule
    from race_management import RaceManagementModule
    from results import ResultsModule
    from mission_planning import MissionPlanningModule
    from leaderboard import LeaderboardModule
    from notification import NotificationModule


class StreetRaceManager:
    """
    Main orchestrator for the StreetRace Manager system.

    Integrates all modules and sets up proper communication
    between them through callbacks.
    """

    def __init__(self, initial_cash: float = 1000.0):
        """
        Initialize the StreetRace Manager with all modules.

        Args:
            initial_cash: Starting cash balance.
        """
        # Initialize modules in dependency order
        self.registration = RegistrationModule()
        self.crew_management = CrewManagementModule(self.registration)
        self.inventory = InventoryModule(initial_cash)
        self.race_management = RaceManagementModule(
            self.registration,
            self.crew_management,
            self.inventory
        )
        self.results = ResultsModule(
            self.race_management,
            self.inventory
        )
        self.mission_planning = MissionPlanningModule(
            self.crew_management,
            self.inventory
        )
        self.leaderboard = LeaderboardModule(self.results)
        self.notification = NotificationModule()

        # Set up inter-module callbacks
        self._setup_callbacks()

    def _setup_callbacks(self):
        """Configure callbacks between modules."""
        # Inventory low stock alerts -> Notification
        self.inventory.set_low_inventory_callback(
            lambda item_type, details: self.notification.send_low_inventory_alert(
                item_type, details
            )
        )

        # Race completed -> Results recording
        self.race_management.set_race_completed_callback(
            lambda race_id, positions, damaged: self.results.record_race_outcome(
                race_id, positions, damaged
            )
        )

        # Results recorded -> Leaderboard update
        self.results.set_leaderboard_callback(
            lambda member_id, stats: self.leaderboard.update_leaderboard(
                member_id, stats
            )
        )

        # Results -> Notification
        self.results.set_notification_callback(
            lambda member_id, message: self.notification.send_result_notification(
                member_id, message
            )
        )

        # Mission -> Notification
        self.mission_planning.set_notification_callback(
            lambda member_id, message: self.notification.send_result_notification(
                member_id, message
            )
        )

    # =================== CONVENIENCE METHODS ===================

    def register_and_assign_driver(
        self,
        name: str,
        skill_level: int = 5
    ) -> CrewMember:
        """
        Register a new crew member and assign them the driver role.

        Args:
            name: The name of the crew member.
            skill_level: The skill level (1-10).

        Returns:
            The registered CrewMember with driver role.
        """
        member = self.registration.register_member(name)
        self.crew_management.assign_role(member.member_id, "driver")
        self.crew_management.update_skill_level(member.member_id, skill_level)
        return member

    def register_and_assign_mechanic(
        self,
        name: str,
        skill_level: int = 5
    ) -> CrewMember:
        """
        Register a new crew member and assign them the mechanic role.

        Args:
            name: The name of the crew member.
            skill_level: The skill level (1-10).

        Returns:
            The registered CrewMember with mechanic role.
        """
        member = self.registration.register_member(name)
        self.crew_management.assign_role(member.member_id, "mechanic")
        self.crew_management.update_skill_level(member.member_id, skill_level)
        return member

    def register_and_assign_strategist(
        self,
        name: str,
        skill_level: int = 5
    ) -> CrewMember:
        """
        Register a new crew member and assign them the strategist role.

        Args:
            name: The name of the crew member.
            skill_level: The skill level (1-10).

        Returns:
            The registered CrewMember with strategist role.
        """
        member = self.registration.register_member(name)
        self.crew_management.assign_role(member.member_id, "strategist")
        self.crew_management.update_skill_level(member.member_id, skill_level)
        return member

    def setup_and_run_race(
        self,
        race_name: str,
        participants: List[Dict],
        prize_pool: float = 1000.0
    ) -> RaceResult:
        """
        Convenience method to create, populate, start, and complete a race.

        Args:
            race_name: Name of the race.
            participants: List of dicts with 'driver_id' and 'car_id'.
            prize_pool: Total prize money.

        Returns:
            The RaceResult object.
        """
        # Create race
        race = self.race_management.create_race(
            name=race_name,
            race_type="street",
            prize_pool=prize_pool
        )

        # Add participants
        for p in participants:
            self.race_management.add_participant(
                race.race_id,
                p['driver_id'],
                p['car_id']
            )

        # Start race
        self.race_management.start_race(race.race_id)

        # Generate positions (1st, 2nd, 3rd, etc.)
        positions = {}
        for i, p in enumerate(participants, 1):
            positions[i] = p['driver_id']

        # Complete race
        self.race_management.complete_race(race.race_id, positions)

        return self.results.get_race_result(race.race_id)

    def create_repair_mission_for_damaged_car(
        self,
        car_id: str,
        mechanic_id: str
    ) -> Mission:
        """
        Create and start a repair mission for a damaged car.

        Args:
            car_id: The damaged car's ID.
            mechanic_id: The mechanic to assign.

        Returns:
            The Mission object.
        """
        mission = self.mission_planning.create_repair_mission(car_id)
        self.mission_planning.assign_mission(mission.mission_id, [mechanic_id])
        self.mission_planning.start_mission(mission.mission_id)
        return mission

    def get_system_status(self) -> dict:
        """
        Get a summary of the system status.

        Returns:
            Dictionary with system statistics.
        """
        return {
            "registration": {
                "total_members": self.registration.get_member_count(),
                "active_members": self.registration.get_active_member_count()
            },
            "crew": {
                "drivers": self.crew_management.get_role_count("driver"),
                "mechanics": self.crew_management.get_role_count("mechanic"),
                "strategists": self.crew_management.get_role_count("strategist")
            },
            "inventory": self.inventory.get_inventory_summary(),
            "races": {
                "scheduled": len(self.race_management.get_races_by_status("scheduled")),
                "in_progress": len(self.race_management.get_races_by_status("in_progress")),
                "completed": len(self.race_management.get_races_by_status("completed"))
            },
            "missions": {
                "pending": len(self.mission_planning.list_pending_missions()),
                "active": len(self.mission_planning.list_active_missions())
            },
            "leaderboard": self.leaderboard.get_statistics_summary()
        }

    def get_member_full_profile(self, member_id: str) -> dict:
        """
        Get complete profile information for a member.

        Args:
            member_id: The member's ID.

        Returns:
            Dictionary with all member information.
        """
        member = self.registration.get_member(member_id)
        stats = self.results.get_member_stats(member_id)
        race_history = self.results.get_race_history(member_id)

        return {
            "member": {
                "id": member.member_id,
                "name": member.name,
                "role": member.role.value if member.role else None,
                "skill_level": member.skill_level,
                "is_active": member.is_active,
                "is_busy": member.is_busy,
                "registered_at": member.registered_at.isoformat()
            },
            "statistics": {
                "races_participated": stats.races_participated,
                "races_won": stats.races_won,
                "total_earnings": stats.total_earnings,
                "ranking_points": stats.ranking_points,
                "win_ratio": self.leaderboard.calculate_win_ratio(member_id)
            },
            "race_history_count": len(race_history),
            "current_rank": self.leaderboard.get_member_rank(member_id)
        }
