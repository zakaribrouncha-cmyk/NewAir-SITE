from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from http import cookies
import json, os, secrets, time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
import requests

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; USERS=DATA/'users.json'; CANDIDATURES=DATA/'candidatures.json'
ADMIN_COOKIE='newair_admin_session'; USER_COOKIE='newair_user_session'; DID_COOKIE='newair_discord_id'
ADMIN_SESSIONS={}; USER_SESSIONS={}; OAUTH_STATES={}
ACCEPTED_ROLE_ID=os.environ.get('DISCORD_ACCEPTED_ROLE_ID','1523767412103708762').strip()
REFUSED_ROLE_ID=os.environ.get('DISCORD_REFUSED_ROLE_ID','1523768172291948674').strip()
AUTH='Author'+'ization'

def clean(v):
    v=str(v or '').strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")): v=v[1:-1].strip()
    return v

def env(n): return clean(os.environ.get(n,''))
def env_list_one(n): return [clean(x) for x in os.environ.get(n,'').split(',') if clean(x)]
def env_any(*names):
    out=[]
    for n in names: out += env_list_one(n)
    return list(dict.fromkeys(out))
def read_json(p,d):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return d
def write_json(p,v):
    DATA.mkdir(exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def cfg():
    admin=env_any('DISCORD_ADMIN_ROLE_IDS','ID_ROLE_ADMIN','ADMIN_ROLE_ID','ROLE_ADMIN')
    staff=env_any('DISCORD_STAFF_ROLE_IDS','ID_ROLE_STAFF','STAFF_ROLE_ID','ROLE_STAFF')
    superadmin=env_any('DISCORD_SUPERADMIN_ROLE_IDS','ID_ROLE_SUPERADMIN','SUPERADMIN_ROLE_ID','ROLE_SUPERADMIN')
    fondateur=env_any('DISCORD_FONDATEUR_ROLE_IDS','ID_ROLE_FONDATEUR','FONDATEUR_ROLE_ID','ROLE_FONDATEUR','ID_ROLE_PROPRIETAIRE')
    haut=env_any('DISCORD_HAUT_GRADE_PANEL_ROLE_IDS','ID_ROLE_HAUT_GRADE_PANEL','HAUT_GRADE_PANEL_ROLE_ID','ROLE_HAUT_GRADE_PANEL')
    return {'cid':env('DISCORD_CLIENT_ID'),'sec':env('DISCORD_CLIENT_SECRET'),'bt':env('DISCORD_BOT_TOKEN'),'gid':env('DISCORD_GUILD_ID'),'redir':env('DISCORD_REDIRECT_URI'),'admin':admin,'staff':staff,'superadmin':superadmin,'fondateur':fondateur,'haut':haut,'all':admin+staff+superadmin+fondateur+haut}
def ready(need_roles=False):
    c=cfg(); return bool(c['cid'] and c['sec'] and c['bt'] and c['gid'] and (c['all'] or not need_roles))
def h(extra=None):
    x={'User-Agent':'Mozilla/5.0 NewAirSite/1.0','Accept':'application/json'}
    if extra: x.update(extra)
    return x
def rjson(method,url,headers=None,**kw):
    r=requests.request(method,url,headers=h(headers),timeout=15,**kw)
    if r.status_code>=400:
        try: d=r.json()
        except Exception: d=r.text[:500]
        raise RuntimeError(f'HTTP {r.status_code} Discord: {d}')
    if not r.text: return {}
    try: return r.json()
    except Exception: return {}
def avatar(u):
    a=u.get('avatar')
    if not a: return '/assets/newair-logo-swirl.png'
    if str(a).startswith('http') or str(a).startswith('/'): return a
    ext='gif' if str(a).startswith('a_') else 'png'
    return f"https://cdn.discordapp.com/avatars/{u.get('id')}/{a}.{ext}?size=256"
def grade_from_roles(roles):
    c=cfg(); roles=set([str(x) for x in (roles or [])])
    if roles.intersection(set(c['haut'])) or roles.intersection(set(c['fondateur'])): return 'Fondateur'
    if roles.intersection(set(c['superadmin'])): return 'SuperAdmin'
    if roles.intersection(set(c['staff'])): return 'Staff'
    if roles.intersection(set(c['admin'])): return 'Admin'
    return None
def exchange(code,redir):
    c=cfg()
    return rjson('POST','https://discord.com/api/oauth2/token',headers={'Content-Type':'application/x-www-form-urlencoded'},data={'client_id':c['cid'],'client_secret':c['sec'],'grant_type':'authorization_code','code':code,'redirect_uri':redir})
def get_user(at): return rjson('GET','https://discord.com/api/users/@me',headers={AUTH:'Bear'+'er '+at})
def get_member(uid):
    c=cfg(); return rjson('GET',f"https://discord.com/api/guilds/{c['gid']}/members/{uid}",headers={AUTH:'Bo'+'t '+c['bt']})
def get_member_oauth(at):
    c=cfg(); return rjson('GET',f"https://discord.com/api/users/@me/guilds/{c['gid']}/member",headers={AUTH:'Bear'+'er '+at})
def upsert_user(u, member=None):
    rows=read_json(USERS,[]); now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()); item=next((x for x in rows if str(x.get('discord_id'))==str(u.get('id'))),None)
    roles=(member or {}).get('roles',[]) if member else (item or {}).get('roles',[])
    gr=grade_from_roles(roles)
    data={'discord_id':u.get('id'),'username':u.get('username'),'global_name':(member or {}).get('nick') or u.get('global_name') or u.get('username'),'avatar':avatar(u),'roles':roles,'grade':gr,'is_admin':bool(gr),'status':item.get('status','linked') if item else 'linked','linked_at':item.get('linked_at',now) if item else now,'last_login':now}
    if item: item.update(data)
    else: rows.insert(0,data); item=data
    write_json(USERS,rows); return item
def find_user(uid):
    if not uid: return None
    return next((x for x in read_json(USERS,[]) if str(x.get('discord_id'))==str(uid)),None)
def role(uid,rid,method):
    if not uid or not rid: return False
    c=cfg()
    try: rjson(method,f"https://discord.com/api/guilds/{c['gid']}/members/{uid}/roles/{rid}",headers={AUTH:'Bo'+'t '+c['bt']}); return True
    except Exception as e: print('role error',e); return False
def set_status(uid,status):
    rows=read_json(USERS,[]); item=next((x for x in rows if str(x.get('discord_id'))==str(uid)),None)
    if item: item['status']=status; item['reviewed_at']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()); write_json(USERS,rows)
    if status=='accepted': role(uid,REFUSED_ROLE_ID,'DELETE'); role(uid,ACCEPTED_ROLE_ID,'PUT')
    if status=='rejected': role(uid,ACCEPTED_ROLE_ID,'DELETE'); role(uid,REFUSED_ROLE_ID,'PUT')
    return item
def esc(v): return str(v or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')
def account_html(u):
    n=esc(u.get('global_name') or u.get('username') or 'Compte'); av=esc(u.get('avatar') or '/assets/newair-logo-swirl.png'); st=esc(u.get('status') or 'linked'); gr=esc(u.get('grade') or 'Joueur')
    admin_link="<a style='color:white' href='/admin/'>Panel admin</a> · " if u.get('is_admin') else ''
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Compte NewAir</title><link rel='stylesheet' href='/assets/styles-Db9UqP69.css'></head><body style='margin:0;background:#000;color:white;font-family:Arial'><main style='max-width:900px;margin:0 auto;padding:100px 22px'><h1 style='font-size:54px'>MON COMPTE</h1><section style='border:1px solid #1e4f8f;border-radius:18px;padding:30px;background:#050b16'><img src='{av}' style='width:82px;height:82px;border-radius:999px;object-fit:cover'><h2>{n}</h2><p>Grade Discord : <b>{gr}</b></p><p>Statut : <b>{st}</b></p>{admin_link}<a style='color:white' href='/'>Accueil</a> · <a style='color:white' href='/api/discord/logout'>Déconnexion</a></section></main><script src='/assets/newair-custom.js?v=roles3' defer></script></body></html>"""
def team_data():
    out=[]; seen=set(); c=cfg(); err=None
    if c['bt'] and c['gid']:
        try:
            data=rjson('GET',f"https://discord.com/api/guilds/{c['gid']}/members?limit=1000",headers={AUTH:'Bo'+'t '+c['bt']})
            for m in data:
                gr=grade_from_roles(m.get('roles',[]))
                if not gr: continue
                u=m.get('user',{}); uid=str(u.get('id')); seen.add(uid)
                name=m.get('nick') or u.get('global_name') or u.get('username') or 'Staff NewAir'
                out.append({'name':name,'role':gr,'discord_id':uid,'avatar':avatar(u),'subtitle':'Rôle Discord : '+gr})
        except Exception as e:
            err=str(e); print('team error',e)
    for u in read_json(USERS,[]):
        gr=u.get('grade') or grade_from_roles(u.get('roles',[]))
        uid=str(u.get('discord_id'))
        if gr and uid not in seen:
            out.append({'name':u.get('global_name') or u.get('username') or 'Staff NewAir','role':gr,'discord_id':uid,'avatar':u.get('avatar') or '/assets/newair-logo-swirl.png','subtitle':'Compte lié : '+gr})
    order={'Fondateur':0,'SuperAdmin':1,'Staff':2,'Admin':3}
    out.sort(key=lambda x:(order.get(x.get('role'),9),x.get('name','').lower()))
    return {'members':out,'error':err}

class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.js':'application/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.mp4':'video/mp4','.webp':'image/webp','.svg':'image/svg+xml'}
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS'); self.send_header('Access-Control-Allow-Headers','content-type, authorization'); super().end_headers()
    def send_json(self,v,status=200):
        b=json.dumps(v,ensure_ascii=False).encode('utf-8'); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def send_html(self,html,status=200):
        b=html.encode('utf-8'); self.send_response(status); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def inject_html(self,html):
        script="<script src='/assets/newair-custom.js?v=roles3' defer></script>"
        if '/assets/newair-custom.js' not in html: html=html.replace('</body>',script+'</body>') if '</body>' in html else html+script
        return html
    def serve_html_file(self,file): return self.send_html(self.inject_html(file.read_text(encoding='utf-8-sig')))
    def redirect(self,loc,cookie=None):
        self.send_response(302); self.send_header('Location',loc)
        if cookie:
            if isinstance(cookie,(list,tuple)):
                for c in cookie: self.send_header('Set-Cookie',c)
            else: self.send_header('Set-Cookie',cookie)
        self.end_headers()
    def base(self):
        proto=self.headers.get('X-Forwarded-Proto') or 'https'; host=self.headers.get('X-Forwarded-Host') or self.headers.get('Host') or 'localhost:4174'; return f'{proto}://{host}'.rstrip('/')
    def redir(self): return cfg()['redir'] or self.base()+'/api/discord/callback'
    def cookie(self,n):
        jar=cookies.SimpleCookie()
        try: jar.load(self.headers.get('Cookie','')); return jar[n].value if n in jar else None
        except Exception: return None
    def current_user(self):
        s=USER_SESSIONS.get(self.cookie(USER_COOKIE) or '')
        if s and s.get('expires',0)>time.time(): return s
        u=find_user(self.cookie(DID_COOKIE))
        return {'user':u,'expires':time.time()+31536000} if u else None
    def current_admin(self):
        s=ADMIN_SESSIONS.get(self.cookie(ADMIN_COOKIE) or '')
        if s and s.get('expires',0)>time.time(): return s
        u=self.current_user()
        if u and u.get('user') and u['user'].get('is_admin'): return {'admin':u['user'],'expires':time.time()+31536000}
        return None
    def body_json(self):
        raw=self.rfile.read(int(self.headers.get('content-length','0') or '0')).decode('utf-8','replace')
        try: return json.loads(raw) if raw.strip() else {}
        except Exception: return {}
    def do_GET(self):
        p=urlparse(self.path); path=p.path; q=parse_qs(p.query)
        if path in ('/login','/login/'): return self.redirect('/api/discord/login?mode=user&next=/')
        if path in ('/compte','/compte/'):
            s=self.current_user(); return self.send_html(account_html(s['user'])) if s else self.redirect('/login')
        if path=='/api/discord/debug':
            c=cfg(); return self.send_json({'ok':True,'client_id_set':bool(c['cid']),'client_secret_length':len(c['sec']),'bot_token_set':bool(c['bt']),'guild_id_set':bool(c['gid']),'redirect_uri_used':self.redir(),'admin_roles_count':len(c['all']),'staff_roles_count':len(c['staff']),'fondateur_roles_count':len(c['fondateur']),'haut_roles_count':len(c['haut']),'requests_enabled':True,'html_inject':True,'oauth_scope':'identify guilds.members.read'})
        if path=='/api/team': return self.send_json(team_data())
        if path=='/api/user/me':
            s=self.current_user(); return self.send_json({'ok':True,'user':s['user']}) if s else self.send_json({'ok':False},401)
        if path=='/api/users':
            if not self.current_admin(): return self.send_json({'ok':False},401)
            return self.send_json({'ok':True,'users':read_json(USERS,[])})
        if path=='/api/admin/me':
            s=self.current_admin(); return self.send_json({'ok':True,'admin':s['admin']}) if s else self.send_json({'ok':False,'configured':ready(True)},401)
        if path=='/api/discord/login':
            mode=(q.get('mode') or ['user'])[0]
            if not ready(mode=='admin'): return self.send_json({'ok':False,'error':'ENV Discord manquant sur Render'},500)
            state=secrets.token_urlsafe(24); nxt=(q.get('next') or (['/admin/'] if mode=='admin' else ['/']))[0]; red=self.redir(); OAUTH_STATES[state]={'expires':time.time()+600,'mode':mode,'next':nxt,'redirect_uri':red}; c=cfg()
            return self.redirect('https://discord.com/oauth2/authorize?'+urlencode({'client_id':c['cid'],'redirect_uri':red,'response_type':'code','scope':'identify guilds.members.read','state':state}))
        if path=='/api/discord/callback':
            state=(q.get('state') or [''])[0]; code=(q.get('code') or [''])[0]; saved=OAUTH_STATES.pop(state,None) or {'mode':'user','next':'/','redirect_uri':self.redir()}
            if not code: return self.redirect('/')
            try:
                token=exchange(code,saved.get('redirect_uri') or self.redir()); du=get_user(token['access_token'])
                mem=None
                try: mem=get_member(du['id'])
                except Exception as e:
                    print('bot member roles error',e)
                    try: mem=get_member_oauth(token['access_token'])
                    except Exception as e2: print('oauth member roles error',e2)
                item=upsert_user(du,mem)
                if saved.get('mode')=='admin' and not item.get('is_admin'): return self.redirect('/admin/?error=role')
                sid=secrets.token_urlsafe(32); USER_SESSIONS[sid]={'expires':time.time()+31536000,'user':item}
                cookies=[f'{USER_COOKIE}={sid}; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000',f'{DID_COOKIE}={item.get("discord_id")}; Path=/; SameSite=Lax; Max-Age=31536000']
                if item.get('is_admin'):
                    aid=secrets.token_urlsafe(32); ADMIN_SESSIONS[aid]={'expires':time.time()+31536000,'admin':item}; cookies.append(f'{ADMIN_COOKIE}={aid}; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000')
                return self.redirect(saved.get('next') or '/',cookies)
            except Exception as e:
                print('auth error',e); return self.send_html(f"Connexion Discord impossible.<br><br>Erreur exacte : <pre>{esc(e)}</pre><br>Redirect utilisé : <code>{esc(saved.get('redirect_uri') or self.redir())}</code>",500)
        if path=='/api/discord/logout':
            sid=self.cookie(USER_COOKIE); USER_SESSIONS.pop(sid,None) if sid else None
            return self.redirect('/',[f'{USER_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax',f'{ADMIN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax',f'{DID_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax'])
        if path=='/api/discord/admin-logout':
            sid=self.cookie(ADMIN_COOKIE); ADMIN_SESSIONS.pop(sid,None) if sid else None; return self.redirect('/admin/',f'{ADMIN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax')
        if path in ('/api/candidatures','/api/whitelist'):
            if not self.current_admin(): return self.send_json({'ok':False},401)
            return self.send_json({'ok':True,'rows':read_json(CANDIDATURES,[])})
        candidate=ROOT/path.lstrip('/')
        if path in ('/','/index.html'): candidate=ROOT/'index.html'
        elif candidate.is_dir(): candidate=candidate/'index.html'
        elif path!='/' and not candidate.exists() and not Path(path).suffix: candidate=ROOT/'index.html'
        if candidate.exists() and candidate.suffix.lower()=='.html': return self.serve_html_file(candidate)
        return super().do_GET()
    def do_POST(self):
        path=urlparse(self.path).path; data=self.body_json()
        if path=='/api/users/status':
            if not self.current_admin(): return self.send_json({'ok':False},401)
            u=set_status(data.get('discord_id'),data.get('status')); return self.send_json({'ok':bool(u),'user':u})
        if path in ('/api/candidatures/status','/api/whitelist/status'):
            if not self.current_admin(): return self.send_json({'ok':False},401)
            rows=read_json(CANDIDATURES,[]); row=next((x for x in rows if x.get('id')==data.get('id')),None)
            if not row: return self.send_json({'ok':False,'error':'introuvable'},404)
            st=data.get('status',row.get('status','pending')); row['status']=st; row['reviewed_at']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
            if row.get('discord_user_id'): set_status(row['discord_user_id'],st)
            write_json(CANDIDATURES,rows); return self.send_json({'ok':True,'candidature':row})
        s=self.current_user(); u=s.get('user') if s else None; rows=read_json(CANDIDATURES,[])
        row={'id':f"wl_{len(rows)+1}_{os.urandom(3).hex()}",'created_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'status':'pending',**(data if isinstance(data,dict) else {})}
        if u: row.update({'discord_user_id':u.get('discord_id'),'discord_username':u.get('username'),'discord_name':u.get('global_name'),'discord_avatar':u.get('avatar'),'discord_tag':u.get('username')})
        rows.insert(0,row); write_json(CANDIDATURES,rows); return self.send_json({'ok':True,'id':row['id']})

if __name__=='__main__':
    os.chdir(ROOT); port=int(os.environ.get('PORT','4174')); server=ThreadingHTTPServer(('0.0.0.0',port),Handler); print(f'NewAir web service on port {port}'); server.serve_forever()
