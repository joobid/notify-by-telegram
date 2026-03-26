#!/usr/bin/env python3
"""
notify-by-telegram: Send notifications to Telegram from Claude Cowork.

Usage:
    python notify.py "Your message here"
    python notify.py --markdown "**Bold** and _italic_ message"
    echo "Piped message" | python notify.py
    python notify.py --title "Task Done" "The report is ready"
    python notify.py --topic 123 "Message to a specific topic"
"""

import argparse
import os
import ssl
import subprocess
import sys
import tempfile
import urllib.request
import urllib.parse
import json
from pathlib import Path


def load_env(env_path: Path) -> None:
    """Load variables from a .env file into os.environ."""
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                os.environ.setdefault(key, value)


def get_config() -> tuple[str, str, str | None]:
    """Resolve bot token, chat ID, and optional topic ID from .env or environment."""
    env_file = Path(__file__).parent / ".env"
    load_env(env_file)

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    topic_id = os.environ.get("TELEGRAM_TOPIC_ID")

    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set.", file=sys.stderr)
        print("Set it in .env or as an environment variable.", file=sys.stderr)
        sys.exit(1)

    if not chat_id:
        print("Error: TELEGRAM_CHAT_ID not set.", file=sys.stderr)
        print("Set it in .env or as an environment variable.", file=sys.stderr)
        sys.exit(1)

    # Normalize chat ID: if topic is set, it's a supergroup — ensure -100 prefix
    if chat_id and not chat_id.startswith("-"):
        chat_id = f"-100{chat_id}"
    elif chat_id and chat_id.startswith("-") and not chat_id.startswith("-100"):
        chat_id = f"-100{chat_id.lstrip('-')}"

    return token, chat_id, topic_id


def _build_ssl_context() -> ssl.SSLContext:
    """Build an SSL context that trusts macOS system & corporate certificates."""
    # If SSL_CERT_FILE is already set, use the default context
    if os.environ.get("SSL_CERT_FILE"):
        return ssl.create_default_context()

    # Try to export macOS system certs (includes corporate proxy CAs)
    keychains = [
        "/Library/Keychains/System.keychain",
        "/System/Library/Keychains/SystemRootCertificates.keychain",
    ]
    pem_blocks: list[str] = []
    for kc in keychains:
        if not Path(kc).exists():
            continue
        try:
            result = subprocess.run(
                ["security", "find-certificate", "-a", "-p", kc],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                pem_blocks.append(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    if pem_blocks:
        combined = "\n".join(pem_blocks)
        tmp = tempfile.NamedTemporaryFile(suffix=".pem", delete=False, mode="w")
        tmp.write(combined)
        tmp.close()
        ctx = ssl.create_default_context(cafile=tmp.name)
        os.unlink(tmp.name)
        return ctx

    # Fallback: default context
    return ssl.create_default_context()


def send_message(
    token: str,
    chat_id: str,
    text: str,
    parse_mode: str = "MarkdownV2",
    silent: bool = False,
    topic_id: str | None = None,
) -> dict:
    """Send a message via Telegram Bot API using only stdlib."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_notification": silent,
    }

    if topic_id:
        payload["message_thread_id"] = int(topic_id)

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )

    ctx = _build_ssl_context()

    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Telegram API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special = r"_*[]()~`>#+-=|{}.!\\"
    escaped = []
    for ch in text:
        if ch in special:
            escaped.append(f"\\{ch}")
        else:
            escaped.append(ch)
    return "".join(escaped)


def format_message(text: str, title: str | None = None, raw_markdown: bool = False) -> str:
    """Format the notification message."""
    if raw_markdown:
        return text

    escaped_text = escape_markdown_v2(text)

    if title:
        escaped_title = escape_markdown_v2(title)
        return f"*{escaped_title}*\n\n{escaped_text}"

    return escaped_text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a notification to Telegram from Claude Cowork.",
        epilog="Examples:\n"
               "  python notify.py 'Task completed'\n"
               "  python notify.py --title 'Report' 'Your report is ready'\n"
               "  python notify.py --markdown '**Done**: all tests passed'\n"
               "  python notify.py --topic 123 'Sent to a specific topic'\n"
               "  echo 'Hello' | python notify.py\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("message", nargs="?", help="Message text to send")
    parser.add_argument("--title", "-t", help="Bold title prepended to the message")
    parser.add_argument(
        "--markdown", action="store_true",
        help="Send raw MarkdownV2 (skip auto-escaping)",
    )
    parser.add_argument(
        "--silent", "-s", action="store_true",
        help="Send without notification sound",
    )
    parser.add_argument(
        "--topic", help="Topic (thread) ID to send to within a group/supergroup",
    )

    args = parser.parse_args()

    # Read from stdin if no message argument
    if args.message:
        text = args.message
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        parser.print_help()
        sys.exit(1)

    if not text:
        print("Error: empty message.", file=sys.stderr)
        sys.exit(1)

    token, chat_id, env_topic_id = get_config()
    topic_id = args.topic or env_topic_id
    formatted = format_message(text, title=args.title, raw_markdown=args.markdown)
    result = send_message(token, chat_id, formatted, silent=args.silent, topic_id=topic_id)

    if result.get("ok"):
        print("Notification sent.")
    else:
        print(f"Unexpected response: {result}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
