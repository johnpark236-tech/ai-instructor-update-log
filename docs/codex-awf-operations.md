# Codex AWF pilot operations
Status: pilot ONLY, no automatic merges or production deployments.
Run GitHub Actions > Codex AWF (pilot, no merge) > Run workflow with a narrowly scoped task.
Existing pages.yml, daily-ai-top10.yml, telegram-notify.yml are untouched.
The workflow intentionally fails closed if the Codex CLI or a supported authenticated login is unavailable.
GitHub-hosted runners are ephemeral. A local ChatGPT subscription login is NOT automatically available in Actions; never upload ~/.codex/auth.json as a committed file or artifact. Use an approved, secure credential mechanism before enabling agent execution.
The reviewer uses a fresh read-only CLI process. Its verdict is AI feedback, not an independent GitHub branch-protection approval.
The pipeline runs mandatory lesson-index reconstruction plus JS syntax validation. PPT generation requires npm install --no-save --no-package-lock pptxgenjs@3.12.0 && node scripts/build_downloads.js, and must be incorporated before production merge.
Quota detection records a UTC retry time only; automatic durable checkpoint/restart scheduling is NOT enabled in pilot.
To recover: leave main untouched, inspect awf-results logs, correct the branch, and re-run checks. Never automatically force-push or roll back production.
Production auto-merge requires verified credential strategy, committed changes in a PR, policy check, full download build and independent validation, required CI checks, workflow completion, and Pages deploy status verification.
