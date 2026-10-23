"""Fail-closed change-scope and mandatory content validation."""
import json
import subprocess
from pathlib import Path

def shell(root, command, timeout=600):
    return subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout)

def changed(root, base="origin/main"):
    # Intent-to-add exposes new/untracked files to git diff without committing them.
    p=shell(root, ["git","add","-N","."])
    if p.returncode: raise RuntimeError(p.stderr)
    p=shell(root, ["git","diff","--name-only","--diff-filter=ACMRTUXB",base])
    if p.returncode: raise RuntimeError(p.stderr)
    return [x for x in p.stdout.splitlines() if x]

def scope(paths):
    if not paths: return False,"No changed files"
    protected = ("orchestrator/",".github/","AGENTS.md","index.html",
                 "lessons.html","releases.html","lesson-pptx.js","lesson-meta.js")
    if any(x.startswith(protected) for x in paths):
        return False,"Protected infrastructure/site files require manual review"
    allowed = ("lessons/", "ai-daily.json", "lessons.json", "releases.json")
    if any(not (x.startswith("lessons/") and x.endswith(".json") or x in allowed[1:]) for x in paths):
        return False,"Unexpected changed path"
    return True,"OK"

def validate(root:Path):
    logs=[]
    for cmd in (["python","scripts/build_lessons_index.py"],
                ["node","--check","scripts/build_downloads.js"]):
        p=shell(root,cmd,timeout=600)
        logs.append("$ "+" ".join(cmd)+"\n"+p.stdout+"\n"+p.stderr)
        if p.returncode: return False,"\n".join(logs)
    for name in ("ai-daily.json","lessons.json","releases.json"):
        try: json.loads((root/name).read_text(encoding="utf-8-sig"))
        except (OSError,ValueError) as exc: return False,name+": "+str(exc)
    return True,"\n".join(logs)
