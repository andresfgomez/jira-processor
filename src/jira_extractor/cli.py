"""CLI entry point for jira-extractor."""
from __future__ import annotations

import sys

import click

from jira_extractor.config.loader import load_config
from jira_extractor.config.schema import AppConfig
from jira_extractor.logging_config import setup_logging


@click.group()
def main() -> None:
    """Jira Server data extractor — export issues to CSV or PostgreSQL."""


@main.command("extract")
@click.option("--config", "config_path", default="config.toml", show_default=True, help="Path to config.toml")
@click.option("--output-dir", default=None, help="Override output.directory from config")
@click.option(
    "--target",
    type=click.Choice(["csv", "postgres"]),
    default=None,
    help="Override output.target from config",
)
@click.option("--updated-after", default=None, help="Override time_range.updated_after (YYYY-MM-DD)")
@click.option("--updated-before", default=None, help="Override time_range.updated_before (YYYY-MM-DD)")
@click.option("--schedule", "use_schedule", is_flag=True, default=False, help="Run on a recurring schedule (requires [scheduler] extra)")
def extract_cmd(
    config_path: str,
    output_dir: str | None,
    target: str | None,
    updated_after: str | None,
    updated_before: str | None,
    use_schedule: bool,
) -> None:
    """Extract Jira issues and write them to CSV or PostgreSQL."""
    cfg = _load_and_override(config_path, output_dir, target, updated_after, updated_before)
    setup_logging(cfg.logging.level, cfg.logging.format)

    if use_schedule or cfg.schedule.enabled:
        _run_scheduled(cfg)
    else:
        _run_once(cfg)


@main.command("validate-config")
@click.option("--config", "config_path", default="config.toml", show_default=True)
def validate_config_cmd(config_path: str) -> None:
    """Print the resolved configuration (secrets redacted)."""
    try:
        cfg = load_config(config_path)
    except Exception as exc:
        click.echo(f"Configuration error: {exc}", err=True)
        sys.exit(1)

    setup_logging(cfg.logging.level, cfg.logging.format)

    import json

    safe = cfg.model_dump()
    # Redact secrets
    safe["jira"]["token"] = "**REDACTED**"
    if safe.get("postgres", {}).get("dsn"):
        safe["postgres"]["dsn"] = "**REDACTED**"
    click.echo(json.dumps(safe, indent=2, default=str))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_and_override(
    config_path: str,
    output_dir: str | None,
    target: str | None,
    updated_after: str | None,
    updated_before: str | None,
) -> AppConfig:
    try:
        cfg = load_config(config_path)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output_dir:
        cfg.output.directory = output_dir
    if target:
        cfg.output.target = target  # type: ignore[assignment]
    if updated_after:
        cfg.time_range.updated_after = updated_after
    if updated_before:
        cfg.time_range.updated_before = updated_before

    return cfg


def _run_once(cfg: AppConfig) -> None:
    from jira_extractor.extractor.extractor import run_extraction

    try:
        count = run_extraction(cfg)
        click.echo(f"Done. {count} issues exported.")
    except Exception as exc:
        click.echo(f"Extraction failed: {exc}", err=True)
        sys.exit(1)


def _run_scheduled(cfg: AppConfig) -> None:
    from jira_extractor.extractor.extractor import run_extraction
    from jira_extractor.scheduler.runner import start_scheduler

    def job() -> None:
        run_extraction(cfg)

    start_scheduler(job, cfg.schedule.cron, cfg.schedule.timezone)
