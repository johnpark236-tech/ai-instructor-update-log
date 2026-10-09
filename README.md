# AI DAILY TOP10

AI 신생 서비스와 신규 기능을 매일 조사해 7개 분야별 TOP 10으로 보여주는 정적 홈페이지입니다.

## 자동 갱신

- 기본 실행: ChatGPT 예약 작업
- 실행 시각: 매일 오전 6시 KST
- 결과 파일: `ai-daily.json`
- 업데이트 방식: 웹 리서치 → GitHub main 브랜치 커밋 → 홈페이지 데이터 반영

## 분야

추론 / 이미지 생성 / 영상 제작 / 음성·보이스 / 코딩 AI / AI 에이전트·자동화 / 검색·리서치 AI

## GitHub 구성

- `index.html`: 반응형 홈페이지
- `ai-daily.json`: 매일 갱신되는 TOP 10 데이터
- `scripts/update_ai_daily.py`: OpenAI API를 이용한 수동 백업 갱신 스크립트
- `.github/workflows/daily-ai-top10.yml`: API 기반 수동 백업 워크플로
- `.github/workflows/pages.yml`: GitHub Pages 자동 배포

## GitHub Pages 최초 1회 설정

현재 저장소의 Pages 기능은 아직 활성화되어 있지 않습니다.

Repository → Settings → Pages → Build and deployment → Source에서 `GitHub Actions`를 선택하세요.

이후 `ai-daily.json`이 갱신될 때마다 Pages 워크플로가 홈페이지를 자동 재배포합니다.

## 선택 사항: OpenAI API 백업 실행

GitHub Actions에서 별도로 수동 갱신을 실행하려면 Repository secret에 `OPENAI_API_KEY`를 등록하세요.
API key는 코드나 JSON에 직접 저장하지 마세요.

## 자동 반영 흐름

`매일 06:00 KST 조사` → `ai-daily.json 갱신` → `main 커밋` → `GitHub Pages 자동 재배포`

## 실습 교안 (기준 v2.0, 매시간 자동 추가)

- 작성 기준: [`docs/lesson-standard-v2.md`](docs/lesson-standard-v2.md) — 교안 ID(AI-YYYY-MM-CATxx-NNN), 대상 배지, 직업군 JOB 코드, 카테고리 CAT-01~12, 이론·실습·정리 3부 구성, 강사용 지도 노트, 유효기간
- 페이지: `lessons.html` — 순서 번호, 완료하면 숨김(완료 탭 보관), 신규/기존 AI·카테고리·대상·직업군 필터, 학습자용/강사용 보기 전환, 인터랙티브 퀴즈
- 내려받기: PPT 학습자용 / PPT 강사용(지도 노트 슬라이드 + 발표자 노트에 멘트) / 복붙 프롬프트 모음 .txt
- 교안 파일: `lessons/<교안 ID>.json`, 인덱스 `lessons.json`
- 검증: `python scripts/build_lessons_index.py` (교안과 릴리즈 노트를 함께 검사)

## AI 릴리즈 노트 (출시일 관리)

- 데이터: `releases.json` — 공식 릴리스 노트에서 확인한 출시·신기능 1건당 1줄, 교안이 있으면 `lesson_id`로 연결
- 페이지: `releases.html` — 월별 출시 기록, 서비스·신규/기존·교안 있음/대기 필터
- 매시간 예약 작업이 주요 AI 서비스의 공식 릴리스 노트를 확인해 새 항목을 추가하고, 교안이 없는 항목 중 하나로 교안을 작성

## 알림

- 카카오톡: 매시간 예약 작업이 교안을 올린 뒤 "나에게 보내기"로 200자 요약 + 링크 전송
- 텔레그램(선택): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` Secret 등록 시 `.github/workflows/telegram-notify.yml`이 새 교안마다 발송
