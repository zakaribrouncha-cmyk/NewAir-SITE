(function () {
  const discordUrl = "https://discord.gg/UyzapQ2zap";
  const tiktokUrl = "https://www.tiktok.com/@nhc0023";
  const whitelistKey = "newair-whitelist-candidatures";
  const blockedPaths = ["/cartes", "/jeu", "/combat", "/marche", "/classement"];
  const textRules = [[/OBSIDIAN/g,"NewAir"],[/Obsidian/g,"NewAir"],[/obsidian/g,"newair"],[/CITYBACK/g,"NewAir"],[/CityBack/g,"NewAir"],[/cityback/g,"newair"]];
  function fixMojibake(text){if(!/[ÃÂâ€]/.test(text||""))return text||"";try{return decodeURIComponent(escape(text))}catch{return text||""}}
  function cleanText(text){return textRules.reduce((value,rule)=>value.replace(rule[0],rule[1]),fixMojibake(text||""))}
  function walkAndFix(root){if(!root)return;if(root.nodeType===Node.TEXT_NODE){const next=cleanText(root.nodeValue||"");if(next!==root.nodeValue)root.nodeValue=next;return}if(root.nodeType!==Node.ELEMENT_NODE)return;["href","src","alt","aria-label","placeholder","title"].forEach(attr=>{if(!root.hasAttribute(attr))return;let value=cleanText(root.getAttribute(attr)||"");value=value.replace(/https:\/\/discord\.gg\/[^"'\s]+/g,discordUrl).replace(/https:\/\/www\.tiktok\.com\/@[^"'\s]+/g,tiktokUrl).replace(/\/assets\/obsidian-/g,"/assets/newair-").replace(/\/assets\/cityback-/g,"/assets/newair-");if(value!==root.getAttribute(attr))root.setAttribute(attr,value)});const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);nodes.forEach(walkAndFix)}
  function installSocials(){document.querySelectorAll('a[href*="discord.gg"]').forEach(link=>{link.href=discordUrl})}
  function addEquipeNav(){
    document.querySelectorAll('ul').forEach(ul=>{
      if(ul.dataset.newairEquipeNav==="1")return;
      const hasAccueil=[...ul.querySelectorAll('a')].some(a=>(a.textContent||"").trim().toUpperCase()==="ACCUEIL");
      if(!hasAccueil)return;
      ul.dataset.newairEquipeNav="1";
      const li=document.createElement('li');
      li.innerHTML='<a href="/equipe/" class="text-[11px] xl:text-xs font-bold tracking-[0.25em] xl:tracking-[0.3em] whitespace-nowrap transition-colors text-white/70 hover:text-white">ÉQUIPE</a>';
      const compte=[...ul.children].find(child=>(child.textContent||"").toUpperCase().includes('COMPTE'));
      if(compte)ul.insertBefore(li,compte);else ul.appendChild(li);
    });
  }
  function saveLocalCandidature(data){const rows=JSON.parse(localStorage.getItem(whitelistKey)||"[]");const row={id:`wl_${Date.now()}_${Math.random().toString(36).slice(2,8)}`,created_at:new Date().toISOString(),status:"pending",...data};rows.unshift(row);localStorage.setItem(whitelistKey,JSON.stringify(rows));return row}
  function findCandidate(value){if(!value||typeof value!=="object")return null;if(value.discord_tag||value.rp_firstname||value.rp_lastname||value.rp_project)return value;for(const key of Object.keys(value)){const found=findCandidate(value[key]);if(found)return found}return null}
  function cleanLoginPage(){if(!location.pathname.startsWith("/login"))return;document.querySelectorAll(".newair-admin-login-helper").forEach(node=>node.remove());const emailInput=document.querySelector('input[type="email"], input[placeholder*="email" i]');const passInput=document.querySelector('input[type="password"]');if(!emailInput||!passInput)return;emailInput.placeholder="Adresse email";passInput.placeholder="Mot de passe"}
  function redirectOldAdminPanel(){if(location.pathname.startsWith("/compte")&&location.search.includes("admin"))location.replace("/admin/")}
  function installFormSafety(){document.querySelectorAll("form").forEach(form=>{if(form.dataset.newairPostSafe==="1")return;form.dataset.newairPostSafe="1";form.addEventListener("submit",()=>{const data={};Array.from(form.elements||[]).forEach(field=>{if(field.name)data[field.name]=field.value});if(location.pathname.startsWith("/whitelist")&&Object.keys(data).length)saveLocalCandidature(data)},true)})}
  const nativeFetch=window.fetch;window.fetch=async function(input,init){const request=input instanceof Request?input:null;const url=request?request.url:String(input);const method=(init?.method||request?.method||"GET").toUpperCase();if(method==="POST"&&url.startsWith(location.origin)){try{const body=init?.body||(request?await request.clone().text():"");const json=typeof body==="string"&&body?JSON.parse(body):body;const candidate=findCandidate(json);if(candidate)saveLocalCandidature(candidate)}catch{}}return nativeFetch.apply(this,arguments)};
  if(blockedPaths.some(path=>location.pathname===path||location.pathname===`${path}/`)){location.replace("/");return}
  function runOnce(){walkAndFix(document.documentElement);installSocials();addEquipeNav();cleanLoginPage();redirectOldAdminPanel();installFormSafety()}
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",runOnce,{once:true});else runOnce();setInterval(runOnce,900);new MutationObserver(mutations=>{mutations.forEach(mutation=>{if(mutation.type==="attributes")walkAndFix(mutation.target);mutation.addedNodes.forEach(node=>walkAndFix(node))})}).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:["href","src","alt","placeholder","title","aria-label"]});
})();
