# 시간당 뉴스 1건 + AI 교안 1건: Codex CLI 로컬 자동 발행

## 운영 범위와 안전성

- 뉴스: [만날신문](https://mannalkorean.com/) / `johnpark236-tech/mannal_news`
- 교안: [AI 강사 사이트](https://johnpark236-tech.github.io/ai-instructor-update-log/) / `johnpark236-tech/ai-instructor-update-log`
- **각 작업 매시간 최대 1건**. 새 공식 자료가 없으면 발행하지 않고 SKIP.
- **Claude 없음**. 생성 Codex CLI 1회 + **별도 읽기 전용 Codex CLI 자체 검수** 최대 3회 재작업 + Python 스키마 검사.
- 기존 AI/신규 AI, 12 CAT, JOB, 난이도, 무료/유료, 출처, 3문제, 학습자·강사용 PPT/프롬프트 유지.
- 사용자 구독으로 `codex login`; **추가 API 키·API 요금 사용 없음**. 무료/구독 한도 소진·로그인 만료 시 오류 기록, 무단 과금 우회 금지.
- GitHub에 게시되는 것은 검증된 콘텐츠 파일뿐. 커밋/푸시는 생성기 모델이 아니라 검증 후 실행기가 처리.
- 오류·중복·출처 미검증·허용 경로 밖 수정·자체 검수 반려 시 **게시하지 않음**.
- `main` 푸시 성공과 Pages 배포 성공은 다름. 배포는 각 저장소의 기존 GitHub Actions에서 진행.

## 권장 환경: 개인 Windows PC (공개 GitHub Actions 러너 사용 금지)

저장소가 **공개**이므로 개인 ChatGPT 로그인을 GitHub 공유 러너에 넣지 않습니다.
GitHub 서버는 PC의 ChatGPT 구독 세션을 공유하지 못합니다.
본 구성은 **PC가 켜져 있고 Windows 사용자로 로그인되어 있을 때** 실행되는
**작업 스케줄러** 방식입니다. 절전/로그아웃/인터넷 장애 시 정시 발행은 보장되지 않습니다.
완전한 무인 클라우드 24/7 서비스가 필요하다면 별도의 안전한 인증·전용 호스트 설계가 필요합니다.

### 최초 1회 설치

1. PC에 최신 Codex CLI, Python 3.11 이상, Git을 설치하고 PowerShell에서 `codex login`으로 **ChatGPT 계정 로그인**.
2. `codex login status`로 로그인 확인. GitHub 계정으로 `git push` 권한도 미리 연결(Git Credential Manager 또는 `gh auth login` + `gh auth setup-git`).
3. 이 저장소를 로컬에 clone하고 아래 명령을 해당 폴더에서 1회 실행:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\automation\codex\install-windows.ps1
   ```

4. 작업 스케줄러에서 `Mannal-Codex-AI-News`, `Mannal-Codex-AI-Lessons` 활성화 확인.
5. 시작 시각: **뉴스 매시 05분**, **교안 매시 35분** (PC 현지시간이 한국시간인지 확인).
6. 첫 작업을 직접 시험하려면 두 개를 동시에 실행하지 말고 다음 순서대로 실행:

   ```powershell
   $root = Join-Path $env:USERPROFILE 'MannalCodexHourly'
   & "$root\ai-instructor-update-log\automation\codex\run-task.ps1" -Kind news -Root $root
   & "$root\ai-instructor-update-log\automation\codex\run-task.ps1" -Kind lesson -Root $root
   ```

7. `$HOME\.mannal-codex-hourly\runs.jsonl`에서 `PUSHED` / `SKIPPED` / `FAILED` 확인하고 각 GitHub Actions Pages 배포 상태 확인.
8. **Codex CLI 정상 작동 확인 후에만** 기존 ChatGPT 뉴스 자동 발행 예약을 중지하여 중복 게시 방지. 기존 시간별 **AI 업데이트 브리핑**은 별도 작업이므로 원하지 않으면 그대로 유지.

## 구현 파일

- `prompts/news.md`: 공식 근거·기존 기사 비교 후 뉴스와 SVG 하나
- `prompts/lesson.md`: 새 교안 JSON 하나, release/index 정확히 연결
- `prompts/review.md`: 독립 Codex 검수 (읽기 전용)
- `review-schema.json`: 승인/반려 구조화 출력
- `hourly_publish.py`: 인증·Git 동기화→작성→경로·데이터 검증→Codex 자체 검수→승인 시 커밋·푸시
- `run-task.ps1`: Windows 작업 스케줄러 진입점
- `install-windows.ps1`: 2개 작업 등록

## 검증·장애 대응

```powershell
python -X utf8 automation/codex/hourly_publish.py --self-test
codex login status
Get-ScheduledTask -TaskName 'Mannal-Codex-AI-*'
Get-Content "$HOME\.mannal-codex-hourly\runs.jsonl" -Tail 20
```

- 한도 초과: API 결제로 전환하지 말고 FAILED 기록 후 다음 시간 실행.
- Git 충돌: 덮어쓰기/강제 푸시 금지. 최신 main을 다시 동기화한 뒤 다음 실행.
- 자체 검수 3회 반려: **자동 게시 금지**, 사용자가 로컬 변경 파일을 검토·복구 후 재실행.
- 첫 시간에 기사·교안이 반드시 1개씩 만들어지는 것은 아님. **공식 신기능이 없으면 생성하지 않는 규칙** 우선.
- 모든 명령은 로그인된 사용자의 PC에서 동작하며, 이 문서와 도구 생성만으로 PC의 작업 스케줄러가 자동 설치되는 것은 아님.
