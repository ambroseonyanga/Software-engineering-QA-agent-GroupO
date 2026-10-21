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
const assistantToggle = document.getElementById('assistant-toggle');
assistantToggle?.addEventListener('click', () => {
  const expanded = assistantToggle.getAttribute('aria-expanded') === 'true';
  assistantToggle.setAttribute('aria-expanded', String(!expanded));
  document.getElementById('assistant-body').hidden = expanded;
  if (!expanded) document.getElementById('assistant-question').focus();
});
document.getElementById('assistant-body')?.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    document.getElementById('assistant-body').hidden = true;
    assistantToggle.setAttribute('aria-expanded', 'false');
    assistantToggle.focus();
  }
});
document.getElementById('assistant-form')?.addEventListener('submit', async event => {
  event.preventDefault();
  const button = event.currentTarget.querySelector('button');
  const answer = document.getElementById('assistant-answer');
  button.disabled = true;
  answer.textContent = 'Checking project knowledge…';
  try {
    const response = await fetch('/api/assistant', {method:'POST', body:new URLSearchParams({question:document.getElementById('assistant-question').value,session_id:event.currentTarget.dataset.session,screen:event.currentTarget.dataset.screen})});
    const data = await response.json();
    answer.textContent = data.answer || 'No answer was returned.';
  } catch { answer.textContent = 'Cannot reach the application. Please try again.'; }
  finally { button.disabled = false; }
});
