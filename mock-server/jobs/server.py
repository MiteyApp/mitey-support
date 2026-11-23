"""A tiny stateful job API for demoing Mitey workflows (poll, retry, chained ids).

Standard library only; state lives in memory and resets on restart.

  POST /login                          -> {"token": "..."}
  POST /submissions        (Bearer)    -> 201 {"id", "status": "processing"}
  PUT  /submissions/{id}/files/{name}  -> {"name", "size"}
  GET  /submissions/{id}               -> {"id", "status", "files"}  status turns
                                          "done" PROCESSING_SECONDS after the first
                                          file upload ("failed" if the title is "fail")
  POST /submissions/{id}/submit        -> {"receipt"}, or 409 until it's done
  GET  /flaky?key=...                  -> 503 (Retry-After: 1) twice per key, then 200
"""

import json
import os
import re
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROCESSING_SECONDS = float(os.environ.get("PROCESSING_SECONDS", "4"))
MAX_BODY = 1 << 20

tokens = set()
submissions = {}
flaky_calls = {}


class Handler(BaseHTTPRequestHandler):
    server_version = "mitey-jobs/1"

    def _send(self, status, payload, headers=None):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
        return self.rfile.read(n) if n else b""

    def _authed(self):
        auth = self.headers.get("Authorization", "")
        return auth.startswith("Bearer ") and auth[7:] in tokens

    def _status(self, sub):
        if sub["title"] == "fail":
            return "failed"
        if sub["first_file_at"] and time.time() - sub["first_file_at"] >= PROCESSING_SECONDS:
            return "done"
        return "processing"

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/login":
            token = f"demo-{uuid.uuid4().hex[:12]}"
            tokens.add(token)
            return self._send(200, {"token": token, "expiresIn": 3600})
        if not self._authed():
            return self._send(401, {"error": "send the token from POST /login as a Bearer token"})
        if path == "/submissions":
            try:
                data = json.loads(self._body() or b"{}")
            except ValueError:
                return self._send(400, {"error": "body must be JSON"})
            sid = f"sub-{uuid.uuid4().hex[:8]}"
            submissions[sid] = {"title": str(data.get("title", "")), "files": [], "first_file_at": None}
            return self._send(201, {"id": sid, "status": "processing"}, {"Location": f"/submissions/{sid}"})
        m = re.fullmatch(r"/submissions/([\w-]+)/submit", path)
        if m and m.group(1) in submissions:
            sub = submissions[m.group(1)]
            status = self._status(sub)
            if status != "done":
                return self._send(409, {"error": f"submission is {status}"})
            return self._send(200, {"receipt": f"rcpt-{uuid.uuid4().hex[:6]}", "files": len(sub["files"])})
        return self._send(404, {"error": "not found"})

    def do_PUT(self):
        if not self._authed():
            return self._send(401, {"error": "unauthorized"})
        m = re.fullmatch(r"/submissions/([\w-]+)/files/([^/]+)", self.path.split("?")[0])
        if not m or m.group(1) not in submissions:
            return self._send(404, {"error": "not found"})
        sub = submissions[m.group(1)]
        size = len(self._body())
        sub["files"].append(m.group(2))
        sub["first_file_at"] = sub["first_file_at"] or time.time()
        return self._send(200, {"name": m.group(2), "size": size})

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/flaky":
            key = dict(p.split("=", 1) for p in query.split("&") if "=" in p).get("key", "")
            flaky_calls[key] = flaky_calls.get(key, 0) + 1
            if flaky_calls[key] <= 2:
                return self._send(503, {"error": "try again", "attempt": flaky_calls[key]}, {"Retry-After": "1"})
            return self._send(200, {"ok": True, "attempts": flaky_calls[key]})
        m = re.fullmatch(r"/submissions/([\w-]+)", path)
        if m:
            if not self._authed():
                return self._send(401, {"error": "unauthorized"})
            sub = submissions.get(m.group(1))
            if not sub:
                return self._send(404, {"error": "not found"})
            return self._send(200, {"id": m.group(1), "status": self._status(sub), "files": sub["files"]})
        return self._send(404, {"error": "not found"})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8090), Handler).serve_forever()
