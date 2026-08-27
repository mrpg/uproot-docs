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

1. **Config:** Select which experiment config to run.
2. **Number of players:** How many player slots to create.
3. **Settings (JSON):** Optional JSON object for session settings (accessible via `session.settings`); apps can replace this JSON editor with a [custom settings form](../advanced/settings-forms.md).
4. **Custom session name:** Optional (auto-generated if omitted).
5. **Custom player names:** Optional (auto-generated if omitted).
6. **Simulate responses:** If enabled, the app’s `simulate.js` file runs on every player page load (see [App testing](#app-testing) below).

After creation, each player gets a unique URL:

```
https://your-server.com/p/{session_name}/{player_name}/
```

## Session management

The session detail page (`/admin/session/{sname}/`) is your control center during an experiment.

### Player monitor

The session page shows all players with their current status:

- **current page:** which page each player is on;
- **online status:** whether the player is currently connected;
- **progress:** how far through the experiment each player is.

### Player actions

Select one or more players and use these actions:

| Action | What it does |
|--------|-------------|
| **Advance** | Move selected players forward one page |
| **Revert** | Move selected players back one page |
| **Move to end** | Skip selected players to the end of the experiment |
| **Reload** | Force a page reload in selected players’ browsers |
| **Send message** | Display a message on selected players’ screens |
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

Click **View data** on the session page to browse all stored data in a table view. Each player’s fields are shown with their current values, timestamps, and the code location that set each value.

### Downloading data

Click **Download data** on the session page to download the session’s complete data as a single ZIP archive. See [Exporting data](export.md) for what is inside and how to analyze it.

### Page times

Download a CSV of page visit times showing when each player entered and left each page (available under *Other data* on the **Download data** page). Useful for measuring response times.

### Digest

If your app defines `digest(session)`, the digest view shows its output. A list of rows is a common return value. Pair it with `AdminDigest.html` in the app directory: that file must contain **only** a `main` block (do not extend `Base.html`). Lists and other non-dict values are available as `data`:

```html+jinja
{% block main %}
<p>{{ data | length }} groups so far.</p>
{% endblock main %}
```

If `digest()` returns a dictionary, its keys become template variables instead. For example, `return {"groups": rows}` makes the rows available as `groups`.

[:material-github: See the prisoners_dilemma_repeated example for a digest implementation](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma_repeated)

### Pipeline

If your app defines `pipeline(session)`, the admin can run it from the session page. Return a list of dictionaries to get a downloadable table (one row per dict):

```python
def pipeline(session):
    rows = []
    for group in session.groups(app=__name__):
        p1, p2 = group.players
        p1_data = p1.within(app=__name__)
        p2_data = p2.within(app=__name__)
        rows.append(dict(
            group=group.name,
            p1=p1.name,
            p1_cooperate=p1_data.get("cooperate"),
            p2=p2.name,
            p2_cooperate=p2_data.get("cooperate"),
        ))
    return rows
```

[`player.within()`](../building/results.md#using-playerwithin) selects values recorded in this app. Using `.get()` keeps the pipeline usable before every participant has submitted a decision.

If `pipeline` declares a `data` parameter, the admin (or [REST API](../reference/admin-api.md)) can post JSON that is passed through as `data`. The admin provides a built-in JSON input for this. To show app-specific instructions or status above the pipeline buttons, add `AdminPipeline.html` with a `main` block only.

[:material-github: See pipeline in the prisoners_dilemma example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma) · [prediction_market example](https://github.com/mrpg/uproot-examples/tree/master/prediction_market)

## Managing rooms

Navigate to **Rooms** to see all rooms, separated into open and closed sections. See [Rooms](rooms.md) for details on room configuration.

From a room’s admin page you can:

- see which participants are waiting in the room (with live label tracking);
- create a session with pre-assigned player slots;
- edit room settings (config, labels, capacity) when no session is associated.

When a session is associated, the room’s admin page shows:

- **room status:** open/closed, capacity, and join mode (free join or restricted);
- **close room**/**Reopen room:** stop or resume accepting new participants without affecting the running session (see [Closing and reopening a room](rooms.md#closing-and-reopening-a-room));
- **disassociate:** unlink the session, so the room can be reused.

## Admin chat

The admin chat lets experimenters communicate directly with individual participants during a running session. Open it from the session detail page by clicking the chat icon next to a player.

Features:

- **Per-player channels:** Each participant gets a private conversation with the experimenter.
- **Enable/disable replies:** Control whether the participant can write back or only receive messages.
- **Participant-side widget:** A floating chat button appears on the participant’s screen when the admin sends a message.
- **Real-time updates:** Messages appear instantly on both sides via WebSocket.

Participants see a small button in the bottom-right corner. Messages from the experimenter appear in a pop-up chat window. Whether the participant can reply is controlled by the toggle in the admin view.

!!! note
    Admin chat channels are created automatically the first time the admin sends a message to a participant. No setup is required in your app code.

## App testing

uproot supports automated page interactions via a `simulate.js` file in each app. When a session is created with the **Simulate responses** option enabled, `simulate.js` runs on every player page load.

This lets you verify that your experiment works end-to-end without manually clicking through as a participant.

The fastest way to run a simulated session is from the command line: [`uproot start`](../reference/cli.md#uproot-start) with the `--simulate` flag starts the server with a room whose session has simulation enabled.

```console
uv run uproot start myconfig --simulate
```

Open the printed room link and watch the app play itself.

### Writing simulate.js

When you create a new project with `uproot setup`, a template `simulate.js` is generated automatically. Register a handler with `uproot.simulate.on()` and use the simulation helpers to fill fields and submit:

```javascript
uproot.simulate.on("my_app/Decision", (sim) => {
    sim.choose("choice", sim.random(["A", "B"])).submit();
});
```

The page key passed to `uproot.simulate.on()` is `"app_name/PageClassName"`.

| Helper | What it does |
|--------|----------------|
| `sim.fill(name, value)` or `sim.fill({age: 30, name: "Ada"})` | Set one or several input values |
| `sim.choose(name, value)` | Select a radio button or dropdown option |
| `sim.check(name)` / `sim.uncheck(name)` | Toggle a checkbox |
| `sim.oneOf(name, values)` | Choose a random value from an array |
| `sim.chooseAnyRadio()` | Pick a random radio button on the page |
| `sim.random(array)` | Return a random element |
| `sim.integer(min, max)` | Return a random integer in `[min, max]` |
| `sim.submit()` | Submit the page |
| `sim.value(name)` | Read the current value |
| `sim.element(name)` / `sim.field(name)` | Find a DOM element |

The setters (`fill`, `choose`, `check`, `uncheck`, `select`, `oneOf`, and `chooseAnyRadio`) and `submit` return `sim`, so you can chain them. Lookup helpers such as `value`, `element`, and `field` return the requested value or DOM element instead. Pages with no fields can just call `sim.submit()`.

!!! warning
    Simulation is session-level and permanent. Once a session is created with simulation enabled, it cannot be disabled for that session. Create a new session without the option to run without simulation.

[:material-github: See simulate.js in the prisoners_dilemma example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma)

## Server status

The status page (`/admin/status/`) shows:

- database size;
- installed package versions;
- environment variables;
- active authentication sessions.

## Database dump

Download a complete database dump from `/admin/dump/`. This is equivalent to running `uproot dump` from the CLI.

## Summary

| Page | URL | Purpose |
|------|-----|---------|
| Dashboard | `/admin/dashboard/` | Overview of sessions and rooms |
| Sessions | `/admin/sessions/` | List all sessions |
| New session | `/admin/sessions/new/` | Create a session |
| Session detail | `/admin/session/{sname}/` | Monitor and control a session |
| Admin chat | `/admin/session/{sname}/chat/` | Chat with individual participants |
| Data browser | `/admin/session/{sname}/viewdata/` | Browse session data |
| Data download | `/admin/session/{sname}/data/` | Download session data as a ZIP archive |
| Rooms | `/admin/rooms/` | List all rooms |
| Status | `/admin/status/` | Server information |
