import re
from datetime import datetime, timedelta

DAY = timedelta(days=1)
WEEK = timedelta(weeks=1)

ErrDateTimeParsing = ValueError("Invalid date/time format")


def parse_duration(s: str) -> timedelta:
    """
    Parses a duration string supporting ns, us, ms, s, m, h, d (24 hours), w (7 days).
    Example: "5m", "1d2h", "10.5s"
    """
    if not s:
        raise ValueError("empty duration string")
    
    # Handle pure numbers if given as seconds
    try:
        val = float(s)
        return timedelta(seconds=val)
    except ValueError:
        pass

    pattern = re.compile(r'([+-]?(?:\d+(?:\.\d+)?|\.\d+))([a-zA-Zµ]+)')
    matches = pattern.findall(s)
    if not matches:
        raise ValueError(f"invalid duration: {s}")

    total_seconds = 0.0
    units = {
        'ns': 1e-9,
        'us': 1e-6,
        'µs': 1e-6,
        'ms': 1e-3,
        's': 1.0,
        'm': 60.0,
        'h': 3600.0,
        'd': 86400.0,
        'w': 7 * 86400.0,
    }

    for val_str, unit in matches:
        unit = unit.lower()
        if unit not in units:
            raise ValueError(f"unknown unit {unit} in duration {s}")
        total_seconds += float(val_str) * units[unit]

    return timedelta(seconds=total_seconds)


def next_time(now: datetime, target_time: datetime) -> datetime:
    """
    Takes a datetime with HH:MM:SS set and returns the future datetime relative to now
    with the same HH:MM:SS.
    """
    res = now.replace(
        hour=target_time.hour,
        minute=target_time.minute,
        second=target_time.second,
        microsecond=0,
    )
    if res <= now:
        res += timedelta(days=1)
    return res


def parse_date_time(now: datetime, s: str) -> datetime:
    """
    Parses date/times in one of the following formats:
    - Date and 24h time: YYYY-MM-DD HH:MM:SS
    - Just a date: YYYY-MM-DD
    - Just a 24h time: HH:MM:SS
    - Just a time (12-hour, 'kitchen' style): H:MM AM/PM or H:MM:SS AM/PM
    """
    s = s.strip()
    
    # 1. YYYY-MM-DD HH:MM:SS
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    # 2. YYYY-MM-DD
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    except ValueError:
        pass

    # 3. HH:MM:SS
    try:
        t = datetime.strptime(s, "%H:%M:%S")
        return next_time(now, t)
    except ValueError:
        pass

    # 4. HH:MM (24-hour without seconds)
    try:
        t = datetime.strptime(s, "%H:%M")
        return next_time(now, t)
    except ValueError:
        pass

    # 5. H:MM AM/PM or H:MM:SS AM/PM
    for fmt in ("%I:%M %p", "%I:%M:%S %p", "%I:%M%p", "%I:%M:%S%p"):
        try:
            t = datetime.strptime(s, fmt)
            return next_time(now, t)
        except ValueError:
            pass

    raise ErrDateTimeParsing
