---
description: 'How uproot stores data in an append-only log: personal data, player, group, and session data, initialization callbacks, random numbers, mutable values, and accessing other players.'
---

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

1. **Reproducibility:** Analyze the exact sequence of participant decisions.
2. **Debugging:** Trace when and where unexpected values appeared.
3. **Temporal analysis:** Study how responses evolved over time.
4. **Data integrity:** No accidental overwrites or race conditions.

### Personal data stays in the log

Because uproot never deletes anything, every value a participant submits stays in your database for good. Overwriting or deleting the field later does not remove the earlier value. The only way to remove it is to delete the entire database with [`uproot reset`](../reference/cli.md).

So decide before your study runs which personal data (names, email addresses, bank details, and so on) should reach the database at all:

- To check or process a value without saving it, use [stealth fields](forms.md#stealth-fields).
- To keep a value away from the server entirely, do not submit it. Form inputs without a `name` attribute are never sent. You can, for example, encrypt contact details in the participant’s browser and submit only the encrypted text. The [e2mupay](https://github.com/mrpg/e2mupay) apps do this with OpenPGP.

See [Exporting data](../running/export.md) for more information about when this data is exported.

## Initialization callbacks

Two module-level functions let you set up initial data before participants see any pages.

### new_session

`new_session(session)` is called once when a session is initialized. Use it to set up session-wide data, such as shared configuration, models, or anything that should exist before any player arrives:

```python
def new_session(session):
    session.chat = chat.create(session)
    session.total_contributions = 0
```

### new_player

`new_player(player)` is called once per participant when they start the study. Use it to set up per-player defaults:

```python
def new_player(player):
    player.payoff = 0
    player.my_chat = chat.create(player.session)
    chat.add_player(player.my_chat, player)
```

### Every app at once

When a participant starts, uproot calls `new_player` of **every app** in the configuration, in app order. It does not wait until the participant reaches each app. (Likewise, the first participant to start triggers `new_session` of every app.) So an app that comes last in the configuration can still prepare data at the very start, for example to record when the participant began:

```python
from datetime import datetime, timezone


def new_player(player):
    player.started_at = datetime.now(timezone.utc).isoformat()
```

The flip side is that `new_player` cannot use anything the participant does in earlier apps, because none of it has happened yet.

!!! warning "Using data from an earlier app in `new_player`"
    Suppose the app `survey` asks for `player.age`, and a later app `treatment` reads it in `new_player`:

    ```python
    def new_player(player):
        player.high_dose = player.age >= 30  # Wrong: runs before the survey
    ```

    The participant cannot start the study. uproot reports `AttributeError: Player(*('nvfyk', 'ic9uj')) has no .age`, because `player.age` does not exist yet. Move such code to the first page of `treatment`, using [`before_once`](../reference/page-methods.md#before_once), which runs when the participant actually gets there:

    ```python
    class Instructions(Page):
        @classmethod
        def before_once(page, player):
            player.high_dose = player.age >= 30
    ```

### Lazy execution

Both callbacks are **lazy**: they run when a participant opens their link for the first time, not when you create the session in the admin. `new_session` runs before `new_player` for the very first participant in a session.

Two [admin actions](../running/admin.md) initialize participants who have not started yet: **Run `new_player`** and **Mark as dropout**. For these participants, the callbacks run at the moment of the admin action. Keep this in mind if `new_player` records a time.

!!! note "Each callback runs only once"
    `new_session` runs at most once per session, and `new_player` at most once per participant. Running them again from the admin has no effect on sessions and participants that are already initialized. In particular, you cannot use these actions to reset data or to rerun corrected code mid-experiment. To correct existing data, set the fields directly, for example with **Set fields** in the admin.

[:material-github: See new_player and new_session in the chat example](https://github.com/mrpg/uproot-examples/tree/main/chat) · [conjoint example](https://github.com/mrpg/uproot-examples/tree/main/conjoint)

## Random numbers

Use `rng()` whenever you need randomness—whether for assigning treatments, shuffling, or drawing from a distribution. It returns an independent `random.Random` object seeded from the operating system. If later draws must continue the same random sequence, store the generator on the player; the data layer saves its state.

```python
def new_player(player):
    randomizer = rng()
    player.treatment = randomizer.choice(["A", "B"])
    player.rng = randomizer
```

Do not use the module-level functions in `random` for experiment outcomes. A generator returned by `rng()` can be saved and resumed, which makes a sequence of draws reproducible from its stored state.

[:material-github: See the treatments example](https://github.com/mrpg/uproot-examples/tree/main/treatments)

## Player data

Store data on individual participants using simple attribute assignment:

```python
class Decision(Page):
    fields = dict(
        choice=RadioField(label="Your choice", choices=[(1, "A"), (2, "B")]),
    )

    @classmethod
    def after_once(page, player):
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

!!! warning
    The names `along`, `fields`, `flush`, `get`, `history`, `refresh`, `strict`, and `within` are reserved for storage operations. Use a different name for your own data fields.

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

Apps can replace the admin’s raw JSON settings editor with their own form, see [Custom settings forms](../advanced/settings-forms.md).

[:material-github: See the read_settings example](https://github.com/mrpg/uproot-examples/tree/main/read_settings) · [conjoint example](https://github.com/mrpg/uproot-examples/tree/main/conjoint)

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

When mutating lists or dictionaries in-place, uproot needs to know the value changed. Inside standard page methods (`templatevars`, `after_once`, `after_always_once`, etc.), this is handled automatically. Outside of page methods—for example, in standalone helper functions or `@live` methods—use a context manager:

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
| Strings | `player.nickname = "Alice"` |
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

Several other types are also supported, such as `set` and `random.Random`. A full list of permitted types is available [here](https://github.com/mrpg/appendmuch/blob/main/src/appendmuch/codec.py).

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

# Only groups created in this app (needed in multi-app configs)
for g in player.session.groups(app=__name__):
    print(g.name)
```

There is no separate function-form API for these relationships in the current
framework; use the virtual fields shown above.

### Accessing history (advanced)

View the complete history of a player’s data:

```python
history = player.history()
# Returns: {"choice": [Value(...), Value(...)], "payoff": [...], ...}
```

Each historical value includes:

- `time`: Unix timestamp of the change;
- `data`: the value that was stored;
- `context`: the file and line that made the change;
- `unavailable`: whether this represents a deletion of a field.

Use `player.fields()` when you only need the names of fields that are currently available:

```python
field_names = player.fields()
# Returns: ["choice", "payoff", ...]
```

## Quick reference

| Storage level | Access | Use for |
|---------------|--------|---------|
| `player.field` | Individual | Participant responses, computed values |
| `player.session.field`{ .text-nowrap } | Shared | Session config, aggregate statistics |
| `player.group.field` | Group only | Group state, shared resources |

| Pattern | When to use |
|---------|-------------|
| `player.x = value` | Storing immutable data (numbers, strings, bools) |
| `with player as p:` | Mutating lists or dicts outside page methods |
| `hasattr(player, "x")` | Checking if a field exists |
| `player.fields()` | Listing the currently available fields |
| `player.history()`{ .text-nowrap } | Accessing the complete audit trail |

[:material-github: See data patterns in the examples](https://github.com/mrpg/uproot-examples)
