"""Same UI and Python engine without Streamlit: python3 preview.py --port 8501."""
import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from scenario_workspace import build_workspace


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent / "orbit_ui"), **kwargs)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/experiment":
            self.send_json(build_workspace())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != "/api/experiment":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 < length < 4096:
                raise ValueError("잘못된 요청 크기입니다.")
            values = json.loads(self.rfile.read(length))
            if not isinstance(values, dict):
                raise ValueError("설정은 객체여야 합니다.")
            self.send_json(build_workspace(values))
        except (ValueError, TypeError) as exc:
            self.send_json({"error": str(exc)}, 400)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    print(f"ORBIT LAB: http://127.0.0.1:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
