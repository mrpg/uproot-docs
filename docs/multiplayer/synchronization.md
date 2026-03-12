# Synchronizing progress

In multiplayer experiments, you often need to wait for all group members to reach a certain point before continuing. The `SynchronizingWait` page type handles this automatically and provides a callback to process all players' data together.

## Basic synchronization

Create a wait page that synchronizes players by subclassing `SynchronizingWait`:

```python
class WaitForAll(SynchronizingWait):
    pass
```

When a participant reaches this page, they wait until all other group members arrive. Once everyone is present, they all advance together.

```python
page_order = [
    GroupPlease,      # Form groups first
    Decision,         # Each player makes a decision
    WaitForAll,       # Wait for all decisions
    Results,          # Show results
]
```

## Processing data with all_here

The `all_here` callback runs exactly once when all group members have arrived. This is where you calculate outcomes based on everyone's choices:

```python
class Sync(SynchronizingWait):
    @classmethod
    def all_here(page, group):
        total = sum(p.contribution for p in group.players)

        for player in group.players:
            player.payoff = ENDOWMENT - player.contribution + MPCR * total
```

The callback receives the `group` object and has access to all players' data.

:material-github: [See the public_goods_game example](https://github.com/mrpg/uproot-examples/tree/master/public_goods_game) · [beauty_contest example](https://github.com/mrpg/uproot-examples/tree/master/beauty_contest) · [minimum_effort_game example](https://github.com/mrpg/uproot-examples/tree/master/minimum_effort_game)

## Calculating payoffs

A common pattern is to calculate payoffs for all players in `all_here`. Here's a complete example using the prisoner's dilemma payoff matrix:

```python
def set_payoff(player):
    other = player.other_in_group

    match player.cooperate, other.cooperate:
        case True, True:
            player.payoff = 10
        case True, False:
            player.payoff = 0
        case False, True:
            player.payoff = 15
        case False, False:
            player.payoff = 3


class Sync(SynchronizingWait):
    @classmethod
    def all_here(page, group):
        for player in group.players:
            set_payoff(player)
```

:material-github: [See the prisoners_dilemma example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma)

### Using apply for bulk operations

You can also use `apply()` to run a function on all players:

```python
class Sync(SynchronizingWait):
    @classmethod
    def set_payoff(page, player):
        other = player.other_in_group

        if player.claim + other.claim <= 100:
            player.payoff = player.claim

    @classmethod
    def all_here(page, group):
        group.players.apply(page.set_payoff)
```

:material-github: [See the focal_point example](https://github.com/mrpg/uproot-examples/tree/master/focal_point)

## Finding specific players

Use `find_one()` to locate players with specific attributes:

```python
class Sync(SynchronizingWait):
    @classmethod
    def all_here(page, group):
        dictator = group.players.find_one(dictator=True)
        recipient = group.players.find_one(dictator=False)

        dictator.payoff = cu(10) - dictator.give
        recipient.payoff = dictator.give
```

:material-github: [See the dictator_game example](https://github.com/mrpg/uproot-examples/tree/master/dictator_game) · [trust_game example](https://github.com/mrpg/uproot-examples/tree/master/trust_game) · [ultimatum_game example](https://github.com/mrpg/uproot-examples/tree/master/ultimatum_game)

## Session-level synchronization

By default, `SynchronizingWait` synchronizes within the group. To synchronize across the entire session instead:

```python
class WaitForSession(SynchronizingWait):
    synchronize = "session"

    @classmethod
    def all_here(page, session):
        # Runs when ALL participants in the session have arrived
        session.total_participants = len(session.players)
```

Note that when `synchronize = "session"`, the callback receives the `session` object instead of `group`.

## Custom synchronization with wait_for

Override the `wait_for` method for custom synchronization logic:

```python
class CustomWait(SynchronizingWait):
    @classmethod
    def wait_for(page, player):
        # Return list of PlayerIdentifiers to wait for
        # Default implementation returns player.group.players
        return player.group.players
```

## Synchronization in repeated games

When using `Rounds`, each round typically needs its own synchronization point:

```python
page_order = [
    GroupPlease,
    Rounds(
        Decision,
        Sync,           # Sync after each round
        RoundResults,
        n=3,
    ),
    FinalResults,
]
```

The `all_here` callback runs once per round, allowing you to calculate round-specific outcomes:

```python
class Sync(SynchronizingWait):
    @classmethod
    def all_here(page, group):
        for player in group.players:
            set_payoff(player)  # Payoff for this round
```

In templates, you can access the current round number:

```html+jinja
<h2>Round {{ player.round }} results</h2>
```

:material-github: [See the prisoners_dilemma_repeated example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma_repeated)

## Accessing historical data in repeated games

Use `player.within()` to access data from specific rounds:

```python
def digest(session):
    for group in session.groups:
        player1 = group.players.find_one(member_id=0)

        for round in range(1, player1.round + 1):
            # Get this player's choice in a specific round
            choice = player1.within(round=round).get("cooperate")
```

:material-github: [See the prisoners_dilemma_repeated example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma_repeated)

## Complete example: public goods game

Here's a complete example showing synchronization with a three-player group:

```python
ENDOWMENT = cu("10")
MPCR = cu("0.5")  # Marginal Per Capita Return


class GroupPlease(GroupCreatingWait):
    group_size = 3


class Contribute(Page):
    fields = dict(
        contribution=DecimalField(
            label="How much do you contribute to the group account?",
            min=0,
            max=ENDOWMENT,
        ),
    )

    @classmethod
    def templatevars(page, player):
        group_size = GroupPlease.group_size
        multiplier = MPCR * group_size

        return dict(
            endowment=ENDOWMENT,
            group_size=group_size,
            multiplier=multiplier,
        )


class Sync(SynchronizingWait):
    @classmethod
    def all_here(page, group):
        total = sum(p.contribution for p in group.players)

        for player in group.players:
            player.payoff = ENDOWMENT - player.contribution + MPCR * total


class Results(Page):
    @classmethod
    def templatevars(page, player):
        total = sum(p.contribution for p in player.group.players)
        return dict(total=total)


page_order = [
    GroupPlease,
    Contribute,
    Sync,
    Results,
]
```

:material-github: [See the full public_goods_game example](https://github.com/mrpg/uproot-examples/tree/master/public_goods_game)

## Detecting presence

In classroom or lab experiments you sometimes need to know which participants are actively present before forming groups or proceeding. The `detect_presence` pattern uses a short time window during which participants must signal that they are there:

```python
from time import time as now


class C:
    DETECTION_PERIOD = 30.0  # seconds


class RaiseHands(Page):
    @classmethod
    def timeout(page, player):
        if player.session.get("detection_period_until") is None:
            player.session.detection_period_until = now() + C.DETECTION_PERIOD
            for p in player.session.players:
                p.present = False
        return player.session.detection_period_until - now()

    @classmethod
    def may_proceed(page, player):
        return now() >= player.session.detection_period_until

    @live
    def set_presence(page, player, new_value: bool):
        player.present = new_value
        return new_value
```

After the page completes, `player.present` tells you whether each participant signalled their presence. You can then use this in `show()`, `all_here()`, or when forming groups.

:material-github: [See the full detect_presence example](https://github.com/mrpg/uproot-examples/tree/master/detect_presence)

## Summary

| Feature | Purpose |
|---------|---------|
| `SynchronizingWait` | Wait page that syncs group members |
| `all_here(page, group)` | Callback when all members arrive |
| `synchronize = "group"` | Sync within group (default) |
| `synchronize = "session"` | Sync entire session |
| `wait_for(page, player)` | Custom sync logic |
| `group.players.find_one()` | Find player by attribute |
| `group.players.apply()` | Run function on all players |
| `player.within(round=n)` | Access data from specific round |
