"""Tests for scope loading, authorization, and scope enforcement."""

import pytest
import yaml

from pentest_agent.scope import (
    ScopeNotAuthorized,
    ScopeViolation,
    assert_in_scope,
    is_authorized,
    load_scope,
    require_authorized,
)


def _write_scope(tmp_path, **overrides):
    base = {
        "engagement": {"client": "TestCo"},
        "targets": [
            {"host": "example.com", "ports": [80, 443]},
            {"host": "10.0.0.0/24"},
        ],
        "exclusions": [{"host": "10.0.0.5", "reason": "db"}],
        "intensity": "standard",
        "authorization": {
            "signed_by": "Tester",
            "signed_date": "2026-09-19",
            "statement": "authorized",
        },
    }
    base.update(overrides)
    path = tmp_path / "scope.yaml"
    path.write_text(yaml.safe_dump(base))
    return path


def test_load_scope_ok(tmp_path):
    scope = load_scope(_write_scope(tmp_path))
    assert scope["intensity"] == "standard"
    assert len(scope["targets"]) == 2


def test_load_scope_bad_intensity(tmp_path):
    with pytest.raises(ValueError, match="invalid intensity"):
        load_scope(_write_scope(tmp_path, intensity="aggressive"))


def test_load_scope_no_targets(tmp_path):
    with pytest.raises(ValueError, match="non-empty 'targets'"):
        load_scope(_write_scope(tmp_path, targets=[]))


def test_require_authorized_needs_flag(tmp_path):
    scope = load_scope(_write_scope(tmp_path))
    with pytest.raises(ScopeNotAuthorized, match="--i-am-authorized"):
        require_authorized(scope, cli_flag=False)


def test_require_authorized_needs_signature(tmp_path):
    scope = load_scope(_write_scope(tmp_path, authorization={}))
    assert not is_authorized(scope)
    with pytest.raises(ScopeNotAuthorized, match="not signed"):
        require_authorized(scope, cli_flag=True)


def test_require_authorized_ok(tmp_path):
    scope = load_scope(_write_scope(tmp_path))
    require_authorized(scope, cli_flag=True)  # must not raise


def test_in_scope_exact_and_port(tmp_path):
    scope = load_scope(_write_scope(tmp_path))
    assert_in_scope(scope, "example.com", 80)
    with pytest.raises(ScopeViolation, match="Port 22"):
        assert_in_scope(scope, "example.com", 22)


def test_in_scope_cidr(tmp_path):
    scope = load_scope(_write_scope(tmp_path))
    assert_in_scope(scope, "10.0.0.42")  # inside 10.0.0.0/24
    with pytest.raises(ScopeViolation, match="NOT in the authorized"):
        assert_in_scope(scope, "10.0.1.9")


def test_exclusion_wins_over_cidr(tmp_path):
    scope = load_scope(_write_scope(tmp_path))
    with pytest.raises(ScopeViolation, match="explicitly EXCLUDED"):
        assert_in_scope(scope, "10.0.0.5")


def test_unknown_host_refused(tmp_path):
    scope = load_scope(_write_scope(tmp_path))
    with pytest.raises(ScopeViolation):
        assert_in_scope(scope, "evil.example")
