"""교안 문체를 기술 문서용 개조식(명사형 종결)으로 바꾸고, 남은 서술형 어미를 찾는다.

  ~합니다 → ~함 / ~입니다 → ~임 / ~됩니다 → ~됨 / ~있습니다 → ~있음
  ~하세요 → ~할 것 / ~바뀐다 → ~바뀜 / ~했다 → ~함

사용법
  python scripts/style_terse.py --fix  lessons/*.json   # 변환해서 저장
  python scripts/style_terse.py --check lessons/*.json  # 남은 서술형 어미 목록 (있으면 종료 코드 1)

변환하지 않는 곳: 복붙용 프롬프트(prompt), 강사가 소리 내어 읽는 멘트(instructor.script),
퀴즈 문제·보기(quiz.q, quiz.options), 출처·URL·ID·서비스명.
"""
import json
import pathlib
import re
import sys

BASE, JUNG, JONG = 0xAC00, 588, 28
J_B, J_M, J_N, J_L = 17, 16, 4, 8  # 종성 인덱스: ㅂ ㅁ ㄴ ㄹ

EXEMPT_KEYS = {"prompt", "url", "id", "tool", "feature", "company", "created_at", "checked",
               "review_by", "released", "date", "price", "icon", "emoji", "access", "type",
               "version", "stage", "categories", "jobs", "learner_levels", "instructor_levels", "level"}
# 경로(키 순서)로 예외 지정
EXEMPT_PATHS = [("instructor", "script"), ("wrap", "quiz", "q"), ("wrap", "quiz", "options"),
                ("sources",), ("pricing", "sources")]

END = r"(?=[.!]?(?:\s|$|[()\"'”’,\ue000]))"


def is_hangul(ch):
    return 0xAC00 <= ord(ch) <= 0xD7A3


def jong(ch):
    return (ord(ch) - BASE) % JONG


def set_jong(ch, j):
    o = ord(ch) - BASE
    return chr(BASE + o - o % JONG + j)


def sub_end(pattern, repl, s):
    return re.sub(pattern + END, repl, s)


# 따옴표·괄호 안(예시 문장, 문법 표현 "-아/어 주세요", 대화 예문)은 원문 유지
QUOTE = re.compile(r"'[^'\n]*'|‘[^’\n]*’|\"[^\"\n]*\"|“[^”\n]*”|「[^」\n]*」|\([^()\n]*(?:\([^()\n]*\)[^()\n]*)*\)")
DIALOGUE = re.compile(r"^\s*(?:\[[^\]]{1,12}\]|[A-Za-z가-힣0-9]{1,6}\s?:)\s")


def convert(s):
    """따옴표 안(예시 문장·화면 문구)과 대화 대본 줄은 그대로 두고 나머지만 개조식으로."""
    if not s or not any(is_hangul(c) for c in s):
        return s
    out = []
    for line in s.split("\n"):
        if DIALOGUE.match(line) and "\n" in s:
            out.append(line)
            continue
        keep = []
        masked = QUOTE.sub(lambda m: keep.append(m.group(0)) or f"\ue000{len(keep) - 1}\ue001", line)
        conv = convert_line(masked)
        line = re.sub(r"\ue000(\d+)\ue001", lambda m: keep[int(m.group(1))], conv).rstrip()
        # 끝 마침표 정리 (개조식은 마침표 없음)
        if len(line) > 1 and line.endswith(".") and not line.endswith("..") and (is_hangul(line[-2]) or line[-2] in ")'\"”’"):
            line = line[:-1]
        out.append(line)
    return "\n".join(out)


def convert_line(s):
    if not any(is_hangul(c) for c in s):
        return s
    t = s
    # 1) 하였습니다/했습니다 → 함, 되었습니다/됐습니다 → 됨
    t = sub_end(r"(?:하였|했)습니다", "함", t)
    t = sub_end(r"(?:되었|됐)습니다", "됨", t)
    # 2) ~습니다 → ~음 (있습니다→있음, 않습니다→않음, 넣었습니다→넣었음)
    t = sub_end(r"습니다", "음", t)
    # 3) ~ㅂ니다 → ~ㅁ (합니다→함, 됩니다→됨, 입니다→임, 나옵니다→나옴), ㄹ 어간(만듭니다→만듦)
    def b_to_m(m):
        ch = m.group(1)
        if ch == "듭":
            return "듦"
        return set_jong(ch, J_M)
    t = re.sub(r"([가-힣])니다" + END, lambda m: b_to_m(m) if jong(m.group(1)) == J_B else m.group(0), t)
    # 4) ~하세요 → ~할 것, ~으세요 → ~을 것, (받침 없는 음절)세요 → ㄹ + 것
    t = sub_end(r"하세요", "할 것", t)
    t = sub_end(r"하십시오", "할 것", t)
    t = sub_end(r"으세요", "을 것", t)
    t = re.sub(r"([가-힣])세요" + END, lambda m: (set_jong(m.group(1), J_L) + " 것") if jong(m.group(1)) == 0 else m.group(0), t)
    # 5) 해요체
    for a, b in [("해요", "함"), ("돼요", "됨"), ("있어요", "있음"), ("없어요", "없음"), ("나와요", "나옴"),
                 ("줘요", "줌"), ("봐요", "봄"), ("써요", "씀"), ("와요", "옴"), ("이에요", "임"), ("예요", "임"),
                 ("거예요", "것임"), ("아니에요", "아님")]:
        t = sub_end(a, b, t)
    # 6) 해라체 (~한다/~했다/~있다)
    t = sub_end(r"(?:하였|했)다", "함", t)
    t = sub_end(r"(?:되었|됐)다", "됨", t)
    t = sub_end(r"([가-힣])었다", r"\1었음", t)
    t = sub_end(r"([가-힣])았다", r"\1았음", t)
    t = sub_end(r"있다", "있음", t)
    t = sub_end(r"없다", "없음", t)
    t = sub_end(r"않는다", "않음", t)
    t = sub_end(r"([가-힣])는다", r"\1음", t)
    t = re.sub(r"([가-힣])다" + END, lambda m: set_jong(m.group(1), J_M) if jong(m.group(1)) == J_N else m.group(0), t)
    # 7) 끝 마침표 정리 (개조식은 마침표 없음)
    t = t.rstrip()
    if len(t) > 1 and t.endswith(".") and not t.endswith("..") and (is_hangul(t[-2]) or t[-2] in ")'\"”’"):
        t = t[:-1]
    return t


REMAIN = re.compile(r"(?:니다|하세요|세요|해요|어요|아요|예요)" + r"[.!]?(?:\s|$|\()")


def remains(s):
    for line in s.split("\n"):
        if DIALOGUE.match(line) and "\n" in s:
            continue
        if REMAIN.search(QUOTE.sub("'…'", line)):
            return True
    return False


def exempt(path):
    if path and path[-1] in EXEMPT_KEYS:
        return True
    keys = tuple(p for p in path if isinstance(p, str))
    for ex in EXEMPT_PATHS:
        if keys[: len(ex)] == ex:
            return True
    return False


def walk(node, path, fn):
    if isinstance(node, dict):
        return {k: walk(v, path + (k,), fn) for k, v in node.items()}
    if isinstance(node, list):
        return [walk(v, path + (i,), fn) for i, v in enumerate(node)]
    if isinstance(node, str):
        return node if exempt(path) else fn(node, path)
    return node


def main(argv):
    mode, files = argv[0], [pathlib.Path(a) for a in argv[1:]]
    bad = 0
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        if mode == "--fix":
            nd = walk(d, (), lambda s, p: convert(s))
            if nd != d:
                f.write_text(json.dumps(nd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            hits = []
            walk(d, (), lambda s, p: (hits.append((".".join(map(str, p)), s)) if remains(s) else None) or s)
            for p, s in hits:
                print(f"{f.name}: {p}: …{s[-40:]}")
            bad += len(hits)
    if mode == "--check" and bad:
        print(f"서술형 어미 {bad}곳 — 개조식(~함·~임·~됨)으로 바꿀 것")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
