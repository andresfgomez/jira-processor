# Jira Extractor

A Python CLI tool that extracts issues from a **Jira Server** instance via JQL and exports them to a **CSV file** or a **PostgreSQL database**. Built for scheduled or on-demand runs without exhausting the Jira API.

---

## Features

- Query issues using JQL with configurable criteria (project, issue type, status, labels, time range)
- Paginated extraction respecting Jira Server's API limits
- Configurable request delay and automatic exponential backoff on rate-limit responses (HTTP 429 / 503)
- Export to **CSV** or **PostgreSQL** (upsert-safe — reruns never duplicate rows)
- Custom field support: sprint, story points, and any two additional custom fields
- Run manually from the CLI or on a recurring schedule via APScheduler
- Secrets managed through environment variables (token never stored in config files)

---

## Exported Fields

| Field | Description |
|---|---|
| `key` | Jira issue key (e.g. `PROJ-123`) |
| `category` | Project category |
| `issuetype` | Issue type (Bug, Story, Task, …) |
| `status` | Current workflow status |
| `resolution_date` | Date the issue was resolved |
| `sprint_name` | Name of the active (or most recent) sprint |
| `assignee_name` | Assignee display name |
| `assignee_email` | Assignee email address |
| `creator_name` | Creator display name |
| `creator_email` | Creator email address |
| `story_points` | Story points estimate |
| `ai_assisted_effort` | Custom field: AI Assisted Effort |
| `ai_usage_level` | Custom field: AI Usage Level |

---

## Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) package manager
- Access to a Jira Server instance
- A Jira personal access token

---

## Installation

```bash
git clone https://github.com/andresfgomez/jira-processor.git
cd jira-processor
uv sync
```

For scheduled runs, install the optional APScheduler dependency:

```bash
uv sync --extra scheduler
```

---

## Configuration

### 1. Set up secrets

```bash
cp .env.example .env
```

Edit `.env`:

```ini
# Required
JIRA_TOKEN=your-personal-access-token

# Required only when output.target = "postgres"
POSTGRES_DSN=postgresql://user:password@host:5432/dbname
```

> **Getting a Jira personal access token:** go to your Jira profile → **Personal Access Tokens** → **Create token**.

### 2. Edit `config.toml`

```toml
[jira]
base_url              = "https://your-jira.company.com"
projects              = ["PROJ", "INFRA"]   # Jira project keys
issue_types           = ["Bug", "Story"]    # empty [] = all types
statuses              = ["Done"]            # empty [] = all statuses
labels                = []
max_results           = 100                 # page size (max 100)
request_delay_seconds = 0.5                 # increase if rate-limited

[time_range]
updated_after  = "2024-01-01"   # YYYY-MM-DD; issues updated on or after
updated_before = ""             # leave empty for no upper bound

[custom_fields]
# Find field IDs via: GET https://your-jira.company.com/rest/api/2/field
sprint             = "customfield_10020"
story_points       = "customfield_10016"
ai_assisted_effort = "customfield_XXXXX"   # replace with actual field ID
ai_usage_level     = "customfield_XXXXX"   # replace with actual field ID

[output]
target    = "csv"        # "csv" or "postgres"
directory = "./output"   # destination folder for CSV files

[postgres]
dsn    = ""              # or set POSTGRES_DSN env var
table  = "jira_issues"
schema = "public"
upsert = true            # update existing rows on re-run

[schedule]
enabled  = false
cron     = "0 6 * * *"  # 6 AM daily (5-field cron expression)
timezone = "UTC"

[logging]
level  = "INFO"    # DEBUG | INFO | WARNING | ERROR
format = "text"    # "text" or "json"
```

---

## Usage

### Verify configuration

Print the resolved configuration with secrets redacted before running:

```bash
uv run jira-extractor validate-config
```

### Export to CSV

```bash
uv run jira-extractor extract
```

Output files are written to `./output/` with names like:
```
output/jira_a3f9c21b_20250401_143022.csv
              ↑ JQL hash    ↑ UTC timestamp
```

Each run creates a new file — existing files are never overwritten.

### Export to PostgreSQL

```bash
uv run jira-extractor extract --target postgres
```

The target table is created automatically on first run. Subsequent runs upsert on the `key` column — safe to rerun the same time range.

### Override config values inline

```bash
# Different time range
uv run jira-extractor extract --updated-after 2025-01-01 --updated-before 2025-03-31

# Different output directory
uv run jira-extractor extract --output-dir /data/exports

# Switch output target without editing config.toml
uv run jira-extractor extract --target postgres

# Use a different config file
uv run jira-extractor extract --config /path/to/other-config.toml
```

### Scheduled run

Runs indefinitely on the cron schedule defined in `config.toml` (requires the `scheduler` extra):

```bash
uv run jira-extractor extract --schedule
```

Or enable it permanently in `config.toml`:

```toml
[schedule]
enabled  = true
cron     = "0 6 * * *"
timezone = "America/New_York"
```

---

## Project Structure

```
jira-processor/
├── config.toml                          # All non-secret configuration
├── .env.example                         # Template for secrets
├── pyproject.toml                       # Dependencies and CLI entry point
├── output/                              # Default CSV output directory
└── src/jira_extractor/
    ├── cli.py                           # CLI commands (extract, validate-config)
    ├── logging_config.py                # Logging setup
    ├── config/
    │   ├── schema.py                    # Pydantic v2 config models
    │   └── loader.py                    # Loads config.toml + env vars
    ├── client/
    │   ├── jira_client.py               # httpx wrapper with Bearer auth
    │   └── rate_limiter.py              # Request delay + backoff on 429/503
    ├── extractor/
    │   ├── query_builder.py             # Assembles JQL from config
    │   ├── paginator.py                 # startAt/maxResults pagination
    │   └── extractor.py                 # Orchestration + field flattening
    ├── output/
    │   ├── writers.py                   # CSVWriter and PostgresWriter
    │   ├── factory.py                   # Selects writer from config
    │   └── naming.py                    # Timestamped output file naming
    └── scheduler/
        └── runner.py                    # APScheduler wrapper
```

---

## Running Tests

```bash
uv run pytest tests/ -v
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `httpx` | HTTP client for Jira API calls |
| `pydantic-settings` | Config validation and env var merging |
| `click` | CLI framework |
| `psycopg[binary]` | PostgreSQL driver |
| `python-dotenv` | Loads `.env` file |
| `python-json-logger` | Optional JSON-formatted log output |
| `apscheduler` *(optional)* | In-process cron scheduling |
