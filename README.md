# Gmail MCP Server

A Model Context Protocol (MCP) server that provides Gmail access for Claude Code and other MCP
clients. Built with FastMCP.

## Features

- **list_unread** - List unread emails from inbox
- **search** - Search emails using Gmail query syntax
- **archive** - Archive emails (removes from inbox)
- **mark_as_read** - Mark emails as read without archiving
- **get_labels** - Get all Gmail labels

## Installation

### Using uvx (recommended)

```bash
uvx gmail-mcp
```

### Using pip

```bash
pip install gmail-mcp
```

## Setup

### 1. Create Google Cloud OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the JSON file
5. Configure OAuth consent screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Add your email as a test user (required for testing)

### 2. Set Environment Variables

Set the path to your OAuth credentials file:

```bash
export GMAIL_MCP_CREDENTIALS_PATH="/path/to/your/credentials.json"
```

Optionally, customize the token cache location (default: `~/.config/gmail-mcp/token.json`):

```bash
export GMAIL_MCP_TOKEN_PATH="/custom/path/token.json"
```

### 3. Run OAuth Setup

Run the interactive setup to authenticate:

```bash
uvx gmail-mcp --setup
```

This will open a browser window for Google OAuth authentication. After authorizing, the token
will be cached for future use.

## MCP Client Configuration

### Claude Code

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uvx",
      "args": ["gmail-mcp"],
      "env": {
        "GMAIL_MCP_CREDENTIALS_PATH": "/path/to/your/credentials.json"
      }
    }
  }
}
```

### With Custom Token Path

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uvx",
      "args": ["gmail-mcp"],
      "env": {
        "GMAIL_MCP_CREDENTIALS_PATH": "/path/to/your/credentials.json",
        "GMAIL_MCP_TOKEN_PATH": "/custom/path/token.json"
      }
    }
  }
}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GMAIL_MCP_CREDENTIALS_PATH` | Yes | - | Path to OAuth credentials JSON |
| `GMAIL_MCP_TOKEN_PATH` | No | `~/.config/gmail-mcp/token.json` | Path to token cache file |

## Tool Reference

### list_unread

List unread emails from inbox.

**Parameters:**
- `max_results` (int, optional): Maximum emails to return (1-100). Default: 20.

**Returns:** List of email objects with id, from, subject, date, snippet, labels, body_preview.

### search

Search emails using Gmail query syntax.

**Parameters:**
- `query` (str): Gmail search query (e.g., "from:user@example.com is:unread")
- `max_results` (int, optional): Maximum results (1-100). Default: 20.

**Returns:** List of matching email objects.

**Example queries:**
- `from:notifications@github.com` - Emails from GitHub
- `is:unread newer_than:1d` - Unread emails from last 24 hours
- `subject:invoice` - Emails with "invoice" in subject
- `has:attachment larger:5M` - Emails with attachments over 5MB

### archive

Archive emails by removing INBOX and UNREAD labels.

**Parameters:**
- `message_ids` (list[str]): List of message IDs to archive.

**Returns:** Dict with `archived_count`, `failed_count`, and `details`.

### mark_as_read

Mark emails as read without archiving.

**Parameters:**
- `message_ids` (list[str]): List of message IDs to mark as read.

**Returns:** Dict with `marked_count`, `failed_count`, and `details`.

### get_labels

Get all Gmail labels for the authenticated user.

**Returns:** List of label objects with id, name, type, and message counts.

## Development

### Prerequisites

- Python 3.13+
- Nix (optional, for reproducible environment)

### Setup with Nix

```bash
cd gmail-mcp
nix develop
```

### Setup with pip

```bash
cd gmail-mcp
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
ruff format .
```

## License

MIT
