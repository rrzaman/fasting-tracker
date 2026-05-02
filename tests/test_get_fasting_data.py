import json
from datetime import date, timedelta
from decimal import Decimal

import boto3
import pytest
from moto import mock_aws

FASTING_TABLE = "fasting-records"
OVERRIDES_TABLE = "fasting-overrides"
FIXED_TODAY = date(2026, 5, 1)


class _FixedDate(date):
    """Subclass of date with a frozen today() for deterministic range tests."""
    @classmethod
    def today(cls):
        return FIXED_TODAY


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ca-west-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    import lambda_function.get_fasting_data as mod
    monkeypatch.setattr(mod, "date", _FixedDate)


def _create_tables(dynamodb):
    dynamodb.create_table(
        TableName=FASTING_TABLE,
        KeySchema=[{"AttributeName": "date", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "date", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    dynamodb.create_table(
        TableName=OVERRIDES_TABLE,
        KeySchema=[{"AttributeName": "date", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "date", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


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

    @mock_aws
    def test_returns_zero_count_and_empty_data(self):
        _create_tables(boto3.resource("dynamodb", region_name="ca-west-1"))
        from lambda_function.get_fasting_data import handler

        resp = handler(_event(), None)

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["count"] == 0
        assert body["data"] == []

    @mock_aws
    def test_response_contains_date_range_keys(self):
        _create_tables(boto3.resource("dynamodb", region_name="ca-west-1"))
        from lambda_function.get_fasting_data import handler

        body = json.loads(handler(_event(), None)["body"])

        assert "start_date" in body
        assert "end_date" in body


class TestItemsReturnedCorrectly:
    """Fasting records come back with all fields and in date order."""

    @mock_aws
    def test_returns_seeded_fasting_records(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_tables(ddb)
        table = ddb.Table(FASTING_TABLE)  # type: ignore[attr-defined]
        table.put_item(Item=_fasting_item("2026-04-14"))
        table.put_item(Item=_fasting_item("2026-04-21"))
        from lambda_function.get_fasting_data import handler

        body = json.loads(handler(_event(), None)["body"])

        assert body["count"] == 2
        assert {i["date"]
                for i in body["data"]} == {"2026-04-14", "2026-04-21"}

    @mock_aws
    def test_correct_field_values(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_tables(ddb)
        ddb.Table(FASTING_TABLE).put_item(  # type: ignore[attr-defined]
            Item=_fasting_item("2026-04-20", fast_type="arafah")
        )
        from lambda_function.get_fasting_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]

        assert items[0]["date"] == "2026-04-20"
        assert items[0]["fast_type"] == "arafah"
        assert items[0]["is_fasting"] is True

    @mock_aws
    def test_items_sorted_by_date(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_tables(ddb)
        table = ddb.Table(FASTING_TABLE)  # type: ignore[attr-defined]
        table.put_item(Item=_fasting_item("2026-04-28"))
        table.put_item(Item=_fasting_item("2026-04-14"))
        table.put_item(Item=_fasting_item("2026-04-21"))
        from lambda_function.get_fasting_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]

        dates = [i["date"] for i in items]
        assert dates == sorted(dates)

    @mock_aws
    def test_decimal_fields_serialized_as_float(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_tables(ddb)
        ddb.Table(FASTING_TABLE).put_item(  # type: ignore[attr-defined]
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

    @mock_aws
    def test_item_outside_range_excluded(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_tables(ddb)
        table = ddb.Table(FASTING_TABLE)  # type: ignore[attr-defined]
        table.put_item(Item=_fasting_item("2026-04-25"))  # inside  range
        table.put_item(Item=_fasting_item("2026-04-10"))  # outside range
        from lambda_function.get_fasting_data import handler

        body = json.loads(
            handler(_event({"days_back": "10", "days_forward": "10"}), None)["body"])

        assert body["count"] == 1
        assert body["data"][0]["date"] == "2026-04-25"

    @mock_aws
    def test_items_inside_range_all_included(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_tables(ddb)
        table = ddb.Table(FASTING_TABLE)  # type: ignore[attr-defined]
        table.put_item(Item=_fasting_item("2026-04-22"))  # inside
        # inside (5 days forward)
        table.put_item(Item=_fasting_item("2026-05-05"))
        from lambda_function.get_fasting_data import handler

        body = json.loads(
            handler(_event({"days_back": "10", "days_forward": "10"}), None)["body"])

        dates = {i["date"] for i in body["data"]}
        assert "2026-04-22" in dates
        assert "2026-05-05" in dates

    @mock_aws
    def test_start_and_end_date_in_response(self):
        _create_tables(boto3.resource("dynamodb", region_name="ca-west-1"))
        from lambda_function.get_fasting_data import handler

        body = json.loads(
            handler(_event({"days_back": "10", "days_forward": "10"}), None)["body"])

        assert body["start_date"] == "2026-04-21"
        assert body["end_date"] == "2026-05-11"

    @mock_aws
    def test_default_parameters(self):
        """Default days_back=365, days_forward=90."""
        _create_tables(boto3.resource("dynamodb", region_name="ca-west-1"))
        from lambda_function.get_fasting_data import handler

        body = json.loads(handler(_event(), None)["body"])

        # FIXED_TODAY(2026-05-01) - 365 = 2025-05-01; + 90 = 2026-07-30
        assert body["start_date"] == "2025-05-01"
        assert body["end_date"] == "2026-07-30"


class TestOverrideMerging:
    """Overrides are merged into fasting records before the response is built."""

    @mock_aws
    def test_skipped_override_sets_is_fasting_false(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_tables(ddb)
        ddb.Table(FASTING_TABLE).put_item(  # type: ignore[attr-defined]
            Item=_fasting_item("2026-04-21", fast_type="weekly_sunnah")
        )
        ddb.Table(OVERRIDES_TABLE).put_item(  # type: ignore[attr-defined]
            Item={"date": "2026-04-21", "override_type": "skipped"}
        )
        from lambda_function.get_fasting_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]
        item = next(i for i in items if i["date"] == "2026-04-21")

        assert item["is_fasting"] is False

    @mock_aws
    def test_skipped_override_clears_fast_type(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_tables(ddb)
        ddb.Table(FASTING_TABLE).put_item(  # type: ignore[attr-defined]
            Item=_fasting_item("2026-04-21", fast_type="weekly_sunnah")
        )
        ddb.Table(OVERRIDES_TABLE).put_item(  # type: ignore[attr-defined]
            Item={"date": "2026-04-21", "override_type": "skipped"}
        )
        from lambda_function.get_fasting_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]
        item = next(i for i in items if i["date"] == "2026-04-21")

        assert item["fast_type"] is None
        assert item["override"] == "skipped"

    @mock_aws
    def test_extra_override_on_existing_record_sets_is_fasting_true(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_tables(ddb)
        ddb.Table(FASTING_TABLE).put_item(  # type: ignore[attr-defined]
            Item=_fasting_item("2026-04-21", is_fasting=False)
        )
        ddb.Table(OVERRIDES_TABLE).put_item(  # type: ignore[attr-defined]
            Item={"date": "2026-04-21", "override_type": "extra"}
        )
        from lambda_function.get_fasting_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]
        item = next(i for i in items if i["date"] == "2026-04-21")

        assert item["is_fasting"] is True
        assert item["override"] == "extra"

    @mock_aws
    def test_extra_override_on_non_scheduled_day_creates_new_record(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_tables(ddb)
        # No fasting record for this date — override creates one
        ddb.Table(OVERRIDES_TABLE).put_item(  # type: ignore[attr-defined]
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

    @mock_aws
    def test_override_outside_range_not_applied(self):
        """An override for a date outside the query window must not appear."""
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_tables(ddb)
        ddb.Table(OVERRIDES_TABLE).put_item(  # type: ignore[attr-defined]
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

    @mock_aws
    def test_cors_header_present(self):
        _create_tables(boto3.resource("dynamodb", region_name="ca-west-1"))
        from lambda_function.get_fasting_data import handler

        resp = handler(_event(), None)

        assert resp["headers"]["Access-Control-Allow-Origin"] == "*"


class TestLegacyEventFormat:
    """Handler resolves HTTP method from old httpMethod key (REST API format)."""

    @mock_aws
    def test_httpmethod_key_works(self):
        _create_tables(boto3.resource("dynamodb", region_name="ca-west-1"))
        from lambda_function.get_fasting_data import handler

        resp = handler(
            {"httpMethod": "GET", "queryStringParameters": {}}, None)

        assert resp["statusCode"] == 200
