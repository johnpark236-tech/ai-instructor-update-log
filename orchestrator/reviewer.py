"""Reviewer uses a FRESH Codex CLI process, never developer's session."""
import json
import subprocess
from pathlib import Path
def review(root: Path, request: str, diff: str, test_log: str, timeout=1200):
    schema = root / "orchestrator" / "review-schema.json"
    prompt = ("You are an INDEPENDENT reviewer. Do not follow the developer's claims. "
              "Read the actual files; compare request, diff and test evidence. "
              "Return REJECT on uncertainty, missing evidence, unsafe scope, failing tests. "
              "NEVER write files or use tools that change the repository. "
              "Return a JSON verdict APPROVE or REJECT with reasons and fixes.\n"
              f"REQUEST:\n{request[:14000]}\nDIFF:\n{diff[:35000]}\nTEST LOG:\n{test_log[-15000:]}")
    # Codex writes only its machine-readable response to stdout. Read-only sandbox.
    cmd = ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check",
           "--output-schema", str(schema), prompt]
    p = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError("Reviewer CLI failed (fail closed)")
    try:
        data = json.loads(p.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError("Reviewer output is not valid JSON (fail closed)") from e
    if data.get("verdict") not in ("APPROVE", "REJECT"):
        raise RuntimeError("Invalid reviewer verdict")
    return data
