"""APScheduler-based runner for scheduled extractions."""
from __future__ import annotations

import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


def start_scheduler(
    run_fn: Callable[[], None],
    cron_expression: str,
    timezone: str,
) -> None:
    """Block indefinitely, calling run_fn on the given cron schedule."""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler  # type: ignore[import-untyped]
        from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "APScheduler is required for --schedule mode. "
            "Install it with: uv add --optional scheduler apscheduler"
        ) from exc

    # Parse the 5-field cron expression: minute hour dom month dow
    parts = cron_expression.split()
    if len(parts) != 5:
        raise ValueError(f"Expected a 5-field cron expression, got: {cron_expression!r}")
    minute, hour, day, month, day_of_week = parts

    trigger = CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
        timezone=timezone,
    )

    scheduler = BlockingScheduler(timezone=timezone)
    scheduler.add_job(run_fn, trigger=trigger, id="jira_extract", replace_existing=True)

    logger.info(
        "Scheduler started — cron: %s tz: %s (press Ctrl+C to stop)",
        cron_expression,
        timezone,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
