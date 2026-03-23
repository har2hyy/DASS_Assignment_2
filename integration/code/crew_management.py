"""
Crew Management Module - Manages roles and skill levels.

Responsibilities:
- Assign roles to registered members
- Update skill levels
- Track member roles and skills
- List members by role
- Validate role requirements
"""

from typing import Dict, List, Optional

try:
    from .models import CrewMember, Role
    from .registration import RegistrationModule
    from .exceptions import (
        MemberNotFoundError,
        InvalidRoleError,
        RoleNotAssignedError,
        InvalidSkillLevelError
    )
except ImportError:
    from models import CrewMember, Role
    from registration import RegistrationModule
    from exceptions import (
        MemberNotFoundError,
        InvalidRoleError,
        RoleNotAssignedError,
        InvalidSkillLevelError
    )


class CrewManagementModule:
    """
    Manages crew member roles and skill levels.

    This module depends on RegistrationModule - a member must be
    registered before a role can be assigned.
    """

    VALID_ROLES = [Role.DRIVER, Role.MECHANIC, Role.STRATEGIST]
    MIN_SKILL_LEVEL = 1
    MAX_SKILL_LEVEL = 10

    def __init__(self, registration_module: RegistrationModule):
        """
        Initialize crew management with a registration module reference.

        Args:
            registration_module: The registration module for member validation.
        """
        self._registration = registration_module

    def assign_role(self, member_id: str, role: str) -> CrewMember:
        """
        Assign a role to a registered member.

        Business Rule: A crew member MUST be registered before a role can be assigned.

        Args:
            member_id: The unique identifier of the member.
            role: The role to assign (driver, mechanic, strategist).

        Returns:
            The updated CrewMember object.

        Raises:
            MemberNotFoundError: If member is not registered.
            InvalidRoleError: If role is not valid.
        """
        # Validate member exists (Business Rule)
        if not self._registration.validate_member_exists(member_id):
            raise MemberNotFoundError(member_id)

        # Validate role
        role_enum = self._validate_and_get_role(role)

        # Update member's role
        member = self._registration.get_member(member_id)
        member.role = role_enum

        return member

    def update_skill_level(self, member_id: str, skill_level: int) -> CrewMember:
        """
        Update a member's skill level.

        Args:
            member_id: The unique identifier of the member.
            skill_level: The new skill level (1-10).

        Returns:
            The updated CrewMember object.

        Raises:
            MemberNotFoundError: If member is not registered.
            InvalidSkillLevelError: If skill level is out of range.
        """
        # Validate member exists
        if not self._registration.validate_member_exists(member_id):
            raise MemberNotFoundError(member_id)

        # Validate skill level
        if not isinstance(skill_level, int):
            raise InvalidSkillLevelError(skill_level)
        if skill_level < self.MIN_SKILL_LEVEL or skill_level > self.MAX_SKILL_LEVEL:
            raise InvalidSkillLevelError(skill_level)

        # Update skill level
        member = self._registration.get_member(member_id)
        member.skill_level = skill_level

        return member

    def get_member_role(self, member_id: str) -> Optional[Role]:
        """
        Get a member's current role.

        Args:
            member_id: The unique identifier of the member.

        Returns:
            The member's Role, or None if no role assigned.

        Raises:
            MemberNotFoundError: If member is not registered.
        """
        if not self._registration.validate_member_exists(member_id):
            raise MemberNotFoundError(member_id)

        member = self._registration.get_member(member_id)
        return member.role

    def get_skill_level(self, member_id: str) -> int:
        """
        Get a member's current skill level.

        Args:
            member_id: The unique identifier of the member.

        Returns:
            The member's skill level.

        Raises:
            MemberNotFoundError: If member is not registered.
        """
        if not self._registration.validate_member_exists(member_id):
            raise MemberNotFoundError(member_id)

        member = self._registration.get_member(member_id)
        return member.skill_level

    def list_members_by_role(self, role: str) -> List[CrewMember]:
        """
        Get all members with a specific role.

        Args:
            role: The role to filter by.

        Returns:
            List of CrewMember objects with the specified role.

        Raises:
            InvalidRoleError: If role is not valid.
        """
        role_enum = self._validate_and_get_role(role)

        return [
            m for m in self._registration.list_active_members()
            if m.role == role_enum
        ]

    def list_available_members_by_role(self, role: str) -> List[CrewMember]:
        """
        Get all available (not busy) members with a specific role.

        Args:
            role: The role to filter by.

        Returns:
            List of available CrewMember objects with the specified role.

        Raises:
            InvalidRoleError: If role is not valid.
        """
        role_enum = self._validate_and_get_role(role)

        return [
            m for m in self._registration.list_active_members()
            if m.role == role_enum and not m.is_busy
        ]

    def validate_role(self, member_id: str, expected_role: str) -> bool:
        """
        Check if a member has a specific role.

        Args:
            member_id: The unique identifier of the member.
            expected_role: The role to check for.

        Returns:
            True if member has the expected role.

        Raises:
            MemberNotFoundError: If member is not registered.
            InvalidRoleError: If expected_role is not valid.
        """
        if not self._registration.validate_member_exists(member_id):
            raise MemberNotFoundError(member_id)

        role_enum = self._validate_and_get_role(expected_role)
        member = self._registration.get_member(member_id)

        return member.role == role_enum

    def has_role_assigned(self, member_id: str) -> bool:
        """
        Check if a member has any role assigned.

        Args:
            member_id: The unique identifier of the member.

        Returns:
            True if member has a role, False otherwise.

        Raises:
            MemberNotFoundError: If member is not registered.
        """
        if not self._registration.validate_member_exists(member_id):
            raise MemberNotFoundError(member_id)

        member = self._registration.get_member(member_id)
        return member.role is not None

    def remove_role(self, member_id: str) -> CrewMember:
        """
        Remove a member's role assignment.

        Args:
            member_id: The unique identifier of the member.

        Returns:
            The updated CrewMember object.

        Raises:
            MemberNotFoundError: If member is not registered.
        """
        if not self._registration.validate_member_exists(member_id):
            raise MemberNotFoundError(member_id)

        member = self._registration.get_member(member_id)
        member.role = None

        return member

    def set_member_busy(self, member_id: str, busy: bool = True) -> CrewMember:
        """
        Set a member's busy status.

        Args:
            member_id: The unique identifier of the member.
            busy: Whether the member is busy.

        Returns:
            The updated CrewMember object.

        Raises:
            MemberNotFoundError: If member is not registered.
        """
        if not self._registration.validate_member_exists(member_id):
            raise MemberNotFoundError(member_id)

        member = self._registration.get_member(member_id)
        member.is_busy = busy

        return member

    def is_member_available(self, member_id: str) -> bool:
        """
        Check if a member is available (not busy and active).

        Args:
            member_id: The unique identifier of the member.

        Returns:
            True if member is available.

        Raises:
            MemberNotFoundError: If member is not registered.
        """
        if not self._registration.validate_member_exists(member_id):
            raise MemberNotFoundError(member_id)

        member = self._registration.get_member(member_id)
        return member.is_active and not member.is_busy

    def get_role_count(self, role: str) -> int:
        """
        Get the count of members with a specific role.

        Args:
            role: The role to count.

        Returns:
            Count of members with the role.

        Raises:
            InvalidRoleError: If role is not valid.
        """
        return len(self.list_members_by_role(role))

    def get_available_role_count(self, role: str) -> int:
        """
        Get the count of available members with a specific role.

        Args:
            role: The role to count.

        Returns:
            Count of available members with the role.

        Raises:
            InvalidRoleError: If role is not valid.
        """
        return len(self.list_available_members_by_role(role))

    def _validate_and_get_role(self, role: str) -> Role:
        """
        Validate a role string and return the corresponding Role enum.

        Args:
            role: The role string to validate.

        Returns:
            The corresponding Role enum.

        Raises:
            InvalidRoleError: If role is not valid.
        """
        if not role or not isinstance(role, str):
            raise InvalidRoleError(str(role))

        role_lower = role.lower().strip()
        try:
            return Role(role_lower)
        except ValueError:
            raise InvalidRoleError(role)
