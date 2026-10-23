// Quiz UI contract for existing and future lessons. Runs with Node 20 only.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'lessons.html'), 'utf8');
const pptx = fs.readFileSync(path.join(root, 'lesson-pptx.js'), 'utf8');
const standard = fs.readFileSync(path.join(root, 'docs/lesson-standard-v2.md'), 'utf8');

assert.match(html, /✅ 핵심 문제 \$\{wr\.quiz\.length\}개 풀어보기/);
assert.match(html, /class="qfeedback" role="status" aria-live="polite"/);
assert.match(html, /class="qe">정답/);
assert.match(html, /aria-pressed="false"/);
assert.match(pptx, /3부 정리 · 핵심 문제 3개 풀어보기/);
assert.match(standard, /신규 교안은 정확히 3개/);

// Catch syntax problems in inline JavaScript before deploying any lesson.
const inlineScripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)]
  .map(m => m[1]).filter(Boolean);
assert.ok(inlineScripts.length > 0, 'Inline page JavaScript missing');
for (const script of inlineScripts) new vm.Script(script);

// Exercise the real click handler extracted from lessons.html with a minimal DOM mock.
const handler = html.split('\n').find(line => line.includes("app.querySelectorAll('.q').forEach"));
assert.ok(handler, 'Common quiz event handler missing');
const classes = () => ({
  values: new Set(),
  add(...names) { for (const n of names) this.values.add(n); },
  remove(...names) { for (const n of names) this.values.delete(n); },
  toggle(name, enabled) { if (enabled) this.values.add(name); else this.values.delete(name); },
  contains(name) { return this.values.has(name); }
});
const options = Array.from({length: 4}, (_, i) => ({
  dataset: {j: String(i)},
  classList: classes(),
  attributes: {},
  setAttribute(k, v) { this.attributes[k] = v; }
}));
const feedback = {textContent: ''};
const q = {
  dataset: {a: '1'},
  classList: classes(),
  querySelectorAll(sel) { assert.equal(sel, '.opt'); return options; },
  querySelector(sel) {
    if (sel === '.qfeedback') return feedback;
    const m = sel.match(/^\.opt\[data-j="(\d)"\]$/);
    assert.ok(m, 'Unexpected selector: ' + sel);
    return options[Number(m[1])];
  }
};
vm.runInNewContext(handler, {app: {querySelectorAll: () => [q]}, String});
options[0].onclick();
assert.equal(feedback.textContent, '아쉬워요! 설명을 보고 다시 생각해 보세요.');
assert.ok(q.classList.contains('incorrect'));
assert.ok(options[0].classList.contains('wrong'));
assert.ok(options[1].classList.contains('right'));
assert.equal(options[0].attributes['aria-pressed'], 'true');
options[1].onclick();
assert.equal(feedback.textContent, '정답입니다! 잘하셨어요.');
assert.ok(q.classList.contains('correct'));
assert.ok(!q.classList.contains('incorrect'));
assert.ok(!options[0].classList.contains('wrong'));
assert.ok(options[1].classList.contains('right'));
assert.equal(options[1].attributes['aria-pressed'], 'true');
assert.equal(options[0].attributes['aria-pressed'], 'false');
options[3].onclick();
assert.equal(feedback.textContent, '아쉬워요! 설명을 보고 다시 생각해 보세요.');
assert.ok(q.classList.contains('incorrect'));
assert.ok(!q.classList.contains('correct'));
console.log('PASS: page JavaScript syntax, all-lesson quiz heading, PPT wording, accessibility and answer feedback');
