# FEMI Public Controller

A minimal, public, five-minute Telegram polling gateway for StoryKnot. The heavy video worker, owner messages and database live in the private repository `Ajibola19/Femi-GitHub-Actions`.

## Configure before activation

In this public repository, open Settings → Secrets and variables → Actions.

Add three **repository secrets**:
- `TELEGRAM_BOT_TOKEN`: the existing FEMI Telegram bot token.
- `TELEGRAM_CHAT_ID`: the owner's Telegram chat ID.
- `PRIVATE_REPO_DISPATCH_TOKEN`: a fine-grained GitHub personal access token belonging to the repository owner, with access **only** to `Ajibola19/Femi-GitHub-Actions` and repository **Contents: Read and write** permissions. GitHub's repository_dispatch API requires Contents write access. Do not paste the token into committed files.

Add one **repository variable** `FEMI_PUBLIC_ACTIVE` = `false` initially.

## Cutover checklist

1. Verify `.github/workflows/femi-private-receiver.yml` exists in the private worker.
2. Configure the three public secrets. The existing bot webhook cannot be used alongside getUpdates; disable the webhook at cutover without dropping pending messages.
3. Stop the private repo's `femi-github-controller.yml` five-minute schedule so only the public poller reads Telegram. Keep private Shorts, storyboard, image/Wan and long-video schedules enabled.
4. Set `FEMI_PUBLIC_ACTIVE` to `true`, then run the public workflow manually and check the Actions log. Send a test Telegram message and confirm its private dispatch is processed.
5. Check the cursor stored at `state/offset.json`. It tracks update IDs only, never message bodies.

**Notes:** Five-minute schedules can be delayed. Public runner usage is free for standard GitHub-hosted runners under GitHub's normal policies; triggered jobs in the private repository still count toward private minutes. Public repositories expose code and workflow logs, so keep all production data and credentials in secrets and the private worker.
