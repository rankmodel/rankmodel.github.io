"""Tests for monetization entities (users, API keys, organizations)."""

import pytest

from data.cache import ModelCache


@pytest.fixture
def cache(tmp_path):
    return ModelCache(db_path=str(tmp_path / "mon.db"))


def test_user_create_and_get(cache):
    cache.create_user("u1", "u1@x.com", "pro", "cus_123")
    u = cache.get_user("u1")
    assert u["plan_key"] == "pro"
    assert u["stripe_customer_id"] == "cus_123"
    assert cache.get_user("ghost") is None


def test_api_key_lifecycle(cache):
    cache.create_user("u1", plan_key="featured")
    cache.create_api_key("key-abc", "u1", "featured")
    assert cache.get_api_key_plan("key-abc") == "featured"
    cache.revoke_api_key("key-abc")
    assert cache.get_api_key_plan("key-abc") is None
    assert cache.get_api_key_plan("unknown") is None


def test_organization_certification(cache):
    cache.create_organization("org-1", "Acme Labs")
    assert cache.get_organization("org-1")["certified_until"] is None
    cache.certify_organization("org-1", 9999999999)
    assert cache.get_organization("org-1")["certified_until"] == 9999999999
