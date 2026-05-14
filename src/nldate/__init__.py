from __future__ import annotations

import re
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

NUMBER_WORDS: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "a": 1,
    "an": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


def parse(s: str, today: date | None = None) -> date:
    """
    Parse a natural-language date string into a datetime.date.

    Examples:
        parse("today")
        parse("tomorrow")
        parse("5 days before December 1st, 2025")
        parse("next Tuesday")
        parse("1 year and 2 months after yesterday")
    """
    if today is None:
        today = date.today()

    text = _normalize(s)

    if text == "":
        raise ValueError("empty date string")

    direct = _parse_simple_relative(text, today)
    if direct is not None:
        return direct

    weekday = _parse_weekday(text, today)
    if weekday is not None:
        return weekday

    in_ago = _parse_in_or_ago(text, today)
    if in_ago is not None:
        return in_ago

    before_after = _parse_before_after(text, today)
    if before_after is not None:
        return before_after

    absolute = _parse_absolute_date(text, today)
    if absolute is not None:
        return absolute

    raise ValueError(f"Could not parse date: {s!r}")


def _normalize(s: str) -> str:
    text = s.strip().lower()
    text = text.replace(",", " ")
    text = re.sub(r"\b(\d+)(st|nd|rd|th)\b", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _parse_simple_relative(text: str, today: date) -> date | None:
    if text == "today":
        return today
    if text == "tomorrow":
        return today + timedelta(days=1)
    if text == "yesterday":
        return today - timedelta(days=1)
    return None


def _parse_weekday(text: str, today: date) -> date | None:
    weekday_pattern = (
        r"(next|last|this)? ?"
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
        )
    match = re.fullmatch(weekday_pattern, text)
    
    if match is None:
        return None

    modifier = match.group(1)
    weekday_name = match.group(2)
    target = WEEKDAYS[weekday_name]
    current = today.weekday()

    if modifier == "last":
        days_back = (current - target) % 7
        if days_back == 0:
            days_back = 7
        return today - timedelta(days=days_back)

    days_forward = (target - current) % 7

    if modifier == "next" and days_forward == 0:
        days_forward = 7

    return today + timedelta(days=days_forward)


def _parse_in_or_ago(text: str, today: date) -> date | None:
    in_match = re.fullmatch(r"in (.+)", text)
    if in_match is not None:
        delta = _parse_duration(in_match.group(1))
        return today + delta

    ago_match = re.fullmatch(r"(.+) ago", text)
    if ago_match is not None:
        delta = _parse_duration(ago_match.group(1))
        return today - delta

    return None


def _parse_before_after(text: str, today: date) -> date | None:
    match = re.fullmatch(r"(.+) (before|after|from) (.+)", text)
    if match is None:
        return None

    duration_text = match.group(1)
    direction = match.group(2)
    base_text = match.group(3)

    delta = _parse_duration(duration_text)
    base = parse(base_text, today)

    if direction == "before":
        return base - delta

    return base + delta


def _parse_duration(text: str) -> relativedelta:
    years = 0
    months = 0
    weeks = 0
    days = 0

    cleaned = text.replace(" and ", " ")
    parts = re.findall(
        r"\b(\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a|an)\s+"
        r"(year|years|month|months|week|weeks|day|days)\b",
        cleaned,
    )

    if not parts:
        raise ValueError(f"Could not parse duration: {text!r}")

    for raw_number, unit in parts:
        number = _parse_number(raw_number)

        if unit.startswith("year"):
            years += number
        elif unit.startswith("month"):
            months += number
        elif unit.startswith("week"):
            weeks += number
        elif unit.startswith("day"):
            days += number

    return relativedelta(years=years, months=months, weeks=weeks, days=days)


def _parse_number(raw: str) -> int:
    if raw.isdigit():
        return int(raw)
    return NUMBER_WORDS[raw]


def _parse_absolute_date(text: str, today: date) -> date | None:
    patterns = [
    (
        r"(january|february|march|april|may|june|july|august|"
        r"september|october|november|december) "
        r"(\d{1,2}) (\d{4})"
    ),
    r"(\d{4})-(\d{1,2})-(\d{1,2})",
    r"(\d{1,2})/(\d{1,2})/(\d{4})",
]

    month_names = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    month_match = re.fullmatch(patterns[0], text)
    if month_match is not None:
        month = month_names[month_match.group(1)]
        day = int(month_match.group(2))
        year = int(month_match.group(3))
        return date(year, month, day)

    iso_match = re.fullmatch(patterns[1], text)
    if iso_match is not None:
        year = int(iso_match.group(1))
        month = int(iso_match.group(2))
        day = int(iso_match.group(3))
        return date(year, month, day)

    slash_match = re.fullmatch(patterns[2], text)
    if slash_match is not None:
        month = int(slash_match.group(1))
        day = int(slash_match.group(2))
        year = int(slash_match.group(3))
        return date(year, month, day)

    no_year_pattern = (
        r"(january|february|march|april|may|june|july|august|"
        r"september|october|november|december) "
        r"(\d{1,2})"
        )
    
    no_year_match = re.fullmatch(no_year_pattern, text)

    if no_year_match is not None:
        month = month_names[no_year_match.group(1)]
        day = int(no_year_match.group(2))
        return date(today.year, month, day)

    return None
