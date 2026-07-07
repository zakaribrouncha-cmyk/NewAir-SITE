document.addEventListener('DOMContentLoaded',()=>{
  const q=s=>document.querySelector(s), qa=s=>[...document.querySelectorAll(s)];
  q('#openMenu')?.addEventListener('click',()=>q('#mobilePanel')?.classList.add('open'));
  q('#closeMenu')?.addEventListener('click',()=>q('#mobilePanel')?.classList.remove('open'));
  qa('[data-discord-link]').forEach(a=>a.href='https://discord.gg/UyzapQ2zap');
  qa('[data-tiktok-link]').forEach(a=>a.href='https://www.tiktok.com/@newairrp');
  const tabs=qa('.step-tab'), panels=qa('.step-panel');
  function show(i){tabs.forEach((t,n)=>t.classList.toggle('active',n===i));panels.forEach((p,n)=>p.classList.toggle('active',n===i));}
  tabs.forEach((t,i)=>t.addEventListener('click',()=>show(i)));
  qa('[data-next]').forEach(b=>b.addEventListener('click',()=>{let i=tabs.findIndex(t=>t.classList.contains('active'));show(Math.min(i+1,panels.length-1));}));
  qa('[data-prev]').forEach(b=>b.addEventListener('click',()=>{let i=tabs.findIndex(t=>t.classList.contains('active'));show(Math.max(i-1,0));}));
  q('#fullMap')?.addEventListener('click',()=>{q('#mapShell')?.classList.toggle('fullscreen');q('#fullMap').textContent=q('#mapShell')?.classList.contains('fullscreen')?'QUITTER':'PLEIN ÉCRAN';});
});