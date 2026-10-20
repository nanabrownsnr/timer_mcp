"""Tests for duration parsing module."""

import pytest

from timer_mcp.duration import (
    parse_duration_to_seconds,
    format_duration,
    parse_duration_string,
)


class TestParseDurationToSeconds:
    """Tests for parse_duration_to_seconds function."""

    def test_seconds_only(self):
        assert parse_duration_to_seconds(seconds=30) == 30

    def test_minutes_only(self):
        assert parse_duration_to_seconds(minutes=5) == 300

    def test_hours_only(self):
        assert parse_duration_to_seconds(hours=2) == 7200

    def test_days_only(self):
        assert parse_duration_to_seconds(days=1) == 86400

    def test_combined_duration(self):
        result = parse_duration_to_seconds(days=1, hours=2, minutes=30, seconds=15)
        assert result == 95415  # 86400 + 7200 + 1800 + 15

    def test_zero_value_single_field(self):
        """Zero should be a valid value for a single field."""
        assert parse_duration_to_seconds(seconds=0) == 0

    def test_all_fields_zero(self):
        """All zeros should total zero."""
        assert parse_duration_to_seconds(seconds=0, minutes=0, hours=0, days=0) == 0

    def test_no_fields_provided(self):
        """Must raise ValueError when no fields provided."""
        with pytest.raises(ValueError, match="At least one duration field"):
            parse_duration_to_seconds()

    def test_all_fields_none(self):
        """Must raise ValueError when all fields are None."""
        with pytest.raises(ValueError, match="At least one duration field"):
            parse_duration_to_seconds(seconds=None, minutes=None, hours=None, days=None)

    def test_negative_seconds(self):
        """Must raise ValueError for negative seconds."""
        with pytest.raises(ValueError, match="must be non-negative"):
            parse_duration_to_seconds(seconds=-1)

    def test_negative_minutes(self):
        with pytest.raises(ValueError, match="must be non-negative"):
            parse_duration_to_seconds(minutes=-5)

    def test_negative_hours(self):
        with pytest.raises(ValueError, match="must be non-negative"):
            parse_duration_to_seconds(hours=-2)

    def test_negative_days(self):
        with pytest.raises(ValueError, match="must be non-negative"):
            parse_duration_to_seconds(days=-1)

    def test_maximum_duration_one_year(self):
        """Must raise ValueError when duration exceeds 1 year."""
        with pytest.raises(ValueError, match="Maximum duration is 1 year"):
            parse_duration_to_seconds(days=366)

    def test_maximum_duration_exceeded_via_hours(self):
        with pytest.raises(ValueError, match="Maximum duration is 1 year"):
            parse_duration_to_seconds(hours=8761)

    def test_large_value_single_field(self):
        """Large but valid single field should work."""
        # 365 days = 1 year = maximum allowed
        result = parse_duration_to_seconds(days=365)
        assert result == 31536000

    def test_type_error_string_value(self):
        """Must raise TypeError for non-integer values."""
        with pytest.raises(TypeError, match="Duration values must be integers"):
            parse_duration_to_seconds(seconds="30")

    def test_type_error_float_value(self):
        with pytest.raises(TypeError, match="Duration values must be integers"):
            parse_duration_to_seconds(minutes=5.5)

    def test_large_hours(self):
        """Hours > 24 should be allowed (they're just cumulative)."""
        assert parse_duration_to_seconds(hours=48) == 172800


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_zero_seconds(self):
        assert format_duration(0) == "0s"

    def test_single_seconds(self):
        assert format_duration(30) == "30s"

    def test_minutes_only(self):
        assert format_duration(300) == "5m"

    def test_hours_only(self):
        assert format_duration(7200) == "2h"

    def test_days_only(self):
        assert format_duration(86400) == "1d"

    def test_combined_format(self):
        result = format_duration(95415)
        assert result == "1d 2h 30m 15s"

    def test_minutes_and_seconds(self):
        result = format_duration(135)
        assert result == "2m 15s"

    def test_hours_and_seconds(self):
        result = format_duration(3661)
        assert result == "1h 1m 1s"

    def test_hours_and_minutes(self):
        result = format_duration(3900)
        assert result == "1h 5m"

    def test_days_and_hours(self):
        result = format_duration(172800)
        assert result == "2d"

    def test_large_duration(self):
        result = format_duration(31536000)
        assert result == "365d"

    def test_negative_value(self):
        assert format_duration(-100) == "0s"

    def test_single_digit_seconds(self):
        assert format_duration(7) == "7s"

    def test_exact_hours(self):
        assert format_duration(3600) == "1h"

    def test_exact_days(self):
        assert format_duration(172800) == "2d"


class TestParseDurationString:
    """Tests for parse_duration_string function."""

    def test_seconds_short(self):
        assert parse_duration_string("30s") == 30

    def test_seconds_plural(self):
        assert parse_duration_string("30 seconds") == 30

    def test_minutes_short(self):
        assert parse_duration_string("5m") == 300

    def test_minutes_plural(self):
        assert parse_duration_string("5 minutes") == 300

    def test_hours_short(self):
        assert parse_duration_string("2h") == 7200

    def test_hours_plural(self):
        assert parse_duration_string("2 hours") == 7200

    def test_days_short(self):
        assert parse_duration_string("1d") == 86400

    def test_days_plural(self):
        assert parse_duration_string("1 day") == 86400

    def test_combined_string(self):
        assert parse_duration_string("1d 2h 30m 15s") == 95415

    def test_case_insensitive(self):
        assert parse_duration_string("5 MINUTES") == 300
        assert parse_duration_string("2 HOURS") == 7200

    def test_mixed_case(self):
        assert parse_duration_string("1D 2h 30M 15S") == 95415

    def test_invalid_string(self):
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_duration_string("not a duration")

    def test_empty_string(self):
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_duration_string("")

    def test_zero_duration_string(self):
        with pytest.raises(ValueError, match="resolved to zero"):
            parse_duration_string("0 seconds")

    def test_secs_abbreviation(self):
        assert parse_duration_string("30 secs") == 30

    def test_min_abbreviation(self):
        assert parse_duration_string("5 min") == 300

    def test_hr_abbreviation(self):
        assert parse_duration_string("2 hr") == 7200

    def test_no_spaces(self):
        assert parse_duration_string("30s") == 30
        assert parse_duration_string("5m") == 300
