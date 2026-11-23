# Mitey mock API stack

A one-command mock backend that exercises **every** Mitey feature: REST, the auth
schemes, OAuth2, mTLS, WebSocket, and gRPC. Built from proven upstream images plus a
small nginx for the mTLS endpoint. For local testing & demos only.

## Quick start

```sh
cd mock
docker compose up -d        # or: docker-compose up -d
docker compose ps           # all services healthy?
# …demo in Mitey…
docker compose down         # stop
```

The TLS endpoints use a **committed** throwaway demo CA: the canonical server set
(`certs/{ca.pem,server.pem,server.key}`) is tracked in git so the mock and the
[example workspace](../mock-workspace/) always share one stable CA. The
`certinit` container therefore just reuses the committed certs (it no longer
regenerates them on a fresh clone). `client.p12` password is **`impostor`**.

To deliberately re-roll the demo CA, run `sh certs/gen-certs.sh --force`, then
re-commit the server set and copy the new `ca.pem`/`client.p12` into the example
bundle's `.assets/certs/` (the script prints this reminder).

## Services & ports

| URL | Service | What it's for |
|-----|---------|---------------|
| `http://localhost:8080` | go-httpbin | REST, auth (Basic/Bearer), WebSocket, SSE |
| `http://localhost:8081` | mock-oauth2-server | OAuth2 / OIDC flows |
| `http://localhost:8090` | jobs (`jobs/server.py`) | Workflows: a stateful job API to chain, poll and retry |
| `localhost:9000` / `localhost:9001` | grpcbin | gRPC (plaintext / TLS), with reflection |
| `https://localhost:8443` | nginx (mTLS) | client-cert-required TLS → httpbin |
| `https://localhost:8444` | nginx (TLS only) | plain TLS w/ custom CA → httpbin |

## Endpoint → Mitey feature map

### HTTP basics
| Try in Mitey | Endpoint |
|---------------|----------|
| Methods / echo | `GET http://localhost:8080/get`, `POST …/post` (raw / form / multipart), `PUT …/put` (binary file body) |
| Status codes | `GET http://localhost:8080/status/418` |
| Headers & query | `GET http://localhost:8080/headers`, `…/anything?foo=bar` |
| Compression | `GET http://localhost:8080/gzip` · `/brotli` · `/deflate` |
| Redirects | `GET http://localhost:8080/redirect/3` |
| Latency / size | `GET http://localhost:8080/delay/2` · `/bytes/100000` |
| Cookies | `GET http://localhost:8080/cookies/set?session=abc` |

### Workflows (`http://localhost:8090`)
A small in-memory job API (`jobs/server.py`, Python stdlib) for chaining requests:

| Endpoint | Behaviour |
|----------|-----------|
| `POST /login` | `{"token": …}` — send it as a Bearer token to everything below |
| `POST /submissions` | `201 {"id": "sub-…", "status": "processing"}` (title `fail` makes it fail) |
| `PUT /submissions/{id}/files/{name}` | stores a file name |
| `GET /submissions/{id}` | `status` turns `done` 4 s after the first upload (`PROCESSING_SECONDS`) — poll it |
| `POST /submissions/{id}/submit` | `{"receipt": …}`, or `409` until the submission is done |
| `GET /flaky?key=…` | `503` with `Retry-After: 1` twice per key, then `200` — retry it |

The example workspace's **Submission lifecycle** workflow runs the whole chain.

### WebSocket
Open the **WS** panel → `ws://localhost:8080/websocket/echo` → send a message, see it echoed.

### Auth
| Scheme | How |
|--------|-----|
| Basic | `GET http://localhost:8080/basic-auth/user/passwd` with Basic `user` / `passwd` |
| Bearer | `GET http://localhost:8080/bearer` with any Bearer token |
| API key | `GET http://localhost:8080/anything` with the key in a header or query param (echoed back so you can confirm placement) |

### OAuth2 (Auth tab → OAuth 2.0)
- **Client credentials:** Token URL `http://localhost:8081/default/token`, any client id/secret,
  optional scope. Get Token → use it against `http://localhost:8080/bearer`.
- **Authorization code + PKCE:** Auth URL `http://localhost:8081/default/authorize`,
  Token URL `http://localhost:8081/default/token`, any client id, PKCE on. The mock
  auto-issues the code to Mitey's loopback redirect. (Debugger UI:
  `http://localhost:8081/default/debugger`.)

### mTLS (Cert/TLS tab)
- URL: `GET https://localhost:8443/anything`
- CA bundle: `mock-server/certs/ca.pem`
- Client cert: `mock-server/certs/client.p12` (password `impostor`) — or `client.pem` + `client.key`
- Expect **200** with the cert; **without** the client cert the handshake is rejected.
- `https://localhost:8444/anything` tests a custom CA on its own (no client cert needed).

### gRPC (gRPC panel)
- Target `localhost:9000` → service `grpcbin.GRPCBin`.
- Methods: `DummyUnary` (unary), `DummyServerStream` (server-stream),
  `DummyClientStream` (client-stream), `DummyBidirectionalStreamEcho` (bidi).
- `localhost:9001` is the same over TLS (set CA / insecure as needed).

> **Reflection note:** grpcbin exposes only the **v1alpha** reflection service
> (`grpc.reflection.v1alpha.ServerReflection`). Mitey's gRPC client tries reflection
> **v1** first and **falls back to v1alpha** (`src-tauri/src/grpc.rs`), so **Reflect works
> against grpcbin**. (You can still use **Load .proto** with grpcbin's
> [`grpcbin.proto`](https://github.com/moul/grpcbin/blob/master/grpcbin.proto) if you prefer.)

## Notes
- Image tags are pinned for reproducibility — bump them in `docker-compose.yml` as needed.
- Everything is throwaway: `docker compose down -v` removes containers and the cert volume.
- No secrets or real data here; safe to run anywhere.
