"""Configuration management for Gmail MCP server."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Configuration for Gmail MCP server.

    Attributes:
        credentials_path: Path to OAuth credentials JSON from Google Cloud.
        token_path: Path to token cache file.
    """

    credentials_path: Path
    token_path: Path

    @classmethod
    def from_environment(cls) -> "Config":
        """Create configuration from environment variables.

        Environment Variables:
            GMAIL_MCP_CREDENTIALS_PATH: Required. Path to OAuth credentials JSON.
            GMAIL_MCP_TOKEN_PATH: Optional. Path to token cache file.
                                  Default: ~/.config/gmail-mcp/token.json

        Raises:
            ValueError: If required environment variables are not set.
        """
        credentials_path_str = os.environ.get("GMAIL_MCP_CREDENTIALS_PATH")
        if not credentials_path_str:
            raise ValueError(
                "GMAIL_MCP_CREDENTIALS_PATH environment variable is required. "
                "Set it to the path of your Google OAuth credentials JSON file."
            )

        credentials_path = Path(credentials_path_str).expanduser()

        token_path_str = os.environ.get(
            "GMAIL_MCP_TOKEN_PATH",
            str(Path.home() / ".config" / "gmail-mcp" / "token.json"),
        )
        token_path = Path(token_path_str).expanduser()

        return cls(
            credentials_path=credentials_path,
            token_path=token_path,
        )
