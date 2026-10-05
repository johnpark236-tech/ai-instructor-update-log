# AI DAILY TOP10

AI 신생 서비스와 신규 기능을 매일 조사해 7개 분야별 TOP 10으로 보여주는 정적 홈페이지입니다.

## 자동 갱신

- 실행 시각: 매일 오전 6시 KST
- GitHub Actions cron: `0 21 * * *` (UTC)
- 조사 모델: `gpt-6-luna`
- 조사 방식: OpenAI Responses API + Web Search
- 결과 파일: `ai-daily.json`

## 분야

추론 / 이미지 생성 / 영상 제작 / 음성·보이스 / 코딩 AI / AI 에이전트·자동화 / 검색·리서치

## 최초 1회 필요한 설정

1. Repository → Settings → Secrets and variables → Actions → New repository secret
2. 이름: `OPENAI_API_KEY`
3. 값: 본인의 OpenAI API key
4. Repository → Settings → Pages → Source를 `GitHub Actions`로 선택
5. Actions → `Daily AI TOP10 Update` → `Run workflow`로 최초 실행

API key는 코드나 JSON에 직접 저장하지 마세요.

## 자동 반영 흐름

`06:00 KST 조사` → `ai-daily.json 갱신` → `main 커밋` → `GitHub Pages 자동 재배포`
