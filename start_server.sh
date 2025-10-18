#!/bin/bash
set -e  # Exit immediately on error

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------
APP_MODULE="app.main:app"
HOST="0.0.0.0"
PORT="8000"
ADMIN_EMAIL="admin@hotel.com"
ADMIN_PASSWORD="Admin@12345"
ADMIN_ROLE="Admin"

echo "🚀 Starting Hotel Management System setup..."

# -------------------------------------------------------
# 1. ACTIVATE ENVIRONMENT (if virtualenv exists)
# -------------------------------------------------------
if [ -d ".venv" ]; then
  echo "🧩 Activating virtual environment..."
  source .venv/Scripts/activate
fi

# -------------------------------------------------------
# 2. RUN DATABASE MIGRATIONS
# -------------------------------------------------------
echo "📦 Preparing migrations..."
alembic upgrade head

# -------------------------------------------------------
# 3. CREATE DEFAULT ADMIN (if not exists)
# -------------------------------------------------------
echo "👤 Creating default admin user (if missing)..."
python <<'PYCODE'
import asyncio
from sqlalchemy import select, and_
from app.account_module.models import user, role, user_role_assignment  # ensure model registry consistency
from app.hotel_module.models import  hotel  # ensure model registry consistency
from app.account_module.models.user import User,StaffProfile
from app.account_module.models.role import Role
from app.account_module.models.user_role_assignment import UserRoleAssignment
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash


async def create_admin():
    async with AsyncSessionLocal() as session:
        # Ensure roles exist
        admin_role = await session.scalar(select(Role).where(Role.name == "Admin"))
        if not admin_role:
            print("⚠️ Admin role not found. Creating default roles...")
            roles = [
                Role(name="Admin", description="System administrator"),
                Role(name="Manager", description="Hotel manager"),
                Role(name="Receptionist", description="Front desk staff"),
                Role(name="Housekeeper", description="Room cleaning staff"),
                Role(name="Guest", description="Regular hotel user"),
            ]
            session.add_all(roles)
            await session.commit()
            admin_role = await session.scalar(select(Role).where(Role.name == "Admin"))

        # Check if any global admin already exists (via UserRoleAssignment)
        existing_admin_assignment = await session.scalar(
            select(UserRoleAssignment).where(
                and_(
                    UserRoleAssignment.role_id == admin_role.id,
                    UserRoleAssignment.hotel_id.is_(None)
                )
            )
        )
        if existing_admin_assignment:
            print("✅ Global Admin user already exists.")
            return

        # Create new admin user
        admin = User(
            email="admin@hotel.com",
            password_hash=get_password_hash("Admin@12345"),
            is_active=True,
        )
        session.add(admin)
        await session.flush()  # ensure admin.id is available

        # Assign Admin role globally (no hotel_id)
        admin_assignment = UserRoleAssignment(
            user_id=admin.id,
            role_id=admin_role.id,
            hotel_id=None,
        )
        session.add(admin_assignment)

        await session.commit()
        print("✅ Default global Admin user created successfully.")


if __name__ == "__main__":
    asyncio.run(create_admin())
PYCODE

# -------------------------------------------------------
# 4. START FASTAPI SERVER
# -------------------------------------------------------
echo "🌐 Starting FastAPI server..."
exec uvicorn $APP_MODULE --host $HOST --port $PORT --reload
