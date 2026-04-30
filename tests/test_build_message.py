from lambda_function.reminder_function import build_message


class TestAyyamAlBid:
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


class TestRamadan:
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


class TestDhulHijjahEarly:
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


class TestArafah:
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


class TestAshura:
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


class TestWeeklySunnah:
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


class TestProhibited:
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


class TestUnknownFastType:
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
