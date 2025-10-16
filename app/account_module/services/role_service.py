"""Role service."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.account_module.models.role import Role
from app.account_module.models.user_role_assignment import UserRoleAssignment
from app.account_module.schemas.role import RoleCreate, RoleUpdate
from app.account_module.schemas.user_role_assignment import UserRoleAssignmentCreate


class RoleService:                                            
    """Service for role operations."""

    @staticmethod
    async def create_role(db: AsyncSession, role_data: RoleCreate) -> Role:
        """
        Create a new role.

        Args:
            db: Database session
            role_data: Role creation data

        Returns:
            Role: Created role

        Raises:
            ValueError: If role name already exists
        """
        # Check if role already exists
        result = await db.execute(select(Role).where(Role.name == role_data.name))
        existing_role = result.scalar_one_or_none()

        if existing_role:
            raise ValueError("Role name already exists")

        role = Role(
            name=role_data.name,
            description=role_data.description
        )

        db.add(role)
        await db.flush()
        await db.refresh(role)

        return role

    @staticmethod
    async def get_role_by_id(db: AsyncSession, role_id: int) -> Optional[Role]:
        """
        Get role by ID.

        Args:
            db: Database session
            role_id: Role ID

        Returns:
            Optional[Role]: Role or None if not found
        """
        result = await db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_role_by_name(db: AsyncSession, name: str) -> Optional[Role]:
        """
        Get role by name.

        Args:
            db: Database session
            name: Role name

        Returns:
            Optional[Role]: Role or None if not found
        """
        result = await db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_roles(db: AsyncSession) -> List[Role]:
        """
        Get all roles.

        Args:
            db: Database session

        Returns:
            List[Role]: List of roles
        """
        result = await db.execute(select(Role))
        return list(result.scalars().all())

    @staticmethod
    async def update_role(db: AsyncSession, role_id: int, role_data: RoleUpdate) -> Optional[Role]:
        """
        Update role.

        Args:
            db: Database session
            role_id: Role ID
            role_data: Update data

        Returns:
            Optional[Role]: Updated role or None if not found
        """
        role = await RoleService.get_role_by_id(db, role_id)

        if not role:
            return None

        if role_data.name is not None:
            role.name = role_data.name
        if role_data.description is not None:
            role.description = role_data.description

        await db.flush()
        await db.refresh(role)

        return role

    @staticmethod
    async def delete_role(db: AsyncSession, role_id: int) -> bool:
        """
        Delete role.

        Args:
            db: Database session
            role_id: Role ID

        Returns:
            bool: True if deleted, False if not found
        """
        role = await RoleService.get_role_by_id(db, role_id)

        if not role:
            return False

        await db.delete(role)
        return True

    @staticmethod
    async def assign_role_to_user(
        db: AsyncSession,
        assignment_data: UserRoleAssignmentCreate
    ) -> UserRoleAssignment:
        """
        Assign a role to a user.

        Args:
            db: Database session
            assignment_data: Role assignment data

        Returns:
            UserRoleAssignment: Created assignment

        Raises:
            ValueError: If assignment already exists
        """
        # Check if assignment already exists
        query = select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == assignment_data.user_id,
            UserRoleAssignment.role_id == assignment_data.role_id
        )

        if assignment_data.hotel_id is not None:
            query = query.where(UserRoleAssignment.hotel_id ==
                                assignment_data.hotel_id)
        else:
            query = query.where(UserRoleAssignment.hotel_id.is_(None))

        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError("Role assignment already exists")

        assignment = UserRoleAssignment(
            user_id=assignment_data.user_id,
            role_id=assignment_data.role_id,
            hotel_id=assignment_data.hotel_id
        )

        db.add(assignment)
        await db.flush()
        await db.refresh(assignment)

        return assignment

    @staticmethod
    async def get_user_roles(db: AsyncSession, user_id: int) -> List[UserRoleAssignment]:
        """
        Get all role assignments for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List[UserRoleAssignment]: List of role assignments
        """
        result = await db.execute(
            select(UserRoleAssignment).where(
                UserRoleAssignment.user_id == user_id)
        )
        return list(result.scalars().all())
