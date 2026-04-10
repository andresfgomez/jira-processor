"""Load and merge configuration from config.toml + environment variables."""
from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from dotenv import load_dotenv  # type: ignore[import-untyped]

from jira_extractor.config.schema import (
    AppConfig,
    CustomFieldsConfig,
    JiraConfig,
    LoggingConfig,
    OutputConfig,
    PostgresConfig,
    ScheduleConfig,
    TimeRangeConfig,
)


def load_config(config_path: str | Path = "config.toml") -> AppConfig:
    """Load config.toml, overlay environment variables, return validated AppConfig."""
    load_dotenv()

    path = Path(config_path)
    raw: dict[str, Any] = {}
    if path.exists():
        with open(path, "rb") as fh:
            raw = tomllib.load(fh)

    jira_raw = raw.get("jira", {})
    # Token always comes from env; never from the config file.
    token = os.environ.get("JIRA_TOKEN", jira_raw.pop("token", ""))
    if not token:
        raise ValueError(
            "JIRA_TOKEN environment variable is required but not set. "
            "Add it to your .env file or export it before running."
        )

    jira_cfg = JiraConfig(token=token, **jira_raw)

    time_range_cfg = TimeRangeConfig(**raw.get("time_range", {}))
    custom_fields_cfg = CustomFieldsConfig(**raw.get("custom_fields", {}))
    output_cfg = OutputConfig(**raw.get("output", {}))

    postgres_raw = raw.get("postgres", {})
    # DSN can come from env or config; env takes precedence.
    postgres_dsn = os.environ.get("POSTGRES_DSN", postgres_raw.pop("dsn", ""))
    postgres_cfg = PostgresConfig(dsn=postgres_dsn, **postgres_raw)

    schedule_cfg = ScheduleConfig(**raw.get("schedule", {}))
    logging_cfg = LoggingConfig(**raw.get("logging", {}))

    return AppConfig(
        jira=jira_cfg,
        time_range=time_range_cfg,
        custom_fields=custom_fields_cfg,
        output=output_cfg,
        postgres=postgres_cfg,
        schedule=schedule_cfg,
        logging=logging_cfg,
    )
