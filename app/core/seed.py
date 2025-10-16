from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.account_module.models.role import Role

# Create engine and session
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


async def seed_roles():
    """Ensure default roles exist in the database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Role))
        existing_roles = result.scalars().all()

        if not existing_roles:
            session.add_all([
                Role(name="Admin", description="System administrator"),
                Role(name="Manager", description="Hotel manager"),
                Role(name="Receptionist", description="Front desk staff"),
                Role(name="Housekeeper", description="Room cleaning staff"),
                Role(name="Guest", description="Regular hotel user"),
            ])
            await session.commit()
            print("✅ Default roles created.")
        else:
            print("ℹ️ Roles already exist, skipping seed.")


async def lifespan(app: FastAPI):
    """Lifespan context runs once at startup and shutdown."""
    print("🚀 App starting up...")
    # Run migrations or seeding logic
    await seed_roles()
    yield
    print("🛑 App shutting down...")
