"""lessons/*.json 교안 파일을 검증하고 lessons.json 인덱스를 다시 만든다.

사용법: python scripts/build_lessons_index.py
교안 파일 형식이 틀리면 오류 목록을 출력하고 종료 코드 1로 끝난다.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LESSON_DIR = ROOT / "lessons"
INDEX = ROOT / "lessons.json"

CATEGORIES = {"추론", "이미지", "영상", "음성", "코딩", "에이전트", "리서치"}
REQUIRED = {
    "id": str, "created_at": str, "title": str, "tool": str, "company": str,
    "category": str, "type": str, "released": str, "level": str, "minutes": int,
    "summary": str, "why": str, "prerequisites": list, "pricing": dict, "steps": list,
    "practice": dict, "teaching_tips": list, "pitfalls": list, "quiz": list,
    "sources": list,
}
INDEX_FIELDS = ["id", "created_at", "title", "tool", "company", "category",
                "type", "released", "level", "minutes", "summary"]
ACCESS = {"free", "freemium", "paid"}


def check(path, data):
    errs = []
    for key, typ in REQUIRED.items():
        if key not in data:
            errs.append(f"{key} 없음")
        elif not isinstance(data[key], typ):
            errs.append(f"{key} 형식 오류")
    if errs:
        return [f"{path.name}: {e}" for e in errs]
    if data["id"] != path.stem:
        errs.append("id가 파일 이름과 다름")
    if data["category"] not in CATEGORIES:
        errs.append(f"category는 {sorted(CATEGORIES)} 중 하나")
    if data["type"] not in {"new", "update"}:
        errs.append("type은 new 또는 update")
    if len(data["steps"]) < 3:
        errs.append("steps는 3개 이상")
    for s in data["steps"]:
        if not {"title", "do", "expect"} <= set(s):
            errs.append("steps 항목에 title/do/expect 필요")
            break
    pr = data["pricing"]
    if pr.get("access") not in ACCESS:
        errs.append("pricing.access는 free/freemium/paid 중 하나")
    plans = pr.get("plans")
    if not isinstance(plans, list) or not plans or not all({"name", "price", "features"} <= set(x) for x in plans):
        errs.append("pricing.plans에 name/price/features 항목 1개 이상 필요")
    if not pr.get("summary") or not pr.get("checked"):
        errs.append("pricing에 summary/checked 필요")
    if not {"task", "checklist"} <= set(data["practice"]):
        errs.append("practice에 task/checklist 필요")
    if not data["sources"] or not all(str(s.get("url", "")).startswith("http") for s in data["sources"]):
        errs.append("sources에 http 링크 1개 이상 필요")
    return [f"{path.name}: {e}" for e in errs]


def main():
    lessons, errors = [], []
    for path in sorted(LESSON_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}: JSON 오류 {exc}")
            continue
        errs = check(path, data)
        if errs:
            errors.extend(errs)
            continue
        item = {k: data[k] for k in INDEX_FIELDS}
        item["access"] = data["pricing"]["access"]
        lessons.append(item)
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    lessons.sort(key=lambda x: (x["created_at"], x["id"]), reverse=True)
    INDEX.write_text(json.dumps({"count": len(lessons), "lessons": lessons},
                                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"lessons.json 갱신: {len(lessons)}개")


if __name__ == "__main__":
    main()
