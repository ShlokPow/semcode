# semcode

[![ci](https://github.com/ShlokPow/semcode/actions/workflows/ci.yml/badge.svg)](https://github.com/ShlokPow/semcode/actions/workflows/ci.yml)

Hybrid semantic + keyword code search over Python/JS/TS repos, exposed to Claude Code as an MCP
server. Design and phase plan: [`SPEC.md`](SPEC.md).

## Local setup

Requires Docker and [uv](https://docs.astral.sh/uv/).

```sh
docker compose up -d        # Postgres 16 + pgvector
uv run semcode db init      # apply migrations
uv run pytest
```
