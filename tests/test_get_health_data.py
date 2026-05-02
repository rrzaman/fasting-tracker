import json
from datetime import date, timedelta
from decimal import Decimal

import boto3
import pytest
from moto import mock_aws

HEALTH_TABLE = "health-snapshots"
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
    import lambda_function.get_health_data as mod
    monkeypatch.setattr(mod, "date", _FixedDate)


def _create_health_table(dynamodb):
    dynamodb.create_table(
        TableName=HEALTH_TABLE,
        KeySchema=[
            {"AttributeName": "date",   "KeyType": "HASH"},
            {"AttributeName": "metric", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "date",   "AttributeType": "S"},
            {"AttributeName": "metric", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


def _event(params=None):
    """HTTP API v2 GET event."""
    return {
        "requestContext": {"http": {"method": "GET"}},
        "queryStringParameters": params or {},
    }


class TestEmptyTable:
    """Empty health-snapshots table returns a valid zero-item response."""

    @mock_aws
    def test_returns_zero_count_and_empty_data(self):
        _create_health_table(boto3.resource(
            "dynamodb", region_name="ca-west-1"))
        from lambda_function.get_health_data import handler

        resp = handler(_event(), None)

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["count"] == 0
        assert body["data"] == []

    @mock_aws
    def test_response_contains_date_range_keys(self):
        _create_health_table(boto3.resource(
            "dynamodb", region_name="ca-west-1"))
        from lambda_function.get_health_data import handler

        body = json.loads(handler(_event(), None)["body"])

        assert "start_date" in body
        assert "end_date" in body


class TestItemsReturnedCorrectly:
    """Seeded items are returned with all fields intact."""

    @mock_aws
    def test_returns_seeded_items(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_health_table(ddb)
        table = ddb.Table(HEALTH_TABLE)  # type: ignore[attr-defined]
        table.put_item(Item={
                       "date": "2026-04-15", "metric": "resting_heart_rate", "value": Decimal("72")})
        table.put_item(Item={
                       "date": "2026-04-15", "metric": "weight",             "value": Decimal("75")})
        from lambda_function.get_health_data import handler

        body = json.loads(handler(_event({"days": "90"}), None)["body"])

        assert body["count"] == 2
        metrics = {item["metric"] for item in body["data"]}
        assert metrics == {"resting_heart_rate", "weight"}

    @mock_aws
    def test_correct_field_values(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_health_table(ddb)
        ddb.Table(HEALTH_TABLE).put_item(  # type: ignore[attr-defined]
            Item={"date": "2026-04-20",
                  "metric": "resting_heart_rate", "value": Decimal("68")}
        )
        from lambda_function.get_health_data import handler

        items = json.loads(
            handler(_event({"days": "90"}), None)["body"])["data"]

        assert items[0]["date"] == "2026-04-20"
        assert items[0]["metric"] == "resting_heart_rate"

    @mock_aws
    def test_decimal_values_serialized_as_float(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_health_table(ddb)
        ddb.Table(HEALTH_TABLE).put_item(  # type: ignore[attr-defined]
            Item={"date": "2026-04-20", "metric": "weight",
                  "value": Decimal("75.5")}
        )
        from lambda_function.get_health_data import handler

        items = json.loads(handler(_event(), None)["body"])["data"]

        assert isinstance(items[0]["value"], float)
        assert items[0]["value"] == 75.5

    @mock_aws
    def test_items_sorted_by_date_then_metric(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_health_table(ddb)
        table = ddb.Table(HEALTH_TABLE)  # type: ignore[attr-defined]
        table.put_item(Item={
                       "date": "2026-04-20", "metric": "weight",             "value": Decimal("75")})
        table.put_item(Item={
                       "date": "2026-04-10", "metric": "weight",             "value": Decimal("74")})
        table.put_item(Item={
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

    @mock_aws
    def test_item_outside_range_excluded(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_health_table(ddb)
        table = ddb.Table(HEALTH_TABLE)  # type: ignore[attr-defined]
        table.put_item(Item={
                       # in range
                       "date": "2026-04-15", "metric": "weight", "value": Decimal("74")})
        table.put_item(Item={"date": "2026-01-01", "metric": "weight",
                       "value": Decimal("80")})  # out of range
        from lambda_function.get_health_data import handler

        body = json.loads(handler(_event({"days": "30"}), None)["body"])

        assert body["count"] == 1
        assert body["data"][0]["date"] == "2026-04-15"

    @mock_aws
    def test_items_inside_range_all_included(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_health_table(ddb)
        table = ddb.Table(HEALTH_TABLE)  # type: ignore[attr-defined]
        table.put_item(Item={
                       # 1 day ago
                       "date": "2026-04-30", "metric": "weight", "value": Decimal("74")})
        table.put_item(Item={"date": "2026-04-20", "metric": "weight",
                       "value": Decimal("75")})  # 11 days ago
        from lambda_function.get_health_data import handler

        # days=15 → start = 2026-04-16; both items fall within range
        body = json.loads(handler(_event({"days": "15"}), None)["body"])

        dates = {i["date"] for i in body["data"]}
        assert "2026-04-30" in dates
        assert "2026-04-20" in dates

    @mock_aws
    def test_start_and_end_date_in_response(self):
        _create_health_table(boto3.resource(
            "dynamodb", region_name="ca-west-1"))
        from lambda_function.get_health_data import handler

        body = json.loads(handler(_event({"days": "30"}), None)["body"])

        assert body["start_date"] == "2026-04-01"
        assert body["end_date"] == "2026-05-01"

    @mock_aws
    def test_default_days_is_90(self):
        _create_health_table(boto3.resource(
            "dynamodb", region_name="ca-west-1"))
        from lambda_function.get_health_data import handler

        body = json.loads(handler(_event(), None)["body"])

        # FIXED_TODAY(2026-05-01) - 90 days = 2026-01-31
        assert body["start_date"] == "2026-01-31"
        assert body["end_date"] == "2026-05-01"


class TestMetricFilter:
    """Optional ?metric= parameter narrows results to a single metric."""

    @mock_aws
    def test_filters_to_requested_metric(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_health_table(ddb)
        table = ddb.Table(HEALTH_TABLE)  # type: ignore[attr-defined]
        table.put_item(Item={
                       "date": "2026-04-20", "metric": "weight",             "value": Decimal("75")})
        table.put_item(Item={
                       "date": "2026-04-20", "metric": "resting_heart_rate", "value": Decimal("70")})
        from lambda_function.get_health_data import handler

        body = json.loads(
            handler(_event({"days": "90", "metric": "weight"}), None)["body"])

        assert body["count"] == 1
        assert body["data"][0]["metric"] == "weight"

    @mock_aws
    def test_nonexistent_metric_returns_empty(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_health_table(ddb)
        ddb.Table(HEALTH_TABLE).put_item(  # type: ignore[attr-defined]
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

    @mock_aws
    def test_cors_header_present(self):
        _create_health_table(boto3.resource(
            "dynamodb", region_name="ca-west-1"))
        from lambda_function.get_health_data import handler

        resp = handler(_event(), None)

        assert resp["headers"]["Access-Control-Allow-Origin"] == "*"


class TestLegacyEventFormat:
    """Handler resolves HTTP method from old httpMethod key (REST API format)."""

    @mock_aws
    def test_httpmethod_key_works(self):
        _create_health_table(boto3.resource(
            "dynamodb", region_name="ca-west-1"))
        from lambda_function.get_health_data import handler

        resp = handler(
            {"httpMethod": "GET", "queryStringParameters": {}}, None)

        assert resp["statusCode"] == 200
