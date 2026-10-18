"""Same UI and Python engine without Streamlit: python3 preview.py --port 8501."""
import argparse
import gzip
import json
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from scenario_workspace import build_workspace, validate_workspace


def accepts_gzip(header):
    offers = {}
    for part in header.lower().split(','):
        coding, *params = part.strip().split(';')
        quality = 1.0
        for param in params:
            if param.strip().startswith('q='):
                try:
                    quality = float(param.strip()[2:])
                except ValueError:
                    quality = 0.0
        offers[coding] = quality if 0 <= quality <= 1 else 0.0
    return offers.get('gzip', offers.get('*', 0)) > 0


@lru_cache(maxsize=16)
def _encoded_workspace(items, compressed):
    payload = build_workspace(dict(items))
    body = json.dumps(payload, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':')).encode()
    if compressed and len(body) >= 2048:
        return gzip.compress(body, compresslevel=3, mtime=0), 'gzip'
    return body, None


def response_bytes(values=None, compressed=False):
    # Validate every request before using a canonical, bounded cache key.
    settings = validate_workspace(values)
    return _encoded_workspace(tuple(sorted(settings.items())), compressed)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent / "orbit_ui"), **kwargs)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/experiment":
            self.send_experiment()
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
            self.send_experiment(values)
        except (ValueError, TypeError) as exc:
            self.send_json({"error": str(exc)}, 400)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()
        self.send_body(body, status)

    def send_experiment(self, values=None):
        body, encoding = response_bytes(values, accepts_gzip(self.headers.get('Accept-Encoding', '')))
        self.send_body(body, 200, encoding)

    def send_body(self, body, status, encoding=None):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Vary", "Accept-Encoding")
        if encoding:
            self.send_header("Content-Encoding", encoding)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # A superseded slider request may have been cancelled.


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    print(f"ORBIT LAB: http://127.0.0.1:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
