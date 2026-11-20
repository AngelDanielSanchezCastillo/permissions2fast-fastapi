"""Tests for the assign_role bootstrap script."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_assign_role_creates_role_if_not_exists():
    """assign_role creates the role if it doesn't exist."""
    session = AsyncMock()

    # Mock user
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "admin@example.com"

    # Mock role (not found)
    mock_result_user = MagicMock()
    mock_result_user.one_or_none.return_value = mock_user

    mock_result_role = MagicMock()
    mock_result_role.one_or_none.return_value = None

    session.exec = AsyncMock(side_effect=[mock_result_user, mock_result_role])
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.refresh = AsyncMock()

    # Mock created role
    created_role = MagicMock()
    created_role.id = 99
    created_role.name = "custom_role"

    with patch(
        "permissions2fast_fastapi.scripts.assign_role.create_role",
        new_callable=AsyncMock,
        return_value=created_role,
    ), patch(
        "permissions2fast_fastapi.scripts.assign_role.assign_user_role",
        new_callable=AsyncMock,
        return_value=MagicMock(),
    ):
        from permissions2fast_fastapi.scripts.assign_role import assign_role_to_user

        result = await assign_role_to_user(
            session=session,
            email="admin@example.com",
            role_name="custom_role",
        )

        assert result["user_email"] == "admin@example.com"
        assert result["role_name"] == "custom_role"
        assert result["role_created"] is True
        assert result["user_id"] == 1
        assert result["role_id"] == 99


@pytest.mark.asyncio
async def test_assign_role_uses_existing_role():
    """assign_role uses existing role if it already exists."""
    session = AsyncMock()

    # Mock user
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "admin@example.com"

    # Mock role (found)
    mock_role = MagicMock()
    mock_role.id = 1
    mock_role.name = "admin"

    mock_result_user = MagicMock()
    mock_result_user.one_or_none.return_value = mock_user

    mock_result_role = MagicMock()
    mock_result_role.one_or_none.return_value = mock_role

    session.exec = AsyncMock(side_effect=[mock_result_user, mock_result_role])
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    with patch(
        "permissions2fast_fastapi.scripts.assign_role.assign_user_role",
        new_callable=AsyncMock,
        return_value=MagicMock(),
    ):
        from permissions2fast_fastapi.scripts.assign_role import assign_role_to_user

        result = await assign_role_to_user(
            session=session,
            email="admin@example.com",
            role_name="admin",
        )

        assert result["user_email"] == "admin@example.com"
        assert result["role_name"] == "admin"
        assert result["role_created"] is False


@pytest.mark.asyncio
async def test_assign_role_raises_if_user_not_found():
    """assign_role raises ValueError if user doesn't exist."""
    session = AsyncMock()

    # Mock user (not found)
    mock_result_user = MagicMock()
    mock_result_user.one_or_none.return_value = None

    session.exec = AsyncMock(return_value=mock_result_user)

    from permissions2fast_fastapi.scripts.assign_role import assign_role_to_user

    with pytest.raises(ValueError, match="not found"):
        await assign_role_to_user(
            session=session,
            email="nonexistent@example.com",
            role_name="admin",
        )
