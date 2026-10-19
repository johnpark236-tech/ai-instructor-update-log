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
  // 출시 후 14일이 지나서 만든 교안 = 지난 기능 다시 보기
  isPast(L) {
    const c = Date.parse(String(L.created_at || '').slice(0, 10)), r = Date.parse(L.released || '');
    return !isNaN(c) && !isNaN(r) && (c - r) / 86400000 > 14;
  },
  // 요금 문자열의 첫 금액 → {v, cur}. 읽을 수 없으면 null. 환율 추정 안 함
  parsePrice(t) {
    t = String(t || '').trim();
    if (/^(0원|₩0|\$0|0달러|무료)/.test(t)) return { v: 0, cur: null };
    let m = t.match(/\$\s?([\d,]+(?:\.\d+)?)/) || t.match(/([\d,]+(?:\.\d+)?)\s?달러/);
    if (m) return { v: +m[1].replace(/,/g, ''), cur: 'USD' };
    m = t.match(/₩\s?([\d,]+)/) || t.match(/([\d,]+)\s?원/);
    if (m) return { v: +m[1].replace(/,/g, ''), cur: 'KRW' };
    return null;
  },
  // 그래프로 그릴 수 있는 요금제 목록 (통화 1종, 2개 이상, 유료 1개 이상). 아니면 null
  priceSeries(P) {
    const rows = (P.plans || []).map(x => ({ x, p: this.parsePrice(x.price) })), ok = rows.filter(r => r.p);
    const curs = [...new Set(ok.map(r => r.p.cur).filter(Boolean))];
    if (ok.length < 2 || curs.length !== 1 || !ok.some(r => r.p.v > 0)) return null;
    return { cur: curs[0], ok, skip: rows.filter(r => !r.p) };
  },
  // 한 칸에 여러 내용이 이어진 글 → 항목 배열. ①②…, ' + ', ', 그리고 ', 문장 끝 '. ' 기준 (따옴표 안은 나누지 않음)
  // 반환 {lead, items}: 'xxx:' 처럼 머리말로 끝나는 첫 부분은 lead 로 분리
  splitItems(t) {
    t = String(t || '').trim(); if (!t) return { lead: '', items: [] };
    const keep = [];
    let x = t.replace(/'[^'\n]*'|‘[^’\n]*’|"[^"\n]*"|“[^”\n]*”|\([^()\n]*(?:\([^()\n]*\)[^()\n]*)*\)|\[[^\]\n]*\]/g, q => { keep.push(q); return '' + (keep.length - 1) + ''; });
    let parts = /[①-⑩](?!번)/.test(x) ? x.split(/\s*(?=[①-⑩](?!번))/) : [x];
    parts = parts.flatMap(p => p.split(/\s+\+\s+(?=[가-힣'‘"“\uE000])|,\s*그리고\s+|(?<=[가-힣A-Za-z0-9)\]%])\.\s+(?=\S)/));
    const back = p => p.replace(/(\d+)/g, (_, i) => keep[+i]);
    let items = parts.map(p => back(p).trim().replace(/^[①-⑩]\s*/, '').replace(/[.,]$/, '').trim()).filter(Boolean);
    let lead = '';
    if (items.length > 1 && /[:：—]$/.test(items[0])) lead = items.shift();
    return { lead, items };
  },
  // 목록 필터용 AI 묶음 — 회사명 없이 AI 이름만. Gmail·Meet·Workspace 의 AI 기능은 Gemini 로 동작하므로 Gemini 에 포함
  brand(L) {
    const t = String(L.tool || ''), c = String(L.company || '');
    // 회사 기준 우선: 기존 AI 회사가 만든 새 도구는 그 회사 AI 로 묶음 (예: Google Deep Review → Gemini)
    if (/^Google/i.test(c)) return 'Gemini';
    if (/^OpenAI/i.test(c)) return 'ChatGPT';
    if (/^Anthropic/i.test(c)) return 'Claude';
    if (/^Microsoft/i.test(c)) return 'Copilot';
    if (/^xAI/i.test(c)) return 'Grok';
    if (/^Genspark/i.test(c)) return 'Genspark';
    if (/^Meta\b/i.test(c)) return 'Meta AI';
    if (/ChatGPT|Codex|Sora/i.test(t)) return 'ChatGPT';
    if (/Claude/i.test(t)) return 'Claude';
    if (/Gemini|NotebookLM|Gmail|Google (Meet|Workspace|Docs|Sheets|Slides|Drive)|Veo|Imagen/i.test(t)) return 'Gemini';
    if (/Copilot/i.test(t)) return 'Copilot';
    if (/Grok/i.test(t)) return 'Grok';
    if (/Genspark/i.test(t)) return 'Genspark';
    return t.split(/\s|\(/)[0] || '기타';
  },
  // 교안 3개 미만인 AI 는 '기타' 버튼 하나로 묶음 (버튼이 너무 많아지지 않게)
  // 교안 수와 상관없이 항상 따로 보이는 AI 버튼
  PINNED_AI: ['ChatGPT', 'Gemini', 'Claude', 'Grok', 'Genspark'],
  brandGroups(list) {
    const c = {}; this.PINNED_AI.forEach(b => { c[b] = 0; }); list.forEach(l => { const b = this.brand(l); c[b] = (c[b] || 0) + 1; });
    const keep = ([b, n]) => n >= 3 || this.PINNED_AI.includes(b);
    const P = this.PINNED_AI, main = Object.entries(c).filter(keep).sort((a, b) => (P.includes(b[0]) - P.includes(a[0])) || b[1] - a[1]);
    const etc = Object.entries(c).filter(e => !keep(e)).map(([b]) => b);
    return { main, etc, etcN: etc.reduce((s, b) => s + c[b], 0) };
  },
  brandMatch(L, sel, list) {
    if (!sel) return true;
    const b = this.brand(L);
    return sel === '기타' ? this.brandGroups(list).etc.includes(b) : b === sel;
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
