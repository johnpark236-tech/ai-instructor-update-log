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
    L = JSON.parse(JSON.stringify(L), (key, value) => typeof value === 'string' ? value.replace(/비포/g, 'Before').replace(/애프터/g, 'After') : value);
    const MT = window.LESSON_META, ins = mode === 'instructor';
    const pptx = new window.PptxGenJS();
    pptx.layout = 'LAYOUT_WIDE'; pptx.title = L.title; pptx.author = 'AI 실습 교안';
    const script = (L.instructor.script || []).slice();
    const takeScript = re => { const i = script.findIndex(s => re.test(s.label)); return i < 0 ? null : script.splice(i, 1)[0]; };
    let n = 0;
    // 여러 내용이 이어진 글 → '1) …' 줄바꿈 목록
    const NT = t => { const r = MT.splitItems(t); return r.items.length < 2 ? String(t || '') : (r.lead ? r.lead + '\n' : '') + r.items.map((x, i) => `${i + 1}) ${x}`).join('\n'); };
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
    const bullets = (items, size, color) => items.map(t => ({ text: t, options: { bullet: { type: 'number', numberType: 'arabicParenR', indent: 22 }, fontFace: FONT, fontSize: size, color: color || C.text, paraSpaceAfter: 6, breakLine: true } }));
    function table(s, head, rows, y, colW, size) {
      const hdr = head.map(h => ({ text: h, options: { bold: true, color: 'FFFFFF', fill: { color: C.cyan } } }));
      const body = rows.map((r, i) => r.map((c, j) => ({ text: (j === 0 && rows.length > 1 ? `${i + 1}) ` : '') + NT(c), options: { fill: { color: i % 2 ? 'FFFFFF' : C.card }, bold: j === 0 } })));
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
    cover.addText(NT(L.summary), { x: 0.8, y: 3.7, w: 11.6, h: 1.4, fontFace: FONT, fontSize: 17, color: 'C0CDE0', valign: 'top', margin: 0 });
    cover.addText(MT.levelBadges(L).join('   '), { x: 0.8, y: 5.4, w: 11.8, h: 0.4, fontFace: FONT, fontSize: 14, color: 'FFFFFF', margin: 0 });
    cover.addText(`${L.company} ${L.tool} — ${L.feature}  |  출시 ${L.released}  |  기준일 ${L.checked} · 재검토 ${L.review_by}  |  ${MT.totalMinutes(L)}분`, { x: 0.8, y: 6.3, w: 11.8, h: 0.4, fontFace: FONT, fontSize: 12, color: '91A6C2', margin: 0 });
    const op = takeScript(/오프닝/); note(cover, op && op.text);

    // 한눈에 보기 (그림 우선 요약)
    const G = L.glance;
    if (G) {
      let g = slide('⚡ 한눈에 보기');
      g.addText(`${G.emoji}  ${G.one_liner}`, { x: 0.55, y: 1.15, w: 12.2, h: 0.75, fontFace: FONT, fontSize: 26, bold: true, color: C.text, margin: 0 });
      const benefitReady = !!(G.what && Array.isArray(G.benefits) && G.benefits.length === 3 && G.benefits.every(b => b && b.title && b.text));
      if (benefitReady) {
        g.addText('이런 기능이에요', {x:0.55,y:1.95,w:12.2,h:0.3,fontFace:FONT,fontSize:15,bold:true,color:C.cyan,margin:0});
        g.addText(G.what, {x:0.55,y:2.3,w:12.2,h:0.75,fontFace:FONT,fontSize:22,bold:true,color:C.text,margin:0});
        g.addText('이런 점이 좋아요', {x:0.55,y:3.1,w:12.2,h:0.3,fontFace:FONT,fontSize:15,bold:true,color:C.cyan,margin:0});
        const bw=(12.2-0.5)/3;
        G.benefits.forEach((b,i)=>{
          const x=0.55+i*(bw+0.25);
          g.addShape(pptx.ShapeType.roundRect,{x,y:3.55,w:bw,h:1.9,fill:{color:C.card},line:{color:C.line},rectRadius:0.12});
          g.addText(b.icon+' '+b.title,{x:x+0.18,y:3.75,w:bw-0.36,h:0.5,fontFace:FONT,fontSize:20,bold:true,color:C.text,margin:0});
          g.addText(b.text,{x:x+0.18,y:4.35,w:bw-0.36,h:0.85,fontFace:FONT,fontSize:17,color:C.sub,margin:0});
        });
        g.addText('이런 분께  '+G.for_whom,{x:0.55,y:5.7,w:12.2,h:0.5,fontFace:FONT,fontSize:18,bold:true,color:C.green,margin:0});
        g.addText(`⏱ ${MT.totalMinutes(L)}분   💳 ${acc}   📅 출시 ${L.released}   🎯 ${L.learner_levels.map(x=>MT.LEVEL[x]+x).join(' ')}`,{x:0.55,y:6.45,w:12.2,h:0.4,fontFace:FONT,fontSize:13,color:C.sub,margin:0});
        const flowSlide=slide('🧭 실습 흐름');
        table(flowSlide,['단계','설명'],G.cards.map(c=>[c.icon+' '+c.title,c.text]),1.3,[4.1,8.1],18);
        box(flowSlide,'🎁 오늘 만들 작품\n'+NT(L.outcome),0.55,5.1,12.2,1.5,C.greenBg,C.green,15,true);
      } else {
      box(g, '🎁 오늘 만들 작품\n' + NT(L.outcome), 0.55, 1.95, 12.2, 1.4, C.greenBg, C.green, 13, true);
      const cn = G.cards.length, cw2 = (12.2 - 0.25 * (cn - 1)) / cn;
      G.cards.forEach((c, i) => {
        const x = 0.55 + i * (cw2 + 0.25);
        g.addShape(pptx.ShapeType.roundRect, { x, y: 3.5, w: cw2, h: 2.7, fill: { color: C.card }, line: { color: C.line }, rectRadius: 0.12 });
        g.addText(c.icon, { x, y: 3.6, w: cw2, h: 1.0, fontSize: 40, align: 'center', margin: 0 });
        g.addText(`${i + 1}) ${c.title}`, { x: x + 0.15, y: 4.55, w: cw2 - 0.3, h: 0.55, fontFace: FONT, fontSize: 18, bold: true, color: C.text, align: 'center', margin: 0 });
        g.addText(c.text, { x: x + 0.15, y: 5.1, w: cw2 - 0.3, h: 1.0, fontFace: FONT, fontSize: 13, color: C.sub, align: 'center', valign: 'top', margin: 0 });
      });
      g.addText(`⏱ ${MT.totalMinutes(L)}분   💳 ${acc}   📅 출시 ${L.released}   🎯 ${MT.levelBadges(L).join(' ')}`, { x: 0.55, y: 6.35, w: 12.2, h: 0.45, fontFace: FONT, fontSize: 13, color: C.sub, margin: 0 });

      }

      g = slide('🔄 ' + G.diagram.title);
      const nn = G.diagram.nodes.length, gap = 0.55, nw = (12.2 - gap * (nn - 1)) / nn;
      G.diagram.nodes.forEach((nd, i) => {
        const x = 0.55 + i * (nw + gap);
        g.addShape(pptx.ShapeType.roundRect, { x, y: 1.3, w: nw, h: 1.9, fill: { color: 'E0F7FF' }, line: { color: C.cyan, width: 1.5 }, rectRadius: 0.12 });
        g.addText(nd.icon, { x, y: 1.4, w: nw, h: 0.95, fontSize: 34, align: 'center', margin: 0 });
        g.addText(`${i + 1}) ${nd.label}`, { x: x + 0.1, y: 2.35, w: nw - 0.2, h: 0.75, fontFace: FONT, fontSize: 15, bold: true, color: C.text, align: 'center', valign: 'middle', margin: 0 });
        if (i < nn - 1) g.addShape(pptx.ShapeType.rightArrow, { x: x + nw + 0.08, y: 2.0, w: gap - 0.16, h: 0.45, fill: { color: C.cyan }, line: { color: C.cyan } });
      });
      const ba = G.before_after;
      g.addShape(pptx.ShapeType.roundRect, { x: 0.55, y: 3.55, w: 5.7, h: 1.9, fill: { color: 'F4F1F8' }, line: { color: 'C4B5D9' }, rectRadius: 0.12 });
      g.addText([{ text: '😐 ' + ba.before.label, options: { bold: true, fontSize: 16, breakLine: true } }, { text: ba.before.text, options: { fontSize: 14 } }], { x: 0.8, y: 3.65, w: 5.2, h: 1.7, fontFace: FONT, color: C.text, valign: 'middle', margin: 0 });
      g.addShape(pptx.ShapeType.rightArrow, { x: 6.4, y: 4.25, w: 0.55, h: 0.5, fill: { color: C.cyan }, line: { color: C.cyan } });
      g.addShape(pptx.ShapeType.roundRect, { x: 7.05, y: 3.55, w: 5.7, h: 1.9, fill: { color: C.greenBg }, line: { color: '6EE7B7' }, rectRadius: 0.12 });
      g.addText([{ text: '😀 ' + ba.after.label, options: { bold: true, fontSize: 16, breakLine: true } }, { text: ba.after.text, options: { fontSize: 14 } }], { x: 7.3, y: 3.65, w: 5.2, h: 1.7, fontFace: FONT, color: C.green, valign: 'middle', margin: 0 });
      const cw3 = (12.2 - 0.25 * 2) / 3;
      G.cautions.forEach((c, i) => box(g, `⚠️ ${i + 1}) ${c}`, 0.55 + i * (cw3 + 0.25), 5.75, cw3, 0.9, C.warnBg, C.warn, 13, true));
    }

    // PART 1 요약본 — 표·그래프
    if (G) {
      let sm = slide('📊 요약본 · 핵심 요약 / 기능·혜택');
      const mn0 = L.minutes, tot0 = MT.totalMinutes(L);
      const kvRows = [['도구', `${L.company} ${L.tool}`], ['기능', L.feature], ['구분', kind + (MT.isPast(L) ? ' · 지난 기능' : '')], ['결과물', L.outcome],
        ['요금', `${acc} — ${L.pricing.summary}`], ['시간', `${tot0}분 (이론 ${mn0.theory} · 실습 ${mn0.practice} · 정리 ${mn0.wrap})`], ['출시', L.released]];
      sm.addTable([[{ text: '항목', options: { bold: true, color: 'FFFFFF', fill: { color: C.cyan } } }, { text: '내용', options: { bold: true, color: 'FFFFFF', fill: { color: C.cyan } } }],
        ...kvRows.map((r, i) => r.map((c, j) => ({ text: j === 0 ? `${i + 1}) ${c}` : NT(c), options: { fill: { color: i % 2 ? 'FFFFFF' : C.card }, bold: j === 0 } })))],
        { x: 0.55, y: 1.2, w: 6.3, colW: [1.2, 5.1], fontFace: FONT, fontSize: 11, color: C.text, border: { type: 'solid', pt: 0.75, color: C.line }, valign: 'middle', margin: 0.06 });
      const benefits=Array.isArray(G.benefits)&&G.benefits.length===3?G.benefits:G.cards;
      sm.addTable([[{ text: G.what?'좋아지는 점':'기능', options: { bold: true, color: 'FFFFFF', fill: { color: C.cyan } } }, { text: G.what?'설명':'혜택', options: { bold: true, color: 'FFFFFF', fill: { color: C.cyan } } }],
        ...benefits.map((c, i) => [{ text: `${i + 1}) ${c.icon} ${c.title}`, options: { bold: true, fill: { color: i % 2 ? 'FFFFFF' : C.card } } }, { text: c.text, options: { fill: { color: i % 2 ? 'FFFFFF' : C.card } } }])],
        { x: 7.1, y: 1.2, w: 5.65, colW: [2.25, 3.4], fontFace: FONT, fontSize: 13, color: C.text, border: { type: 'solid', pt: 0.75, color: C.line }, valign: 'middle', margin: 0.08 });

      sm = slide('📊 요약본 · 요금·시간 그래프');
      const ps = MT.priceSeries(L.pricing), half = ps ? 6.0 : 12.2;
      if (ps) {
        const cur = ps.cur, lab = r => r.x.name, ok = ps.ok.slice().reverse();
        sm.addText(`💳 요금제별 월 가격 (${cur === 'KRW' ? '원' : '달러'})`, { x: 0.55, y: 1.15, w: 6, h: 0.45, fontFace: FONT, fontSize: 15, bold: true, color: C.text, margin: 0 });
        sm.addChart(pptx.ChartType.bar, [{ name: '월 가격', labels: ok.map(lab), values: ok.map(r => r.p.v) }], {
          x: 0.45, y: 1.6, w: 6.2, h: 4.2, barDir: 'bar', chartColors: ['3987E5'], barGapWidthPct: 60, showLegend: false,
          showValue: true, dataLabelFontSize: 12, dataLabelColor: C.text, dataLabelFormatCode: cur === 'KRW' ? '₩#,##0' : '$#,##0.##',
          catAxisLabelFontSize: 12, catAxisLabelColor: C.text, catAxisLabelFontFace: FONT, valAxisHidden: true, valGridLine: { style: 'none' }, catAxisLineShow: false
        });
        const fn = [`첫 금액 기준 · 연간 할인·지역 가격은 요금표 참고`]; if (ps.skip.length) fn.push('금액 미표시: ' + ps.skip.map(r => r.x.name).join(', '));
        if (ps.ok.some(r => /부터|~|확인 필요/.test(r.x.price))) fn.push('일부 금액은 시작가·확인 필요');
        sm.addText(fn.join(' · '), { x: 0.55, y: 5.9, w: 6, h: 0.6, fontFace: FONT, fontSize: 10, color: C.sub, valign: 'top', margin: 0 });
      }
      const tx = ps ? 7.0 : 0.55, tw = ps ? 5.75 : 12.2;
      sm.addText(`⏱ 수업 시간 배분 (총 ${tot0}분)`, { x: tx, y: 1.15, w: tw, h: 0.45, fontFace: FONT, fontSize: 15, bold: true, color: C.text, margin: 0 });
      sm.addChart(pptx.ChartType.bar, [['이론', mn0.theory], ['실습', mn0.practice], ['정리', mn0.wrap]].map(([nm, v]) => ({ name: `${nm} ${v}분`, labels: ['시간'], values: [v || 0] })), {
        x: tx - 0.1, y: 1.6, w: tw + 0.2, h: 1.9, barDir: 'bar', barGrouping: 'stacked', chartColors: ['3987E5', 'D95926', '199E70'], barGapWidthPct: 20,
        showLegend: true, legendPos: 'b', legendFontSize: 12, legendFontFace: FONT, showValue: true, dataLabelColor: 'FFFFFF', dataLabelFontSize: 12, dataLabelFontBold: true,
        catAxisHidden: true, valAxisHidden: true, valGridLine: { style: 'none' }
      });
      const ba = G.before_after;
      sm.addTable([[{ text: '😐 ' + ba.before.label, options: { bold: true, color: '5B21B6', fill: { color: 'F4F1F8' } } }, { text: '😀 ' + ba.after.label, options: { bold: true, color: C.green, fill: { color: C.greenBg } } }],
        [ba.before.text, ba.after.text]], { x: tx, y: 3.8, w: tw, colW: [tw / 2, tw / 2], fontFace: FONT, fontSize: 12, color: C.text, border: { type: 'solid', pt: 0.75, color: C.line }, valign: 'top', margin: 0.08 });
      sm.addText(G.cautions.map((c, i) => `⚠️ ${i + 1}) ${c}`).join('\n'), { x: tx, y: 5.5, w: tw, h: 1.2, fontFace: FONT, fontSize: 12, color: C.warn, valign: 'top', margin: 0 });

      // PART 3 구분 장
      const dv = pptx.addSlide(); n++;
      dv.background = { color: C.navy };
      dv.addText('📖 자세한 설명', { x: 0.8, y: 2.6, w: 11.8, h: 1.2, fontFace: FONT, fontSize: 40, bold: true, color: 'FFFFFF', margin: 0 });
      dv.addText('메타정보 · 개념 · 비교 · 실습 단계 · 요금 상세 · 윤리 · 평가 · 출처', { x: 0.8, y: 3.8, w: 11.8, h: 0.6, fontFace: FONT, fontSize: 18, color: 'C0CDE0', margin: 0 });
    }

    // 메타정보
    let s = slide('📋 교안 메타정보');
    table(s, ['항목', '내용'], [
      ['대상 배지', MT.levelBadges(L).join('  ')], ['직업군', L.jobs.map(j => `${j} ${MT.JOB[j]}`).join(', ')],
      ['카테고리', L.categories.map(c => `${c} ${MT.CAT[c]}`).join(' · ')], ['기능 출시일', L.released],
      ['필요 요금제', `${acc} — ${L.pricing.summary}`],
      ['소요 시간', `이론 ${L.minutes.theory}분 + 실습 ${L.minutes.practice}분 + 정리 ${L.minutes.wrap}분`],
      ['준비물', L.prerequisites.map((x, i) => `${i + 1}) ${x}`).join('\n')], ['최종 결과물', L.outcome]
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
      s.addText(NT(c.body), { x: x + 0.2, y: 2.2, w: kw - 0.4, h: 4.3, fontFace: FONT, fontSize: 13, color: C.text, valign: 'top', margin: 0 });
    });
    s = slide('1부 이론 · 할 수 있는 것 / 할 수 없는 것');
    s.addText('✅ 할 수 있는 것', { x: 0.6, y: 1.25, w: 5.9, h: 0.5, fontFace: FONT, fontSize: 18, bold: true, color: C.green, margin: 0 });
    s.addText(bullets(th.can, 15), { x: 0.6, y: 1.85, w: 5.9, h: 4.9, valign: 'top', margin: 0 });
    s.addText('❌ 한계·주의', { x: 6.9, y: 1.25, w: 5.9, h: 0.5, fontFace: FONT, fontSize: 18, bold: true, color: C.red, margin: 0 });
    s.addText(bullets(th.cannot, 15), { x: 6.9, y: 1.85, w: 5.9, h: 4.9, valign: 'top', margin: 0 });
    s = slide(`1부 이론 · 비용·요금제 (${acc})`);
    s.addText(NT(L.pricing.summary), { x: 0.55, y: 1.15, w: 12.2, h: 0.8, fontFace: FONT, fontSize: 16, bold: true, color: C.text, valign: 'top', margin: 0 });
    table(s, ['요금제', '가격', '이 기능 관련 · 혜택'], L.pricing.plans.map(p => [p.name, p.price, p.features]), 2.05, [2.3, 2.0, 7.9], 12);
    s.addText(`${L.pricing.note || ''} (확인일 ${L.pricing.checked})`, { x: 0.55, y: 6.75, w: 11.5, h: 0.45, fontFace: FONT, fontSize: 10, color: C.sub, margin: 0 });
    s = slide('1부 이론 · 윤리·저작권·보안');
    s.addText(bullets(th.safety, 16), { x: 0.7, y: 1.35, w: 11.9, h: 5.5, valign: 'top', margin: 0 });
    const sec = takeScript(/보안|윤리/); note(s, sec && sec.text);

    // 2부 실습
    const pc = L.practice;
    s = slide('2부 실습 · 완성 작품 미리보기');
    box(s, NT(pc.preview), 0.7, 1.35, 11.9, 3.9, C.card, C.text, 16);
    box(s, '🎁 최종 결과물\n' + NT(L.outcome), 0.7, 5.5, 11.9, 1.2, C.greenBg, C.green, 15, true);
    const bf = takeScript(/Before|After|비교|전환/i); note(s, bf && bf.text);
    const stepSlide = (st, no, part) => {
      const sl = slide(`2부 ${part} · STEP ${no}. ${st.title}`);
      sl.addText(`${st.minutes ? st.minutes + '분 · ' : ''}${NT(st.do)}`, { x: 0.6, y: 1.2, w: 12.1, h: st.prompt ? 1.0 : 3.2, fontFace: FONT, fontSize: 17, color: C.text, valign: 'top', margin: 0 });
      if(st.prompt){
        const dest=window.LESSON_INPUTS?.get(L,st,no-1);
        const input=dest?('입력: '+dest.label+' → '+dest.location):'[확인 필요] 입력 위치 미등록';
        sl.addText(input, {x:0.6,y:2.28,w:12.1,h:0.55,fontFace:FONT,fontSize:11,color:C.cyan,margin:0,fit:'shrink',...(dest?.url?{hyperlink:{url:dest.url}}:{})});
        if(dest)note(sl,window.LESSON_INPUTS.text(dest));
      }
      let y = st.prompt ? 2.95 : 4.6;
      if (st.prompt) {
        const lines = st.prompt.split('\n').length, h = Math.min(2.6, 0.5 + lines * 0.32);
        sl.addShape(pptx.ShapeType.roundRect, { x: 0.6, y, w: 12.1, h, fill: { color: '0B1728' }, rectRadius: 0.08 });
        sl.addText(st.prompt, { x: 0.85, y: y + 0.1, w: 11.6, h: h - 0.2, fontFace: FONT, fontSize: lines > 5 ? 12 : 14, color: 'E2F3FF', valign: 'top', margin: 0 });
        y += h + 0.2;
      }
      box(sl, '결과 → ' + NT(st.expect), 0.6, y, 12.1, 0.9, C.greenBg, C.green, 14);
      if (st.note) box(sl, '⚠️ ' + NT(st.note), 0.6, y + 1.05, 12.1, 0.85, C.warnBg, C.warn, 12);
    };
    pc.follow.forEach((st, i) => stepSlide(st, i + 1, '따라하기'));
    pc.make_mine.forEach((st, i) => stepSlide(st, pc.follow.length + i + 1, '내 것으로'));
    s = slide('2부 실습 · 도전 과제');
    table(s, ['난이도', '미션'], pc.challenges.map(c => [c.level, c.mission]), 1.3, [1.6, 10.6], 15);

    // 3부 정리
    const wr = L.wrap;
    s = slide('3부 정리 · 핵심 문제 3개 풀어보기');
    box(s, '🗣 ' + NT(wr.share), 0.6, 1.2, 12.1, 1.3, C.card, C.text, 14);
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

