// NewAir safe mode
// This file was simplified to stop browser freezes.
(function(){
  try{
    var session=JSON.parse(localStorage.getItem('newair-user-session')||'null');
    if(session&&session.email){
      document.addEventListener('DOMContentLoaded',function(){
        document.querySelectorAll('a[href="/login"],a[href="/login/"]').forEach(function(a){
          a.href='/compte';
          a.textContent=String(session.email).split('@')[0].slice(0,18);
          a.title=session.email;
        });
      });
    }
  }catch(e){}
})();
