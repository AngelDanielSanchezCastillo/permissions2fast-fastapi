"""
One-off migrations for permissions2fast seed data.

Uniformization (ODD-5): seed literals were regenerated as uuid7. Existing
databases still hold the previous ids, so this module rewrites them to the
manifest literals with FK cascade (delegated to ``adopt_explicit_ids``).
"""

from __future__ import annotations

from typing import Any

from pgsqlasync2fast_fastapi import SeederEngine, adopt_explicit_ids


def build_seeder_engine(profile: str = "dev") -> SeederEngine:
    """Build a SeederEngine for this package's RBAC manifest."""
    from . import get_seeder_config

    config = get_seeder_config()
    return SeederEngine(
        manifest_path=config.manifest_path,
        model_registry=config.model_registry,
        profile=profile,
    )


async def adopt_explicit_seed_ids(
    session: Any,
    profile: str = "dev",
    *,
    dry_run: bool = False,
) -> list[Any]:
    """
    Rewrite existing RBAC ids to this package's explicit uuid7 literals.

    Run inside your own transaction and commit when the returned plan looks
    correct (or use ``dry_run=True`` to inspect it first). Idempotent: returns
    an empty list when the database already uses the literal ids.
    """
    engine = build_seeder_engine(profile=profile)
    return await adopt_explicit_ids(session, engine, layer="boot", dry_run=dry_run)


__all__ = ["build_seeder_engine", "adopt_explicit_seed_ids"]
