"""Guard automatic merge; actual Pages result is checked separately."""
import subprocess
def merge_if_enabled(pr, sha, enabled=False):
    if not enabled:
        return {"merged": False, "reason": "Pilot mode: automatic merge disabled"}
    p=subprocess.run(["gh","pr","merge",str(pr),"--squash","--match-head-commit",sha],
                     capture_output=True,text=True)
    if p.returncode: raise RuntimeError("Merge failed: "+p.stderr[-600:])
    return {"merged":True,"reason":"GitHub merge command succeeded; Pages verification pending"}
def pages_status(root_url, timeout=15):
    import urllib.request
    try:
        with urllib.request.urlopen(root_url, timeout=timeout) as res:
            return res.status==200
    except Exception:
        return False
