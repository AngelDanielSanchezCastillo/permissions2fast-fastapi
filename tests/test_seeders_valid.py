"""CI gate: this package's seeders must be structurally valid before release.

Uses the reusable ``validate_seeders_report`` primitive from pgsqlasync2fast.
2fast packages must ship explicit UUID ids, so this gate also fails on any
warning (e.g. integer id against a UUID primary key). Consuming apps can run
the same check against this package's manifest.
"""

from __future__ import annotations

import pytest

from permissions2fast_fastapi import get_seeder_config


@pytest.mark.parametrize("profile", ["dev", "prod"])
def test_package_seeders_are_valid(profile: str) -> None:
    from pgsqlasync2fast_fastapi import validate_seeders_report

    config = get_seeder_config()
    report = validate_seeders_report(
        config.manifest_path,
        config.model_registry,
        profile=profile,
    )
    assert report.errors == [], f"Invalid seeders for '{profile}': {report.errors}"
    assert report.warnings == [], (
        f"2fast packages must use explicit UUID ids; warnings for '{profile}': "
        f"{report.warnings}"
    )


def test_package_registers_its_seeders() -> None:
    from pgsqlasync2fast_fastapi import get_registered_packages

    # Importing the package must have registered its seeder config.
    import permissions2fast_fastapi  # noqa: F401

    names = {pkg.package_name for pkg in get_registered_packages()}
    assert "permissions2fast-fastapi" in names
