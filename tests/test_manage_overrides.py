"""Tests for lambda_function/manage_overrides.py.

Shared fixtures (aws_env, fasting_table, overrides_table) live in
tests/conftest.py.
"""

import json
from datetime import timedelta
from datetime import datetime as dt
from decimal import Decimal

import pytest


def _event(method, body=None, params=None):
    return {
        "httpMethod": method,
        "body": json.dumps(body) if body else None,
        "queryStringParameters": params or {},
    }


def _event_v2(method, body=None, params=None):
    """HTTP API v2 payload — method lives in requestContext, no httpMethod key."""
    return {
        "requestContext": {"http": {"method": method}},
        "body": json.dumps(body) if body else None,
        "queryStringParameters": params or {},
    }


class TestGet:
    """GET /overrides — returns all overrides sorted by date."""

    def test_empty_table_returns_zero_count(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(_event("GET"), None)

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["count"] == 0
        assert body["data"] == []

    def test_returns_all_items(self, overrides_table, fasting_table):
        overrides_table.put_item(Item={"date": "2026-04-10", "override_type": "skipped"})
        overrides_table.put_item(Item={"date": "2026-04-20", "override_type": "extra"})

        from lambda_function.manage_overrides import handler

        resp = handler(_event("GET"), None)

        body = json.loads(resp["body"])
        assert body["count"] == 2
        assert body["data"][0]["date"] == "2026-04-10"
        assert body["data"][1]["date"] == "2026-04-20"

    def test_items_sorted_by_date(self, overrides_table, fasting_table):
        # Insert out of order
        overrides_table.put_item(Item={"date": "2026-05-01", "override_type": "extra"})
        overrides_table.put_item(Item={"date": "2026-03-01", "override_type": "skipped"})
        overrides_table.put_item(Item={"date": "2026-04-01", "override_type": "extra"})

        from lambda_function.manage_overrides import handler

        resp = handler(_event("GET"), None)

        dates = [item["date"] for item in json.loads(resp["body"])["data"]]
        assert dates == sorted(dates)

    def test_cors_header_present(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(_event("GET"), None)

        assert resp["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_v2_event_returns_items(self, overrides_table, fasting_table):
        """HTTP API v2 payload (requestContext.http.method) is handled for GET."""
        overrides_table.put_item(Item={"date": "2026-04-10", "override_type": "skipped"})
        from lambda_function.manage_overrides import handler

        resp = handler(_event_v2("GET"), None)

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["count"] == 1
        assert body["data"][0]["date"] == "2026-04-10"


class TestPost:
    """POST /overrides — create a new override."""

    def test_create_skipped_override(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(
            _event("POST", {"date": "2026-05-05", "override_type": "skipped"}), None)

        assert resp["statusCode"] == 201
        body = json.loads(resp["body"])
        assert body["item"]["date"] == "2026-05-05"
        assert body["item"]["override_type"] == "skipped"
        assert "recorded_at" in body["item"]

    def test_create_extra_override(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(
            _event("POST", {"date": "2026-05-06", "override_type": "extra"}), None)

        assert resp["statusCode"] == 201
        assert json.loads(resp["body"])["item"]["override_type"] == "extra"

    def test_item_persisted_in_table(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        handler(_event("POST", {"date": "2026-05-07",
                "override_type": "skipped"}), None)

        stored = overrides_table.get_item(
            Key={"date": "2026-05-07"}).get("Item")
        assert stored is not None
        assert stored["override_type"] == "skipped"

    def test_copies_original_fast_type_from_fasting_table(self, overrides_table, fasting_table):
        fasting_table.put_item(
            Item={"date": "2026-05-08", "fast_type": "weekly_sunnah"}
        )
        from lambda_function.manage_overrides import handler

        resp = handler(
            _event("POST", {"date": "2026-05-08", "override_type": "skipped"}), None)

        body = json.loads(resp["body"])
        assert body["item"]["original_fast_type"] == "weekly_sunnah"

    def test_original_fast_type_none_when_no_fasting_record(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(
            _event("POST", {"date": "2026-06-01", "override_type": "extra"}), None)

        assert json.loads(resp["body"])["item"]["original_fast_type"] is None

    def test_missing_date_returns_400(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(_event("POST", {"override_type": "skipped"}), None)

        assert resp["statusCode"] == 400

    def test_invalid_override_type_returns_400(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(
            _event("POST", {"date": "2026-05-05", "override_type": "invalid"}), None)

        assert resp["statusCode"] == 400
        assert "skipped|extra" in json.loads(resp["body"])["error"]

    def test_empty_body_returns_400(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(_event("POST", {}), None)

        assert resp["statusCode"] == 400

    def test_recorded_at_is_valid_iso8601_utc(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(
            _event("POST", {"date": "2026-05-05", "override_type": "skipped"}), None)

        recorded_at = json.loads(resp["body"])["item"]["recorded_at"]
        parsed = dt.fromisoformat(recorded_at)
        assert parsed.tzinfo is not None
        assert parsed.utcoffset() == timedelta(0)

    def test_decimal_fields_serialized_as_float_in_get(self, overrides_table, fasting_table):
        overrides_table.put_item(
            Item={"date": "2026-05-12", "override_type": "extra",
                  "some_metric": Decimal("72.5")}
        )
        from lambda_function.manage_overrides import handler

        resp = handler(_event("GET"), None)

        assert resp["statusCode"] == 200
        item = json.loads(resp["body"])["data"][0]
        assert isinstance(item["some_metric"], float)
        assert item["some_metric"] == 72.5

    def test_v2_event_creates_override(self, overrides_table, fasting_table):
        """HTTP API v2 payload (requestContext.http.method) is handled for POST."""
        from lambda_function.manage_overrides import handler

        resp = handler(
            _event_v2("POST", {"date": "2026-05-20", "override_type": "skipped"}), None)

        assert resp["statusCode"] == 201
        body = json.loads(resp["body"])
        assert body["item"]["date"] == "2026-05-20"
        assert body["item"]["override_type"] == "skipped"


class TestPut:
    """PUT /overrides — update an existing override."""

    def test_update_override_type(self, overrides_table, fasting_table):
        overrides_table.put_item(
            Item={"date": "2026-05-10", "override_type": "skipped"}
        )
        from lambda_function.manage_overrides import handler

        resp = handler(
            _event("PUT", {"date": "2026-05-10", "override_type": "extra"}), None)

        assert resp["statusCode"] == 200
        assert json.loads(resp["body"])["message"] == "Override updated"

    def test_update_persisted_in_table(self, overrides_table, fasting_table):
        overrides_table.put_item(
            Item={"date": "2026-05-10", "override_type": "skipped"}
        )
        from lambda_function.manage_overrides import handler

        handler(_event("PUT", {"date": "2026-05-10",
                "override_type": "extra"}), None)

        stored = overrides_table.get_item(
            Key={"date": "2026-05-10"}).get("Item")
        assert stored["override_type"] == "extra"

    def test_update_refreshes_recorded_at(self, overrides_table, fasting_table):
        overrides_table.put_item(
            Item={"date": "2026-05-11", "override_type": "skipped",
                  "recorded_at": "2026-01-01T00:00:00+00:00"}
        )
        from lambda_function.manage_overrides import handler

        handler(_event("PUT", {"date": "2026-05-11",
                "override_type": "extra"}), None)

        stored = overrides_table.get_item(
            Key={"date": "2026-05-11"}).get("Item")
        assert stored["recorded_at"] != "2026-01-01T00:00:00+00:00"

    def test_missing_date_returns_400(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(_event("PUT", {"override_type": "extra"}), None)

        assert resp["statusCode"] == 400

    def test_invalid_override_type_returns_400(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(
            _event("PUT", {"date": "2026-05-10", "override_type": "bad"}), None)

        assert resp["statusCode"] == 400

    def test_v2_event_updates_override(self, overrides_table, fasting_table):
        """HTTP API v2 payload (requestContext.http.method) is handled for PUT."""
        overrides_table.put_item(
            Item={"date": "2026-05-10", "override_type": "skipped"}
        )
        from lambda_function.manage_overrides import handler

        resp = handler(
            _event_v2("PUT", {"date": "2026-05-10", "override_type": "extra"}), None)

        assert resp["statusCode"] == 200
        assert json.loads(resp["body"])["message"] == "Override updated"


class TestDelete:
    """DELETE /overrides?date=YYYY-MM-DD — remove an override."""

    def test_delete_existing_override(self, overrides_table, fasting_table):
        overrides_table.put_item(
            Item={"date": "2026-05-15", "override_type": "skipped"}
        )
        from lambda_function.manage_overrides import handler

        resp = handler(_event("DELETE", params={"date": "2026-05-15"}), None)

        assert resp["statusCode"] == 200
        assert "2026-05-15" in json.loads(resp["body"])["message"]

    def test_item_removed_from_table(self, overrides_table, fasting_table):
        overrides_table.put_item(
            Item={"date": "2026-05-15", "override_type": "skipped"}
        )
        from lambda_function.manage_overrides import handler

        handler(_event("DELETE", params={"date": "2026-05-15"}), None)

        stored = overrides_table.get_item(
            Key={"date": "2026-05-15"}).get("Item")
        assert stored is None

    def test_delete_non_existent_date_still_200(self, overrides_table, fasting_table):
        """DynamoDB delete_item is idempotent — deleting a missing key is not an error."""
        from lambda_function.manage_overrides import handler

        resp = handler(_event("DELETE", params={"date": "2099-01-01"}), None)

        assert resp["statusCode"] == 200

    def test_missing_date_param_returns_400(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(_event("DELETE"), None)

        assert resp["statusCode"] == 400
        assert "date" in json.loads(resp["body"])["error"]

    def test_null_query_string_parameters_returns_400(self, overrides_table, fasting_table):
        """Handles the case where API Gateway passes queryStringParameters as null."""
        from lambda_function.manage_overrides import handler

        event = {"httpMethod": "DELETE", "body": None,
                 "queryStringParameters": None}
        resp = handler(event, None)

        assert resp["statusCode"] == 400

    def test_v2_event_deletes_override(self, overrides_table, fasting_table):
        """HTTP API v2 payload (requestContext.http.method) is handled for DELETE."""
        overrides_table.put_item(
            Item={"date": "2026-05-15", "override_type": "skipped"}
        )
        from lambda_function.manage_overrides import handler

        resp = handler(_event_v2("DELETE", params={
                       "date": "2026-05-15"}), None)

        assert resp["statusCode"] == 200
        assert "2026-05-15" in json.loads(resp["body"])["message"]


class TestUnsupportedMethod:
    """Any HTTP method other than GET/POST/PUT/DELETE should return 405."""

    def test_patch_returns_405(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(_event("PATCH"), None)

        assert resp["statusCode"] == 405

    def test_head_returns_405(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler(_event("HEAD"), None)

        assert resp["statusCode"] == 405


class TestLegacyEventFormat:
    """Handler resolves HTTP method from old httpMethod key (REST API format)."""

    def test_get_via_httpmethod_key(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler({"httpMethod": "GET"}, None)

        assert resp["statusCode"] == 200

    def test_post_via_httpmethod_key(self, overrides_table, fasting_table):
        from lambda_function.manage_overrides import handler

        resp = handler({
            "httpMethod": "POST",
            "body": json.dumps({"date": "2026-05-10", "override_type": "extra"})
        }, None)

        assert resp["statusCode"] == 201


# ===========================================================================
# Coverage gaps for decimal_to_float and pagination — originally lived in
# test_lambda_gaps.py.
# ===========================================================================

class TestDecimalToFloatError:
    """decimal_to_float raises TypeError for non-Decimal objects."""

    def test_raises_for_dict(self):
        from lambda_function.manage_overrides import decimal_to_float
        with pytest.raises(TypeError, match="not JSON serializable"):
            decimal_to_float({"a": 1})


class TestPagination:
    """Pagination branch in manage_overrides GET handler."""

    def test_get_pagination(self, overrides_table, fasting_table):
        for i in range(5):
            overrides_table.put_item(
                Item={"date": f"2026-04-{i+1:02d}", "override_type": "skipped"}
            )

        from lambda_function.manage_overrides import handler
        resp = handler({"httpMethod": "GET"}, None)
        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["count"] == 5
