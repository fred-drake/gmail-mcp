"""Gmail MCP Server using FastMCP."""

import argparse
import sys
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from .config import Config
from .gmail_client import (
    AuthenticationRequiredError,
    GmailClient,
    get_credentials,
)

# Global client instance (set during lifespan)
_client: GmailClient | None = None


@asynccontextmanager
async def lifespan(mcp: FastMCP):
    """Initialize Gmail client on server startup."""
    global _client
    config = Config.from_environment()
    _client = GmailClient(config.credentials_path, config.token_path)
    yield
    _client = None


mcp = FastMCP(
    "Gmail MCP Server",
    lifespan=lifespan,
)


@mcp.tool()
def list_unread(max_results: int = 20) -> list[dict[str, Any]]:
    """List unread emails from inbox.

    Args:
        max_results: Maximum number of emails to return (1-100). Default: 20.

    Returns:
        List of email objects with id, from, subject, date, snippet, labels, body_preview.
    """
    if _client is None:
        raise RuntimeError("Gmail client not initialized")
    return _client.list_unread(max_results)


@mcp.tool()
def search(query: str, max_results: int = 20) -> list[dict[str, Any]]:
    """Search emails using Gmail query syntax.

    Args:
        query: Gmail search query (e.g., "from:user@example.com is:unread",
               "subject:invoice", "newer_than:1d").
        max_results: Maximum number of results (1-100). Default: 20.

    Returns:
        List of email objects matching the query.
    """
    if _client is None:
        raise RuntimeError("Gmail client not initialized")
    return _client.search(query, max_results)


@mcp.tool()
def archive(message_ids: list[str]) -> dict[str, Any]:
    """Archive emails by removing INBOX and UNREAD labels.

    Args:
        message_ids: List of message IDs to archive.

    Returns:
        Dict with archived_count, failed_count, and details.
    """
    if _client is None:
        raise RuntimeError("Gmail client not initialized")
    return _client.archive_messages(message_ids)


@mcp.tool()
def mark_as_read(message_ids: list[str]) -> dict[str, Any]:
    """Mark emails as read without archiving.

    Args:
        message_ids: List of message IDs to mark as read.

    Returns:
        Dict with marked_count, failed_count, and details.
    """
    if _client is None:
        raise RuntimeError("Gmail client not initialized")
    return _client.mark_as_read(message_ids)


@mcp.tool()
def get_labels() -> list[dict[str, Any]]:
    """Get all Gmail labels for the authenticated user.

    Returns:
        List of label objects with id, name, type, and message counts.
    """
    if _client is None:
        raise RuntimeError("Gmail client not initialized")
    return _client.get_labels()


def run_setup() -> None:
    """Run interactive OAuth setup flow."""
    print("Gmail MCP Server - OAuth Setup", file=sys.stderr)
    print("=" * 40, file=sys.stderr)

    config = Config.from_environment()

    print(f"\nCredentials file: {config.credentials_path}", file=sys.stderr)
    print(f"Token will be saved to: {config.token_path}", file=sys.stderr)

    try:
        creds = get_credentials(
            config.credentials_path,
            config.token_path,
            interactive=True,
        )
        print("\nAuthentication successful!", file=sys.stderr)
        print(f"Token saved to: {config.token_path}", file=sys.stderr)
        print("\nYou can now use the Gmail MCP server.", file=sys.stderr)
    except FileNotFoundError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nAuthentication failed: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the Gmail MCP server."""
    parser = argparse.ArgumentParser(
        description="Gmail MCP Server - Access Gmail from MCP clients"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run interactive OAuth setup flow",
    )
    args = parser.parse_args()

    if args.setup:
        run_setup()
    else:
        try:
            mcp.run()
        except AuthenticationRequiredError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
