from ingestion.fetch_hijri_calendar import classify_day
from random import randint


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


class TestRamadan:
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


class TestAyyamAlBid:
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


class TestArafah:
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


class TestAshura:
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


class TestDhulHijjahEarly:
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
