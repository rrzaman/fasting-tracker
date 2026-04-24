from lambda_function.reminder_function import format_date


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
