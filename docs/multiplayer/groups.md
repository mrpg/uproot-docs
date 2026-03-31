# Grouping participants

Many experiments require participants to interact in pairs or small groups. uproot makes grouping easy with the `GroupCreatingWait` page type, which automatically forms groups as participants arrive.

## Groups are lazy

Groups are only created when participants reach a `GroupCreatingWait` page. uproot does not pre-assign groups when a session starts—grouping happens at runtime as participants arrive. This means the number of groups depends on how many participants actually show up, not on how many were expected.

## Basic group formation

Create a wait page that groups participants by subclassing `GroupCreatingWait` and setting `group_size`:

```python
class WaitForPartner(GroupCreatingWait):
    group_size = 2
```

When participants reach this page, they wait until enough others arrive to form a group. Once a group forms, all members advance to the next page together.

```python
page_order = [
    WaitForPartner,
    GamePage,
    Results,
]
```

:material-github: [See the prisoners_dilemma example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma)

## Assigning roles with after_grouping

Use the `after_grouping` callback to assign roles or initialize group members when the group forms:

```python
class GroupPlease(GroupCreatingWait):
    group_size = 2

    @classmethod
    def after_grouping(page, group):
        for player, is_dictator in zip(group.players, [True, False]):
            player.dictator = is_dictator
```

The callback receives the `group` object and runs exactly once when the group is created. All players in the group can then access their assigned attributes.

:material-github: [See the dictator_game example](https://github.com/mrpg/uproot-examples/tree/master/dictator_game) · [trust_game example](https://github.com/mrpg/uproot-examples/tree/master/trust_game) · [ultimatum_game example](https://github.com/mrpg/uproot-examples/tree/master/ultimatum_game) · [gift_exchange_game example](https://github.com/mrpg/uproot-examples/tree/master/gift_exchange_game)

### Using class attributes for role values

You can define role values as class attributes for cleaner code:

```python
class GroupPlease(GroupCreatingWait):
    group_size = 2
    watch_values = (True, False)

    @classmethod
    def after_grouping(page, group):
        for player, watched in zip(group.players, page.watch_values):
            player.watched = watched
```

:material-github: [See the observed_diary example](https://github.com/mrpg/uproot-examples/tree/master/observed_diary)

## Accessing group members

### group.players

Get all players in a group as a `StorageBunch` using the virtual field:

```python
for player in group.players:
    player.payoff = 10
```

The `StorageBunch` supports iteration, filtering, and bulk operations.

#### Basic iteration

```python
# Sum contributions from all group members
total = sum(p.contribution for p in group.players)

# Unpack directly (e.g. in SynchronizingWait.all_here)
p1, p2 = group.players
```

#### Filtering with `_`

The `_` symbol is a field referent — a placeholder that stands for "each player" in a filter expression. When you write `_.cooperate == True`, uproot builds a comparison object that gets evaluated against each player in the collection.

```python
# Players who cooperated
cooperators = group.players.filter(_.cooperate == True)

# Players with a score above 50
high_scorers = session.players.filter(_.score > 50)

# Combine multiple conditions (all must be true)
eligible = session.players.filter(_.present == True, _.age >= 18)
```

`_` supports all comparison operators: `==`, `!=`, `>`, `>=`, `<`, `<=`. You can also chain attribute access — `_.group.round` refers to each player's group's round field.

!!! note
    `_` builds a lazy comparison, so `_.active` alone (without a comparison operator) tests for truthiness. To check for `False`, write `_.active == False` explicitly.

#### Finding a single player

`find_one()` returns exactly one player matching the criteria. It raises an error if zero or multiple players match.

```python
dictator = group.players.find_one(dictator=True)
leader = group.players.find_one(first_mover=True)
```

#### Extracting values with `each`

`each()` collects a field from every player into a list:

```python
# Get all contributions as a list
contributions = group.players.each("contribution")
# → [10, 20, 15]

# Multiple fields return named tuples
data = group.players.each("name", "score", simplify=False)
# → [data(name='Alice', score=10), data(name='Bob', score=20)]
```

#### Bulk assignment with `assign`

`assign()` sets a field on every player from an iterable:

```python
group.players.assign("role", ["buyer", "seller"])
```

#### Running a function on all players with `apply`

`apply()` calls a function once per player:

```python
group.players.apply(set_payoff)
```

See [Synchronizing progress](synchronization.md#using-apply-for-bulk-operations) for a full example.

### player.other_in_group

For two-person groups, access the other player via the virtual field:

```python
other = player.other_in_group

if player.cooperate and other.cooperate:
    player.payoff = 10
```

Raises an error if the group doesn't have exactly two members.

:material-github: [See the prisoners_dilemma example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma) · [twobytwo example](https://github.com/mrpg/uproot-examples/tree/master/twobytwo)

### player.others_in_group

For groups of any size, get all other members (excluding the current player):

```python
for other in player.others_in_group:
    notify(player, other, "Hello!")
```

## Group-level data storage

Access the shared group storage with `player.group`:

```python
class Calculate(SynchronizingWait):
    @classmethod
    def all_here(page, group):
        # Store a value at the group level
        group.total_contribution = sum(p.contribution for p in group.players)
```

In templates, access group data:

```html+jinja
<p>Your group contributed {{ player.group.total_contribution }} in total.</p>
```

## Larger groups

For experiments with more than two players per group, simply increase `group_size`:

```python
class GroupPlease(GroupCreatingWait):
    group_size = 3
```

Use the same patterns for accessing members:

```python
class Sync(SynchronizingWait):
    @classmethod
    def all_here(page, group):
        total = sum(p.contribution for p in group.players)

        for player in group.players:
            player.payoff = ENDOWMENT - player.contribution + MPCR * total
```

:material-github: [See the public_goods_game example](https://github.com/mrpg/uproot-examples/tree/master/public_goods_game) · [beauty_contest example](https://github.com/mrpg/uproot-examples/tree/master/beauty_contest) · [minimum_effort_game example](https://github.com/mrpg/uproot-examples/tree/master/minimum_effort_game)

## Manual group creation

For custom matching logic, you can create groups programmatically using `create_group()` and `create_groups()` instead of `GroupCreatingWait`. This is useful when you need to:

- Match participants based on survey responses
- Form groups of different sizes
- Sort or balance groups by some criteria

### Basic manual grouping

Use `SynchronizingWait` to wait for all participants, then create groups in the `all_here` callback:

```python
class WaitForEveryone(SynchronizingWait):
    synchronize = "session"

    @classmethod
    def all_here(page, session):
        # Get all players and sort alphabetically by name
        all_players = sorted(session.players, key=lambda p: p.name)

        if len(all_players) == 1:
            # Only one player
            create_group(session, all_players)
        else:
            # Split into two groups of roughly equal size
            mid = len(all_players) // 2
            group_a = all_players[:mid]
            group_b = all_players[mid:]

            create_groups(session, [group_a, group_b])


class ShowGroup(Page):
    @classmethod
    def templatevars(page, player):
        group_members = sorted(player.group.players, key=lambda p: p.name)
        return dict(
            group_name=player.group.name,
            group_members=group_members,
        )


page_order = [
    WaitForEveryone,
    ShowGroup,
]
```

:material-github: [See the grouping_test example](https://github.com/mrpg/uproot-examples/tree/master/grouping_test) · [grouping_test_arbitrary_size example](https://github.com/mrpg/uproot-examples/tree/master/grouping_test_arbitrary_size) · [grouping_test_one_spare example](https://github.com/mrpg/uproot-examples/tree/master/grouping_test_one_spare) · [grouping_via_GroupCreatingWait_and_move_to_page example](https://github.com/mrpg/uproot-examples/tree/master/grouping_via_GroupCreatingWait_and_move_to_page)

### create_group()

Creates a single group from a list of players:

```python
# Create a group from specific players
gid = create_group(session, [player1, player2])

# With a custom group name
gid = create_group(session, members, gname="custom_name")

# Allow reassigning players already in groups
gid = create_group(session, members, overwrite=True)
```

### create_groups()

Creates multiple groups at once:

```python
# Create pairs from a list of players
all_players = list(session.players)
pairs = [[all_players[i], all_players[i+1]] for i in range(0, len(all_players), 2)]
gids = create_groups(session, pairs)
```

### Grouping by attribute

Match participants based on their responses:

```python
class WaitAndMatch(SynchronizingWait):
    synchronize = "session"

    @classmethod
    def all_here(page, session):
        # Separate players by their preference
        prefer_a = [p for p in session.players if p.preference == "A"]
        prefer_b = [p for p in session.players if p.preference == "B"]

        # Match players with different preferences
        for p1, p2 in zip(prefer_a, prefer_b):
            create_group(session, [p1, p2])
```

## Complete example: prisoner's dilemma

Here's a complete two-player game showing group formation, decision collection, and payoff calculation:

```python
class GroupPlease(GroupCreatingWait):
    group_size = 2


class Dilemma(Page):
    fields = dict(
        cooperate=RadioField(
            label="Do you wish to cooperate?",
            choices=[(True, "Yes"), (False, "No")],
        ),
    )


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


class Results(Page):
    pass


page_order = [
    GroupPlease,
    Dilemma,
    Sync,
    Results,
]
```

:material-github: [See the full prisoners_dilemma example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma)

## Summary

| | Purpose |
|--|---------|
| `GroupCreatingWait` | Wait page that forms groups automatically |
| `group_size` | Number of players per group |
| `after_grouping(page, group)` | Callback when group forms |
| `group.players` | All players in a group |
| `player.other_in_group` | The other player (2-person groups) |
| `player.others_in_group` | All other players in the group |
| `session.players` | All players in a session |
| `player.group` | Access group-level storage |
| `create_group()` | Programmatically create a group |
