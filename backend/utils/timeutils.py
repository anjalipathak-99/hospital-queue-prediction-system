"""
Single source of truth for "what time/day is it" across the app.

Everything (created_at defaults, "today" filters, ML hour/day features and the
SQL date()/hour() grouping in the analytics queries) uses the SAME clock:
naive local time in APP_TIMEZONE (default Asia/Kolkata).

Previously rows were stamped with datetime.utcnow() but filtered with
date.today() (server-local date), so between local midnight and the UTC
offset the "today" queue silently missed new appointments, and the ML
model received a UTC hour instead of the hospital's local hour.
"""

import os
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

DEFAULT_TIMEZONE = "Asia/Kolkata"
_TZ = None
_TZ_RESOLVED = False


def _get_tz():
    global _TZ, _TZ_RESOLVED
    if not _TZ_RESOLVED:
        _TZ_RESOLVED = True
        name = os.environ.get("APP_TIMEZONE", DEFAULT_TIMEZONE)
        try:
            _TZ = ZoneInfo(name) if ZoneInfo else None
        except Exception:
            # tz database missing (e.g. Windows without the `tzdata` package)
            _TZ = None
    return _TZ


def now():
    """Current naive datetime in the hospital's timezone."""
    tz = _get_tz()
    if tz is None:
        return datetime.now()
    return datetime.now(tz).replace(tzinfo=None)


def today():
    """Current date in the hospital's timezone."""
    return now().date()
