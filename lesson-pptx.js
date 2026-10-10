// 교안(기준 v2) JSON → PowerPoint(.pptx). lessons.html 의 PPT 버튼에서 사용.
// mode: 'learner' = 학습자 배포본, 'instructor' = 강사용 완전본(지도 노트 슬라이드 + 발표자 노트에 멘트)
(function () {
  const C = { navy: '07111F', cyan: '0891B2', cyanL: '6EE7FF', text: '1E293B', sub: '475569', green: '047857', greenBg: 'ECFDF5', warn: 'B45309', warnBg: 'FFFBEB', red: 'BE123C', line: 'CBD5E1', card: 'F1F5F9', violet: '5B21B6' };
  const FONT = 'Malgun Gothic';
  let libPromise;
  function loadLib() {
    if (window.PptxGenJS) return Promise.resolve();
    if (!libPromise) libPromise = new Promise((ok, fail) => {
      const s = document.createElement('script'); s.src = './vendor/pptxgen.bundle.js'; s.onload = ok;
      s.onerror = () => { libPromise = null; fail(new Error('PPT 라이브러리를 불러오지 못했습니다.')); };
      document.head.appendChild(s);
    });
    return libPromise;
  }

  function build(L, mode) {
    const MT = window.LESSON_META, ins = mode === 'instructor';
    const pptx = new window.PptxGenJS();
    pptx.layout = 'LAYOUT_WIDE'; pptx.title = L.title; pptx.author = 'AI 실습 교안';
    const script = (L.instructor.script || []).slice();
    const takeScript = re => { const i = script.findIndex(s => re.test(s.label)); return i < 0 ? null : script.splice(i, 1)[0]; };
    let n = 0;
    const note = (s, txt) => { if (ins && txt) s.addNotes(txt); };

    function slide(title, section) {
      const s = pptx.addSlide(); n++;
      s.background = { color: 'FFFFFF' };
      s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.95, fill: { color: section === 'ins' ? C.violet : C.navy } });
      s.addText(title, { x: 0.55, y: 0.1, w: 9.6, h: 0.75, fontFace: FONT, fontSize: 24, bold: true, color: 'FFFFFF', valign: 'middle', margin: 0 });
      s.addText(`${L.id} · ${L.tool}`, { x: 9.3, y: 0.1, w: 3.5, h: 0.75, fontFace: FONT, fontSize: 11, color: C.cyanL, align: 'right', valign: 'middle', margin: 0 });
      s.addText(String(n), { x: 12.2, y: 7.05, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 10, color: C.sub, align: 'right', margin: 0 });
      return s;
    }
    const bullets = (items, size, color) => items.map(t => ({ text: t, options: { bullet: { indent: 16 }, fontFace: FONT, fontSize: size, color: color || C.text, paraSpaceAfter: 6, breakLine: true } }));
    function table(s, head, rows, y, colW, size) {
      const hdr = head.map(h => ({ text: h, options: { bold: true, color: 'FFFFFF', fill: { color: C.cyan } } }));
      const body = rows.map((r, i) => r.map((c, j) => ({ text: String(c), options: { fill: { color: i % 2 ? 'FFFFFF' : C.card }, bold: j === 0 } })));
      s.addTable([hdr, ...body], { x: 0.55, y, w: 12.2, colW, fontFace: FONT, fontSize: size || 13, color: C.text, border: { type: 'solid', pt: 0.75, color: C.line }, valign: 'middle', margin: 0.07, autoPage: true, autoPageRepeatHeader: true, autoPageHeaderRows: 1, newSlideStartY: 1.15 });
    }
    function box(s, text, x, y, w, h, fill, color, size, bold) {
      s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, fill: { color: fill }, line: { color: C.line }, rectRadius: 0.1 });
      s.addText(text, { x: x + 0.2, y: y + 0.08, w: w - 0.4, h: h - 0.16, fontFace: FONT, fontSize: size || 15, color: color || C.text, bold: !!bold, valign: 'middle', margin: 0 });
    }

    // 표지
    const cover = pptx.addSlide(); n++;
    cover.background = { color: C.navy };
    const kind = MT.KIND[L.type], acc = MT.ACCESS[L.pricing.access];
    cover.addShape(pptx.ShapeType.roundRect, { x: 0.8, y: 0.6, w: 1.6, h: 0.46, fill: { color: L.type === 'new' ? '70E1A1' : '6EE7FF' }, rectRadius: 0.08 });
    cover.addText(kind, { x: 0.8, y: 0.6, w: 1.6, h: 0.46, fontFace: FONT, fontSize: 16, bold: true, color: C.navy, align: 'center', valign: 'middle', margin: 0 });
    cover.addShape(pptx.ShapeType.roundRect, { x: 2.55, y: 0.6, w: 1.6, h: 0.46, fill: { color: C.navy }, line: { color: '70E1A1', width: 1.5 }, rectRadius: 0.08 });
    cover.addText(acc, { x: 2.55, y: 0.6, w: 1.6, h: 0.46, fontFace: FONT, fontSize: 15, bold: true, color: '70E1A1', align: 'center', valign: 'middle', margin: 0 });
    cover.addText(`📘 표준 교안 · ${L.id} · ${L.version}${ins ? ' · 강사용 완전본' : ' · 학습자용'}`, { x: 4.4, y: 0.6, w: 8.2, h: 0.46, fontFace: FONT, fontSize: 13, color: C.cyanL, valign: 'middle', margin: 0 });
    cover.addText(L.title, { x: 0.8, y: 1.4, w: 11.8, h: 2.1, fontFace: FONT, fontSize: 34, bold: true, color: 'FFFFFF', valign: 'top', margin: 0 });
    cover.addText(L.summary, { x: 0.8, y: 3.7, w: 11.6, h: 1.4, fontFace: FONT, fontSize: 17, color: 'C0CDE0', valign: 'top', margin: 0 });
    cover.addText(MT.levelBadges(L).join('   '), { x: 0.8, y: 5.4, w: 11.8, h: 0.4, fontFace: FONT, fontSize: 14, color: 'FFFFFF', margin: 0 });
    cover.addText(`${L.company} ${L.tool} — ${L.feature}  |  출시 ${L.released}  |  기준일 ${L.checked} · 재검토 ${L.review_by}  |  ${MT.totalMinutes(L)}분`, { x: 0.8, y: 6.3, w: 11.8, h: 0.4, fontFace: FONT, fontSize: 12, color: '91A6C2', margin: 0 });
    const op = takeScript(/오프닝/); note(cover, op && op.text);

    // 한눈에 보기 (그림 우선 요약)
    const G = L.glance;
    if (G) {
      let g = slide('⚡ 한눈에 보기');
      g.addText(`${G.emoji}  ${G.one_liner}`, { x: 0.55, y: 1.15, w: 12.2, h: 0.75, fontFace: FONT, fontSize: 26, bold: true, color: C.text, margin: 0 });
      box(g, '🎁 오늘 만들 작품: ' + L.outcome, 0.55, 2.0, 12.2, 0.85, C.greenBg, C.green, 15, true);
      const cn = G.cards.length, cw2 = (12.2 - 0.25 * (cn - 1)) / cn;
      G.cards.forEach((c, i) => {
        const x = 0.55 + i * (cw2 + 0.25);
        g.addShape(pptx.ShapeType.roundRect, { x, y: 3.1, w: cw2, h: 3.0, fill: { color: C.card }, line: { color: C.line }, rectRadius: 0.12 });
        g.addText(c.icon, { x, y: 3.25, w: cw2, h: 1.0, fontSize: 40, align: 'center', margin: 0 });
        g.addText(c.title, { x: x + 0.15, y: 4.3, w: cw2 - 0.3, h: 0.55, fontFace: FONT, fontSize: 18, bold: true, color: C.text, align: 'center', margin: 0 });
        g.addText(c.text, { x: x + 0.15, y: 4.85, w: cw2 - 0.3, h: 1.1, fontFace: FONT, fontSize: 13, color: C.sub, align: 'center', valign: 'top', margin: 0 });
      });
      g.addText(`⏱ ${MT.totalMinutes(L)}분   💳 ${acc}   📅 출시 ${L.released}   🎯 ${MT.levelBadges(L).join(' ')}`, { x: 0.55, y: 6.35, w: 12.2, h: 0.45, fontFace: FONT, fontSize: 13, color: C.sub, margin: 0 });

      g = slide('🔄 ' + G.diagram.title);
      const nn = G.diagram.nodes.length, gap = 0.55, nw = (12.2 - gap * (nn - 1)) / nn;
      G.diagram.nodes.forEach((nd, i) => {
        const x = 0.55 + i * (nw + gap);
        g.addShape(pptx.ShapeType.roundRect, { x, y: 1.3, w: nw, h: 1.9, fill: { color: 'E0F7FF' }, line: { color: C.cyan, width: 1.5 }, rectRadius: 0.12 });
        g.addText(nd.icon, { x, y: 1.4, w: nw, h: 0.95, fontSize: 34, align: 'center', margin: 0 });
        g.addText(nd.label, { x: x + 0.1, y: 2.35, w: nw - 0.2, h: 0.75, fontFace: FONT, fontSize: 15, bold: true, color: C.text, align: 'center', valign: 'middle', margin: 0 });
        if (i < nn - 1) g.addShape(pptx.ShapeType.rightArrow, { x: x + nw + 0.08, y: 2.0, w: gap - 0.16, h: 0.45, fill: { color: C.cyan }, line: { color: C.cyan } });
      });
      const ba = G.before_after;
      g.addShape(pptx.ShapeType.roundRect, { x: 0.55, y: 3.55, w: 5.7, h: 1.9, fill: { color: 'F4F1F8' }, line: { color: 'C4B5D9' }, rectRadius: 0.12 });
      g.addText([{ text: '😐 ' + ba.before.label, options: { bold: true, fontSize: 16, breakLine: true } }, { text: ba.before.text, options: { fontSize: 14 } }], { x: 0.8, y: 3.65, w: 5.2, h: 1.7, fontFace: FONT, color: C.text, valign: 'middle', margin: 0 });
      g.addShape(pptx.ShapeType.rightArrow, { x: 6.4, y: 4.25, w: 0.55, h: 0.5, fill: { color: C.cyan }, line: { color: C.cyan } });
      g.addShape(pptx.ShapeType.roundRect, { x: 7.05, y: 3.55, w: 5.7, h: 1.9, fill: { color: C.greenBg }, line: { color: '6EE7B7' }, rectRadius: 0.12 });
      g.addText([{ text: '😀 ' + ba.after.label, options: { bold: true, fontSize: 16, breakLine: true } }, { text: ba.after.text, options: { fontSize: 14 } }], { x: 7.3, y: 3.65, w: 5.2, h: 1.7, fontFace: FONT, color: C.green, valign: 'middle', margin: 0 });
      const cw3 = (12.2 - 0.25 * 2) / 3;
      G.cautions.forEach((c, i) => box(g, '⚠️ ' + c, 0.55 + i * (cw3 + 0.25), 5.75, cw3, 0.9, C.warnBg, C.warn, 13, true));
    }

    // 메타정보
    let s = slide('📋 교안 메타정보');
    table(s, ['항목', '내용'], [
      ['대상 배지', MT.levelBadges(L).join('  ')], ['직업군', L.jobs.map(j => `${j} ${MT.JOB[j]}`).join(', ')],
      ['카테고리', L.categories.map(c => `${c} ${MT.CAT[c]}`).join(' · ')], ['기능 출시일', L.released],
      ['필요 요금제', `${acc} — ${L.pricing.summary}`],
      ['소요 시간', `이론 ${L.minutes.theory}분 + 실습 ${L.minutes.practice}분 + 정리 ${L.minutes.wrap}분`],
      ['준비물', L.prerequisites.join(' / ')], ['최종 결과물', L.outcome]
    ], 1.2, [2.6, 9.6], 12);

    // 타임라인 + 목표
    s = slide('🗓️ 기능 출시 타임라인');
    table(s, ['날짜', '업데이트 내용'], L.timeline.map(t => [t.date, t.text]), 1.2, [1.9, 10.3], 13);
    s = slide('🎯 학습 목표');
    s.addText(L.objectives.map((o, i) => ({ text: `${i + 1}. ${o}`, options: { fontFace: FONT, fontSize: 22, color: C.text, paraSpaceAfter: 18, breakLine: true } })), { x: 0.9, y: 1.5, w: 11.6, h: 5, valign: 'top', margin: 0 });

    // 1부 이론
    const th = L.theory;
    s = slide('1부 이론 · 한 문장 정의');
    s.addText(th.definition, { x: 0.7, y: 1.4, w: 11.9, h: 1.8, fontFace: FONT, fontSize: 24, bold: true, color: C.text, valign: 'top', margin: 0 });
    box(s, '🧠 ' + th.analogy, 0.7, 3.6, 11.9, 2.6, C.card, C.text, 17);
    s = slide('1부 이론 · 이전 방식과 비교');
    const cw = 12.2 / th.comparison.headers.length;
    table(s, th.comparison.headers, th.comparison.rows, 1.2, th.comparison.headers.map((_, i) => i === 0 ? Math.min(2, cw) : (12.2 - Math.min(2, cw)) / (th.comparison.headers.length - 1)), 12);
    s = slide('1부 이론 · 핵심 개념');
    const k = th.concepts.length, kw = (12.2 - 0.3 * (k - 1)) / k;
    th.concepts.forEach((c, i) => {
      const x = 0.55 + i * (kw + 0.3);
      s.addShape(pptx.ShapeType.roundRect, { x, y: 1.3, w: kw, h: 5.4, fill: { color: C.card }, line: { color: C.line }, rectRadius: 0.1 });
      s.addText(`${'①②③④⑤'[i] || '•'} ${c.title}`, { x: x + 0.2, y: 1.45, w: kw - 0.4, h: 0.7, fontFace: FONT, fontSize: 17, bold: true, color: C.cyan, margin: 0 });
      s.addText(c.body, { x: x + 0.2, y: 2.2, w: kw - 0.4, h: 4.3, fontFace: FONT, fontSize: 13, color: C.text, valign: 'top', margin: 0 });
    });
    s = slide('1부 이론 · 할 수 있는 것 / 할 수 없는 것');
    s.addText('✅ 할 수 있는 것', { x: 0.6, y: 1.25, w: 5.9, h: 0.5, fontFace: FONT, fontSize: 18, bold: true, color: C.green, margin: 0 });
    s.addText(bullets(th.can, 15), { x: 0.6, y: 1.85, w: 5.9, h: 4.9, valign: 'top', margin: 0 });
    s.addText('❌ 한계·주의', { x: 6.9, y: 1.25, w: 5.9, h: 0.5, fontFace: FONT, fontSize: 18, bold: true, color: C.red, margin: 0 });
    s.addText(bullets(th.cannot, 15), { x: 6.9, y: 1.85, w: 5.9, h: 4.9, valign: 'top', margin: 0 });
    s = slide(`1부 이론 · 비용·요금제 (${acc})`);
    s.addText(L.pricing.summary, { x: 0.55, y: 1.15, w: 12.2, h: 0.8, fontFace: FONT, fontSize: 16, bold: true, color: C.text, valign: 'top', margin: 0 });
    table(s, ['요금제', '가격', '이 기능 관련 · 혜택'], L.pricing.plans.map(p => [p.name, p.price, p.features]), 2.05, [2.3, 2.0, 7.9], 12);
    s.addText(`${L.pricing.note || ''} (확인일 ${L.pricing.checked})`, { x: 0.55, y: 6.75, w: 11.5, h: 0.45, fontFace: FONT, fontSize: 10, color: C.sub, margin: 0 });
    s = slide('1부 이론 · 윤리·저작권·보안');
    s.addText(bullets(th.safety, 16), { x: 0.7, y: 1.35, w: 11.9, h: 5.5, valign: 'top', margin: 0 });
    const sec = takeScript(/보안|윤리/); note(s, sec && sec.text);

    // 2부 실습
    const pc = L.practice;
    s = slide('2부 실습 · 완성 작품 미리보기');
    box(s, pc.preview, 0.7, 1.35, 11.9, 3.9, C.card, C.text, 16);
    box(s, '🎁 최종 결과물: ' + L.outcome, 0.7, 5.5, 11.9, 1.2, C.greenBg, C.green, 15, true);
    const bf = takeScript(/비포|애프터|비교|전환/); note(s, bf && bf.text);
    const stepSlide = (st, no, part) => {
      const sl = slide(`2부 ${part} · STEP ${no}. ${st.title}`);
      sl.addText(`${st.minutes ? st.minutes + '분 · ' : ''}${st.do}`, { x: 0.6, y: 1.2, w: 12.1, h: st.prompt ? 1.6 : 3.2, fontFace: FONT, fontSize: 17, color: C.text, valign: 'top', margin: 0 });
      let y = st.prompt ? 2.95 : 4.6;
      if (st.prompt) {
        const lines = st.prompt.split('\n').length, h = Math.min(2.6, 0.5 + lines * 0.32);
        sl.addShape(pptx.ShapeType.roundRect, { x: 0.6, y, w: 12.1, h, fill: { color: '0B1728' }, rectRadius: 0.08 });
        sl.addText(st.prompt, { x: 0.85, y: y + 0.1, w: 11.6, h: h - 0.2, fontFace: FONT, fontSize: lines > 5 ? 12 : 14, color: 'E2F3FF', valign: 'top', margin: 0 });
        y += h + 0.2;
      }
      box(sl, '결과 → ' + st.expect, 0.6, y, 12.1, 0.9, C.greenBg, C.green, 14);
      if (st.note) box(sl, '⚠️ ' + st.note, 0.6, y + 1.05, 12.1, 0.85, C.warnBg, C.warn, 12);
    };
    pc.follow.forEach((st, i) => stepSlide(st, i + 1, '따라하기'));
    pc.make_mine.forEach((st, i) => stepSlide(st, pc.follow.length + i + 1, '내 것으로'));
    s = slide('2부 실습 · 도전 과제');
    table(s, ['난이도', '미션'], pc.challenges.map(c => [c.level, c.mission]), 1.3, [1.6, 10.6], 15);

    // 3부 정리
    const wr = L.wrap;
    s = slide('3부 정리 · 작품 공유 & 확인 퀴즈');
    box(s, '🗣 ' + wr.share, 0.6, 1.2, 12.1, 1.3, C.card, C.text, 14);
    s.addText(wr.quiz.flatMap((q, i) => [
      { text: `Q${i + 1}. ${q.q}`, options: { fontFace: FONT, fontSize: 15, bold: true, color: C.text, breakLine: true } },
      { text: q.options.map((o, j) => `${'①②③④'[j]} ${o}`).join('   '), options: { fontFace: FONT, fontSize: 13, color: C.sub, paraSpaceAfter: 12, breakLine: true } }
    ]), { x: 0.6, y: 2.75, w: 12.1, h: 4.2, valign: 'top', margin: 0 });
    s = slide('3부 정리 · 퀴즈 정답');
    s.addText(wr.quiz.flatMap((q, i) => [
      { text: `Q${i + 1}. ${q.q}`, options: { fontFace: FONT, fontSize: 14, color: C.sub, breakLine: true } },
      { text: `→ ${'①②③④'[q.answer]} ${q.options[q.answer]} — ${q.explain}`, options: { fontFace: FONT, fontSize: 16, bold: true, color: C.green, paraSpaceAfter: 14, breakLine: true } }
    ]), { x: 0.6, y: 1.3, w: 12.1, h: 5.6, valign: 'top', margin: 0 });
    s = slide('3부 정리 · 평가 루브릭');
    table(s, ['기준', '상 (3점)', '중 (2점)', '하 (1점)'], (wr.rubric || MT.RUBRIC).map(r => [r.criterion, r.high, r.mid, r.low]), 1.3, [2.0, 3.8, 3.2, 3.2], 13);

    // 강사용 지도 노트
    if (ins) {
      const I = L.instructor;
      s = slide('👨‍🏫 차시별 시간표', 'ins'); table(s, ['시간', '내용', '비고'], I.timetable.map(t => [t.time, t.content, t.note || '']), 1.2, [1.8, 6.0, 4.4], 13);
      s = slide('👨‍🏫 그대로 읽어도 되는 멘트', 'ins'); table(s, ['구간', '멘트'], I.script.map(x => [x.label, x.text]), 1.2, [2.2, 10.0], 12);
      s = slide('👨‍🏫 시연 실패 대비 Plan B', 'ins'); table(s, ['상황', '대응'], I.plan_b.map(p => [p.situation, p.response]), 1.2, [4.0, 8.2], 13);
      s = slide('👨‍🏫 수강생이 자주 막히는 지점', 'ins'); table(s, ['막히는 지점', '해결법'], I.stuck.map(p => [p.issue, p.fix]), 1.2, [4.6, 7.6], 13);
      s = slide('👨‍🏫 예상 질문 & 모범 답변', 'ins'); table(s, ['질문', '답변'], I.faq.map(p => [p.q, p.a]), 1.2, [4.2, 8.0], 12);
      s = slide('👨‍🏫 레벨별 변형 가이드', 'ins'); table(s, ['대상', '변형 방법'], I.level_guide.map(g => [g.level, g.guide]), 1.2, [3.2, 9.0], 13);
      s = slide('👨‍🏫 응용 포인트 · 강의 전날 체크', 'ins');
      s.addText(bullets(I.pro_points || [], 13), { x: 0.6, y: 1.25, w: 6.0, h: 5.6, valign: 'top', margin: 0 });
      s.addText((I.day_before || []).map(t => ({ text: '☐ ' + t, options: { fontFace: FONT, fontSize: 13, color: C.text, paraSpaceAfter: 8, breakLine: true } })), { x: 6.9, y: 1.25, w: 5.9, h: 5.6, valign: 'top', margin: 0 });
    }

    // 다음에 배울 것 + 출처
    s = slide('다음에 배울 것 · 출처');
    s.addText(bullets(wr.next || [], 15), { x: 0.6, y: 1.25, w: 12.1, h: 1.8, valign: 'top', margin: 0 });
    s.addText(L.sources.map(x => ({ text: `${x.title} (확인 ${x.checked || L.checked})`, options: { hyperlink: { url: x.url }, bullet: { indent: 16 }, fontFace: FONT, fontSize: 13, color: C.cyan, paraSpaceAfter: 8, breakLine: true } })), { x: 0.6, y: 3.2, w: 12.1, h: 3.6, valign: 'top', margin: 0 });
    const cl = takeScript(/마무리/);
    note(s, [cl && cl.text, ...script.map(x => `[${x.label}] ${x.text}`)].filter(Boolean).join('\n\n'));
    return pptx;
  }

  // 서버(배포 단계)에서도 같은 함수로 PPT를 미리 만든다: scripts/build_downloads.js
  window.buildLessonPptx = build;

  window.downloadLessonPptx = async function (L, btn, mode) {
    mode = mode === 'instructor' ? 'instructor' : 'learner';
    const label = btn && btn.textContent;
    try {
      if (btn) { btn.disabled = true; btn.textContent = 'PPT 만드는 중…'; }
      await loadLib();
      await build(L, mode).writeFile({ fileName: `${L.id}-${mode === 'instructor' ? '강사용' : '학습자용'}.pptx` });
    } catch (e) {
      alert('PPT를 만들지 못했습니다: ' + e.message);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = label; }
    }
  };
})();
