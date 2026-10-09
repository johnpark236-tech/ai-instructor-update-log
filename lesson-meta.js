// 교안 기준 v2 코드표 (docs/lesson-standard-v2.md 4장). lessons.html, releases.html, lesson-pptx.js 공용.
window.LESSON_META = {
  CAT: {
    'CAT-01': '대화형 AI', 'CAT-02': '프롬프트', 'CAT-03': '문서·오피스', 'CAT-04': '이미지',
    'CAT-05': '영상·음성·음악', 'CAT-06': '리서치·분석', 'CAT-07': '코딩·노코드', 'CAT-08': '에이전트·자동화',
    'CAT-09': '윤리·저작권·보안', 'CAT-10': 'AI 교수법', 'CAT-11': '비즈니스·수익화', 'CAT-12': '도구 비교'
  },
  JOB: {
    'JOB-OFF': '사무·행정', 'JOB-MKT': '마케팅·소상공인', 'JOB-EDU': '교사·강사', 'JOB-CRE': '크리에이터',
    'JOB-WRI': '작가·출판', 'JOB-DEV': '개발·노코드', 'JOB-DAT': '데이터·연구', 'JOB-BIZ': '창업·1인기업',
    'JOB-PUB': '공공·평생교육', 'JOB-HLT': '의료·돌봄', 'JOB-FAR': '농업·제조·현장', 'JOB-SEN': '시니어',
    'JOB-STU': '학생·취준', 'JOB-GLB': '외국인·다문화'
  },
  LEVEL: { '초급': '🟢', '중급': '🟡', '고급': '🔴', '초보강사': '🔵', '중급강사': '🟣', '고급강사': '⚫' },
  KIND: { new: '신규 AI', update: '기존 AI' },
  ACCESS: { free: '무료', freemium: '무료+유료', paid: '유료' },
  RUBRIC: [
    { criterion: '완성도', high: '작품이 목적대로 작동·활용 가능', mid: '일부 미완성', low: '결과물 없음' },
    { criterion: '응용력', high: '자기 맥락으로 의미 있게 변형', mid: '예시를 약간 변형', low: '예시 그대로' },
    { criterion: '검증 습관', high: 'AI 결과의 오류를 찾아 수정함', mid: '일부 확인', low: '확인 없이 사용' },
    { criterion: '윤리·안전', high: '저작권·개인정보 고려를 설명 가능', mid: '부분적 인지', low: '인지 없음' }
  ],
  // 예전 링크(v1 교안 id) → 새 교안 ID
  LEGACY: {
    '2026-10-09-2349-gemini-skills': 'AI-2026-10-CAT02-001',
    '2026-10-10-0100-chatgpt-intelligent-ui': 'AI-2026-10-CAT01-002'
  },
  levelBadges(L) {
    return [...(L.learner_levels || []).map(x => `${this.LEVEL[x]}학습자-${x}`), ...(L.instructor_levels || []).map(x => `${this.LEVEL[x]}${x}`)];
  },
  totalMinutes(L) { const m = L.minutes || {}; return (m.theory || 0) + (m.practice || 0) + (m.wrap || 0); },
  promptText(L) {
    const out = [`# ${L.title}`, `교안 ID: ${L.id} (${L.version}) · 기준일 ${L.checked}`, ''];
    const add = (head, steps) => (steps || []).forEach((s, i) => { if (s.prompt) out.push(`## ${head} ${i + 1}. ${s.title}`, s.prompt, ''); });
    add('따라하기', L.practice.follow); add('내 것으로', L.practice.make_mine);
    out.push('## 도전 과제'); L.practice.challenges.forEach(c => out.push(`${c.level} ${c.mission}`));
    return out.join('\n');
  }
};
