"""교안(lessons/*.json, 기준 v2)과 AI 릴리즈 노트(releases.json)를 검증하고
lessons.json 인덱스를 다시 만든다. 기준 문서: docs/lesson-standard-v2.md

사용법: python scripts/build_lessons_index.py
형식이 틀리면 오류 목록을 출력하고 종료 코드 1로 끝난다.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LESSON_DIR = ROOT / "lessons"
INDEX = ROOT / "lessons.json"
RELEASES = ROOT / "releases.json"

CATS = {f"CAT-{i:02d}" for i in range(1, 13)}
JOBS = {"JOB-OFF", "JOB-MKT", "JOB-EDU", "JOB-CRE", "JOB-WRI", "JOB-DEV", "JOB-DAT",
        "JOB-BIZ", "JOB-PUB", "JOB-HLT", "JOB-FAR", "JOB-SEN", "JOB-STU", "JOB-GLB"}
LEARNER = {"초급", "중급", "고급"}
INSTRUCTOR = {"초보강사", "중급강사", "고급강사"}
ACCESS = {"free", "freemium", "paid"}
ID_RE = re.compile(r"^AI-(\d{4})-(\d{2})-(CAT\d{2})-(\d{3})$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

INDEX_FIELDS = ["id", "version", "created_at", "checked", "review_by", "title", "summary",
                "tool", "feature", "company", "type", "released", "categories", "jobs",
                "learner_levels", "instructor_levels", "outcome"]


def need(errs, cond, msg):
    if not cond:
        errs.append(msg)


def is_list(v, n=1, keys=None):
    if not isinstance(v, list) or len(v) < n:
        return False
    if keys:
        return all(isinstance(x, dict) and keys <= set(x) for x in v)
    return all(isinstance(x, str) and x.strip() for x in v)


def check_step(errs, where, steps):
    if not is_list(steps, 1, {"title", "do", "expect"}):
        errs.append(f"{where}: 단계마다 title/do/expect 필요")


def check_lesson(path, d):
    e = []
    s = lambda k: isinstance(d.get(k), str) and d[k].strip()
    for k in ["id", "version", "stage", "created_at", "checked", "review_by", "title", "summary",
              "tool", "feature", "company", "type", "released", "outcome"]:
        need(e, s(k), f"{k} 없음")
    if e:
        return e
    m = ID_RE.match(d["id"])
    need(e, m, "id 형식은 AI-YYYY-MM-CATxx-NNN")
    need(e, d["id"] == path.stem, "id가 파일 이름과 다름")
    need(e, d["type"] in {"new", "update"}, "type은 new(신규 AI) 또는 update(기존 AI)")
    for k in ["checked", "review_by", "released"]:
        need(e, DATE_RE.match(d[k]), f"{k}는 YYYY-MM-DD")
    need(e, d["review_by"] > d["checked"], "review_by는 checked 이후")
    cats = d.get("categories")
    need(e, isinstance(cats, list) and cats and set(cats) <= CATS, "categories는 CAT-01~12 코드 1개 이상")
    if m and isinstance(cats, list) and cats:
        need(e, m.group(3) == cats[0].replace("-", ""), "id의 CAT은 categories 첫 항목과 같아야 함")
    jobs = d.get("jobs")
    need(e, isinstance(jobs, list) and 1 <= len(jobs) <= 4 and set(jobs) <= JOBS, "jobs는 JOB 코드 1~4개")
    need(e, isinstance(d.get("learner_levels"), list) and set(d["learner_levels"]) <= LEARNER, "learner_levels 값 오류")
    need(e, isinstance(d.get("instructor_levels"), list) and set(d["instructor_levels"]) <= INSTRUCTOR, "instructor_levels 값 오류")
    need(e, d.get("learner_levels") or d.get("instructor_levels"), "대상 배지 1개 이상 필요")
    mn = d.get("minutes")
    need(e, isinstance(mn, dict) and all(isinstance(mn.get(k), int) and mn[k] > 0 for k in ["theory", "practice", "wrap"]),
         "minutes는 {theory, practice, wrap} 양의 정수")
    need(e, is_list(d.get("prerequisites")), "prerequisites 필요")
    need(e, is_list(d.get("objectives")) and len(d["objectives"]) <= 3, "objectives 1~3개")

    pr = d.get("pricing") or {}
    need(e, pr.get("access") in ACCESS, "pricing.access는 free/freemium/paid")
    need(e, is_list(pr.get("plans"), 1, {"name", "price", "features"}), "pricing.plans에 name/price/features 필요")
    need(e, pr.get("summary") and pr.get("checked"), "pricing에 summary/checked 필요")

    need(e, is_list(d.get("timeline"), 1, {"date", "text"}), "timeline 1개 이상 {date,text}")

    th = d.get("theory") or {}
    for k in ["definition", "analogy"]:
        need(e, isinstance(th.get(k), str) and th[k].strip(), f"theory.{k} 필요")
    cmp_ = th.get("comparison") or {}
    need(e, is_list(cmp_.get("headers"), 2) and isinstance(cmp_.get("rows"), list) and cmp_["rows"]
         and all(isinstance(r, list) and len(r) == len(cmp_["headers"]) for r in cmp_["rows"]),
         "theory.comparison headers/rows 칸 수 일치 필요")
    need(e, is_list(th.get("concepts"), 3, {"title", "body"}), "theory.concepts 3개 이상")
    need(e, is_list(th.get("can")) and is_list(th.get("cannot")), "theory.can / cannot 필요")
    need(e, is_list(th.get("safety"), 3), "theory.safety(윤리·보안) 3개 이상")

    pc = d.get("practice") or {}
    need(e, isinstance(pc.get("preview"), str) and pc["preview"].strip(), "practice.preview 필요")
    check_step(e, "practice.follow", pc.get("follow"))
    check_step(e, "practice.make_mine", pc.get("make_mine"))
    need(e, is_list(pc.get("challenges"), 1, {"level", "mission"}), "practice.challenges 필요")

    wr = d.get("wrap") or {}
    need(e, isinstance(wr.get("share"), str) and wr["share"].strip(), "wrap.share 필요")
    qz = wr.get("quiz")
    ok = is_list(qz, 3, {"q", "options", "answer", "explain"}) and all(
        isinstance(q["options"], list) and len(q["options"]) == 4 and isinstance(q["answer"], int) and 0 <= q["answer"] <= 3 for q in qz)
    need(e, ok, "wrap.quiz 3개 이상, options 4개, answer 0~3")
    if wr.get("rubric") is not None:
        need(e, is_list(wr["rubric"], 1, {"criterion", "high", "mid", "low"}), "wrap.rubric 형식 오류")

    ins = d.get("instructor") or {}
    need(e, is_list(ins.get("timetable"), 3, {"time", "content"}), "instructor.timetable 3개 이상")
    need(e, is_list(ins.get("script"), 2, {"label", "text"}), "instructor.script 2개 이상")
    need(e, is_list(ins.get("plan_b"), 2, {"situation", "response"}), "instructor.plan_b 2개 이상")
    need(e, is_list(ins.get("stuck"), 5, {"issue", "fix"}), "instructor.stuck 5개")
    need(e, is_list(ins.get("faq"), 5, {"q", "a"}), "instructor.faq 5개 이상")
    need(e, is_list(ins.get("level_guide"), 2, {"level", "guide"}), "instructor.level_guide 2개 이상")
    need(e, is_list(ins.get("day_before")), "instructor.day_before 필요")

    need(e, is_list(d.get("sources"), 1, {"title", "url"}) and all(str(x["url"]).startswith("http") for x in d["sources"]),
         "sources 1개 이상 (http 링크)")
    return [f"{path.name}: {x}" for x in e]


def check_releases(lesson_ids):
    errs = []
    if not RELEASES.exists():
        return ["releases.json 없음"]
    try:
        data = json.loads(RELEASES.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"releases.json JSON 오류 {exc}"]
    seen = set()
    for i, r in enumerate(data.get("items", [])):
        tag = f"releases.json[{i}]"
        for k in ["id", "date", "tool", "company", "type", "title", "summary", "checked"]:
            if not (isinstance(r.get(k), str) and r[k].strip()):
                errs.append(f"{tag}: {k} 없음")
        if errs:
            continue
        if r["id"] in seen:
            errs.append(f"{tag}: id 중복 {r['id']}")
        seen.add(r["id"])
        if not DATE_RE.match(r["date"]):
            errs.append(f"{tag}: date 형식 오류")
        if r["type"] not in {"new", "update"}:
            errs.append(f"{tag}: type 오류")
        src = r.get("source") or {}
        if not str(src.get("url", "")).startswith("http"):
            errs.append(f"{tag}: source.url 필요")
        lid = r.get("lesson_id")
        if lid is not None and lid not in lesson_ids:
            errs.append(f"{tag}: lesson_id {lid} 교안 없음")
    return errs, data


def main():
    lessons, errors, ids = [], [], set()
    for path in sorted(LESSON_DIR.glob("*.json")):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}: JSON 오류 {exc}")
            continue
        errs = check_lesson(path, d)
        if errs:
            errors.extend(errs)
            continue
        ids.add(d["id"])
        item = {k: d[k] for k in INDEX_FIELDS}
        item["access"] = d["pricing"]["access"]
        item["total_minutes"] = sum(d["minutes"].values())
        item["notice"] = d.get("notice") or ""
        lessons.append(item)
    res = check_releases(ids)
    if isinstance(res, list):
        errors.extend(res)
    else:
        rerr, rdata = res
        errors.extend(rerr)
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    lessons.sort(key=lambda x: (x["created_at"], x["id"]), reverse=True)
    INDEX.write_text(json.dumps({"standard": "v2.0", "count": len(lessons), "lessons": lessons},
                                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    items = rdata.get("items", [])
    print(f"lessons.json 갱신: 교안 {len(lessons)}개 / 릴리즈 노트 {len(items)}건 "
          f"(교안 대기 {sum(1 for r in items if not r.get('lesson_id'))}건)")


if __name__ == "__main__":
    main()
