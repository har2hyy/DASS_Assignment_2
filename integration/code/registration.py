"""
Registration Module - Handles crew member registration.

Responsibilities:
- Register new crew members with name
- Retrieve member information
- List all registered members
- Validate member existence
- Remove/deactivate members
"""

from datetime import datetime
from typing import Dict, List, Optional

try:
    from .models import CrewMember, generate_id
    from .exceptions import (
        MemberNotFoundError,
        MemberAlreadyExistsError,
        InvalidMemberDataError
    )
except ImportError:
    from models import CrewMember, generate_id
    from exceptions import (
        MemberNotFoundError,
        MemberAlreadyExistsError,
        InvalidMemberDataError
    )


class RegistrationModule:
    """
    Manages crew member registration.

    This module is the entry point for adding new members to the system.
    A member must be registered before any role can be assigned.
    """

    def __init__(self):
        """Initialize the registration module with an empty member registry."""
        self._members: Dict[str, CrewMember] = {}

    def register_member(self, name: str, member_id: Optional[str] = None) -> CrewMember:
        """
        Register a new crew member.

        Args:
            name: The name of the crew member (2-50 characters).
            member_id: Optional custom ID. Auto-generated if not provided.

        Returns:
            The newly registered CrewMember object.

        Raises:
            InvalidMemberDataError: If name is invalid.
            MemberAlreadyExistsError: If member_id already exists.
        """
        # Validate name
        if not name or not isinstance(name, str):
            raise InvalidMemberDataError("Name must be a non-empty string")

        name = name.strip()
        if len(name) < 2 or len(name) > 50:
            raise InvalidMemberDataError("Name must be between 2 and 50 characters")

        # Generate or validate member_id
        if member_id is None:
            member_id = generate_id()
        else:
            member_id = str(member_id).strip()
            if not member_id:
                raise InvalidMemberDataError("Member ID cannot be empty")

        # Check for duplicate
        if member_id in self._members:
            raise MemberAlreadyExistsError(member_id)

        # Create and store member
        member = CrewMember(
            member_id=member_id,
            name=name,
            registered_at=datetime.now()
        )
        self._members[member_id] = member

        return member

    def get_member(self, member_id: str) -> CrewMember:
        """
        Retrieve a member by ID.

        Args:
            member_id: The unique identifier of the member.

        Returns:
            The CrewMember object.

        Raises:
            MemberNotFoundError: If member doesn't exist.
        """
        if member_id not in self._members:
            raise MemberNotFoundError(member_id)
        return self._members[member_id]

    def list_all_members(self) -> List[CrewMember]:
        """
        Get a list of all registered members.

        Returns:
            List of all CrewMember objects.
        """
        return list(self._members.values())

    def list_active_members(self) -> List[CrewMember]:
        """
        Get a list of all active (non-deactivated) members.

        Returns:
            List of active CrewMember objects.
        """
        return [m for m in self._members.values() if m.is_active]

    def validate_member_exists(self, member_id: str) -> bool:
        """
        Check if a member exists in the system.

        Args:
            member_id: The unique identifier to check.

        Returns:
            True if member exists, False otherwise.
        """
        return member_id in self._members

    def remove_member(self, member_id: str) -> bool:
        """
        Deactivate a member (soft delete).

        Args:
            member_id: The unique identifier of the member.

        Returns:
            True if successfully deactivated.

        Raises:
            MemberNotFoundError: If member doesn't exist.
        """
        if member_id not in self._members:
            raise MemberNotFoundError(member_id)

        self._members[member_id].is_active = False
        return True

    def delete_member(self, member_id: str) -> bool:
        """
        Permanently delete a member (hard delete).

        Args:
            member_id: The unique identifier of the member.

        Returns:
            True if successfully deleted.

        Raises:
            MemberNotFoundError: If member doesn't exist.
        """
        if member_id not in self._members:
            raise MemberNotFoundError(member_id)

        del self._members[member_id]
        return True

    def get_member_count(self) -> int:
        """
        Get the total number of registered members.

        Returns:
            Total count of members.
        """
        return len(self._members)

    def get_active_member_count(self) -> int:
        """
        Get the count of active members.

        Returns:
            Count of active members.
        """
        return len([m for m in self._members.values() if m.is_active])

    def update_member_name(self, member_id: str, new_name: str) -> CrewMember:
        """
        Update a member's name.

        Args:
            member_id: The unique identifier of the member.
            new_name: The new name for the member.

        Returns:
            The updated CrewMember object.

        Raises:
            MemberNotFoundError: If member doesn't exist.
            InvalidMemberDataError: If new name is invalid.
        """
        if member_id not in self._members:
            raise MemberNotFoundError(member_id)

        if not new_name or not isinstance(new_name, str):
            raise InvalidMemberDataError("Name must be a non-empty string")

        new_name = new_name.strip()
        if len(new_name) < 2 or len(new_name) > 50:
            raise InvalidMemberDataError("Name must be between 2 and 50 characters")

        self._members[member_id].name = new_name
        return self._members[member_id]

    def search_members_by_name(self, name_query: str) -> List[CrewMember]:
        """
        Search for members by name (case-insensitive partial match).

        Args:
            name_query: The search string.

        Returns:
            List of matching CrewMember objects.
        """
        query_lower = name_query.lower()
        return [
            m for m in self._members.values()
            if query_lower in m.name.lower()
        ]
