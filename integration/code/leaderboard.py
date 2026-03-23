"""
Leaderboard Module (Custom) - Tracks crew rankings and statistics.

Responsibilities:
- Maintain overall crew leaderboard
- Track win/loss ratios
- Calculate total earnings
- Provide ranking statistics
"""

from typing import Dict, List, Optional

try:
    from .models import MemberStats
    from .results import ResultsModule
except ImportError:
    from models import MemberStats
    from results import ResultsModule


class LeaderboardModule:
    """
    Tracks and displays crew member rankings and statistics.

    This is a custom module that aggregates data from the Results module
    to provide comprehensive leaderboard functionality.

    Dependencies:
    - ResultsModule: For accessing race results and statistics
    """

    def __init__(self, results_module: ResultsModule):
        """
        Initialize leaderboard with results module reference.

        Args:
            results_module: For accessing race results.
        """
        self._results = results_module
        self._custom_stats: Dict[str, dict] = {}

    def update_leaderboard(self, member_id: str, stats: MemberStats) -> dict:
        """
        Update leaderboard entry for a member.

        Args:
            member_id: The member's ID.
            stats: The member's statistics.

        Returns:
            Updated leaderboard entry.
        """
        entry = {
            "member_id": member_id,
            "races_participated": stats.races_participated,
            "races_won": stats.races_won,
            "total_earnings": stats.total_earnings,
            "ranking_points": stats.ranking_points,
            "win_ratio": self.calculate_win_ratio(member_id),
            "missions_completed": stats.missions_completed
        }

        self._custom_stats[member_id] = entry
        return entry

    def get_top_racers(self, count: int = 10) -> List[MemberStats]:
        """
        Get the top racers by ranking points.

        Args:
            count: Number of top racers to return.

        Returns:
            List of top MemberStats sorted by ranking points.
        """
        all_rankings = self._results.get_rankings()
        return all_rankings[:count]

    def get_member_stats(self, member_id: str) -> MemberStats:
        """
        Get comprehensive statistics for a member.

        Args:
            member_id: The member's ID.

        Returns:
            MemberStats object for the member.
        """
        return self._results.get_member_stats(member_id)

    def calculate_win_ratio(self, member_id: str) -> float:
        """
        Calculate win ratio for a member.

        Args:
            member_id: The member's ID.

        Returns:
            Win ratio (0.0 to 1.0).
        """
        stats = self._results.get_member_stats(member_id)

        if stats.races_participated == 0:
            return 0.0

        return stats.races_won / stats.races_participated

    def get_total_earnings(self, member_id: str) -> float:
        """
        Get total earnings for a member.

        Args:
            member_id: The member's ID.

        Returns:
            Total earnings amount.
        """
        stats = self._results.get_member_stats(member_id)
        return stats.total_earnings

    def get_leaderboard(self, sort_by: str = "ranking_points") -> List[dict]:
        """
        Get the full leaderboard sorted by specified criterion.

        Args:
            sort_by: Field to sort by (ranking_points, total_earnings, races_won, win_ratio).

        Returns:
            List of leaderboard entries.
        """
        all_stats = self._results.get_rankings()

        leaderboard = []
        for stats in all_stats:
            entry = {
                "member_id": stats.member_id,
                "races_participated": stats.races_participated,
                "races_won": stats.races_won,
                "total_earnings": stats.total_earnings,
                "ranking_points": stats.ranking_points,
                "win_ratio": self.calculate_win_ratio(stats.member_id),
                "missions_completed": stats.missions_completed
            }
            leaderboard.append(entry)

        # Sort by specified criterion
        sort_key_map = {
            "ranking_points": lambda x: x["ranking_points"],
            "total_earnings": lambda x: x["total_earnings"],
            "races_won": lambda x: x["races_won"],
            "win_ratio": lambda x: x["win_ratio"],
            "races_participated": lambda x: x["races_participated"]
        }

        sort_key = sort_key_map.get(sort_by, sort_key_map["ranking_points"])
        leaderboard.sort(key=sort_key, reverse=True)

        # Add rank to each entry
        for i, entry in enumerate(leaderboard, 1):
            entry["rank"] = i

        return leaderboard

    def get_member_rank(self, member_id: str) -> int:
        """
        Get a member's current rank on the leaderboard.

        Args:
            member_id: The member's ID.

        Returns:
            Rank position (1-indexed, 0 if not ranked).
        """
        leaderboard = self.get_leaderboard()

        for entry in leaderboard:
            if entry["member_id"] == member_id:
                return entry["rank"]

        return 0

    def get_statistics_summary(self) -> dict:
        """
        Get overall leaderboard statistics summary.

        Returns:
            Dictionary with summary statistics.
        """
        all_stats = self._results.get_rankings()

        if not all_stats:
            return {
                "total_racers": 0,
                "total_races_completed": 0,
                "total_prize_distributed": 0.0,
                "average_earnings": 0.0,
                "top_earner": None,
                "most_wins": None
            }

        total_races = sum(s.races_participated for s in all_stats)
        total_earnings = sum(s.total_earnings for s in all_stats)
        top_earner = max(all_stats, key=lambda x: x.total_earnings)
        most_wins = max(all_stats, key=lambda x: x.races_won)

        return {
            "total_racers": len(all_stats),
            "total_races_completed": total_races,
            "total_prize_distributed": total_earnings,
            "average_earnings": total_earnings / len(all_stats) if all_stats else 0,
            "top_earner": {
                "member_id": top_earner.member_id,
                "earnings": top_earner.total_earnings
            },
            "most_wins": {
                "member_id": most_wins.member_id,
                "wins": most_wins.races_won
            }
        }

    def compare_members(self, member_id_1: str, member_id_2: str) -> dict:
        """
        Compare statistics between two members.

        Args:
            member_id_1: First member's ID.
            member_id_2: Second member's ID.

        Returns:
            Comparison dictionary.
        """
        stats_1 = self._results.get_member_stats(member_id_1)
        stats_2 = self._results.get_member_stats(member_id_2)

        return {
            "member_1": {
                "member_id": member_id_1,
                "races_won": stats_1.races_won,
                "total_earnings": stats_1.total_earnings,
                "ranking_points": stats_1.ranking_points,
                "win_ratio": self.calculate_win_ratio(member_id_1)
            },
            "member_2": {
                "member_id": member_id_2,
                "races_won": stats_2.races_won,
                "total_earnings": stats_2.total_earnings,
                "ranking_points": stats_2.ranking_points,
                "win_ratio": self.calculate_win_ratio(member_id_2)
            },
            "comparison": {
                "more_wins": member_id_1 if stats_1.races_won > stats_2.races_won else member_id_2,
                "higher_earnings": member_id_1 if stats_1.total_earnings > stats_2.total_earnings else member_id_2,
                "higher_rank": member_id_1 if stats_1.ranking_points > stats_2.ranking_points else member_id_2
            }
        }
