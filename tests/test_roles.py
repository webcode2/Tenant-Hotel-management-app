"""Test role management and authorization."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.account_module.models.role import Role
from app.account_module.models.user_role_assignment import UserRoleAssignment
from app.account_module.services.role_service import RoleService


async def create_admin_user_with_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Helper to create an admin user and return auth token."""
    # Register user
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "password": "adminpass123"
        }
    )
    user_data = register_response.json()

    # Get Admin role
    from sqlalchemy import select
    result = await db_session.execute(select(Role).where(Role.name == "Admin"))
    admin_role = result.scalar_one()

    # Assign Admin role (global)
    assignment = UserRoleAssignment(
        user_id=user_data["id"],
        role_id=admin_role.id,
        hotel_id=None
    )
    db_session.add(assignment)
    await db_session.commit()

    # Login to get token
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "admin@example.com",
            "password": "adminpass123"
        }
    )

    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_role(client: AsyncClient, db_session: AsyncSession):
    """Test creating a new role."""
    token = await create_admin_user_with_token(client, db_session)

    response = await client.post(
        "/roles/",
        json={
            "name": "NewRole",
            "description": "A new test role"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "NewRole"
    assert data["description"] == "A new test role"


@pytest.mark.asyncio
async def test_create_role_unauthorized(client: AsyncClient):
    """Test creating role without authentication."""
    response = await client.post(
        "/roles/",
        json={
            "name": "UnauthorizedRole",
            "description": "Should fail"
        }
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_all_roles(client: AsyncClient, db_session: AsyncSession):
    """Test getting all roles."""
    token = await create_admin_user_with_token(client, db_session)

    response = await client.get(
        "/roles/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5  # Default roles from migration


@pytest.mark.asyncio
async def test_assign_role_to_user(client: AsyncClient, db_session: AsyncSession):
    """Test assigning a role to a user."""
    token = await create_admin_user_with_token(client, db_session)

    # Create a new user
    new_user_response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    new_user_id = new_user_response.json()["id"]

    # Get Manager role
    from sqlalchemy import select
    result = await db_session.execute(select(Role).where(Role.name == "Manager"))
    manager_role = result.scalar_one()

    # Assign role
    response = await client.post(
        "/roles/assignments",
        json={
            "user_id": new_user_id,
            "role_id": manager_role.id,
            "hotel_id": None
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == new_user_id
    assert data["role_id"] == manager_role.id
    assert data["hotel_id"] is None


@pytest.mark.asyncio
async def test_role_based_access_control(client: AsyncClient, db_session: AsyncSession):
    """Test that role-based access control works."""
    # Create a regular user without admin role
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "regular@example.com",
            "password": "password123"
        }
    )

    # Login
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "regular@example.com",
            "password": "password123"
        }
    )
    token = login_response.json()["access_token"]

    # Try to access admin-only endpoint
    response = await client.get(
        "/roles/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert "not enough permissions" in response.json()["detail"].lower()
