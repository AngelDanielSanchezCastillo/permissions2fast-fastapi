# permissions2fast-fastapi

🔒 Role-Based Access Control (RBAC) extension for `oauth2fast-fastapi`.

Easily manage user roles and permissions in your FastAPI application with support for High-Performance Redis Caching.

## Features

- 👥 **Role Management**: Create, assign, and manage roles for users.
- 🔑 **Granular Permissions**: Define specific permissions and assign them to roles or directly to users (polymorphic assignments).
- � **Redis Caching (Optional)**: High-performance permission evaluation using Redis to minimize database lookups.
- �🛡️ **Route Protection**: Dependencies to protect endpoints based on roles or permissions.
- ⚡ **Async Support**: Fully async database interactions via `pgsqlasync2fast-fastapi`.
- 🔌 **Seamless Integration**: Built to extend `oauth2fast-fastapi`.

## Installation

```bash
pip install permissions2fast-fastapi
```

## Configuration

This package uses the same database connection logic as `oauth2fast-fastapi`. Configure your environment variables in `.env`.

### Basic Settings

```bash
# Database Configuration
DB_CONNECTIONS__AUTH__USERNAME=db_user
DB_CONNECTIONS__AUTH__PASSWORD=db_password
DB_CONNECTIONS__AUTH__HOST=localhost
DB_CONNECTIONS__AUTH__DATABASE=db_name
DB_CONNECTIONS__AUTH__PORT=5432
```

### Advanced Features (Redis)

You can enable Redis caching by setting the following environment variables:

```bash
PERMISSIONS_REDIS_RBAC_ENABLED=True

# Redis connection details (if caching is enabled)
PERMISSIONS_REDIS__HOST=localhost
PERMISSIONS_REDIS__PORT=6379
PERMISSIONS_REDIS__DB=0
# PERMISSIONS_REDIS__PASSWORD=your_redis_password
```

## Usage

### 1. Basic Integration

```python
from fastapi import FastAPI
from permissions2fast_fastapi import permissions_router, roles_router
from oauth2fast_fastapi import router as auth_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(permissions_router)
app.include_router(roles_router)
```

### 2. Protecting Routes

Use the provided dependencies to restrict access to endpoints. The system will automatically check Redis cache if enabled, and fallback to database queries if needed.

```python
from fastapi import Depends
from permissions2fast_fastapi.dependencies import has_permission, has_role
from oauth2fast_fastapi.models import User

# Require a specific role
@app.get("/admin-dashboard")
async def admin_dashboard(user: User = Depends(has_role("admin"))):
    return {"message": "Welcome Admin"}

# Require a specific permission
@app.get("/edit-post")
async def edit_post(user: User = Depends(has_permission("posts.edit"))):
    return {"message": "You can edit posts"}
```

### 3. Using the Default Seeder

To quickly set up default access control for the package routes itself (admin role and necessary permissions to add/remove routes, roles, and permissions), you can use the built-in JSON seeder during the application startup process (`lifespan`).

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pgsqlasync2fast_fastapi import startup_database, get_db_manager
from oauth2fast_fastapi import get_db_engine, AuthModel
from permissions2fast_fastapi import seed_rbac_from_json

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This example assumes you have an 'auth' bound session using pgsqlasync2fast-fastapi
    await startup_database()

    # List configured connections
    manager = get_db_manager()

    # Create auth database tables
    engine = get_db_engine("auth", manager)
    async with engine.begin() as conn:
        # Create auth tables (User, etc.)
        await conn.run_sync(AuthModel.metadata.create_all)
    # Run the seeder when starting up your application
    session = await manager.get_session("auth")
    try:
        # Seeder is idempotent and won't duplicate data on multiple startups
        await seed_rbac_from_json(session, route_prefix="")
    finally:
        await session.close()

app = FastAPI(lifespan=lifespan)
```
