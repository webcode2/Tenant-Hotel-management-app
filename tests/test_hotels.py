"""Test hotel management endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.models.user_role_assignment import UserRoleAssignment


async def create_admin_with_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Helper to create an admin user and return auth token."""
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "hotelAdmin@example.com",
            "password": "adminpass123"
        }
    )
    user_data = register_response.json()

    from sqlalchemy import select
    result = await db_session.execute(select(Role).where(Role.name == "Admin"))
    admin_role = result.scalar_one()

    assignment = UserRoleAssignment(
        user_id=user_data["id"],
        role_id=admin_role.id,
        hotel_id=None
    )
    db_session.add(assignment)
    await db_session.commit()

    login_response = await client.post(
        "/auth/login",
        json={
            "email": "hotelAdmin@example.com",
            "password": "adminpass123"
        }
    )

    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_hotel(client: AsyncClient, db_session: AsyncSession):
    """Test creating a new hotel."""
    token = await create_admin_with_token(client, db_session)

    response = await client.post(
        "/hotels/",
        json={
            "name": "Grand Hotel",
            "address": "123 Main St, City, Country"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Grand Hotel"
    assert data["address"] == "123 Main St, City, Country"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_all_hotels(client: AsyncClient, db_session: AsyncSession):
    """Test getting all hotels."""
    token = await create_admin_with_token(client, db_session)

    # Create a hotel
    await client.post(
        "/hotels/",
        json={
            "name": "Test Hotel",
            "address": "Test Address"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # Get all hotels
    response = await client.get(
        "/hotels/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_hotel_scoped_role(client: AsyncClient, db_session: AsyncSession):
    """Test hotel-scoped role assignment."""
    token = await create_admin_with_token(client, db_session)

    # Create a hotel
    hotel_response = await client.post(
        "/hotels/",
        json={
            "name": "Scoped Hotel",
            "address": "Scoped Address"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    hotel_id = hotel_response.json()["id"]

    # Create a new user
    user_response = await client.post(
        "/auth/register",
        json={
            "email": "manager@example.com",
            "password": "password123"
        }
    )
    user_id = user_response.json()["id"]

    # Get Manager role
    from sqlalchemy import select
    result = await db_session.execute(select(Role).where(Role.name == "Manager"))
    manager_role = result.scalar_one()

    # Assign hotel-scoped Manager role
    response = await client.post(
        "/roles/assignments",
        json={
            "user_id": user_id,
            "role_id": manager_role.id,
            "hotel_id": hotel_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["hotel_id"] == hotel_id
