/* Optional cookie-less event tracking. Activated only if GOATCOUNTER_CODE is set. */
(function(){
  'use strict';
  const code=String(window.MANNAL_GOATCOUNTER_CODE||'').trim();
  if(!/^[a-z0-9][a-z0-9-]{1,62}$/.test(code)){
    window.MannalAnalytics={viewLesson:function(){}, download:function(){}};
    return;
  }
  let pending=[],loading=false;
  function flush(){
    if(!window.goatcounter || typeof window.goatcounter.count!=='function')return;
    while(pending.length)window.goatcounter.count(pending.shift());
  }
  function count(event){
    pending.push(event);
    if(window.goatcounter && typeof window.goatcounter.count==='function'){flush();return}
    if(loading)return;
    loading=true;
    const script=document.createElement('script');
    script.src='https://gc.zgo.at/count.js';
    script.async=true;
    script.setAttribute('data-goatcounter','https://'+code+'.goatcounter.com/count');
    script.setAttribute('data-goatcounter-settings',JSON.stringify({no_onload:true,no_events:true}));
    script.onload=flush;
    script.onerror=function(){pending.length=0};
    document.head.appendChild(script);
  }
  function viewLesson(id){
    if(!/^AI-\d{4}-\d{2}-CAT\d{2}-\d{3}$/.test(String(id)))return;
    count({path:'/lesson/'+id,title:'AI 교안 '+id,event:false});
  }
  function download(id,kind){
    if(!/^AI-\d{4}-\d{2}-CAT\d{2}-\d{3}$/.test(id) || !/^(learner|instructor|prompts)$/.test(kind))return;
    count({path:'download/lesson/'+id+'/'+kind,title:'교안 '+id+' '+kind,event:true,no_session:true});
  }
  document.addEventListener('click',function(e){
    const link=e.target && e.target.closest ? e.target.closest('a.dl[download]') : null;
    if(!link)return;
    const m=(link.getAttribute('href')||'').match(/(AI-\d{4}-\d{2}-CAT\d{2}-\d{3})-(learner|instructor|prompts)\.(?:pptx|txt)$/);
    if(m)download(m[1],m[2]);
  });
  window.MannalAnalytics={viewLesson:viewLesson,download:download};
})();
