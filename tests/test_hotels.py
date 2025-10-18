"""Test hotel management endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.account_module.models.role import Role
from app.account_module.models.user_role_assignment import UserRoleAssignment

# --- Define the necessary payload data based on the new schema ---
TEST_HOTEL_AREA_PAYLOAD = {
    "country": "Test Country",
    "state_or_province": "Test State",
    "city_or_town": "Test City",
    "county": "Test County",
    "street": "123 Main St",
    "zip_or_postal_code": "12345",
    "building_name_or_suite": "Suite 100",
}

# --- Helper to create an admin user and return auth token (No change needed here) ---
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

# ----------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_hotel(client: AsyncClient, db_session: AsyncSession):
    """Test creating a new hotel with the required nested 'area' schema."""
    token = await create_admin_with_token(client, db_session)

    hotel_payload = {
        "name": "Grand Hotel",
        "description": "A luxury establishment.",
        # The 'address' field is replaced by the 'area' object
        "area": TEST_HOTEL_AREA_PAYLOAD,
        "facilities": ["Pool", "Gym", "Parking"]
    }

    response = await client.post(
        "/hotels/",
        json=hotel_payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Grand Hotel"
    assert data["area"]["country"] == "Test Country"  # Check nested field
    assert data["facilities"] == ["Pool", "Gym", "Parking"]
    assert "id" in data

    # Store the created hotel ID for potential future tests if needed
    return data["id"]


@pytest.mark.asyncio
async def test_get_all_hotels(client: AsyncClient, db_session: AsyncSession):
    """Test getting all hotels."""
    token = await create_admin_with_token(client, db_session)

    # 1. Create a hotel using the new schema
    hotel_payload = {
        "name": "Test Hotel for List",
        "description": "Description for listing.",
        "area": TEST_HOTEL_AREA_PAYLOAD,
        "facilities": []
    }

    await client.post(
        "/hotels/",
        json=hotel_payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    # 2. Get all hotels
    response = await client.get(
        "/hotels/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
   # 💥 CHANGE 1: Assert that the response is a list, not a dict with 'items'
    assert isinstance(data, list)

    # 💥 CHANGE 2: Assert that the list contains at least one item
    assert len(data) > 0

    # 💥 CHANGE 3: Check the content of the first item (or search for the created one)
    hotel_item = next(
        (item for item in data if item["name"] == "Test Hotel for List"), None)
    assert hotel_item is not None
    assert hotel_item["name"] == "Test Hotel for List"
    assert "area" in hotel_item


@pytest.mark.asyncio
async def test_hotel_scoped_role(client: AsyncClient, db_session: AsyncSession):
    """Test hotel-scoped role assignment."""
    token = await create_admin_with_token(client, db_session)

    # 1. Create a hotel using the new schema
    hotel_payload = {
        "name": "Scoped Hotel",
        "description": "Hotel for manager assignment.",
        "area": TEST_HOTEL_AREA_PAYLOAD,
        "facilities": []
    }

    hotel_response = await client.post(
        "/hotels/",
        json=hotel_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    hotel_id = hotel_response.json()["id"]

    # 2. Create a new user (No change needed)
    user_response = await client.post(
        "/auth/register",
        json={
            "email": "manager@example.com",
            "password": "password123"
        }
    )
    user_id = user_response.json()["id"]

    # 3. Get Manager role (No change needed)
    from sqlalchemy import select
    result = await db_session.execute(select(Role).where(Role.name == "Manager"))
    manager_role = result.scalar_one()

    # 4. Assign hotel-scoped Manager role (No change needed in payload)
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
