# 클라우드 Codex CLI 자동발행 — PC 전원 OFF 가능

**운영 실행 환경:** GitHub Actions `ubuntu-latest` (Windows PC와 무관)

| 채널 | 저장소 | 예약(매시) | 결과 |
| --- | --- | --- | --- |
| AI 뉴스 | `johnpark236-tech/mannal_news` | 매시 **05분** | 공식 발표 확인 → 1건 기사 JSON·SVG → Codex 자체 검수 → main → deploy.yml |
| AI 교안 | `johnpark236-tech/ai-instructor-update-log` | 매시 **35분** | 공식 발표 확인 → CAT/JOB 교안 JSON → Codex 자체 검수 → main → pages.yml |

- 두 작업 모두 **매시간 최대 1건**. 공식 신규 발표가 없으면 발행하지 않고 `SKIPPED` 기록
- **개발 Codex CLI + 독립된 Codex CLI 읽기 전용 자체 검수 + Python 구조 검증**. Claude 불필요
- 새 AI와 기존 AI 신기능을 구분. 출처·요금·한국 접근 제한 근거 필수, `[확인 필요]` 표시. 신규 교안 문제는 정확히 3개
- 로그인: ChatGPT 계정 Codex CLI 세션의 `auth.json`을 **GitHub Actions Secrets**에 안전하게 1회 등록. API 키 추가하지 않음. 구독 한도·재인증 제한에 영향받음
- Codex 생성·검수 단계에는 GitHub 쓰기 토큰을 노출하지 않음. 승인 뒤 별도 단계에서만 `GITHUB_TOKEN`으로 푸시
- GitHub에서 `GITHUB_TOKEN` 푸시한 변경은 push 이벤트를 자동 발생시키지 않으므로 **Pages 워크플로를 별도 `workflow_dispatch`** 호출
- **주의:** 이는 OpenAI 서비스인 *Codex Cloud*의 내장 예약 기능이 아니라, **GitHub Actions가 클라우드에서 Codex CLI를 실행**하는 구조
- **보안:** 인증 파일을 저장소에 커밋하지 않고, GitHub Actions Cache/Artifact에 백업하지 않음. `auth.json` 내용은 계정 비밀번호 수준의 민감 정보. 채팅이나 PR 댓글로 전달하지 않음
- 무인 실행에 ChatGPT 로그인 세션을 쓰는 방식은 인증 토큰 만료·회전으로 재로그인 필요 가능. OpenAI가 공식 권장하는 CI 방식은 API 키 인증이지만, 이 구성은 사용자 요청대로 추가 API 키를 쓰지 않는 실험적 대안이므로 장기 연속 성공을 보장하지 않음

## 최초 1회 — PC에서 클라우드 비밀값 등록 (이후 PC 꺼도 됨)

PC의 **Codex CLI에 ChatGPT 계정으로 로그인**했다고 하셨으므로 다음은 GitHub 쪽 인증만 설정합니다.
이미 설치된 GitHub CLI(`gh`)가 없다면 https://cli.github.com/ 에서 설치하세요.

```powershell
gh auth login
Test-Path "$env:USERPROFILE\.codex\auth.json"
```

`True`일 때 아래 명령을 실행합니다. **비밀값을 화면에 출력하지 않고** 암호화된 GitHub Secrets로 전달합니다.

```powershell
Get-Content "$env:USERPROFILE\.codex\auth.json" -Raw | gh secret set CODEX_AUTH_JSON -R johnpark236-tech/ai-instructor-update-log
Get-Content "$env:USERPROFILE\.codex\auth.json" -Raw | gh secret set CODEX_AUTH_JSON -R johnpark236-tech/mannal_news
```

GitHub CLI 설치가 어렵다면 두 저장소의 **Settings → Secrets and variables → Actions → New repository secret**에서 이름을 `CODEX_AUTH_JSON`으로 등록하세요. 원본 `auth.json`의 전체 JSON을 복사해 등록하며, **이 채팅에는 절대 붙여넣지 않습니다.**

`Test-Path`가 `False`이면 토큰 파일이 OS 키 저장소에 있을 수 있으므로 내보내기 대신 파일 저장 방식으로 Codex CLI 재로그인을 검토하세요. 무리해서 인증 토큰을 추출하거나 공개하지 마세요.

## 설치 후 수동 시험 — GitHub에서 한 번씩

```powershell
gh workflow run codex-cloud-hourly-news.yml -R johnpark236-tech/mannal_news --ref main
gh workflow run codex-cloud-hourly-lesson.yml -R johnpark236-tech/ai-instructor-update-log --ref main
```

- Actions에서 두 작업이 `completed/success`인지 확인. **SKIPPED는 새 공식 발표가 없을 때 정상**
- GitHub Pages 실제 게시 확인. 뉴스 `deploy.yml`, 교안 `pages.yml`
- 최초 성공 뒤 기존 ChatGPT의 **만날신문 AI 기자 자동 발행** 작업을 일시정지해 **중복 발행 방지**
- 롤디펜스 `WORK_GAME_AUTO`처럼 **GitHub 서버 러너가 동작**하므로 PC를 끄더라도 예약 실행은 계속됨. 단, GitHub 스케줄 지연·비활성화, 구독 한도 및 인증 갱신 문제는 있을 수 있음

## 클라우드 작업 코드

- 교안: `.github/workflows/codex-cloud-hourly-lesson.yml`
- 뉴스: `mannal_news/.github/workflows/codex-cloud-hourly-news.yml`
- 공통: `automation/codex/hourly_publish.py`, `prompts/news.md`, `prompts/lesson.md`, `prompts/review.md`, `review-schema.json`

---

<details>
<summary>이전 로컬 Windows 작업 스케줄러 방식 (선택 사항 · 클라우드 운영에서는 불필요)</summary>

## 이전 로컬 자동화 설명

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


</details>
