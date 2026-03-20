# API reference

This page documents the key functions and classes available when building uproot experiments. All of these are available automatically in app modules via `from uproot.smithereens import *` and `from uproot.fields import *`.

## Page types

### Page

The standard page type. Displays a template and optionally collects form data.

```python
class MyPage(Page):
    fields = dict(name=StringField(label="Your name"))

    @classmethod
    def templatevars(page, player):
        return dict(greeting="Hello")
```

See [Page methods](page-methods.md) for all available methods.

### NoshowPage

A page that runs logic without displaying anything to the participant.

```python
class Calculate(NoshowPage):
    @classmethod
    def after_always_once(page, player):
        player.payoff = player.correct * 10
```

### GroupCreatingWait

A wait page that forms groups of participants.

```python
class GroupPlease(GroupCreatingWait):
    group_size = 2

    @classmethod
    def after_grouping(page, group):
        for player, role in zip(group.players, ["proposer", "responder"]):
            player.role = role
```

### SynchronizingWait

A wait page that synchronizes group or session members.

```python
class Sync(SynchronizingWait):
    @classmethod
    def all_here(page, group):
        for player in group.players:
            set_payoff(player)
```

Set `synchronize = "session"` to synchronize across the entire session.

## SmoothOperators

### Random

Shuffles pages into a random order per participant.

```python
page_order = [Random(TaskA, TaskB, TaskC)]
```

### Bracket

Groups pages as an atomic unit within `Random`.

```python
page_order = [Random(Bracket(Intro1, Task1), Bracket(Intro2, Task2))]
```

### Rounds

Repeats pages a fixed number of times. Sets `player.round` (1-indexed).

```python
page_order = [Rounds(Decision, Feedback, n=5)]
```

### Repeat

Repeats pages indefinitely until `player.add_round = False`.

```python
page_order = [Repeat(Trial, Check), Done]
```

### Between

Randomly selects one option per participant. Records selection in `player.between_showed`.

```python
page_order = [Between(Treatment, Control)]
```

## PlayerContext

Base class for computed properties available in templates as `player.context.*`.

```python
class Context(PlayerContext):
    @property
    def earnings(self):
        return self.player.payoff * C.EXCHANGE_RATE
```

## Real-time functions

### notify

Send data from one player to one or more recipients.

```python
notify(sender, recipients, data, event="EventName")
```

| Parameter | Description |
|-----------|-------------|
| `sender` | The sending player (determines page context) |
| `recipients` | Player, `StorageBunch`, or list of players |
| `data` | Any JSON-serializable data |
| `event` | Custom event name (default: `"_uproot_Received"`) |

### send_to

Send data to one or more players without a sender context.

```python
send_to(recipients, data, event="EventName")
```

### send_to_one

Send data to a single player.

```python
send_to_one(player, data, event="EventName")
```

### reload

Force a player's browser to reload the current page.

```python
reload(player)
```

### move_to_page

Move a player to a specific page.

```python
move_to_page(player, TargetPage, reload_=True)
```

### move_to_end

Move a player past all remaining pages.

```python
move_to_end(player, reload_=True)
```

## Dropout functions

### watch_for_dropout

Monitor a player for disconnection and call a handler when they go offline.

```python
watch_for_dropout(player, handler, tolerance=30.0)
```

### mark_dropout

Manually mark a player as a dropout.

```python
mark_dropout(player_pid)
```

## Group functions

### create_group

Create a group from a list of players.

```python
gid = create_group(session, [player1, player2], gname="custom_name", overwrite=False)
```

### create_groups

Create multiple groups at once.

```python
gids = create_groups(session, [[p1, p2], [p3, p4]])
```

## The @live decorator

Makes a page method callable from JavaScript via WebSocket.

```python
class MyPage(Page):
    @live
    async def my_method(page, player, arg: str):
        return {"result": arg.upper()}
```

Called from JavaScript:

```javascript
uproot.invoke("my_method", "hello").then(data => console.log(data.result));
```

## Utility functions

### cu

Create a `Decimal` from a string. Shorthand for `Decimal(value)`.

```python
endowment = cu("10.00")
```

### safe

Mark a string as HTML-safe (won't be escaped in templates).

```python
label=StringField(label=safe("Enter a value <b>in euros</b>"))
```

### data_uri

Convert binary data to a data URI string for embedding in HTML.

```python
player.image_uri = data_uri(image_bytes, "image/png")
```

## Identifier types

| Type | Description |
|------|-------------|
| `PlayerIdentifier` | Uniquely identifies a player |
| `SessionIdentifier` | Uniquely identifies a session |
| `GroupIdentifier` | Uniquely identifies a group |
| `ModelIdentifier` | Uniquely identifies a model |

These are used internally and in [custom data models](../advanced/models.md).

## StorageBunch

A collection of storage objects (players, groups) with query methods.

| Method | Description |
|--------|-------------|
| `len(bunch)` | Number of items |
| `bunch[i]` | Get by index |
| `item in bunch` | Membership test |
| `bunch.filter(*.comparisons)` | Filter by field values using `_` |
| `bunch.find_one(**kwargs)` | Find exactly one match |
| `bunch.assign(key, values)` | Set a field on all items |
| `bunch.each(*keys)` | Extract fields from all items |
| `bunch.apply(fn)` | Apply a function to all items |

### Filtering with _

```python
from uproot.smithereens import _

cooperators = group.players.filter(_.cooperate == True)
high_earners = session.players.filter(_.payoff > 10)
```
