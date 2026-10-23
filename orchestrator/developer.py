"""Developer runs as an isolated Codex CLI process."""
import subprocess
from pathlib import Path
def develop(root: Path, prompt: str, timeout=1800):
    command = ["codex", "exec", "--sandbox", "workspace-write", "--skip-git-repo-check", prompt]
    return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=timeout)
