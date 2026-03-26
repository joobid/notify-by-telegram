---
name: telegram-notify
description: Send a notification to the user's Telegram when a task finishes. Trigger this skill whenever the user says "notifícame por Telegram", "avísame por Telegram", "mándame un Telegram", "notify me on Telegram", "send me a Telegram", "Telegram notification", or any variation asking to be notified or alerted via Telegram when something completes. Also trigger when the user includes "Telegram" in the context of task completion, results delivery, or status updates.
---

# Telegram Notification Skill

When this skill is triggered, send a notification to the user's Telegram using the `notify.py` script after completing the current task.

## How to use

At the **end** of whatever task you are performing, use the `mcp__Control_your_Mac__osascript` tool to run the script **on the host Mac** (not via Bash, which runs inside the sandboxed VM and cannot reach the Telegram API).

Call the tool like this:

```
Tool: mcp__Control_your_Mac__osascript
Script: do shell script "/usr/bin/python3 /Users/<you>/claude/notify-by-telegram/notify.py --title '<TASK_TITLE>' '<RESULT_SUMMARY>'"
```

Where:
- `<TASK_TITLE>` is a short label describing the task (2-5 words)
- `<RESULT_SUMMARY>` is a one-line summary of the outcome or result

## Critical rules

- **ALWAYS use `mcp__Control_your_Mac__osascript`**, never Bash. The Cowork VM sandbox blocks outbound HTTPS to Telegram. The osascript tool runs on the real Mac where network access and certificates work.
- **NEVER ask the user for credentials, tokens, chat IDs, or any configuration.** Everything is already configured in `/Users/<you>/claude/notify-by-telegram/.env`. The script reads it automatically.
- Always run the notification as the **last step**, after the task is fully complete.
- Keep the title short and the summary concise (one sentence max).
- If the task failed or had errors, still notify but mention the failure in the summary.
- Do not ask the user for confirmation before sending — they already requested the notification.
- Use single quotes around the arguments to avoid shell escaping issues. If the summary contains single quotes, escape them as `'"'"'`.
- Do NOT try to read the `.env` file or inspect the credentials.

## Examples

After generating a report:
```
Tool: mcp__Control_your_Mac__osascript
Script: do shell script "/usr/bin/python3 /Users/<you>/claude/notify-by-telegram/notify.py --title 'Report Ready' 'Your Q1 sales report has been generated and saved.'"
```

After a scheduled task completes:
```
Tool: mcp__Control_your_Mac__osascript
Script: do shell script "/usr/bin/python3 /Users/<you>/claude/notify-by-telegram/notify.py --title 'Daily Summary' 'Processed 142 emails, 3 flagged for review.'"
```

After a task fails:
```
Tool: mcp__Control_your_Mac__osascript
Script: do shell script "/usr/bin/python3 /Users/<you>/claude/notify-by-telegram/notify.py --title 'Task Failed' 'Could not connect to the database. Check credentials.'"
```
