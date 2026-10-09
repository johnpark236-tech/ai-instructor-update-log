// 교안 JSON → PowerPoint(.pptx) 변환. lessons.html 의 "PPT로 다운로드" 버튼에서 사용한다.
(function () {
  const C = { navy: '07111F', band: '0E1B2E', cyan: '0891B2', cyanL: '6EE7FF', text: '1E293B', sub: '475569', green: '047857', greenBg: 'ECFDF5', warn: 'B45309', line: 'CBD5E1', card: 'F1F5F9' };
  const FONT = 'Malgun Gothic';
  let libPromise;

  function loadLib() {
    if (window.PptxGenJS) return Promise.resolve();
    if (!libPromise) {
      libPromise = new Promise((ok, fail) => {
        const s = document.createElement('script');
        s.src = './vendor/pptxgen.bundle.js';
        s.onload = ok;
        s.onerror = () => { libPromise = null; fail(new Error('PPT 라이브러리를 불러오지 못했습니다.')); };
        document.head.appendChild(s);
      });
    }
    return libPromise;
  }

  function header(pptx, L, title, pageNo) {
    const s = pptx.addSlide();
    s.background = { color: 'FFFFFF' };
    s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 1.0, fill: { color: C.navy } });
    s.addText(title, { x: 0.6, y: 0.12, w: 10.5, h: 0.76, fontFace: FONT, fontSize: 26, bold: true, color: 'FFFFFF', valign: 'middle', margin: 0 });
    s.addText(`${L.tool} · ${L.category}`, { x: 9.2, y: 0.12, w: 3.55, h: 0.76, fontFace: FONT, fontSize: 12, color: C.cyanL, align: 'right', valign: 'middle', margin: 0 });
    s.addText(String(pageNo), { x: 12.2, y: 7.0, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 10, color: C.sub, align: 'right', margin: 0 });
    return s;
  }

  function bullets(items, size, color) {
    return items.map(t => ({ text: t, options: { bullet: { indent: 18 }, fontFace: FONT, fontSize: size, color: color || C.text, paraSpaceAfter: 8, breakLine: true } }));
  }

  function build(L) {
    const pptx = new window.PptxGenJS();
    pptx.layout = 'LAYOUT_WIDE';
    pptx.title = L.title;
    pptx.author = 'AI 실습 교안';
    let n = 1;

    // 1. 표지
    const cover = pptx.addSlide();
    cover.background = { color: C.navy };
    cover.addShape(pptx.ShapeType.roundRect, { x: 0.8, y: 0.55, w: 1.9, h: 0.5, fill: { color: L.type === 'new' ? '70E1A1' : '6EE7FF' }, rectRadius: 0.08 });
    cover.addText(L.type === 'new' ? '신규 AI' : '기존 AI', { x: 0.8, y: 0.55, w: 1.9, h: 0.5, fontFace: FONT, fontSize: 18, bold: true, color: '07111F', align: 'center', valign: 'middle', margin: 0 });
    cover.addText(`${L.category} · ${L.tool} · ${L.company}`, { x: 0.8, y: 1.2, w: 11.7, h: 0.5, fontFace: FONT, fontSize: 16, bold: true, color: C.cyanL, charSpacing: 2, margin: 0 });
    cover.addText(L.title, { x: 0.8, y: 1.9, w: 11.7, h: 2.0, fontFace: FONT, fontSize: 40, bold: true, color: 'FFFFFF', valign: 'top', margin: 0 });
    cover.addText(L.summary, { x: 0.8, y: 4.1, w: 11.0, h: 1.4, fontFace: FONT, fontSize: 20, color: 'C0CDE0', valign: 'top', margin: 0 });
    cover.addText(`${L.type === 'new' ? '신규 AI' : '기존 AI 새 기능'}   |   ${L.level} · 약 ${L.minutes}분   |   발표 ${L.released}   |   작성 ${L.created_at}`, { x: 0.8, y: 6.3, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 13, color: '91A6C2', margin: 0 });

    // 2. 왜 지금 + 준비물
    let s = header(pptx, L, '왜 지금 배우나 · 준비물', ++n);
    s.addText(L.why, { x: 0.6, y: 1.4, w: 6.0, h: 5.3, fontFace: FONT, fontSize: 21, color: C.text, valign: 'top', margin: 0, paraSpaceAfter: 6 });
    s.addShape(pptx.ShapeType.roundRect, { x: 7.0, y: 1.4, w: 5.7, h: 5.3, fill: { color: C.card }, line: { color: C.line }, rectRadius: 0.12 });
    s.addText('준비물', { x: 7.3, y: 1.6, w: 5.1, h: 0.5, fontFace: FONT, fontSize: 18, bold: true, color: C.cyan, margin: 0 });
    s.addText(bullets(L.prerequisites, 19), { x: 7.3, y: 2.2, w: 5.1, h: 4.3, valign: 'top', margin: 0 });

    // 2-1. 요금제별 기능
    if (L.pricing && L.pricing.plans && L.pricing.plans.length) {
      const P = L.pricing, acc = { free: '무료', freemium: '무료+유료', paid: '유료' }[P.access] || '';
      s = header(pptx, L, `요금제별 기능 · 혜택${acc ? ' (' + acc + ')' : ''}`, ++n);
      s.addText(P.summary, { x: 0.6, y: 1.25, w: 12.1, h: 0.9, fontFace: FONT, fontSize: 17, bold: true, color: C.text, valign: 'top', margin: 0 });
      const rows = [[{ text: '요금제', options: { bold: true, color: 'FFFFFF', fill: { color: C.cyan } } }, { text: '가격', options: { bold: true, color: 'FFFFFF', fill: { color: C.cyan } } }, { text: '기능 · 혜택', options: { bold: true, color: 'FFFFFF', fill: { color: C.cyan } } }]]
        .concat(P.plans.map((x, i) => [{ text: x.name, options: { bold: true } }, { text: x.price }, { text: x.features }].map(c => ({ text: c.text, options: Object.assign({ fill: { color: i % 2 ? 'FFFFFF' : C.card } }, c.options || {}) }))));
      s.addTable(rows, { x: 0.6, y: 2.2, w: 12.1, colW: [2.4, 1.9, 7.8], fontFace: FONT, fontSize: 13, color: C.text, border: { type: 'solid', pt: 0.75, color: C.line }, valign: 'middle', margin: 0.08 });
      s.addText(`${P.note || ''} (확인일 ${P.checked})`, { x: 0.6, y: 6.75, w: 11.5, h: 0.4, fontFace: FONT, fontSize: 10, color: C.sub, margin: 0 });
    }

    // 3. 단계별 따라 하기 (한 장에 한 단계)
    L.steps.forEach((st, i) => {
      s = header(pptx, L, `따라 하기 ${i + 1}/${L.steps.length} — ${st.title}`, ++n);
      s.addShape(pptx.ShapeType.ellipse, { x: 0.6, y: 1.45, w: 0.8, h: 0.8, fill: { color: C.cyan } });
      s.addText(String(i + 1), { x: 0.6, y: 1.45, w: 0.8, h: 0.8, fontFace: FONT, fontSize: 24, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0 });
      s.addText(st.do, { x: 1.7, y: 1.4, w: 11.0, h: 3.2, fontFace: FONT, fontSize: 22, color: C.text, valign: 'top', margin: 0 });
      s.addShape(pptx.ShapeType.roundRect, { x: 1.7, y: 4.9, w: 11.0, h: 1.8, fill: { color: C.greenBg }, line: { color: '6EE7B7' }, rectRadius: 0.12 });
      s.addText([{ text: '결과  ', options: { bold: true } }, { text: st.expect }], { x: 2.0, y: 5.0, w: 10.4, h: 1.6, fontFace: FONT, fontSize: 18, color: C.green, valign: 'middle', margin: 0 });
    });

    // 4. 실습 과제
    s = header(pptx, L, '실습 과제', ++n);
    s.addText(L.practice.task, { x: 0.6, y: 1.4, w: 12.1, h: 1.8, fontFace: FONT, fontSize: 22, bold: true, color: C.text, valign: 'top', margin: 0 });
    if (L.practice.sample_input) {
      s.addText('연습용 입력', { x: 0.6, y: 3.4, w: 6, h: 0.4, fontFace: FONT, fontSize: 14, bold: true, color: C.cyan, margin: 0 });
      s.addShape(pptx.ShapeType.roundRect, { x: 0.6, y: 3.9, w: 12.1, h: 2.8, fill: { color: C.card }, line: { color: C.line }, rectRadius: 0.12 });
      s.addText(L.practice.sample_input, { x: 0.9, y: 4.0, w: 11.5, h: 2.6, fontFace: FONT, fontSize: 18, color: C.text, valign: 'middle', margin: 0 });
    }

    // 5. 체크리스트
    s = header(pptx, L, '실습 체크리스트', ++n);
    s.addText(L.practice.checklist.map(t => ({ text: '☐  ' + t, options: { fontFace: FONT, fontSize: 22, color: C.text, paraSpaceAfter: 16, breakLine: true } })), { x: 0.8, y: 1.5, w: 11.8, h: 5.3, valign: 'top', margin: 0 });

    // 6. 수업 팁 + 주의할 점
    s = header(pptx, L, '수업에 쓸 때 · 주의할 점', ++n);
    s.addText('수업에 쓸 때', { x: 0.6, y: 1.35, w: 5.9, h: 0.5, fontFace: FONT, fontSize: 18, bold: true, color: C.cyan, margin: 0 });
    s.addText(bullets(L.teaching_tips.length ? L.teaching_tips : ['—'], 19), { x: 0.6, y: 1.95, w: 5.9, h: 4.9, valign: 'top', margin: 0 });
    s.addText('주의할 점', { x: 6.9, y: 1.35, w: 5.9, h: 0.5, fontFace: FONT, fontSize: 18, bold: true, color: C.warn, margin: 0 });
    s.addText(bullets(L.pitfalls, 19), { x: 6.9, y: 1.95, w: 5.9, h: 4.9, valign: 'top', margin: 0 });

    // 7. 퀴즈 → 정답
    s = header(pptx, L, '확인 퀴즈', ++n);
    s.addText(L.quiz.map((q, i) => ({ text: `Q${i + 1}. ${q.q}`, options: { fontFace: FONT, fontSize: 22, color: C.text, paraSpaceAfter: 20, breakLine: true } })), { x: 0.8, y: 1.5, w: 11.8, h: 5.3, valign: 'top', margin: 0 });
    s = header(pptx, L, '퀴즈 정답', ++n);
    s.addText(L.quiz.flatMap((q, i) => [
      { text: `Q${i + 1}. ${q.q}`, options: { fontFace: FONT, fontSize: 16, color: C.sub, breakLine: true } },
      { text: `→ ${q.a}`, options: { fontFace: FONT, fontSize: 20, bold: true, color: C.green, paraSpaceAfter: 16, breakLine: true } }
    ]), { x: 0.8, y: 1.5, w: 11.8, h: 5.3, valign: 'top', margin: 0 });

    // 8. 출처
    s = header(pptx, L, '출처', ++n);
    s.addText(L.sources.map(src => ({ text: src.title, options: { hyperlink: { url: src.url }, bullet: { indent: 18 }, fontFace: FONT, fontSize: 20, color: C.cyan, paraSpaceAfter: 14, breakLine: true } })), { x: 0.6, y: 1.5, w: 12.1, h: 5.2, valign: 'top', margin: 0 });

    return pptx;
  }

  window.downloadLessonPptx = async function (L, btn) {
    const label = btn && btn.textContent;
    try {
      if (btn) { btn.disabled = true; btn.textContent = 'PPT 만드는 중…'; }
      await loadLib();
      await build(L).writeFile({ fileName: `${L.id}.pptx` });
    } catch (e) {
      alert('PPT를 만들지 못했습니다: ' + e.message);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = label; }
    }
  };
})();
