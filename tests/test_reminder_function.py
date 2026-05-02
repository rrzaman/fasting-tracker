from calendar import timegm
from datetime import date, datetime as dt, timedelta

import boto3
import pytest
from moto import mock_aws

RECIPIENTS_TABLE = "notification-recipients"
REMINDER_LOG_TABLE = "reminder-log"
FIXED_TODAY = date(2026, 5, 1)


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    """Dummy AWS credentials so boto3 never reaches real AWS."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ca-west-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")


def _create_recipients_table(dynamodb):
    dynamodb.create_table(
        TableName=RECIPIENTS_TABLE,
        KeySchema=[{"AttributeName": "phone", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "phone", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


def _create_reminder_log_table(dynamodb):
    dynamodb.create_table(
        TableName=REMINDER_LOG_TABLE,
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


def _get_log_item(ddb, fast_type: str):
    """Helper: fetch a single record from the reminder-log table."""
    return ddb.Table(REMINDER_LOG_TABLE).get_item(  # type: ignore[attr-defined]
        Key={"date": str(FIXED_TODAY), "fast_type": fast_type}
    ).get("Item")


class TestGetRecipients:
    """get_recipients — scans notification-recipients and returns all items."""

    @mock_aws
    def test_returns_all_recipients(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_recipients_table(ddb)
        table = ddb.Table(RECIPIENTS_TABLE)  # type: ignore[attr-defined]
        table.put_item(Item={"phone": "+15550001111", "name": "Rayyan", "lang": "en"})
        table.put_item(Item={"phone": "+15550002222", "name": "Fatima", "lang": "bn"})
        from lambda_function.reminder_function import get_recipients

        result = get_recipients()

        assert {r["phone"] for r in result} == {"+15550001111", "+15550002222"}

    @mock_aws
    def test_empty_table_returns_empty_list(self):
        _create_recipients_table(boto3.resource("dynamodb", region_name="ca-west-1"))
        from lambda_function.reminder_function import get_recipients

        result = get_recipients()

        assert result == []

    @mock_aws
    def test_returns_correct_fields(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_recipients_table(ddb)
        ddb.Table(RECIPIENTS_TABLE).put_item(  # type: ignore[attr-defined]
            Item={"phone": "+15550001111", "name": "Rayyan", "lang": "en"}
        )
        from lambda_function.reminder_function import get_recipients

        result = get_recipients()

        assert len(result) == 1
        r = result[0]
        assert r["phone"] == "+15550001111"
        assert r["name"] == "Rayyan"
        assert r["lang"] == "en"

    @mock_aws
    def test_multiple_recipients_all_present(self):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_recipients_table(ddb)
        table = ddb.Table(RECIPIENTS_TABLE)  # type: ignore[attr-defined]
        recipients = [
            {"phone": f"+1555000{i:04d}", "name": f"User{i}", "lang": "en"}
            for i in range(5)
        ]
        for r in recipients:
            table.put_item(Item=r)
        from lambda_function.reminder_function import get_recipients

        result = get_recipients()

        assert len(result) == 5


class TestAlreadySentToday:
    """already_sent_today — reads reminder-log to guard against duplicate sends."""

    @mock_aws
    def test_returns_false_when_log_is_empty(self, monkeypatch):
        _create_reminder_log_table(boto3.resource("dynamodb", region_name="ca-west-1"))
        from lambda_function import reminder_function
        monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)

        result = reminder_function.already_sent_today("ramadan")

        assert result is False

    @mock_aws
    def test_returns_false_for_different_fast_type(self, monkeypatch):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_reminder_log_table(ddb)
        ddb.Table(REMINDER_LOG_TABLE).put_item(  # type: ignore[attr-defined]
            Item={"date": str(FIXED_TODAY), "fast_type": "arafah", "sent_at": "2026-05-01T08:00:00"}
        )
        from lambda_function import reminder_function
        monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)

        result = reminder_function.already_sent_today("ramadan")

        assert result is False

    @mock_aws
    def test_returns_false_when_log_exists_for_different_date(self, monkeypatch):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_reminder_log_table(ddb)
        yesterday = FIXED_TODAY - timedelta(days=1)
        ddb.Table(REMINDER_LOG_TABLE).put_item(  # type: ignore[attr-defined]
            Item={"date": str(yesterday), "fast_type": "ramadan", "sent_at": "2026-04-30T08:00:00"}
        )
        from lambda_function import reminder_function
        monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)

        result = reminder_function.already_sent_today("ramadan")

        assert result is False

    @mock_aws
    def test_returns_true_after_log_reminder_sent(self, monkeypatch):
        _create_reminder_log_table(boto3.resource("dynamodb", region_name="ca-west-1"))
        from lambda_function import reminder_function
        monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)

        reminder_function.log_reminder_sent("ramadan")
        result = reminder_function.already_sent_today("ramadan")

        assert result is True

    @mock_aws
    def test_returns_false_for_fast_type_not_yet_logged(self, monkeypatch):
        """Logging one fast type must not affect the guard for a different type."""
        _create_reminder_log_table(boto3.resource("dynamodb", region_name="ca-west-1"))
        from lambda_function import reminder_function
        monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)

        reminder_function.log_reminder_sent("ramadan")
        result = reminder_function.already_sent_today("arafah")

        assert result is False


class TestLogReminderSent:
    """log_reminder_sent — persists an idempotency record with a 30-day TTL."""

    @mock_aws
    def test_writes_record_to_table(self, monkeypatch):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_reminder_log_table(ddb)
        from lambda_function import reminder_function
        monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)

        reminder_function.log_reminder_sent("arafah")

        assert _get_log_item(ddb, "arafah") is not None

    @mock_aws
    def test_writes_correct_date_and_fast_type(self, monkeypatch):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_reminder_log_table(ddb)
        from lambda_function import reminder_function
        monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)

        reminder_function.log_reminder_sent("arafah")

        item = _get_log_item(ddb, "arafah")
        assert item["date"] == "2026-05-01"
        assert item["fast_type"] == "arafah"

    @mock_aws
    def test_writes_sent_at_as_tz_aware_iso8601(self, monkeypatch):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_reminder_log_table(ddb)
        from lambda_function import reminder_function
        monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)

        reminder_function.log_reminder_sent("arafah")

        sent_at = _get_log_item(ddb, "arafah")["sent_at"]
        parsed = dt.fromisoformat(sent_at)
        assert parsed.tzinfo is not None

    @mock_aws
    def test_writes_expires_at_as_integer(self, monkeypatch):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_reminder_log_table(ddb)
        from lambda_function import reminder_function
        monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)

        reminder_function.log_reminder_sent("arafah")

        # DynamoDB returns numbers as Decimal; int() handles both int and Decimal.
        expires_at = int(_get_log_item(ddb, "arafah")["expires_at"])
        assert isinstance(expires_at, int)
        assert expires_at > 0

    @mock_aws
    def test_expires_at_is_approximately_30_days_ahead(self, monkeypatch):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_reminder_log_table(ddb)
        from lambda_function import reminder_function
        monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)

        reminder_function.log_reminder_sent("arafah")

        expires_at = int(_get_log_item(ddb, "arafah")["expires_at"])
        # timegm converts the date's timetuple as UTC midnight; allow ±2 days for
        # any timezone offset between the test host and the strftime("%s") result.
        expected_ts = timegm((FIXED_TODAY + timedelta(days=30)).timetuple())
        assert abs(expires_at - expected_ts) < 86400 * 2

    @mock_aws
    def test_separate_fast_types_produce_separate_records(self, monkeypatch):
        ddb = boto3.resource("dynamodb", region_name="ca-west-1")
        _create_reminder_log_table(ddb)
        from lambda_function import reminder_function
        monkeypatch.setattr(reminder_function, "get_local_today", lambda: FIXED_TODAY)

        reminder_function.log_reminder_sent("ramadan")
        reminder_function.log_reminder_sent("arafah")

        assert _get_log_item(ddb, "ramadan") is not None
        assert _get_log_item(ddb, "arafah") is not None
