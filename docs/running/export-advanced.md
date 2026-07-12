# Advanced data access

This page covers programmatic and low-level ways to get at your data: automated exports via the REST API, streaming JSONL, full database backups, and offline analysis with `uproot.read`. If you just want to download and analyze your data, start with [Exporting data](export.md).

## Export via the REST API

Use the [Admin REST API](../reference/admin-api.md) for programmatic access. All endpoints require Bearer token authentication.

### Downloading the briefcase

`GET /admin/api/v1/sessions/{sname}/data/export/` returns the same ZIP briefcase as the admin interface's **Download data** page:

```bash
curl -OJ -H "Authorization: Bearer YOUR_TOKEN" \
  "https://your-server.com/admin/api/v1/sessions/mysession/data/export/"
```

(`-OJ` saves the file under the name suggested by the server, e.g. `mysession_2026-07-04_1412.zip`.)

Query parameters:

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `filetype` | `csv`, `jsonl` | `csv` | File type used inside the briefcase |
| `gvar` | field names (repeatable) | — | Adds a grouped latest format (e.g., `latest_by_round/`) |
| `filters` | `true`, `false` | `true` | Apply reasonable filters |

For example, a JSONL briefcase with an extra format grouped by app and round:

```bash
curl -OJ -H "Authorization: Bearer YOUR_TOKEN" \
  "https://your-server.com/admin/api/v1/sessions/mysession/data/export/?filetype=jsonl&gvar=app&gvar=round"
```

!!! note
    The `uproot api` CLI command prints responses as text, so it is not suited to binary downloads like the briefcase — use `curl` (or any HTTP client) for this endpoint.

### Streaming JSONL

`GET /admin/api/v1/sessions/{sname}/data/jsonl/` streams a single format as JSONL — no ZIP, no splitting by storage kind. This is useful for piping data directly into other tools, or when sessions are large:

```bash
# Raw event log (default)
uproot api sessions/mysession/data/jsonl > mysession.jsonl

# Latest state, with filters
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://your-server.com/admin/api/v1/sessions/mysession/data/jsonl/?format=latest&filters=true"
```

Query parameters:

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `format` | `ultralong`, `sparse`, `latest` | `ultralong` | Export format |
| `gvar` | field names (repeatable) | — | Group-by variables (for `latest`) |
| `filters` | `true`, `false` | `false` | Apply reasonable filters |

## Database dumps

For a complete backup of all data, use the dump/restore commands:

```bash
# Dump the entire database to a file
uproot dump --file backup.bin

# Restore from a dump
uproot restore --file backup.bin
```

You can also download a dump from the admin interface at `/admin/dump/`.

!!! note
    Database dumps contain all sessions and all data. Use the briefcase or JSONL endpoints for per-session exports.

## Offline analysis with uproot.read

For analysis in Python (e.g., in a Jupyter notebook), you can open an `uproot.sqlite3` database file directly and navigate it using the same Storage objects the server uses:

```python
from uproot.read import read

db = read("uproot.sqlite3")

for session in db.sessions:
    for group in session.groups:
        for player in group.players:
            with player:
                print(player.name, player.label, player.payoff)

db.close()
```

The `Database` object supports context managers:

```python
with read("uproot.sqlite3") as db:
    session = db.session("my_session")
    with session:
        for player in session.players:
            with player:
                print(player.choice)
```

### Plain-row helpers

For analysis scripts that need regular dictionaries rather than live Storage objects, use the plain-row methods. Each returns a list of dictionaries with identifier columns plus any extra fields you request. Missing fields become `None`.

```python
with read("uproot.sqlite3") as db:
    players = db.player_rows(["label", "role", "payoff"])
    memberships = db.membership_rows()
```

| Method | Identifier columns | Extra fields |
|--------|--------------------|--------------|
| `db.session_rows(fields)` | `session` | Yes |
| `db.group_rows(fields)` | `session`, `group` | Yes |
| `db.player_rows(fields)` | `session`, `uname` | Yes |
| `db.membership_rows()` | `session`, `group`, `uname`, `position` | No |

To grab all four tables at once, use `snapshot`:

```python
with read("uproot.sqlite3") as db:
    snap = db.snapshot(
        session_fields=["sid"],
        group_fields=["round"],
        player_fields=["label", "role", "payoff"],
    )

print(snap.sessions)      # list of dicts
print(snap.groups)
print(snap.players)
print(snap.memberships)
print(snap.as_dict())      # single dict with all four tables
```

### Database API

| Method/Property | Description |
|-----------------|-------------|
| `db.sessions` | All sessions in the database |
| `db.session(sname)` | Get a session by name |
| `db.group(sname, gname)` | Get a group by session and group name |
| `db.player(sname, uname)` | Get a player by session and username |
| `db.session_rows(fields)` | Plain dictionaries, one per session |
| `db.group_rows(fields)` | Plain dictionaries, one per group |
| `db.player_rows(fields)` | Plain dictionaries, one per player |
| `db.membership_rows()` | Plain dictionaries, one per group membership |
| `db.snapshot(...)` | All four plain-row tables as a `Snapshot` |
| `db.close()` | Close the database |

!!! note
    `uproot.read` gives you the same Storage objects used at runtime—you can access `player.group`, `player.session`, `group.players`, and all virtual fields. Remember to use `with player:` (or `with session:`, etc.) before reading attributes. The plain-row helpers handle context management internally.

## Summary

| Method | Use case |
|--------|----------|
| [ZIP briefcase](export.md) | Per-session data for analysis (admin UI or API) |
| Streaming JSONL endpoint | Piping one format into other tools |
| `uproot.read` | Offline analysis in Python/Jupyter |
| `uproot dump` | Full database backup |
