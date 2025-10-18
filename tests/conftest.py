"""Test configuration and fixtures."""
import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.main import app
from app.core.database import Base, get_db

# Test database URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for session scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    - Creates all tables before test.
    - Seeds default roles.
    - Drops tables after test (optional).
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        # --- SEED DEFAULT ROLES ---
        from sqlalchemy import select
        from app.account_module.models.role import Role

        existing_roles = (await session.execute(select(Role))).scalars().all()
        if not existing_roles:
            session.add_all([
                Role(name="Admin", description="System administrator"),
                Role(name="Manager", description="Hotel manager"),
                Role(name="Receptionist", description="Front desk staff"),
                Role(name="Housekeeper", description="Room cleaning staff"),
                Role(name="Guest", description="Regular hotel user"),
            ])
            await session.commit()
        # --------------------------

        yield session

    # Uncomment if you want to drop tables after each test
    async with test_engine.begin() as conn:
       all_tables = list(Base.metadata.sorted_tables)
       all_tables.reverse()
       await conn.run_sync(
           lambda sync_conn: Base.metadata.drop_all(
               sync_conn, tables=all_tables)
       )

    # async with test_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with overridden database dependency.

    Args:
        db_session: Test database session

    Yields:
        AsyncClient: Test HTTP client
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
