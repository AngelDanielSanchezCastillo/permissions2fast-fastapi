# permissions2fast-fastapi

🔒 Role-Based Access Control (RBAC) extension for `oauth2fast-fastapi`.

Easily manage user roles and permissions in your FastAPI application.

## Features

- 👥 **Role Management**: Create, assign, and manage roles.
- 🔑 **Granular Permissions**: Define specific permissions and assign them to roles.
- 🛡️ **Route Protection**: Dependencies to protect endpoints based on roles or permissions.
- ⚡ **Async Support**: Fully async database interactions.
- 🔌 **Seamless Integration**: Built to extend `oauth2fast-fastapi`.

## Installation

```bash
pip install permissions2fast-fastapi
```

## Configuration

This package uses the same database configuration as `oauth2fast-fastapi`. Ensure your `.env` file is configured correctly.

### Database Settings (Shared with Auth)
```bash
AUTH_DB__USERNAME=postgres
AUTH_DB__PASSWORD=yourpassword
AUTH_DB__HOSTNAME=localhost
AUTH_DB__NAME=myapp_db
AUTH_DB__PORT=5432
```

### Redis Settings (Specific to Permissions)
This package uses Redis for caching permissions. You can use the same Redis server as other modules (like mailing) but specify a different database if needed.

```bash
PERMISSIONS_REDIS__HOST=localhost
PERMISSIONS_REDIS__PORT=6379
PERMISSIONS_REDIS__DB=0  # Can be different from mailing DB
PERMISSIONS_REDIS__PASSWORD=yourredispassword
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

Use the provided dependencies to restrict access to endpoints.

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
