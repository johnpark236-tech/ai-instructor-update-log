# Claude → Codex 인수인계 — AI 실습 교안 작성 (2026-10-25)

> 이 문서를 Codex에게 그대로 주거나, 맨 아래 **"Codex 시작 프롬프트"**만 복사해 붙여넣으면 됨.
> 저장소: `johnpark236-tech/ai-instructor-update-log` (main) · 사이트: https://johnpark236-tech.github.io/ai-instructor-update-log/lessons.html

---

## 0. 한 줄 요약

AI 전문 강사(John)가 **모든 분야 사람들에게 신규 AI·기존 AI 신기능을 신속·정확하게** 전달하기 위한 실습 교안 사이트.
교안은 `lessons/<ID>.json` 데이터 1개 = 교안 1개. 화면(`lessons.html`)·PPT(`lesson-pptx.js`)는 데이터에서 자동 생성.
Claude가 2026-10-09 ~ 10-24 매시간 작성 → **2026-10-24 Claude 예약 작업 중지**(매시간 작성·오후 5시 카톡 요약 모두). 이후 Codex가 이어받음.

---

## 1. 현재 상태 (인수 시점)

| 항목 | 상태 |
|---|---|
| 교안 수 | 171개 (`lessons.json` count) · 기준 `v2.3` |
| 릴리즈 노트 | 247건, 교안 대기(lesson_id 없음) 44건 |
| Claude 매시간 작성 | ⏸ 중지 (2026-10-24) |
| Claude 오후 5시 카톡 요약 | ⏸ 중지 (2026-10-25) |
| Codex 자동 작성 | `.github/workflows/codex-cloud-hourly-lesson.yml` (매시 35분, GitHub Actions에서 Codex CLI 실행) — **최근 5회 연속 `failure`** (2026-10-25 기준, "Codex creates, checks, and independently self-reviews one lesson" 단계). 원인 미확인 → 첫 작업으로 로그 확인 필요 |
| Codex 프롬프트 | `automation/codex/prompts/lesson.md`(작성), `prompts/review.md`(검수), 실행기 `automation/codex/hourly_publish.py` |

---

## 2. 저장소 구조 — 파일 역할

| 경로 | 역할 | 수정 |
|---|---|---|
| `docs/lesson-standard-v2.md` | **교안 작성 기준 v2.3 (최상위 규칙)** — 반드시 전체 읽기 | 규칙 바뀔 때만 |
| `lessons/AI-YYYY-MM-CATxx-NNN.json` | 교안 데이터 (1파일 = 1교안) | 새 교안 추가 |
| `lessons.json` | 목록 인덱스 — **직접 편집 금지**, 스크립트가 생성 | 자동 |
| `releases.json` | AI 출시 기록(릴리즈 노트) `{id,date,tool,company,type,title,summary,source{title,url},checked,lesson_id}` | 항목 추가·lesson_id 연결 |
| `scripts/build_lessons_index.py` | 스키마·glance 길이·문체 검사 + `lessons.json` 생성. 실패 시 종료코드 1 | — |
| `scripts/style_terse.py` | 문체 자동 변환(`--fix`)·검사(`--check`) | — |
| `lesson-meta.js` | 코드표(CAT·JOB·레벨), `isPast`, `splitItems`(번호 분리), `parsePrice`, `brand`(AI 필터 묶음) | 신중히 |
| `lessons.html` | 목록·교안 화면 (필터·즐겨찾기·공유·글씨 크기·요약본 그래프) | 신중히 |
| `lesson-pptx.js`, `scripts/build_downloads.js` | PPT(학습자용·강사용)·프롬프트 txt — **배포 때 서버에서 생성** (`downloads/`는 git 제외) | 신중히 |
| `releases.html` | 릴리즈 노트 화면 | — |
| `.github/workflows/pages.yml` | 배포: Node로 PPT 생성 → GitHub Pages | — |
| `.github/workflows/telegram-notify.yml` | 선택형 텔레그램 알림 (Secrets `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 있을 때만) | — |
| `tests/` | 화면 테스트(`quiz_ui.test.cjs` 등) | — |

---

## 3. 교안 작성 규칙 핵심 (상세는 기준 문서)

### 3-1. 주제 고르기 (기준 9장)
1. **최근 14일 안 새 출시** — 신규 AI·기존 AI 신기능 중 교안 없는 것
2. 없으면 `releases.json`의 **교안 대기**(lesson_id null) 예전 출시 → 사이트에 자동으로 `📚 지난 기능` 표시(출시 후 14일 넘으면)
3. 그것도 없으면 주요 서비스 공식 릴리스 노트를 6~12개월 전까지 거슬러 찾아 `releases.json`에 먼저 기록 후 작성
- **중복 금지**: `lessons.json`에 같은 tool+feature 있으면 다른 주제
- 확인 대상(공식 출처만): OpenAI(ChatGPT·Codex), Anthropic(Claude·Claude Code), Google(Gemini·NotebookLM·Workspace), **xAI Grok**, **Genspark**, Microsoft Copilot, Perplexity, Meta AI, Adobe Firefly, Canva AI, Midjourney, Runway, ElevenLabs, Suno, Notion AI, Cursor·GitHub Copilot·Gemini CLI. 유튜브·SNS = 단서로만
- **우선순위**: 교안이 적은 Grok·Genspark는 공식 근거 확인되면 먼저 작성 (John 요청)

### 3-2. 신규 AI / 기존 AI 구분 (기준 11장, John 확정 2026-10-19)
| type | 기준 |
|---|---|
| `new` 신규 AI | 새로 등장한 AI 브랜드·서비스 (그 회사·브랜드의 첫 AI 제품)만 |
| `update` 기존 AI | 이미 AI 서비스를 하는 회사가 자기 AI로 만든 새 기능·모델·도구. **별도 사이트·앱·이름이어도 기존 AI** (예: Google Deep Review·SynthID Detector, Genspark GenMail, Meta Muse) |
- 판단 질문: "이 회사·브랜드가 이미 AI 서비스를 하고 있나?" → 예 = `update`. `releases.json`도 같은 기준

### 3-3. 사실 규칙 (기준 5장)
- 공식 1차 출처(릴리스 노트·도움말·공식 블로그·요금 페이지)만 사실 근거. 기사는 보조 근거 + 출처 이름 표기
- 불확실 → `[확인 필요]` / `[미검증]` / `[실험 기능]`. **지어내지 말 것** (날짜·가격·메뉴 경로·한국 제공 여부)
- 한국 이용 가능 여부·요금제는 **그 신기능 자체**의 공식 근거로 확인 (Codex 프롬프트 규칙 유지)

### 3-4. 데이터 형식 (기준 6장 표 그대로)
- ID: `AI-YYYY-MM-CATxx-NNN` (해당 월·카테고리 다음 번호). `version` `v1.0`, `created_at` "YYYY-MM-DD HH:MM KST"
- `glance` 필수·글자 수 제한: one_liner 30자, cards 3~4개(title 12·text 25자), diagram nodes 3~5개(label 12자), before_after(label 14·text 50자), cautions 3개(25자)
- `pricing.access`: `free` / `freemium` / `paid`. **`plans[].price`에 실제 금액**("월 $20", "0원", "₩29,000") — 요약본 요금 그래프가 첫 금액을 읽음. 모르면 숫자 지어내지 말고 공식 안내 문구 그대로
- `sources`, `pricing.sources`는 `{title,url}` 객체 배열. `verification`은 문자열 배열
- `tool` 필드 표기 = AI 필터 버튼과 연결: "ChatGPT", "Claude", "Gemini", "Grok", "Genspark" 등 공식 표기. (필터는 `company`로 묶음: Google→Gemini, OpenAI→ChatGPT, Anthropic→Claude, Microsoft→Copilot, xAI→Grok)
- `wrap.quiz` **정확히 3문제**, 보기 4개, `answer` 0~3, 쉬운 해설
- 강사용: 시간표·멘트·Plan B·막히는 지점 5개·FAQ 5개 이상·레벨별 가이드·전날 체크리스트

### 3-5. 문체 (기준 10장, John 확정)
- **개조식 명사형 종결**: ~함 / ~임 / ~됨 / ~있음 / ~할 것 / 진행. **~합니다·~입니다·~하세요·~해요 금지**, 문장 끝 마침표 생략, 설명보다 이해 중심으로 짧게
- 예외(원문 유지): `prompt`(복붙 프롬프트), `instructor.script`(강사 낭독 멘트), 퀴즈 문제·보기, **따옴표·괄호 안 예시 문장**(예: 문법 "-아/어 주세요", 대화 예문)
- 작성 후 `python3 scripts/style_terse.py --fix lessons/<ID>.json` → 검사기가 남은 서술형 어미를 오류로 막음

### 3-6. 번호 표기 (기준 10-3, John 확정)
- 한 칸에 여러 항목(결과물·요약·예시)은 **①②③ 또는 " + "** 로 구분해 쓸 것 → 화면·PPT가 `1) 2) 3)` 자동 표시 + 개수 배지
- 화면 구성(자동): 맨 위 히어로 → PART 1 📊 요약본(핵심 요약표·기능혜택표·요금 그래프·시간 그래프·작동원리·비포애프터·주의) → PART 2 🛠 실습 → PART 3 📖 자세한 설명

---

## 4. 교안 1개 작성 절차 (명령어)

```bash
git fetch origin main && git checkout main && git reset --hard origin/main   # 최신 main
# 1) 읽기: docs/lesson-standard-v2.md 전체, 최근 lessons/*.json 2~3개, lessons.json, releases.json
# 2) 주제 선정(3-1) → 공식 출처 확인 → releases.json 항목 추가/lesson_id 연결
# 3) lessons/<ID>.json 작성 (기존 교안 파일은 수정하지 않음)
python3 scripts/style_terse.py --fix lessons/<ID>.json
python3 scripts/build_lessons_index.py        # "lessons.json 갱신: 교안 N개 …" 나올 때까지 수정
# 4) (선택) 화면 확인: python3 -m http.server 8765 → http://localhost:8765/lessons.html?id=<ID>
#    PPT 확인: npm install --no-save pptxgenjs@3.12.0 && node scripts/build_downloads.js
# 5) 변경 파일은 lessons/<ID>.json, lessons.json, releases.json 3개만
git add lessons/<ID>.json lessons.json releases.json
git -c user.name="John Park" -c user.email="244302970+johnpark236-tech@users.noreply.github.com" \
    commit -m "lesson: <ID> <도구> <기능>"
git fetch origin main && git rebase origin/main   # 충돌 시 lessons.json 은 build_lessons_index.py 로 재생성
git push origin HEAD:main
```

### Git 규칙 (필수)
- 커밋 이메일 **반드시** `244302970+johnpark236-tech@users.noreply.github.com` (이름 John Park). **개인 이메일 절대 금지** (과거 기록에서 제거 완료한 상태)
- push 전 항상 `git fetch && git rebase origin/main` (다른 자동 작업이 동시에 push)
- `GITHUB_TOKEN`으로 push하면 Pages가 자동 실행되지 않음 → `pages.yml`을 `workflow_dispatch`로 별도 실행 (Codex 실행기 `cloud_ops.py deploy`가 처리)
- 배포 확인: `gh run list -w pages.yml`, 실제 페이지 `…/lessons.html?id=<ID>`

---

## 5. 알림 (카카오톡) — 인수인계 주의

- Claude는 **카카오톡 "나에게 보내기"(PlayMCP 커넥터)** 로 새 교안마다 알림을 보냈음. 이 커넥터는 **Claude 계정 전용** → Codex에서는 사용 불가
- 알림 형식(유지 권장, 200자 이내):
  ```
  📘[기존 AI·무료] <이모지> <한 줄 요약>
  🎁 <오늘 만들 작품>
  💳 <요금 요약>
  👉 https://johnpark236-tech.github.io/ai-instructor-update-log/lessons.html?id=<ID>
  ```
  - 링크는 **반드시 `?id=` 형식 + `https://`** — 카카오톡은 `#` 뒷부분을 빼먹어 목록으로 열림 (2026-10-15 확인)
- Codex 쪽 대안: ① 텔레그램 워크플로(Secrets 등록 시 자동) ② 카카오 공식 API(카카오 개발자 앱 + 토큰 필요) ③ 알림 없이 사이트·Actions 대시보드로 확인 — **John에게 선택 확인 필요**

---

## 6. 사이트 기능 (건드릴 때 깨지지 않게)

- 목록: 새 교안이 맨 위(#N…#1), 탭 `학습할 교안 / ★ 즐겨찾기 / 완료`, 칩 `전체·신규 AI·기존 AI·📚 지난 기능`, 💳 요금(무료/무료+유료/유료), 🤖 AI(ChatGPT·Gemini·Claude·Grok·Genspark 고정 + 교안 3개 이상 AI, 나머지 '기타')
- 교안마다 📤 공유(휴대폰 공유창, 실패 시 링크 복사) · ☆ 즐겨찾기 · ✓ 완료. 완료·즐겨찾기는 localStorage, `#import=` 링크로 기기 이동
- 상단 글씨 크기 5단계(가−/가+), 카카오톡 앱 내 브라우저 감지 → "크롬으로 열기"(캐시 회피 `?v=`)
- `?id=<ID>` 주소로 교안 바로 열림, 예전 `#<ID>`도 지원
- PPT 다운로드는 서버 생성 파일 링크(`downloads/<ID>-learner.pptx` 등) — 카카오톡 내 브라우저는 blob 다운로드 불가라 이 방식 유지

---

## 7. 지금 Codex 설정과 기준 문서의 차이 — 확인·정리 필요

| 항목 | 기준 문서 / John 요청 | 현재 `automation/codex/prompts/lesson.md` | 권장 |
|---|---|---|---|
| 새 소식 없을 때 | 9장: 건너뛰지 않기 — 교안 대기·지난 기능으로 작성 | 무변경 **SKIP** | John 결정 필요. 매시간 작성이 중지된 상태라 SKIP 허용이 현실적일 수 있음 |
| 신규/기존 구분 | 11장 기준(회사 기준) | "신규 AI 또는 기존 AI 신기능" 일반 설명 | 11장 기준 문장 추가 |
| 번호 표기 | 10-3 (①② / +) | 없음 | 추가 |
| Grok·Genspark 우선 | John 요청 | 없음 | 추가 |
| 카톡 알림 | 매 교안 | 없음 | 5장 대안 결정 |
| `?id=` 링크 | 필수 | 해당 없음 | 알림 도입 시 적용 |

---

## 8. 완료 체크리스트 (교안 1개마다)

- [ ] 공식 1차 출처로 출시일·기능·요금·한국 이용 조건 확인, 불확실은 `[확인 필요]`
- [ ] 중복 아님 (`lessons.json` tool+feature)
- [ ] type 11장 기준, tool 표기 필터와 일치
- [ ] glance 길이·quiz 3문제·강사용 항목 충족
- [ ] 문체 개조식 (`style_terse.py --check` 통과), 여러 항목은 ①② 구분
- [ ] `build_lessons_index.py` 통과, 변경 파일 3개만
- [ ] noreply 이메일 커밋 → rebase → push → Pages 배포 성공 → `?id=` 주소로 실제 화면 확인

---

## Codex 시작 프롬프트 (복사해서 붙여넣기)

```
너는 AI 전문 강사 John의 "AI 실습 교안" 사이트를 Claude에게서 이어받아 운영한다.
저장소: johnpark236-tech/ai-instructor-update-log (main)
사이트: https://johnpark236-tech.github.io/ai-instructor-update-log/lessons.html

1. 먼저 docs/codex-handoff.md(인수인계)와 docs/lesson-standard-v2.md(작성 기준 v2.3) 전체를 읽고 그대로 따를 것.
2. 첫 작업: .github/workflows/codex-cloud-hourly-lesson.yml 최근 실행이 연속 실패 중임.
   gh run list -w codex-cloud-hourly-lesson.yml / gh run view <id> --log-failed 로 원인을 찾아 보고하고,
   고칠 수 있으면 고친 뒤 workflow_dispatch로 1회 시험 실행할 것.
3. automation/codex/prompts/lesson.md 를 인수인계 7장 표와 비교해 빠진 규칙
   (신규/기존 구분 11장, 번호 표기 10-3, Grok·Genspark 우선)을 추가하는 변경안을 만들 것.
   "새 소식 없을 때 SKIP vs 지난 기능으로 작성"과 "알림 방식(텔레그램/카카오 API/없음)"은
   내가 정할 테니 선택지만 정리해서 물어볼 것.
4. 교안을 직접 1개 작성할 때는 인수인계 4장 절차와 8장 체크리스트를 지키고,
   커밋 이메일은 244302970+johnpark236-tech@users.noreply.github.com 만 사용할 것.
5. 사실은 공식 1차 출처로만, 모르면 [확인 필요]. 지어내지 말 것.
6. 결과는 한국어로, 바뀐 파일·배포 결과·실제 교안 주소(?id= 형식)를 짧게 보고할 것.
```
