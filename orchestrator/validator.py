"""Fail-closed scope and content validation."""
import json
import re
import subprocess
from pathlib import Path
def shell(root, command, timeout=600):
    return subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout)
def changed(root, base="origin/main"):
    p = shell(root, ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", base])
    if p.returncode: raise RuntimeError(p.stderr)
    return [x for x in p.stdout.splitlines() if x]
def scope(paths):
    blocked = ("orchestrator/", ".github/workflows/", "AGENTS.md")
    if any(x.startswith(blocked) or x in ("index.html",) for x in paths):
        return False, "Protected infrastructure/site files require manual review"
    if any(x.endswith(".json") and not (x.startswith("lessons/") or x in ("lessons.json","releases.json","ai-daily.json")) for x in paths):
        return False, "Unexpected JSON path"
    return True, "OK"
def validate(root: Path):
    logs=[]
    for cmd in (["python", "scripts/build_lessons_index.py"],
                ["node", "--check", "scripts/build_downloads.js"]):
        p=shell(root,cmd,timeout=600)
        logs.append("$ "+" ".join(cmd)+"\n"+p.stdout+"\n"+p.stderr)
        if p.returncode: return False, "\n".join(logs)
    for name in ("ai-daily.json","lessons.json","releases.json"):
        try: json.loads((root/name).read_text(encoding="utf-8-sig"))
        except (OSError,ValueError) as exc: return False, name+": "+str(exc)
    return True,"\n".join(logs)
