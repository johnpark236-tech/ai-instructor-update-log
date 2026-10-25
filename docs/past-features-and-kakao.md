# 지난 기능 교안 및 카카오톡 알림 운영

2026-10-25 John 승인: 새 소식이 없으면 미작성 지난 기능으로 작성(B), 카카오톡은 연결 가능 방식 확인 후 적용.

## 교안 정책

최근 14일 발표 → releases.json의 미작성 지난 출시 → 최근 6~12개월 공식 릴리스의 미작성 기능 순으로 조사한다. 지금 제공 여부·메뉴·요금·한국 이용 조건을 재검증하고, 원래 released를 유지해 기존 화면의 📚 지난 기능 표시를 사용한다. 과거 기능의 최초 출시일을 오늘로 바꾸지 않는다. 모든 후보가 중복·검증 불가하면 사유를 기록하고 보류한다. 한도 소진·인증 오류 시 허위 교안을 만들지 않는다.

CAT/JOB·학습자/강사 구분·실습·퀴즈 3문제·PPT/TXT 구조를 유지한다. 회사 기준 new/update, ①② 또는 + 구분, 개조식 예외를 명확히 했고 특정 회사 고정 우선은 적용하지 않는다. 콘텐츠 커밋은 John Park / 244302970+johnpark236-tech@users.noreply.github.com을 사용한다. 뉴스 중지는 유지한다.

## 카카오 연결 확인

현재 ChatGPT의 PlayMCP 나에게 보내기로 연결 시험 메시지 1통이 발송됐다. 이 성공이 GitHub Actions의 로그인·토큰 확보를 뜻하지는 않는다. Actions에서 ChatGPT 연결 도구를 그대로 호출하는 경로는 구성하지 않았다.

무인 발행 후 알림은 공식 카카오 REST API의 나에게 보내기 경로를 준비했다. scripts/notify_kakao.py는 PUBLISHED인 교안만 대상으로 하며 실제 확인 URL과 동일한 ?id= 링크를 마지막 줄에 온전히 유지하고 전체 200자 이내로 구성한다. SKIP·반려·실패·COMMITTED 상태에서는 보내지 않는다. 확정 HTTP 실패는 최대 1회 재시도, 타임아웃은 중복 발송 위험 때문에 DELIVERY_UNKNOWN으로 남긴다. 알림 실패로 발행을 되돌리지 않는다.

## 필요한 사용자 설정

카카오 개발자 앱에서 카카오 로그인과 talk_message 동의, 사이트 도메인/제품 링크를 설정하고 본인 계정으로 인증해야 한다. 새 계정·앱 생성과 동의는 사용자 설정이 필요하다. 토큰은 채팅에 보내지 않고 이 저장소 Settings → Secrets and variables → Actions에 등록한다.

- KAKAO_REST_API_KEY: 카카오 REST API 키
- KAKAO_REFRESH_TOKEN: 본인 계정의 갱신 토큰
- KAKAO_CLIENT_SECRET: 앱에서 활성화된 클라이언트 시크릿
- KAKAO_ACCESS_TOKEN: 선택형 현재 액세스 토큰. 이것만 등록하면 만료 후 자동 갱신할 수 없음

카카오에서 새 refresh_token이 반환되면 비밀 값은 출력·업로드하지 않는다. 결과에 refresh_token_rotation_required가 기록되며, 갱신 토큰이 만료되기 전에 사용자 재인증과 Secret 재등록이 필요하다. 무기한 로그인 유지로 보고하지 않는다.

설정 확인: Actions → Kakao lesson notification readiness. NOT_CONFIGURED는 자동 알림 미설정이며 전송 완료가 아니다. REFRESH_CONFIGURED도 등록 여부만 확인한 상태이므로 실제 발행 알림 성공은 notification.status=SENT로 별도 확인한다. 토큰이 없으면 발행은 계속되고 알림만 보류한다.

신규 교안 개별 알림을 대상으로 한다. 이전에 중지한 오후 5시 일일 요약 예약은 이번 변경에서 재개하지 않는다.

공식 문서:
- https://developers.kakao.com/docs/ko/kakaotalk-message/rest-api
- https://developers.kakao.com/docs/ko/kakaologin/rest-api
