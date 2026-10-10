// 배포 단계에서 모든 교안의 PPT(학습자용·강사용)와 프롬프트 모음을 미리 만들어 downloads/ 에 저장한다.
// 휴대폰 앱 내 브라우저(카카오톡 등)는 브라우저 안에서 만든 파일(blob) 저장을 지원하지 않기 때문에,
// 일반 파일 링크로 내려받을 수 있게 한다.
// 사용법: npm install --no-save pptxgenjs@3.12.0 && node scripts/build_downloads.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'downloads');
global.window = global;
global.PptxGenJS = require('pptxgenjs');
global.document = undefined;
for (const f of ['lesson-meta.js', 'lesson-pptx.js']) {
  vm.runInThisContext(fs.readFileSync(path.join(ROOT, f), 'utf8'), { filename: f });
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const files = fs.readdirSync(path.join(ROOT, 'lessons')).filter(f => f.endsWith('.json')).sort();
  let n = 0;
  for (const f of files) {
    const L = JSON.parse(fs.readFileSync(path.join(ROOT, 'lessons', f), 'utf8'));
    for (const mode of ['learner', 'instructor']) {
      const buf = await window.buildLessonPptx(L, mode).write({ outputType: 'nodebuffer' });
      fs.writeFileSync(path.join(OUT, `${L.id}-${mode}.pptx`), buf);
      n++;
    }
    fs.writeFileSync(path.join(OUT, `${L.id}-prompts.txt`), '﻿' + window.LESSON_META.promptText(L), 'utf8');
  }
  console.log(`downloads/: 교안 ${files.length}개, PPT ${n}개 생성`);
})().catch(e => { console.error(e); process.exit(1); });
