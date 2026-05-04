"""Tests for lambda_function/get_fasting_data.py.

Shared fixtures (aws_env, fasting_table, overrides_table,
frozen_today_get_fasting_data) live in tests/conftest.py.
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


def _fasting_item(date_str, fast_type="weekly_sunnah", is_fasting=True):
    return {
        "date":         date_str,
        "fast_type":    fast_type,
        "is_fasting":   is_fasting,
        "hijri_month":  Decimal("10"),
        "hijri_day":    Decimal("13"),
    }


class TestEmptyTables:
    """Both tables empty → valid zero-item response."""

    def test_returns_zero_count_and_empty_data(self, fasting_table, overrides_table,
                                               frozen_today_get_fasting_data):
        from lambda_function.get_fasting_data import handler

        resp = handler(_event(), None)

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["count"] == 0
        assert body["data"] == []

    def test_response_contains_date_range_keys(self, fasting_table, overrides_table,
                                               frozen_today_get_fasting_data):
        from lambda_function.get_fasting_data import handler

        body = json.loads(handler(_event(), None)["body"])

        assert "start_date" in body
        assert "end_date" in body


class TestItemsReturnedCorrectly:
    """Fasting records come back with all fields and in date order."""

    def test_returns_seeded_fasting_records(self, fasting_table, overrides_table,
                                            frozen_today_get_fasting_data):
        fasting_table.put_item(Item=_fasting_item("2026-04-14"))
        fasting_table.put_item(Item=_fasting_item("2026-04-21"))
        from lambda_function.get_fasting_data import handler

        body = json.loads(handler(_event(), None)["body"])

        assert body["count"] == 2
        assert {i["date"]
                for i in body["data"]} == {"2026-04-14", "2026-04-21"}

    def test_correct_field_values(self, fasting_table, overrides_table,
                                  frozen_today_get_fasting_data):
        fasting_table.put_item(
            Item=_fasting_item("2026-04-20", fast_type="arafah")
        )
        from lambda_function.get_fasting_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]

        assert items[0]["date"] == "2026-04-20"
        assert items[0]["fast_type"] == "arafah"
        assert items[0]["is_fasting"] is True

    def test_items_sorted_by_date(self, fasting_table, overrides_table,
                                  frozen_today_get_fasting_data):
        fasting_table.put_item(Item=_fasting_item("2026-04-28"))
        fasting_table.put_item(Item=_fasting_item("2026-04-14"))
        fasting_table.put_item(Item=_fasting_item("2026-04-21"))
        from lambda_function.get_fasting_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]

        dates = [i["date"] for i in items]
        assert dates == sorted(dates)

    def test_decimal_fields_serialized_as_float(self, fasting_table, overrides_table,
                                                frozen_today_get_fasting_data):
        fasting_table.put_item(
            Item=_fasting_item("2026-04-20")
        )
        from lambda_function.get_fasting_data import handler

        # Decimal hijri_month/hijri_day must not raise TypeError
        resp = handler(_event(), None)
        assert resp["statusCode"] == 200
        items = json.loads(resp["body"])["data"]
        assert isinstance(items[0]["hijri_month"], float)


class TestDateRangeFiltering:
    """Only records within the requested window are returned.

    FIXED_TODAY = 2026-05-01.
    days_back=10, days_forward=10 → range 2026-04-21..2026-05-11
    """

    def test_item_outside_range_excluded(self, fasting_table, overrides_table,
                                         frozen_today_get_fasting_data):
        fasting_table.put_item(Item=_fasting_item(
            "2026-04-25"))  # inside  range
        fasting_table.put_item(Item=_fasting_item(
            "2026-04-10"))  # outside range
        from lambda_function.get_fasting_data import handler

        body = json.loads(
            handler(_event({"days_back": "10", "days_forward": "10"}), None)["body"])

        assert body["count"] == 1
        assert body["data"][0]["date"] == "2026-04-25"

    def test_items_inside_range_all_included(self, fasting_table, overrides_table,
                                             frozen_today_get_fasting_data):
        fasting_table.put_item(Item=_fasting_item("2026-04-22"))  # inside
        # inside (5 days forward)
        fasting_table.put_item(Item=_fasting_item("2026-05-05"))
        from lambda_function.get_fasting_data import handler

        body = json.loads(
            handler(_event({"days_back": "10", "days_forward": "10"}), None)["body"])

        dates = {i["date"] for i in body["data"]}
        assert "2026-04-22" in dates
        assert "2026-05-05" in dates

    def test_start_and_end_date_in_response(self, fasting_table, overrides_table,
                                            frozen_today_get_fasting_data):
        from lambda_function.get_fasting_data import handler

        body = json.loads(
            handler(_event({"days_back": "10", "days_forward": "10"}), None)["body"])

        assert body["start_date"] == "2026-04-21"
        assert body["end_date"] == "2026-05-11"

    def test_default_parameters(self, fasting_table, overrides_table,
                                frozen_today_get_fasting_data):
        """Default days_back=365, days_forward=90."""
        from lambda_function.get_fasting_data import handler

        body = json.loads(handler(_event(), None)["body"])

        # FIXED_TODAY(2026-05-01) - 365 = 2025-05-01; + 90 = 2026-07-30
        assert body["start_date"] == "2025-05-01"
        assert body["end_date"] == "2026-07-30"


class TestOverrideMerging:
    """Overrides are merged into fasting records before the response is built."""

    def test_skipped_override_sets_is_fasting_false(self, fasting_table, overrides_table,
                                                    frozen_today_get_fasting_data):
        fasting_table.put_item(
            Item=_fasting_item("2026-04-21", fast_type="weekly_sunnah")
        )
        overrides_table.put_item(
            Item={"date": "2026-04-21", "override_type": "skipped"}
        )
        from lambda_function.get_fasting_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]
        item = next(i for i in items if i["date"] == "2026-04-21")

        assert item["is_fasting"] is False

    def test_skipped_override_clears_fast_type(self, fasting_table, overrides_table,
                                               frozen_today_get_fasting_data):
        fasting_table.put_item(
            Item=_fasting_item("2026-04-21", fast_type="weekly_sunnah")
        )
        overrides_table.put_item(
            Item={"date": "2026-04-21", "override_type": "skipped"}
        )
        from lambda_function.get_fasting_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]
        item = next(i for i in items if i["date"] == "2026-04-21")

        assert item["fast_type"] is None
        assert item["override"] == "skipped"

    def test_extra_override_on_existing_record_sets_is_fasting_true(self, fasting_table,
                                                                    overrides_table,
                                                                    frozen_today_get_fasting_data):
        fasting_table.put_item(
            Item=_fasting_item("2026-04-21", is_fasting=False)
        )
        overrides_table.put_item(
            Item={"date": "2026-04-21", "override_type": "extra"}
        )
        from lambda_function.get_fasting_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]
        item = next(i for i in items if i["date"] == "2026-04-21")

        assert item["is_fasting"] is True
        assert item["override"] == "extra"

    def test_extra_override_on_non_scheduled_day_creates_new_record(self, fasting_table,
                                                                    overrides_table,
                                                                    frozen_today_get_fasting_data):
        # No fasting record for this date — override creates one
        overrides_table.put_item(
            Item={"date": "2026-04-22", "override_type": "extra"}
        )
        from lambda_function.get_fasting_data import handler

        body = json.loads(handler(_event(), None)["body"])
        item = next((i for i in body["data"]
                    if i["date"] == "2026-04-22"), None)

        assert item is not None
        assert item["is_fasting"] is True
        assert item["fast_type"] == "extra"
        assert item["override"] == "extra"

    def test_override_outside_range_not_applied(self, fasting_table, overrides_table,
                                                frozen_today_get_fasting_data):
        """An override for a date outside the query window must not appear."""
        overrides_table.put_item(
            Item={"date": "2026-04-10", "override_type": "extra"}
        )
        from lambda_function.get_fasting_data import handler

        # days_back=5 → start = 2026-04-26; override date 2026-04-10 is outside
        body = json.loads(
            handler(_event({"days_back": "5", "days_forward": "5"}), None)["body"])

        dates = {i["date"] for i in body["data"]}
        assert "2026-04-10" not in dates


class TestCorsHeaders:
    """Access-Control-Allow-Origin is present on all responses."""

    def test_cors_header_present(self, fasting_table, overrides_table,
                                 frozen_today_get_fasting_data):
        from lambda_function.get_fasting_data import handler

        resp = handler(_event(), None)

        assert resp["headers"]["Access-Control-Allow-Origin"] == "*"


class TestLegacyEventFormat:
    """Handler resolves HTTP method from old httpMethod key (REST API format)."""

    def test_httpmethod_key_works(self, fasting_table, overrides_table,
                                  frozen_today_get_fasting_data):
        from lambda_function.get_fasting_data import handler

        resp = handler(
            {"httpMethod": "GET", "queryStringParameters": {}}, None)

        assert resp["statusCode"] == 200


# ===========================================================================
# Coverage gaps for decimal_to_float and pagination — originally lived in
# test_lambda_gaps.py.
# ===========================================================================

class TestDecimalToFloatError:
    """decimal_to_float raises TypeError for non-Decimal objects."""

    def test_raises_for_string(self):
        from lambda_function.get_fasting_data import decimal_to_float
        with pytest.raises(TypeError, match="not JSON serializable"):
            decimal_to_float("hello")


class TestPagination:
    """Pagination: when scan returns LastEvaluatedKey, the handler pages through."""

    def test_fasting_table_pagination(self, fasting_table, overrides_table,
                                      frozen_today_get_fasting_data):
        # FIXED_TODAY=2026-05-01, days_back=10 → range 2026-04-21..2026-05-11.
        # Seed five items inside that window to exercise the paging loop.
        for i in range(5):
            fasting_table.put_item(Item={
                "date": f"2026-04-{22+i:02d}",
                "is_fasting": True,
                "fast_type": "weekly_sunnah",
            })

        from lambda_function.get_fasting_data import handler

        resp = handler({"queryStringParameters": {
                       "days_back": "10", "days_forward": "10"}}, None)
        body = json.loads(resp["body"])
        assert body["count"] == 5
        dates = sorted([i["date"] for i in body["data"]])
        assert dates == [f"2026-04-{22+i:02d}" for i in range(5)]

    def test_overrides_table_pagination(self, fasting_table, overrides_table,
                                        frozen_today_get_fasting_data):
        for i in range(5):
            overrides_table.put_item(
                Item={"date": f"2026-04-{22+i:02d}",
                      "override_type": "skipped"}
            )

        from lambda_function.get_fasting_data import handler

        resp = handler({"queryStringParameters": {
                       "days_back": "10", "days_forward": "10"}}, None)
        body = json.loads(resp["body"])
        assert body["count"] == 5
