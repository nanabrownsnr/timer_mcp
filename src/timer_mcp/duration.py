"""Duration parsing utilities for Timer MCP.

Handles conversion of duration specifications (seconds, minutes, hours, days)
into total seconds and validates input constraints.
"""

from typing import Optional


def parse_duration_to_seconds(
    seconds: Optional[int] = None,
    minutes: Optional[int] = None,
    hours: Optional[int] = None,
    days: Optional[int] = None,
) -> int:
    """Parse a duration specification into total seconds.

    Args:
        seconds: Seconds component (must be >= 0)
        minutes: Minutes component (must be >= 0)
        hours: Hours component (must be >= 0)
        days: Days component (must be >= 0)

    Returns:
        Total duration in seconds as an integer.

    Raises:
        ValueError: If no fields provided, any value is negative,
                    or total exceeds 1 year.
        TypeError: If any value is not an integer.
    """
    values = [seconds, minutes, hours, days]

    # Validate types
    for val in values:
        if val is not None and not isinstance(val, int):
            raise TypeError(f"Duration values must be integers, got {type(val).__name__}: {val}")

    # Check that at least one is provided
    if all(v is None for v in values):
        raise ValueError("At least one duration field must be provided (seconds, minutes, hours, or days)")

    # Check for negative values
    for name, val in zip(["seconds", "minutes", "hours", "days"], values):
        if val is not None and val < 0:
            raise ValueError(f"Duration '{name}' must be non-negative, got {val}")

    # Calculate total
    total = 0
    if seconds is not None:
        total += seconds
    if minutes is not None:
        total += minutes * 60
    if hours is not None:
        total += hours * 3600
    if days is not None:
        total += days * 86400

    # Enforce maximum (1 year)
    MAX_SECONDS = 86400 * 365
    if total > MAX_SECONDS:
        raise ValueError(f"Maximum duration is 1 year ({MAX_SECONDS} seconds), got {total}")

    return total


def format_duration(total_seconds: int) -> str:
    """Format a duration in seconds to a human-readable string.

    Args:
        total_seconds: Total seconds to format.

    Returns:
        Human-readable duration string (e.g., "2h 30m 15s").
    """
    if total_seconds <= 0:
        return "0s"

    parts = []
    days, remaining = divmod(total_seconds, 86400)
    hours, remaining = divmod(remaining, 3600)
    minutes, seconds = divmod(remaining, 60)

    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def parse_duration_string(duration_str: str) -> int:
    """Parse a duration string like '5 minutes', '30 seconds', '2 hours' into seconds.

    Args:
        duration_str: A string like '5 minutes', '30s', '2 hours', '1d 3h'.

    Returns:
        Total duration in seconds.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    import re

    total = 0
    pattern = r"(\d+)\s*(s|sec|seconds?|m|min|minutes?|h|hr|hours?|d|day|days?)"
    matches = re.findall(pattern, duration_str, re.IGNORECASE)

    if not matches:
        raise ValueError(f"Cannot parse duration string: '{duration_str}'")

    for value, unit in matches:
        value = int(value)
        unit_lower = unit.lower()

        if unit_lower in ("s", "sec", "second", "seconds"):
            total += value
        elif unit_lower in ("m", "min", "minute", "minutes"):
            total += value * 60
        elif unit_lower in ("h", "hr", "hour", "hours"):
            total += value * 3600
        elif unit_lower in ("d", "day", "days"):
            total += value * 86400

    if total <= 0:
        raise ValueError(f"Duration string '{duration_str}' resolved to zero or negative seconds")

    return total
