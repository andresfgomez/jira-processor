"""Configuration schema — Pydantic v2 models for the full application config."""
from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class JiraConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JIRA_")

    base_url: str = "https://jira.example.com"
    token: SecretStr = Field(default=..., description="Personal access token")
    projects: list[str] = Field(default_factory=list)
    issue_types: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    max_results: int = Field(default=100, ge=1, le=100)
    request_delay_seconds: float = Field(default=0.5, ge=0.0)

    @field_validator("base_url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


class TimeRangeConfig(BaseSettings):
    updated_after: str = ""
    updated_before: str = ""


class CustomFieldsConfig(BaseSettings):
    """Jira custom field IDs — look these up in your Jira instance via
    /rest/api/2/field and find the 'id' for each field."""

    sprint: str = "customfield_10020"
    story_points: str = "customfield_10016"
    ai_assisted_effort: str = "customfield_10100"
    ai_usage_level: str = "customfield_10101"


class OutputConfig(BaseSettings):
    target: Literal["csv", "postgres"] = "csv"
    directory: str = "./output"
    csv_fields: list[str] = Field(
        default_factory=lambda: [
            "key",
            "category",
            "issuetype",
            "status",
            "resolution_date",
            "sprint_name",
            "assignee_name",
            "assignee_email",
            "creator_name",
            "creator_email",
            "story_points",
            "ai_assisted_effort",
            "ai_usage_level",
        ]
    )


class PostgresConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", populate_by_name=True)

    dsn: SecretStr = Field(default=SecretStr(""), description="PostgreSQL connection DSN")
    table: str = "jira_issues"
    schema_name: str = Field(default="public", alias="schema")
    upsert: bool = True


class ScheduleConfig(BaseSettings):
    enabled: bool = False
    cron: str = "0 6 * * *"
    timezone: str = "UTC"


class LoggingConfig(BaseSettings):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["text", "json"] = "text"


class AppConfig(BaseSettings):
    jira: JiraConfig
    time_range: TimeRangeConfig = Field(default_factory=TimeRangeConfig)
    custom_fields: CustomFieldsConfig = Field(default_factory=CustomFieldsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
