# second-brain

## Installation

1. Clone the repository.
2. Install dependencies:

```bash
uv sync
```

## Usage

```bash
uv run second_brain                          # via the CLI entrypoint
uv run --env-file .env second_brain          # with the dev environment
uv run python -m second_brain                # as a Python module
```

## Environment Variables

`.env.example` is the template — copy it to `.env` for development:

```bash
cp .env.example .env
```

- `LOG_LEVEL` — console log level (default: `INFO`; set to `DEBUG` in `.env` for verbose console output)
- `LOG_FILE` — path to the log file (default: `app.log`)

`uv run --env-file .env` loads the dev environment explicitly (no auto-loading).

## Testing

```bash
uv run pytest              # run tests
uv run pytest --cov        # run tests with coverage
```

## Documentation

```bash
uv run python scripts/serve_docs.py    # preview docs locally
uv run mkdocs build                    # build static docs
```
