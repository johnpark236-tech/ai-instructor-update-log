const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=process.env.LESSON_INPUT_TEST_ROOT||path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const context={URL,console};context.window=context;context.globalThis=context;vm.createContext(context);
for(const file of ['lesson-meta.js','lesson-inputs.js'])vm.runInContext(read(file),context,{filename:file});
const api=context.LESSON_INPUTS;
let lessons=0,prompts=0;const kinds={};
for(const f of fs.readdirSync(path.join(root,'lessons')).filter(f=>f.endsWith('.json'))){
 const L=JSON.parse(read('lessons/'+f));lessons++;
 const ss=[...L.practice.follow,...L.practice.make_mine];
 ss.forEach((s,i)=>{if(!s.prompt)return;const t=api.get(L,s,i);assert.ok(t,`${L.id} STEP ${i+1}: missing actual input destination`);assert.ok(t.location.trim());if(t.url)assert.equal(new URL(t.url).protocol,'https:');prompts++;kinds[t.kind]=(kinds[t.kind]||0)+1});
 const txt=context.LESSON_META.promptText(L);if(ss.some(s=>s.prompt))assert.ok(txt.includes('입력할 곳:'),L.id+' TXT missing input instructions');
}
const load=id=>JSON.parse(read('lessons/'+id+'.json'));
const get=(id,n)=>{const L=load(id);return api.get(L,[...L.practice.follow,...L.practice.make_mine][n-1],n-1)};
assert.equal(get('AI-2026-10-CAT08-005',1).url,'https://gemini.google.com/');
assert.equal(get('AI-2026-10-CAT08-005',2).url,'https://mail.google.com/');
assert.equal(get('AI-2026-10-CAT08-005',3).url,'https://studio.workspace.google.com/');
assert.equal(get('AI-2026-10-CAT08-005',5).url,'https://mail.google.com/');
assert.equal(get('AI-2026-10-CAT08-005',7).url,'https://studio.workspace.google.com/');
assert.match(get('AI-2026-10-CAT08-005',3).note,/Workspace Experiments/);
assert.equal(get('AI-2026-10-CAT04-008',4).url,'https://claude.ai/'); // Runway is a connected tool; prompt belongs in Claude
assert.equal(get('AI-2026-10-CAT03-023',4).url,'https://word.cloud.microsoft/');
assert.equal(get('AI-2026-10-CAT03-023',6).url,'https://powerpoint.cloud.microsoft/');
assert.equal(get('AI-2026-10-CAT07-019',1).url,null); // CLI setup isn't a web prompt
assert.equal(get('AI-2026-10-CAT08-021',3).url,'https://x.com/');
assert.equal(api.safe({label:'bad',location:'input',url:'javascript:alert(1)'}),null);
assert.equal(api.safe({label:'bad',location:'input',url:'https://user:secret@example.com/'}),null);
assert.equal(api.get({id:'new'},{title:'Gmail → Drive',prompt:'Gemini'},0),null); // Never infer destination from mentioned tools
assert.equal(api.get({id:'new'},{title:'x',prompt:'Gmail and Drive',input:{label:'Claude',url:'https://claude.ai/',location:'대화창'}},0).url,'https://claude.ai/');
assert.equal(api.get(load('AI-2026-10-CAT08-005'),{title:'changed step',prompt:'x'},0),null); // A changed step must be rechecked
const html=read('lessons.html');
for(const m of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))if(m[1].trim())new vm.Script(m[1]);
new vm.Script(read('lesson-pptx.js'));
assert.ok(html.includes('${promptInput(L,s,i)}'));assert.ok(!html.includes('function practiceSites('));
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
context.esc=esc;
vm.runInContext(html.slice(html.indexOf('function promptInput('),html.indexOf('const steps=')),context);
const L=load('AI-2026-10-CAT08-005');const card=context.promptInput(L,L.practice.follow[0],0);
assert.match(card,/href="https:\/\/gemini.google.com\/"/);assert.ok(!card.includes('studio.workspace.google.com'));
assert.match(card,/target="_blank" rel="noopener noreferrer"/);
console.log(`PASS: ${lessons} lessons / ${prompts} input blocks; ${JSON.stringify(kinds)}; semantic destinations, safe links, changed-step guard, TXT and renderer syntax`);
