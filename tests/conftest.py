"""Shared pytest fixtures for the fasting-tracker test suite.

Anything defined here is auto-discovered by pytest and made available to
every test under `tests/` without an explicit import.

What lives here:
- AWS credential env vars (autouse) so boto3 never reaches real AWS.
- A `dynamodb` fixture that yields a moto-backed DynamoDB resource.
- One factory fixture per DynamoDB table the project uses; each creates
  the table and returns the boto3 Table handle ready to use.
- Constants for time-frozen tests (`FIXED_TODAY`, `FixedDate`).
"""

from datetime import date

import boto3
import pytest
from moto import mock_aws


# ---------------------------------------------------------------------------
# Time-freezing helpers used by handlers that call date.today()
# ---------------------------------------------------------------------------

FIXED_TODAY = date(2026, 5, 1)


class FixedDate(date):
    """Subclass of date with a frozen today() for deterministic range tests."""
    @classmethod
    def today(cls):
        return FIXED_TODAY


# ---------------------------------------------------------------------------
# AWS environment
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    """Dummy AWS credentials so boto3 never reaches real AWS."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ca-west-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")


@pytest.fixture
def _aws_mock():
    """Private fixture that activates moto's mock_aws context.

    Other AWS-resource fixtures (dynamodb, s3_client) depend on this so a
    single moto activation is shared when a test requests multiple services.
    """
    with mock_aws():
        yield


@pytest.fixture
def dynamodb(_aws_mock):
    """Moto-backed DynamoDB resource. Use as `def test_foo(dynamodb):`."""
    return boto3.resource("dynamodb", region_name="ca-west-1")


@pytest.fixture
def s3_client(_aws_mock):
    """Moto-backed S3 client with the project bucket pre-created."""
    client = boto3.client("s3", region_name="ca-west-1")
    client.create_bucket(
        Bucket="fasting-tracker-rayyan",
        CreateBucketConfiguration={"LocationConstraint": "ca-west-1"},
    )
    return client


# ---------------------------------------------------------------------------
# Per-table factory fixtures — each returns a ready-to-use boto3 Table handle
# ---------------------------------------------------------------------------

@pytest.fixture
def fasting_table(dynamodb):
    """fasting-records table — partition key only on date."""
    dynamodb.create_table(
        TableName="fasting-records",
        KeySchema=[{"AttributeName": "date", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "date", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    return dynamodb.Table("fasting-records")


@pytest.fixture
def health_table(dynamodb):
    """health-snapshots table — composite key (date, metric)."""
    dynamodb.create_table(
        TableName="health-snapshots",
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
    return dynamodb.Table("health-snapshots")


@pytest.fixture
def overrides_table(dynamodb):
    """fasting-overrides table — partition key only on date."""
    dynamodb.create_table(
        TableName="fasting-overrides",
        KeySchema=[{"AttributeName": "date", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "date", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    return dynamodb.Table("fasting-overrides")


@pytest.fixture
def reminder_log_table(dynamodb):
    """reminder-log table — composite key (date, fast_type)."""
    dynamodb.create_table(
        TableName="reminder-log",
        KeySchema=[
            {"AttributeName": "date",      "KeyType": "HASH"},
            {"AttributeName": "fast_type", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "date",      "AttributeType": "S"},
            {"AttributeName": "fast_type", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return dynamodb.Table("reminder-log")


@pytest.fixture
def recipients_table(dynamodb):
    """notification-recipients table — partition key only on phone."""
    dynamodb.create_table(
        TableName="notification-recipients",
        KeySchema=[{"AttributeName": "phone", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "phone", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    return dynamodb.Table("notification-recipients")


# ---------------------------------------------------------------------------
# Per-module time-freezing fixtures
# Each Lambda module imports its own date/get_local_today reference, so the
# patch must target that module specifically.
# ---------------------------------------------------------------------------

@pytest.fixture
def frozen_today_reminder(monkeypatch):
    """Pin reminder_function.get_local_today() to FIXED_TODAY (2026-05-01)."""
    from lambda_function import reminder_function
    monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)


@pytest.fixture
def frozen_today_get_fasting_data(monkeypatch):
    """Pin get_fasting_data.date.today() to FIXED_TODAY (2026-05-01)."""
    import lambda_function.get_fasting_data as mod
    monkeypatch.setattr(mod, "date", FixedDate)


@pytest.fixture
def frozen_today_get_health_data(monkeypatch):
    """Pin get_health_data.date.today() to FIXED_TODAY (2026-05-01)."""
    import lambda_function.get_health_data as mod
    monkeypatch.setattr(mod, "date", FixedDate)
