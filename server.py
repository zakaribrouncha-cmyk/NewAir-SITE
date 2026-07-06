from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from http import cookies
import json
import os
import secrets
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_FILE = DATA_DIR / "candidatures.json"
USERS_FILE = DATA_DIR / "users.json"
OAUTH_STATES = {}
ADMIN_SESSIONS = {}
USER_SESSIONS = {}
ADMIN_COOKIE = "newair_admin_session"
USER_COOKIE = "newair_user_session"
ACCEPTED_ROLE_ID = os.environ.get("DISCORD_ACCEPTED_ROLE_ID", "1523767412103708762").strip()
REFUSED_ROLE_ID = os.environ.get("DISCORD_REFUSED_ROLE_ID", "1523768172291948674").strip()


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path, payload):
    DATA_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_rows():
    return read_json(DATA_FILE, [])


def write_rows(rows):
    write_json(DATA_FILE, rows)


def read_users():
    return read_json(USERS_FILE, [])


def write_users(users):
    write_json(USERS_FILE, users)


def env_list(name):
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


def public_base_url():
    return os.environ.get("PUBLIC_BASE_URL") or os.environ.get("RENDER_EXTERNAL_URL") or "http://localhost:4174"


def discord_config():
    redirect_uri = os.environ.get("DISCORD_REDIRECT_URI") or f"{public_base_url().rstrip('/')}/api/discord/callback"
    all_roles = []
    all_roles += env_list("DISCORD_ADMIN_ROLE_IDS")
    all_roles += env_list("DISCORD_STAFF_ROLE_IDS")
    all_roles += env_list("DISCORD_SUPERADMIN_ROLE_IDS")
    all_roles += env_list("DISCORD_FONDATEUR_ROLE_IDS")
    all_roles += env_list("DISCORD_HAUT_GRADE_PANEL_ROLE_IDS")
    return {
        "client_id": os.environ.get("DISCORD_CLIENT_ID", "").strip(),
        "client_secret": os.environ.get("DISCORD_CLIENT_SECRET", "").strip(),
        "bot_token": os.environ.get("DISCORD_BOT_TOKEN", "").strip(),
        "guild_id": os.environ.get("DISCORD_GUILD_ID", "").strip(),
        "role_ids": all_roles,
        "staff_roles": env_list("DISCORD_STAFF_ROLE_IDS"),
        "superadmin_roles": env_list("DISCORD_SUPERADMIN_ROLE_IDS"),
        "fondateur_roles": env_list("DISCORD_FONDATEUR_ROLE_IDS"),
        "haut_grade_panel_roles": env_list("DISCORD_HAUT_GRADE_PANEL_ROLE_IDS"),
        "redirect_uri": redirect_uri,
    }


def discord_ready(require_admin_roles=False):
    cfg = discord_config()
    base = all([cfg["client_id"], cfg["client_secret"], cfg["bot_token"], cfg["guild_id"]])
    return bool(base and (cfg["role_ids"] or not require_admin_roles))


def discord_request(url, headers=None, data=None, method=None):
    request = Request(url, headers=headers or {}, data=data, method=method)
    with urlopen(request, timeout=12) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def exchange_discord_code(code):
    cfg = discord_config()
    body = urlencode({
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": cfg["redirect_uri"],
    }).encode("utf-8")
    return discord_request("https://discord.com/api/oauth2/token", {"Content-Type": "application/x-www-form-urlencoded"}, body)


def get_discord_user(access_token):
    return discord_request("https://discord.com/api/users/@me", {"Authorization": f"Bearer {access_token}"})


def get_discord_member(user_id):
    cfg = discord_config()
    return discord_request(f"https://discord.com/api/guilds/{cfg['guild_id']}/members/{user_id}", {"Authorization": f"Bot {cfg['bot_token']}"})


def discord_avatar(user):
    avatar = user.get("avatar")
    if not avatar:
        return ""
    ext = "gif" if avatar.startswith("a_") else "png"
    return f"https://cdn.discordapp.com/avatars/{user.get('id')}/{avatar}.{ext}?size=256"


def member_grade(roles):
    cfg = discord_config()
    roles = set(roles or [])
    if roles.intersection(set(cfg["haut_grade_panel_roles"])):
        return "Fondateur"
    if roles.intersection(set(cfg["fondateur_roles"])):
        return "Fondateur"
    if roles.intersection(set(cfg["superadmin_roles"])):
        return "SuperAdmin"
    if roles.intersection(set(cfg["staff_roles"])):
        return "Staff"
    if roles.intersection(set(env_list("DISCORD_ADMIN_ROLE_IDS"))):
        return "Admin"
    return None


def member_has_admin_role(member):
    roles = set(member.get("roles") or [])
    return bool(roles.intersection(set(discord_config()["role_ids"])))


def upsert_user(user):
    users = read_users()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    item = next((u for u in users if u.get("discord_id") == user.get("id")), None)
    payload = {
        "discord_id": user.get("id"),
        "username": user.get("username"),
        "global_name": user.get("global_name"),
        "avatar": discord_avatar(user),
        "status": item.get("status", "linked") if item else "linked",
        "linked_at": item.get("linked_at", now) if item else now,
        "last_login": now,
    }
    if item:
        item.update(payload)
    else:
        users.insert(0, payload)
        item = payload
    write_users(users)
    return item


def set_user_status(discord_id, status):
    users = read_users()
    item = next((u for u in users if u.get("discord_id") == discord_id), None)
    if item:
        item["status"] = status
        item["reviewed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_users(users)
    apply_whitelist_role(discord_id, status)
    return item


def bot_role(discord_id, role_id, method):
    if not discord_id or not role_id:
        return False
    cfg = discord_config()
    try:
        discord_request(
            f"https://discord.com/api/guilds/{cfg['guild_id']}/members/{discord_id}/roles/{role_id}",
            {"Authorization": f"Bot {cfg['bot_token']}"},
            data=b"" if method == "PUT" else None,
            method=method,
        )
        return True
    except Exception as exc:
        print("Discord role error:", exc)
        return False


def apply_whitelist_role(discord_id, status):
    if status == "accepted":
        bot_role(discord_id, REFUSED_ROLE_ID, "DELETE")
        return bot_role(discord_id, ACCEPTED_ROLE_ID, "PUT")
    if status == "rejected":
        bot_role(discord_id, ACCEPTED_ROLE_ID, "DELETE")
        return bot_role(discord_id, REFUSED_ROLE_ID, "PUT")
    return False


def discord_team():
    cfg = discord_config()
    if not cfg["bot_token"] or not cfg["guild_id"]:
        return {"members": []}
    try:
        data = discord_request(f"https://discord.com/api/guilds/{cfg['guild_id']}/members?limit=1000", {"Authorization": f"Bot {cfg['bot_token']}"})
        members = []
        for item in data:
            grade = member_grade(item.get("roles", []))
            if not grade:
                continue
            user = item.get("user", {})
            name = item.get("nick") or user.get("global_name") or user.get("username") or "Staff NewAir"
            members.append({"name": name, "role": grade, "discord_id": user.get("id", ""), "avatar": discord_avatar(user), "subtitle": f"Rôle Discord : {grade}"})
        return {"members": members}
    except Exception as exc:
        print("Discord team error:", exc)
        return {"members": []}


def cleanup_sessions():
    now = time.time()
    for store in (ADMIN_SESSIONS, USER_SESSIONS, OAUTH_STATES):
        for key in list(store.keys()):
            if store[key].get("expires", 0) < now:
                store.pop(key, None)


class NewAirHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".js": "application/javascript; charset=utf-8", ".mjs": "application/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml", ".webp": "image/webp", ".mp4": "video/mp4"}

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "content-type, authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, location, cookie_header=None):
        self.send_response(302)
        self.send_header("Location", location)
        if cookie_header:
            self.send_header("Set-Cookie", cookie_header)
        self.end_headers()

    def read_cookie(self, name):
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
            return jar[name].value if name in jar else None
        except Exception:
            return None

    def current_admin(self):
        cleanup_sessions()
        sid = self.read_cookie(ADMIN_COOKIE)
        session = ADMIN_SESSIONS.get(sid or "")
        return session if session and session.get("expires", 0) > time.time() else None

    def current_user(self):
        cleanup_sessions()
        sid = self.read_cookie(USER_COOKIE)
        session = USER_SESSIONS.get(sid or "")
        return session if session and session.get("expires", 0) > time.time() else None

    def require_admin(self):
        session = self.current_admin()
        if session:
            return session
        self.send_json({"ok": False, "error": "Connexion Discord admin requise"}, 401)
        return None

    def body_json(self):
        length = int(self.headers.get("content-length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8", errors="replace") if length else "{}"
        try:
            return json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            return {"raw": raw}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/team":
            return self.send_json(discord_team())

        if path == "/api/user/me":
            user = self.current_user()
            if not user:
                return self.send_json({"ok": False, "error": "Non connecté"}, 401)
            return self.send_json({"ok": True, "user": user["user"]})

        if path == "/api/users":
            if not self.require_admin():
                return
            return self.send_json({"ok": True, "users": read_users()})

        if path == "/api/admin/me":
            session = self.current_admin()
            if not session:
                return self.send_json({"ok": False, "configured": discord_ready(True), "error": "Non connecté à Discord ou rôle admin manquant"}, 401)
            return self.send_json({"ok": True, "admin": session["admin"]})

        if path == "/api/discord/login":
            mode = (query.get("mode") or ["user"])[0]
            if not discord_ready(mode == "admin"):
                return self.send_json({"ok": False, "error": "Configuration Discord manquante sur Render"}, 500)
            state = secrets.token_urlsafe(24)
            OAUTH_STATES[state] = {"expires": time.time() + 600, "mode": mode, "next": (query.get("next") or ["/compte"])[0]}
            cfg = discord_config()
            auth_url = "https://discord.com/oauth2/authorize?" + urlencode({"client_id": cfg["client_id"], "redirect_uri": cfg["redirect_uri"], "response_type": "code", "scope": "identify", "state": state})
            return self.redirect(auth_url)

        if path == "/api/discord/callback":
            state = (query.get("state") or [""])[0]
            code = (query.get("code") or [""])[0]
            saved = OAUTH_STATES.pop(state, None)
            if not code or not saved or saved.get("expires", 0) < time.time():
                return self.redirect("/login?error=discord_state")
            try:
                token = exchange_discord_code(code)
                user = get_discord_user(token["access_token"])
                item = upsert_user(user)
                if saved.get("mode") == "admin":
                    member = get_discord_member(user["id"])
                    if not member_has_admin_role(member):
                        return self.redirect("/admin/?error=role")
                    grade = member_grade(member.get("roles", [])) or "Admin"
                    sid = secrets.token_urlsafe(32)
                    ADMIN_SESSIONS[sid] = {"expires": time.time() + 86400, "admin": {**item, "grade": grade, "roles": member.get("roles", [])}}
                    return self.redirect("/admin/", f"{ADMIN_COOKIE}={sid}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400")
                sid = secrets.token_urlsafe(32)
                USER_SESSIONS[sid] = {"expires": time.time() + 31536000, "user": item}
                return self.redirect(saved.get("next") or "/compte", f"{USER_COOKIE}={sid}; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000")
            except Exception as exc:
                print("Discord auth error:", exc)
                return self.redirect("/login?error=discord")

        if path == "/api/discord/logout":
            sid = self.read_cookie(USER_COOKIE)
            if sid:
                USER_SESSIONS.pop(sid, None)
            return self.redirect("/login", f"{USER_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax")

        if path == "/api/discord/admin-logout":
            sid = self.read_cookie(ADMIN_COOKIE)
            if sid:
                ADMIN_SESSIONS.pop(sid, None)
            return self.redirect("/admin/", f"{ADMIN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax")

        if path in ("/api/candidatures", "/api/whitelist"):
            if not self.require_admin():
                return
            return self.send_json({"ok": True, "rows": read_rows()})

        candidate = ROOT / path.lstrip("/")
        if path != "/" and not candidate.exists() and not Path(path).suffix:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        payload = self.body_json()

        if path == "/api/users/status":
            if not self.require_admin():
                return
            user = set_user_status(payload.get("discord_id"), payload.get("status"))
            return self.send_json({"ok": bool(user), "user": user})

        if path in ("/api/candidatures/status", "/api/whitelist/status"):
            if not self.require_admin():
                return
            rows = read_rows()
            row = next((r for r in rows if r.get("id") == payload.get("id")), None)
            if not row:
                return self.send_json({"ok": False, "error": "Candidature introuvable"}, 404)
            status = payload.get("status", row.get("status", "pending"))
            row["status"] = status
            row["reviewed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            if row.get("discord_user_id"):
                set_user_status(row["discord_user_id"], status)
            write_rows(rows)
            return self.send_json({"ok": True, "candidature": row})

        user_session = self.current_user()
        user = user_session.get("user") if user_session else None
        rows = read_rows()
        data = payload.get("data") if isinstance(payload, dict) and isinstance(payload.get("data"), dict) else payload
        row = {"id": f"wl_{len(rows) + 1}_{os.urandom(3).hex()}", "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "path": path, "status": "pending", **(data if isinstance(data, dict) else {"data": data})}
        if user:
            row.update({"discord_user_id": user.get("discord_id"), "discord_username": user.get("username"), "discord_name": user.get("global_name"), "discord_avatar": user.get("avatar"), "discord_tag": user.get("username")})
        rows.insert(0, row)
        write_rows(rows)
        return self.send_json({"ok": True, "id": row["id"], "message": "Candidature reçue"})


if __name__ == "__main__":
    os.chdir(ROOT)
    port = int(os.environ.get("PORT", "4174"))
    host = os.environ.get("HOST", "0.0.0.0")
    server = ThreadingHTTPServer((host, port), NewAirHandler)
    print(f"NewAir en ligne sur http://{host}:{port}/")
    server.serve_forever()
