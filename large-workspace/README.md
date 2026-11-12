# Mitey — Large Workspace (1000 requests)

A ready-to-open Mitey **workspace** holding **1000 HTTP requests** across **49 folders**,
targeting [typicode's **JSONPlaceholder**](https://jsonplaceholder.typicode.com) — a free,
public fake REST API. Nothing to install, nothing to start: pick the **JSONPlaceholder**
environment and send.

Two things it is good for:

- **A realistic big workspace.** Sidebar navigation, search, filtering, and the tree scan
  all behave differently at 1000 requests than at 20. This is the fixture for checking
  that they still feel fast.
- **A grab-bag of HTTP.** Every verb, three body kinds, query filters, pagination,
  folder-inherited headers and variables, dynamic variables, and post-request tests.

This folder is self-contained and **relocatable** — clone it anywhere and open it
(File → Open Workspace…). It contains no machine-specific paths and no secrets.

## Method mix

80% POST by design, with the remaining fifth spread over the other verbs:

| Method | Count | Share |
|---------|------:|------:|
| POST    |   800 | 80.0% |
| GET     |    80 |  8.0% |
| PUT     |    45 |  4.5% |
| PATCH   |    35 |  3.5% |
| DELETE  |    30 |  3.0% |
| HEAD    |     5 |  0.5% |
| OPTIONS |     5 |  0.5% |
| **Total** | **1000** | |

## Environments

| Environment | `baseUrl` | Notes |
|-------------|-----------|-------|
| **JSONPlaceholder** | `https://jsonplaceholder.typicode.com` | The hosted public API. No setup. |
| **Local json-server** | `http://localhost:3000` | The same routes served locally — see below. |

Both also define `userId`, `postId`, `commentId`, `albumId`, `photoId`, and `todoId`, which
roughly a quarter of the id-bearing requests template into their path instead of a literal
id — so you can retarget a whole class of requests by editing one variable.

### Running it against a local `json-server`

JSONPlaceholder is rate-limited and shared. For heavy or offline use, serve the same
routes yourself with [`json-server`](https://github.com/typicode/json-server) and switch to
the **Local json-server** environment:

```sh
npx json-server db.json          # serves the same /posts, /comments, … routes on :3000
```

Unlike the hosted API, a local `json-server` actually **persists** writes — so the 800
POSTs will really create records. Point it at a throwaway `db.json`.

> **Note:** JSONPlaceholder fakes its writes. A POST returns `201` with an echoed body and
> a new `id`, but nothing is stored, so a following `GET /posts/101` returns `404`. That is
> upstream behaviour, not a workspace bug.

## Layout

```
large-workspace/
├── mitey.workspace.yaml      # workspace name + global variables
├── settings.yaml                # workspace-level header (X-Mitey-Workspace)
├── .env/
│   ├── JSONPlaceholder.env.yaml
│   └── Local json-server.env.yaml
├── Posts/        settings.yaml + Create/ Read/ Update/ Delete/
├── Comments/     …
├── Albums/       …
├── Photos/       …
├── Todos/        …
├── Users/        …
└── Diagnostics/  HEAD + OPTIONS against each collection
```

Every resource folder follows the same shape:

- **`Create/`** — the POSTs, chunked into `Batch 01`, `Batch 02`, … of 50 so no single
  folder holds 200 rows.
- **`Read/`** — GETs cycling through seven shapes: list all, by id, `_page`/`_limit`
  pagination, `_sort`/`_order`, a field filter (`?userId=…`), a nested collection
  (`/users/9/posts`), and a short `_limit=5` list.
- **`Update/`** — PUT (full replacement) and PATCH (one or two fields).
- **`Delete/`** — DELETE by id.

Each resource folder carries a `settings.yaml` with a folder-scoped `resource` variable and
an `X-Resource` header, both inherited by every request beneath it — so the tree also
exercises folder inheritance at depth.

## What the requests exercise

- **Three body kinds.** The POSTs split roughly 85% raw JSON / 10%
  `application/x-www-form-urlencoded` / 5% `multipart/form-data` (text fields only — no
  on-disk assets, which is what keeps the workspace relocatable). PUT and PATCH bodies are
  always raw JSON.
- **Dynamic variables.** ~30% of requests send `X-Trace-Id: {{$guid}}`, resolved fresh per
  send.
- **Post-request tests.** ~12% of requests assert their status code with `mt.test` /
  `mt.expect`, so a folder run produces a meaningful pass/fail column.
- **Inherited headers and variables** from the workspace root and each resource folder.

## Driving it headlessly

The `mitey` binary is also a CLI, which makes this workspace a convenient load
generator (macOS path shown; on Windows use `mitey.exe`):

```sh
mitey ls  --workspace ./large-workspace                      # 1000 requests
mitey run "Create post 001" --workspace ./large-workspace --env JSONPlaceholder
mitey run "Read posts 001 — list all" --workspace ./large-workspace --json
```

Scripts don't run headless, so the `mt.test` assertions above are a GUI-only affordance.

## Regenerating

This workspace is generated, not hand-written. The generator lives in the main Mitey
repo at `scripts/gen-large-workspace.mjs` and is deterministic — a re-run with an
unchanged script reproduces the tree byte for byte:

```sh
node scripts/gen-large-workspace.mjs --out ../mitey-support/large-workspace
```

Edit the generator rather than the 1000 files. This `README.md` is hand-written and is
preserved across regeneration.
