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

## 실습 교안 (매시간 자동 추가)

- 페이지: `lessons.html` (목록·검색·분야 필터, 교안별 체크리스트와 퀴즈)
- 교안 파일: `lessons/<YYYY-MM-DD-HHMM-slug>.json` — 교안 1개당 파일 1개
- 인덱스: `lessons.json` — `python scripts/build_lessons_index.py`가 교안 파일을 검증하고 다시 만듦
- 갱신: Claude 예약 작업이 1시간마다 새 AI 서비스/신기능 1개를 공식 출처로 조사 → 교안 JSON 작성 → 인덱스 재생성 → main 커밋 → Pages 자동 재배포
- 중복 방지: 이미 `lessons.json`에 있는 도구·기능은 다시 다루지 않음

교안 JSON 필드: `id, created_at, title, tool, company, category(추론/이미지/영상/음성/코딩/에이전트/리서치), type(new/update), released, level, minutes, summary, why, prerequisites[], steps[{title,do,expect}], practice{task,sample_input,checklist[]}, teaching_tips[], pitfalls[], quiz[{q,a}], sources[{title,url}]`
