#!/usr/bin/env python3
"""Daily privacy-preserving page readership and download-click report via GoatCounter.
No visitor names, IP addresses or personal identifiers are fetched or written.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("Asia/Seoul")
CATEGORIES = {
    "news": ("/news/", "download/news/"),
    "lesson": ("/lesson/", "download/lesson/"),
}


def get_period(day):
    start = dt.datetime.combine(day, dt.time.min, tzinfo=ZONE)
    end = start + dt.timedelta(days=1)
    return start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")


def request_hits(code, token, date, transport=None):
    start, end = get_period(date)
    base = "https://" + code + ".goatcounter.com/api/v0/stats/hits"
    seen = set()
    all_hits = []
    for _ in range(50):
        params = [("start", start), ("end", end), ("group", "day"), ("limit", "100")]
        params.extend(("exclude_paths", str(p)) for p in sorted(seen))
        req = urllib.request.Request(
            base + "?" + urllib.parse.urlencode(params),
            headers={"Authorization": "Bearer " + token, "Accept": "application/json"})
        if transport is None:
            with urllib.request.urlopen(req, timeout=25) as response:
                payload = json.load(response)
        else:
            payload = transport(req)
        batch = payload.get("hits", [])
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected GoatCounter API data format")
        for hit in batch:
            path_id = hit.get("path_id")
            if path_id in seen:
                raise RuntimeError("GoatCounter pagination returned duplicate path_id")
            seen.add(path_id)
            all_hits.append(hit)
        if not payload.get("more"):
            return all_hits
        if not batch:
            raise RuntimeError("GoatCounter indicated more entries but returned an empty page")
    raise RuntimeError("GoatCounter response exceeded 5,000 tracked paths")


def summarize(hits, kind):
    page_prefix, download_prefix = CATEGORIES[kind]
    views, downloads = [], []
    for hit in hits:
        path = str(hit.get("path", ""))
        title = str(hit.get("title", ""))[:180]
        count = int(hit.get("count", 0))
        if count < 0:
            raise RuntimeError("Negative count in analytics data")
        if path.startswith(page_prefix) and not hit.get("event"):
            views.append({"path": path, "title": title, "count": count, "metric": "view"})
        elif path.startswith(download_prefix) and hit.get("event"):
            downloads.append({"path": path, "title": title, "count": count, "metric": "download_click"})
    return sorted(views, key=lambda r: -r["count"]), sorted(downloads, key=lambda r: -r["count"])


def markdown(site, date, views, downloads):
    lines = [
        "## " + ("만날신문" if site == "news" else "AI 교안") + " 일별 독자·다운로드 대시보드",
        "",
        f"**집계일(KST): {date.isoformat()}**",
        "",
        f"- 콘텐츠별 방문 수 합계: **{sum(x['count'] for x in views):,}회**",
        f"- 자료 다운로드 클릭: **{sum(x['count'] for x in downloads):,}회**",
        f"- 조회된 콘텐츠: **{len(views)}건**",
        "",
        "> 집계가 활성화된 날짜부터만 기록됩니다. 방문 수는 콘텐츠별 방문(세션 중복 억제)으로, 실제 개인의 신원이나 사이트 전체 순방문자 수가 아닙니다.",
        "> 다운로드는 링크 클릭 횟수로, 실제 파일 저장 성공 횟수와 차이가 있을 수 있습니다.",
        "",
        "### 콘텐츠별 방문",
        "",
        "| 콘텐츠 경로 | 방문 수 |",
        "|---|---:|",
    ]
    for entry in views[:100]:
        lines.append(f"| `{entry['path']}` | {entry['count']:,} |")
    if not views:
        lines.append("| 집계된 방문 기록 없음 | — |")
    lines.extend(["", "### 자료 다운로드 클릭", "", "| 자료 종류·교안 ID | 횟수 |", "|---|---:|"])
    for entry in downloads[:100]:
        lines.append(f"| `{entry['path']}` | {entry['count']:,} |")
    if not downloads:
        lines.append("| 집계된 다운로드 기록 없음 | — |")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=("news", "lesson"), required=True)
    ap.add_argument("--date", help="YYYY-MM-DD in Asia/Seoul, default yesterday")
    args = ap.parse_args()
    date = (dt.date.fromisoformat(args.date) if args.date else
            dt.datetime.now(ZONE).date() - dt.timedelta(days=1))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    code = os.getenv("GOATCOUNTER_CODE", "").strip()
    token = os.getenv("GOATCOUNTER_API_TOKEN", "").strip()
    if not code or not token:
        msg = (
            "## 통계 연결 준비 필요\n\n"
            "GitHub 저장소 변수 `GOATCOUNTER_CODE` 및 Actions Secret "
            "`GOATCOUNTER_API_TOKEN`을 등록해야 실제 방문·다운로드 통계를 확인할 수 있습니다.\n\n"
            "미설정 상태를 **0명/0회로 표시하지 않습니다.**\n"
        )
        if summary:
            with open(summary, "a", encoding="utf-8") as f:
                f.write(msg)
        print("ANALYTICS_NOT_CONFIGURED")
        return 0
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", code):
        raise SystemExit("Invalid GOATCOUNTER_CODE")
    hits = request_hits(code, token, date)
    views, downloads = summarize(hits, args.kind)
    rendered = markdown(args.kind, date, views, downloads)
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(rendered)
    out = pathlib.Path("analytics-report")
    out.mkdir(exist_ok=True)
    report = out / f"{args.kind}-{date.isoformat()}.csv"
    with report.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "path", "title", "count"])
        writer.writeheader()
        writer.writerows(views + downloads)
    print(f"ANALYTICS_OK: {len(views)} content paths; {sum(v['count'] for v in downloads)} download clicks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
