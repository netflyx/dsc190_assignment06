from datetime import date

import pytest

from nldate import parse


def test_today() -> None:
    assert parse("today", today=date(2025, 12, 1)) == date(2025, 12, 1)


def test_tomorrow() -> None:
    assert parse("tomorrow", today=date(2025, 12, 1)) == date(2025, 12, 2)


def test_yesterday() -> None:
    assert parse("yesterday", today=date(2025, 12, 1)) == date(2025, 11, 30)


def test_in_three_days() -> None:
    assert parse("in 3 days", today=date(2025, 12, 1)) == date(2025, 12, 4)


def test_three_days_ago() -> None:
    assert parse("3 days ago", today=date(2025, 12, 1)) == date(2025, 11, 28)


def test_next_tuesday() -> None:
    assert parse("next Tuesday", today=date(2025, 12, 1)) == date(2025, 12, 2)


def test_last_friday() -> None:
    assert parse("last Friday", today=date(2025, 12, 1)) == date(2025, 11, 28)


def test_absolute_month_date() -> None:
    assert parse("December 1st, 2025") == date(2025, 12, 1)


def test_five_days_before_absolute_date() -> None:
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_one_year_two_months_after_yesterday() -> None:
    assert parse(
        "1 year and 2 months after yesterday",
        today=date(2025, 12, 1),
    ) == date(2027, 1, 30)


def test_two_weeks_from_tomorrow() -> None:
    assert parse("two weeks from tomorrow", today=date(2025, 12, 1)) == date(
        2025, 12, 16
    )


def test_iso_date() -> None:
    assert parse("2025-12-01") == date(2025, 12, 1)


def test_bad_input_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse("banana day")
