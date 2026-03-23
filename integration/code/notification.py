"""
Notification Module (Custom) - Sends alerts and notifications.

Responsibilities:
- Send race alerts (scheduled, started, completed)
- Send mission notifications
- Send low inventory alerts
- Send result notifications
- Track notification history
"""

from datetime import datetime
from typing import Dict, List, Optional, Callable

try:
    from .models import Notification, NotificationType, generate_id
except ImportError:
    from models import Notification, NotificationType, generate_id


class NotificationModule:
    """
    Manages system notifications and alerts.

    This is a custom module that integrates with other modules
    through callbacks to send appropriate notifications.
    """

    def __init__(self):
        """Initialize notification module."""
        self._notifications: Dict[str, Notification] = {}
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, recipient_id: str, callback: Callable):
        """
        Subscribe to notifications for a recipient.

        Args:
            recipient_id: The recipient's ID.
            callback: Function to call when notification is sent.
        """
        if recipient_id not in self._subscribers:
            self._subscribers[recipient_id] = []
        self._subscribers[recipient_id].append(callback)

    def unsubscribe(self, recipient_id: str, callback: Callable):
        """
        Unsubscribe from notifications.

        Args:
            recipient_id: The recipient's ID.
            callback: The callback to remove.
        """
        if recipient_id in self._subscribers:
            self._subscribers[recipient_id] = [
                cb for cb in self._subscribers[recipient_id] if cb != callback
            ]

    def _send_notification(
        self,
        notification_type: NotificationType,
        recipient_id: str,
        message: str
    ) -> Notification:
        """
        Internal method to create and send a notification.

        Args:
            notification_type: Type of notification.
            recipient_id: The recipient's ID.
            message: Notification message.

        Returns:
            The created Notification object.
        """
        notification = Notification(
            notification_id=generate_id(),
            notification_type=notification_type,
            recipient_id=recipient_id,
            message=message,
            created_at=datetime.now()
        )

        self._notifications[notification.notification_id] = notification

        # Notify subscribers
        if recipient_id in self._subscribers:
            for callback in self._subscribers[recipient_id]:
                try:
                    callback(notification)
                except Exception:
                    pass  # Don't let callback errors break notification flow

        return notification

    def send_race_alert(
        self,
        race_id: str,
        member_ids: List[str],
        alert_type: str = "scheduled"
    ) -> List[Notification]:
        """
        Send race alerts to specified members.

        Args:
            race_id: The race ID.
            member_ids: List of member IDs to notify.
            alert_type: Type of alert (scheduled, started, completed).

        Returns:
            List of created Notification objects.
        """
        notifications = []

        type_mapping = {
            "scheduled": NotificationType.RACE_SCHEDULED,
            "started": NotificationType.RACE_STARTED,
            "completed": NotificationType.RACE_COMPLETED
        }

        notification_type = type_mapping.get(
            alert_type.lower(),
            NotificationType.RACE_SCHEDULED
        )

        message_templates = {
            "scheduled": f"New race scheduled! Race ID: {race_id}",
            "started": f"Race {race_id} has started!",
            "completed": f"Race {race_id} has been completed!"
        }

        message = message_templates.get(
            alert_type.lower(),
            f"Race update: {race_id}"
        )

        for member_id in member_ids:
            notification = self._send_notification(
                notification_type,
                member_id,
                message
            )
            notifications.append(notification)

        return notifications

    def send_mission_alert(
        self,
        mission_id: str,
        crew_ids: List[str],
        mission_name: str = ""
    ) -> List[Notification]:
        """
        Send mission assignment alerts to crew members.

        Args:
            mission_id: The mission ID.
            crew_ids: List of crew member IDs.
            mission_name: Name of the mission.

        Returns:
            List of created Notification objects.
        """
        notifications = []

        message = f"You have been assigned to mission: {mission_name or mission_id}"

        for crew_id in crew_ids:
            notification = self._send_notification(
                NotificationType.MISSION_ASSIGNED,
                crew_id,
                message
            )
            notifications.append(notification)

        return notifications

    def send_mission_completed_alert(
        self,
        mission_id: str,
        crew_ids: List[str],
        success: bool,
        mission_name: str = ""
    ) -> List[Notification]:
        """
        Send mission completion alerts.

        Args:
            mission_id: The mission ID.
            crew_ids: List of crew member IDs.
            success: Whether mission was successful.
            mission_name: Name of the mission.

        Returns:
            List of created Notification objects.
        """
        notifications = []

        status = "completed successfully" if success else "failed"
        message = f"Mission '{mission_name or mission_id}' has {status}"

        for crew_id in crew_ids:
            notification = self._send_notification(
                NotificationType.MISSION_COMPLETED,
                crew_id,
                message
            )
            notifications.append(notification)

        return notifications

    def send_low_inventory_alert(
        self,
        item_type: str,
        item_details: str,
        recipient_ids: Optional[List[str]] = None
    ) -> List[Notification]:
        """
        Send low inventory alerts.

        Args:
            item_type: Type of item (parts, cash).
            item_details: Details about the low item.
            recipient_ids: Optional list of recipients (broadcasts to all if None).

        Returns:
            List of created Notification objects.
        """
        notifications = []

        if item_type == "cash":
            message = f"Warning: Low cash balance! Current: ${item_details}"
            notification_type = NotificationType.LOW_CASH
        else:
            message = f"Warning: Low inventory! {item_type}: {item_details}"
            notification_type = NotificationType.LOW_INVENTORY

        # If no recipients specified, create a system notification
        if not recipient_ids:
            recipient_ids = ["system"]

        for recipient_id in recipient_ids:
            notification = self._send_notification(
                notification_type,
                recipient_id,
                message
            )
            notifications.append(notification)

        return notifications

    def send_result_notification(
        self,
        member_id: str,
        result_message: str
    ) -> Notification:
        """
        Send race result notification to a member.

        Args:
            member_id: The member's ID.
            result_message: The result message.

        Returns:
            The created Notification object.
        """
        return self._send_notification(
            NotificationType.RANKING_UPDATE,
            member_id,
            result_message
        )

    def send_ranking_update(
        self,
        member_id: str,
        new_rank: int,
        old_rank: Optional[int] = None
    ) -> Notification:
        """
        Send ranking update notification.

        Args:
            member_id: The member's ID.
            new_rank: New ranking position.
            old_rank: Previous ranking position.

        Returns:
            The created Notification object.
        """
        if old_rank:
            change = old_rank - new_rank
            direction = "up" if change > 0 else "down"
            message = f"Your ranking has moved {direction}! New rank: #{new_rank}"
        else:
            message = f"You are now ranked #{new_rank}!"

        return self._send_notification(
            NotificationType.RANKING_UPDATE,
            member_id,
            message
        )

    def get_notifications(self, recipient_id: str) -> List[Notification]:
        """
        Get all notifications for a recipient.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            List of Notification objects.
        """
        return [
            n for n in self._notifications.values()
            if n.recipient_id == recipient_id
        ]

    def get_unread_notifications(self, recipient_id: str) -> List[Notification]:
        """
        Get unread notifications for a recipient.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            List of unread Notification objects.
        """
        return [
            n for n in self._notifications.values()
            if n.recipient_id == recipient_id and not n.is_read
        ]

    def mark_as_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: The notification ID.

        Returns:
            True if marked successfully.
        """
        if notification_id in self._notifications:
            self._notifications[notification_id].is_read = True
            return True
        return False

    def mark_all_as_read(self, recipient_id: str) -> int:
        """
        Mark all notifications for a recipient as read.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            Number of notifications marked as read.
        """
        count = 0
        for notification in self._notifications.values():
            if notification.recipient_id == recipient_id and not notification.is_read:
                notification.is_read = True
                count += 1
        return count

    def get_notification_count(self, recipient_id: str) -> dict:
        """
        Get notification counts for a recipient.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            Dictionary with total and unread counts.
        """
        all_notifications = self.get_notifications(recipient_id)
        unread = [n for n in all_notifications if not n.is_read]

        return {
            "total": len(all_notifications),
            "unread": len(unread),
            "read": len(all_notifications) - len(unread)
        }

    def get_notifications_by_type(
        self,
        notification_type: NotificationType
    ) -> List[Notification]:
        """
        Get all notifications of a specific type.

        Args:
            notification_type: The notification type to filter by.

        Returns:
            List of Notification objects.
        """
        return [
            n for n in self._notifications.values()
            if n.notification_type == notification_type
        ]

    def delete_notification(self, notification_id: str) -> bool:
        """
        Delete a notification.

        Args:
            notification_id: The notification ID.

        Returns:
            True if deleted successfully.
        """
        if notification_id in self._notifications:
            del self._notifications[notification_id]
            return True
        return False

    def clear_notifications(self, recipient_id: str) -> int:
        """
        Clear all notifications for a recipient.

        Args:
            recipient_id: The recipient's ID.

        Returns:
            Number of notifications cleared.
        """
        to_delete = [
            nid for nid, n in self._notifications.items()
            if n.recipient_id == recipient_id
        ]

        for nid in to_delete:
            del self._notifications[nid]

        return len(to_delete)

    def get_all_notifications(self) -> List[Notification]:
        """
        Get all notifications in the system.

        Returns:
            List of all Notification objects.
        """
        return list(self._notifications.values())
