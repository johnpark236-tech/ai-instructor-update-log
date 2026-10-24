#!/usr/bin/env python3
"""Windows/local Codex subscription CLI publisher. No API keys, no Claude, fail closed."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
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
        detail = (p.stderr.strip() or p.stdout.strip() or "No process diagnostics")
        raise RuntimeError(f"{argv[0]} failed ({p.returncode}): {detail[-3500:]}")
    return p.stdout.strip()


def safe_detail(detail):
    """Keep diagnostic useful without logging credential-looking strings."""
    s = str(detail)
    s = re.sub(r"(?i)(?:sk-|gho_|ghp_|ghu_|ghs_|ghr_)[A-Za-z0-9_-]{12,}", "[REDACTED]", s)
    s = re.sub(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{12,}", "Bearer [REDACTED]", s)
    return s[:900]


def progress(kind, phase, **info):
    clean = {k: safe_detail(v) for k, v in info.items()}
    print(json.dumps({"kind": kind, "phase": phase, **clean}, ensure_ascii=False), flush=True)


class CodexQuotaExceeded(RuntimeError):
    """The ChatGPT Codex quota is exhausted; defer this run until the next schedule."""


# Check only recognizable Codex service quota messages, not arbitrary 'limit' words
# in article research, validation feedback or Git errors.
_QUOTA_SIGNATURES = (
    r"(?i)(?:you(?:'ve| have)? (?:hit|reached|exceeded)|your) (?:the )?(?:codex |chatgpt )?(?:usage |rate |weekly |daily )?limit",
    r"(?i)(?:rate[_ -]?limit[_ -]?exceeded|usage[_ -]?limit[_ -]?reached|insufficient[_ -]?quota|quota[_ -]?exceeded)",
    r"(?i)(?:out of|exhausted|no remaining) (?:codex |chatgpt )?(?:credits|usage|quota)",
    r"(?i)(?:codex|chatgpt).{0,45}(?:quota|usage limit).{0,35}(?:reached|exceeded|exhausted)",
    r"(?:Codex|ChatGPT).{0,35}(?:한도|사용량).{0,15}(?:초과|도달|소진)",
    r"(?:사용량|사용|요청)\s*한도(?:에\s*도달|\s*초과|\s*소진)",
    r"(?i)(?:rate limit|usage limit|quota).{0,70}(?:try again|resets?|reset at|upgrade your plan)",
)


def is_codex_quota_error(message):
    value = str(message)
    return any(re.search(pattern, value) for pattern in _QUOTA_SIGNATURES)


def codex_quota_wait(kind, phase, detail):
    """Do not publish drafts made before the quota ran out."""
    progress(kind, "quota_paused", stage=phase, reason="Codex subscription usage limit", next="next hourly scheduled run")
    return {
        "status": "RATE_LIMITED",
        "reason": "ChatGPT Codex subscription quota exhausted",
        "next_action": "Automatically retry at next hourly GitHub Actions schedule",
        "draft_discarded": True,
    }


def generation_result(path, files):
    """A no-op is not evidence that research succeeded."""
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {"status": "FAILED_GENERATION", "reason": "Missing or invalid structured generation report"}
    statuses = {"GENERATED", "SKIPPED_NO_NEWS", "SKIPPED_DUPLICATE", "FAILED_SEARCH",
                "REJECTED_AVAILABILITY", "FAILED_GENERATION"}
    status = result.get("status")
    reason = result.get("reason")
    sources = result.get("sources")
    if status not in statuses or not isinstance(reason, str) or not reason.strip() or not isinstance(sources, list):
        return {"status": "FAILED_GENERATION", "reason": "Invalid generation report fields"}
    if (status == "GENERATED") != bool(files):
        return {"status": "FAILED_GENERATION", "reason": "Generation report disagrees with file changes"}
    if status in {"SKIPPED_NO_NEWS", "SKIPPED_DUPLICATE"} and not sources:
        return {"status": "FAILED_SEARCH", "reason": "No successfully checked official sources recorded"}
    if any(not isinstance(url, str) or urlparse(url).scheme != "https" for url in sources):
        return {"status": "FAILED_GENERATION", "reason": "Invalid research source URLs"}
    return {"status": status, "reason": safe_detail(reason), "sources": sources}


def failure_status(exc):
    text = str(exc).lower()
    if isinstance(exc, CodexQuotaExceeded):
        return "RATE_LIMITED"
    if any(x in text for x in ("unauthorized", "refresh_token", "401", "not logged in", "authentication")):
        return "AUTH_FAILED"
    if isinstance(exc, subprocess.TimeoutExpired):
        return "FAILED_GENERATION"
    return "UNKNOWN_ERROR"


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
    for question in lesson["wrap"]["quiz"]:
        if (not isinstance(question, dict) or len(question.get("options", [])) != 4
                or type(question.get("answer")) is not int or question["answer"] not in range(4)
                or not question.get("explain")):
            raise RuntimeError("Quiz requires four options, answer 0..3 and explanation")
    if not isinstance(lesson.get("verification"), list):
        raise RuntimeError("verification must be an array to avoid loading freeze")
    # Keep new lesson hyperlinks compatible with lessons.html, which reads
    # pricing.sources[].url/title. Never change legacy lesson data here.
    sources = lesson.get("pricing", {}).get("sources", [])
    if not isinstance(sources, list) or any(
        not isinstance(x, dict)
        or not isinstance(x.get("title"), str) or not x["title"].strip()
        or not isinstance(x.get("url"), str)
        or urlparse(x["url"]).scheme not in ("https", "http")
        for x in sources
    ):
        raise RuntimeError("pricing.sources must be [{title, url}] objects, not URL strings")

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


def discard_unverifiable_lesson(repo, files, content_id):
    """Reset ONLY the uncommitted lesson candidate; preserve all existing main data."""
    expected = sorted(["lessons.json", "releases.json", f"lessons/{content_id}.json"])
    if sorted(files) != expected:
        raise RuntimeError("Cannot safely discard candidate with unexpected changed paths")
    candidate = repo / f"lessons/{content_id}.json"
    try:
        git(repo, "cat-file", "-e", f"HEAD:lessons/{content_id}.json")
    except RuntimeError:
        pass
    else:
        raise RuntimeError("Refuse to delete an existing published lesson")
    if not candidate.is_file():
        raise RuntimeError("New lesson file is not present")
    candidate.unlink()
    git(repo, "restore", "--source=HEAD", "--worktree", "--", "lessons.json", "releases.json")
    if changed_files(repo):
        raise RuntimeError("Candidate reset incomplete; stop to avoid modifying unrelated work")


def codex(cli, repo, prompt, output_file, *, review=False, timeout=600):
    argv = [
        cli, "--search", "exec", "--ephemeral",
        "--sandbox", "read-only" if review else "workspace-write",
        "--output-last-message", str(output_file),
    ]
    argv += ["--output-schema", str(SCHEMA if review else AUTOMATION / "generation-schema.json")]
    argv += ["-"]
    try:
        output = run(argv, repo, input_text=prompt, timeout=timeout)
    except RuntimeError as exc:
        if is_codex_quota_error(str(exc)):
            raise CodexQuotaExceeded("Codex subscription usage limit reached") from None
        raise
    # Some CLI versions return code 0 with a human-readable quota notice.
    if output_file.is_file():
        final_message = output_file.read_text(encoding="utf-8", errors="replace")
        if is_codex_quota_error(final_message):
            raise CodexQuotaExceeded("Codex subscription usage limit reached")
    elif is_codex_quota_error(output):
        raise CodexQuotaExceeded("Codex subscription usage limit reached")
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


def execute(kind, repo, *, no_push=False):
    cli = shutil.which("codex")
    if not cli:
        raise RuntimeError("Codex CLI not installed or not in PATH. Run codex login first.")
    preflight(repo, kind, cli)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    session_dir = HOME / f"{kind}-{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)
    prompt_base = (AUTOMATION / "prompts" / f"{kind}.md").read_text(encoding="utf-8")
    reviewer_base = (AUTOMATION / "prompts" / "review.md").read_text(encoding="utf-8")
    feedback = ""
    progress(kind, "start", repo=repo.name)
    last_rejection = "FAILED_GENERATION"
    for attempt in range(1, 4):
        progress(kind, "draft_start", attempt=attempt)
        dev_prompt = prompt_base + (
            f"\n\n## {attempt}차 검수 반려사항 — 반드시 수정\n{feedback}\n"
            "기존 작업 폴더에 이전 차수에 작성한 파일이 남아 있으면 그 파일을 직접 수정하라. "
            "반려되었다는 이유로 검증 가능한 기존 초안까지 삭제하지 말라. "
            "수정 후 git status --short로 변동 확인. 직접 파일을 작성하고 실행을 종료하라.\n"
            if feedback else "")
        try:
            codex(cli, repo, dev_prompt, session_dir / f"draft-{attempt}.txt")
        except CodexQuotaExceeded as exc:
            return codex_quota_wait(kind, "draft", str(exc))
        files = changed_files(repo)
        progress(kind, "draft_result", attempt=attempt, changed=",".join(files) or "(none)")
        report = generation_result(session_dir / f"draft-{attempt}.txt", files)
        progress(kind, "generation_report", attempt=attempt, status=report["status"], reason=report["reason"])
        if report["status"] != "GENERATED":
            # A repair cannot erase a previous rejection by claiming no news.
            if feedback and report["status"].startswith("SKIPPED"):
                return {"status": last_rejection, "reason": safe_detail(feedback), "attempts": attempt}
            return {**report, "attempts": attempt}
        permitted(kind, files, repo)
        if kind == "lesson":
            # Derive lesson index deterministically from validated lesson sources.
            # Codex must write only the new lesson and releases; index is built here.
            try:
                build_output = run([sys.executable, "scripts/build_lessons_index.py"], repo, timeout=150)
                progress(kind, "index_built", attempt=attempt, summary=build_output[-180:])
                files = changed_files(repo)
                permitted(kind, files, repo)
            except Exception as exc:
                feedback = str(exc)
                last_rejection = "REJECTED_SCHEMA"
                progress(kind, "index_rejected", attempt=attempt, reason=feedback)
                continue
        try:
            content_id = validate_news(repo, files) if kind == "news" else validate_lesson(repo, files)
            progress(kind, "schema_pass", attempt=attempt, content_id=content_id)
        except Exception as exc:
            feedback = str(exc)
            last_rejection = "REJECTED_SCHEMA"
            progress(kind, "schema_rejected", attempt=attempt, reason=feedback)
            continue
        reviewed_bytes = {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in files}
        review_prompt = (
            reviewer_base + f"\n\n검수 작업 유형: {kind}\n새 콘텐츠: {content_id}\n"
            "다음 변경 경로만 검토:\n" + "\n".join(files) +
            "\n모든 변경을 HEAD와 비교하고 공식 출처를 재확인해 엄격하게 승인/반려하라. "
            "git diff는 새(untracked) 파일 내용을 표시하지 않을 수 있으므로 "
            "git status --short의 새 파일도 직접 열어 검토하라.")
        try:
            codex(cli, repo, review_prompt, session_dir / f"review-{attempt}.json",
                  review=True, timeout=400)
        except CodexQuotaExceeded as exc:
            return codex_quota_wait(kind, "review", str(exc))
        try:
            result = json.loads((session_dir / f"review-{attempt}.json").read_text(encoding="utf-8"))
        except (ValueError, FileNotFoundError) as exc:
            last_rejection = "FAILED_GENERATION"
            feedback = "검수자가 올바른 JSON 형식으로 승인 또는 반려 사유를 출력하지 못함"
            progress(kind, "review_invalid_output", attempt=attempt, reason=feedback)
            continue
        if result.get("verdict") != "APPROVE":
            last_rejection = "REJECTED_FACT_CHECK"
            feedback = "\n".join(str(x) for x in result.get("reasons", [])) or "Reviewer rejected without reasons"
            progress(kind, "review_rejected", attempt=attempt, reason=feedback)
            # A fundamental lack of Korean rollout/license evidence cannot be
            # fixed by prose. Try a DIFFERENT verified official topic instead.
            region_blocked = any(term in feedback for term in (
                "한국 사용", "국내", "한국 제공", "지역·라이선스", "지역별",
                "country availability", "Korean availability"))
            if kind == "lesson" and region_blocked and attempt < 3:
                rejected = current_json(repo, f"lessons/{content_id}.json")
                rejected_title = rejected.get("title", content_id)
                discard_unverifiable_lesson(repo, files, content_id)
                feedback = (
                    "이전 주제 국내 제공/라이선스 근거 미확인: " + rejected_title +
                    "\n해당 기능으로 다시 작성하지 말고, 공식 문서에서 한국 이용 조건이 "
                    "확인되는 전혀 다른 신규 AI 기능을 찾아라. 적합한 주제 없으면 "
                    "파일 무변경 종료하라. 거부 사유: " + feedback)
                progress(kind, "candidate_replaced", attempt=attempt, old=content_id)
            continue
        progress(kind, "review_approved", attempt=attempt, content_id=content_id)
        # Revalidate after read-only review in case of unexpected modifications.
        if files != changed_files(repo) or reviewed_bytes != {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in files}:
            raise RuntimeError("Files changed during review")
        permitted(kind, files, repo)
        validate_news(repo, files) if kind == "news" else validate_lesson(repo, files)
        run(["git", "diff", "--check"], repo)
        run(["git", "add", "--", *files], repo)
        staged = git(repo, "diff", "--cached", "--name-only").splitlines()
        if sorted(staged) != files:
            raise RuntimeError("Unexpected staged files")
        # CI runners do not have a configured Git author by default.
        # Use an explicit automation identity only for validated content commits.
        git(repo, "config", "user.name", "mannal-codex-bot")
        git(repo, "config", "user.email", "actions@users.noreply.github.com")
        commit_message = f"content: hourly Codex {kind} {content_id}"
        git(repo, "commit", "-m", commit_message)
        progress(kind, "commit_created", content_id=content_id)
        if no_push:
            # GitHub Actions: the token is made available only in a separate
            # trusted push/dispatch step AFTER all Codex invocations finish.
            return {"status": "COMMITTED", "id": content_id, "files": files,
                    "commit": git(repo, "rev-parse", "HEAD"), "attempts": attempt,
                    "note": "Local commit validated; cloud workflow handles push/deploy"}
        git(repo, "push", "origin", "HEAD:main", timeout=180)
        progress(kind, "git_push_completed", content_id=content_id)
        return {"status": "PUSHED", "id": content_id, "files": files,
                "note": "GitHub push confirmed; GitHub Pages deployment is asynchronous"}
    return {"status": last_rejection, "reason": safe_detail(feedback), "attempts": 3}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--kind", choices=["news", "lesson"])
    p.add_argument("--news-repo", type=pathlib.Path)
    p.add_argument("--lesson-repo", type=pathlib.Path)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--no-push", action="store_true", help="GitHub runner: validate and commit; a separate privileged step pushes")
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
            result = execute(args.kind, repo, no_push=args.no_push)
        result.update({"kind": args.kind, "time": started, "ended_at": dt.datetime.now().astimezone().isoformat(),
                       "run_url": os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" + os.environ.get("GITHUB_REPOSITORY", "") + "/actions/runs/" + os.environ.get("GITHUB_RUN_ID", "")})
        HOME.mkdir(exist_ok=True, parents=True)
        with (HOME / "runs.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        print(json.dumps(result, ensure_ascii=False))
        if result["status"].startswith(("FAILED", "REJECTED", "AUTH_", "UNKNOWN")):
            sys.exit(1)
    except Exception as exc:
        result = {"status": failure_status(exc), "kind": args.kind, "time": started, "error": safe_detail(exc)}
        HOME.mkdir(exist_ok=True, parents=True)
        with (HOME / "runs.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        # Do not emit unsanitized subprocess output or authentication diagnostics.
        sys.exit(1)


if __name__ == "__main__":
    main()
