"""
Permissions2Fast FastAPI Settings

Configuration for permissions2fast-fastapi module using pydantic-settings.
Reads from environment variables with PERMISSIONS_ prefix.
"""

import os

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Look for .env in the current working directory (where the app is running)
DOTENV_PATH = os.path.join(os.getcwd(), ".env")


class RedisSettings(BaseModel):
    """Redis configuration for caching permissions."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: SecretStr | None = None
    decode_responses: bool = True


class PermissionsSettings(BaseSettings):
    """Permissions and RBAC configuration settings."""

    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        env_file_encoding="utf-8",
        env_prefix="PERMISSIONS_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Redis settings for caching permissions
    redis: RedisSettings = RedisSettings()

    # Redis cache feature flag
    redis_rbac_enabled: bool = False

    # Cache settings
    cache_ttl_seconds: int = 300  # 5 minutes default


try:
    settings = PermissionsSettings()
except Exception as e:
    # Use log2fast_fastapi for proper error logging if available
    try:
        from log2fast_fastapi import get_logger
        logger = get_logger(__name__)
        logger.exception(
            "🚨 Error loading Permissions2Fast configuration",
            extra_data={
                "error": str(e),
                "dotenv_path": DOTENV_PATH,
            },
        )
    except ImportError:
        print(f"🚨 Error loading Permissions2Fast configuration: {e}")
    raise
