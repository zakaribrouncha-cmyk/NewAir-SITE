// NewAir auth + navbar sync
(function(){
  var tiktokUrl='https://www.tiktok.com/@nhc0023';
  var loginUrl='/api/discord/login?mode=user&next=/';
  var tiktokIcon='<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16.6 3c.31 2.16 1.52 3.73 3.58 4.43v3.31a7.77 7.77 0 0 1-3.55-.98v5.46c0 3.53-2.35 5.78-5.64 5.78-3.1 0-5.17-2.02-5.17-4.9 0-3.25 2.55-5.26 6.03-4.83v3.4c-1.32-.25-2.26.29-2.26 1.34 0 .86.68 1.45 1.64 1.45 1.1 0 1.82-.66 1.82-2.18V3h3.55Z"></path></svg>';
  var user=null;
  function css(){
    if(document.getElementById('newair-sync-style'))return;
    var s=document.createElement('style');s.id='newair-sync-style';
    s.textContent='.newair-social-link{display:inline-flex!important;align-items:center!important;justify-content:center!important;width:24px!important;height:24px!important;color:rgba(255,255,255,.9)!important;text-decoration:none!important}.newair-social-link svg{width:20px!important;height:20px!important;display:block!important;filter:drop-shadow(0 0 8px rgba(95,150,214,.55))}.newair-connected-account{display:inline-flex!important;align-items:center!important;gap:8px!important;border:1px solid rgba(95,150,214,.55)!important;background:rgba(11,42,91,.22)!important;color:#d9e9ff!important;padding:6px 10px!important;border-radius:999px!important;text-decoration:none!important}.newair-connected-account img{width:26px;height:26px;border-radius:999px;object-fit:cover}';
    document.head.appendChild(s);
  }
  function txt(el){return (el.textContent||'').toUpperCase()}
  function makeEquipe(){var a=document.createElement('a');a.href='/equipe/';a.textContent='ÉQUIPE';a.style.color='rgba(255,255,255,.75)';a.style.textDecoration='none';a.style.fontSize='11px';a.style.fontWeight='800';a.style.letterSpacing='.30em';a.style.textTransform='uppercase';return a}
  function equipe(){
    document.querySelectorAll('nav').forEach(function(nav){if(txt(nav).indexOf('ÉQUIPE')!==-1)return;var a=makeEquipe();var compte=[].slice.call(nav.querySelectorAll('a')).find(function(x){return txt(x).indexOf('COMPTE')!==-1});var right=nav.querySelector('.right');if(compte)nav.insertBefore(a,compte);else if(right)nav.insertBefore(a,right);else nav.appendChild(a)});
    document.querySelectorAll('ul').forEach(function(ul){if(txt(ul).indexOf('ACCUEIL')===-1||txt(ul).indexOf('ÉQUIPE')!==-1)return;var li=document.createElement('li');li.innerHTML='<a href="/equipe/" class="text-[11px] xl:text-xs font-bold tracking-[0.25em] xl:tracking-[0.3em] whitespace-nowrap transition-colors text-white/70 hover:text-white">ÉQUIPE</a>';var compte=[].slice.call(ul.children).find(function(x){return txt(x).indexOf('COMPTE')!==-1});if(compte)ul.insertBefore(li,compte);else ul.appendChild(li)});
  }
  function socials(){
    document.querySelectorAll('a[href*="youtube.com"],a[href*="youtu.be"]').forEach(function(a){a.remove()});
    document.querySelectorAll('a[href*="instagram.com"]').forEach(function(a){a.href=tiktokUrl;a.target='_blank';a.rel='noreferrer';a.classList.add('newair-social-link');a.setAttribute('aria-label','TikTok');a.innerHTML=tiktokIcon});
    document.querySelectorAll('a[href*="tiktok.com"],a[aria-label*="TikTok" i]').forEach(function(a){a.href=tiktokUrl;a.target='_blank';a.rel='noreferrer';a.classList.add('newair-social-link');a.setAttribute('aria-label','TikTok');a.innerHTML=tiktokIcon});
    document.querySelectorAll('nav,.right,.flex.items-center').forEach(function(box){if(box.querySelector('a[aria-label="TikTok"]'))return;var t=txt(box);if(t.indexOf('REJOINDRE')===-1&&t.indexOf('CONNEXION')===-1&&!box.classList.contains('right'))return;var a=document.createElement('a');a.href=tiktokUrl;a.target='_blank';a.rel='noreferrer';a.className='newair-social-link';a.setAttribute('aria-label','TikTok');a.innerHTML=tiktokIcon;var join=[].slice.call(box.querySelectorAll('a')).find(function(x){return txt(x).indexOf('REJOINDRE')!==-1});if(join)box.insertBefore(a,join);else box.appendChild(a)});
  }
  function loginLinks(){document.querySelectorAll('a[href="/login"],a[href="/login/"]').forEach(function(a){a.href=loginUrl})}
  function av(u){var a=u.avatar||'';if(a.indexOf('http')===0||a.indexOf('/')===0)return a;if(a&&u.discord_id){var ext=a.indexOf('a_')===0?'gif':'png';return 'https://cdn.discordapp.com/avatars/'+u.discord_id+'/'+a+'.'+ext+'?size=128'}return '/assets/newair-logo-swirl.png'}
  function isAdmin(u){return !!(u&&(u.is_admin||['Staff','Fondateur','SuperAdmin','Admin'].indexOf(u.grade)>=0))}
  function account(u){user=u;var name=u.global_name||u.username||'Compte';document.querySelectorAll('a[href="/login"],a[href="/login/"] ,a[href="'+loginUrl+'"],a.newair-connected-account').forEach(function(a){a.href='/compte/';a.classList.add('newair-connected-account');a.innerHTML='<img src="'+av(u)+'" onerror="this.src=\'/assets/newair-logo-swirl.png\'" alt=""><span>'+name+'</span>'});document.querySelectorAll('a[href="/compte"],a[href="/compte/"]').forEach(function(a){if(a.classList.contains('newair-connected-account'))return;var li=a.closest('li');if(li)li.style.display='none';else a.style.display='none'});if(isAdmin(u))admin()}
  function admin(){document.querySelectorAll('nav').forEach(function(nav){if(txt(nav).indexOf('ADMIN PANEL')!==-1)return;var a=document.createElement('a');a.href='/admin/';a.textContent='ADMIN PANEL';a.style.color='#d9e9ff';a.style.textDecoration='none';a.style.fontSize='11px';a.style.fontWeight='800';a.style.letterSpacing='.30em';a.style.textTransform='uppercase';var right=nav.querySelector('.right');if(right)nav.insertBefore(a,right);else nav.appendChild(a)});document.querySelectorAll('ul').forEach(function(ul){if(txt(ul).indexOf('ACCUEIL')===-1||txt(ul).indexOf('ADMIN PANEL')!==-1)return;var li=document.createElement('li');li.innerHTML='<a href="/admin/" class="text-[11px] xl:text-xs font-bold tracking-[0.25em] xl:tracking-[0.3em] whitespace-nowrap transition-colors text-blue-200 hover:text-white">ADMIN PANEL</a>';ul.appendChild(li)})}
  function session(){fetch('/api/user/me',{credentials:'include',cache:'no-store'}).then(function(r){return r.ok?r.json():null}).then(function(j){if(j&&j.ok&&j.user)account(j.user);else loginLinks()}).catch(loginLinks)}
  function run(){css();loginLinks();equipe();socials();if(user)account(user)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){run();session()},{once:true});else{run();session()}setTimeout(run,700);setTimeout(run,2000);setTimeout(run,4000);setTimeout(session,1200);setTimeout(session,3500);
})();
