"""Local console. stdlib only, so `omnitrace serve` needs no extra packages."""

from __future__ import annotations

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from src.cases import get_case, list_cases
from src.console_page import PAGE
from src.otel_trace import export_otlp
from src.session import OmniTraceSession

_GUIDE_VIDEO = Path(__file__).resolve().parent.parent / "examples" / "guide.mp4"


class App:
    def __init__(self) -> None:
        self.session = OmniTraceSession()
        self.lock = threading.Lock()


class ConsoleServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], app: App) -> None:
        self.app = app
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def _route(self) -> str:
        path = self.path.split("?", 1)[0]
        if len(path) > 1:
            path = path.rstrip("/")
        return path

    def do_GET(self) -> None:  # noqa: N802
        path = self._route()
        if path in ("/", "/index.html"):
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/session":
            self._json(200, self.server.app.session.view())
            return
        if path == "/api/cases":
            self._json(200, {"cases": [case.to_dict() for case in list_cases()]})
            return
        if path == "/guide.mp4":
            self._send_file(_GUIDE_VIDEO, "video/mp4")
            return
        if path.startswith("/api/sample/"):
            case_id = path.removeprefix("/api/sample/").strip("/")
            try:
                payload = export_otlp(get_case(case_id))
            except KeyError as exc:
                self._json(404, {"error": str(exc)})
                return
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Disposition", f'attachment; filename="{case_id}.otlp.json"')
            self.end_headers()
            self.wfile.write(body)
            return
        self._json(404, {"error": "No such path"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._payload()
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
            return
        path = self._route()
        app: App = self.server.app
        with app.lock:
            try:
                if path == "/api/run":
                    case_id = str(payload.get("case_id") or "supply")
                    app.session = OmniTraceSession()
                    app.session.run(get_case(case_id))
                    self._json(200, app.session.view())
                    return
                if path == "/api/load":
                    app.session = OmniTraceSession()
                    app.session.load(payload)
                    self._json(200, app.session.view())
                    return
                session = app.session
                if path == "/api/isolate":
                    session.isolate()
                    self._json(200, session.view())
                    return
                if path == "/api/fork":
                    session.fork()
                    self._json(200, session.view())
                    return
                if path == "/api/inspect":
                    session.inspect()
                    self._json(200, session.view())
                    return
            except (RuntimeError, ValueError, KeyError) as exc:
                self._json(400, {"error": str(exc)})
                return
        self._json(404, {"error": "No such path"})

    def _payload(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("Body must be a JSON object")
        return data

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._bytes(status, "application/json; charset=utf-8", body)

    def _send_file(self, file: Path, content_type: str) -> None:
        if not file.is_file():
            self._json(404, {"error": "No tutorial video yet. Add examples/guide.mp4"})
            return
        size = file.stat().st_size
        start, end = 0, size - 1
        status = 200
        range_header = self.headers.get("Range")
        if range_header:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
            if match is None or not (match.group(1) or match.group(2)):
                self._bytes(416, "text/plain; charset=utf-8", b"Invalid range")
                return
            if match.group(1):
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else size - 1
            else:
                tail = int(match.group(2))
                start = max(size - tail, 0)
            if start >= size or start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            end = min(end, size - 1)
            status = 206
        length = end - start + 1
        with file.open("rb") as handle:
            handle.seek(start)
            chunk = handle.read(length)
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(len(chunk)))
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(chunk)

    def _bytes(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def make_server(host: str = "127.0.0.1", port: int = 8765) -> ConsoleServer:
    return ConsoleServer((host, port), App())


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = make_server(host, port)
    bound_host, bound_port = server.server_address
    print(f"OmniTrace console: http://{bound_host}:{bound_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
