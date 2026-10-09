"""새로 추가된 교안을 텔레그램으로 알린다.

사용법:
  python scripts/notify_telegram.py lessons/A.json [lessons/B.json ...]
  python scripts/notify_telegram.py --latest      # 가장 최근 교안 1개 (테스트용)

환경 변수:
  TELEGRAM_BOT_TOKEN  BotFather 가 준 봇 토큰 (GitHub Secret)
  TELEGRAM_CHAT_ID    메시지를 받을 채팅 ID (GitHub Secret)
  SITE_BASE           사이트 주소, 예: https://johnpark236-tech.github.io/ai-instructor-update-log
"""
import html
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent


def compose(lesson, base):
    e = lambda s: html.escape(str(s), quote=False)
    link = f"{base}/lessons.html#{urllib.parse.quote(lesson['id'])}"
    kind = "신규 AI" if lesson.get("type") == "new" else "기존 AI"
    acc = {"free": "무료", "freemium": "무료+유료", "paid": "유료"}.get(lesson["pricing"]["access"], "")
    steps = lesson["practice"]["follow"] + lesson["practice"]["make_mine"]
    m = lesson["minutes"]
    lines = [
        f"📘 <b>새 AI 실습 교안</b>  {e(lesson['id'])} ({e(lesson['created_at'])})",
        "",
        f"<b>[{kind}·{acc}] {e(lesson['title'])}</b>",
        f"{e(lesson['tool'])} · {e(lesson['feature'])} | 출시 {e(lesson['released'])} | {sum(m.values())}분",
        "",
        f"📝 <b>요약</b>\n{e(lesson['summary'])}",
        "",
        f"🎁 <b>결과물</b>\n{e(lesson['outcome'])}",
        "",
        f"💳 <b>요금</b>\n{e(lesson['pricing']['summary'])}\n" + "\n".join(f"· {e(x['name'])} ({e(x['price'])})" for x in lesson['pricing']['plans']),
        "",
        "🧭 <b>실습 단계</b>\n" + "\n".join(f"{i}. {e(s['title'])}" for i, s in enumerate(steps, 1)),
        "",
        f"👉 <a href=\"{html.escape(link)}\">교안 열기 · PPT 다운로드</a>",
        e(link),
    ]
    return "\n".join(lines)[:4000]


def send(token, chat_id, text):
    data = urllib.parse.urlencode({
        "chat_id": chat_id, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read().decode())
    if not body.get("ok"):
        raise RuntimeError(body)


def main(argv):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("::warning::TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID Secret 이 없어 알림을 건너뜁니다.")
        return 0
    base = os.getenv("SITE_BASE", "").rstrip("/")
    if argv == ["--latest"]:
        files = sorted((ROOT / "lessons").glob("*.json"))[-1:]
    else:
        files = [ROOT / a for a in argv if a.endswith(".json")]
    failed = 0
    for f in files:
        try:
            lesson = json.loads(f.read_text(encoding="utf-8"))
            send(token, chat_id, compose(lesson, base))
            print(f"보냄: {f.name}")
        except Exception as exc:  # 한 교안 실패가 다른 알림을 막지 않게
            failed += 1
            print(f"::error::{f.name} 알림 실패: {exc}")
        time.sleep(1)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
