"""Test booking management endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from typing import Literal, Optional
from sqlalchemy import select

from app.account_module.models.role import Role
from app.account_module.models.user_role_assignment import UserRoleAssignment
from app.hotel_module.models.hotel import Hotel  # Assuming Hotel model exists
from app.hotel_module.models.room import Room  # Assuming Room model exists

# --- Helper Functions for Setup ---

BOOKING_BASE_URL = "/bookings/"
TODAY = date.today()
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


async def get_role_id(db_session: AsyncSession, role_name: Literal["Admin", "Manager", "Guest"]) -> int:
    """Helper to get a role ID from the database."""
    result = await db_session.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one()
    return role.id


async def register_and_assign_role(client: AsyncClient, db_session: AsyncSession, email: str, role_name: Literal["Admin", "Manager", "Guest"], hotel_id: Optional[int] = None) -> str:
    """Helper to register a user, assign a role, and return the auth token."""
    password = "testpassword123"

    register_response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password
        }
    )
    user_data = register_response.json()
    user_id = user_data["id"]

    role_id = await get_role_id(db_session, role_name)

    assignment = UserRoleAssignment(
        user_id=user_id,
        role_id=role_id,
        hotel_id=hotel_id
    )
    db_session.add(assignment)
    await db_session.commit()

    login_response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    return login_response.json()["access_token"]


async def create_guest_with_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Helper to create a guest user and return auth token."""
    return await register_and_assign_role(client, db_session, "guest@example.com", "Guest")


async def create_admin_with_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Helper to create an admin user and return auth token."""
    return await register_and_assign_role(client, db_session, "admin@example.com", "Admin")


async def create_manager_with_token(client: AsyncClient, db_session: AsyncSession, hotel_id: Optional[int] = None) -> str:
    """Helper to create a manager user and return auth token."""
    # Use a unique email if hotel_id is provided for hotel-scoped manager
    email = f"manager_{hotel_id}@example.com" if hotel_id else "global_manager@example.com"
    return await register_and_assign_role(client, db_session, email, "Manager", hotel_id)


async def create_hotel_and_room(db_session: AsyncSession) -> tuple[int, int]:
    """Helper to create necessary Hotel and Room data directly in DB."""
    # Create Hotel with mandatory area fields from TEST_HOTEL_AREA_PAYLOAD
    hotel = Hotel(

        name="Booking Test Hotel (DB)",
        description="Test description for DB setup.",
        facilities=["Pool", "Gym"],
        area=TEST_HOTEL_AREA_PAYLOAD
    )
    db_session.add(hotel)
    await db_session.flush()  # Flushes to get hotel.id

    # Create Room linked to the new hotel
    room = Room(
        hotel_id=hotel.id,
        name="Room D-101",
        room_type="DOUBLE",  # Consistent with Pydantic Enum convention
        price_per_night=10000,  # $100.00
        max_occupancy=2,
        number_of_beds=1,
        status="AVAILABLE",  # Consistent with Pydantic Enum convention
        description="Standard test room description.",
        facilities=["Mini Bar"],
        photos=[],
    )
    db_session.add(room)
    await db_session.commit()
    return hotel.id, room.id


# --- Test Data ---


def get_valid_booking_data(room_id: int):
    """Returns valid booking data for creation."""
    return {
        "room_id": room_id,
        "customer_contact": "guest@example.com",
        "check_in_date": TODAY.strftime("%Y-%m-%d"),
        "check_out_date": (TODAY + timedelta(days=3)).strftime("%Y-%m-%d"),
        "num_guests": 2,
        "total_price": 30000,  # 3 nights * $100/night
        "status": "confirmed"
    }

# --- Tests ---


@pytest.mark.asyncio
async def test_create_booking_as_guest(client: AsyncClient, db_session: AsyncSession):
    """Test creating a new booking as a Guest."""
    _, room_id = await create_hotel_and_room(db_session)
    token = await create_guest_with_token(client, db_session)
    booking_data = get_valid_booking_data(room_id)

    response = await client.post(
        BOOKING_BASE_URL,
        json=booking_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["customer_contact"] == booking_data["customer_contact"]
    # Assuming service sets status upon creation
    assert data["status"] == "confirmed"
    assert "id" in data
    assert "num_guests" in data


@pytest.mark.asyncio
async def test_get_all_bookings_as_admin(client: AsyncClient, db_session: AsyncSession):
    """Test getting all bookings with Admin role (covered by selected code)."""
    _, room_id = await create_hotel_and_room(db_session)
    admin_token = await create_admin_with_token(client, db_session)
    guest_token = await create_guest_with_token(client, db_session)

    # 1. Create a few bookings by a guest
    for i in range(2):
        booking_data = get_valid_booking_data(room_id)
        booking_data["customer_name"] = f"Test Guest {i}"
        await client.post(BOOKING_BASE_URL, json=booking_data, headers={"Authorization": f"Bearer {guest_token}"})

    # 2. Admin attempts to get all bookings (should succeed)
    response = await client.get(
        BOOKING_BASE_URL,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Check that at least two bookings are returned
    assert len(data) >= 2
    # Check that list schema is used
    assert "room_id" in data[0]
    assert "customer_contact" in data[0]
    assert "total_price" in data[0]


@pytest.mark.asyncio
async def test_get_all_bookings_unauthorized(client: AsyncClient, db_session: AsyncSession):
    """Test unauthorized access to the GET /bookings/ route (Guest should fail)."""
    guest_token = await create_guest_with_token(client, db_session)

    # Guest attempts to get all bookings (should fail with 403 Forbidden)
    response = await client.get(
        BOOKING_BASE_URL,
        headers={"Authorization": f"Bearer {guest_token}"}
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_get_my_bookings_as_guest(client: AsyncClient, db_session: AsyncSession):
    """Test Guest getting their own bookings (GET /bookings/me)."""
    _, room_id = await create_hotel_and_room(db_session)
    guest_token = await create_guest_with_token(client, db_session)

    # Guest creates a booking
    await client.post(BOOKING_BASE_URL, json=get_valid_booking_data(room_id), headers={"Authorization": f"Bearer {guest_token}"})

    # Guest retrieves their own bookings
    response = await client.get(
        f"{BOOKING_BASE_URL}me/{get_valid_booking_data(room_id)["customer_contact"]}",
        headers={"Authorization": f"Bearer {guest_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["customer_contact"] == get_valid_booking_data(room_id)[
        "customer_contact"]


@pytest.mark.asyncio
async def test_update_booking_as_owner(client: AsyncClient, db_session: AsyncSession):
    """Test updating a booking by the owner (Guest)."""
    _, room_id = await create_hotel_and_room(db_session)
    guest_token = await create_guest_with_token(client, db_session)

    # Create booking
    create_response = await client.post(BOOKING_BASE_URL, json=get_valid_booking_data(room_id), headers={"Authorization": f"Bearer {guest_token}"})
    booking_id = create_response.json()["id"]

    # Update booking
    update_data = {
        "customer_contact": "UpdatednewJohn@Doe.com", "status": "pending"}
    update_response = await client.put(
        f"{BOOKING_BASE_URL}{booking_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {guest_token}"}
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["customer_contact"] == "UpdatednewJohn@Doe.com"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_delete_booking_as_owner(client: AsyncClient, db_session: AsyncSession):
    """Test deleting/cancelling a booking by the owner (Guest)."""
    _, room_id = await create_hotel_and_room(db_session)
    guest_token = await create_guest_with_token(client, db_session)

    # Create booking
    create_response = await client.post(BOOKING_BASE_URL, json=get_valid_booking_data(room_id), headers={"Authorization": f"Bearer {guest_token}"})
    booking_id = create_response.json()["id"]

    # Delete booking
    delete_response = await client.delete(
        f"{BOOKING_BASE_URL}{booking_id}",
        headers={"Authorization": f"Bearer {guest_token}"}
    )

    assert delete_response.status_code == 204

    # Verify deletion
    verify_response = await client.get(
        f"{BOOKING_BASE_URL}{booking_id}",
        # Still need token, but should get 404
        headers={"Authorization": f"Bearer {guest_token}"}
    )
    assert verify_response.status_code == 404
