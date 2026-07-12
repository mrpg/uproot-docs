# CLI commands

uproot provides a command-line interface for managing projects and running experiments. Commands are split into two categories: **global commands** that work anywhere, and **project commands** that must be run inside a project directory.

## Global commands

### uproot setup

Create a new uproot project.

```bash
uproot setup my_project
```

| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing files |
| `--minimal` | Create a minimal project without the example app |
| `--no-example` | Skip the example app |

### uproot api

Access the [Admin REST API](admin-api.md) from the command line.

```bash
# List sessions
uproot api sessions

# Get session details
uproot api sessions/mysession

# Create a session
uproot api -X POST sessions -d '{"config": "myconfig", "n_players": 4}'

# Access a remote server
uproot api -u https://example.com/ sessions
```

| Option | Default | Description |
|--------|---------|-------------|
| `--url`, `-u` | `http://127.0.0.1:8000/` | Server base URL |
| `--auth`, `-a` | `$UPROOT_API_KEY` | Bearer token |
| `--method`, `-X` | `GET` | HTTP method |
| `--data`, `-d` | — | JSON request body |

### uproot --version

Show the installed uproot version.

### uproot --copyright

Show copyright information.

## Project commands

These commands must be run from inside an uproot project directory (where `main.py` is located).

### uproot run

Start the development server.

```bash
uproot run
```

| Option | Default | Description |
|--------|---------|-------------|
| `-h`, `--host` | `127.0.0.1` | Host to bind to |
| `-p`, `--port` | `8000` | Port to listen on |
| `--unsafe` | — | Disable HTTPS requirement (for development behind certain proxies) |
| `--public-demo` | — | Run in public demo mode (restricted admin) |

### uproot start

Start the development server with a participant link ready to go. This is the fastest way to try an experiment: instead of creating a session in the admin by hand, uproot creates an open [room](../running/rooms.md) for your config and prints its URL when the server starts.

```bash
uproot start myconfig
```

```
Room:
     http://127.0.0.1:8000/room/quick1/
```

Open the room URL in one browser tab per participant — each tab joins the session as a new player. If your project has exactly one config, you can omit the config name and just run `uproot start`.

The rooms created this way are ordinary rooms named `quick1`, `quick2`, and so on; each `uproot start` creates a new one, and they appear under **Rooms** in the admin like any other.

It accepts the same `--host`, `--port`, `--unsafe`, and `--public-demo`
options as `uproot run`, plus:

| Option | Description |
|--------|-------------|
| `CONFIG` or `--config` | Config to use (optional if the project has exactly one config) |
| `--simulate` | Enable the app's `simulate.js` responses for the quick room's session (see [App testing](../running/admin.md#app-testing)) |

### uproot reset

Reset the database, deleting all sessions and data.

```bash
uproot reset
```

| Option | Description |
|--------|-------------|
| `--yes` | Skip the confirmation prompt |

!!! warning
    This permanently deletes all experiment data. Use `uproot dump` first if you need a backup.

### uproot dump

Dump the entire database to a file.

```bash
uproot dump --file backup.bin
```

| Option | Description |
|--------|-------------|
| `--file` | Path to the output file (required) |

### uproot restore

Restore a database from a dump file.

```bash
uproot restore --file backup.bin
```

| Option | Description |
|--------|-------------|
| `--file` | Path to the dump file (required) |
| `--yes` | Skip the confirmation prompt |

### uproot new

Create a new app in the current project.

```bash
uproot new my_app
```

| Option | Description |
|--------|-------------|
| `--minimal` | Create a minimal app without example code |

This creates a new directory with `__init__.py` and starter template files. You still need to register the app in `main.py` using `load_config`.

### uproot newpage

Create a new page in an existing app.

```bash
uproot newpage my_app MyNewPage
```

This creates a new HTML template file for the page and adds the page class to the app's `__init__.py`.

### uproot examples

Download the example experiments from GitHub.

```bash
uproot examples
```

Downloads and extracts all example apps into the current directory. Useful for learning and reference.

### uproot deployment

Print the currently set `UPROOT_*` environment variables.

```bash
uproot deployment
```

## Using with uv

If you're using uv (recommended), prefix commands with `uv run`:

```bash
uv run uproot run
uv run uproot new my_app
uv run uproot dump --file backup.bin
```
