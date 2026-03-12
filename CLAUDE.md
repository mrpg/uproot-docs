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

The navigation is organized by user goals:

1. **Getting started** — Installation, tutorial, project structure
2. **Building experiments** — Pages, forms, data, results
3. **Multiplayer experiments** — Groups, synchronization, real-time, chat
4. **Advanced features** — Rounds, randomization, timeouts, dropouts, uploads, models
5. **Running experiments** — Admin, sessions/rooms, export, deployment
6. **Reference** — Fields, page methods, API, CLI

## Style guidelines

- Use sentence case for headings, not Title Case
- Keep pages focused on what users want to accomplish
- Link to [uproot-examples](https://github.com/mrpg/uproot-examples) for complete working code
- Use admonitions (`!!! note`, `!!! warning`) for callouts
- Use tabbed content (`=== "Tab"`) for platform-specific instructions
- uproot-examples uses the `master` branch (not `main`), so links should be e.g. `https://github.com/mrpg/uproot-examples/tree/master/...`
- Use `:material-github:` prefix for GitHub links in docs
- No manual imports needed in code examples—uproot projects have everything available automatically

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
- `group.players` — All players in a group (preferred; `players(group)` still works)
- `session.players` — All players in a session
- `session.groups` — All groups in a session
- `player.other_in_group` — The other player (2-person groups; `other_in_group(player)` still works)
- `player.others_in_group` — All other players in the group
- `player.other_in_session` — The other player in a 2-person session
- `player.others_in_session` — All other players in the session
- `session.settings` — Session settings as a read-only dotted dict (set via admin JSON)

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
Defined in `fields` dict or async `fields()` method:
- `TextField`, `IntegerField`, `FloatField`
- `RadioField`, `CheckboxField`, `SelectField`
- `SliderField`, `RangeSliderField`
- `HiddenField`
