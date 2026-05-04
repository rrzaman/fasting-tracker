"""Tests for lambda_function/get_health_data.py.

Shared fixtures (aws_env, health_table, frozen_today_get_health_data)
live in tests/conftest.py.
"""

import json
from decimal import Decimal

import pytest


def _event(params=None):
    """HTTP API v2 GET event."""
    return {
        "requestContext": {"http": {"method": "GET"}},
        "queryStringParameters": params or {},
    }


class TestEmptyTable:
    """Empty health-snapshots table returns a valid zero-item response."""

    def test_returns_zero_count_and_empty_data(self, health_table,
                                               frozen_today_get_health_data):
        from lambda_function.get_health_data import handler

        resp = handler(_event(), None)

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["count"] == 0
        assert body["data"] == []

    def test_response_contains_date_range_keys(self, health_table,
                                               frozen_today_get_health_data):
        from lambda_function.get_health_data import handler

        body = json.loads(handler(_event(), None)["body"])

        assert "start_date" in body
        assert "end_date" in body


class TestItemsReturnedCorrectly:
    """Seeded items are returned with all fields intact."""

    def test_returns_seeded_items(self, health_table, frozen_today_get_health_data):
        health_table.put_item(Item={
            "date": "2026-04-15", "metric": "resting_heart_rate", "value": Decimal("72")})
        health_table.put_item(Item={
            "date": "2026-04-15", "metric": "weight",             "value": Decimal("75")})
        from lambda_function.get_health_data import handler

        body = json.loads(handler(_event({"days": "90"}), None)["body"])

        assert body["count"] == 2
        metrics = {item["metric"] for item in body["data"]}
        assert metrics == {"resting_heart_rate", "weight"}

    def test_correct_field_values(self, health_table, frozen_today_get_health_data):
        health_table.put_item(
            Item={"date": "2026-04-20",
                  "metric": "resting_heart_rate", "value": Decimal("68")}
        )
        from lambda_function.get_health_data import handler

        items = json.loads(
            handler(_event({"days": "90"}), None)["body"])["data"]

        assert items[0]["date"] == "2026-04-20"
        assert items[0]["metric"] == "resting_heart_rate"

    def test_decimal_values_serialized_as_float(self, health_table,
                                                frozen_today_get_health_data):
        health_table.put_item(
            Item={"date": "2026-04-20", "metric": "weight",
                  "value": Decimal("75.5")}
        )
        from lambda_function.get_health_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]

        assert isinstance(items[0]["value"], float)
        assert items[0]["value"] == 75.5

    def test_items_sorted_by_date_then_metric(self, health_table,
                                              frozen_today_get_health_data):
        health_table.put_item(Item={
            "date": "2026-04-20", "metric": "weight",             "value": Decimal("75")})
        health_table.put_item(Item={
            "date": "2026-04-10", "metric": "weight",             "value": Decimal("74")})
        health_table.put_item(Item={
            "date": "2026-04-20", "metric": "resting_heart_rate", "value": Decimal("70")})
        from lambda_function.get_health_data import handler

        items = json.loads(
            handler(_event({"days": "90"}), None)["body"])["data"]

        keys = [(i["date"], i["metric"]) for i in items]
        assert keys == sorted(keys)


class TestDateRangeFiltering:
    """Only items within the requested date window are returned.

    FIXED_TODAY = 2026-05-01.
    days=30  → range 2026-04-01..2026-05-01
    days=90  → range 2026-01-31..2026-05-01
    """

    def test_item_outside_range_excluded(self, health_table,
                                         frozen_today_get_health_data):
        health_table.put_item(Item={
            # in range
            "date": "2026-04-15", "metric": "weight", "value": Decimal("74")})
        health_table.put_item(Item={"date": "2026-01-01", "metric": "weight",
                                    "value": Decimal("80")})  # out of range
        from lambda_function.get_health_data import handler

        body = json.loads(handler(_event({"days": "30"}), None)["body"])

        assert body["count"] == 1
        assert body["data"][0]["date"] == "2026-04-15"

    def test_items_inside_range_all_included(self, health_table,
                                             frozen_today_get_health_data):
        health_table.put_item(Item={
            # 1 day ago
            "date": "2026-04-30", "metric": "weight", "value": Decimal("74")})
        health_table.put_item(Item={"date": "2026-04-20", "metric": "weight",
                                    "value": Decimal("75")})  # 11 days ago
        from lambda_function.get_health_data import handler

        # days=15 → start = 2026-04-16; both items fall within range
        body = json.loads(handler(_event({"days": "15"}), None)["body"])

        dates = {i["date"] for i in body["data"]}
        assert "2026-04-30" in dates
        assert "2026-04-20" in dates

    def test_start_and_end_date_in_response(self, health_table,
                                            frozen_today_get_health_data):
        from lambda_function.get_health_data import handler

        body = json.loads(handler(_event({"days": "30"}), None)["body"])

        assert body["start_date"] == "2026-04-01"
        assert body["end_date"] == "2026-05-01"

    def test_default_days_is_90(self, health_table, frozen_today_get_health_data):
        from lambda_function.get_health_data import handler

        body = json.loads(handler(_event(), None)["body"])

        # FIXED_TODAY(2026-05-01) - 90 days = 2026-01-31
        assert body["start_date"] == "2026-01-31"
        assert body["end_date"] == "2026-05-01"


class TestMetricFilter:
    """Optional ?metric= parameter narrows results to a single metric."""

    def test_filters_to_requested_metric(self, health_table,
                                         frozen_today_get_health_data):
        health_table.put_item(Item={
            "date": "2026-04-20", "metric": "weight",             "value": Decimal("75")})
        health_table.put_item(Item={
            "date": "2026-04-20", "metric": "resting_heart_rate", "value": Decimal("70")})
        from lambda_function.get_health_data import handler

        body = json.loads(
            handler(_event({"days": "90", "metric": "weight"}), None)["body"])

        assert body["count"] == 1
        assert body["data"][0]["metric"] == "weight"

    def test_nonexistent_metric_returns_empty(self, health_table,
                                              frozen_today_get_health_data):
        health_table.put_item(
            Item={"date": "2026-04-20",
                  "metric": "weight", "value": Decimal("75")}
        )
        from lambda_function.get_health_data import handler

        body = json.loads(
            handler(_event({"metric": "nonexistent"}), None)["body"])

        assert body["count"] == 0
        assert body["data"] == []


class TestCorsHeaders:
    """Access-Control-Allow-Origin is present on all responses."""

    def test_cors_header_present(self, health_table, frozen_today_get_health_data):
        from lambda_function.get_health_data import handler

        resp = handler(_event(), None)

        assert resp["headers"]["Access-Control-Allow-Origin"] == "*"


class TestLegacyEventFormat:
    """Handler resolves HTTP method from old httpMethod key (REST API format)."""

    def test_httpmethod_key_works(self, health_table, frozen_today_get_health_data):
        from lambda_function.get_health_data import handler

        resp = handler(
            {"httpMethod": "GET", "queryStringParameters": {}}, None)

        assert resp["statusCode"] == 200


# ===========================================================================
# Coverage gaps for decimal_to_float and pagination — originally lived in
# test_lambda_gaps.py.
# ===========================================================================

class TestDecimalToFloatError:
    """decimal_to_float raises TypeError for non-Decimal objects."""

    def test_raises_for_list(self):
        from lambda_function.get_health_data import decimal_to_float
        with pytest.raises(TypeError, match="not JSON serializable"):
            decimal_to_float([1, 2])


class TestPagination:
    """Pagination: when scan returns LastEvaluatedKey, the handler pages through."""

    def test_pagination(self, health_table, frozen_today_get_health_data):
        # FIXED_TODAY=2026-05-01, days=30 → range 2026-04-01..2026-05-01
        for i in range(5):
            health_table.put_item(
                Item={"date": f"2026-04-{i+1:02d}", "metric": "steps",
                      "value": Decimal("1000")}
            )

        from lambda_function.get_health_data import handler

        resp = handler({"queryStringParameters": {"days": "30"}}, None)
        body = json.loads(resp["body"])
        assert body["count"] == 5
