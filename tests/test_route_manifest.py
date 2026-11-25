"""Tests for the JSON route manifest loader/validator (permissions2fast)."""

from __future__ import annotations

import json

from permissions2fast_fastapi.services.route_manifest import (
    load_route_manifest,
    validate_route_manifest,
)


def _write(tmp_path, payload):
    path = tmp_path / "routes.json"
    path.write_text(json.dumps(payload))
    return path


def test_valid_manifest_loads_typed_specs(tmp_path):
    path = _write(tmp_path, {
        "routes": [
            {"method": "GET", "path": "/roles", "permission": "roles:read", "roles": ["admin"]},
            {"method": "post", "path": "/roles", "permission": "roles:write", "roles": [], "profile": ["dev"]},
        ]
    })
    specs = load_route_manifest(path)
    assert len(specs) == 2
    assert specs[0].method == "GET"
    assert specs[0].permission == "roles:read"
    assert specs[1].method == "POST"
    assert specs[1].profile == {"dev"}


def test_duplicate_routes_are_rejected(tmp_path):
    path = _write(tmp_path, [
        {"method": "GET", "path": "/x"},
        {"method": "GET", "path": "/x"},
    ])
    assert any("duplicate route" in e for e in validate_route_manifest(path))


def test_invalid_method_and_missing_path(tmp_path):
    path = _write(tmp_path, [{"method": "FETCH", "path": ""}])
    errors = validate_route_manifest(path)
    assert any("invalid method" in e for e in errors)
    assert any("missing 'path'" in e for e in errors)


def test_missing_file_reported(tmp_path):
    errors = validate_route_manifest(tmp_path / "nope.json")
    assert errors and "not found" in errors[0]
