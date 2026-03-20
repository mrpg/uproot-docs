# Exporting data

uproot stores all experiment data in an [append-only log](../building/data.md). You can export this data in several formats from the admin interface, the REST API, or the CLI.

## Export from the admin interface

Navigate to a session's detail page and click **Data** → **Download**. Choose between CSV and JSON, and select an export format.

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

## Filtering

Enable the `filters` option to apply reasonable filters that clean up internal fields:

- Renames `_uproot_group` to `group`
- Renames `_uproot_session` to `session`
- Keeps `_uproot_dropout` and `_uproot_settings`
- Removes other internal `_uproot_*` fields

## Export via the REST API

Use the [Admin REST API](../reference/admin-api.md) for programmatic access:

```bash
# Download CSV (ultralong format)
uproot api session/mysession/data/csv

# Download CSV (latest format, with filters)
uproot api "session/mysession/data/csv?format=latest&filters=true"

# Download JSON
uproot api session/mysession/data/json

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
    Database dumps contain all sessions and all data. Use the CSV/JSON export endpoints for per-session exports.

## Live data browser

The admin data browser (`/admin/session/{sname}/data/`) shows session data in real-time in your browser. It updates automatically as new data comes in, making it useful for monitoring experiments in progress.

The data display page (`/admin/session/{sname}/viewdata/`) shows a table view of all player data with timestamps and code locations.

## Summary

| Method | Use case |
|--------|----------|
| Admin data browser | Real-time monitoring during experiments |
| CSV/JSON download | Per-session data for analysis |
| Page times CSV | Response time analysis |
| `uproot dump` | Full database backup |
| REST API | Programmatic access and automation |
