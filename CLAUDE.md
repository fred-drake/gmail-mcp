# Gmail MCP Server - Development Context

## Project Overview

This is a Model Context Protocol (MCP) server that provides Gmail access to Claude Code and other
MCP clients. It uses FastMCP for the server framework and the Google Gmail API for email operations.

## Architecture

```
src/gmail_mcp/
├── __init__.py       # Package version
├── server.py         # FastMCP server, tool definitions, CLI entry point
├── gmail_client.py   # Gmail API wrapper with OAuth authentication
└── config.py         # Environment variable configuration
```

### Key Components

- **server.py**: FastMCP server with lifespan context for client initialization. Defines 5 tools:
  `list_unread`, `search`, `archive`, `mark_as_read`, `get_labels`. CLI supports `--setup` flag.

- **gmail_client.py**: `GmailClient` class wrapping Google Gmail API. Handles OAuth token caching
  and refresh. `get_credentials()` supports both interactive (browser) and non-interactive modes.

- **config.py**: `Config` dataclass with `from_environment()` factory method. Required:
  `GMAIL_MCP_CREDENTIALS_PATH`. Optional: `GMAIL_MCP_TOKEN_PATH` (defaults to
  `~/.config/gmail-mcp/token.json`).

## Critical Implementation Notes

### STDIO Transport

MCP servers use STDIO transport. **Never write to stdout** - all logging must go to stderr:

```python
import logging
import sys

logging.basicConfig(stream=sys.stderr, ...)
print("message", file=sys.stderr)  # For user messages
```

### OAuth Scope

Uses `https://www.googleapis.com/auth/gmail.modify` scope, which allows reading and modifying
emails but not deleting permanently.

### Archive Behavior

Archiving removes both `INBOX` and `UNREAD` labels to ensure emails leave inbox and don't
reappear as unread.

### Token Refresh

Tokens are automatically refreshed when expired. The server handles this transparently without
user interaction.

## Development Commands

```bash
# Enter dev shell (Nix)
nix develop

# Install in dev mode (pip)
pip install -e ".[dev]"

# Run OAuth setup
uvx gmail-mcp --setup
# or
python -m gmail_mcp.server --setup

# Run tests
pytest

# Run tests with coverage
pytest --cov=gmail_mcp

# Lint
ruff check .
ruff format .
```

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `GMAIL_MCP_CREDENTIALS_PATH` | Yes | - |
| `GMAIL_MCP_TOKEN_PATH` | No | `~/.config/gmail-mcp/token.json` |

## Testing Locally

1. Set up OAuth credentials in Google Cloud Console
2. Export `GMAIL_MCP_CREDENTIALS_PATH`
3. Run `uvx gmail-mcp --setup` to authenticate
4. Add server to Claude Code MCP config
5. Restart Claude Code

## Common Issues

### "Authentication required" error

Run `uvx gmail-mcp --setup` to complete OAuth flow.

### "Credentials file not found" error

Ensure `GMAIL_MCP_CREDENTIALS_PATH` points to valid OAuth credentials JSON downloaded from
Google Cloud Console.

### Emails not appearing in inbox after archive

This is expected - archive removes the `INBOX` label. Search for them with
`search(query="label:all")` or find them in Gmail's "All Mail".

### Token refresh fails

Delete the token file (default: `~/.config/gmail-mcp/token.json`) and re-run setup.

## Publishing

```bash
# Build
uv build

# Publish to PyPI (requires credentials)
uv publish
```
