from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_FILE = DATA_DIR / "candidatures.json"


def read_rows():
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def write_rows(rows):
    DATA_DIR.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


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

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/api/candidatures", "/api/whitelist"):
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
