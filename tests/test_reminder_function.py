"""Tests for lambda_function/reminder_function.py.

Covers every public helper plus the Lambda handler entry point.
Shared fixtures (aws_env, fasting_table, recipients_table, reminder_log_table,
frozen_today_reminder, FIXED_TODAY) live in tests/conftest.py.
"""

from calendar import timegm
from datetime import date, datetime as dt, timedelta
from unittest.mock import MagicMock, patch

import pytest

from lambda_function.reminder_function import build_message, format_date

from tests.conftest import FIXED_TODAY


# ---------------------------------------------------------------------------
# Local helper — fetch a single record from the reminder-log table.
# ---------------------------------------------------------------------------

def _get_log_item(table, fast_type: str):
    return table.get_item(
        Key={"date": str(FIXED_TODAY), "fast_type": fast_type}
    ).get("Item")


# ===========================================================================
# format_date — turns "YYYY-MM-DD" into "Month Nth" with correct ordinal.
# ===========================================================================

class TestFormatDateSuffixes:
    """Tests for correct ordinal suffixes on day numbers."""

    def test_1st_suffix(self):
        assert format_date("2026-04-01") == "April 1st"

    def test_2nd_suffix(self):
        assert format_date("2026-04-02") == "April 2nd"

    def test_3rd_suffix(self):
        assert format_date("2026-04-03") == "April 3rd"

    def test_4th_uses_th(self):
        assert format_date("2026-04-04") == "April 4th"

    def test_11th_uses_th_not_st(self):
        """11th is a common edge case — should be 'th' not 'st'."""
        assert format_date("2026-04-11") == "April 11th"

    def test_12th_uses_th_not_nd(self):
        """12th is a common edge case — should be 'th' not 'nd'."""
        assert format_date("2026-04-12") == "April 12th"

    def test_13th_uses_th_not_rd(self):
        """13th is a common edge case — should be 'th' not 'rd'."""
        assert format_date("2026-04-13") == "April 13th"

    def test_21st_suffix(self):
        """21st should resume 'st' pattern after teens."""
        assert format_date("2026-04-21") == "April 21st"

    def test_22nd_suffix(self):
        assert format_date("2026-04-22") == "April 22nd"

    def test_23rd_suffix(self):
        assert format_date("2026-04-23") == "April 23rd"

    def test_31st_suffix(self):
        assert format_date("2026-03-31") == "March 31st"


class TestFormatDateMonths:
    """Tests for correct month names across the year."""

    def test_january(self):
        assert format_date("2026-01-15") == "January 15th"

    def test_june(self):
        assert format_date("2026-06-01") == "June 1st"

    def test_december(self):
        assert format_date("2026-12-25") == "December 25th"


class TestFormatDateEdgeCases:
    """Tests for edge case inputs."""

    def test_empty_string_returns_unknown(self):
        """Empty string should return fallback rather than crashing."""
        assert format_date("") == "unknown date"


# ===========================================================================
# build_message — chooses which SMS body to send for a given fast item.
# Returns None when no notification should be sent on this date.
# ===========================================================================

class TestBuildMessageAyyamAlBid:
    """Tests for Ayyam al-Bid notification logic."""

    def test_sends_message_on_day_13(self):
        """Should send notification when detected day is 13th of the month."""

        item = {
            "fast_type": "ayyam_al_bid",
            "date": "2026-04-30",
            "hijri_month": 10,
            "hijri_day": 13
        }

        result = build_message(item)
        assert result is not None
        assert "Ayyam al-Bid" in result
        assert "Shawwal" in result

    def test_no_message_on_day_14(self):
        """Should return None for days 14 since reminder was sent on 13th."""

        item = {
            "fast_type": "ayyam_al_bid",
            "date": "2026-05-01",
            "hijri_month": 10,
            "hijri_day": 14
        }

        result = build_message(item)
        assert result is None

    def test_no_message_on_day_15(self):
        """Should return None for days 15 since reminder was sent on 13th."""

        item = {
            "fast_type": "ayyam_al_bid",
            "date": "2026-05-02",
            "hijri_month": 10,
            "hijri_day": 15
        }

        result = build_message(item)
        assert result is None

    def test_no_message_dhul_hijjah_day_13(self):
        """Dhul Hijjah day 13 sends no message, due to being Ayyam al-Tashreeq.."""

        item = {
            "fast_type": "prohibited",
            "date": "2026-05-30",
            "hijri_month": 12,
            "hijri_day": 13
        }

        result = build_message(item)
        assert result is None

    def test_dhul_hijjah_day_14_sends_adjusted_message(self):
        """Dhul Hijjah day 14 sends adjusted message since 13th is prohibited."""

        item = {
            "fast_type": "ayyam_al_bid",
            "date": "2026-05-31",
            "hijri_month": 12,
            "hijri_day": 14
        }

        result = build_message(item)
        assert result is not None
        assert "14th, 15th and 16th" in result
        assert "Dhul Hijjah" in result

    def test_no_message_dhul_hijjah_day_15(self):
        """Dhul Hijjah day 15 sends no message."""

        item = {
            "fast_type": "ayyam_al_bid",
            "date": "2026-05-31",
            "hijri_month": 12,
            "hijri_day": 15
        }

        result = build_message(item)
        assert result is None

    def test_no_message_dhul_hijjah_day_16(self):
        """Dhul Hijjah day 16 sends no message."""

        item = {
            "fast_type": "ayyam_al_bid",
            "date": "2026-05-31",
            "hijri_month": 12,
            "hijri_day": 16
        }

        result = build_message(item)
        assert result is None


class TestBuildMessageRamadan:
    """Tests for Ramadan notification logic."""

    def test_sends_message_on_day_1(self):
        """Should send notification the day before Ramadan (Shaban 29/30)."""

        item = {
            "fast_type": "ramadan",
            "date": "2026-02-18",
            "hijri_month": 9,
            "hijri_day": 1
        }

        result = build_message(item)
        assert result is not None
        assert "Ramadan Mubarak" in result

    def test_no_message_on_day_2(self):
        """Should not send notification message any other day of Ramadan, excluding immediately before Eid."""

        item = {
            "fast_type": "ramadan",
            "date": "2026-02-19",
            "hijri_month": 9,
            "hijri_day": 2
        }

        result = build_message(item)
        assert result is None


class TestBuildMessageDhulHijjahEarly:
    """Tests for Dhul Hijjah early (days 1-8) notifications."""

    def test_message_on_day_1(self):
        """Should send notification before first day."""

        item = {
            "fast_type": "dhul_hijjah_early",
            "date": "2026-05-17",
            "hijri_month": 12,
            "hijri_day": 1
        }

        result = build_message(item)
        assert result is not None
        assert "Dhul Hijjah" in result
        assert "9 days" in result

    def test_no_message_on_day_2(self):
        """Should not send a notification on second day."""

        item = {
            "fast_type": "dhul_hijjah_early",
            "date": "2026-05-18",
            "hijri_month": 12,
            "hijri_day": 2
        }

        result = build_message(item)
        assert result is None


class TestBuildMessageArafah:
    """Tests for Arafah fasting notification."""

    def test_message_arafah(self):
        """Should send one message notifying for Arafah fasting."""

        item = {
            "fast_type": "arafah",
            "date": "2026-05-26",
            "hijri_month": 12,
            "hijri_day": 9
        }

        result = build_message(item)
        assert result is not None
        assert "Arafah" in result


class TestBuildMessageAshura:
    """Tests for Ashura fasting notification."""

    def test_message_ashura(self):
        """Should send one notification before ninth of Muharram."""

        item = {
            "fast_type": "ashura",
            "date": "2026-06-25",
            "hijri_month": 1,
            "hijri_day": 10
        }

        result = build_message(item)
        assert result is not None
        assert "Ashura" in result


class TestBuildMessageWeeklySunnah:
    """Tests for weekly Sunnah fasting on Mondays and Thursdays."""

    def test_message_monday_thursday(self):
        """Should send notification on Monday or Thursday."""

        item = {
            "fast_type": "weekly_sunnah",
            "date": "2026-04-23",
            "hijri_month": 6,
            "hijri_day": 11
        }

        result = build_message(item)
        assert result is not None
        assert "Sunnah" in result


class TestBuildMessageProhibited:
    """Tests for prohibited fasting days (both Eid + Ayyam al-Tashreeq)"""

    def test_eid_al_fitr_message(self):
        """Should send Eid Mubarak message for Eid al-Fitr."""

        item = {
            "fast_type": "prohibited",
            "date": "2026-03-20",
            "hijri_month": 10,
            "hijri_day": 1,
            "celebration_type": "eid_al_fitr"
        }

        result = build_message(item)
        assert result is not None
        assert "Eid al-Fitr" in result

    def test_eid_al_adha_message(self):
        """Should send Eid Mubarak message for Eid al-Adha and Ayyam al-Tashreeq."""

        item = {
            "fast_type": "prohibited",
            "date": "2026-05-27",
            "hijri_month": 12,
            "hijri_day": 10,
            "celebration_type": "eid_al_adha"
        }

        result = build_message(item)
        assert result is not None
        assert "Eid al-Adha" in result


class TestBuildMessageUnknownFastType:
    """Tests edge case handling for unrecognised fast types."""

    def test_unknown_type_returns_none(self):
        """Should return None gracefully for any unrecognised fast type."""
        item = {
            "fast_type": "something_unexpected",
            "date": "2026-04-23",
            "hijri_month": 6,
            "hijri_day": 11
        }
        result = build_message(item)
        assert result is None

    def test_missing_fast_type_returns_none(self):
        """Should return None when fast_type key is absent."""
        item = {
            "date": "2026-04-23",
            "hijri_month": 6,
            "hijri_day": 11
        }
        result = build_message(item)
        assert result is None


# ===========================================================================
# get_recipients — scans notification-recipients and returns all items.
# ===========================================================================

class TestGetRecipients:
    """get_recipients — scans notification-recipients and returns all items."""

    def test_returns_all_recipients(self, recipients_table):
        recipients_table.put_item(Item={"phone": "+15550001111", "name": "Rayyan", "lang": "en"})
        recipients_table.put_item(Item={"phone": "+15550002222", "name": "Fatima", "lang": "bn"})
        from lambda_function.reminder_function import get_recipients

        result = get_recipients()

        assert {r["phone"] for r in result} == {"+15550001111", "+15550002222"}

    def test_empty_table_returns_empty_list(self, recipients_table):
        from lambda_function.reminder_function import get_recipients

        result = get_recipients()

        assert result == []

    def test_returns_correct_fields(self, recipients_table):
        recipients_table.put_item(
            Item={"phone": "+15550001111", "name": "Rayyan", "lang": "en"}
        )
        from lambda_function.reminder_function import get_recipients

        result = get_recipients()

        assert len(result) == 1
        r = result[0]
        assert r["phone"] == "+15550001111"
        assert r["name"] == "Rayyan"
        assert r["lang"] == "en"

    def test_multiple_recipients_all_present(self, recipients_table):
        recipients = [
            {"phone": f"+1555000{i:04d}", "name": f"User{i}", "lang": "en"}
            for i in range(5)
        ]
        for r in recipients:
            recipients_table.put_item(Item=r)
        from lambda_function.reminder_function import get_recipients

        result = get_recipients()

        assert len(result) == 5


class TestGetRecipientsException:
    """get_recipients exception handling."""

    @patch("lambda_function.reminder_function.boto3.resource")
    def test_returns_empty_list_on_exception(self, mock_resource):
        mock_table = MagicMock()
        mock_table.scan.side_effect = Exception("DynamoDB error")
        mock_resource.return_value.Table.return_value = mock_table

        from lambda_function.reminder_function import get_recipients
        result = get_recipients()

        assert result == []


# ===========================================================================
# already_sent_today — reads reminder-log to guard against duplicate sends.
# ===========================================================================

class TestAlreadySentToday:
    """already_sent_today — reads reminder-log to guard against duplicate sends."""

    def test_returns_false_when_log_is_empty(self, reminder_log_table, frozen_today_reminder):
        from lambda_function import reminder_function

        result = reminder_function.already_sent_today("ramadan")

        assert result is False

    def test_returns_false_for_different_fast_type(self, reminder_log_table, frozen_today_reminder):
        reminder_log_table.put_item(
            Item={"date": str(FIXED_TODAY), "fast_type": "arafah", "sent_at": "2026-05-01T08:00:00"}
        )
        from lambda_function import reminder_function

        result = reminder_function.already_sent_today("ramadan")

        assert result is False

    def test_returns_false_when_log_exists_for_different_date(self, reminder_log_table, frozen_today_reminder):
        yesterday = FIXED_TODAY - timedelta(days=1)
        reminder_log_table.put_item(
            Item={"date": str(yesterday), "fast_type": "ramadan", "sent_at": "2026-04-30T08:00:00"}
        )
        from lambda_function import reminder_function

        result = reminder_function.already_sent_today("ramadan")

        assert result is False

    def test_returns_true_after_log_reminder_sent(self, reminder_log_table, frozen_today_reminder):
        from lambda_function import reminder_function

        reminder_function.log_reminder_sent("ramadan")
        result = reminder_function.already_sent_today("ramadan")

        assert result is True

    def test_returns_false_for_fast_type_not_yet_logged(self, reminder_log_table, frozen_today_reminder):
        """Logging one fast type must not affect the guard for a different type."""
        from lambda_function import reminder_function

        reminder_function.log_reminder_sent("ramadan")
        result = reminder_function.already_sent_today("arafah")

        assert result is False


class TestAlreadySentTodayException:
    """already_sent_today exception handling."""

    def test_returns_false_on_exception(self, frozen_today_reminder):
        from lambda_function import reminder_function

        with patch("lambda_function.reminder_function.boto3.resource") as mock_res:
            mock_table = MagicMock()
            mock_table.get_item.side_effect = Exception("DynamoDB error")
            mock_res.return_value.Table.return_value = mock_table

            assert reminder_function.already_sent_today("ramadan") is False


# ===========================================================================
# log_reminder_sent — persists an idempotency record with a 30-day TTL.
# ===========================================================================

class TestLogReminderSent:
    """log_reminder_sent — persists an idempotency record with a 30-day TTL."""

    def test_writes_record_to_table(self, reminder_log_table, frozen_today_reminder):
        from lambda_function import reminder_function

        reminder_function.log_reminder_sent("arafah")

        assert _get_log_item(reminder_log_table, "arafah") is not None

    def test_writes_correct_date_and_fast_type(self, reminder_log_table, frozen_today_reminder):
        from lambda_function import reminder_function

        reminder_function.log_reminder_sent("arafah")

        item = _get_log_item(reminder_log_table, "arafah")
        assert item["date"] == "2026-05-01"
        assert item["fast_type"] == "arafah"

    def test_writes_sent_at_as_tz_aware_iso8601(self, reminder_log_table, frozen_today_reminder):
        from lambda_function import reminder_function

        reminder_function.log_reminder_sent("arafah")

        sent_at = _get_log_item(reminder_log_table, "arafah")["sent_at"]
        parsed = dt.fromisoformat(sent_at)
        assert parsed.tzinfo is not None

    def test_writes_expires_at_as_integer(self, reminder_log_table, frozen_today_reminder):
        from lambda_function import reminder_function

        reminder_function.log_reminder_sent("arafah")

        # DynamoDB returns numbers as Decimal; int() handles both int and Decimal.
        expires_at = int(_get_log_item(reminder_log_table, "arafah")["expires_at"])
        assert isinstance(expires_at, int)
        assert expires_at > 0

    def test_expires_at_is_approximately_30_days_ahead(self, reminder_log_table, frozen_today_reminder):
        from lambda_function import reminder_function

        reminder_function.log_reminder_sent("arafah")

        expires_at = int(_get_log_item(reminder_log_table, "arafah")["expires_at"])
        # timegm converts the date's timetuple as UTC midnight; allow ±2 days for
        # any timezone offset between the test host and the strftime("%s") result.
        expected_ts = timegm((FIXED_TODAY + timedelta(days=30)).timetuple())
        assert abs(expires_at - expected_ts) < 86400 * 2

    def test_separate_fast_types_produce_separate_records(self, reminder_log_table, frozen_today_reminder):
        from lambda_function import reminder_function

        reminder_function.log_reminder_sent("ramadan")
        reminder_function.log_reminder_sent("arafah")

        assert _get_log_item(reminder_log_table, "ramadan") is not None
        assert _get_log_item(reminder_log_table, "arafah") is not None


class TestLogReminderSentException:
    """log_reminder_sent exception handling."""

    def test_returns_none_on_exception(self, frozen_today_reminder):
        from lambda_function import reminder_function

        with patch("lambda_function.reminder_function.boto3.resource") as mock_res:
            mock_table = MagicMock()
            mock_table.put_item.side_effect = Exception("DynamoDB error")
            mock_res.return_value.Table.return_value = mock_table

            # Should not raise even though logging fails
            reminder_function.log_reminder_sent("ramadan")


# ===========================================================================
# get_upcoming_fasts — queries DynamoDB for fasting days in the next N days.
# ===========================================================================

class TestGetUpcomingFasts:
    """get_upcoming_fasts — queries DynamoDB for fasting days in the next N days."""

    def test_returns_upcoming_fasting_days(self, fasting_table, frozen_today_reminder):
        # FIXED_TODAY = 2026-05-01, so tomorrow (2026-05-02) is an upcoming fast
        fasting_table.put_item(Item={"date": "2026-05-02", "is_fasting": True, "fast_type": "weekly_sunnah"})
        fasting_table.put_item(Item={"date": "2026-05-03", "is_fasting": False, "fast_type": None})
        from lambda_function import reminder_function

        result = reminder_function.get_upcoming_fasts(1)

        assert len(result) == 1
        assert result[0]["date"] == "2026-05-02"
        assert result[0]["fast_type"] == "weekly_sunnah"

    def test_skips_non_fasting_days(self, fasting_table, frozen_today_reminder):
        fasting_table.put_item(Item={"date": "2026-05-02", "is_fasting": False, "fast_type": None})
        from lambda_function import reminder_function

        result = reminder_function.get_upcoming_fasts(1)

        assert result == []

    def test_checks_multiple_days_ahead(self, fasting_table, frozen_today_reminder):
        fasting_table.put_item(Item={"date": "2026-05-02", "is_fasting": True, "fast_type": "weekly_sunnah"})
        fasting_table.put_item(Item={"date": "2026-05-03", "is_fasting": True, "fast_type": "weekly_sunnah"})
        from lambda_function import reminder_function

        result = reminder_function.get_upcoming_fasts(2)

        assert len(result) == 2

    def test_skips_today(self, fasting_table, frozen_today_reminder):
        fasting_table.put_item(Item={"date": "2026-05-01", "is_fasting": True, "fast_type": "ramadan"})
        from lambda_function import reminder_function

        result = reminder_function.get_upcoming_fasts(1)

        assert result == []

    def test_includes_eid_al_adha(self, fasting_table, frozen_today_reminder):
        """Eid al-Adha is prohibited (is_fasting=False) but still needs a reminder."""
        fasting_table.put_item(Item={
            "date": "2026-05-02",
            "is_fasting": False,
            "fast_type": "prohibited",
            "celebration_type": "eid_al_adha",
            "hijri_month": "12",
            "hijri_day": "10",
        })
        from lambda_function import reminder_function

        result = reminder_function.get_upcoming_fasts(1)

        assert len(result) == 1
        assert result[0]["celebration_type"] == "eid_al_adha"

    def test_includes_eid_al_fitr(self, fasting_table, frozen_today_reminder):
        """Eid al-Fitr is prohibited but still needs a reminder."""
        fasting_table.put_item(Item={
            "date": "2026-05-02",
            "is_fasting": False,
            "fast_type": "prohibited",
            "celebration_type": "eid_al_fitr",
            "hijri_month": "10",
            "hijri_day": "1",
        })
        from lambda_function import reminder_function

        result = reminder_function.get_upcoming_fasts(1)

        assert len(result) == 1
        assert result[0]["celebration_type"] == "eid_al_fitr"

    def test_skips_ayyam_al_tashreeq(self, fasting_table, frozen_today_reminder):
        """Prohibited days other than Eid have no message and should be filtered out."""
        fasting_table.put_item(Item={
            "date": "2026-05-02",
            "is_fasting": False,
            "fast_type": "prohibited",
            "celebration_type": "ayyam_al_tashreeq",
            "hijri_month": "12",
            "hijri_day": "11",
        })
        from lambda_function import reminder_function

        result = reminder_function.get_upcoming_fasts(1)

        assert result == []


# ===========================================================================
# send_sms — sends SMS messages to phone numbers via AWS SNS.
# ===========================================================================

class TestSendSms:
    """send_sms — sends SMS messages to phone numbers via AWS SNS."""

    @patch("lambda_function.reminder_function.boto3.client")
    def test_sends_to_each_recipient(self, mock_client):
        sns = MagicMock()
        mock_client.return_value = sns
        from lambda_function.reminder_function import send_sms

        send_sms("Hello", ["+15550001111", "+15550002222"])

        assert sns.publish.call_count == 2
        sns.publish.assert_any_call(
            PhoneNumber="+15550001111",
            Message="Hello",
            MessageAttributes={
                "AWS.SNS.SMS.SMSType": {
                    "DataType": "String",
                    "StringValue": "Transactional",
                }
            },
        )

    @patch("lambda_function.reminder_function.boto3.client")
    def test_skips_empty_numbers(self, mock_client):
        sns = MagicMock()
        mock_client.return_value = sns
        from lambda_function.reminder_function import send_sms

        send_sms("Hello", ["+15550001111", "", None])  # type: ignore[list-item]

        assert sns.publish.call_count == 1
        sns.publish.assert_called_once_with(
            PhoneNumber="+15550001111",
            Message="Hello",
            MessageAttributes={
                "AWS.SNS.SMS.SMSType": {
                    "DataType": "String",
                    "StringValue": "Transactional",
                }
            },
        )


# ===========================================================================
# get_latest_date — scans a DynamoDB table and returns the most recent date.
# ===========================================================================

class TestGetLatestDate:
    """get_latest_date — scans a DynamoDB table and returns the most recent date."""

    def test_returns_most_recent_date(self, fasting_table):
        fasting_table.put_item(Item={"date": "2026-04-01", "is_fasting": True})
        fasting_table.put_item(Item={"date": "2026-04-15", "is_fasting": True})
        fasting_table.put_item(Item={"date": "2026-04-10", "is_fasting": True})
        from lambda_function.reminder_function import get_latest_date

        result = get_latest_date("fasting-records")

        assert result == date(2026, 4, 15)

    def test_empty_table_returns_none(self, fasting_table):
        from lambda_function.reminder_function import get_latest_date

        result = get_latest_date("fasting-records")

        assert result is None


# ===========================================================================
# check_health_data_lag — sends SMS reminder when health data is stale.
# ===========================================================================

class TestCheckHealthDataLag:
    """check_health_data_lag — sends SMS reminder when health data is stale."""

    @patch("lambda_function.reminder_function.send_sms")
    @patch("lambda_function.reminder_function.get_latest_date")
    @patch("lambda_function.reminder_function.get_local_today")
    def test_sends_reminder_when_data_is_stale(self, mock_today, mock_latest, mock_send):
        mock_today.return_value = date(2026, 5, 1)
        mock_latest.return_value = date(2026, 4, 10)  # 21 days old
        from lambda_function.reminder_function import check_health_data_lag

        check_health_data_lag("+15550001111")

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert "21 days old" in call_args[0][0]
        assert call_args[0][1] == ["+15550001111"]

    @patch("lambda_function.reminder_function.send_sms")
    @patch("lambda_function.reminder_function.get_latest_date")
    @patch("lambda_function.reminder_function.get_local_today")
    def test_no_reminder_when_data_is_fresh(self, mock_today, mock_latest, mock_send):
        mock_today.return_value = date(2026, 5, 1)
        mock_latest.return_value = date(2026, 4, 25)  # 6 days old
        from lambda_function.reminder_function import check_health_data_lag

        check_health_data_lag("+15550001111")

        mock_send.assert_not_called()

    @patch("lambda_function.reminder_function.send_sms")
    @patch("lambda_function.reminder_function.get_latest_date")
    def test_no_reminder_when_no_health_data(self, mock_latest, mock_send):
        mock_latest.return_value = None
        from lambda_function.reminder_function import check_health_data_lag

        check_health_data_lag("+15550001111")

        mock_send.assert_not_called()


# ===========================================================================
# check_calendar_horizon — extends fasting calendar if horizon < 60 days.
# ===========================================================================

class TestCheckCalendarHorizon:
    """check_calendar_horizon — extends fasting calendar if horizon is less than 60 days."""

    @patch("lambda_function.reminder_function.get_latest_date")
    @patch("lambda_function.reminder_function.get_local_today")
    @patch("lambda_function.reminder_function.FASTING_TABLE", "fasting-records")
    def test_extends_calendar_when_horizon_low(self, mock_today, mock_latest):
        mock_today.return_value = date(2026, 5, 1)
        mock_latest.return_value = date(2026, 6, 1)  # 31 days ahead, < 60

        with patch.dict("sys.modules", {
            "ingestion.fetch_hijri_calendar": MagicMock(),
            "ingestion.upload_to_aws": MagicMock(),
        }):
            mock_build = MagicMock(return_value="mock_df")
            mock_upload = MagicMock()

            import sys
            sys.modules["ingestion.fetch_hijri_calendar"] = MagicMock()
            sys.modules["ingestion.fetch_hijri_calendar"].build_fasting_calendar = mock_build
            sys.modules["ingestion.upload_to_aws"] = MagicMock()
            sys.modules["ingestion.upload_to_aws"].upload_df_to_dynamodb = mock_upload

            from lambda_function.reminder_function import check_calendar_horizon
            check_calendar_horizon()

            mock_build.assert_called_once()
            mock_upload.assert_called_once_with("mock_df", "fasting-records")

    @patch("lambda_function.reminder_function.get_latest_date")
    @patch("lambda_function.reminder_function.get_local_today")
    def test_does_not_extend_when_horizon_adequate(self, mock_today, mock_latest):
        mock_today.return_value = date(2026, 5, 1)
        mock_latest.return_value = date(2026, 8, 1)  # 92 days ahead, > 60

        with patch("ingestion.fetch_hijri_calendar.build_fasting_calendar") as mock_build:
            with patch("ingestion.upload_to_aws.upload_df_to_dynamodb") as mock_upload:
                from lambda_function.reminder_function import check_calendar_horizon
                check_calendar_horizon()

                mock_build.assert_not_called()
                mock_upload.assert_not_called()

    @patch("lambda_function.reminder_function.get_latest_date")
    def test_does_not_extend_when_no_fasting_data(self, mock_latest):
        mock_latest.return_value = None

        with patch("ingestion.fetch_hijri_calendar.build_fasting_calendar") as mock_build:
            with patch("ingestion.upload_to_aws.upload_df_to_dynamodb") as mock_upload:
                from lambda_function.reminder_function import check_calendar_horizon
                check_calendar_horizon()

                mock_build.assert_not_called()
                mock_upload.assert_not_called()


# ===========================================================================
# handler — Lambda entry point for EventBridge daily trigger.
# ===========================================================================

class TestHandler:
    """handler — Lambda entry point for EventBridge daily trigger."""

    @patch("lambda_function.reminder_function.send_sms")
    def test_test_message_event_sends_sms(self, mock_send,
                                          recipients_table, reminder_log_table,
                                          frozen_today_reminder):
        """Handler sends test messages when event has test_message key."""
        recipients_table.put_item(Item={"phone": "+15550001111", "name": "Rayyan", "lang": "en"})

        from lambda_function import reminder_function

        event = {
            "test_message": {
                "date": "2026-05-02",
                "fast_type": "ramadan",
                "hijri_month": "9",
                "hijri_day": "1",
            }
        }

        reminder_function.handler(event, None)

        assert mock_send.call_count == 1
        assert "[TEST]" in mock_send.call_args[0][0]
        assert "Ramadan Mubarak" in mock_send.call_args[0][0]

    @patch("lambda_function.reminder_function.send_sms")
    def test_test_message_skips_recipients_without_phone(self, mock_send,
                                                         reminder_log_table,
                                                         frozen_today_reminder):
        from lambda_function import reminder_function
        # Mock get_recipients to return empty phone
        with patch.object(reminder_function, "get_recipients",
                          return_value=[{"phone": "", "name": "Rayyan", "lang": "en"}]):
            event = {"test_message": {"date": "2026-05-02", "fast_type": "ramadan",
                                      "hijri_month": "9", "hijri_day": "1"}}

            reminder_function.handler(event, None)

            assert mock_send.call_count == 0

    @patch("lambda_function.reminder_function.already_sent_today")
    @patch("lambda_function.reminder_function.send_sms")
    @patch("lambda_function.reminder_function.check_health_data_lag")
    @patch("lambda_function.reminder_function.check_calendar_horizon")
    def test_does_not_log_if_no_messages_sent(self, mock_horizon, mock_health,
                                              mock_send, mock_already,
                                              fasting_table, reminder_log_table,
                                              frozen_today_reminder):
        fasting_table.put_item(
            Item={"date": "2026-05-02", "is_fasting": True, "fast_type": "weekly_sunnah",
                  "hijri_month": "10", "hijri_day": "13"}
        )

        from lambda_function import reminder_function
        mock_already.return_value = False

        # No recipients with valid phone numbers
        with patch.object(reminder_function, "get_recipients",
                          return_value=[{"phone": "", "name": "Rayyan", "lang": "en"}]):
            with patch("lambda_function.reminder_function.log_reminder_sent") as mock_log:
                reminder_function.handler({}, None)
                mock_log.assert_not_called()

    @patch("lambda_function.reminder_function.already_sent_today")
    @patch("lambda_function.reminder_function.send_sms")
    @patch("lambda_function.reminder_function.check_health_data_lag")
    @patch("lambda_function.reminder_function.check_calendar_horizon")
    def test_skips_fast_type_already_sent(self, mock_horizon, mock_health,
                                          mock_send, mock_already,
                                          fasting_table, recipients_table,
                                          reminder_log_table,
                                          frozen_today_reminder):
        fasting_table.put_item(
            Item={"date": "2026-05-02", "is_fasting": True, "fast_type": "ramadan",
                  "hijri_month": "9", "hijri_day": "1"}
        )
        recipients_table.put_item(
            Item={"phone": "+15550001111", "name": "Rayyan", "lang": "en"}
        )

        from lambda_function import reminder_function
        mock_already.return_value = True

        reminder_function.handler({}, None)

        mock_send.assert_not_called()

    @patch("lambda_function.reminder_function.already_sent_today")
    @patch("lambda_function.reminder_function.send_sms")
    @patch("lambda_function.reminder_function.check_health_data_lag")
    @patch("lambda_function.reminder_function.check_calendar_horizon")
    def test_no_upcoming_fasts_still_runs_lag_and_horizon(self, mock_horizon, mock_health,
                                                          mock_send, mock_already,
                                                          fasting_table, recipients_table,
                                                          frozen_today_reminder):
        from lambda_function import reminder_function
        mock_already.return_value = False

        reminder_function.handler({}, None)

        mock_send.assert_not_called()
        mock_horizon.assert_called_once()

    @patch("lambda_function.reminder_function.already_sent_today")
    @patch("lambda_function.reminder_function.send_sms")
    @patch("lambda_function.reminder_function.check_health_data_lag")
    @patch("lambda_function.reminder_function.check_calendar_horizon")
    def test_handler_logs_reminder_sent(self, mock_horizon, mock_health,
                                        mock_send, mock_already,
                                        fasting_table, recipients_table,
                                        reminder_log_table,
                                        frozen_today_reminder):
        fasting_table.put_item(
            Item={"date": "2026-05-02", "is_fasting": True, "fast_type": "weekly_sunnah",
                  "hijri_month": "10", "hijri_day": "13"}
        )
        recipients_table.put_item(
            Item={"phone": "+15550001111", "name": "Rayyan", "lang": "en"}
        )

        from lambda_function import reminder_function
        mock_already.return_value = False

        with patch("lambda_function.reminder_function.log_reminder_sent") as mock_log:
            reminder_function.handler({}, None)
            mock_log.assert_called_once_with("weekly_sunnah")

    @patch("lambda_function.reminder_function.already_sent_today")
    @patch("lambda_function.reminder_function.send_sms")
    @patch("lambda_function.reminder_function.check_health_data_lag")
    @patch("lambda_function.reminder_function.check_calendar_horizon")
    def test_handler_sends_eid_al_adha_reminder(self, mock_horizon, mock_health,
                                                mock_send, mock_already,
                                                fasting_table, recipients_table,
                                                reminder_log_table,
                                                frozen_today_reminder):
        """End-to-end: an Eid al-Adha record in the calendar triggers an SMS and a log entry."""
        fasting_table.put_item(
            Item={"date": "2026-05-02", "is_fasting": False, "fast_type": "prohibited",
                  "celebration_type": "eid_al_adha",
                  "hijri_month": "12", "hijri_day": "10"}
        )
        recipients_table.put_item(
            Item={"phone": "+15550001111", "name": "Rayyan", "lang": "en"}
        )

        from lambda_function import reminder_function
        mock_already.return_value = False

        with patch("lambda_function.reminder_function.log_reminder_sent") as mock_log:
            reminder_function.handler({}, None)

            assert mock_send.call_count == 1
            assert "Eid al-Adha" in mock_send.call_args[0][0]
            mock_log.assert_called_once_with("prohibited")
