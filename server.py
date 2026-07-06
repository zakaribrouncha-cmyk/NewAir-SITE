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
SESSIONS = {}
OAUTH_STATES = {}
SESSION_COOKIE = "newair_admin_session"


def read_rows():
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def write_rows(rows):
    DATA_DIR.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


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


def discord_ready():
    cfg = discord_config()
    return all([cfg["client_id"], cfg["client_secret"], cfg["bot_token"], cfg["guild_id"], cfg["role_ids"]])


def discord_request(url, headers=None, data=None):
    request = Request(url, headers=headers or {}, data=data)
    with urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def exchange_discord_code(code):
    cfg = discord_config()
    body = urlencode({
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": cfg["redirect_uri"],
    }).encode("utf-8")
    return discord_request(
        "https://discord.com/api/oauth2/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=body,
    )


def get_discord_user(access_token):
    return discord_request(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
    )


def get_discord_member(user_id):
    cfg = discord_config()
    return discord_request(
        f"https://discord.com/api/guilds/{cfg['guild_id']}/members/{user_id}",
        headers={"Authorization": f"Bot {cfg['bot_token']}"},
    )


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


def discord_avatar(user):
    avatar = user.get("avatar")
    if not avatar:
        return ""
    ext = "gif" if avatar.startswith("a_") else "png"
    return f"https://cdn.discordapp.com/avatars/{user.get('id')}/{avatar}.{ext}?size=256"


def discord_team():
    cfg = discord_config()
    if not cfg["bot_token"] or not cfg["guild_id"]:
        return {"members": []}
    try:
        data = discord_request(
            f"https://discord.com/api/guilds/{cfg['guild_id']}/members?limit=1000",
            headers={"Authorization": f"Bot {cfg['bot_token']}"},
        )
        members = []
        for item in data:
            grade = member_grade(item.get("roles", []))
            if not grade:
                continue
            user = item.get("user", {})
            name = item.get("nick") or user.get("global_name") or user.get("username") or "Staff NewAir"
            members.append({
                "name": name,
                "role": grade,
                "discord_id": user.get("id", ""),
                "avatar": discord_avatar(user),
                "subtitle": f"Rôle Discord : {grade}",
            })
        return {"members": members}
    except Exception as exc:
        print("Discord team error:", exc)
        return {"members": []}


def cleanup_sessions():
    now = time.time()
    for store in (SESSIONS, OAUTH_STATES):
        for key in list(store.keys()):
            if store[key].get("expires", 0) < now:
                store.pop(key, None)


class NewAirHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript; charset=utf-8",
        ".mjs": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
    }

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
        raw = self.headers.get("Cookie", "")
        jar = cookies.SimpleCookie()
        try:
            jar.load(raw)
            return jar[name].value if name in jar else None
        except Exception:
            return None

    def current_admin(self):
        cleanup_sessions()
        session_id = self.read_cookie(SESSION_COOKIE)
        if not session_id:
            return None
        session = SESSIONS.get(session_id)
        if not session or session.get("expires", 0) < time.time():
            return None
        return session

    def require_admin(self):
        session = self.current_admin()
        if session:
            return session
        self.send_json({"ok": False, "error": "Connexion Discord admin requise"}, 401)
        return None

    def do_GET(self):
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)

        if path == "/api/team":
            return self.send_json(discord_team())

        if path == "/api/admin/me":
            session = self.current_admin()
            if not session:
                return self.send_json({
                    "ok": False,
                    "configured": discord_ready(),
                    "error": "Non connecté à Discord ou rôle admin manquant",
                }, 401)
            return self.send_json({"ok": True, "admin": session["admin"]})

        if path == "/api/discord/login":
            if not discord_ready():
                return self.send_json({
                    "ok": False,
                    "error": "Configuration Discord manquante sur Render",
                    "required_env": [
                        "PUBLIC_BASE_URL",
                        "DISCORD_CLIENT_ID",
                        "DISCORD_CLIENT_SECRET",
                        "DISCORD_BOT_TOKEN",
                        "DISCORD_GUILD_ID",
                        "DISCORD_ADMIN_ROLE_IDS",
                        "DISCORD_STAFF_ROLE_IDS",
                        "DISCORD_SUPERADMIN_ROLE_IDS",
                        "DISCORD_FONDATEUR_ROLE_IDS",
                        "DISCORD_HAUT_GRADE_PANEL_ROLE_IDS",
                    ],
                }, 500)
            cleanup_sessions()
            state = secrets.token_urlsafe(24)
            OAUTH_STATES[state] = {"expires": time.time() + 600}
            cfg = discord_config()
            auth_url = "https://discord.com/oauth2/authorize?" + urlencode({
                "client_id": cfg["client_id"],
                "redirect_uri": cfg["redirect_uri"],
                "response_type": "code",
                "scope": "identify",
                "state": state,
                "prompt": "none",
            })
            return self.redirect(auth_url)

        if path == "/api/discord/callback":
            state = (query.get("state") or [""])[0]
            code = (query.get("code") or [""])[0]
            saved_state = OAUTH_STATES.pop(state, None)
            if not code or not saved_state or saved_state.get("expires", 0) < time.time():
                return self.redirect("/admin/?error=discord_state")
            try:
                token = exchange_discord_code(code)
                user = get_discord_user(token["access_token"])
                member = get_discord_member(user["id"])
                if not member_has_admin_role(member):
                    return self.redirect("/admin/?error=role")
                session_id = secrets.token_urlsafe(32)
                grade = member_grade(member.get("roles", [])) or "Admin"
                SESSIONS[session_id] = {
                    "expires": time.time() + 86400,
                    "admin": {
                        "id": user.get("id"),
                        "username": user.get("username"),
                        "global_name": user.get("global_name"),
                        "avatar": user.get("avatar"),
                        "roles": member.get("roles", []),
                        "grade": grade,
                    },
                }
                cookie_header = f"{SESSION_COOKIE}={session_id}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400"
                return self.redirect("/admin/", cookie_header=cookie_header)
            except Exception as exc:
                print("Discord auth error:", exc)
                return self.redirect("/admin/?error=discord")

        if path == "/api/discord/logout":
            session_id = self.read_cookie(SESSION_COOKIE)
            if session_id:
                SESSIONS.pop(session_id, None)
            return self.redirect("/admin/", cookie_header=f"{SESSION_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax")

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
        length = int(self.headers.get("content-length", "0") or "0")
        raw_body = self.rfile.read(length).decode("utf-8", errors="replace") if length else "{}"
        try:
            payload = json.loads(raw_body) if raw_body.strip() else {}
        except json.JSONDecodeError:
            payload = {"raw": raw_body}

        if path in ("/api/candidatures/status", "/api/whitelist/status"):
            if not self.require_admin():
                return
            rows = read_rows()
            row_id = payload.get("id")
            row = next((r for r in rows if r.get("id") == row_id), None)
            if not row:
                return self.send_json({"ok": False, "error": "Candidature introuvable"}, 404)
            row["status"] = payload.get("status", row.get("status", "pending"))
            row["reviewed_at"] = payload.get("reviewed_at") or "reviewed"
            write_rows(rows)
            return self.send_json({"ok": True, "candidature": row})

        rows = read_rows()
        data = payload.get("data") if isinstance(payload, dict) and isinstance(payload.get("data"), dict) else payload
        row = {
            "id": f"wl_{len(rows) + 1}_{os.urandom(3).hex()}",
            "created_at": payload.get("created_at") if isinstance(payload, dict) else None,
            "path": path,
            "status": "pending",
            **(data if isinstance(data, dict) else {"data": data}),
        }
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
