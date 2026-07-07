from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from http import cookies
import json
import os
import secrets
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CANDIDATURES = DATA / "candidatures.json"
USERS = DATA / "users.json"
ADMIN_COOKIE = "newair_admin_session"
USER_COOKIE = "newair_user_session"
ADMIN_SESSIONS = {}
USER_SESSIONS = {}
OAUTH_STATES = {}
ACCEPTED_ROLE_ID = os.environ.get("DISCORD_ACCEPTED_ROLE_ID", "1523767412103708762").strip()
REFUSED_ROLE_ID = os.environ.get("DISCORD_REFUSED_ROLE_ID", "1523768172291948674").strip()


def clean(value):
    value = str(value or "").strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1].strip()
    return value


def env(name):
    return clean(os.environ.get(name, ""))


def env_list(name):
    return [clean(x) for x in os.environ.get(name, "").split(",") if clean(x)]


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path, value):
    DATA.mkdir(exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def cfg():
    admin = env_list("DISCORD_ADMIN_ROLE_IDS")
    staff = env_list("DISCORD_STAFF_ROLE_IDS")
    superadmin = env_list("DISCORD_SUPERADMIN_ROLE_IDS")
    fondateur = env_list("DISCORD_FONDATEUR_ROLE_IDS")
    haut = env_list("DISCORD_HAUT_GRADE_PANEL_ROLE_IDS")
    return {
        "client_id": env("DISCORD_CLIENT_ID"),
        "client_secret": env("DISCORD_CLIENT_SECRET"),
        "bot_token": env("DISCORD_BOT_TOKEN"),
        "guild_id": env("DISCORD_GUILD_ID"),
        "redirect_uri_env": env("DISCORD_REDIRECT_URI"),
        "admin": admin,
        "staff": staff,
        "superadmin": superadmin,
        "fondateur": fondateur,
        "haut": haut,
        "all_admin_roles": admin + staff + superadmin + fondateur + haut,
    }


def ready(need_roles=False):
    c = cfg()
    base = c["client_id"] and c["client_secret"] and c["bot_token"] and c["guild_id"]
    return bool(base and (c["all_admin_roles"] or not need_roles))


def call_json(url, headers=None, data=None, method=None):
    req = Request(url, headers=headers or {}, data=data, method=method)
    try:
        with urlopen(req, timeout=12) as res:
            raw = res.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            detail = json.loads(raw)
        except Exception:
            detail = raw
        raise RuntimeError(f"HTTP {e.code} Discord: {detail}")


def avatar(user):
    a = user.get("avatar")
    if not a:
        return "/assets/newair-logo-swirl.png"
    ext = "gif" if a.startswith("a_") else "png"
    return f"https://cdn.discordapp.com/avatars/{user.get('id')}/{a}.{ext}?size=256"


def grade_from_roles(roles):
    c = cfg()
    roles = set(roles or [])
    if roles.intersection(set(c["haut"])) or roles.intersection(set(c["fondateur"])):
        return "Fondateur"
    if roles.intersection(set(c["superadmin"])):
        return "SuperAdmin"
    if roles.intersection(set(c["staff"])):
        return "Staff"
    if roles.intersection(set(c["admin"])):
        return "Admin"
    return None


def exchange_code(code, redirect_uri):
    c = cfg()
    body = urlencode({
        "client_id": c["client_id"],
        "client_secret": c["client_secret"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }).encode("utf-8")
    return call_json("https://discord.com/api/oauth2/token", {"Content-Type": "application/x-www-form-urlencoded"}, body)


def discord_user(access_token):
    return call_json("https://discord.com/api/users/@me", {"Authorization": "Bearer " + access_token})


def discord_member(user_id):
    c = cfg()
    return call_json(f"https://discord.com/api/guilds/{c['guild_id']}/members/{user_id}", {"Authorization": "Bot " + c["bot_token"]})


def upsert_user(user):
    rows = read_json(USERS, [])
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    item = next((x for x in rows if x.get("discord_id") == user.get("id")), None)
    data = {
        "discord_id": user.get("id"),
        "username": user.get("username"),
        "global_name": user.get("global_name") or user.get("username"),
        "avatar": avatar(user),
        "status": item.get("status", "linked") if item else "linked",
        "linked_at": item.get("linked_at", now) if item else now,
        "last_login": now,
    }
    if item:
        item.update(data)
    else:
        rows.insert(0, data)
        item = data
    write_json(USERS, rows)
    return item


def put_role(discord_id, role_id, method):
    if not discord_id or not role_id:
        return False
    c = cfg()
    try:
        call_json(f"https://discord.com/api/guilds/{c['guild_id']}/members/{discord_id}/roles/{role_id}", {"Authorization": "Bot " + c["bot_token"]}, data=b"" if method == "PUT" else None, method=method)
        return True
    except Exception as e:
        print("role error", e)
        return False


def set_status(discord_id, status):
    rows = read_json(USERS, [])
    item = next((x for x in rows if x.get("discord_id") == discord_id), None)
    if item:
        item["status"] = status
        item["reviewed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_json(USERS, rows)
    if status == "accepted":
        put_role(discord_id, REFUSED_ROLE_ID, "DELETE")
        put_role(discord_id, ACCEPTED_ROLE_ID, "PUT")
    if status == "rejected":
        put_role(discord_id, ACCEPTED_ROLE_ID, "DELETE")
        put_role(discord_id, REFUSED_ROLE_ID, "PUT")
    return item


def esc(v):
    return str(v or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def account_html(user):
    name = user.get("global_name") or user.get("username") or "Compte"
    av = user.get("avatar") or "/assets/newair-logo-swirl.png"
    status = user.get("status") or "linked"
    return f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Compte NewAir</title><link rel='stylesheet' href='/assets/styles-Db9UqP69.css'><style>body{{margin:0;background:#000;color:#fff;font-family:Arial,Helvetica,sans-serif}}.nav{{height:80px;display:flex;align-items:center;justify-content:center;gap:30px;background:rgba(0,0,0,.72);border-bottom:1px solid rgba(255,255,255,.08)}}.nav a,.pill{{color:#fff;text-decoration:none;font-size:12px;letter-spacing:.22em;text-transform:uppercase}}.pill{{display:flex;align-items:center;gap:8px;border:1px solid rgba(95,150,214,.55);border-radius:999px;padding:7px 12px;letter-spacing:.08em}}.pill img{{width:28px;height:28px;border-radius:999px;object-fit:cover}}.wrap{{max-width:1000px;margin:0 auto;padding:90px 22px}}.k{{font-size:11px;letter-spacing:.4em;color:#9fc3ef;text-transform:uppercase}}h1{{font-family:Impact,Arial Black,sans-serif;font-size:70px;letter-spacing:.06em;margin:18px 0}}.card{{border:1px solid rgba(95,150,214,.3);background:rgba(5,10,20,.88);border-radius:18px;padding:30px}}.profile{{display:flex;align-items:center;gap:18px}}.avatar{{width:82px;height:82px;border-radius:999px;object-fit:cover;border:1px solid rgba(95,150,214,.6)}}.muted{{color:rgba(255,255,255,.58)}}.btn{{display:inline-flex;margin-top:22px;margin-right:10px;padding:12px 16px;border:1px solid rgba(95,150,214,.65);border-radius:9px;color:white;text-decoration:none;text-transform:uppercase;letter-spacing:.18em;font-weight:900;font-size:12px;background:#0b2a5b}}</style></head><body><nav class='nav'><a href='/'>Accueil</a><a href='/equipe/'>Équipe</a><a href='/whitelist'>Whitelist</a><a href='/compte'>Compte</a><span class='pill'><img src='{esc(av)}' alt=''>{esc(name)}</span></nav><main class='wrap'><div class='k'>Espace joueur</div><h1>MON COMPTE</h1><section class='card'><div class='profile'><img class='avatar' src='{esc(av)}' alt=''><div><h2>{esc(name)}</h2><p class='muted'>@{esc(user.get('username'))} · ID {esc(user.get('discord_id'))}</p><p>Statut candidature : <b>{esc(status)}</b></p></div></div><a class='btn' href='/whitelist'>Faire ma whitelist</a><a class='btn' href='/api/discord/logout'>Déconnexion</a></section></main></body></html>"""


def team_data():
    c = cfg()
    if not c["bot_token"] or not c["guild_id"]:
        return {"members": []}
    try:
        data = call_json(f"https://discord.com/api/guilds/{c['guild_id']}/members?limit=1000", {"Authorization": "Bot " + c["bot_token"]})
        members = []
        for m in data:
            grade = grade_from_roles(m.get("roles", []))
            if not grade:
                continue
            u = m.get("user", {})
            name = m.get("nick") or u.get("global_name") or u.get("username") or "Staff NewAir"
            members.append({"name": name, "role": grade, "discord_id": u.get("id"), "avatar": avatar(u), "subtitle": "Rôle Discord : " + grade})
        return {"members": members}
    except Exception as e:
        print("team error", e)
        return {"members": []}


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".js": "application/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8", ".mp4": "video/mp4", ".webp": "image/webp", ".svg": "image/svg+xml"}

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "content-type, authorization")
        super().end_headers()

    def send_json(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, loc, cookie=None):
        self.send_response(302)
        self.send_header("Location", loc)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def current_url_base(self):
        proto = self.headers.get("X-Forwarded-Proto") or "https"
        host = self.headers.get("Host") or env("PUBLIC_BASE_URL").replace("https://", "").replace("http://", "") or "localhost:4174"
        return f"{proto}://{host}".rstrip("/")

    def redirect_uri(self):
        return cfg()["redirect_uri_env"] or self.current_url_base() + "/api/discord/callback"

    def cookie(self, name):
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
            return jar[name].value if name in jar else None
        except Exception:
            return None

    def current_admin(self):
        sid = self.cookie(ADMIN_COOKIE)
        s = ADMIN_SESSIONS.get(sid or "")
        return s if s and s.get("expires", 0) > time.time() else None

    def current_user(self):
        sid = self.cookie(USER_COOKIE)
        s = USER_SESSIONS.get(sid or "")
        return s if s and s.get("expires", 0) > time.time() else None

    def body_json(self):
        raw = self.rfile.read(int(self.headers.get("content-length", "0") or "0")).decode("utf-8", "replace")
        try:
            return json.loads(raw) if raw.strip() else {}
        except Exception:
            return {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        q = parse_qs(parsed.query)
        if path in ("/login", "/login/"):
            return self.redirect("/api/discord/login?mode=user&next=/")
        if path in ("/compte", "/compte/"):
            s = self.current_user()
            return self.send_html(account_html(s["user"])) if s else self.redirect("/login")
        if path == "/api/discord/debug":
            c = cfg()
            return self.send_json({
                "ok": True,
                "client_id_set": bool(c["client_id"]),
                "client_secret_length": len(c["client_secret"]),
                "bot_token_set": bool(c["bot_token"]),
                "guild_id_set": bool(c["guild_id"]),
                "redirect_uri_used": self.redirect_uri(),
                "admin_roles_count": len(c["all_admin_roles"]),
            })
        if path == "/api/team":
            return self.send_json(team_data())
        if path == "/api/user/me":
            s = self.current_user()
            return self.send_json({"ok": True, "user": s["user"]}) if s else self.send_json({"ok": False}, 401)
        if path == "/api/users":
            if not self.current_admin():
                return self.send_json({"ok": False}, 401)
            return self.send_json({"ok": True, "users": read_json(USERS, [])})
        if path == "/api/admin/me":
            s = self.current_admin()
            return self.send_json({"ok": True, "admin": s["admin"]}) if s else self.send_json({"ok": False, "configured": ready(True)}, 401)
        if path == "/api/discord/login":
            mode = (q.get("mode") or ["user"])[0]
            if not ready(mode == "admin"):
                return self.send_json({"ok": False, "error": "ENV Discord manquant sur Render"}, 500)
            state = secrets.token_urlsafe(24)
            next_url = (q.get("next") or (["/admin/"] if mode == "admin" else ["/"]))[0]
            redirect_uri = self.redirect_uri()
            OAUTH_STATES[state] = {"expires": time.time() + 600, "mode": mode, "next": next_url, "redirect_uri": redirect_uri}
            c = cfg()
            url = "https://discord.com/oauth2/authorize?" + urlencode({"client_id": c["client_id"], "redirect_uri": redirect_uri, "response_type": "code", "scope": "identify", "state": state})
            return self.redirect(url)
        if path == "/api/discord/callback":
            state = (q.get("state") or [""])[0]
            code = (q.get("code") or [""])[0]
            saved = OAUTH_STATES.pop(state, None) or {"mode": "user", "next": "/", "redirect_uri": self.redirect_uri()}
            if not code:
                return self.redirect("/")
            try:
                token = exchange_code(code, saved.get("redirect_uri") or self.redirect_uri())
                u = discord_user(token["access_token"])
                item = upsert_user(u)
                if saved.get("mode") == "admin":
                    member = discord_member(u["id"])
                    grade = grade_from_roles(member.get("roles", []))
                    if not grade:
                        return self.redirect("/admin/?error=role")
                    sid = secrets.token_urlsafe(32)
                    ADMIN_SESSIONS[sid] = {"expires": time.time() + 86400, "admin": {**item, "grade": grade, "roles": member.get("roles", [])}}
                    return self.redirect(saved.get("next") or "/admin/", f"{ADMIN_COOKIE}={sid}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400")
                sid = secrets.token_urlsafe(32)
                USER_SESSIONS[sid] = {"expires": time.time() + 31536000, "user": item}
                return self.redirect(saved.get("next") or "/", f"{USER_COOKIE}={sid}; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000")
            except Exception as e:
                print("auth error", e)
                return self.send_html(f"Connexion Discord impossible.<br><br>Erreur exacte : <pre>{esc(e)}</pre><br>Redirect utilisé : <code>{esc(saved.get('redirect_uri') or self.redirect_uri())}</code>", 500)
        if path == "/api/discord/logout":
            sid = self.cookie(USER_COOKIE)
            if sid:
                USER_SESSIONS.pop(sid, None)
            return self.redirect("/", f"{USER_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax")
        if path == "/api/discord/admin-logout":
            sid = self.cookie(ADMIN_COOKIE)
            if sid:
                ADMIN_SESSIONS.pop(sid, None)
            return self.redirect("/admin/", f"{ADMIN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax")
        if path in ("/api/candidatures", "/api/whitelist"):
            if not self.current_admin():
                return self.send_json({"ok": False}, 401)
            return self.send_json({"ok": True, "rows": read_json(CANDIDATURES, [])})
        candidate = ROOT / path.lstrip("/")
        if path != "/" and not candidate.exists() and not Path(path).suffix:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        data = self.body_json()
        if path == "/api/users/status":
            if not self.current_admin():
                return self.send_json({"ok": False}, 401)
            user = set_status(data.get("discord_id"), data.get("status"))
            return self.send_json({"ok": bool(user), "user": user})
        if path in ("/api/candidatures/status", "/api/whitelist/status"):
            if not self.current_admin():
                return self.send_json({"ok": False}, 401)
            rows = read_json(CANDIDATURES, [])
            row = next((x for x in rows if x.get("id") == data.get("id")), None)
            if not row:
                return self.send_json({"ok": False, "error": "introuvable"}, 404)
            status = data.get("status", row.get("status", "pending"))
            row["status"] = status
            row["reviewed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            if row.get("discord_user_id"):
                set_status(row["discord_user_id"], status)
            write_json(CANDIDATURES, rows)
            return self.send_json({"ok": True, "candidature": row})
        user_session = self.current_user()
        user = user_session.get("user") if user_session else None
        rows = read_json(CANDIDATURES, [])
        row = {"id": f"wl_{len(rows)+1}_{os.urandom(3).hex()}", "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "status": "pending", **(data if isinstance(data, dict) else {})}
        if user:
            row.update({"discord_user_id": user.get("discord_id"), "discord_username": user.get("username"), "discord_name": user.get("global_name"), "discord_avatar": user.get("avatar"), "discord_tag": user.get("username")})
        rows.insert(0, row)
        write_json(CANDIDATURES, rows)
        return self.send_json({"ok": True, "id": row["id"]})


if __name__ == "__main__":
    os.chdir(ROOT)
    port = int(os.environ.get("PORT", "4174"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"NewAir web service on port {port}")
    server.serve_forever()
