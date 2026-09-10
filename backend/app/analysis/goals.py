from datetime import date, timedelta


def project_completion_date(
    target_amount_minor: int,
    saved_amount_minor: int,
    avg_monthly_net_minor: float,
    today: date,
) -> date | None:
    """Projects when a goal will be reached at the current average monthly
    net savings rate. Returns None if savings are flat/negative — at that
    rate the goal is never reached, and a caller shouldn't display a fake
    date to a user who needs to know that."""
    remaining = target_amount_minor - saved_amount_minor
    if remaining <= 0:
        return today
    if avg_monthly_net_minor <= 0:
        return None

    months_needed = remaining / avg_monthly_net_minor
    # Approximate month-add via days; fine for a projection, not a ledger.
    return today + timedelta(days=months_needed * 30.44)


def progress_pct(target_amount_minor: int, saved_amount_minor: int) -> float:
    if target_amount_minor <= 0:
        return 0.0
    return round(min(100.0, saved_amount_minor / target_amount_minor * 100), 1)
