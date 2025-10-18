"""Test room management endpoints, scoped to a hotel."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.account_module.models.role import Role
from app.account_module.models.user_role_assignment import UserRoleAssignment


# --- Helper Data (Mirrored from previous context) ---
TEST_HOTEL_AREA_PAYLOAD = {
    "country": "Test Country",
    "state_or_province": "Test State",
    "city_or_town": "Test City",
    "county": "Test County",
    "street": "123 Main St",
    "zip_or_postal_code": "12345",
    "building_name_or_suite": "Suite 100",
}

# --- Shared Helpers ---


async def create_admin_with_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Helper to create an admin user and return auth token."""
    # Ensure role is available if not already in setup
    try:
        result = await db_session.execute(select(Role).where(Role.name == "Admin"))
        admin_role = result.scalar_one()
    except Exception:
        # Create roles if they don't exist (e.g., in a clean test run)
        admin_role = Role(name="Admin", description="System administrator")
        db_session.add(admin_role)
        await db_session.commit()
        await db_session.refresh(admin_role)

    register_response = await client.post(
        "/auth/register",
        json={
            "email": "hotelAdmin@example.com",
            "password": "adminpass123"
        }
    )
    user_data = register_response.json()

    assignment = UserRoleAssignment(
        user_id=user_data["id"],
        role_id=admin_role.id,
        hotel_id=None  # Global admin
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


async def create_test_hotel(client: AsyncClient, token: str, name: str) -> int:
    """Helper to create a hotel and return its ID."""
    hotel_payload = {
        "name": name,
        "description": f"Test hotel for {name}.",
        "area": TEST_HOTEL_AREA_PAYLOAD,
        "facilities": ["Free WiFi", "Breakfast"]
    }
    response = await client.post(
        "/hotels/",
        json=hotel_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    return response.json()["id"]


# --- Test Cases for Rooms ---

@pytest.mark.asyncio
async def test_create_room(client: AsyncClient, db_session: AsyncSession):
    """Test creating a new room for a specific hotel using the updated schema."""
    token = await create_admin_with_token(client, db_session)
    hotel_id = await create_test_hotel(client, token, "Test Hotel for Room")

    # Updated payload to match RoomCreate schema
    room_payload = {
        "name": "King Suite 101",
        "room_type": "King",
        "price_per_night": 19900,  # Integer price (e.g., $199.00)
        "max_occupancy": 3,
        "status": "available",
        "description": "Luxury suite with ocean view.",
        "number_of_beds": 1,
        "facilities": ["Mini Bar", "Balcony", "Jacuzzi"],
        "photos": [{"public_id": "p1", "secure_url": "url1"}],
        "hotel_id": int(hotel_id),  # hotel_id is now ONLY in the payload
    }

    response = await client.post(
        "/rooms/",  # CHANGED: Flat path /rooms/
        json=room_payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "King Suite 101"  # Check new name field
    assert data["price_per_night"] == 19900  # Check new price field
    assert data["max_occupancy"] == 3  # Check new capacity field
    assert data["status"] == "available"  # Check new status field
    assert data["number_of_beds"] == 1  # Check new number_of_beds field
    assert data["hotel_id"] == hotel_id
    assert "id" in data

    # Check structured data
    assert data["facilities"] == ["Mini Bar", "Balcony", "Jacuzzi"]
    assert len(data["photos"]) == 1
    assert data["photos"][0]["public_id"] == "p1"


@pytest.mark.asyncio
async def test_get_room_details(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving details for a single room."""
    token = await create_admin_with_token(client, db_session)
    hotel_id = await create_test_hotel(client, token, "Hotel Get Room")

    # 1. Create the room with updated schema fields
    create_response = await client.post(
        "/rooms/",  # Changed path
        json={
            "name": "Room 205",
            "room_type": "Double",
            "price_per_night": 12000,
            "max_occupancy": 4,
            "status": "available",
            "description": "Family room.",
            "number_of_beds": 2,
            "facilities": ["Wifi"],
            "photos": [],
            "hotel_id": hotel_id,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    room_id = create_response.json()["id"]

    # 2. Retrieve the room
    response = await client.get(
        f"/rooms/{room_id}",  # CHANGED: Flat path /rooms/{room_id}
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == room_id
    assert data["name"] == "Room 205"
    assert data["max_occupancy"] == 4
    assert data["price_per_night"] == 12000
    assert data["hotel_id"] == hotel_id
    assert data["number_of_beds"] == 2


@pytest.mark.asyncio
async def test_get_all_rooms_by_hotel(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving a list of rooms scoped to a single hotel. Uses query parameter for filtering."""
    token = await create_admin_with_token(client, db_session)
    hotel_id_a = await create_test_hotel(client, token, "Hotel A List")
    # Control group
    hotel_id_b = await create_test_hotel(client, token, "Hotel B Control")

    # Base payload structure for simplicity
    base_payload = {
        "room_type": "Standard", "price_per_night": 10000, "max_occupancy": 2,
        "status": "available", "number_of_beds": 1, "facilities": [], "photos": []
    }

    # Create two rooms in Hotel A
    await client.post(
        "/rooms/",  # Changed path
        json={**base_payload, "name": "Room 301", "hotel_id": hotel_id_a},
        headers={"Authorization": f"Bearer {token}"}
    )
    await client.post(
        "/rooms/",  # Changed path
        json={**base_payload, "name": "Room 302", "hotel_id": hotel_id_a},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Create one room in Hotel B (should not appear in A's list)
    await client.post(
        "/rooms/",  # Changed path
        json={**base_payload, "name": "Room 500",
              "price_per_night": 5000, "hotel_id": hotel_id_b},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Get rooms for Hotel A using a query parameter for filtering
    response = await client.get(
        # CHANGED: Flat path + query parameter
        f"/rooms/?hotel_id={hotel_id_a}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # Only two rooms should be returned (from Hotel A)
    # Check new name field
    assert any(room["name"] == "Room 301" for room in data)
    # Check new name field
    assert not any(room["name"] == "Room 500" for room in data)


@pytest.mark.asyncio
async def test_update_room(client: AsyncClient, db_session: AsyncSession):
    """Test updating a room's details."""
    token = await create_admin_with_token(client, db_session)
    hotel_id = await create_test_hotel(client, token, "Hotel Update Room")

    # 1. Create the room with original data
    create_response = await client.post(
        "/rooms/",  # Changed path
        json={
            "name": "Old Room 401", "room_type": "Standard", "price_per_night": 10000,
            "max_occupancy": 2, "status": "available", "number_of_beds": 1,
            "facilities": ["Old TV"], "photos": [], "hotel_id": hotel_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    room_id = create_response.json()["id"]

    # 2. Update the room using fields from RoomUpdate schema
    update_payload = {
        "price_per_night": 15050,
        "max_occupancy": 3,
        "status": "booked",
        "facilities": ["Mini Bar", "Jacuzzi", "New TV"],
        "photos": [{"public_id": "new_pic", "secure_url": "new_url"}]
    }
    response = await client.put(
        f"/rooms/{room_id}",  # CHANGED: Flat path /rooms/{room_id}
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == room_id
    assert data["price_per_night"] == 15050
    assert data["max_occupancy"] == 3
    assert data["status"] == "booked"
    assert data["facilities"] == ["Mini Bar", "Jacuzzi", "New TV"]
    assert len(data["photos"]) == 1

    # Ensure non-updated fields (like name) remain the same
    assert data["name"] == "Old Room 401"
    assert data["number_of_beds"] == 1


@pytest.mark.asyncio
async def test_delete_room(client: AsyncClient, db_session: AsyncSession):
    """Test deleting a room."""
    token = await create_admin_with_token(client, db_session)
    hotel_id = await create_test_hotel(client, token, "Hotel Delete Room")

    # 1. Create the room
    create_response = await client.post(
        "/rooms/",  # Changed path
        json={
            "name": "Room 501", "room_type": "Standard", "price_per_night": 10000,
            "max_occupancy": 2, "status": "available", "number_of_beds": 1,
            "facilities": [], "photos": [], "hotel_id": hotel_id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    room_id = create_response.json()["id"]

    # 2. Delete the room
    response = await client.delete(
        f"/rooms/{room_id}",  # CHANGED: Flat path /rooms/{room_id}
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204  # HTTP 204 No Content for successful deletion

    # 3. Verify deletion (Attempt to retrieve the room)
    check_response = await client.get(
        f"/rooms/{room_id}",  # CHANGED: Flat path /rooms/{room_id}
        headers={"Authorization": f"Bearer {token}"}
    )
    assert check_response.status_code == 404
