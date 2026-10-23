#!/usr/bin/env python3
"""Windows/local Codex subscription CLI publisher. No API keys, no Claude, fail closed."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

PROJECT_REPO = "johnpark236-tech/ai-instructor-update-log"
NEWS_REPO = "johnpark236-tech/mannal_news"
AUTOMATION = pathlib.Path(__file__).resolve().parent
HOME = pathlib.Path.home() / ".mannal-codex-hourly"
SCHEMA = AUTOMATION / "review-schema.json"


def run(argv, cwd, *, timeout=90, check=True, input_text=None):
    p = subprocess.run(
        [str(x) for x in argv], cwd=str(cwd), input=input_text, text=True,
        encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f"{argv[0]} failed ({p.returncode}): {p.stderr[-2200:]}")
    return p.stdout.strip()


def git(repo, *args, timeout=90):
    return run(["git", *args], repo, timeout=timeout)


def orig_json(repo, path):
    return json.loads(git(repo, "show", f"HEAD:{path}"))


def current_json(repo, path):
    return json.loads((repo / path).read_text(encoding="utf-8-sig"))


def changed_files(repo):
    tracked = git(repo, "diff", "--name-only").splitlines()
    untracked = git(repo, "ls-files", "--others", "--exclude-standard").splitlines()
    staged = git(repo, "diff", "--cached", "--name-only").splitlines()
    return sorted(set(tracked + untracked + staged))


def preflight(repo, kind, cli):
    if not repo.is_dir() or not (repo / ".git").exists():
        raise RuntimeError(f"Dedicated checkout missing: {repo}")
    expected = NEWS_REPO if kind == "news" else PROJECT_REPO
    remote = git(repo, "remote", "get-url", "origin").lower().removesuffix(".git").rstrip("/")
    if not (remote.endswith("github.com/" + expected.lower()) or
            remote.endswith("github.com:" + expected.lower())):
        raise RuntimeError("Unexpected GitHub remote: " + remote)
    if git(repo, "branch", "--show-current") != "main":
        raise RuntimeError("Only dedicated local 'main' checkout is supported")
    if git(repo, "status", "--porcelain", "-uall"):
        raise RuntimeError("Checkout has local edits. Resolve them before unattended publishing.")
    run([cli, "login", "status"], repo, timeout=30)
    git(repo, "pull", "--ff-only", "origin", "main", timeout=120)
    if git(repo, "status", "--porcelain", "-uall"):
        raise RuntimeError("Checkout is dirty after pull")


def permitted(kind, files, repo):
    if not files:
        return
    for p in files:
        if kind == "news":
            ok = (p == "public/data/ai-news.json" or
                  bool(re.fullmatch(r"public/images/ai-auto-[a-z0-9-]+\.svg", p)))
        else:
            ok = (p in ("lessons.json", "releases.json") or
                  bool(re.fullmatch(r"lessons/AI-\d{4}-\d{2}-CAT\d{2}-\d{3}\.json", p)))
        if not ok:
            raise RuntimeError(f"Unauthorized path change: {p}")
        if not (repo / p).is_file():
            raise RuntimeError(f"Deleted / missing content file: {p}")


def validate_news(repo, files):
    old, new = orig_json(repo, "public/data/ai-news.json"), current_json(repo, "public/data/ai-news.json")
    if not isinstance(old, list) or not isinstance(new, list) or len(new) != len(old) + 1 or new[1:] != old:
        raise RuntimeError("News must prepend exactly one article without changing existing articles")
    x = new[0]
    required = ["id", "slug", "category", "categoryLabel", "title", "subtitle",
                "summary", "content", "author", "publishedAt", "updatedAt",
                "image", "imageAlt", "imageCaption", "tags", "sourceUrl",
                "sourceTitle", "sourcePublishedAt", "isAiGenerated", "isDemo"]
    if any(k not in x or x[k] in ("", None) for k in required):
        raise RuntimeError("Missing required news Article field")
    if x["category"] != "ai" or x["isDemo"] is not False or x["isAiGenerated"] is not True:
        raise RuntimeError("News category or AI attribution missing")
    if not x["id"].startswith("ai-auto-") or x["id"] in {y["id"] for y in old}:
        raise RuntimeError("New article id invalid or duplicated")
    old_urls = {y.get("sourceUrl", "").rstrip("/") for y in old}
    url = x["sourceUrl"]
    if url.rstrip("/") in old_urls or urlparse(url).scheme != "https":
        raise RuntimeError("Repeated source URL or not an HTTPS official source")
    if not isinstance(x["content"], list) or not x["content"]:
        raise RuntimeError("Missing content sections")
    if len(x["content"][0].get("paragraphs", [])) != 3:
        raise RuntimeError("First section must have exactly three summary sentences")
    image = x["image"]
    if not re.fullmatch(r"/images/ai-auto-[a-z0-9-]+\.svg", image):
        raise RuntimeError("Bad SVG image path")
    svg_path = "public" + image
    if svg_path not in files or not (repo / svg_path).is_file():
        raise RuntimeError("Missing newly written SVG image")
    ET.parse(repo / svg_path)
    if len(files) != 2:
        raise RuntimeError("News changed paths must be one JSON and one SVG")
    return x["id"]


def validate_lesson(repo, files):
    old, new = orig_json(repo, "lessons.json"), current_json(repo, "lessons.json")
    a = {x["id"]: x for x in old["lessons"]}
    b = {x["id"]: x for x in new["lessons"]}
    ids = set(b) - set(a)
    if len(ids) != 1 or set(a) - set(b) or any(b[k] != a[k] for k in a):
        raise RuntimeError("Only one new lesson allowed and existing index records must be identical")
    if len(new["lessons"]) != len(old["lessons"]) + 1 or new["count"] != len(new["lessons"]):
        raise RuntimeError("Lesson index count mismatch")
    lesson_id = next(iter(ids))
    f = f"lessons/{lesson_id}.json"
    if f not in files or "releases.json" not in files or "lessons.json" not in files or len(files) != 3:
        raise RuntimeError("Lesson edits must be exactly new JSON + lessons.json + releases.json")
    try:
        git(repo, "cat-file", "-e", f"HEAD:{f}")
    except Exception:
        pass
    else:
        raise RuntimeError("The supposed new lesson already existed in HEAD")
    lesson = current_json(repo, f)
    if lesson.get("id") != lesson_id or len(lesson.get("wrap", {}).get("quiz", [])) != 3:
        raise RuntimeError("Lesson id or exact three questions invalid")
    if not isinstance(lesson.get("verification"), list):
        raise RuntimeError("verification must be an array to avoid loading freeze")
    releases = current_json(repo, "releases.json")["items"]
    if not any(r.get("lesson_id") == lesson_id for r in releases):
        raise RuntimeError("New lesson not linked to release notes")
    old_releases = orig_json(repo, "releases.json")["items"]
    old_map = {v["id"]: v for v in old_releases}
    new_map = {v["id"]: v for v in releases}
    if set(old_map) - set(new_map) or len(new_map) != len(releases):
        raise RuntimeError("Deleted/duplicated existing release notes")
    for k, v in old_map.items():
        if v != new_map[k] and not (
            v.get("lesson_id") is None and new_map[k].get("lesson_id") == lesson_id and
            {a: b for a, b in v.items() if a != "lesson_id"} ==
            {a: b for a, b in new_map[k].items() if a != "lesson_id"}
        ):
            raise RuntimeError("Unrelated release note changed: " + k)
    for new_r in (v for k, v in new_map.items() if k not in old_map):
        if new_r.get("lesson_id") != lesson_id:
            raise RuntimeError("New release item must link to the new lesson")
    run([sys.executable, "scripts/build_lessons_index.py"], repo, timeout=120)
    if git(repo, "diff", "--check"):
        raise RuntimeError("Whitespace diff-check failed")
    if shutil.which("node"):
        run(["node", "tests/quiz_ui.test.cjs"], repo, timeout=120)
    return lesson_id


def codex(cli, repo, prompt, output_file, *, review=False, timeout=2200):
    argv = [
        cli, "exec", "--ephemeral", "--search",
        "--sandbox", "read-only" if review else "workspace-write",
        "--output-last-message", str(output_file),
    ]
    if review:
        argv += ["--output-schema", str(SCHEMA)]
    argv += ["-"]
    output = run(argv, repo, input_text=prompt, timeout=timeout)
    return output


@contextlib.contextmanager
def lock():
    HOME.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (HOME / "hourly.lock").open("a+b") as f:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            if not f.read(1):
                f.write(b"0")
                f.flush()
            f.seek(0)
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise RuntimeError("Another publisher is running; skip overlapping job")
            try:
                yield
            finally:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)


def execute(kind, repo):
    cli = shutil.which("codex")
    if not cli:
        raise RuntimeError("Codex CLI not installed or not in PATH. Run codex login first.")
    preflight(repo, kind, cli)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    session_dir = HOME / f"{kind}-{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)
    prompt_base = (AUTOMATION / "prompts" / f"{kind}.md").read_text(encoding="utf-8")
    reviewer_base = (AUTOMATION / "prompts" / "review.md").read_text(encoding="utf-8")
    feedback = ""
    for attempt in range(1, 4):
        dev_prompt = prompt_base + (
            f"\n\n## {attempt}차 검수 반려사항 — 반드시 수정\n{feedback}\n" if feedback else "")
        codex(cli, repo, dev_prompt, session_dir / f"draft-{attempt}.txt")
        files = changed_files(repo)
        if not files:
            if attempt == 1:
                return {"status": "SKIPPED", "reason": "no new verified source"}
            raise RuntimeError("Rejected draft was not repaired")
        permitted(kind, files, repo)
        try:
            content_id = validate_news(repo, files) if kind == "news" else validate_lesson(repo, files)
        except Exception as exc:
            feedback = str(exc)
            continue
        review_prompt = (
            reviewer_base + f"\n\n검수 작업 유형: {kind}\n새 콘텐츠: {content_id}\n"
            "다음 변경 경로만 검토:\n" + "\n".join(files) +
            "\n모든 변경을 HEAD와 비교하고 공식 출처를 재확인해 엄격하게 승인/반려하라.")
        codex(cli, repo, review_prompt, session_dir / f"review-{attempt}.json",
              review=True, timeout=1500)
        try:
            result = json.loads((session_dir / f"review-{attempt}.json").read_text(encoding="utf-8"))
        except (ValueError, FileNotFoundError) as exc:
            raise RuntimeError("Reviewer did not produce valid JSON") from exc
        if result.get("verdict") != "APPROVE":
            feedback = "\n".join(result.get("reasons", [])) or "Reviewer rejected without reasons"
            continue
        # Revalidate after read-only review in case of unexpected modifications.
        if files != changed_files(repo):
            raise RuntimeError("Files changed during review")
        permitted(kind, files, repo)
        validate_news(repo, files) if kind == "news" else validate_lesson(repo, files)
        run(["git", "diff", "--check"], repo)
        run(["git", "add", "--", *files], repo)
        staged = git(repo, "diff", "--cached", "--name-only").splitlines()
        if sorted(staged) != files:
            raise RuntimeError("Unexpected staged files")
        commit_message = f"content: hourly Codex {kind} {content_id}"
        git(repo, "commit", "-m", commit_message)
        git(repo, "push", "origin", "HEAD:main", timeout=180)
        return {"status": "PUSHED", "id": content_id, "files": files,
                "note": "GitHub push confirmed; GitHub Pages deployment is asynchronous"}
    raise RuntimeError("Codex self-review rejected the content after three attempts")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--kind", choices=["news", "lesson"])
    p.add_argument("--news-repo", type=pathlib.Path)
    p.add_argument("--lesson-repo", type=pathlib.Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        assert SCHEMA.is_file()
        assert all((AUTOMATION / "prompts" / f"{name}.md").is_file()
                   for name in ("news", "lesson", "review"))
        print("CONFIG_OK")
        return
    if not args.kind or not args.news_repo or not args.lesson_repo:
        p.error("--kind, --news-repo and --lesson-repo are required")
    repo = (args.news_repo if args.kind == "news" else args.lesson_repo).resolve()
    started = dt.datetime.now().astimezone().isoformat()
    try:
        with lock():
            result = execute(args.kind, repo)
        result.update({"kind": args.kind, "time": started})
        HOME.mkdir(exist_ok=True, parents=True)
        with (HOME / "runs.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        result = {"status": "FAILED", "kind": args.kind, "time": started, "error": str(exc)}
        HOME.mkdir(exist_ok=True, parents=True)
        with (HOME / "runs.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
