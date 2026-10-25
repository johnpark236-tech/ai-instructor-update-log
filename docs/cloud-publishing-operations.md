# 클라우드 뉴스·교안 운영 인수인계

2026-10-25 KST 점검. 이 문서의 관측값은 당시 기록이며 이후에는 Actions와 실제 사이트를 다시 확인한다.

## 구조와 인증

- 공통 엔진: `automation/codex/hourly_publish.py` (이 저장소 main). 뉴스 워크플로가 이 저장소를 별도 checkout한다.
- 뉴스: `johnpark236-tech/mannal_news`, 매시 05분. 교안: 이 저장소, 매시 35분.
- Codex CLI 0.164.0, 기존 ChatGPT 구독 인증 `CODEX_AUTH_JSON`. 추가 AI API 과금 없음.
- 생성 workspace-write → 독립 read-only 검수 → Python 검증 → 로컬 커밋 → 별도 토큰 단계 push → Pages dispatch → 해당 SHA 배포 성공 → 실제 URL·파일 확인.
- GitHub write token은 Codex 단계 환경에 주입하지 않는다. auth.json은 실행 종료 시 삭제. 원본 인증정보·CLI 대화·출력은 artifact로 올리지 않는다.
- 인증 만료는 비밀 값을 채팅에 붙이지 말고 기존 로그인 갱신과 Actions Secret 재등록으로 복구한다. 동시 runner의 refresh-token 갱신 충돌 가능성은 아직 실증하지 못했으므로 인증 장애 로그로 확인한다.

## 확인한 장애와 근거

뉴스 실행 40102539682, 교안 실행 40103905158은 녹색 success지만 SKIPPED이며 발행하지 않았다. 기존 엔진은 파일 변경 없음만으로 신규 소식 없음으로 판단했고 조사 실패와 구분하지 않았다.

뉴스 실행 40067291744는 1차 JSON 요약 구조 실패 후 수정했으나 Google Knowledge Catalog 프리뷰의 국내 제공·요금 근거 미확인으로 2·3차 검수 반려됐다. 정보성 발표 보도와 한국 사용자 실습 교안의 검수 기준이 같아 생긴 정책 불일치다.

조회한 뉴스 전체 87개 실행, 교안 최근 100개 실행 중 현재 hourly workflow는 각각 6회다. 10-24 01시대 KST부터 10-25 01시대 KST 점검까지 뉴스는 SKIPPED 4회·RATE_LIMITED 1회·반려 실패 1회, 교안은 SKIPPED 4회·RATE_LIMITED 1회·콘텐츠 커밋 1회다. 예약 생성 간격이 수 시간인 사례가 존재한다. GitHub는 원래 예약 슬롯을 반환하지 않으므로 지연과 유실의 근본 원인을 이 기록만으로 확정할 수 없다.

교안 성공: 실행 40069508706, 커밋 bf98b4f4444f15a8ea1651bff7e654d195ef94aa, 배포 실행 40069789674. 신규 교안 AI-2026-10-CAT04-015는 2026-10-24 15:19 KST 작성, 15:20경 커밋. 총 교안 169개·release 245개 보존. 점검 시 실제 lesson JSON·인덱스·학습자/강사용 PPTX ZIP·프롬프트 TXT 접근 확인.

뉴스 최신 데이터 7개. 최신 기사는 영국 AI 생물안보 연구소 발표 기사 `ai-auto-20261024-uk-biosecurity`. 실제 기사 JSON·SVG·홈페이지 접근 확인. 현재 hourly Codex 실행의 발행 실적과 별도 ChatGPT 예약의 발행 실적을 혼동하지 않는다.

교안 사이트 `analytics-config.js`는 빈 사이트 코드다. 통계 수집은 미설정이며 과거 수치를 소급 생성하지 않는다. 뉴스 통계 설정은 빌드 환경과 daily-analytics 실행을 별도 확인해야 한다.

초기 점검에서는 기존 ChatGPT 예약 ‘만날신문 AI 기자 자동 발행’이 활성 상태였다. 이후 2026-10-25 02:41 KST 사용자 명시적 승인에 따라 중지했고, 홈페이지 발행 경로를 GitHub Actions의 Codex CLI로 통합했다.

## 상태와 결과

- GENERATED는 초안 생성 결과이며 발행 성공이 아니다.
- SKIPPED_NO_NEWS / SKIPPED_DUPLICATE는 실제 확인한 공식 출처 URL·이유가 있어야 한다.
- 보고 없음/형식 오류/파일 변경 불일치는 FAILED_GENERATION, 검색 장애는 FAILED_SEARCH.
- REJECTED_SCHEMA / REJECTED_FACT_CHECK / REJECTED_AVAILABILITY는 게시하지 않는다.
- RATE_LIMITED는 즉시 호출 중지, 다음 예약에서 재시도. 회복 시각은 추정하지 않는다.
- COMMITTED / PUSHED는 각각 로컬 커밋/원격 업로드이며 배포 성공을 뜻하지 않는다.
- PUBLISHED는 matching SHA의 Pages 워크플로 성공 및 실제 데이터·이미지/다운로드 파일 검증 통과다. 화면 클릭/렌더링 검증은 별도다.
- FAILED_DEPLOY는 push/배포/실제 URL 검증 실패. 인증정보가 들어갈 수 있는 subprocess argv는 출력하지 않는다.
- AUTH_FAILED는 인지 가능한 인증 오류, 나머지는 UNKNOWN_ERROR. setup 단계에서 결과 자체가 없으면 보고서에 미기록으로 표시한다.

각 실행의 Summary와 `<news|lesson>-publishing-result-<runid>` artifact의 result.json/report.md를 확인한다. 보관은 30일이다. 영구 이력 보관은 추후 별도 저장 정책을 설계해야 한다.

## 대시보드와 예약 복구

`publishing-dashboard.yml`은 매시 17·37·57분 및 발행 workflow 완료 시 실행된다. 최근 24시간 실행 수, 실제 PUBLISHED 수, 미기록 수, 90분 초과 예약 실행 간격을 표시한다. 과거 green run을 발행 성공으로 소급 계산하지 않는다. 결과 artifact는 `publishing-dashboard-<runid>`다.

마지막 실행 이후 1시간 이상이고 활성 실행도 없으면 workflow_dispatch로 1회 보충 요청한다. 원래 발행 workflow의 concurrency와 기존 콘텐츠 중복 검사를 유지한다. 이 보조 호출기도 GitHub 예약에 의존하므로 완전한 정시 실행 보장은 아니다. 별도 계정·유료 스케줄러는 도입하지 않았다.

## 장애 복구

1. 생성·검수 반려: Summary의 reason과 공식 원문 확인. 이용 불가 실습은 다른 후보로 교체, 정보성 발표는 미확인을 명시하고 발표 읽기 활동으로 작성.
2. 한도: 그대로 대기. 같은 회차 무한 재호출·API 우회 금지.
3. Git 충돌: 강제 push하지 않는다. FAILED_DEPLOY 기록 확인 후 최신 main 기반 새 실행. 이미 커밋된 콘텐츠 중복 금지.
4. Pages: deployment_run_url, 해당 SHA, 실제 JSON과 파일 확인. 데이터가 올랐다는 이유로 다운로드 성공을 단정하지 않는다.
5. 통계: GOATCOUNTER_CODE 및 API token을 안전한 GitHub 설정으로 등록한 뒤 daily-analytics와 실제 이벤트를 검증. 방문 횟수/순방문자·다운로드 클릭/저장 성공을 구분.

## 검증 범위와 남은 작업

로컬 회귀 테스트·교안 index 검증·공통 퀴즈 검사·뉴스 TypeScript 검사·Vite build를 실시한다. 현재 수정으로 실서비스의 신규 콘텐츠가 생성·배포되었다는 뜻은 아니다. 신규 코드의 클라우드 실행 결과를 확인한 뒤 완료 판정한다.

남은 과제: 구독 한도 소진→회복 실증, 신규 스키마로 Codex 생성·독립 검수·배포 통합 실증, 실제 휴대폰 UI 확인, 통계 계정 연결, 기존 ChatGPT 뉴스 예약 통합 승인, 외부 스케줄러 필요성 판단, 장기 이력 보관.


## 2026-10-25 02:06 KST 통합 확인 결과

- 뉴스 신규 기사 `ai-auto-20261025-google-tb-screening` 생성 → 스키마 검사 → 독립 Codex 검수 APPROVE → 커밋 → 안전한 rebase 후 main 업로드 확인. 원격 콘텐츠 커밋 ac37a768e06f9ff98ba325bd25466082d1b0db89. 기존 7건 보존, 총 8건.
- 실행 40113352808의 첫 시도는 동시 main 변경으로 업로드 실패, 두 번째는 공식 원문 접근 장애로 FAILED_SEARCH, 세 번째는 기사·SVG 작성 및 업로드 성공 후 Pages 2차 배포 지연으로 FAILED_DEPLOY를 기록했다. 각 시도는 별개이며 실패를 숨기지 않는다.
- 이후 실제 사이트에서 새 기사 객체 전체와 SVG 원문 바이트의 일치를 확인했다. 운영 대시보드 실행 40114468843의 dashboard.json은 해당 기록을 실제 URL 확인 후 PUBLISHED로 재판정했다. 당시 최근 24시간 워크플로 기록 7회, PUBLISHED 1회, 과거 결과 파일 미기록 6회다. 과거 6회는 로그를 별도 조사한 결과이며 자동 집계에서는 추측하지 않는다.
- 원래 Actions 실행은 failure로 남아 있다. 실제 게시 PUBLISHED와 Actions 결과를 별도로 표시하는 의도된 동작이다. 일반적인 Pages 대기 시간을 5분으로 늘리고, 이후 대시보드에서 지연 반영을 다시 확인한다.
- 교안 실행 40113352163은 기존 후보 중복과 신기능 국내 제공 근거 부족을 구체적으로 기록해 REJECTED_AVAILABILITY로 종료했다. 허위 교안을 생성하지 않았으며 169개 보존. 마지막 교안 발행은 10-24 15:20경의 AI-2026-10-CAT04-015다.
- 로컬 테스트 19개 통과. Windows/Linux 클라우드 검사 및 뉴스 설정 검사가 통과했고 제목 줄바꿈 수정의 배포 JS 반영을 확인했다. 현재 기사 JSON·SVG와 기존 교안 PPTX/TXT 검증은 했으나 휴대폰 육안·클릭 검증은 하지 않았다.
- 통계 미설정 및 기존 ChatGPT 뉴스 예약 중복 경로는 여전히 남아 있다. 외부 통계 계정 생성·중요 예약 중단은 인수인계 문서상 사전 승인 대상이다.

실행 증거:
- 뉴스 발행: https://github.com/johnpark236-tech/mannal_news/actions/runs/40113352808
- 뉴스 운영 대시보드: https://github.com/johnpark236-tech/mannal_news/actions/runs/40114468843
- 새 기사: https://mannalkorean.com/#/article/ai-auto-20261025-google-tb-screening
- 교안 미발행 사유: https://github.com/johnpark236-tech/ai-instructor-update-log/actions/runs/40113352163
- 변경 PR: https://github.com/johnpark236-tech/ai-instructor-update-log/pull/7 및 https://github.com/johnpark236-tech/mannal_news/pull/1 (모두 main 병합)


## 2026-10-25 02:41 KST 발행 예약 통합 완료

- 사용자 승인: ‘이 예약을 중지하고 Codex CLI 중심으로 통합해줘’.
- ChatGPT ‘만날신문 AI 기자 자동 발행’ 예약을 is_enabled=false로 변경하고 중지 응답을 확인했다. 삭제하지 않아 필요 시 복구 가능하다.
- 홈페이지의 정기 발행 주체는 GitHub Actions Codex CLI다. 뉴스 매시 05분, 교안 매시 35분. PC 전원과 무관하게 클라우드에서 실행한다.
- 기존 한도 소진 시 다음 예약 재시도·독립 검수·중복 검사·실제 URL 확인·운영 대시보드를 유지한다. GitHub 예약 지연과 구독 한도 때문에 매시간 발행을 보장하지 않는다.
- AI 업데이트 브리핑 등 다른 ChatGPT 예약은 변경하지 않았다. 통계 서비스 연결은 이번 승인 범위에 포함되지 않으며 여전히 별도 설정이 필요하다.


## 2026-10-25 매시간 발행 설정 재점검

사용자 요청에 따라 뉴스 매시 05분·교안 매시 35분의 Codex CLI 예약을 유지하고, 보충 점검을 20분 간격(매시 17·37·57분)으로 강화했다. 1시간 동안 새 실행이 없고 실행 중인 작업도 없으면 보충 실행을 요청한다. 회귀 테스트에서 59/60분 경계·활성 작업 차단·최신 실행 선택·이력 없음 처리를 확인했다. GitHub 예약 지연 및 사용 한도·출처 검증 결과에 따라 실제 게시를 생략할 수 있으며, 정시 또는 매시간 무조건 1건 게시를 보장하지 않는다.

교안도 Codex 자동 발행 성공 기록이 확인됐다: https://github.com/johnpark236-tech/ai-instructor-update-log/actions/runs/40132595307 (AI-2026-10-CAT08-029, 2026-10-25 06:10 KST경 커밋).
