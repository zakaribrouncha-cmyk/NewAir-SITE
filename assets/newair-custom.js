// NewAir safe mode + light extras
(function(){
  var sessionKey='newair-user-session';
  var tiktokUrl='https://www.tiktok.com/@nhc0023';
  var tiktokIcon='<svg viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5" aria-hidden="true"><path d="M16.6 3c.31 2.16 1.52 3.73 3.58 4.43v3.31a7.77 7.77 0 0 1-3.55-.98v5.46c0 3.53-2.35 5.78-5.64 5.78-3.1 0-5.17-2.02-5.17-4.9 0-3.25 2.55-5.26 6.03-4.83v3.4c-1.32-.25-2.26.29-2.26 1.34 0 .86.68 1.45 1.64 1.45 1.1 0 1.82-.66 1.82-2.18V3h3.55Z"></path></svg>';

  function getSession(){try{return JSON.parse(localStorage.getItem(sessionKey)||'null')}catch(e){return null}}

  function forceHomepageVideo(){
    if(!location.pathname || location.pathname==='/' || location.pathname==='/index.html'){
      document.querySelectorAll('video').forEach(function(v){
        v.style.display='block';v.style.visibility='visible';v.style.opacity='1';v.style.filter='none';v.style.zIndex='0';
        try{v.muted=true;v.loop=true;v.play().catch(function(){})}catch(e){}
      });
      var video=document.querySelector('body > video');
      if(video&&video.nextElementSibling)video.nextElementSibling.style.background='rgba(0,0,0,0.18)';
    }
  }

  function showConnectedAccount(){
    var session=getSession();
    document.querySelectorAll('a[href="/login"],a[href="/login/"],a[href="/compte"],a[href="/compte/"]').forEach(function(a){
      if(session&&session.email&&a.getAttribute('href').indexOf('/login')===0){
        a.href='/compte';a.textContent=String(session.email).split('@')[0].slice(0,18);a.title=session.email;a.classList.add('newair-connected-account')
      }
    })
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
    holders.forEach(function(holder){if(holder.querySelector('a[data-newair-tiktok="1"],a[href*="tiktok.com"]'))return;var link=document.createElement('a');link.href=tiktokUrl;link.target='_blank';link.rel='noreferrer';link.setAttribute('aria-label','TikTok');link.setAttribute('data-newair-tiktok','1');link.className='hover:text-white transition-colors';link.innerHTML=tiktokIcon;holder.appendChild(link)})
  }

  function addStyle(){
    if(document.getElementById('newair-light-style'))return;
    var s=document.createElement('style');s.id='newair-light-style';
    s.textContent='.newair-connected-account{max-width:210px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;border-color:rgba(95,150,214,.55)!important;background:rgba(11,42,91,.18)!important;color:#d9e9ff!important;box-shadow:0 0 20px rgba(95,150,214,.24)!important}body>video{opacity:1!important;display:block!important;visibility:visible!important;filter:none!important}body>video+div{background:rgba(0,0,0,.18)!important}';
    document.head.appendChild(s)
  }

  function run(){addStyle();forceHomepageVideo();showConnectedAccount();addTeamLink();keepOnlyTikTok()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run,{once:true});else run();
  setTimeout(run,800);setTimeout(run,2000);setTimeout(run,4000);
})();
