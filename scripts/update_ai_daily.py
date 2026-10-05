import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
OUT = os.getenv("AI_DAILY_OUTPUT", "ai-daily.json")
KST = ZoneInfo("Asia/Seoul")

CATEGORIES = [
    ("추론", "추론 / LLM"),
    ("이미지", "이미지 생성"),
    ("영상", "영상 제작"),
    ("음성", "음성 / 보이스"),
    ("코딩", "코딩 AI"),
    ("에이전트", "AI 에이전트 / 자동화"),
    ("리서치", "검색 / 리서치 AI"),
]


def load_previous():
    if not os.path.exists(OUT):
        return {"categories": []}
    try:
        with open(OUT, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"categories": []}


def previous_items(previous, key):
    for category in previous.get("categories", []):
        if category.get("key") == key:
            return category.get("items", [])
    return []


def parse_json_array(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("JSON array not found")
    return json.loads(text[start:end + 1])


def validate(items):
    if not isinstance(items, list) or len(items) != 10:
        raise ValueError(f"expected 10 items, got {len(items) if isinstance(items, list) else 'non-list'}")
    required = {"name", "company", "status", "summary", "score", "released", "price", "best_for", "url"}
    for item in items:
        if not isinstance(item, dict) or not required.issubset(item):
            raise ValueError("invalid item schema")
        if item["status"] not in {"new", "update", "tracking"}:
            item["status"] = "tracking"
        item["score"] = max(0, min(100, int(item["score"])))
    return items


def research_category(client, key, title, date_text):
    prompt = f"""
오늘은 {date_text} (KST)입니다. 당신은 AI 산업을 매일 조사하는 베테랑 기술 리서치 실장입니다.

분야: {title}

최근 72시간의 공식 발표, 제품/모델 릴리스, 신규 기능, 신규 AI 서비스, 가격·접근성 변화를 웹에서 조사하고,
'오늘 확인할 가치'가 높은 AI/서비스를 정확히 TOP 10으로 선정하세요.

평가 기준:
- 최근 발표·업데이트 35%
- 성능/품질 25%
- 실사용성 20%
- 접근성·가격 10%
- 생태계·확장성 10%

규칙:
- 공식 블로그, 공식 릴리스 노트, 공식 문서, 공식 GitHub 등 1차 출처를 최우선으로 사용하세요.
- 신뢰할 수 있는 최신 보도는 보조 근거로 사용할 수 있습니다.
- 루머, 확인되지 않은 출시, 과장된 벤치마크는 제외하세요.
- 신규 서비스면 status='new', 의미 있는 신규 기능/업데이트면 'update', 주목할 대표 서비스이나 최근 큰 변화가 없으면 'tracking'.
- summary는 한국어 1~2문장으로 '무엇이 바뀌었고 왜 중요한지'를 쓰세요.
- url에는 해당 내용을 확인할 수 있는 공식/1차 출처를 넣으세요.
- released는 YYYY-MM-DD, 확인 불가하면 빈 문자열.
- price는 확인 가능한 경우에만 짧게, 아니면 빈 문자열.
- best_for는 20자 이내 한국어.
- score는 0~100 정수.

설명 문장이나 마크다운 없이 아래 JSON 배열만 반환하세요.
[
  {{
    "name":"",
    "company":"",
    "status":"update",
    "summary":"",
    "score":95,
    "released":"",
    "price":"",
    "best_for":"",
    "url":""
  }}
]
정확히 10개 항목이어야 합니다.
"""
    response = client.responses.create(
        model=MODEL,
        tools=[{"type": "web_search"}],
        input=prompt,
        max_output_tokens=12000,
    )
    return validate(parse_json_array(response.output_text))


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY GitHub Actions secret is not configured.")

    client = OpenAI(api_key=api_key)
    previous = load_previous()
    now = datetime.now(KST)
    date_text = now.strftime("%Y-%m-%d")
    categories = []
    failures = []

    for key, title in CATEGORIES:
        try:
            print(f"Researching: {title}")
            items = research_category(client, key, title, date_text)
        except Exception as exc:
            print(f"FAILED {title}: {exc}")
            items = previous_items(previous, key)
            failures.append(key)
        categories.append({"key": key, "title": title, "items": items})

    result = {
        "updated_at": now.strftime("%Y-%m-%d %H:%M KST"),
        "update_status": "partial" if failures else "success",
        "failed_categories": failures,
        "model": MODEL,
        "categories": categories,
    }

    if not any(c["items"] for c in categories):
        raise SystemExit("No category data was produced; keeping the previous file.")

    temp = OUT + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    os.replace(temp, OUT)
    print(f"Updated {OUT}: status={result['update_status']}")


if __name__ == "__main__":
    main()
