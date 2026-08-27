# Project structure

An uproot project is a Python package with a specific layout. Here is what a typical project looks like.

## Directory layout

```
my_project/
├── main.py                  # Entry point and configuration
├── pyproject.toml           # Python dependencies
├── requirements.txt         # Alternative dependency file
├── .env                     # Local environment settings
├── Procfile                 # For cloud deployment (Heroku, Railway)
├── uproot_license.txt       # uproot’s LGPL license
├── _static/                 # Static files shared by all apps (optional)
├── my_app/
│   ├── __init__.py          # App logic: pages, fields, callbacks
│   ├── Welcome.html         # Template for Welcome page
│   ├── Decision.html        # Template for Decision page
│   ├── Results.html         # Template for Results page
│   ├── simulate.js          # Automated page interactions for testing (optional)
│   └── _static/             # App-specific static files (optional)
│       └── diagram.png
└── another_app/
    ├── __init__.py
    └── ...
```

## The `main.py` file

The entry point configures your experiment and starts the server:

```python
import uproot.deployment as upd
from uproot.cli import cli
from uproot.server import load_config, uproot_server

upd.project_metadata(created="1970-01-01", uproot="*.*.*")

load_config(uproot_server, config="my_experiment", apps=["my_app"])

upd.ADMINS["admin"] = upd.auto_login()  # Token login locally; password in production

upd.LANGUAGE = "en"  # Built-in: "de", "en", "es", "ja"

if __name__ == "__main__":
    cli()
```

### Configs

Each `load_config` call registers a **config**—a named experiment configuration that specifies which apps to run and in what order:

```python
# A single-app config
load_config(uproot_server, config="survey", apps=["survey"])

# A multi-app config: participants go through both apps in sequence
load_config(uproot_server, config="full_experiment", apps=["instructions", "game", "survey"])
```

When you create a session in the admin, you select a config. The session runs all listed apps in order.

During development, the fastest way to try a config is [`uproot start`](../reference/cli.md#uproot-start): `uv run uproot start my_experiment` starts the server and prints a participant link for that config, with no admin steps needed.

You can optionally pass a `settings` dictionary to `load_config` that provides default session settings:

```python
load_config(
    uproot_server,
    config="my_experiment",
    apps=["my_app"],
    settings={"n_rounds": 5, "show_feedback": True},
)
```

### Admin accounts

```python
# Auto-login on localhost (development only)
upd.ADMINS["admin"] = ...

# Password-protected (required for production)
upd.ADMINS["admin"] = "your-secure-password"
```

### API keys

```python
# Register a server-side REST API token
upd.API_KEYS.add("your-api-key")
```

`UPROOT_API_KEY` is read by the `uproot api` client. It does not register a
server token by itself; add the token to `upd.API_KEYS` in the project.

### Default rooms

```python
from uproot.rooms import room

upd.DEFAULT_ROOMS.append(
    room("my_room", config="my_experiment", labels=["A", "B", "C"])
)
```

Rooms defined this way are created automatically when the server starts.

## App module

Each app is a Python package (a directory with `__init__.py`). The `__init__.py` defines the experiment logic.

### Required

- **`page_order`**—list of page classes (and [SmoothOperators](../building/operators.md)) that define the participant flow:

```python
page_order = [Welcome, Decision, Results]
```

### Optional module-level attributes

| Attribute | Purpose |
|-----------|---------|
| `DESCRIPTION` | Human-readable description shown in admin |
| `SUGGESTED_MULTIPLE` | Hint for session creation (e.g., `2` for pair experiments) |
| `LANDING_PAGE` | If `True`, inserts a landing page before the app’s pages. Override it with `LandingPage.html` in the app directory, or add extra text with `LandingPageInfo.html` |
| `C` | Constants class, available in templates as `C`. Set `C.__export__` to a list of names (or `...`) to copy those constants into JavaScript as `window.C` |

### Optional callbacks

| Callback | When it runs |
|----------|-------------|
| `new_session(session)` | Once when session initializes |
| `new_player(player)` | Once per player when they join |
| `restart()` | On server restart (can be async) |
| `digest(session)` | Returns data for the admin digest view (pair with `AdminDigest.html`) |
| `pipeline(session)` | Admin-runnable job; return a list of dicts for a downloadable table. May take optional `data=` |
| `language(player)` | Returns ISO 639 language code for the player |
| `api(request, session)` | Authenticated HTTP endpoint at `/api/{app}/{sname}/` |
| `api2(request, session)` | Unauthenticated HTTP endpoint at `/api2/{app}/{sname}/`—treat input as public |

See [Storing and accessing data](../building/data.md) for details on `new_session` and `new_player`.

### Page classes

Pages are defined as classes that inherit from `Page`, `NoshowPage`, `GroupCreatingWait`, or `SynchronizingWait`:

```python
class Welcome(Page):
    pass

class Calculate(NoshowPage):
    @classmethod
    def after_always_once(page, player):
        player.score = player.correct * 10
```

See [Pages and templates](../building/pages.md) for details.

### Templates

Each displayed page needs a corresponding HTML or [Markdown](../building/pages.md#markdown-pages) template in the same app directory. By default, uproot first looks for an `.html` file matching the class name, then for `.md`:

```
my_app/
├── __init__.py      # class Welcome(Page)
└── Welcome.html     # Template for Welcome (or Welcome.md)
```

HTML templates extend a base layout:

```html+jinja
{% extends "Base.html" %}

{% block title %}Welcome{% endblock title %}

{% block main %}
<h1>Welcome to the experiment</h1>
{% endblock main %}
```

### Using `PlayerContext`

Define a `Context` class for computed values accessible across all templates:

```python
class Context(PlayerContext):
    @property
    def total_earnings(self):
        return self.player.payoff * C.EXCHANGE_RATE
```

Available in templates as `player.context.total_earnings`.

## Database

uproot uses SQLite by default. The database file `uproot.sqlite3` is created automatically in your project directory when the server starts. No configuration needed.

SQLite works well in production too—uproot is optimized for it. PostgreSQL is available as an alternative but is never required. See [Deployment](../running/deployment.md) for details.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `UPROOT_DATABASE` | `sqlite3` | Database driver (`sqlite3`, `memory`, `postgresql`) |
| `UPROOT_SQLITE3` | `uproot.sqlite3` | SQLite file path |
| `UPROOT_POSTGRESQL` | — | PostgreSQL connection URL |
| `UPROOT_ORIGIN` | — | Public server URL |
| `UPROOT_SUBDIRECTORY` | — | Subdirectory prefix for all routes |
| `UPROOT_API_KEY` | — | Bearer token used by the `uproot api` client |
| `UPROOT_ADMIN_PASSWORD` | — | Password used by `upd.auto_login()` when set |
| `UPROOT_ALLOW_ENTER` | off | If `1`/`true`/`yes`/`on`, the Enter key submits participant forms |

Run `uproot deployment` to see the current values.

## What’s next?

- **[Pages and templates](../building/pages.md)**—How pages work.
- **[Collecting data with forms](../building/forms.md)**—Available field types.
- **[The admin interface](../running/admin.md)**—Managing your experiments.
