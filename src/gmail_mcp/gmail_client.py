"""Gmail API client with OAuth authentication."""

import base64
import logging
import sys
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging to stderr (critical for STDIO transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Gmail API scope for full access (needed to archive/modify)
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class AuthenticationRequiredError(Exception):
    """Raised when OAuth authentication is required but not available."""

    pass


def get_credentials(
    credentials_path: Path,
    token_path: Path,
    interactive: bool = False,
) -> Credentials:
    """Get valid OAuth credentials.

    For MCP server mode (interactive=False): Only loads cached tokens,
    raises error if authentication is needed.

    For setup mode (interactive=True): Runs browser OAuth flow.

    Args:
        credentials_path: Path to OAuth client secrets JSON.
        token_path: Path to token cache file.
        interactive: If True, allow browser-based OAuth flow.

    Returns:
        Valid Google OAuth credentials.

    Raises:
        AuthenticationRequiredError: If auth needed but not in interactive mode.
        FileNotFoundError: If credentials file doesn't exist.
    """
    creds = None

    # Check for existing cached token
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            logger.info("Loaded cached credentials from %s", token_path)
        except Exception as e:
            logger.warning("Failed to load cached credentials: %s", e)

    # If we have valid credentials, return them
    if creds and creds.valid:
        return creds

    # Try to refresh expired credentials
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds, token_path)
            logger.info("Refreshed expired credentials")
            return creds
        except Exception as e:
            logger.warning("Failed to refresh credentials: %s", e)

    # At this point, we need fresh authentication
    if not interactive:
        raise AuthenticationRequiredError(
            "Gmail authentication required. Run: uvx gmail-mcp --setup"
        )

    # Verify credentials file exists
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"OAuth credentials file not found: {credentials_path}\n"
            "Download it from Google Cloud Console."
        )

    # Interactive browser flow
    logger.info("Starting OAuth flow...")
    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    creds = flow.run_local_server(port=0)
    _save_token(creds, token_path)
    logger.info("Authentication successful, token saved to %s", token_path)
    return creds


def _save_token(creds: Credentials, token_path: Path) -> None:
    """Save credentials to token file."""
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as token_file:
        token_file.write(creds.to_json())


class GmailClient:
    """Gmail API client for MCP operations."""

    def __init__(self, credentials_path: Path, token_path: Path) -> None:
        """Initialize Gmail client.

        Args:
            credentials_path: Path to OAuth credentials JSON.
            token_path: Path to token cache file.
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._service = None

    @property
    def service(self):
        """Get or create Gmail API service."""
        if self._service is None:
            creds = get_credentials(
                self.credentials_path,
                self.token_path,
                interactive=False,
            )
            self._service = build("gmail", "v1", credentials=creds)
        return self._service

    def list_unread(self, max_results: int = 20) -> list[dict[str, Any]]:
        """List unread emails from inbox.

        Args:
            max_results: Maximum number of emails to return (1-100).

        Returns:
            List of email objects with id, from, subject, date, snippet, labels.
        """
        max_results = min(max(1, max_results), 100)

        try:
            results = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    labelIds=["INBOX", "UNREAD"],
                    maxResults=max_results,
                )
                .execute()
            )

            messages = results.get("messages", [])
            if not messages:
                return []

            return [self._get_message_details(msg["id"]) for msg in messages]

        except HttpError as error:
            logger.error("Gmail API error listing messages: %s", error)
            raise

    def search(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Search emails using Gmail query syntax.

        Args:
            query: Gmail search query (e.g., "from:user@example.com is:unread").
            max_results: Maximum number of results (1-100).

        Returns:
            List of email objects matching the query.
        """
        max_results = min(max(1, max_results), 100)

        try:
            results = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    q=query,
                    maxResults=max_results,
                )
                .execute()
            )

            messages = results.get("messages", [])
            if not messages:
                return []

            return [self._get_message_details(msg["id"]) for msg in messages]

        except HttpError as error:
            logger.error("Gmail API error searching messages: %s", error)
            raise

    def archive_messages(self, message_ids: list[str]) -> dict[str, Any]:
        """Archive messages by removing INBOX and UNREAD labels.

        Args:
            message_ids: List of message IDs to archive.

        Returns:
            Dict with archived_count, failed_count, and details.
        """
        results = {"archived": [], "failed": []}

        for msg_id in message_ids:
            try:
                self.service.users().messages().modify(
                    userId="me",
                    id=msg_id,
                    body={"removeLabelIds": ["INBOX", "UNREAD"]},
                ).execute()
                results["archived"].append(msg_id)
                logger.info("Archived message: %s", msg_id)
            except HttpError as error:
                results["failed"].append({"id": msg_id, "error": str(error)})
                logger.error("Failed to archive %s: %s", msg_id, error)

        return {
            "archived_count": len(results["archived"]),
            "failed_count": len(results["failed"]),
            "details": results,
        }

    def mark_as_read(self, message_ids: list[str]) -> dict[str, Any]:
        """Mark messages as read without archiving.

        Args:
            message_ids: List of message IDs to mark as read.

        Returns:
            Dict with marked_count, failed_count, and details.
        """
        results = {"marked": [], "failed": []}

        for msg_id in message_ids:
            try:
                self.service.users().messages().modify(
                    userId="me",
                    id=msg_id,
                    body={"removeLabelIds": ["UNREAD"]},
                ).execute()
                results["marked"].append(msg_id)
                logger.info("Marked as read: %s", msg_id)
            except HttpError as error:
                results["failed"].append({"id": msg_id, "error": str(error)})
                logger.error("Failed to mark as read %s: %s", msg_id, error)

        return {
            "marked_count": len(results["marked"]),
            "failed_count": len(results["failed"]),
            "details": results,
        }

    def get_labels(self) -> list[dict[str, Any]]:
        """Get all Gmail labels for the authenticated user.

        Returns:
            List of label objects with id, name, type, and counts.
        """
        try:
            results = self.service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])

            return [
                {
                    "id": label["id"],
                    "name": label["name"],
                    "type": label.get("type", "user"),
                    "messages_total": label.get("messagesTotal"),
                    "messages_unread": label.get("messagesUnread"),
                    "threads_total": label.get("threadsTotal"),
                    "threads_unread": label.get("threadsUnread"),
                }
                for label in labels
            ]

        except HttpError as error:
            logger.error("Gmail API error getting labels: %s", error)
            raise

    def _get_message_details(self, message_id: str) -> dict[str, Any]:
        """Get full details for a message.

        Args:
            message_id: The message ID.

        Returns:
            Dict with message details.
        """
        message = (
            self.service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        headers = message.get("payload", {}).get("headers", [])

        date_str = self._get_header(headers, "Date")
        try:
            parsed_date = parsedate_to_datetime(date_str)
            date_str = parsed_date.strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass

        return {
            "id": message_id,
            "thread_id": message.get("threadId"),
            "from": self._get_header(headers, "From"),
            "to": self._get_header(headers, "To"),
            "subject": self._get_header(headers, "Subject"),
            "date": date_str,
            "snippet": message.get("snippet", ""),
            "labels": message.get("labelIds", []),
            "body_preview": self._get_message_body(message.get("payload", {}))[:2000],
        }

    def _get_header(self, headers: list[dict], name: str) -> str:
        """Get header value by name (case-insensitive)."""
        for header in headers:
            if header["name"].lower() == name.lower():
                return header["value"]
        return ""

    def _get_message_body(self, payload: dict) -> str:
        """Extract body text from message payload."""
        body = ""

        if "body" in payload and payload["body"].get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                "utf-8", errors="replace"
            )
        elif "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                if mime_type == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8", errors="replace"
                    )
                    break
                elif (
                    mime_type == "text/html"
                    and not body
                    and part.get("body", {}).get("data")
                ):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8", errors="replace"
                    )
                elif "parts" in part:
                    nested_body = self._get_message_body(part)
                    if nested_body:
                        body = nested_body
                        break

        return body[:5000]
