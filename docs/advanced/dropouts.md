# Handling dropouts

In multiplayer experiments, participants may close their browser or lose their connection. uproot provides tools to detect dropouts and handle them gracefully.

## Automatic dropout detection

Use `watch_for_dropout` to monitor a player and trigger a callback when they go offline:

```python
def new_player(player):
    player.dropout = False
    watch_for_dropout(player, handle_dropout)


async def handle_dropout(player):
    player.dropout = True
    move_to_end(player)
```

The watcher checks every few seconds whether the player’s browser is still connected. If the player has been offline for longer than the tolerance period (default: 30 seconds), the handler fires.

:material-github: [See the dropouts example](https://github.com/mrpg/uproot-examples/tree/master/dropouts)

## watch_for_dropout

```python
watch_for_dropout(player, handler, tolerance=30.0)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `player` | player | — | The player to watch |
| `handler` | async function | — | Called when dropout is detected |
| `tolerance` | `float` | `30.0` | Seconds of inactivity before triggering |

The handler receives the `player` as its argument. It can be an async function.

Register the watcher in `new_player` so it starts monitoring as soon as the player joins.

## Moving dropouts to the end

The most common response to a dropout is to move them to the end page:

```python
async def handle_dropout(player):
    player.dropout = True
    move_to_end(player)
```

`move_to_end(player)` advances the player past all remaining pages. If they return, they will see the end page instead of being stuck on a wait page that blocks other players.

## Marking dropouts manually

From the admin interface, select players and use the **Mark as dropout** action.
This sets `player._uproot_dropout = True` and triggers the admin dropout flow.

Programmatically:

```python
from uproot.smithereens import mark_dropout

mark_dropout(player.pid)
```

`mark_dropout` marks the player for the dropout watcher. Register a watcher if
you want a handler to run; the function alone does not move the player or call
the handler immediately.

## Handling dropouts in group experiments

In multiplayer experiments, a dropout can block other group members at synchronization points. A single participant closing their browser, walking away, or losing connectivity can leave their partner staring at “waiting for other participants” indefinitely.

A robust solution tracks dropout at the *group* level and handles three distinct dropout vectors:

1. **Browser disconnect:** The participant closes the tab or loses connectivity (`watch_for_dropout`).
2. **Page timeout:** The participant sits on a decision page without submitting (`timeout_reached`).
3. **Sync timeout:** One participant submits but their partner never arrives at the wait page (`timeout` on `SynchronizingWait`).

### The group-level drop pattern

Use a boolean `group.dropped` flag as the single source of truth. When any dropout vector fires, mark the group and redirect all other members to a dedicated Dropped page:

```python
class C:
    TIMEOUT = 60       # seconds to make a decision
    SYNC_TIMEOUT = 90  # seconds to wait at sync points


def drop_group(group, culprit):
    group.dropped = True
    group.dropped_by = culprit.name
    for p in group.players:
        if p.name != culprit.name:
            with p as pp:
                move_to_page(pp, Dropped)
```

`drop_group` does three things: marks the group, records who caused the drop, and moves every *other* player to the Dropped page. The `with p as pp:` [context manager](../building/data.md) is required here because you are mutating a player object from outside that player’s own page method.

!!! warning "Guard against double-dropping"
    Multiple dropout vectors can fire for the same group (e.g., a browser disconnect triggers `watch_for_dropout` at the same moment a page timeout fires). Always check `if not group.get("dropped")` before calling `drop_group`.

### Registering watchers in after_grouping

Register `watch_for_dropout` in `after_grouping`, not `new_player`, because the handler needs access to the group. When iterating `group.players` inside `after_grouping`, wrap each player in a context manager:

```python
class GroupPlease(GroupCreatingWait):
    group_size = 2

    @classmethod
    def after_grouping(page, group):
        group.dropped = False
        for player in group.players:
            player.timed_out = False

            with player:
                watch_for_dropout(player, handle_dropout)
```

The `with player:` block is needed because `after_grouping` receives the group, and iterating `group.players` yields player objects that require the context manager for uproot to track their mutations properly.

### The dropout handler

The handler fires when a participant disconnects. It marks the player as timed out, drops the group if it has not been dropped already, and moves the disconnected player to the end:

```python
async def handle_dropout(player):
    player.timed_out = True
    group = player.group
    if group is not None and not group.get("dropped"):
        drop_group(group, player)
    move_to_end(player)
```

### Page timeouts on decision pages

Add a [timeout](timeouts.md) to every decision page. When it expires, `timeout_reached` drops the group:

```python
class Dilemma(Page):
    fields = dict(
        cooperate=RadioField(
            label="Do you wish to cooperate?",
            choices=[(True, "Yes"), (False, "No")],
        ),
    )

    @classmethod
    def timeout(page, player):
        return C.TIMEOUT

    @classmethod
    def timeout_reached(page, player):
        player.timed_out = True
        if not player.group.get("dropped"):
            drop_group(player.group, player)

    @classmethod
    def before_once(page, player):
        if player.group.get("dropped"):
            move_to_page(player, Dropped)
```

The `before_once` guard at the bottom is equally important: If the group was already dropped (because the *other* player timed out or disconnected), this player should not see the decision page at all. Instead, they get redirected to `Dropped` immediately.

!!! tip
    If you have many decision pages, you can avoid repeating these three methods on each one. See [Reducing repetition with a mixin class](#appendix-reducing-repetition-with-a-mixin-class) at the end of this page.

### Sync timeout

A `SynchronizingWait` page can also time out. This covers the case where one player submits their decision but the other never arrives:

```python
class Sync(SynchronizingWait):
    @classmethod
    def timeout(page, player):
        return C.SYNC_TIMEOUT

    @classmethod
    def timeout_reached(page, player):
        if not player.group.get("dropped"):
            player.group.dropped = True
            player.group.dropped_by = "sync_timeout"

    @classmethod
    def all_here(page, group):
        if group.get("dropped"):
            return
        for player in group.players:
            # ... compute and assign payoffs ...
```

The guard in `all_here` prevents payoff calculation for dropped groups.

### The Dropped page

Create a terminal page that tells participants what happened. Distinguish between the player who timed out and their partner:

```html+jinja
{% extends "Base.html" %}

{% block title %}Time expired{% endblock title %}

{% block main %}
{% if player.timed_out %}
<p>You did not make a choice in time. Your pair has been removed from this round.</p>
{% else %}
<p>Your partner did not make a choice in time. Your pair has been removed from this round.</p>
{% endif %}
{% endblock main %}
```

In your Python code, the Dropped page moves the player to the end after they see the message:

```python
class Dropped(Page):
    @classmethod
    def after_once(page, player):
        move_to_end(player)
```

Add Dropped to the end of `page_order`:

```python
page_order = [
    GroupPlease,
    Dilemma,
    Sync,
    Results,
    Dropped,
]
```

### Guarding downstream pages

Every page after grouping should check the drop flag and redirect. Add a `before_once` guard to your Results page (and any other post-sync page). (If you have many such pages, see the [mixin appendix](#appendix-reducing-repetition-with-a-mixin-class).)

```python
class Results(Page):
    @classmethod
    def before_once(page, player):
        if player.group.get("dropped"):
            move_to_page(player, Dropped)
```

### Excluding dropped groups from data

If your experiment uses a `digest` function, skip dropped groups so they do not contaminate the summary:

```python
def digest(session):
    dropped_pairs = 0

    for group in session.groups(app=__name__):
        if group.get("dropped"):
            dropped_pairs += 1
            continue

        # ... normal payoff analysis ...

    return {
        # ...
        "dropped_pairs": dropped_pairs,
    }
```

If your experiment uses a `pipeline` function, include `timed_out` and `dropped` so you can filter in downstream analysis:

```python
def pipeline(session):
    rows = []
    for group in session.groups(app=__name__):
        for player in group.players:
            player_data = player.within(app=__name__)
            rows.append({
                # ... other fields ...
                "timed_out": player_data.get("timed_out"),
                "dropped": group.get("dropped"),
            })
    return rows
```

### Showing dropout counts in the admin digest

If your experiment uses an `AdminDigest.html` template, display a warning when groups were dropped:

```html+jinja
{% if dropped_pairs > 0 %}
<div class="alert alert-warning mb-3">
    {{ dropped_pairs }} pair{{ "s" if dropped_pairs != 1 }} dropped due to timeout.
</div>
{% endif %}
```

## Adjusting tolerance

Lower the tolerance for fast-paced experiments where delays are critical:

```python
watch_for_dropout(player, handle_dropout, tolerance=10.0)
```

Increase it for experiments where participants may be reading long instructions:

```python
watch_for_dropout(player, handle_dropout, tolerance=120.0)
```

## Checking dropout status in templates

```html+jinja
{% if player.dropout %}
<p>This player has been marked as a dropout.</p>
{% endif %}
```

## Summary

| Feature | Purpose |
|---------|---------|
| `watch_for_dropout(player, handler, tolerance=30.0)` | Monitor a player for disconnection |
| `move_to_end(player)` | Move player past all remaining pages |
| `move_to_page(player, PageClass)` | Redirect a player to a specific page |
| `mark_dropout(pid)` | Manually mark a player as dropout |
| `player._uproot_dropout` | Internal dropout flag |
| Admin: Mark as dropout | Manual dropout from admin interface |
| `group.dropped` | Group-level flag for tracking dropped groups |
| `with p as pp:` / `with player:` | Context manager for cross-player mutations |
| `group.get("dropped")` | Safe check that returns `None` if not set |
| `before_once` guard | Redirect dropped players away from normal pages |

---

## Appendix: reducing repetition with a mixin class

!!! note "Optional—for readers comfortable with Python classes"
    This section shows a convenience pattern for experiments with many decision pages. It is not required. If you only have one or two decision pages, adding the methods directly (as shown above) is simpler and perfectly fine.

In the group dropout pattern above, every decision page needs the same three methods: `timeout`, `timeout_reached`, and `before_once`. If your experiment has several decision pages, repeating those methods on each one gets tedious. Python lets you factor them out into a **[mixin class](https://docs.python.org/3/tutorial/classes.html#multiple-inheritance)**. This is a small class that bundles reusable methods and can be combined with `Page` (or any other page type) via [multiple inheritance](https://realpython.com/inheritance-composition-python/#mixing-features-with-mixin-classes).

### Defining the mixin

```python
class DroppableMixin:
    """Adds timeout + dropout guard to any page."""

    @classmethod
    def timeout(page, player):
        return C.TIMEOUT

    @classmethod
    def timeout_reached(page, player):
        player.timed_out = True
        if not player.group.get("dropped"):
            drop_group(player.group, player)

    @classmethod
    def before_once(page, player):
        if player.group.get("dropped"):
            move_to_page(player, Dropped)
```

### Using the mixin

Place `DroppableMixin` *before* `Page` in the class definition. Python checks classes left to right, so methods from `DroppableMixin` take precedence over defaults in `Page`:

```python
class Dilemma(DroppableMixin, Page):
    fields = dict(
        cooperate=RadioField(
            label="Do you wish to cooperate?",
            choices=[(True, "Yes"), (False, "No")],
        ),
    )


class Negotiation(DroppableMixin, Page):
    fields = dict(
        offer=IntegerField(label="Your offer", min=0, max=100),
    )


class Results(DroppableMixin, Page):
    @classmethod
    def templatevars(page, player):
        return dict(payoff=player.payoff)
```

Each page now inherits the timeout and dropout guard automatically. You still define `fields`, `templatevars`, and any other page-specific methods as usual; they sit alongside the inherited ones without conflict.

### Overriding a single method

If one page needs a different timeout, override just that method. The other two (`timeout_reached` and `before_once`) are still inherited from the mixin:

```python
class LongDecision(DroppableMixin, Page):
    @classmethod
    def timeout(page, player):
        return 120  # more time for this page
```

### Pages that only need the guard

Some pages (like `Results`) do not need a timeout—they have no form to submit. The mixin still works: `timeout` returning a value on a page without fields is harmless. But if you prefer, you can skip the mixin and add just the guard directly:

```python
class Results(Page):
    @classmethod
    def before_once(page, player):
        if player.group.get("dropped"):
            move_to_page(player, Dropped)
```

Either approach is fine. The mixin is most valuable when you have many decision pages that all share the same timeout and dropout logic.
