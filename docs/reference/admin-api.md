# Admin API reference

The Admin REST API provides programmatic access to manage uproot experiments.
All endpoints are located under `/admin/api/v1/` and require Bearer token authentication.

## Authentication

All requests must include an `Authorization` header with a valid API token:

```
Authorization: Bearer YOUR_API_TOKEN
```

To enable API access, add your token(s) in your project's `main.py`:

```python
upd.API_KEYS.add("YOUR_API_TOKEN")
```

## CLI access

The `uproot api` command provides convenient command-line access to the Admin API:

```bash
# Set your API key (or use --auth/-a flag)
export UPROOT_API_KEY="YOUR_API_TOKEN"

# List sessions
uproot api sessions

# Get session details
uproot api session/mysession

# List rooms
uproot api rooms

# Get player data
uproot api session/mysession/players
uproot api session/mysession/players/online

# Create a session
uproot api -X POST sessions -d '{"config": "myconfig", "n_players": 4}'

# Toggle session active status
uproot api -X PATCH session/mysession/active

# Advance players
uproot api -X POST session/mysession/players/advance -d '{"unames": ["ABC"]}'

# Access a remote server via HTTPS
uproot api -u https://example.com/ sessions

# Access a server with a subdirectory
uproot api -u https://example.com/mysubdir/ sessions
```

**Options**:

| Option | Default | Description |
|--------|---------|-------------|
| `--url`, `-u` | `http://127.0.0.1:8000/` | Server base URL |
| `--auth`, `-a` | `$UPROOT_API_KEY` | Bearer token |
| `--method`, `-X` | `GET` | HTTP method |
| `--data`, `-d` | — | JSON request body |

## Sessions

### `GET /admin/api/v1/sessions/`

List all sessions with their metadata.

**Response**: Dictionary mapping session names to session metadata.

---

### `POST /admin/api/v1/sessions/`

Create a new session with the specified configuration and players.

**Request body** (`SessionCreate`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `config` | string | Yes | Configuration name |
| `n_players` | integer | Yes | Number of players to create |
| `sname` | string | No | Custom session name (auto-generated if omitted) |
| `unames` | array[string] | No | Custom usernames for players |
| `settings` | object | No | Session settings |

**Response**: `{"sname": "...", "created": true}`

---

### `GET /admin/api/v1/session/{sname}/`

Get detailed information about a specific session.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Response**: Session details including `sname`, `config`, `active`, `testing`, `description`, `room`, `settings`, `n_players`, `n_groups`, `n_models`, `apps`.

---

### `PATCH /admin/api/v1/session/{sname}/active/`

Toggle the active status of a session.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Response**: `{"active": true/false}`

---

### `PATCH /admin/api/v1/session/{sname}/testing/`

Toggle the testing mode of a session.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Response**: `{"testing": true/false}`

---

### `PATCH /admin/api/v1/session/{sname}/description/`

Update the description of a session.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Request body** (`DescriptionUpdate`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | No | New description (empty string to clear) |

**Response**: `{"description": "..."}`

---

### `PATCH /admin/api/v1/session/{sname}/settings/`

Update the settings of a session.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Request body** (`SettingsUpdate`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `settings` | object | Yes | New settings to apply |

**Response**: `{"settings": {...}}`

---

## Players

### `GET /admin/api/v1/session/{sname}/players/`

Get specified fields for all players in a session.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Query parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fields` | array[string] | `["id", "page_order", "show_page", "started", "label"]` | Fields to retrieve |

**Response**: Dictionary mapping usernames to their field values.

---

### `GET /admin/api/v1/session/{sname}/players/online/`

Get online status and info for all players in a session.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Response**: Online status information for each player.

---

### `PATCH /admin/api/v1/session/{sname}/players/fields/`

Set arbitrary fields on specified players.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Request body** (`PlayersFields`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `unames` | array[string] | Yes | List of usernames |
| `fields` | object | Yes | Fields to set on each player |
| `reload` | boolean | No | Whether to trigger page reload (default: `false`) |

**Response**: `{"updated": [...], "fields": [...]}`

---

### `POST /admin/api/v1/session/{sname}/players/advance/`

Advance specified players by one page.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Request body** (`PlayersAction`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `unames` | array[string] | Yes | List of usernames to advance |

**Response**: Status of the advance operation.

---

### `POST /admin/api/v1/session/{sname}/players/revert/`

Revert specified players by one page.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Request body** (`PlayersAction`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `unames` | array[string] | Yes | List of usernames to revert |

**Response**: Status of the revert operation.

---

### `POST /admin/api/v1/session/{sname}/players/end/`

Move specified players to the end of the experiment.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Request body** (`PlayersAction`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `unames` | array[string] | Yes | List of usernames to move to end |

**Response**: Status of the operation.

---

### `POST /admin/api/v1/session/{sname}/players/reload/`

Force page reload for specified players.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Request body** (`PlayersAction`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `unames` | array[string] | Yes | List of usernames to reload |

**Response**: `{"reloaded": [...]}`

---

### `POST /admin/api/v1/session/{sname}/players/redirect/`

Redirect specified players to an external URL.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Request body** (`PlayerRedirect`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `unames` | array[string] | Yes | List of usernames |
| `url` | string | Yes | URL to redirect to (must start with `http://` or `https://`) |

**Response**: `{"redirected": [...], "url": "..."}`

---

### `POST /admin/api/v1/session/{sname}/players/message/`

Send an admin message to specified players.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Request body** (`PlayerMessage`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `unames` | array[string] | Yes | List of usernames |
| `message` | string | Yes | Message to send |

**Response**: `{"messaged": [...]}`

---

### `POST /admin/api/v1/session/{sname}/players/dropout/`

Mark specified players as manually dropped out.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Request body** (`PlayersAction`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `unames` | array[string] | Yes | List of usernames to mark as dropout |

**Response**: `{"marked_dropout": [...]}`

---

## Data export

### `GET /admin/api/v1/session/{sname}/data/`

Get all session data in display format, optionally filtered by timestamp.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Query parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `since` | number | `0.0` | Only return data updated since this epoch timestamp |

**Response**: `{"data": {...}, "last_update": ...}`

---

### `GET /admin/api/v1/session/{sname}/data/csv/`

Download session data as CSV.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Query parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `"ultralong"` | Export format: `ultralong`, `sparse`, or `latest` |
| `gvar` | array[string] | `[]` | Group-by variables |
| `filters` | boolean | `false` | Apply reasonable filters |

**Response**: CSV file download.

---

### `GET /admin/api/v1/session/{sname}/data/json/`

Download session data as JSON (streaming).

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Query parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `"ultralong"` | Export format: `ultralong`, `sparse`, or `latest` |
| `gvar` | array[string] | `[]` | Group-by variables |
| `filters` | boolean | `false` | Apply reasonable filters |

**Response**: JSON file download.

---

### `GET /admin/api/v1/session/{sname}/page-times/`

Download page visit times as CSV.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Response**: CSV file download with page timing data.

---

## Rooms

### `GET /admin/api/v1/rooms/`

List all rooms with their configuration.

**Response**: Dictionary mapping room names to room configuration.

---

### `POST /admin/api/v1/rooms/`

Create a new room.

**Request body** (`RoomCreate`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Room name |
| `config` | string | No | Default configuration for sessions |
| `labels` | array[string] | No | Allowed labels for participants |
| `capacity` | integer | No | Maximum capacity |
| `open` | boolean | No | Whether the room is open for joining (default: `false`) |
| `sname` | string | No | Associated session name |

**Response**: `{"name": "...", "created": true}`

---

### `GET /admin/api/v1/room/{roomname}/`

Get detailed information about a specific room.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `roomname` | string | Room name |

**Response**: Room details including `name`, `config`, `labels`, `capacity`, `open`, `sname`.

---

### `PATCH /admin/api/v1/room/{roomname}/`

Update room settings. Only works when no session is associated.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `roomname` | string | Room name |

**Request body** (`RoomUpdate`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `config` | string | No | Default configuration |
| `labels` | array[string] | No | Allowed labels |
| `capacity` | integer | No | Maximum capacity |
| `open` | boolean | No | Whether the room is open (default: `false`) |

**Response**: `{"name": "...", "updated": true}`

---

### `DELETE /admin/api/v1/room/{roomname}/`

Delete a room. Only works when no session is associated.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `roomname` | string | Room name |

**Response**: `{"name": "...", "deleted": true}`

---

### `POST /admin/api/v1/room/{roomname}/disassociate/`

Disassociate a room from its current session.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `roomname` | string | Room name |

**Response**: `{"name": "...", "disassociated": true}`

---

### `POST /admin/api/v1/room/{roomname}/session/`

Create a new session within a room.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `roomname` | string | Room name |

**Request body** (`RoomSessionCreate`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `config` | string | Yes | Configuration name |
| `n_players` | integer | Yes | Number of players |
| `assignees` | array[string] | No | Labels to assign to players |
| `settings` | object | No | Session settings |
| `sname` | string | No | Custom session name |
| `unames` | array[string] | No | Custom usernames |
| `no_grow` | boolean | No | Lock capacity to n_players (default: `false`) |

**Response**: `{"sname": "...", "roomname": "...", "created": true}`

---

### `GET /admin/api/v1/room/{roomname}/online/`

Get online status for a room's waiting area.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `roomname` | string | Room name |

**Response**: Online status information.

---

## Configurations

### `GET /admin/api/v1/configs/`

List all available configurations and apps.

**Response**: Dictionary of configuration names and their apps.

---

### `GET /admin/api/v1/configs/{cname}/summary/`

Get a human-readable summary of a configuration.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `cname` | string | Configuration name |

**Response**: `{"name": "...", "summary": "...", "apps": [...], "settings": {...}, "multiple_of": ...}`

---

## System

### `GET /admin/api/v1/announcements/`

Fetch announcements from upstream.

**Response**: Announcements data or `{"error": "Failed to fetch announcements"}`.

---

### `GET /admin/api/v1/session/{sname}/digest/`

Get list of apps that have digest methods available.

**Path parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sname` | string | Session name |

**Response**: `{"apps": [...]}`

---

### `GET /admin/api/v1/auth/sessions/`

Get information about active authentication sessions.

**Response**: Active authentication session data.

---

### `GET /admin/api/v1/status/`

Get server status information.

**Response**: `{"version": "...", "database_size_mb": ..., "public_demo": false}` or `{"public_demo": true}` for demo instances.
