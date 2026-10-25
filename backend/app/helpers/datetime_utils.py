from datetime import date, datetime, time, timedelta, timezone

PERIODS_PER_DAY = 48
PERIOD_MINUTES = 30
HOURS_PER_DAY = 24


def to_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("decision_time must be timezone-aware")
    return value.astimezone(timezone.utc)


def assume_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def delivery_bounds(delivery_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(delivery_date, time.min, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def half_hour_slots(delivery_date: date) -> list[datetime]:
    start, _ = delivery_bounds(delivery_date)
    return [start + timedelta(minutes=PERIOD_MINUTES * index) for index in range(PERIODS_PER_DAY)]


def hourly_slots(delivery_date: date) -> list[datetime]:
    start, _ = delivery_bounds(delivery_date)
    return [start + timedelta(hours=index) for index in range(HOURS_PER_DAY)]


def hour_start(value: datetime) -> datetime:
    value = assume_utc(value)
    return value.replace(minute=0, second=0, microsecond=0)


def format_utc(value: datetime) -> str:
    text = value.astimezone(timezone.utc).isoformat()
    if text.endswith("+00:00"):
        return text[:-6] + "Z"
    return text
