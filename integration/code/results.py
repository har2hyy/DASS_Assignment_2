"""
Results Module - Records race outcomes and handles prize money.

Responsibilities:
- Record race outcomes
- Calculate prize distribution
- Update member rankings
- Track race history
- Handle prize money (updates inventory)
"""

from datetime import datetime
from typing import Dict, List, Optional

try:
    from .models import RaceResult, MemberStats, generate_id
    from .race_management import RaceManagementModule
    from .inventory import InventoryModule
    from .exceptions import (
        RaceNotFoundError,
        InvalidRaceResultError,
        ResultAlreadyRecordedError
    )
except ImportError:
    from models import RaceResult, MemberStats, generate_id
    from race_management import RaceManagementModule
    from inventory import InventoryModule
    from exceptions import (
        RaceNotFoundError,
        InvalidRaceResultError,
        ResultAlreadyRecordedError
    )


class ResultsModule:
    """
    Manages race results, rankings, and prize distribution.

    Dependencies:
    - RaceManagementModule: To get race details
    - InventoryModule: To update cash balance with prize money
    """

    # Prize distribution percentages by position
    PRIZE_DISTRIBUTION = {
        1: 0.50,  # 1st place gets 50%
        2: 0.30,  # 2nd place gets 30%
        3: 0.15,  # 3rd place gets 15%
        # Remaining 5% goes to the house/organizer
    }

    # Ranking points by position
    RANKING_POINTS = {
        1: 25,
        2: 18,
        3: 15,
        4: 12,
        5: 10,
        6: 8,
        7: 6,
        8: 4,
        9: 2,
        10: 1
    }

    def __init__(
        self,
        race_management_module: RaceManagementModule,
        inventory_module: InventoryModule
    ):
        """
        Initialize results module with required dependencies.

        Args:
            race_management_module: For race details.
            inventory_module: For cash balance updates.
        """
        self._race_management = race_management_module
        self._inventory = inventory_module
        self._results: Dict[str, RaceResult] = {}
        self._member_stats: Dict[str, MemberStats] = {}
        self._leaderboard_callback = None
        self._notification_callback = None

    def set_leaderboard_callback(self, callback):
        """Set callback for leaderboard updates."""
        self._leaderboard_callback = callback

    def set_notification_callback(self, callback):
        """Set callback for result notifications."""
        self._notification_callback = callback

    def record_race_outcome(
        self,
        race_id: str,
        positions: Dict[int, str],
        damaged_cars: Optional[List[str]] = None
    ) -> RaceResult:
        """
        Record the outcome of a completed race.

        Business Rules:
        - Prize money updates the cash balance in Inventory
        - Rankings are updated based on positions

        Args:
            race_id: The completed race ID.
            positions: Dictionary mapping position (1, 2, 3...) to driver_id.
            damaged_cars: List of car IDs that were damaged.

        Returns:
            The created RaceResult object.

        Raises:
            RaceNotFoundError: If race doesn't exist.
            ResultAlreadyRecordedError: If result already recorded.
            InvalidRaceResultError: If positions data is invalid.
        """
        # Check if result already recorded
        if race_id in self._results:
            raise ResultAlreadyRecordedError(race_id)

        # Validate positions
        if not positions or not isinstance(positions, dict):
            raise InvalidRaceResultError("Positions must be a non-empty dictionary")

        # Get race details
        try:
            race = self._race_management.get_race_details(race_id)
        except RaceNotFoundError:
            raise

        # Calculate prize distribution
        prize_distribution = self._calculate_prize_distribution(
            race.prize_pool,
            positions
        )

        # Create result record
        result = RaceResult(
            race_id=race_id,
            positions=positions.copy(),
            prize_distribution=prize_distribution,
            damaged_cars=damaged_cars or [],
            recorded_at=datetime.now()
        )

        self._results[race_id] = result

        # Update rankings for all participants
        for position, driver_id in positions.items():
            self._update_member_ranking(driver_id, position, prize_distribution.get(driver_id, 0))

        # Update inventory cash balance with total prize money
        total_prize_paid = sum(prize_distribution.values())
        if total_prize_paid > 0:
            self._inventory.add_cash(total_prize_paid)

        # Trigger leaderboard update callback
        if self._leaderboard_callback:
            for driver_id in positions.values():
                stats = self.get_member_stats(driver_id)
                self._leaderboard_callback(driver_id, stats)

        # Trigger notification callback
        if self._notification_callback:
            for position, driver_id in positions.items():
                self._notification_callback(
                    driver_id,
                    f"Race completed! Position: {position}, Prize: ${prize_distribution.get(driver_id, 0):.2f}"
                )

        return result

    def _calculate_prize_distribution(
        self,
        prize_pool: float,
        positions: Dict[int, str]
    ) -> Dict[str, float]:
        """
        Calculate prize money for each position.

        Args:
            prize_pool: Total prize money.
            positions: Position to driver mapping.

        Returns:
            Dictionary mapping driver_id to prize amount.
        """
        distribution = {}

        for position, driver_id in positions.items():
            percentage = self.PRIZE_DISTRIBUTION.get(position, 0)
            prize_amount = prize_pool * percentage
            distribution[driver_id] = prize_amount

        return distribution

    def calculate_prize_money(self, position: int, base_prize: float) -> float:
        """
        Calculate prize money for a specific position.

        Args:
            position: The finishing position.
            base_prize: The total prize pool.

        Returns:
            Prize amount for the position.
        """
        percentage = self.PRIZE_DISTRIBUTION.get(position, 0)
        return base_prize * percentage

    def _update_member_ranking(
        self,
        member_id: str,
        position: int,
        prize_earned: float
    ) -> MemberStats:
        """
        Update a member's ranking statistics.

        Args:
            member_id: The member's ID.
            position: Their finishing position.
            prize_earned: Prize money earned.

        Returns:
            Updated MemberStats object.
        """
        if member_id not in self._member_stats:
            self._member_stats[member_id] = MemberStats(member_id=member_id)

        stats = self._member_stats[member_id]
        stats.races_participated += 1
        stats.total_earnings += prize_earned
        stats.ranking_points += self.RANKING_POINTS.get(position, 0)

        if position == 1:
            stats.races_won += 1

        return stats

    def update_member_ranking(
        self,
        member_id: str,
        result_data: dict
    ) -> MemberStats:
        """
        Manually update a member's ranking with result data.

        Args:
            member_id: The member's ID.
            result_data: Dictionary with 'position' and 'prize_earned'.

        Returns:
            Updated MemberStats object.
        """
        position = result_data.get('position', 0)
        prize_earned = result_data.get('prize_earned', 0.0)

        return self._update_member_ranking(member_id, position, prize_earned)

    def get_rankings(self) -> List[MemberStats]:
        """
        Get all member rankings sorted by ranking points.

        Returns:
            List of MemberStats sorted by ranking points (descending).
        """
        return sorted(
            self._member_stats.values(),
            key=lambda x: x.ranking_points,
            reverse=True
        )

    def get_member_stats(self, member_id: str) -> MemberStats:
        """
        Get statistics for a specific member.

        Args:
            member_id: The member's ID.

        Returns:
            MemberStats object (creates new if doesn't exist).
        """
        if member_id not in self._member_stats:
            self._member_stats[member_id] = MemberStats(member_id=member_id)
        return self._member_stats[member_id]

    def get_race_history(self, member_id: str) -> List[RaceResult]:
        """
        Get all race results for a specific member.

        Args:
            member_id: The member's ID.

        Returns:
            List of RaceResult objects the member participated in.
        """
        history = []
        for result in self._results.values():
            if member_id in result.positions.values():
                history.append(result)
        return history

    def get_race_result(self, race_id: str) -> RaceResult:
        """
        Get the result for a specific race.

        Args:
            race_id: The race ID.

        Returns:
            RaceResult object.

        Raises:
            RaceNotFoundError: If result not found.
        """
        if race_id not in self._results:
            raise RaceNotFoundError(race_id)
        return self._results[race_id]

    def process_car_damage(
        self,
        race_id: str,
        car_id: str,
        repair_cost: float = 0
    ) -> dict:
        """
        Process damage to a car from a race.

        Business Rule: If a car is damaged, it may require a mechanic mission.

        Args:
            race_id: The race ID where damage occurred.
            car_id: The damaged car's ID.
            repair_cost: Estimated repair cost.

        Returns:
            Dictionary with damage processing details.
        """
        # Update car status in inventory
        self._inventory.update_car_status(car_id, "damaged")

        # Attempt to use spare parts if available
        parts_used = []
        try:
            self._inventory.use_spare_parts("engine_parts", 1)
            parts_used.append("engine_parts")
        except Exception:
            pass

        return {
            "race_id": race_id,
            "car_id": car_id,
            "status": "damaged",
            "repair_cost": repair_cost,
            "parts_used": parts_used,
            "needs_mechanic_mission": True
        }

    def get_top_earners(self, limit: int = 10) -> List[MemberStats]:
        """
        Get top earners by total earnings.

        Args:
            limit: Maximum number of results.

        Returns:
            List of MemberStats sorted by total earnings.
        """
        return sorted(
            self._member_stats.values(),
            key=lambda x: x.total_earnings,
            reverse=True
        )[:limit]

    def get_top_winners(self, limit: int = 10) -> List[MemberStats]:
        """
        Get members with most race wins.

        Args:
            limit: Maximum number of results.

        Returns:
            List of MemberStats sorted by races won.
        """
        return sorted(
            self._member_stats.values(),
            key=lambda x: x.races_won,
            reverse=True
        )[:limit]

    def get_all_results(self) -> List[RaceResult]:
        """
        Get all recorded race results.

        Returns:
            List of all RaceResult objects.
        """
        return list(self._results.values())

    def get_total_prize_distributed(self) -> float:
        """
        Get the total prize money distributed across all races.

        Returns:
            Total prize money.
        """
        total = 0.0
        for result in self._results.values():
            total += sum(result.prize_distribution.values())
        return total
