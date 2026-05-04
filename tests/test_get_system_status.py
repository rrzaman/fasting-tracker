"""Tests for lambda_function/get_system_status.py.

Shared fixtures (aws_env, fasting_table, health_table, reminder_log_table,
recipients_table) live in tests/conftest.py.
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


class TestGetRecipients:
    """get_recipients — returns recipient names and languages from DynamoDB."""

    def test_returns_names_and_langs(self, recipients_table):
        recipients_table.put_item(Item={"phone": "+15550001111", "name": "Rayyan", "lang": "en"})
        recipients_table.put_item(Item={"phone": "+15550002222", "name": "Fatima", "lang": "bn"})
        from lambda_function.get_system_status import get_recipients

        result = get_recipients()

        assert len(result) == 2
        assert {"name": "Rayyan", "lang": "en"} in result
        assert {"name": "Fatima", "lang": "bn"} in result

    def test_empty_table_returns_empty_list(self, recipients_table):
        from lambda_function.get_system_status import get_recipients

        result = get_recipients()

        assert result == []


class TestGetLatestDate:
    """get_latest_date — scans a DynamoDB table and returns the most recent date string."""

    def test_returns_most_recent_date(self, fasting_table):
        fasting_table.put_item(Item={"date": "2026-04-01", "is_fasting": True})
        fasting_table.put_item(Item={"date": "2026-04-10", "is_fasting": True})
        fasting_table.put_item(Item={"date": "2026-04-05", "is_fasting": True})
        from lambda_function.get_system_status import get_latest_date

        result = get_latest_date("fasting-records")

        assert result == "2026-04-10"

    def test_empty_table_returns_none(self, fasting_table):
        from lambda_function.get_system_status import get_latest_date

        result = get_latest_date("fasting-records")

        assert result is None


class TestGetLastReminderRun:
    """get_last_reminder_run — reads CloudWatch logs to determine last Lambda execution."""

    @patch("lambda_function.get_system_status.boto3.client")
    def test_no_logs_found_returns_status(self, mock_client):
        logs = MagicMock()
        logs.describe_log_streams.return_value = {"logStreams": []}
        mock_client.return_value = logs
        from lambda_function.get_system_status import get_last_reminder_run

        result = get_last_reminder_run()

        assert result["status"] == "No logs found"
        assert result["timestamp"] is None

    @patch("lambda_function.get_system_status.boto3.client")
    def test_no_events_found_returns_status(self, mock_client):
        logs = MagicMock()
        logs.describe_log_streams.return_value = {
            "logStreams": [{"logStreamName": "stream-1"}]
        }
        logs.get_log_events.return_value = {"events": []}
        mock_client.return_value = logs
        from lambda_function.get_system_status import get_last_reminder_run

        result = get_last_reminder_run()

        assert result["status"] == "No events found"
        assert result["timestamp"] is None

    @patch("lambda_function.get_system_status.boto3.client")
    def test_completed_successfully(self, mock_client):
        logs = MagicMock()
        logs.describe_log_streams.return_value = {
            "logStreams": [
                {"logStreamName": "stream-1", "lastEventTimestamp": 1714550400000}
            ]
        }
        logs.get_log_events.return_value = {
            "events": [
                {"message": "Lambda handler complete"}
            ]
        }
        mock_client.return_value = logs
        from lambda_function.get_system_status import get_last_reminder_run

        result = get_last_reminder_run()

        assert result["status"] == "Completed successfully"
        assert result["timestamp"] is not None

    @patch("lambda_function.get_system_status.boto3.client")
    def test_error_detected(self, mock_client):
        logs = MagicMock()
        logs.describe_log_streams.return_value = {
            "logStreams": [
                {"logStreamName": "stream-1", "lastEventTimestamp": 1714550400000}
            ]
        }
        logs.get_log_events.return_value = {
            "events": [
                {"message": "ERROR: something went wrong"},
                {"message": "Lambda handler complete"},
            ]
        }
        mock_client.return_value = logs
        from lambda_function.get_system_status import get_last_reminder_run

        result = get_last_reminder_run()

        assert result["status"] == "Error detected"
        assert result["has_error"] is True

    @patch("lambda_function.get_system_status.boto3.client")
    def test_logs_client_exception(self, mock_client):
        logs = MagicMock()
        logs.describe_log_streams.side_effect = Exception("Connection error")
        mock_client.return_value = logs
        from lambda_function.get_system_status import get_last_reminder_run

        result = get_last_reminder_run()

        assert "Could not read logs" in result["status"]
        assert result["timestamp"] is None


class TestGetLastSmsSent:
    """get_last_sms_sent — returns the most recent date an SMS reminder was sent."""

    def test_returns_latest_date(self, reminder_log_table):
        reminder_log_table.put_item(Item={"date": "2026-04-01", "fast_type": "ramadan",
                                          "sent_at": "2026-04-01T08:00:00+00:00"})
        reminder_log_table.put_item(Item={"date": "2026-04-10", "fast_type": "arafah",
                                          "sent_at": "2026-04-10T08:00:00+00:00"})
        from lambda_function.get_system_status import get_last_sms_sent

        result = get_last_sms_sent()

        assert result == "2026-04-10"

    def test_empty_table_returns_none(self, reminder_log_table):
        from lambda_function.get_system_status import get_last_sms_sent

        result = get_last_sms_sent()

        assert result is None


class TestGetCalendarHorizon:
    """get_calendar_horizon — returns days ahead the fasting calendar extends."""

    def test_returns_positive_days_ahead(self, fasting_table):
        # Set a future date so horizon is positive
        future_date = "2027-01-01"
        fasting_table.put_item(
            Item={"date": future_date, "is_fasting": True}
        )
        from lambda_function import get_system_status

        with patch.object(get_system_status, "datetime") as mock_dt:
            mock_now = datetime(2026, 5, 1, tzinfo=timezone.utc)
            mock_dt.now.return_value = mock_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = get_system_status.get_calendar_horizon()

        assert result is not None
        assert result > 0

    def test_empty_table_returns_none(self, fasting_table):
        from lambda_function.get_system_status import get_calendar_horizon

        result = get_calendar_horizon()

        assert result is None


class TestGetHealthDataAge:
    """get_health_data_age — returns days since health data was last updated."""

    def test_returns_non_negative_age(self, health_table):
        health_table.put_item(
            Item={"date": "2026-04-20", "metric": "steps", "value": 10000}
        )
        from lambda_function import get_system_status

        with patch.object(get_system_status, "datetime") as mock_dt:
            mock_now = datetime(2026, 5, 1, tzinfo=timezone.utc)
            mock_dt.now.return_value = mock_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = get_system_status.get_health_data_age()

        assert result is not None
        assert result >= 0

    def test_empty_table_returns_none(self, health_table):
        from lambda_function.get_system_status import get_health_data_age

        result = get_health_data_age()

        assert result is None


class TestHandler:
    """handler — returns system status for dashboard display."""

    @patch("lambda_function.get_system_status.boto3.client")
    def test_returns_200_with_expected_keys(self, mock_client,
                                            fasting_table, health_table,
                                            reminder_log_table, recipients_table):
        fasting_table.put_item(
            Item={"date": "2026-05-01", "is_fasting": True}
        )
        health_table.put_item(
            Item={"date": "2026-05-01", "metric": "steps", "value": 10000}
        )
        recipients_table.put_item(
            Item={"phone": "+15550001111", "name": "Rayyan", "lang": "en"}
        )

        logs = MagicMock()
        logs.describe_log_streams.return_value = {"logStreams": []}
        mock_client.return_value = logs

        from lambda_function.get_system_status import handler

        result = handler({}, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "last_reminder_run" in body
        assert "last_sms_sent" in body
        assert "calendar_horizon" in body
        assert "health_data_age" in body
        assert "recipients" in body

    @patch("lambda_function.get_system_status.boto3.client")
    def test_cors_header_present(self, mock_client,
                                 fasting_table, health_table,
                                 reminder_log_table, recipients_table):
        logs = MagicMock()
        logs.describe_log_streams.return_value = {"logStreams": []}
        mock_client.return_value = logs

        from lambda_function.get_system_status import handler

        result = handler({}, None)

        assert result["headers"]["Access-Control-Allow-Origin"] == "*"


# ===========================================================================
# Coverage gaps for pagination and exception branches — originally lived in
# test_lambda_gaps.py.
# ===========================================================================

class TestPaginationAndExceptions:
    """Pagination and exception branches in get_system_status."""

    def test_get_latest_date_pagination(self, fasting_table):
        for i in range(5):
            fasting_table.put_item(
                Item={"date": f"2026-04-{i+1:02d}", "is_fasting": True}
            )

        from lambda_function.get_system_status import get_latest_date
        result = get_latest_date("fasting-records")
        assert result == "2026-04-05"

    def test_get_last_sms_sent_exception_returns_none(self, reminder_log_table):
        """When reminder-log scan fails, get_last_sms_sent returns None."""
        from lambda_function.get_system_status import get_last_sms_sent
        with patch("lambda_function.get_system_status.boto3.resource") as mock_res:
            mock_table = MagicMock()
            mock_table.scan.side_effect = Exception("Scan failed")
            mock_res.return_value.Table.return_value = mock_table
            result = get_last_sms_sent()
            assert result is None

    def test_get_recipients_exception_returns_empty_list(self, recipients_table):
        """When recipients scan fails, get_recipients returns empty list."""
        from lambda_function.get_system_status import get_recipients
        result = get_recipients()
        assert result == []
