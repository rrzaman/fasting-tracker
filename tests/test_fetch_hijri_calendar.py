"""Tests for ingestion/fetch_hijri_calendar.py."""

from datetime import date
from random import randint
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from ingestion.fetch_hijri_calendar import (
    API_BASE_URL,
    build_fasting_calendar,
    classify_day,
    fetch_hijri_month,
)


class TestFetchHijriMonth:
    """fetch_hijri_month — calls Aladhan API and returns data list."""

    @patch("ingestion.fetch_hijri_calendar.requests.get")
    def test_returns_data_list(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"day": 1}]}
        mock_get.return_value = mock_response

        result = fetch_hijri_month(4, 2026)

        assert result == [{"day": 1}]
        mock_get.assert_called_once_with(f"{API_BASE_URL}/4/2026")

    @patch("ingestion.fetch_hijri_calendar.requests.get")
    def test_raises_on_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_response

        with pytest.raises(Exception, match="HTTP Error"):
            fetch_hijri_month(4, 2026)


class TestBuildFastingCalendar:
    """build_fasting_calendar — constructs DataFrame from mocked API data."""

    @patch("ingestion.fetch_hijri_calendar.fetch_hijri_month")
    def test_returns_dataframe(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "4", "en": "April"},
                    "day": "1", "weekday": {"en": "Wednesday"},
                },
                "hijri": {
                    "month": {"number": "6", "en": "Jumada al-Thani"},
                    "day": "13",
                },
            },
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "4", "en": "April"},
                    "day": "2", "weekday": {"en": "Thursday"},
                },
                "hijri": {
                    "month": {"number": "6", "en": "Jumada al-Thani"},
                    "day": "14",
                },
            },
        ]

        result = build_fasting_calendar(date(2026, 4, 1), date(2026, 4, 2))

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == [
            "date", "hijri_month", "hijri_day", "fast_type",
            "is_fasting", "celebration_type",
        ]
        assert result.iloc[0]["date"] == "2026-04-01"
        assert result.iloc[1]["date"] == "2026-04-02"

    @patch("ingestion.fetch_hijri_calendar.fetch_hijri_month")
    def test_skips_days_outside_range(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "4", "en": "April"},
                    "day": "1", "weekday": {"en": "Wednesday"},
                },
                "hijri": {
                    "month": {"number": "6", "en": "Jumada al-Thani"},
                    "day": "13",
                },
            },
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "4", "en": "April"},
                    "day": "10", "weekday": {"en": "Friday"},
                },
                "hijri": {
                    "month": {"number": "6", "en": "Jumada al-Thani"},
                    "day": "22",
                },
            },
        ]

        result = build_fasting_calendar(date(2026, 4, 1), date(2026, 4, 1))

        assert len(result) == 1
        assert result.iloc[0]["date"] == "2026-04-01"

    @patch("ingestion.fetch_hijri_calendar.fetch_hijri_month")
    def test_fetches_multiple_months(self, mock_fetch):
        def side_effect(m, y):
            if m == 4 and y == 2026:
                return [{
                    "gregorian": {
                        "year": "2026", "month": {"number": "4", "en": "April"},
                        "day": "30", "weekday": {"en": "Thursday"},
                    },
                    "hijri": {
                        "month": {"number": "7", "en": "Rajab"},
                        "day": "12",
                    },
                }]
            elif m == 5 and y == 2026:
                return [{
                    "gregorian": {
                        "year": "2026", "month": {"number": "5", "en": "May"},
                        "day": "1", "weekday": {"en": "Friday"},
                    },
                    "hijri": {
                        "month": {"number": "7", "en": "Rajab"},
                        "day": "13",
                    },
                }]
            return []

        mock_fetch.side_effect = side_effect

        result = build_fasting_calendar(date(2026, 4, 30), date(2026, 5, 1))

        assert len(result) == 2
        assert set(result["date"].tolist()) == {"2026-04-30", "2026-05-01"}

    @patch("ingestion.fetch_hijri_calendar.fetch_hijri_month")
    def test_result_sorted_by_date(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "4", "en": "April"},
                    "day": "2", "weekday": {"en": "Thursday"},
                },
                "hijri": {
                    "month": {"number": "6", "en": "Jumada al-Thani"},
                    "day": "14",
                },
            },
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "4", "en": "April"},
                    "day": "1", "weekday": {"en": "Wednesday"},
                },
                "hijri": {
                    "month": {"number": "6", "en": "Jumada al-Thani"},
                    "day": "13",
                },
            },
        ]

        result = build_fasting_calendar(date(2026, 4, 1), date(2026, 4, 2))

        dates = result["date"].tolist()
        assert dates == sorted(dates)

    @patch("ingestion.fetch_hijri_calendar.fetch_hijri_month")
    def test_classifies_fasting_days_correctly(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "9", "en": "September"},
                    "day": "1", "weekday": {"en": "Tuesday"},
                },
                "hijri": {
                    "month": {"number": "9", "en": "Ramadan"},
                    "day": "1",
                },
            },
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "9", "en": "September"},
                    "day": "2", "weekday": {"en": "Wednesday"},
                },
                "hijri": {
                    "month": {"number": "9", "en": "Ramadan"},
                    "day": "2",
                },
            },
        ]

        result = build_fasting_calendar(date(2026, 9, 1), date(2026, 9, 2))

        assert len(result) == 2
        assert result.iloc[0]["fast_type"] == "ramadan"
        assert result.iloc[1]["fast_type"] == "ramadan"
        assert result.iloc[1]["is_fasting"] == True

    @patch("ingestion.fetch_hijri_calendar.fetch_hijri_month")
    def test_classifies_prohibited_days(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "3", "en": "March"},
                    "day": "20", "weekday": {"en": "Friday"},
                },
                "hijri": {
                    "month": {"number": "10", "en": "Shawwal"},
                    "day": "1",
                },
            },
        ]

        result = build_fasting_calendar(date(2026, 3, 20), date(2026, 3, 20))

        assert len(result) == 1
        assert result.iloc[0]["fast_type"] == "prohibited"
        assert result.iloc[0]["is_fasting"] == False
        assert result.iloc[0]["celebration_type"] == "eid_al_fitr"

    @patch("ingestion.fetch_hijri_calendar.fetch_hijri_month")
    def test_classifies_weekly_sunnah(self, mock_fetch):
        # Monday that is not a special fast day
        mock_fetch.return_value = [
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "4", "en": "April"},
                    "day": "6", "weekday": {"en": "Monday"},
                },
                "hijri": {
                    "month": {"number": "7", "en": "Rajab"},
                    "day": "18",
                },
            },
        ]

        result = build_fasting_calendar(date(2026, 4, 6), date(2026, 4, 6))

        assert len(result) == 1
        assert result.iloc[0]["fast_type"] == "weekly_sunnah"
        assert result.iloc[0]["is_fasting"] == True

    @patch("ingestion.fetch_hijri_calendar.fetch_hijri_month")
    def test_handles_year_boundary(self, mock_fetch):
        # December 2026 → January 2027
        def side_effect(m, y):
            if m == 12 and y == 2026:
                return [{
                    "gregorian": {
                        "year": "2026", "month": {"number": "12", "en": "December"},
                        "day": "31", "weekday": {"en": "Thursday"},
                    },
                    "hijri": {
                        "month": {"number": "11", "en": "Dhul Qadah"},
                        "day": "20",
                    },
                }]
            elif m == 1 and y == 2027:
                return [{
                    "gregorian": {
                        "year": "2027", "month": {"number": "1", "en": "January"},
                        "day": "1", "weekday": {"en": "Friday"},
                    },
                    "hijri": {
                        "month": {"number": "11", "en": "Dhul Qadah"},
                        "day": "21",
                    },
                }]
            return []

        mock_fetch.side_effect = side_effect

        result = build_fasting_calendar(date(2026, 12, 31), date(2027, 1, 1))

        assert len(result) == 2
        dates = result["date"].tolist()
        assert "2026-12-31" in dates
        assert "2027-01-01" in dates

    @patch("ingestion.fetch_hijri_calendar.fetch_hijri_month")
    def test_single_day_range(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "4", "en": "April"},
                    "day": "15", "weekday": {"en": "Wednesday"},
                },
                "hijri": {
                    "month": {"number": "6", "en": "Jumada al-Thani"},
                    "day": "27",
                },
            },
        ]

        result = build_fasting_calendar(date(2026, 4, 15), date(2026, 4, 15))

        assert len(result) == 1
        assert result.iloc[0]["date"] == "2026-04-15"

    @patch("ingestion.fetch_hijri_calendar.fetch_hijri_month")
    def test_empty_result_when_no_days_match(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "gregorian": {
                    "year": "2026", "month": {"number": "4", "en": "April"},
                    "day": "10", "weekday": {"en": "Friday"},
                },
                "hijri": {
                    "month": {"number": "6", "en": "Jumada al-Thani"},
                    "day": "22",
                },
            },
        ]

        result = build_fasting_calendar(date(2026, 4, 1), date(2026, 4, 5))

        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)


class TestClassifyDayEdgeCases:
    """Additional edge case tests for classify_day."""

    def test_eid_al_fitr(self):
        result = classify_day("2026-03-20", 10, 1, "Friday")
        assert result == (False, "prohibited", "eid_al_fitr")

    def test_eid_al_adha(self):
        result = classify_day("2026-05-27", 12, 10, "Wednesday")
        assert result == (False, "prohibited", "eid_al_adha")

    def test_arafah(self):
        result = classify_day("2026-05-26", 12, 9, "Tuesday")
        assert result == (True, "arafah", None)

    def test_dhul_hijjah_early(self):
        result = classify_day("2026-05-18", 12, 1, "Monday")
        assert result == (True, "dhul_hijjah_early", None)

    def test_ashura_9th(self):
        result = classify_day("2026-06-25", 1, 9, "Wednesday")
        assert result == (True, "ashura", None)

    def test_ashura_10th(self):
        result = classify_day("2026-06-26", 1, 10, "Thursday")
        assert result == (True, "ashura", None)

    def test_ashura_11th_not_included(self):
        result = classify_day("2026-06-27", 1, 11, "Friday")
        assert result == (False, None, None)

    def test_ayyam_al_bid_13th(self):
        result = classify_day("2026-04-13", 6, 13, "Monday")
        assert result == (True, "ayyam_al_bid", None)

    def test_ayyam_al_bid_14th(self):
        result = classify_day("2026-04-14", 6, 14, "Tuesday")
        assert result == (True, "ayyam_al_bid", None)

    def test_ayyam_al_bid_15th(self):
        result = classify_day("2026-04-15", 6, 15, "Wednesday")
        assert result == (True, "ayyam_al_bid", None)

    def test_dhul_hijjah_16th(self):
        result = classify_day("2026-06-01", 12, 16, "Monday")
        assert result == (True, "ayyam_al_bid", None)

    def test_non_dhul_hijjah_16th(self):
        """16th of any other month is not an Ayyam al-Bid day."""

        result = classify_day("2026-04-16", 6, 16, "Tuesday")

        assert result == (False, None, None)

    def test_monday_regular(self):
        result = classify_day("2026-04-06", 7, 18, "Monday")
        assert result == (True, "weekly_sunnah", None)

    def test_thursday_regular(self):
        result = classify_day("2026-04-09", 7, 21, "Thursday")
        assert result == (True, "weekly_sunnah", None)

    def test_tuesday_no_fast(self):
        result = classify_day("2026-04-07", 7, 19, "Tuesday")
        assert result == (False, None, None)

    def test_ayyam_al_tashreeq_11(self):
        result = classify_day("2026-05-28", 12, 11, "Thursday")
        assert result == (False, "prohibited", "ayyam_al_tashreeq")

    def test_ayyam_al_tashreeq_12(self):
        result = classify_day("2026-05-29", 12, 12, "Friday")
        assert result == (False, "prohibited", "ayyam_al_tashreeq")

    def test_ayyam_al_tashreeq_13(self):
        result = classify_day("2026-05-30", 12, 13, "Saturday")
        assert result == (False, "prohibited", "ayyam_al_tashreeq")


# ---------------------------------------------------------------------------
# Behavioural classify_day tests — grouped by scenario rather than by tuple
# shape. Originally lived in test_classify_day.py.
# ---------------------------------------------------------------------------

class TestProhibitedDays:
    """Tests for correctly classifying prohibited fasting days."""

    def test_eid_al_fitr(self):
        """Should send tuple prohibiting fasting for Eid al-Fitr (prohibited)."""

        item = ("2026-03-20", 10, 1, "Wednesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "eid_al_fitr" in result[2]

    def test_eid_al_adha(self):
        """Should send tuple prohibiting fasting for Eid al-Adha (prohibited)."""

        item = ("2026-05-27", 12, 10, "Wednesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "eid_al_adha" in result[2]

    def test_ayyam_al_tashreeq_day_1(self):
        """Should send tuple prohibiting fasting for first day of Ayyam al-Tashreeq."""

        item = ("2026-05-28", 12, 11, "Wednesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "ayyam_al_tashreeq" in result[2]

    def test_ayyam_al_tashreeq_day_2(self):
        """Should send tuple prohibiting fasting for second day of Ayyam al-Tashreeq."""

        item = ("2026-05-29", 12, 12, "Wednesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "ayyam_al_tashreeq" in result[2]

    def test_ayyam_al_tashreeq_day_3(self):
        """Should send tuple prohibiting fasting for third day of Ayyam al-Tashreeq."""

        item = ("2026-05-30", 12, 13, "Wednesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "ayyam_al_tashreeq" in result[2]


class TestClassifyRamadan:
    """Tests for correctly classifying Ramadan fasts."""

    def test_ramadan_day_1(self):
        """Should send tuple indicating fasting for first day of Ramadan."""

        item = ("2026-05-27", 9, 1, "Wednesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ramadan" in result[1]
        assert result[2] is None

    def test_ramadan_random_day(self):
        """Should send tuple indicating fasting for random day in Ramadan."""

        item = ("2026-05-27", 9, randint(2, 30), "Wednesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ramadan" in result[1]
        assert result[2] is None

    def test_ramadan_ayyam_al_bid(self):
        """Should send tuple indicating fasting for Ramadan, not Ayyam al-Bid."""

        item = ("2026-05-27", 9, randint(13, 15), "Wednesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ramadan" in result[1]
        assert result[2] is None


class TestMonday:
    """Tests for correctly classifying Monday fasts, with prohibited fasts taking precendence."""

    def test_monday_regular(self):
        """Should return tuple indicating fasting on Monday."""

        item = ("2026-04-20", 10, 18, "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "weekly_sunnah" in result[1]
        assert result[2] is None

    def test_monday_ramadan(self):
        """Should return tuple indicating fasting for Ramadan, not Monday."""

        item = ("2026-04-20", 9, 15, "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ramadan" in result[1]
        assert result[2] is None

    def test_monday_ashura(self):
        """Should return ashura, not weekly_sunnah. Note since ASHURA_PREFERENCE is set to early, only considers 9th and 10th."""

        item = ("2026-06-25", 1, randint(9, 10), "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ashura" in result[1]
        assert result[2] is None

    def test_monday_arafah(self):
        """Should return arafah, not weekly_sunnah."""

        item = ("2026-06-25", 12, 9, "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "arafah" in result[1]
        assert result[2] is None

    def test_monday_early_dhul_hijjah(self):
        """Should return dhul_hijjah_early, not weekly_sunnah."""

        item = ("2026-06-25", 12, randint(1, 8), "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "dhul_hijjah_early" in result[1]
        assert result[2] is None

    def test_monday_ayyam_al_bid(self):
        """Should return tuple indicating fasting for Ayyam al-Bid, not Monday."""

        item = ("2026-04-20", 10, randint(13, 15), "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ayyam_al_bid" in result[1]
        assert result[2] is None

    def test_monday_eid_al_fitr(self):
        """Should return tuple prohibiting fasting for Eid al-Fitr, not Monday."""

        item = ("2026-03-20", 10, 1, "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "eid_al_fitr" in result[2]

    def test_monday_eid_al_adha(self):
        """Should return tuple prohibiting fasting for Eid al-Adha, not Monday."""

        item = ("2026-05-29", 12, 10, "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "eid_al_adha" in result[2]

    def test_monday_ayyam_al_tashreeq(self):
        """Should return tuple prohibiting fasting for Ayyam al-Tashreeq, not Monday."""

        item = ("2026-05-29", 12, 11, "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "ayyam_al_tashreeq" in result[2]


class TestThursday:
    """Tests for correctly classifying Thursday fasts, with prohibited fasts taking precendence."""

    def test_thursday_regular(self):
        """Should return tuple indicating fasting on Thursday."""

        item = ("2026-04-20", 10, 18, "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "weekly_sunnah" in result[1]
        assert result[2] is None

    def test_thursday_ramadan(self):
        """Should return tuple indicating fasting for Ramadan, not Thursday."""

        item = ("2026-04-20", 9, 15, "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ramadan" in result[1]
        assert result[2] is None

    def test_thursday_ashura(self):
        """Should return ashura, not weekly_sunnah. Note since ASHURA_PREFERENCE is set to early, only considers 9th and 10th."""

        item = ("2026-06-25", 1, randint(9, 10), "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ashura" in result[1]
        assert result[2] is None

    def test_thursday_arafah(self):
        """Should return arafah, not weekly_sunnah."""

        item = ("2026-06-25", 12, 9, "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "arafah" in result[1]
        assert result[2] is None

    def test_thursday_early_dhul_hijjah(self):
        """Should return dhul_hijjah_early, not weekly_sunnah."""

        item = ("2026-06-25", 12, randint(1, 8), "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "dhul_hijjah_early" in result[1]
        assert result[2] is None

    def test_thursday_ayyam_al_bid(self):
        """Should return tuple indicating fasting for Ayyam al-Bid, not Thursday."""

        item = ("2026-04-20", 10, randint(13, 15), "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ayyam_al_bid" in result[1]
        assert result[2] is None

    def test_thursday_eid_al_fitr(self):
        """Should return tuple prohibiting fasting for Eid al-Fitr, not Thursday."""

        item = ("2026-03-20", 10, 1, "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "eid_al_fitr" in result[2]

    def test_thursda_eid_al_adha(self):
        """Should return tuple prohibiting fasting for Eid al-Adha, not Thursday."""

        item = ("2026-05-29", 12, 10, "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "eid_al_adha" in result[2]

    def test_thursday_ayyam_al_tashreeq(self):
        """Should return tuple prohibiting fasting for Ayyam al-Tashreeq, not Thursday."""

        item = ("2026-05-29", 12, 11, "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "ayyam_al_tashreeq" in result[2]


class TestWeekday:
    """Tests for correctly classifying random weekday on non-prohibited fasting days."""

    def test_tuesday(self):
        """Should return tuple with no recommended fasting day, nor prohibition."""

        item = ("2026-05-29", 11, 18, "Tuesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert result[1] is None and result[2] is None

    def test_wednesday(self):
        """Should return tuple with no recommended fasting day, nor prohibition."""

        item = ("2026-05-29", 11, 18, "Wednesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert result[1] is None and result[2] is None

    def test_friday(self):
        """Should return tuple with no recommended fasting day, nor prohibition."""

        item = ("2026-05-29", 11, 18, "Friday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert result[1] is None and result[2] is None

    def test_saturday(self):
        """Should return tuple with no recommended fasting day, nor prohibition."""

        item = ("2026-05-29", 11, 18, "Saturday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert result[1] is None and result[2] is None

    def test_sunday(self):
        """Should return tuple with no recommended fasting day, nor prohibition."""

        item = ("2026-05-29", 11, 18, "Sunday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert result[1] is None and result[2] is None


class TestClassifyAyyamAlBid:
    """Tests for correctly classifying Ayyam al-Bid (13th-15th) as recommended fasting days."""

    def test_ayyam_al_bid_regular_13th(self):
        """Should return tuple with recommended fasting day 13th of the Hijri month."""

        item = ("2026-05-29", 11, 13, "Sunday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ayyam_al_bid" in result[1]
        assert result[2] is None

    def test_ayyam_al_bid_regular_14th(self):
        """Should return tuple with recommended fasting day for the 14th of the Hijri month."""

        item = ("2026-05-29", 11, 14, "Sunday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ayyam_al_bid" in result[1]
        assert result[2] is None

    def test_ayyam_al_bid_regular_15th(self):
        """Should return tuple with recommended fasting day 15th of the Hijri month."""

        item = ("2026-05-29", 11, 15, "Sunday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ayyam_al_bid" in result[1]
        assert result[2] is None

    def test_ayyam_al_bid_dhul_hijjah_13th(self):
        """Should return with tuple prohibiting fasting for Ayyam al-Tashreeq."""

        item = ("2026-05-29", 12, 13, "Sunday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert "prohibited" in result[1]
        assert "ayyam_al_tashreeq" in result[2]

    def test_ayyam_al_bid_dhul_hijjah_14th(self):
        """Should return with tuple not recommending fasting on the 14th, due to the 13th being prohibited by Ayyam al-Tashreeq."""

        item = ("2026-05-29", 12, 14, "Sunday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ayyam_al_bid" in result[1]
        assert result[2] is None

    def test_ayyam_al_bid_dhul_hijjah_15th(self):
        """15th of Dhul Hijjah is a valid Ayyam al-Bid day."""

        item = ("2026-05-31", 12, 15, "Sunday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ayyam_al_bid" in result[1]
        assert result[2] is None

    def test_ayyam_al_bid_dhul_hijjah_16th(self):
        """16th of Dhul Hijjah fasted as compensation for prohibited 13th."""

        item = ("2026-06-01", 12, 16, "Sunday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ayyam_al_bid" in result[1]
        assert result[2] is None

    def test_ayyam_al_bid_16th_non_dhul_hijjah(self):
        """16th of any other month is not an Ayyam al-Bid day."""

        item = ("2026-04-01", 10, 16, "Wednesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is False
        assert result[1] is None
        assert result[2] is None

    def test_ayyam_al_bid_priority_over_monday(self):
        """Ayyam al-Bid takes priority over weekly Sunnah on Monday."""

        item = ("2026-04-27", 10, 13, "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ayyam_al_bid" in result[1]
        assert result[2] is None

    def test_ayyam_al_bid_priority_over_thursday(self):
        """Ayyam al-Bid takes priority over weekly Sunnah on Thursday."""

        item = ("2026-04-30", 10, 13, "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ayyam_al_bid" in result[1]
        assert result[2] is None


class TestClassifyArafah:
    """Tests for Arafah fasting classification."""

    def test_arafah_classified_correctly(self):
        """9th of Dhul Hijjah should be classified as Arafah."""

        item = ("2026-05-26", 12, 9, "Tuesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "arafah" in result[1]
        assert result[2] is None

    def test_arafah_priority_over_monday(self):
        """Arafah takes priority over weekly Sunnah on Monday."""

        item = ("2026-05-26", 12, 9, "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "arafah" in result[1]
        assert result[2] is None

    def test_arafah_priority_over_thursday(self):
        """Arafah takes priority over weekly Sunnah on Thursday."""

        item = ("2026-05-26", 12, 9, "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "arafah" in result[1]
        assert result[2] is None


class TestClassifyAshura:
    """Tests for Ashura fasting classification."""

    def test_ashura_day_9(self):
        """9th of Muharram should be classified as Ashura."""

        item = ("2026-06-25", 1, 9, "Wednesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ashura" in result[1]
        assert result[2] is None

    def test_ashura_day_10(self):
        """10th of Muharram should be classified as Ashura."""
        item = ("2026-06-26", 1, 10, "Thursday")

        result = classify_day(*item)

        assert result is not None
        assert result[0] is True
        assert "ashura" in result[1]
        assert result[2] is None

    def test_ashura_priority_over_thursday(self):
        """Ashura takes priority over weekly Sunnah on Thursday."""

        item = ("2026-06-26", 1, 10, "Thursday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "ashura" in result[1]
        assert result[2] is None


class TestClassifyDhulHijjahEarly:
    """Tests for early Dhul Hijjah fasting days (1st-8th)."""

    def test_dhul_hijjah_day_1(self):
        """1st of Dhul Hijjah should be classified as dhul_hijjah_early."""

        item = ("2026-05-18", 12, 1, "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "dhul_hijjah_early" in result[1]
        assert result[2] is None

    def test_dhul_hijjah_day_8(self):
        """8th of Dhul Hijjah should be classified as dhul_hijjah_early."""

        item = ("2026-05-25", 12, 8, "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "dhul_hijjah_early" in result[1]
        assert result[2] is None

    def test_dhul_hijjah_day_9_is_arafah(self):
        """9th of Dhul Hijjah is Arafah, not dhul_hijjah_early."""

        item = ("2026-05-26", 12, 9, "Tuesday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "arafah" in result[1]
        assert result[2] is None

    def test_dhul_hijjah_priority_over_monday(self):
        """Dhul Hijjah early fasting takes priority over weekly Sunnah."""

        item = ("2026-05-18", 12, 1, "Monday")

        result = classify_day(*item)
        assert result is not None
        assert result[0] is True
        assert "dhul_hijjah_early" in result[1]
        assert result[2] is None
