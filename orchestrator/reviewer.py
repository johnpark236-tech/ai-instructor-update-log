"""Fresh, read-only Codex reviewer with machine-readable output."""
import json
import subprocess
import tempfile
from pathlib import Path

def review(root:Path, request:str, diff:str, test_log:str, timeout=1200):
    schema=root/"orchestrator"/"review-schema.json"
    prompt=("INDEPENDENT REVIEW: disregard developer claims. "
            "Read actual changed files and compare the task, diff and executed tests. "
            "Reject unsafe changes, unknown source facts, broken references, "
            "missing evidence, failing tests. Do NOT modify anything. "
            "Output only the schema-defined verdict with reasons and fixes.\n"
            f"TASK:\n{request[:12000]}\nDIFF:\n{diff[:45000]}\nTESTS:\n{test_log[-14000:]}")
    with tempfile.TemporaryDirectory(prefix="codex-review-") as temp:
        out=Path(temp)/"review.json"
        cmd=["codex","exec","--sandbox","read-only","--skip-git-repo-check",
             "--output-schema",str(schema),"--output-last-message",str(out),prompt]
        p=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=timeout)
        if p.returncode or not out.exists():
            raise RuntimeError("Reviewer CLI failed or output missing (fail closed)")
        try: verdict=json.loads(out.read_text(encoding="utf-8"))
        except (OSError,ValueError) as e: raise RuntimeError("Reviewer JSON invalid") from e
        if verdict.get("verdict") not in ("APPROVE","REJECT"):
            raise RuntimeError("Reviewer verdict invalid")
        return verdict
