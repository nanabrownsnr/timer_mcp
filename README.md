# Timer MCP

Timer MCP is an unauthenticated Twynity Model Context Protocol (MCP) server that provides delayed execution capabilities. Schedule timers with granular durations (seconds, minutes, hours, days) and receive callback notifications when they expire.

## Features

- **Granular duration support** - Specify durations using seconds, minutes, hours, and days
- **Background scheduling** - Jobs execute asynchronously in the background
- **Status polling** - Poll a status URL to check job progress
- **Job management** - List, cancel, and view completed jobs
- **Docker-ready** - Runs in a container with health checks
- **Unauthenticated** - No user context or identity checks required

## Installation

### From source

```bash
pip install -r requirements.txt
```

### Using Docker

```bash
docker build -t timer-mcp .
docker run -p 8000:8000 timer-mcp
```

### Using uvicorn directly

```bash
uvicorn timer_mcp.main:app --host 0.0.0.0 --port 8000
```

### Environment variables

| Variable     | Description                        | Default   |
|-------------|------------------------------------|-----------|
| `HOST`      | Bind address                       | `0.0.0.0` |
| `PORT`      | Bind port                          | `8000`    |
| `WORKERS`   | Number of uvicorn workers          | `1`       |
| `LOG_LEVEL`  | Logging level                      | `info`    |

## Usage

### Schedule a wait timer

Send a POST request to `/api/v1/mcp` with the `schedule_wait` tool:

```json
POST /api/v1/mcp
{
    "method": "tools/call",
    "params": {
        "name": "schedule_wait",
        "arguments": {
            "duration": {
                "seconds": 30
            },
            "callback_action": "notify_user"
        }
    }
}
```

Response:

```json
{
    "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "pending",
    "duration_seconds": 30,
    "scheduled_at": "2024-01-15T10:30:00+00:00",
    "status_url": "/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message": "Timer scheduled for 30s. Job ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Combined duration example

```json
{
    "duration": {
        "days": 1,
        "hours": 2,
        "minutes": 30,
        "seconds": 15
    },
    "callback_action": "send_report"
}
```

This schedules a timer for 1 day, 2 hours, 30 minutes, and 15 seconds (95415 seconds total).

### Poll job status

```bash
GET /api/v1/status/{job_id}
```

Response:

```json
{
    "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "completed",
    "duration_seconds": 30,
    "scheduled_at": "2024-01-15T10:30:00+00:00",
    "completed_at": "2024-01-15T10:30:30+00:00",
    "callback_action": "notify_user",
    "result": "Callback 'notify_user' executed after 30s"
}
```

### List all jobs

```bash
GET /api/v1/jobs
```

### Cancel a job

```bash
DELETE /api/v1/status/{job_id}
```

### Health check

```bash
GET /api/v1/health
```

### MCP Manifest

```bash
GET /api/v1/manifest
```

## API Reference

| Method | Path                | Description                    |
|--------|---------------------|--------------------------------|
| GET    | `/api/v1/health`    | Health check                   |
| GET    | `/api/v1/manifest`  | MCP service manifest           |
| POST   | `/api/v1/mcp`       | MCP tool invocation            |
| GET    | `/api/v1/status/{id}`| Get job status                |
| GET    | `/api/v1/jobs`      | List all jobs                  |
| DELETE | `/api/v1/status/{id}`| Cancel a job                  |

## MCP Tool: schedule_wait

### Input Schema

```json
{
    "type": "object",
    "properties": {
        "duration": {
            "type": "object",
            "properties": {
                "seconds": { "type": "integer", "minimum": 0 },
                "minutes": { "type": "integer", "minimum": 0 },
                "hours": { "type": "integer", "minimum": 0 },
                "days": { "type": "integer", "minimum": 0 }
            }
        },
        "callback_action": { "type": "string" }
    },
    "required": ["duration"]
}
```

At least one duration field must be provided and non-zero. Maximum duration is 1 year.

## Development

### Run tests

```bash
pip install -e ".[dev]"
pytest
```

### Run with debug logging

```bash
LOG_LEVEL=debug uvicorn timer_mcp.main:app --reload
```

### Docker build

```bash
docker build -t timer-mcp:latest .
```

## Architecture

```
timer-mcp/
├── src/timer_mcp/
│   ├── __init__.py
│   ├── main.py          # Entry point
│   ├── server.py        # FastAPI app factory
│   ├── models.py        # Pydantic models
│   ├── duration.py      # Duration parsing utilities
│   ├── scheduler.py     # Background job scheduler
│   ├── tools.py         # MCP tool definitions and handlers
│   └── routes.py        # HTTP route handlers
├── tests/
│   ├── test_duration.py  # Duration parsing tests
│   ├── test_scheduler.py # Scheduler tests
│   └── test_tools.py     # Integration tests
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```

## License

MIT
