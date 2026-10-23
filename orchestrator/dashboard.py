"""Produce Markdown status for GitHub Issue / workflow summary."""
from datetime import datetime, timezone
def markdown(state):
    return ("## Codex AWF 운영 현황\n\n"
            f"- 상태: **{state.get('status','unknown')}**\n"
            f"- 작업: {state.get('task','')}\n"
            f"- 시도: {state.get('round',0)}\n"
            f"- 검수: {state.get('verdict','NOT_RUN')}\n"
            f"- Pages: {state.get('pages','NOT_VERIFIED')}\n"
            f"- 갱신(UTC): {datetime.now(timezone.utc).isoformat()}\n")
