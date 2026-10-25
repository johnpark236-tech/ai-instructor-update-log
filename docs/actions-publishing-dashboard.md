# Actions 뉴스·교안 통합 대시보드

[통합 대시보드 열기](https://github.com/johnpark236-tech/ai-instructor-update-log/actions/workflows/ai-publishing-dashboard.yml)

1. 가장 위의 실행 기록을 선택한다.
2. Summary(요약)에서 뉴스와 AI 교안 비교표 및 실행 내역을 확인한다.
3. 즉시 갱신하려면 Run workflow → main → Run workflow를 누른다.

매시 19·39·59분에 갱신을 예약한다. GitHub 예약 지연이 있을 수 있으며 표 상단의 실제 갱신 시각을 기준으로 판단한다. 모든 시각은 한국 시간이다.

표시: 최근 실행·다음 예정 예약·최근 24시간 실행/게시/생략/반려/실패/한도 대기/미기록 수·90분 초과 예약 간격·최근 게시 확인 링크·최신 등록 자료·전체 콘텐츠 수. 아래 상세표에서 Actions 상태와 실제 발행 상태, 원인·결과, 실행 링크를 함께 확인한다.

최신 등록 자료는 다른 작성자가 추가했을 수도 있으므로 Codex 자동 발행 건수와 구분한다. PUBLISHED만 실제 게시 확인으로 집계한다. 과거 미기록·조회 실패는 0건으로 해석하지 않는다.

Artifacts의 unified.md/unified.json에 상세 현황을 30일 보관한다. 이 대시보드는 읽기 전용이며 Codex 호출·추가 과금·콘텐츠 작성·발행 예약 변경을 수행하지 않는다. 기존 개별 운영 대시보드의 보충 실행은 유지한다.
