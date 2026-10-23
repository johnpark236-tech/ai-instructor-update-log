# 뉴스·교안 일별 방문·다운로드 대시보드 설정

GitHub Pages 자체는 서버 로그·데이터베이스를 제공하지 않기 때문에 정적 HTML만으로 실제 방문 수를 저장할 수 없습니다.
현재 뉴스와 교안에 **선택적으로 활성화되는 GoatCounter 클라이언트 수집 코드**와
매일 GitHub Actions에서 실적을 조회하는 통계 보고서를 추가했습니다. 
**GoatCounter 사이트 코드와 읽기 권한 API 토큰이 등록되기 전에는 집계되지 않습니다.**
기존 데이터의 소급 집계도 할 수 없으며, 미설정 결과를 0으로 표시하지 않습니다.

## 등록 방법 (초기 한 번)

1. [GoatCounter](https://www.goatcounter.com/)에서 사이트를 두 개 만듭니다.
   - 첫 번째 사이트: `mannalkorean.com` (뉴스)
   - 두 번째 사이트: `johnpark236-tech.github.io` (AI 교안)
   - 통계 계정에서 시간대를 `Asia/Seoul`로 설정합니다.
2. 각각 발급된 사이트 코드(예: `mannalnews`, `mannallesson` 형태 — 실제 코드는 본인이 만든 값)를 해당 저장소의
   **Settings → Secrets and variables → Actions → Variables → New repository variable** 아래
   `GOATCOUNTER_CODE`에 등록합니다. 이 코드 자체는 공개되어도 되는 사이트 식별자입니다.
3. [GoatCounter 공식 API 안내](https://www.goatcounter.com/help/api)에 따라
   **[우측 상단 사용자명 → API]** 에서 사이트별 통계 읽기 API 토큰을 생성합니다.
   각각 해당 GitHub 저장소의 **Actions → Secrets → New repository secret**에
   `GOATCOUNTER_API_TOKEN`으로 넣습니다. 토큰은 절대 코드나 채팅에 붙여넣지 않습니다.
   이미 쓰는 `CODEX_AUTH_JSON`과는 **별개**입니다.
4. 뉴스 배포 워크플로 `Deploy to GitHub Pages`와 교안 `Deploy AI Daily to GitHub Pages`를 수동 실행하거나
   다음 정규 배포를 통해 새 사이트 코드를 적용합니다.
5. 기사 1건과 교안 1건을 열고, 교안의 학습자 PPT·강사용 PPT·프롬프트 다운로드를 시험합니다.
   약간의 지연 뒤 해당 GoatCounter 사이트에서 `/news/<id>`, `/lesson/<id>`,
   `download/lesson/<id>/learner` 등 통계 경로가 생기는지 확인합니다.
6. GitHub Actions **Daily news audience and download dashboard**,
   **Daily lesson audience and download dashboard** 워크플로에서 `Run workflow`로 보고서를 실행합니다.

## GitHub Actions 자동 보고서

- 매일 **00:20 KST**에 전날 00:00~24:00 기간을 조회합니다. GitHub 예약은 지연될 수 있습니다.
- GitHub Actions 실행 화면의 **Summary**에 콘텐츠별 방문(세션 기준 근사치),
  자료 다운로드 클릭 수, 인기 콘텐츠 순위를 표시합니다.
- 결과 표는 실행 **Artifacts → `*-analytics-<runid>` CSV**에도 30일간 보존합니다.
- 외부 API 오류가 있으면 `0`이 아니라 실행 실패로 구분합니다.
- 기존 홈페이지 조회를 소급 생성하지 않으며, 사용자 실명/이메일/IP를 GitHub로 전송하지 않습니다.
- 방문 수는 **콘텐츠별 순방문 추정**으로, 사이트 전체 사람 수와 일치하지 않습니다.
  다운로드 횟수는 파일 저장 완료가 아닌 **다운로드 링크 클릭 횟수**입니다.
- 뉴스는 별도의 첨부자료 다운로드 버튼이 없으면 해당 다운로드 값이 0일 수 있습니다.
- 타인의 접속정보를 분석하려면 개인정보 관련 법령·서비스 고지 문구를 점검하십시오.
  GoatCounter는 쿠키 없는 방문 집계 서비스지만 외부 통계 제공업체를 사용합니다.

## 검증된 공식 근거

- [GoatCounter JavaScript 방문/이벤트](https://www.goatcounter.com/help/js)
- [GoatCounter API 조회](https://www.goatcounter.com/api.html)
- [GoatCounter API 인증](https://www.goatcounter.com/help/api)
