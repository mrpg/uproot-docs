# Exporting data

uproot stores all experiment data in an [append-only log](../building/data.md). You can export this data in several formats from the admin interface, the REST API, or the CLI.

## Export from the admin interface

Navigate to a session's detail page and click **Data** → **Download**. Choose between CSV and JSONL, and select an export format.

## Export formats

uproot offers three export formats that represent the append-only log at different levels of detail.

### ultralong

One row per field change. Every time a field's value is set, a row is created:

| Column | Description |
|--------|-------------|
| `!storage` | The storage path (e.g., `player/session1/ABC`) |
| `!field` | Field name |
| `!time` | Unix timestamp of the change |
| `!context` | Code location that made the change |
| `!unavailable` | Whether this is a deletion marker |
| `!data` | The value |

This is the most detailed format and preserves the complete history. Use it for temporal analysis or debugging.

### sparse

Like ultralong, but each row has the field name as a separate column header with the value placed in that column. This produces a wide but sparse table where most cells are empty.

### latest

One row per storage, showing only the most recent value for each field. This is the most compact format and what you'll typically want for analysis.

Use the `gvar` parameter to group rows by specific fields (e.g., group by `round` to get one row per player per round).

!!! note
    When using `gvar` with the `WITHIN-ADJACENT` algorithm, every field with a non-unavailable latest value is included in each snapshot—the group-by fields determine *when* snapshots are taken, not which other fields they carry. This means fields set before the group-by field appear in the output as expected.

## Filtering

Enable the `filters` option to apply reasonable filters that clean up internal fields:

- Renames `_uproot_group` to `group`
- Renames `_uproot_session` to `session`
- Keeps `_uproot_dropout` and `_uproot_settings`
- Removes other internal `_uproot_*` fields

## Why JSONL?

uproot exports structured data as [JSONL](https://jsonlines.org/) (JSON Lines): one self-contained JSON object per line, separated by newlines. JSONL has significant advantages over both CSV and monolithic JSON for experiment data:

- **Streaming-friendly.** Each line is independently parseable, so data can be processed as it arrives without buffering the entire file into memory.
- **Type-preserving.** Unlike CSV, JSONL retains the distinction between numbers, strings, booleans, nulls, and nested structures. No more guessing whether `"1"` is a number or a string.
- **No quoting ambiguity.** CSV quoting rules are notoriously inconsistent across tools. JSONL uses standard JSON encoding, eliminating field-delimiter conflicts.
- **Append-only by nature.** Adding new records means appending lines—no need to rewrite the file or close an array bracket. This makes JSONL ideal for append-only logs.
- **Handles heterogeneous rows.** Different rows can have different fields without padding every row with empty columns.

### Reading JSONL in pandas

```python
import pandas as pd

df = pd.read_json("mysession.jsonl", lines=True)
```

The `lines=True` parameter tells pandas to parse one JSON object per line rather than expecting a single JSON array.

### Reading JSONL in R

```r
library(jsonlite)

df <- stream_in(file("mysession.jsonl"))
```

`stream_in()` reads JSONL natively and returns a data frame. For large files, it processes the file in chunks without loading everything into memory at once.

## Page times

Page times track when each player entered and left each page. Export as CSV from the session detail page or via the API:

```bash
uproot api session/mysession/page-times
```

The CSV contains:

| Column | Description |
|--------|-------------|
| `sname` | Session name |
| `uname` | Player name |
| `show_page` | Page index |
| `page_name` | Page class name |
| `entered` | Unix timestamp when the player entered the page |
| `left` | Unix timestamp when the player left the page |
| `context` | Round/context information |

## Database dumps

For a complete backup of all data, use the dump/restore commands:

```bash
# Dump the entire database to a file
uv run uproot dump --file backup.bin

# Restore from a dump
uv run uproot restore --file backup.bin
```

You can also download a dump from the admin interface at `/admin/dump/`.

!!! note
    Database dumps contain all sessions and all data. Use the CSV/JSONL export endpoints for per-session exports.

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

### Database API

| Method/Property | Description |
|-----------------|-------------|
| `db.sessions` | All sessions in the database |
| `db.session(sname)` | Get a session by name |
| `db.group(sname, gname)` | Get a group by session and group name |
| `db.player(sname, uname)` | Get a player by session and username |
| `db.close()` | Close the database |

!!! note
    `uproot.read` gives you the same Storage objects used at runtime—you can access `player.group`, `player.session`, `group.players`, and all virtual fields. Remember to use `with player:` (or `with session:`, etc.) before reading attributes.

## Live data browser

The admin data browser (`/admin/session/{sname}/data/`) shows session data in real-time in your browser. It updates automatically as new data comes in, making it useful for monitoring experiments in progress.

The data display page (`/admin/session/{sname}/viewdata/`) shows a table view of all player data with timestamps and code locations.

## Export via the REST API

Use the [Admin REST API](../reference/admin-api.md) for programmatic access:

```bash
# Download CSV (ultralong format)
uproot api session/mysession/data/csv

# Download CSV (latest format, with filters)
uproot api "session/mysession/data/csv?format=latest&filters=true"

# Download JSONL
uproot api session/mysession/data/jsonl

# Download page times
uproot api session/mysession/page-times
```

Or with curl:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://your-server.com/admin/api/v1/session/mysession/data/csv/?format=latest&filters=true"
```

### API query parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `format` | `ultralong`, `sparse`, `latest` | `ultralong` | Export format |
| `gvar` | field names | — | Group-by variables (for `latest` format) |
| `filters` | `true`, `false` | `false` | Apply reasonable filters |

## Summary

| Method | Use case |
|--------|----------|
| Admin data browser | Real-time monitoring during experiments |
| CSV/JSONL download | Per-session data for analysis |
| Page times CSV | Response time analysis |
| `uproot.read` | Offline analysis in Python/Jupyter |
| `uproot dump` | Full database backup |
| REST API | Programmatic access and automation |
