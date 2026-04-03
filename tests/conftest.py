import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel

# Import from oauth2fast-fastapi
from oauth2fast_fastapi import (
    startup_database,
    shutdown_database,
    get_db_session,
    AuthModel,
)
from sqlalchemy import text
from oauth2fast_fastapi.dependencies import get_auth_session
# Import lower level manager access
from pgsqlasync2fast_fastapi.connection import get_manager

# Import local package
# Import local package
from permissions2fast_fastapi.routers import permissions_router, roles_router, routes_router
from permissions2fast_fastapi.utils import permission_cache

# Import all models to ensure they are registered with SQLModel metadata
from permissions2fast_fastapi.models import (
    role_model,
    permission_model,
    permission_category_model,
    route_model,
    user_role_model,
    permission_assignment_model,
    permission_route_model,
)

# We rely on pydantic-settings to load .env automatically.


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def redis_cleanup():
    """Ensure Redis client is closed after each test."""
    yield
    await permission_cache.close_redis_client()


@pytest.fixture(scope="session")
async def db_engine():
    # Initialize the database connection using oauth2fast-fastapi utility
    # This expects DB_CONNECTIONS__AUTH__... environment variables to be set
    await startup_database()
    
    # Get the manager explicitly since we cannot use Depends in a fixture
    manager = get_manager()
    # "auth" is intrinsic to oauth2fast-fastapi
    engine = manager.get_engine("auth")
    
    # Create tables
    print(f"DEBUG: Creating tables for: {AuthModel.metadata.tables.keys()}")
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        await conn.run_sync(AuthModel.metadata.create_all)
    print("DEBUG: Tables created.")
    
    yield engine
    
    # Cleanup
    await shutdown_database()


@pytest.fixture(scope="function")
async def session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    # Clean up the database before each test
    # We truncate all tables to ensure a clean state
    async with db_engine.begin() as conn:
        tables = list(AuthModel.metadata.tables.keys())
        if tables:
            table_names = ", ".join([f'"{t}"' for t in tables])
            await conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))

    # Start a connection
    connection = await db_engine.connect()
    # Begin a transaction
    transaction = await connection.begin()

    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
    )

    try:
        yield session
    finally:
        await session.close()
        # Check if transaction is still active before rolling back
        if transaction.is_active:
            await transaction.rollback()
        await connection.close()


@pytest.fixture(scope="session")
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(permissions_router)
    app.include_router(roles_router)
    app.include_router(routes_router)
    return app


@pytest.fixture(scope="function")
async def client(app: FastAPI, session: AsyncSession, test_user) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_auth_session] = lambda: session
    from oauth2fast_fastapi.dependencies import get_current_verified_user
    app.dependency_overrides[get_current_verified_user] = lambda: test_user
    
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


# --- Shared Fixtures ---

from oauth2fast_fastapi import User
from permissions2fast_fastapi.models.role_model import Role

@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    """Create a persistent test user for these tests."""
    user = User(
        email="test_common@example.com",
        password="hashed_secret",
        name="Test Common User",
        is_active=True,
        is_verified=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def test_role(session: AsyncSession) -> Role:
    """Create a persistent test role for these tests."""
    role = Role(name="TestCommonRole", description="A common test role")
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role
