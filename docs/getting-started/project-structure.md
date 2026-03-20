# Project structure

An uproot project is a Python package with a specific layout. Here's what a typical project looks like.

## Directory layout

```
my_project/
├── main.py                  # Entry point and configuration
├── pyproject.toml           # Python dependencies
├── Procfile                 # For cloud deployment (Heroku, Railway)
├── uproot_license.txt       # uproot's LGPL license
├── my_app/
│   ├── __init__.py          # App logic: pages, fields, callbacks
│   ├── Welcome.html         # Template for Welcome page
│   ├── Decision.html        # Template for Decision page
│   ├── Results.html         # Template for Results page
│   └── static/              # App-specific static files (optional)
│       └── diagram.png
└── another_app/
    ├── __init__.py
    └── ...
```

## main.py

The entry point configures your experiment and starts the server:

```python
import uproot.deployment as upd
from uproot.cli import cli
from uproot.server import load_config, uproot_server

upd.project_metadata(created="1970-01-01", uproot="*.*.*")

load_config(uproot_server, config="my_experiment", apps=["my_app"])

upd.ADMINS["admin"] = ...  # Ellipsis = auto-login on localhost

upd.LANGUAGE = "en"  # Available: "de", "en", "es"

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
# Enable the REST API
upd.API_KEYS.add("your-api-key")
```

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

- **`page_order`** — List of page classes (and [SmoothOperators](../building/operators.md)) that define the participant flow:

```python
page_order = [Welcome, Decision, Results]
```

### Optional module-level attributes

| Attribute | Purpose |
|-----------|---------|
| `DESCRIPTION` | Human-readable description shown in admin |
| `SUGGESTED_MULTIPLE` | Hint for session creation (e.g., `2` for pair experiments) |
| `LANDING_PAGE` | If `True`, shows a landing page before the app starts |
| `C` | Constants class, available in templates as `C` |

### Optional callbacks

| Callback | When it runs |
|----------|-------------|
| `new_session(session)` | Once when session initializes |
| `new_player(player)` | Once per player when they join |
| `restart()` | On server restart (can be async) |
| `digest(session)` | Returns data for admin digest view |
| `language(player)` | Returns ISO 639 language code for the player |

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

Each page needs a corresponding HTML template in the same directory. By default, uproot looks for a file matching the class name:

```
my_app/
├── __init__.py      # class Welcome(Page)
└── Welcome.html     # Template for Welcome
```

Templates extend a base layout:

```html+jinja
{% extends "Base.html" %}

{% block title %}Welcome{% endblock title %}

{% block main %}
<h1>Welcome to the experiment</h1>
{% endblock main %}
```

### PlayerContext

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
| `UPROOT_API_KEY` | — | API key for the REST API |

Run `uproot deployment` to see the current values.

## What's next?

- **[Pages and templates](../building/pages.md)** — How pages work
- **[Collecting data with forms](../building/forms.md)** — Available field types
- **[The admin interface](../running/admin.md)** — Managing your experiments
