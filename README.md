# Mitey — Support, Samples and Examples

The support home for [**Mitey**](https://mitey.app/), a fast, local, cross-platform
API client (a lightweight, native alternative to Postman built on Tauri v2 + SvelteKit,
not Electron). It hosts the ready-to-open example workspaces below, and its
[**issue tracker**](https://github.com/TheImpostorApp/support/issues) is where to report
bugs or ask for help.

Clone this repo, open a workspace folder in Mitey (**File → Open Workspace…**), and start
sending requests. There are two:
[`mock-workspace/`](mock-workspace/) for a tour of every feature (it needs the Docker mock
backend bundled here in [`mock-server/`](mock-server/), so this repo is fully
self-contained), and [`large-workspace/`](large-workspace/) for 1000 requests against a
public API with no setup at all. There are also
[`import-samples/`](import-samples/) — collections in other tools' formats, for trying
out Mitey's importer.

## `mock-workspace/`

A self-contained, **relocatable** workspace that demonstrates every protocol and feature
Mitey supports, all targeting the local mock API stack:

- **HTTP Basics** — GET/POST/PUT, JSON / form / multipart / binary-file bodies, query +
  headers, cookies, gzip, redirects, delays, and non-2xx statuses.
- **Auth** — API key (header & query), Bearer, Basic, Digest, AWS SigV4, and OAuth2
  client credentials.
- **GraphQL** — GraphQL query bodies (with and without variables); targets the free
  public Countries GraphQL API, so it needs no mock stack.
- **Inheritance Demo** — folder-level auth/headers/settings inherited (and overridden)
  by child requests.
- **TLS** — TLS and mutual-TLS (mTLS) using the bundled demo certs.
- **Realtime** — WebSocket, Server-Sent Events (SSE), gRPC, and MCP (spawns the
  community `server-everything` over stdio via `npx` — the one example that needs no
  mock stack, just Node.js).
- **Scripting** — pre/post-request scripts via Mitey's native `mt.*` API (with
  `pm.*` available as a Postman-compatible alias): setting variables, assertions
  (`mt.test` / `mt.expect`), and capturing a value in one request to reuse in another.

The folder contains no machine-specific paths — clone it anywhere and it just works.

### Prerequisites

The requests target the Mitey mock backend (`http://localhost:8080`,
`https://localhost:8443`, etc.), bundled in [`mock-server/`](mock-server/). Start it
before sending requests:

```sh
cd mock-server && docker compose up -d   # or: docker-compose up -d
docker compose ps                        # all services healthy?
```

Stop it with `docker compose down` (add `-v` to also drop the cert volume). See
[`mock-server/README.md`](mock-server/README.md) for the full endpoint → feature map.

### Usage

1. In Mitey, **Open workspace** → select the `mock-workspace/` directory.
2. Pick the **Local** environment.
3. Send any request.

### Drive it from the command line or an AI

The same `mitey` binary is also a headless CLI, so you can drive this workspace
without the window (macOS path shown; on Windows use `mitey.exe`):

```sh
# List the requests, then resolve-and-send one (variables + folder inheritance applied):
mitey ls  --workspace ./mock-workspace
mitey run "GET / echo" --workspace ./mock-workspace --env Local
mitey run "GET / echo" --workspace ./mock-workspace --json   # machine-readable
```

`mitey run` exits `0` on a 2xx response, non-zero otherwise, so it drops straight
into scripts and CI. See the [CLI docs](https://docs.mitey.app/cli).

**Drive it from an AI.** Mitey is also an MCP **server** — a local AI agent (Claude
Desktop/Code, Cursor, Copilot) can list, inspect, and run these requests. In Mitey,
click **Connect MCP** in the status bar for a ready-to-paste config, or point your host at:

```json
{ "mcpServers": { "mitey": {
  "command": "/Applications/Mitey.app/Contents/MacOS/mitey",
  "args": ["mcp", "--workspace", "<path-to>/mock-workspace"]
}}}
```

For Claude Code, the equivalent one-liner is:

```sh
claude mcp add mitey --scope user -- \
  /Applications/Mitey.app/Contents/MacOS/mitey mcp --workspace <path-to>/mock-workspace
```

Keep `--scope user` — without it the server is registered for the current directory only,
and `/mcp` will come up empty everywhere else.

Secrets are redacted and scripts don't run over MCP; authoring is opt-in
(`--allow-write`). See the [MCP server docs](https://docs.mitey.app/mcp-server).

### How paths stay relocatable

Requests that reference on-disk files (TLS certs, the multipart upload payload) use the
built-in **`{{workspaceDir}}`** variable — the absolute path of the opened workspace — so
they resolve wherever the folder is cloned:

- `TLS/*` → `{{workspaceDir}}/.assets/certs/{ca.pem,client.p12}`
- `HTTP Basics → POST multipart` and `PUT binary` → `{{workspaceDir}}/.assets/sample.txt`

`{{workspaceDir}}` is injected automatically; you never define it in an environment.

### Bundled demo certs

`.assets/certs/` holds **throwaway** localhost certs for the TLS examples: `ca.pem` (the
mock CA to trust) and `client.p12` (the mTLS client identity, password **`impostor`**).
They are demo-only — never reuse them. These are the client side of the same committed
CA the bundled [`mock-server/`](mock-server/) stack serves, so the mTLS example works out
of the box. If the CA is ever re-rolled (`sh mock-server/certs/gen-certs.sh --force`),
copy the new `ca.pem`
+ `client.p12` into `.assets/certs/`; a mismatch shows up as a TLS/verify error on the
mTLS example.

## `large-workspace/`

A **1000-request** workspace across **49 folders**, targeting
[typicode's **JSONPlaceholder**](https://jsonplaceholder.typicode.com) — a free public fake
REST API, so this one needs **no mock stack and no setup at all**. Open it, pick the
**JSONPlaceholder** environment, and send.

Where `mock-workspace/` is about *breadth* (every protocol and feature), this one is about
*scale*: it's the fixture for seeing how the sidebar, search, and workspace scan behave at
a realistic size. The method mix is deliberately POST-heavy:

| POST | GET | PUT | PATCH | DELETE | HEAD | OPTIONS |
|-----:|----:|----:|------:|-------:|-----:|--------:|
| 800 (80%) | 80 | 45 | 35 | 30 | 5 | 5 |

Organised as `Posts/`, `Comments/`, `Albums/`, `Photos/`, `Todos/`, `Users/` — each with
`Create/` (batched 50 per folder), `Read/`, `Update/`, `Delete/` — plus a `Diagnostics/`
folder for the HEAD/OPTIONS probes. Along the way it exercises raw JSON / urlencoded /
multipart bodies, query filters and pagination, folder-inherited headers and variables,
`{{$guid}}` dynamic variables, and `mt.test` post-request assertions.

A second **Local json-server** environment repoints everything at `http://localhost:3000`
for offline or heavy use (`npx json-server db.json`) — unlike the hosted API, that one
really persists the 800 creates.

The workspace is **generated**, not hand-written; see
[`large-workspace/README.md`](large-workspace/README.md) for the layout, the environments,
and how to regenerate it.

## `mock-server/` — the mock API stack

A one-command Docker backend (`docker compose up -d`) that exercises every Mitey
feature the workspace touches: REST, the auth schemes, OAuth2/OIDC, mTLS, WebSocket, SSE,
and gRPC. Built from pinned upstream images plus a small nginx for the mTLS endpoint.

| URL | Service | What it's for |
|-----|---------|---------------|
| `http://localhost:8080` | go-httpbin | REST, auth (Basic/Bearer), WebSocket, SSE |
| `http://localhost:8081` | mock-oauth2-server | OAuth2 / OIDC flows |
| `localhost:9000` / `9001` | grpcbin | gRPC (plaintext / TLS), with reflection |
| `https://localhost:8443` | nginx (mTLS) | client-cert-required TLS → httpbin |
| `https://localhost:8444` | nginx (TLS only) | plain TLS w/ custom CA → httpbin |

Everything is throwaway and safe to run anywhere — no secrets or real data. See
[`mock-server/README.md`](mock-server/README.md) for the complete endpoint → feature map.

## `import-samples/` — try the importer

Sample collections in the formats Mitey imports, so you can exercise the
**Import** flow without exporting from another tool first.

| Sample | Format |
|--------|--------|
| [`import-samples/postman/`](import-samples/postman/) | **Postman v2.1** — a collection and two environments, the same files Postman's *Export* produces. |
| [`import-samples/opencollection/`](import-samples/opencollection/) | [**OpenCollection**](https://spec.opencollection.com) — the open YAML format Bruno 3.x writes natively. Covers all four shapes Mitey accepts: an on-disk collection tree, a bundled single file, a lone request file, and a standalone environment file. |

The requests target the same [`mock-server/`](mock-server/) stack as `mock-workspace/`,
so an imported collection is immediately runnable. Each sample's README lists what it
covers and the counts and warnings a correct import reports. See the
[Importing docs](https://docs.mitey.app/import) for the full mapping.

## Repo layout

```
mock-server/                  # bundled Docker mock backend (docker compose up -d)
mock-workspace/               # feature-tour workspace — open this in the app
├── mitey.workspace.yaml   # workspace name + global variables
├── settings.yaml             # workspace-level headers/settings
├── .env/Local.env.yaml       # the "Local" environment (baseUrl, etc.)
├── .assets/                  # certs + sample upload payload
├── HTTP Basics/              # *.request.yaml files, one per request
├── Auth/
├── GraphQL/
├── Inheritance Demo/
├── TLS/
├── Realtime/
└── Scripting/
large-workspace/              # 1000-request workspace (JSONPlaceholder, no setup)
├── mitey.workspace.yaml
├── settings.yaml
├── .env/                     # JSONPlaceholder + Local json-server
├── Posts/  Comments/  Albums/  Photos/  Todos/  Users/
│   └── Create/ (Batch 01…) · Read/ · Update/ · Delete/
└── Diagnostics/
import-samples/               # sample collections for the importer — not workspaces
├── postman/                  # Postman v2.1 collection + two environments
└── opencollection/           # OpenCollection (Bruno) YAML
    ├── mock-api/             # on-disk tree: opencollection.yml + one .yml per request
    ├── mock-api-bundled.yml  # the same collection as one bundled file
    └── staging.env.yml       # a standalone environment file
```

Each `*.request.yaml` is a single request (method, URL, headers, body, auth, scripts).
Folders can carry their own `settings.yaml` for inherited auth/headers.
