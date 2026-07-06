from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_FILE = DATA_DIR / "candidatures.json"


class NewAirHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("content-length", "0") or "0")
        raw_body = self.rfile.read(length).decode("utf-8", errors="replace") if length else "{}"
        try:
            payload = json.loads(raw_body) if raw_body.strip() else {}
        except json.JSONDecodeError:
            payload = {"raw": raw_body}

        DATA_DIR.mkdir(exist_ok=True)
        try:
            rows = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            rows = []

        row = {
            "id": f"wl_{len(rows) + 1}",
            "path": urlparse(self.path).path,
            "status": "pending",
            "data": payload,
        }
        rows.insert(0, row)
        DATA_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

        body = json.dumps({"ok": True, "id": row["id"], "message": "Candidature reçue"}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    os.chdir(ROOT)
    port = int(os.environ.get("PORT", "4174"))
    server = ThreadingHTTPServer(("127.0.0.1", port), NewAirHandler)
    print(f"NewAir local: http://localhost:{port}/")
    server.serve_forever()
