# Mitey — Mock API Samples

A ready-to-open Mitey **workspace** demonstrating every protocol and feature
against the local mock API stack: HTTP basics, auth (API key / Bearer / Basic /
OAuth2), folder inheritance, TLS / mTLS, WebSocket, gRPC, MCP, raw / form /
multipart / binary-file / GraphQL request bodies, and pre/post-request scripting (`mt.*`).

This folder is a self-contained, **relocatable** workspace — clone it anywhere and
open it in Mitey (File → Open Workspace…). It contains no machine-specific paths.

## Prerequisites

The requests target the mock backend (`http://localhost:8080`, `https://localhost:8443`,
etc.). Start it first — see the [`mock/`](../../mock/README.md) stack:

```sh
cd mock && docker compose up -d
```

Then in Mitey: **Open workspace** → select this `mock-workspace` directory, pick the
**Local** environment, and send any request.

**Exception:** `Realtime/MCP` doesn't use the mock stack at all — it spawns the
community [`@modelcontextprotocol/server-everything`](https://github.com/modelcontextprotocol/servers)
locally over the **stdio** transport via `npx` (Node.js required; the first Connect
downloads the package). Hit **Connect**, pick a tool (`echo`, `add`, …), and **Call**.

**Exception:** `GraphQL/*` doesn't use the mock stack either — the mock backend has no
GraphQL service, so these target the free public [Countries GraphQL
API](https://countries.trevorblades.com/) (no auth). Repoint them at any GraphQL endpoint
by editing the **`gqlBaseUrl`** variable in the **Local** environment.

## TLS / mTLS

The **`TLS/`** folder targets the mock stack's mTLS listener (`https://localhost:8443`).

- **Custom CA** — trusts the bundled mock CA, no client identity.
- **mTLS (client cert)** — overrides on the request itself: its own CA + PKCS#12 client
  identity, set on its **Cert** tab.
- **Registered mTLS (host cert)** — sets *nothing*. It works once you register the client
  identity against the host in the **☰ ▸ Certificates…** dialog:

  | field | value |
  |---|---|
  | Host | `localhost:8443` |
  | CA bundle | `<workspace>/.assets/certs/ca.pem` |
  | Client cert | `<workspace>/.assets/certs/client.p12` |
  | PKCS#12 password | `impostor` |

  Certificates are keyed by host, not by folder, so that one entry covers every request
  to `localhost:8443` wherever it lives in the tree. Open the request's **Cert** tab to
  see the read-only **Registered certificate** panel naming the entry it matched.

  The entry is stored on your machine (outside the workspace), which is why it isn't
  shipped with these files — cert paths are machine-specific.

## GraphQL

The **`GraphQL/`** folder uses the **GraphQL** body mode — a query plus a JSON variables
object, sent as an `application/json` POST of `{ "query": …, "variables": … }`.

- **GraphQL query** — a plain query (no variables) listing the world's continents.
- **GraphQL query with variables** — `country(code: $code)`, with the variables pane holding
  `{ "code": "{{countryCode}}" }`. Note the `{{countryCode}}` — variables support the same
  `{{variable}}` substitution as the rest of a request, so the value comes from the **Local**
  environment (`US`); change it there (or override per-environment) to query another country.

## Scripting (pre/post-request `mt.*`)

The **`Scripting/`** folder shows Mitey's scripting. Scripts use the Mitey-native
`mt.*` API; the Postman-style `pm.*` is also available as an alias for compatibility. Open
a request and look at its **Pre-request** / **Post-request** script tabs; the Tests tab shows
`mt.test(...)` results after sending.

- **Pre-request — set variables** — a pre-request script computes a timestamp + nonce and
  `mt.variables.set(...)`s them, so the request templates them in via `{{ts}}` / `{{nonce}}`.
- **Post-request — tests** — `mt.test(...)` + `mt.expect(...)` assertions on status, timing,
  JSON body, and response headers.
- **Chain 1 — capture a value** → **Chain 2 — reuse the captured value** — Chain 1 extracts a
  value from the response and `mt.environment.set("requestId", …)`; Chain 2 reads it back as
  `{{requestId}}` (run them in order). Chain 2's pre-request script fails fast if it's run
  first.

## How file paths stay relocatable

Requests that reference on-disk files (TLS certs, the multipart upload payload) use the
built-in **`{{workspaceDir}}`** variable — the absolute path of the opened workspace —
so they resolve correctly wherever the folder is cloned:

- `TLS/*` → `{{workspaceDir}}/.assets/certs/{ca.pem,client.p12}`
- `HTTP Basics/POST multipart` and `PUT binary` → `{{workspaceDir}}/.assets/sample.txt`

`{{workspaceDir}}` is injected automatically; you don't define it in any environment.

## Bundled demo certs

`.assets/certs/` holds **throwaway** localhost certs used by the TLS examples:
`ca.pem` (the mock CA to trust) and `client.p12` (the mTLS client identity,
password **`impostor`**). They are demo-only — never reuse them.

These certs must match the CA the mock stack serves. That CA is **committed and
stable**: the mock's `certinit` reuses the committed `mock/certs/{ca.pem,server.pem,
server.key}` instead of regenerating, and the `ca.pem`/`client.p12` here are the
matching client side — so the mTLS example works out of the box, no sync needed.

> **Divergence note (standalone repo):** when this bundle lives in its own public
> repo, it carries its own copy of `ca.pem`/`client.p12`, decoupled from the mock
> repo's `mock/certs/`. They stay valid as long as neither side re-rolls the CA. If
> you ever re-roll (`sh certs/gen-certs.sh --force` in the mock repo), the two repos
> diverge — copy the new `ca.pem` + `client.p12` into this bundle's `.assets/certs/`
> and commit. Symptom of a mismatch: the mTLS example fails with a TLS/verify error.
