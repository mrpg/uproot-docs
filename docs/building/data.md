# Storing and accessing data

uproot uses an **append-only log** for all data storage. Every change is permanently recorded with a timestamp, creating a complete audit trail of your experiment. This architecture ensures data integrity, enables temporal analysis, and makes your research fully reproducible.

## The append-only log

Unlike traditional databases that overwrite data, uproot appends every change to a permanent log. This means:

- **Complete history**: Every value a field ever held is recorded
- **Timestamps**: Each change includes when it happened
- **Audit trail**: The code location that made each change is tracked
- **No data loss**: Even deleted fields are preserved (as "tombstones")

### Why this matters for research

The append-only log provides:

1. **Reproducibility** — Analyze the exact sequence of participant decisions
2. **Debugging** — Trace when and where unexpected values appeared
3. **Temporal analysis** — Study how responses evolved over time
4. **Data integrity** — No accidental overwrites or race conditions

See [Exporting data](../running/export.md) for more information about when this data is exported.

## Initialization callbacks

Two module-level functions let you set up initial data before participants see any pages.

### new_session

`new_session(session)` is called once when a session is initialized. Use it to set up session-wide data—shared configuration, models, or anything that should exist before any player arrives:

```python
def new_session(session):
    session.chat = chat.create(session)
    session.total_contributions = 0
```

### new_player

`new_player(player)` is called once per participant when they first join. Use it to set up per-player defaults:

```python
def new_player(player):
    player.round = 0
    player.payoff = 0
    player.my_chat = chat.create(player.session)
    chat.add_player(player.my_chat, player)
```

### Lazy execution

Both callbacks are **lazy**: they run when the first participant initializes, not when the session is created in the admin. `new_session` runs before `new_player` for the very first participant in a session.

!!! note
    Both `new_session` and `new_player` can be manually re-triggered from the admin session dashboard—useful for resetting state or re-running initialization after fixing a bug mid-experiment.

:material-github: [See new_player and new_session in the chat example](https://github.com/mrpg/uproot-examples/tree/master/chat) · [conjoint example](https://github.com/mrpg/uproot-examples/tree/master/conjoint)

## Player data

Store data on individual participants using simple attribute assignment:

```python
class Decision(Page):
    fields = dict(
        choice=RadioField(label="Your choice", choices=[(1, "A"), (2, "B")]),
    )

    @classmethod
    def before_next(page, player):
        # Form fields are saved automatically, but you can add computed fields:
        player.made_choice = True
        player.choice_time = time()
```

Read data back the same way:

```python
class Results(Page):
    @classmethod
    def templatevars(page, player):
        return dict(
            their_choice=player.choice,
            choice_time=player.choice_time,
        )
```

Form field values are saved automatically when participants submit. You can store any additional data you need.

## Session data

Store data shared across all participants in a session using `player.session`:

```python
class Setup(NoshowPage):
    @classmethod
    def after_always_once(page, player):
        if not hasattr(player.session, "initialized"):
            player.session.initialized = True
            player.session.start_time = time()
            player.session.total_contributions = 0
```

Access session data from any player:

```python
@classmethod
def templatevars(page, player):
    return dict(
        session_start=player.session.start_time,
        total=player.session.total_contributions,
    )
```

Session data is visible to all participants and persists for the duration of the session.

### Session settings

When a session is created in the admin interface, administrators can provide a JSON settings object. Access these settings from any page via `player.session.settings`:

```python
class Decision(Page):
    @classmethod
    def templatevars(page, player):
        return dict(
            n_rounds=player.session.settings.get("n_rounds", C.DEFAULT_ROUNDS),
        )
```

In templates:

```html+jinja
<p>This session has {{ player.session.settings.n_pairs }} pairs.</p>
```

`session.settings` is a read-only dict-like object that supports both attribute access (`settings.key`) and `.get(key, default)`.

:material-github: [See the read_settings example](https://github.com/mrpg/uproot-examples/tree/master/read_settings) · [conjoint example](https://github.com/mrpg/uproot-examples/tree/master/conjoint)

## Group data

For multiplayer experiments, store data at the group level using `player.group`:

```python
class GroupPlease(GroupCreatingWait):
    group_size = 2

    @classmethod
    def after_grouping(page, group):
        group.round = 1
        group.total_payoff = 0
```

Access group data from any group member:

```python
@classmethod
def templatevars(page, player):
    return dict(
        current_round=player.group.round,
        group_total=player.group.total_payoff,
    )
```

## Working with mutable types

When mutating lists or dictionaries in-place, uproot needs to know the value changed. Inside standard page methods (`templatevars`, `before_next`, `after_once`, etc.), this is handled automatically. Outside of page methods — for example, in standalone helper functions or `@live` methods — use a context manager:

```python
with player as p:
    p.scores.append(100)
    p.responses["q1"] = "yes"
# Changes are saved when exiting the with block
```

Using a context manager is always safe, even when not strictly required.

## Supported data types

uproot supports all common Python types:

| Type | Example |
|------|---------|
| Numbers | `player.score = 100`, `player.rate = 0.75` |
| Strings | `player.name = "Alice"` |
| Booleans | `player.consented = True` |
| Lists | `player.choices = [1, 2, 3]` |
| Dictionaries | `player.responses = {"q1": "yes"}` |
| None | `player.partner = None` |
| Decimals | `player.payment = Decimal("10.50")` |
| Tuples | `player.coordinates = (10, 20)` |

Nested structures work too:

```python
player.trial_data = {
    "round": 1,
    "choices": [1, 2, 3],
    "timing": {"start": 100.5, "end": 105.2},
}
```

Several other types are also supported, such as `set` and `random.Random`. A full list of permitted types is available [here](https://github.com/mrpg/uproot/blob/main/src/uproot/stable.py#L21).

## Accessing other players

### Virtual fields (preferred)

uproot provides virtual fields on `player` for convenient access to related players. These work in page methods and directly in templates:

```python
# Other player in a 2-person group
partner_choice = player.other_in_group.choice

# All other players in the group (excluding current player)
for p in player.others_in_group:
    total += p.contribution

# Other player in a 2-person session
partner = player.other_in_session

# All other players in the session (excluding current player)
for p in player.others_in_session:
    print(p.name, p.payoff)
```

The same virtual fields work on `group` and `session` objects:

```python
# All players in a group
for p in player.group.players:
    total += p.contribution

# All players in a session
for p in player.session.players:
    print(p.name, p.payoff)

# All groups in a session
for g in player.session.groups:
    print(g.name)
```

### Function form

The standalone functions `other_in_group(player)`, `others_in_group(player)`, and `players(group)` remain available as alternatives.

### Accessing history (advanced)

View the complete history of a player's data:

```python
history = player.__history__()
# Returns: {"choice": [Value(...), Value(...)], "payoff": [...], ...}
```

Each historical value includes:
- `time` — Unix timestamp of the change
- `data` — The value that was stored
- `context` — The file and line that made the change
- `unavailable` — Whether this represents a deletion of a field

## Quick reference

| Storage level | Access | Use for |
|---------------|--------|---------|
| `player.field` | Individual | Participant responses, computed values |
| `player.session.field` | Shared | Session config, aggregate statistics |
| `player.group.field` | Group only | Group state, shared resources |

| Pattern | When to use |
|---------|-------------|
| `player.x = value` | Storing immutable data (numbers, strings, bools) |
| `with player as p:` | Mutating lists or dicts outside page methods |
| `hasattr(player, "x")` | Checking if a field exists |
| `player.__history__()` | Accessing the complete audit trail |

:material-github: [See data patterns in the examples](https://github.com/mrpg/uproot-examples)
