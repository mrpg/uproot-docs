# The admin interface

The admin interface lets you create and manage sessions, monitor participant progress, and intervene during experiments.

## Accessing the admin

The admin is available at `/admin/` on your server. During development:

```
http://127.0.0.1:8000/admin/
```

### Authentication

On localhost with the default config (`upd.ADMINS["admin"] = ...`), uproot prints an auto-login URL when the server starts:

```
Auto login:
     http://127.0.0.1:8000/admin/login/#aBcDeFgHiJkL...
```

For production, set a password in `main.py`:

```python
upd.ADMINS["admin"] = "your-secure-password"
```

You can define multiple admin accounts:

```python
upd.ADMINS["admin"] = "password1"
upd.ADMINS["researcher"] = "password2"
```

!!! warning
    Auto-login with `...` (Ellipsis) should only be used during local development. Always set a real password for production deployments.

## Dashboard

The dashboard (`/admin/dashboard/`) shows an overview of active sessions and rooms. From here you can navigate to any session or room.

## Creating sessions

Navigate to **Sessions** → **New session** to create a session:

1. **Config** — Select which experiment config to run
2. **Number of players** — How many player slots to create
3. **Settings (JSON)** — Optional JSON object for session settings (accessible via `session.settings`)
4. **Custom session name** — Optional (auto-generated if omitted)
5. **Custom player names** — Optional (auto-generated if omitted)

After creation, each player gets a unique URL:

```
https://your-server.com/p/{session_name}/{player_name}/
```

## Session management

The session detail page (`/admin/session/{sname}/`) is your control center during an experiment.

### Player monitor

The session page shows all players with their current status:

- **Current page** — Which page each player is on
- **Online status** — Whether the player is currently connected
- **Progress** — How far through the experiment each player is

### Player actions

Select one or more players and use these actions:

| Action | What it does |
|--------|-------------|
| **Advance** | Move selected players forward one page |
| **Revert** | Move selected players back one page |
| **Move to end** | Skip selected players to the end of the experiment |
| **Reload** | Force a page reload in selected players' browsers |
| **Send message** | Display a message on selected players' screens |
| **Mark as dropout** | Flag selected players as dropouts |
| **Redirect** | Send selected players to an external URL |
| **Set fields** | Set arbitrary field values on selected players |
| **Group/ungroup** | Manually create or dissolve groups |
| **Run new_player** | Re-run the `new_player` callback for selected players |

### Session controls

| Control | What it does |
|---------|-------------|
| **Toggle active** | Pause/resume the session (inactive sessions reject new page loads) |
| **Toggle testing** | Mark the session as a test run (useful for filtering data later) |
| **Update description** | Add a note about the session |
| **Update settings** | Modify session settings (JSON) |
| **Run new_session** | Re-run the `new_session` callback |

### Data browser

Click **Data** on the session page to browse all stored data in a table view. Each player's fields are shown with their current values, timestamps, and the code location that set each value.

### Page times

Download a CSV of page visit times showing when each player entered and left each page. Useful for measuring response times.

### Digest

If your app defines a `digest(session)` function, the digest view shows its output. Use this for experiment-specific summaries.

:material-github: [See the prisoners_dilemma_repeated example for a digest implementation](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma_repeated)

## Managing rooms

Navigate to **Rooms** to see all rooms. See [Rooms](rooms.md) for details on room configuration.

From a room's admin page you can:

- Open or close the room
- Create a session with pre-assigned player slots
- See which participants are waiting in the room
- Disassociate the room from its current session

## Server status

The status page (`/admin/status/`) shows:

- Database size
- Installed package versions
- Environment variables
- Active authentication sessions

## Database dump

Download a complete database dump from `/admin/dump/`. This is equivalent to running `uproot dump` from the CLI.

## Summary

| Page | URL | Purpose |
|------|-----|---------|
| Dashboard | `/admin/dashboard/` | Overview of sessions and rooms |
| Sessions | `/admin/sessions/` | List all sessions |
| New session | `/admin/sessions/new/` | Create a session |
| Session detail | `/admin/session/{sname}/` | Monitor and control a session |
| Data browser | `/admin/session/{sname}/data/` | Browse session data |
| Rooms | `/admin/rooms/` | List all rooms |
| Status | `/admin/status/` | Server information |
