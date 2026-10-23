# AI Instructor Codex rules
- Preserve existing lessons, IDs, categories, source evidence, releases, Pages, and download formats.
- Respect docs/lesson-standard-v2.md. Never invent official releases, prices, Korean availability, URLs, or dates.
- Do not run paid API services or request new credentials.
- Do not modify orchestrator/, .github/, AGENTS.md, or existing HTML without explicit human approval.
- Run python scripts/build_lessons_index.py; check PPT/prompt build with scripts/build_downloads.js.
- Developer must not claim reviewer approval. Reviewer runs in a separate read-only Codex process.
- Never commit tokens, authentication stores, logs with secrets, or private data.
