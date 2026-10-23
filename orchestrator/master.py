"""Fail-closed Codex developer/reviewer pilot orchestration."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from . import developer, reviewer, validator, quota, dashboard
def git(root,*args):
    p=subprocess.run(["git",*args],cwd=root,text=True,capture_output=True,check=True)
    return p.stdout
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def execute(root, task, out):
    cfg=json.loads((root/"orchestrator/config.json").read_text())
    state={"task":task,"status":"STARTED","round":0,"verdict":"NOT_RUN","pages":"NOT_VERIFIED"}
    save(out,state)
    baseline=git(root,"rev-parse","HEAD").strip()
    git(root,"fetch","origin","main")
    for attempt in range(cfg["max_reworks"]+1):
        state.update(status="DEVELOPING" if attempt==0 else "REWORK",round=attempt)
        save(out,state)
        prompt=task if attempt==0 else task+"\nFix all independent-review defects: "+json.dumps(state["review"].get("fixes",[]),ensure_ascii=False)
        p=developer.develop(root,prompt)
        if quota.exceeded(p.stdout+"\n"+p.stderr):
            state.update(status="QUOTA_WAIT",retry_after=quota.retry_after())
            save(out,state); return 75
        if p.returncode:
            state.update(status="FAILED",reason="Developer CLI failed")
            save(out,state); return 1
        paths=validator.changed(root,baseline)
        # Changes to orchestration/security must never be AI-self-approved.
        ok,why=validator.scope(paths)
        if not ok:
            state.update(status="MANUAL_REVIEW",reason=why)
            save(out,state); return 2
        passed,log=validator.validate(root)
        (out.parent/"tests.log").write_text(log,encoding="utf-8")
        if not passed:
            state.update(status="REWORK",review={"fixes":["Repair mandatory tests: "+log[-2000:]]})
            if attempt==cfg["max_reworks"]: break
            continue
        diff=git(root,"diff",baseline)
        state.update(status="REVIEWING");save(out,state)
        verdict=reviewer.review(root,task,diff,log)
        save(out.parent/f"review-{attempt}.json",verdict)
        state.update(verdict=verdict["verdict"],review=verdict)
        if verdict["verdict"]=="APPROVE":
            state.update(status="APPROVED_PILOT",changed_files=paths,
                         reason="No automatic merge in pilot mode")
            save(out,state)
            return 0
    state.update(status="REJECTED_MAX_REWORKS")
    save(out,state); return 2
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task",required=True)
    ap.add_argument("--out",default="awf-results/state.json")
    args=ap.parse_args()
    root=Path.cwd()
    try: code=execute(root,args.task,root/args.out)
    except (Exception,KeyboardInterrupt) as e:
        save(root/args.out,{"task":args.task,"status":"FAILED","error":str(e)[:500]})
        code=1
    path=root/args.out
    print(dashboard.markdown(json.loads(path.read_text())))
    return code
if __name__=="__main__": sys.exit(main())
