from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any, cast

import dateparser
import parsedatetime
from dateutil.relativedelta import relativedelta


def parse(s: str, today: date | None = None) -> date:
    """
    Parse a natural-language date string into a datetime.date.
    """
    ref_date = today if today is not None else date.today()
    ref_dt = datetime.combine(ref_date, datetime.min.time())
    s_lower = s.lower().strip()

    if s_lower == "":
        raise ValueError("empty date string")

    weekday_result = _parse_weekday(s_lower, ref_date)
    if weekday_result is not None:
        return weekday_result

    relative_result = _parse_before_after_from(s_lower, ref_dt)
    if relative_result is not None:
        return relative_result

    cal = parsedatetime.Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)
    time_struct, status = cal.parse(s, ref_dt)

    if status.accuracy > 0:
        return date(*time_struct[:3])

    parsed = dateparser.parse(
        s,
        settings={
            "RELATIVE_BASE": ref_dt,
            "PREFER_DATES_FROM": "future",
        },
    )

    if parsed is not None:
        return cast(date, parsed.date())

    raise ValueError(f"Could not parse: {s}")


def _parse_weekday(text: str, ref_date: date) -> date | None:
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    words = text.split()

    if len(words) != 2:
        return None

    modifier = words[0]
    weekday_name = words[1]

    if weekday_name not in weekdays:
        return None

    target = weekdays[weekday_name]
    current = ref_date.weekday()

    if modifier in {"next", "this"}:
        diff = (target - current) % 7
        if diff == 0:
            diff = 7
        return ref_date + timedelta(days=diff)

    if modifier == "last":
        back = (current - target) % 7
        if back == 0:
            back = 7
        return ref_date - timedelta(days=back)

    return None


def _parse_before_after_from(text: str, ref_dt: datetime) -> date | None:
    anchor_shift = relativedelta()
    working_text = text

    if "yesterday" in working_text:
        anchor_shift = relativedelta(days=-1)
        working_text = working_text.replace("yesterday", "today")
    elif "tomorrow" in working_text:
        anchor_shift = relativedelta(days=1)
        working_text = working_text.replace("tomorrow", "today")

    keywords = r"\b(before|after|from)\b"

    if re.search(keywords, working_text) is None:
        return None

    parts = re.split(keywords, working_text, maxsplit=1)

    if len(parts) != 3:
        return None

    offset_part, relation, base_part = [part.strip() for part in parts]

    if base_part in {"today", "now"}:
        anchor_dt = ref_dt
    else:
        anchor_dt = dateparser.parse(
            base_part,
            settings={"RELATIVE_BASE": ref_dt},
        )

    if anchor_dt is None:
        return None

    offset_delta = _parse_offset_delta(offset_part)

    if offset_delta is None:
        return None

    anchor_with_shift = anchor_dt + anchor_shift

    if relation == "before":
        result = anchor_with_shift - offset_delta
    else:
        result = anchor_with_shift + offset_delta

    return result.date()


def _parse_offset_delta(offset_part: str) -> relativedelta | None:
    matches = re.findall(
        r"(?:(\d+)|(the|a|an))\s+"
        r"(year|month|week|day)s?",
        offset_part,
    )

    if not matches:
        return None

    delta_args: dict[str, int] = {}

    for number_text, _article, unit in matches:
        count = int(number_text) if number_text else 1
        unit_key = f"{unit}s"
        delta_args[unit_key] = delta_args.get(unit_key, 0) + count

    return relativedelta(**cast(Any, delta_args))
