// NewAir safe mode + light extras
(function(){
  var tiktokUrl='https://www.tiktok.com/@nhc0023';
  var tiktokIcon='<svg viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5" aria-hidden="true"><path d="M16.6 3c.31 2.16 1.52 3.73 3.58 4.43v3.31a7.77 7.77 0 0 1-3.55-.98v5.46c0 3.53-2.35 5.78-5.64 5.78-3.1 0-5.17-2.02-5.17-4.9 0-3.25 2.55-5.26 6.03-4.83v3.4c-1.32-.25-2.26.29-2.26 1.34 0 .86.68 1.45 1.64 1.45 1.1 0 1.82-.66 1.82-2.18V3h3.55Z"></path></svg>';
  var currentUser=null;

  function ensureVideo(){
    var video=document.querySelector('body > video, video[src*="bg.mp4"]');
    if(!video){
      video=document.createElement('video');
      video.src='/video/bg.mp4';
      video.autoplay=true; video.loop=true; video.muted=true; video.playsInline=true; video.setAttribute('aria-hidden','true');
      document.body.insertBefore(video,document.body.firstChild);
    }
    video.style.cssText='position:fixed!important;inset:0!important;width:100%!important;height:100%!important;object-fit:cover!important;z-index:0!important;pointer-events:none!important;opacity:1!important;display:block!important;visibility:visible!important;filter:none!important';
    try{video.muted=true;video.loop=true;video.play().catch(function(){})}catch(e){}
    document.querySelectorAll('body > div[style*="position:fixed"][style*="background"]').forEach(function(d){d.style.background='rgba(0,0,0,0.26)'});
    document.querySelectorAll('body > div:not([data-newair-bg]), body > main, #root, #__next').forEach(function(el){
      if(el.tagName==='SCRIPT'||el.tagName==='STYLE'||el.tagName==='VIDEO')return;
      el.style.position=el.style.position||'relative';
      if(!el.style.zIndex)el.style.zIndex='2';
    });
    document.documentElement.style.backgroundColor='#000';
    document.body.style.backgroundColor='#000';
  }

  function fixPageBackdrops(){
    document.querySelectorAll('main, main > section, main > div').forEach(function(el){
      var bg='';try{bg=getComputedStyle(el).backgroundImage||''}catch(e){}
      if(bg.indexOf('hero-newair')!==-1 || bg.indexOf('url(')!==-1 && bg.indexOf('hero')!==-1){el.style.backgroundImage='none'}
    });
  }

  function hideMapPins(){
    if(location.pathname.indexOf('/map')!==0)return;
    document.querySelectorAll('.leaflet-marker-pane,.leaflet-shadow-pane,.leaflet-popup-pane,.leaflet-tooltip-pane,.leaflet-marker-icon,.leaflet-marker-shadow,.leaflet-popup,.leaflet-tooltip').forEach(function(el){
      el.style.display='none';el.style.opacity='0';el.style.pointerEvents='none';
    });
    document.querySelectorAll('main svg').forEach(function(svg){
      if(svg.closest('header')||svg.closest('nav'))return;
      var html=svg.innerHTML||''; var cls=String(svg.getAttribute('class')||'');
      if(cls.indexOf('map-pin')!==-1||html.indexOf('M20 10c0')!==-1||html.indexOf('circle')!==-1){
        var p=svg.closest('button,a,div,span')||svg; p.style.display='none'; p.style.opacity='0'; p.style.pointerEvents='none';
      }
    });
  }

  function userName(u){return u.global_name||u.username||'Compte'}
  function isAdminUser(u){return !!(u && (u.is_admin || u.grade==='Staff' || u.grade==='Fondateur' || u.grade==='SuperAdmin' || u.grade==='Admin'))}
  function hideCompteTab(){
    document.querySelectorAll('a[href="/compte"],a[href="/compte/"]').forEach(function(a){
      if(a.classList.contains('newair-connected-account'))return;
      var li=a.closest('li');
      if(li)li.style.display='none';else a.style.display='none';
    });
  }
  function addAdminPanelLink(){
    if(!currentUser || !isAdminUser(currentUser))return;
    document.querySelectorAll('ul').forEach(function(ul){
      var links=[].slice.call(ul.querySelectorAll('a'));
      var hasHome=links.some(function(a){return (a.textContent||'').trim().toUpperCase()==='ACCUEIL'});
      var hasAdmin=links.some(function(a){return (a.textContent||'').toUpperCase().indexOf('ADMIN')!==-1});
      if(!hasHome||hasAdmin)return;
      var li=document.createElement('li');
      li.setAttribute('data-newair-admin','1');
      li.innerHTML='<a href="/admin/" class="text-[11px] xl:text-xs font-bold tracking-[0.25em] xl:tracking-[0.3em] whitespace-nowrap transition-colors text-blue-200 hover:text-white">ADMIN PANEL</a>';
      ul.appendChild(li);
    });
  }
  function applyConnectedUser(u){
    if(!u)return;
    currentUser=u;
    var name=userName(u);
    var avatar=u.avatar||'/assets/newair-logo-swirl.png';
    hideCompteTab();
    document.querySelectorAll('a[href="/login"],a[href="/login/"]').forEach(function(a){
      a.href='/compte';
      a.title=name;
      a.classList.add('newair-connected-account');
      a.innerHTML='<span class="newair-account-pill"><img src="'+avatar+'" alt=""><span>'+name+'</span></span>';
      a.style.display='inline-flex';
    });
    addAdminPanelLink();
  }
  function checkServerSession(){
    fetch('/api/user/me',{credentials:'include',cache:'no-store'})
      .then(function(r){return r.ok?r.json():null})
      .then(function(j){if(j&&j.ok&&j.user)applyConnectedUser(j.user)})
      .catch(function(){});
  }

  function addTeamLink(){
    document.querySelectorAll('ul').forEach(function(ul){
      if(ul.getAttribute('data-newair-team')==='1')return;
      var links=[].slice.call(ul.querySelectorAll('a'));
      var hasHome=links.some(function(a){return (a.textContent||'').trim().toUpperCase()==='ACCUEIL'});
      var hasTeam=links.some(function(a){return (a.textContent||'').trim().toUpperCase()==='ÉQUIPE'});
      if(!hasHome||hasTeam)return;
      ul.setAttribute('data-newair-team','1');
      var li=document.createElement('li');
      li.innerHTML='<a href="/equipe/" class="text-[11px] xl:text-xs font-bold tracking-[0.25em] xl:tracking-[0.3em] whitespace-nowrap transition-colors text-white/70 hover:text-white">ÉQUIPE</a>';
      var compte=[].slice.call(ul.children).find(function(item){return (item.textContent||'').toUpperCase().indexOf('COMPTE')!==-1});
      if(compte)ul.insertBefore(li,compte);else ul.appendChild(li)
    })
  }

  function keepOnlyTikTok(){
    document.querySelectorAll('a[href*="instagram.com"],a[href*="youtube.com"],a[aria-label*="Instagram" i],a[aria-label*="YouTube" i]').forEach(function(a){a.remove()});
    var holders=[];document.querySelectorAll('a[href*="discord.gg"],a[href*="tiktok.com"]').forEach(function(a){if(a.parentElement)holders.push(a.parentElement)});
    holders.forEach(function(holder){
      if(holder.querySelector('a[data-newair-tiktok="1"],a[href*="tiktok.com"]'))return;
      var link=document.createElement('a');link.href=tiktokUrl;link.target='_blank';link.rel='noreferrer';link.setAttribute('aria-label','TikTok');link.setAttribute('data-newair-tiktok','1');link.className='hover:text-white transition-colors';link.innerHTML=tiktokIcon;holder.appendChild(link)
    })
  }

  function addStyle(){
    if(document.getElementById('newair-light-style'))return;
    var s=document.createElement('style');s.id='newair-light-style';
    s.textContent='body>video,video[src*="bg.mp4"]{opacity:1!important;display:block!important;visibility:visible!important;filter:none!important}.newair-connected-account{max-width:245px!important;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;border-color:rgba(95,150,214,.55)!important;background:rgba(11,42,91,.22)!important;color:#d9e9ff!important;box-shadow:0 0 20px rgba(95,150,214,.24)!important;padding:6px 10px!important;border-radius:999px!important}.newair-account-pill{display:inline-flex;align-items:center;gap:8px}.newair-account-pill img{width:26px;height:26px;border-radius:999px;object-fit:cover}.leaflet-marker-pane,.leaflet-shadow-pane,.leaflet-popup-pane,.leaflet-tooltip-pane,.leaflet-marker-pane *,.leaflet-shadow-pane *,.leaflet-marker-icon,.leaflet-marker-shadow,.leaflet-popup,.leaflet-tooltip{display:none!important;opacity:0!important;pointer-events:none!important}';
    document.head.appendChild(s)
  }

  function run(){addStyle();ensureVideo();fixPageBackdrops();hideMapPins();addTeamLink();keepOnlyTikTok();if(currentUser)applyConnectedUser(currentUser)}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){run();checkServerSession()},{once:true});else{run();checkServerSession()}
  setTimeout(run,700);setTimeout(run,1800);setTimeout(run,4000);setTimeout(checkServerSession,1200);setTimeout(checkServerSession,3500);
})();
