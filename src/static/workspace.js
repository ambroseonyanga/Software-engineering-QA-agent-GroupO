document.querySelectorAll('form[method="post"],form[method="POST"]').forEach(form=>form.addEventListener('submit',()=>{const status=document.getElementById('loading');if(status){status.classList.add('visible');status.textContent='Working on your request. Please keep this page open.';}form.querySelectorAll('button[type="submit"]').forEach(b=>{b.disabled=true;b.textContent='Working...';});}));document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(document.getElementById(b.dataset.copy).innerText);b.textContent='Copied';}catch{b.textContent='Select the text to copy';}}));

const themeToggle = document.getElementById('theme-toggle');
const updateThemeLabel = () => {
  if(themeToggle) themeToggle.textContent = document.documentElement.dataset.theme === 'dark' ? 'Light theme' : 'Dark theme';
  document.querySelectorAll('[data-theme-choice]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.themeChoice===document.documentElement.dataset.theme)));
};
updateThemeLabel();
themeToggle?.addEventListener('click', () => {
  const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem('qa-theme', theme); } catch {}
  updateThemeLabel();
});
document.querySelectorAll('[data-theme-choice]').forEach(button=>button.addEventListener('click',()=>{
  document.documentElement.dataset.theme=button.dataset.themeChoice;
  try{localStorage.setItem('qa-theme',button.dataset.themeChoice)}catch{}
  updateThemeLabel();
}));
const knowledgeForm=document.getElementById('knowledge-form');
knowledgeForm?.addEventListener('submit',async event=>{
 event.preventDefault();const question=document.getElementById('knowledge-question').value.trim();if(!question)return;
 const button=knowledgeForm.querySelector('button'), status=document.getElementById('knowledge-status');button.disabled=true;status.textContent='Checking project records…';
 try{
  const response=await fetch('/api/assistant',{method:'POST',body:new URLSearchParams({question,session_id:knowledgeForm.dataset.session,screen:'knowledge'})});
  const data=await response.json();if(!response.ok)throw new Error(data.answer||'Unable to load project knowledge. Try again.');
  const article=document.createElement('article'), heading=document.createElement('h3'), answer=document.createElement('p');article.className='knowledge-answer';heading.textContent=question;answer.textContent=data.answer||'No answer returned.';article.append(heading,answer);
  if(data.sources?.length){const details=document.createElement('details'),summary=document.createElement('summary'),list=document.createElement('ul');summary.textContent='Sources used';for(const source of data.sources){const li=document.createElement('li');li.textContent=source;list.append(li)}details.append(summary,list);article.append(details)}
  document.getElementById('knowledge-conversation').prepend(article);status.textContent='Answer ready.';
 }catch(error){status.textContent=error.message||'Unable to reach the application. Try again.';}finally{button.disabled=false;}
});

const tracePanel=document.querySelector('.execution-trace');
if(tracePanel){
 const toggle=document.getElementById('trace-toggle'), body=document.getElementById('trace-body'), runs=document.getElementById('trace-run'), list=document.getElementById('trace-events'), status=document.getElementById('trace-status');
 let data, busy=false;
 toggle.addEventListener('click',()=>{body.hidden=!body.hidden;toggle.setAttribute('aria-expanded',String(!body.hidden));tracePanel.classList.toggle('collapsed',body.hidden)});
 const draw=()=>{
  const scrollTop=tracePanel.scrollTop;
  const events=(data.events||[]).filter(e=>e.run_id===runs.value);
  status.textContent=events.length ? `${events.length} recorded events · ${data.status.replaceAll('_',' ')}` : 'No events recorded for this run yet.';
  const retained=new Set();
  for(const [index,event] of events.entries()){
   const key=JSON.stringify([runs.value,event.at,event.action,index]);retained.add(key);
   let li=Array.from(list.children).find(item=>item.dataset.eventKey===key);
   if(li){const pre=li.querySelector('pre'),text=JSON.stringify(event.evidence,null,2);if(pre.textContent!==text)pre.textContent=text;continue;}
   li=document.createElement('li');li.dataset.eventKey=key;const details=document.createElement('details'), summary=document.createElement('summary'), time=document.createElement('time'), evidence=document.createElement('pre');
   summary.textContent=event.action.replaceAll('_',' ');time.dateTime=event.at;time.textContent=event.at ? new Date(event.at).toLocaleString('en-GB', {timeZone:'Africa/Kampala', timeZoneName:'short'}) : 'Time not recorded';evidence.textContent=JSON.stringify(event.evidence,null,2);
   details.append(summary,time,evidence);li.append(details);list.append(li);
  }
  for(const li of Array.from(list.children))if(!retained.has(li.dataset.eventKey))li.remove();
  tracePanel.scrollTop=scrollTop;
  if(data.pending) status.textContent+=' · Workflow in progress; waiting for further events.';
 };
 async function refresh(){
  if(busy)return;busy=true;
  try{const response=await fetch(tracePanel.dataset.url,{cache:'no-store'});if(!response.ok)throw Error();data=await response.json();const previous=runs.value;runs.replaceChildren();for(const run of data.runs){const option=document.createElement('option');option.value=run.id;option.textContent=run.label;runs.append(option)}runs.value=data.runs.some(r=>r.id===previous)?previous:data.runs.at(-1).id;draw();}
  catch{status.textContent='Unable to load trace evidence. Use Refresh to retry. Previously loaded evidence is retained.';}
  finally{busy=false;}
 }
 runs.addEventListener('change',draw);document.getElementById('trace-refresh').addEventListener('click',refresh);refresh();setInterval(()=>{if(!document.hidden&&!body.hidden)refresh()},5000);
}

document.querySelectorAll('.notice.error').forEach(banner => {
  const project = location.pathname.match(/^\/projects\/([^/]+)/)?.[1] || 'global';
  const key = JSON.stringify(['qa-dismissed-error', project, banner.textContent.trim()]);
  try {
    if (localStorage.getItem(key)) { banner.remove(); return; }
  } catch {}
  window.setTimeout(() => {
    try { localStorage.setItem(key, 'dismissed'); } catch {}
    banner.remove();
  }, 5000);
});
