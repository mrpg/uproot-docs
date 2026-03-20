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

The watcher checks every few seconds whether the player's browser is still connected. If the player has been offline for longer than the tolerance period (default: 30 seconds), the handler fires.

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

`move_to_end(player)` advances the player past all remaining pages. If they return, they'll see the end page instead of being stuck on a wait page that blocks other players.

## Marking dropouts manually

From the admin interface, select players and use the **Mark as dropout** action. This sets `player._uproot_dropout = True`.

Programmatically:

```python
from uproot.smithereens import mark_dropout

mark_dropout(player.pid)
```

## Handling dropouts in group experiments

In multiplayer experiments, a dropout can block other group members at synchronization points. Handle this by checking for dropouts in your game logic:

```python
def new_player(player):
    watch_for_dropout(player, handle_dropout)


async def handle_dropout(player):
    player.dropout = True
    move_to_end(player)


class Sync(SynchronizingWait):
    @classmethod
    def all_here(page, group):
        active_players = [p for p in group.players if not p.dropout]

        for player in active_players:
            set_payoff(player)
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
| `mark_dropout(pid)` | Manually mark a player as dropout |
| `player._uproot_dropout` | Internal dropout flag |
| Admin: Mark as dropout | Manual dropout from admin interface |
