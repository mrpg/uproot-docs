# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv run mkdocs build    # Build static HTML to site/
uv run mkdocs serve    # Local preview server at http://127.0.0.1:8000
```

Deploy to production:
```bash
uv run mkdocs build && rsync --delete -PaczL site mg.sb:/srv/http/uproot.science/
```

## Documentation structure

This is MkDocs documentation for [uproot](https://github.com/mrpg/uproot), a framework for browser-based behavioral experiments.

- `mkdocs.yml` — Site configuration and navigation structure
- `docs/` — Markdown source files
- `docs/assets/` — Logo, favicon, images
- `requirements.txt` — mkdocs-material dependency

The navigation follows a learning arc: orient → build → connect → harden → operate → look up.

1. **Getting started** — Installation, tutorial, project structure
2. **Building experiments** — Pages, forms, data, results, SmoothOperators, live methods, Alpine.js
3. **Multiplayer experiments** — Groups, synchronization, real-time, chat
4. **Advanced features** — Timeouts, dropouts, uploads, custom data models
5. **Running experiments** — Admin, sessions/rooms, export, deployment
6. **Reference** — Fields, page methods, API, admin API, CLI

Key structural decisions:
- Sessions and rooms are a single page (`running/rooms.md`), not two — sessions was too thin to stand alone
- Alpine.js lives in Building (not Advanced) — it's a building tool like live methods
- Rounds/randomization do not have their own pages — they are covered by SmoothOperators (`building/operators.md`)
- Results follows Data in the Building section (natural collect → display arc)

## Style guidelines

- Use sentence case for headings, not Title Case
- Keep pages focused on what users want to accomplish
- Link to [uproot-examples](https://github.com/mrpg/uproot-examples) for complete working code
- Use admonitions (`!!! note`, `!!! warning`) for callouts
- Use tabbed content (`=== "Tab"`) for platform-specific instructions
- uproot-examples uses the `master` branch (not `main`), so links should be e.g. `https://github.com/mrpg/uproot-examples/tree/master/...`
- Use `:material-github:` prefix for GitHub links in docs
- No manual imports needed in code examples—uproot projects have everything available automatically via `from uproot.smithereens import *`
- Avoid guide pages that are just thin wrappers pointing to another page — either cover the topic properly or don't give it its own page

## Related repositories

- `../uproot/` — The main uproot framework (source in `src/uproot/`)
- `../uproot-examples/` — Example experiments to reference in docs

## Key uproot concepts

### Page types
- `Page` — Standard page with optional form fields
- `NoshowPage` — Runs code without displaying (for setup/scoring)
- `GroupCreatingWait` — Waits and forms groups of participants
- `SynchronizingWait` — Waits for all group members to arrive

### SmoothOperators (control page_order flow)
- `Random` — Shuffles pages into random order
- `Bracket` — Groups pages as an atomic unit (use with Random)
- `Rounds` — Repeats pages n times (fixed count via `n=` parameter)
- `Repeat` — Repeats indefinitely until `player.add_round = False`
- `Between` — Randomly selects one option (for between-subjects designs)

### Data model
- `player` — Individual participant data storage
- `group` — Shared group data (multiplayer experiments)
- `session` — Session-level data
- `group.players` — All players in a group (returns `StorageBunch`)
- `session.players` — All players in a session (returns `StorageBunch`)
- `session.groups` — All groups in a session
- `player.other_in_group` — The other player (2-person groups; `other_in_group(player)` still works)
- `player.others_in_group` — All other players in the group
- `player.other_in_session` — The other player in a 2-person session
- `player.others_in_session` — All other players in the session
- `session.settings` — Session settings as a read-only dotted dict (set via admin JSON)

### StorageBunch and the `_` field referent
`StorageBunch` is the collection type returned by `group.players`, `session.players`, etc. It supports:
- Iteration: `for p in group.players`
- Unpacking: `p1, p2 = group.players`
- `filter(*comparisons)` — Filter using `_` comparisons
- `find_one(**kwargs)` — Find exactly one match (raises on 0 or 2+)
- `each(*keys, simplify=True)` — Extract field values into a list
- `assign(key, values)` — Set a field on all items from an iterable
- `apply(fn)` — Call a function once per item (supports async)

`_` (from `uproot.smithereens`) is a `FieldReferent` — a placeholder that builds lazy comparisons evaluated per item. Source: `src/uproot/queries.py`.
```python
# _ supports ==, !=, >, >=, <, <= and chained attribute access
cooperators = group.players.filter(_.cooperate == True)
eligible = session.players.filter(_.present == True, _.age >= 18)
same_round = session.players.filter(_.group.round == 3)
```
Bare `_.field` (no operator) tests for truthiness. To check for `False`, write `_.field == False`.

### Page methods (classmethod pattern)
```python
class MyPage(Page):
    @classmethod
    def templatevars(page, player):
        return dict(...)  # Variables for template

    @classmethod
    def show(page, player):
        return True/False  # Conditional display

    @classmethod
    def before_next(page, player):
        ...  # Run before advancing to next page
```

### PlayerContext (pythonic alternative to templatevars)
```python
class Context(PlayerContext):
    @property
    def my_value(self):
        return self.player.some_field  # Available as player.context.my_value in templates
```

### Form fields
Defined in `fields` dict or async `fields()` method (all from `uproot.fields`):
- `StringField`, `TextAreaField`, `EmailField`, `IBANField` — Text inputs
- `IntegerField`, `DecimalField` — Numeric inputs (support `min`, `max`, `addon_start`, `addon_end`)
- `RadioField`, `SelectField` — Single selection (`choices` param; RadioField supports `layout="horizontal"`)
- `BooleanField` — Checkbox
- `LikertField` — Rating scale (`min`, `max`, `label_min`, `label_max`)
- `DecimalRangeField` — Slider (`min`, `max`, `step`, `label_min`, `label_max`, `hide_popover`, `anchoring`)
- `BoundedChoiceField` — Multi-select checkboxes (`choices`, `min`, `max` selections)
- `DateField` — Date picker
- `FileField` — File upload (always a stealth field, handled via `handle_stealth_fields`)

Common parameters: `label`, `optional`, `description`, `default`, `render_kw`, `class_wrapper`

### Page lifecycle (execution order)
1. `show(page, player)` → skip page if False
2. `early(page, player, request=)` → earliest hook, has access to HTTP request
3. `before_always_once(page, player)` → runs once per page display
4. `before_once(page, player)` → runs once per player (first visit only)
5. `fields(page, player)` → dynamic form fields
6. `templatevars(page, player)` / `jsvars(page, player)` → template/JS data
7. *(page renders)*
8. `validate(page, player, data)` → return str, list[str], or dict[str, str] for errors
9. `may_proceed(page, player)` → gate before advancing
10. `stealth_fields` / `handle_stealth_fields(page, player, data)` → manual field handling
11. `after_always_once(page, player)` → after each submission
12. `after_once(page, player)` → after first submission only
13. `before_next(page, player)` → last hook before advancing to next page
14. `timeout(page, player)` / `timeout_reached(page, player)` → page timeouts

### Mutable data in page methods
Inside standard page methods, uproot auto-tracks mutations to lists/dicts. Outside page methods (helpers, `@live` methods), use a context manager:
```python
with player as p:
    p.scores.append(100)
```
Using a context manager is always safe, even when not strictly required.

### Real-time features
- `@live` decorator makes page methods callable from JS via `uproot.invoke("method", args)`
- `notify(sender, recipients, data, event=)` — broadcast to players
- `send_to(recipients, data, event=)` — server-initiated push
- `reload(player)`, `move_to_page(player, PageClass)`, `move_to_end(player)`

### Dropout handling
- `watch_for_dropout(player, handler, tolerance=30.0)` — monitor for disconnection
- `mark_dropout(pid)` — manual dropout
- Handler is an async function receiving `player`

### Custom data models (`uproot.models`)
- `Entry` metaclass for defining entry types (immutable dataclasses)
- `create_model(session)` → `ModelIdentifier`
- `add_entry(mid, player, EntryType, **fields)` — auto-fills identifier fields
- `get_entries(mid, EntryType)` → list of `(UUID, time, entry)` tuples
- `filter_entries(mid, EntryType, **filters)`, `get_latest_entry(mid, EntryType)`

### App module conventions
- `DESCRIPTION` — shown in admin
- `SUGGESTED_MULTIPLE` — hint for session player count (admin shows this when creating sessions)
- `LANDING_PAGE` — if True, shows landing page before app
- `C` — constants class, available in templates
- `new_session(session)` — once per session init (lazy: runs when first player arrives)
- `new_player(player)` — once per player init
- `restart()` — on server restart (can be async)
- `digest(session)` — data for admin digest view
- `page_order` — can be a list or a callable taking `player=`

### Templates
- Extend `"Base.html"` (participant-facing) or `"_uproot/Page.html"`
- Blocks: `{% block title %}`, `{% block main %}`, `{% block head %}`, `{% block late %}`
- `{{ fields() }}` renders all form fields; `{{ field(form.name) }}` renders one
- `{{ chat(session.chat) }}` renders chat widget
- Built-in filters: `| to(n)` (decimal places), `| fmtnum(pre=, post=, places=)`
- All Python builtins available in templates (`sum()`, `max()`, `min()`, `len()`, `range()`, `enumerate()`, `zip()`)
- `{% set buttons = False %}` to hide navigation buttons
- `player.along("round")` — iterate all rounds as `(round_number, data)` tuples
- `player.within(round=n)` — access data from a specific round

### CLI commands
**Global**: `uproot setup <path>`, `uproot api <endpoint>`, `uproot --version`
**Project** (run from project dir): `uproot run`, `uproot reset`, `uproot dump --file`, `uproot restore --file`, `uproot new <app>`, `uproot newpage <app> <page>`, `uproot examples`, `uproot deployment`

### Admin interface
- Web UI at `/admin/` with session/room management
- Player actions: advance, revert, move to end, reload, send message, mark dropout, redirect, set fields, group/ungroup
- Data browser, page times CSV, digest view
- REST API at `/admin/api/v1/` with Bearer token auth (`upd.API_KEYS.add(key)`)

### Database and deployment
- SQLite by default (`uproot.sqlite3`), works well in production — PostgreSQL is available but never required
- Environment vars: `UPROOT_DATABASE`, `UPROOT_SQLITE3`, `UPROOT_POSTGRESQL`, `UPROOT_ORIGIN`, `UPROOT_SUBDIRECTORY`, `UPROOT_API_KEY`
- `upd.ADMINS["admin"] = ...` (Ellipsis = auto-login on localhost)
- `upd.LANGUAGE` — `"de"`, `"en"`, `"es"`
- Rooms: `upd.DEFAULT_ROOMS.append(room(name, config=, labels=, capacity=, open=))`

### Data export
- Formats: `ultralong` (one row per field change), `sparse` (wide), `latest` (current values only)
- `filters=True` cleans up internal `_uproot_*` fields
- Page times CSV tracks when players entered/left each page
- `uproot dump`/`uproot restore` for full database backup
