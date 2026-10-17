# FEMI Public Controller

Lightweight Telegram polling for StoryKnot. This public repository contains no private production code or credentials. GitHub Actions secrets must hold `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and `PRIVATE_REPO_DISPATCH_TOKEN` (fine-grained token with Actions write access to `Ajibola19/Femi-GitHub-Actions`).

The poller runs every five minutes, forwards only messages from the authorized Telegram chat to the private repository using `repository_dispatch`, and sends slot reminders to the private worker. Update offsets only after the private dispatch is accepted. Do **not** activate until the private receiver is installed and the prior webhook/controller is disabled.
