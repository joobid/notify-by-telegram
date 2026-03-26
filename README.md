# notify-by-telegram

Send notifications from Claude Cowork to Telegram using the Bot API.

Workaround for when [Claude Code Channels](https://code.claude.com/docs/en/channels) is blocked by your organization's policy. Includes a Cowork skill so you can simply say "notifícame por Telegram" in any conversation.

## Features

- Sends messages to any Telegram chat, group, or topic (thread)
- Supports bold titles, MarkdownV2, and silent mode
- Handles corporate SSL proxies automatically (exports macOS system certificates)
- Normalizes supergroup chat IDs (adds `-100` prefix automatically)
- Includes a Cowork skill for hands-free integration
- Pre-commit hook to prevent credential leaks

## Requirements

Python 3.10+ (no external dependencies — uses only stdlib).

## Setup

### 1. Create a Telegram bot

Open [@BotFather](https://t.me/BotFather) in Telegram, send `/newbot`, and copy the token. For a detailed walkthrough, see the [official Telegram tutorial](https://core.telegram.org/bots/tutorial).

### 2. Get your Chat ID

Send any message to your bot, then open this URL in your browser (replacing `<token>`):

```
https://api.telegram.org/bot<token>/getUpdates
```

Look for `"chat":{"id": 123456789}` — that number is your Chat ID. For groups/supergroups, you can use the raw ID without the `-100` prefix; the script adds it automatically.

### 3. (Optional) Get your Topic ID

If you want to send messages to a specific topic inside a group with topics enabled:

1. Right-click a message inside the topic in Telegram
2. Click "Copy Message Link"
3. The URL looks like `https://t.me/c/CHAT_ID/TOPIC_ID/MSG_ID` — use the `TOPIC_ID` number

### 4. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TELEGRAM_TOPIC_ID=              # optional
```

### 5. Enable credential protection

Activate the pre-commit hook that blocks accidental credential leaks:

```bash
git config core.hooksPath .githooks
```

This prevents committing `.env` files or any content that matches the Telegram bot token format.

### 6. Test it

```bash
python3 notify.py 'Hello from Cowork!'
```

You should receive the message in Telegram.

### 7. Bot permissions for groups

If sending to a group or supergroup:

- The bot must be a **member** of the group
- If the group has **topics enabled**, the bot needs **admin permissions** (you can disable all admin privileges except sending messages)

## Usage (CLI)

```bash
# Simple message
python3 notify.py 'Task completed'

# With a bold title
python3 notify.py --title 'Report' 'Your weekly report is ready'

# Silent (no notification sound)
python3 notify.py --silent 'Background task done'

# Send to a specific topic (overrides .env)
python3 notify.py --topic 123 'Message to a specific topic'

# Pipe from another command
echo 'Deploy finished' | python3 notify.py

# Raw MarkdownV2 (skip auto-escaping)
python3 notify.py --markdown '*Status*: all tests passed'
```

### All options

| Flag | Short | Description |
|------|-------|-------------|
| `--title` | `-t` | Bold title prepended to the message |
| `--silent` | `-s` | Send without notification sound |
| `--topic` | | Topic (thread) ID, overrides `TELEGRAM_TOPIC_ID` from `.env` |
| `--markdown` | | Send raw MarkdownV2 (skip auto-escaping) |

## Claude Cowork integration

### Cowork Skill (recommended)

The project includes a Cowork skill in `skill/SKILL.md`. Once installed, you can add "notifícame por Telegram" (or "notify me on Telegram") to any request and Claude will automatically send you a notification when the task finishes.

**Trigger phrases:** "notifícame por Telegram", "avísame por Telegram", "mándame un Telegram", "notify me on Telegram", "send me a Telegram when done", or any variation.

**Install the skill:**

```bash
mkdir -p ~/.claude/skills/telegram-notify
cp skill/SKILL.md ~/.claude/skills/telegram-notify/SKILL.md
```

After installing, the skill is available globally in all Cowork sessions, regardless of which project or folder you select.

**Example usage in Cowork:**

> "Generate the Q1 sales report and notifícame por Telegram"

Claude will generate the report and then send you a Telegram notification with a summary of the result.

### Scheduled tasks

You can also reference the script directly in Cowork scheduled task prompts:

```
When done, run: python3 /Users/<you>/claude/notify-by-telegram/notify.py --title 'Task Name' 'Result summary'
```

## Corporate proxy / SSL

The script automatically detects and uses macOS system certificates (including corporate proxy CAs). No need to set `SSL_CERT_FILE` manually. If you're not on macOS or prefer to manage certificates yourself, you can still set the environment variable:

```bash
SSL_CERT_FILE=/path/to/certs.pem python3 notify.py 'Hello'
```

## Security

- `.env` is excluded from git via `.gitignore`
- All `.env.*` variants are also excluded (except `.env.example`)
- A pre-commit hook in `.githooks/pre-commit` blocks commits that contain `.env` files or Telegram bot token patterns
- **Never commit your `.env` file.** If you accidentally expose a token, revoke it immediately via [@BotFather](https://t.me/BotFather) with `/revoke`

## Project structure

```
notify-by-telegram/
├── notify.py          # Main script
├── .env.example       # Credential template
├── .env               # Your credentials (gitignored)
├── .gitignore         # Excludes .env and Python caches
├── .githooks/
│   └── pre-commit     # Blocks credential leaks
├── skill/
│   └── SKILL.md       # Cowork skill definition
└── README.md
```
