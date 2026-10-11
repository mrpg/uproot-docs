# SmoothOperators

SmoothOperators let you define dynamic page sequences that adapt at runtime. Instead of a fixed list of pages, you can randomize order, repeat sections, or select between alternatives—all declaratively in your `page_order`.

## Random

`Random` shuffles pages into a random order for each participant. This is essential for counterbalancing in within-subjects designs.

```python
page_order = [
    Instructions,
    Random(
        TaskA,
        TaskB,
        TaskC,
    ),
    Results,
]
```

Each participant sees `Instructions` first, then the three tasks in a randomized order, then `Results`.

[:material-github: See the randomize_pages example](https://github.com/mrpg/uproot-examples/tree/master/randomize_pages)

### Keeping pages together with Bracket

Sometimes you want to randomize the order of *groups* of pages while keeping each group’s internal order intact. Use `Bracket` to treat multiple pages as a single unit:

```python
page_order = [
    Random(
        Bracket(Intro1, Task1, Debrief1),  # These three stay together
        Bracket(Intro2, Task2, Debrief2),  # These three stay together
        Bracket(Intro3, Task3, Debrief3),  # These three stay together
    ),
]
```

Participants see all three blocks, but in random order. Within each block, pages appear in their defined sequence.

### Randomizing entire apps

You can randomize the order of entire sub-experiments by unpacking their `page_order` into brackets:

```python
from . import app1, app2, app3

page_order = [
    Random(
        Bracket(*app1.page_order),
        Bracket(*app2.page_order),
        Bracket(*app3.page_order),
    ),
]
```

[:material-github: See the randomize_apps example](https://github.com/mrpg/uproot-examples/tree/master/randomize_apps)

## Rounds

`Rounds` repeats a sequence of pages a fixed number of times, automatically tracking the current round.

```python
page_order = [
    Instructions,
    Rounds(
        Decision,
        Feedback,
        n=5,  # Repeat 5 times
    ),
    FinalResults,
]
```

Participants see `Instructions`, then cycle through `Decision` → `Feedback` five times, then see `FinalResults`.

### Accessing the current round

Inside your pages, access `player.round` to know which round you are in (1-indexed):

```python
class Decision(Page):
    @classmethod
    def templatevars(page, player):
        return dict(
            round_number=player.round,
            rounds_remaining=5 - player.round,
        )
```

```html+jinja
<p>Round {{ round_number }} of 5</p>
```

### Several loops in one app

Most apps have a single `Rounds` (or `Repeat`), and you can skip this section. If one app takes participants through *several* loops—for example, practice rounds followed by paid rounds—give each loop a name with `block=`:

```python
page_order = [
    Instructions,
    Rounds(Decision, Feedback, n=2, block="practice"),
    Rounds(Decision, Feedback, n=10, block="main"),
    FinalResults,
]
```

Each block counts `player.round` from 1, and uproot stores the name of the current block in `player.block`. If an app has several loops and one of them has no block, `uproot run` stops right away with an error. See [Blocks](#blocks) below for the details.

### Dynamic round counts

The number of rounds can come from a constant:

```python
class C:
    NUM_ROUNDS = 10

page_order = [
    Rounds(Trial, n=C.NUM_ROUNDS),
]
```

Or be calculated dynamically:

```python
page_order = [
    Rounds(Response, n=len(C.ITEMS)),  # One round per item
]
```

[:material-github: See the rounds example](https://github.com/mrpg/uproot-examples/tree/master/rounds)

### Rounds with groups

`Rounds` works seamlessly with multiplayer experiments. Combine it with `SynchronizingWait` to create repeated group interactions:

```python
page_order = [
    GroupPlease,
    Rounds(
        Dilemma,
        Sync,
        Results,
        n=C.ROUNDS,
    ),
]
```

[:material-github: See the prisoners_dilemma_repeated example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma_repeated)

## Repeat

`Repeat` repeats a sequence of pages indefinitely until you tell it to stop. Control the repetition by setting `player.add_round` to `True` (continue) or `False` (stop).

```python
page_order = [
    Repeat(
        Trial,
        Feedback,
    ),
    Results,
]
```

### Controlling repetition with player.add_round

Set `player.add_round` in your page logic to control whether the sequence repeats:

```python
class Feedback(Page):
    @classmethod
    def after_once(page, player):
        if player.score >= 100:
            player.add_round = False  # Stop repeating, proceed to Results
        else:
            player.add_round = True   # Continue to next repetition
```

Like `Rounds`, `Repeat` automatically tracks `player.round` so you can display progress or use it in your logic. It also accepts the same optional `block=` argument (see [Blocks](#blocks)).

## Between

`Between` randomly selects exactly one option from multiple alternatives. This is perfect for between-subjects designs where each participant sees only one condition.

```python
page_order = [
    Instructions,
    Between(
        ConditionA,
        ConditionB,
        ConditionC,
    ),
    Results,
]
```

Each participant sees exactly one of the three condition pages.

### Selecting between page groups

Use `Bracket` to select between multi-page sequences:

```python
page_order = [
    Between(
        Bracket(TreatmentIntro, TreatmentTask, TreatmentDebrief),
        Bracket(ControlIntro, ControlTask, ControlDebrief),
    ),
]
```

Each participant experiences either the full treatment sequence or the full control sequence.

### Tracking which condition was shown

The selection is recorded in `player.between_showed`, which you can use for analysis:

```python
class Results(Page):
    @classmethod
    def templatevars(page, player):
        return dict(condition=player.between_showed)
```

## Combining operators

SmoothOperators can be nested to create sophisticated experimental designs.

### Randomized treatments with random task order

```python
page_order = [
    Instructions,
    Between(
        Bracket(TreatmentIntro, Treatment),  # Treatment condition
        Bracket(ControlIntro, Control),      # Control condition
    ),
    Random(
        Task1,
        Task2,
        Task3,
    ),
    Results,
]
```

### Repeated rounds with randomized elements

```python
page_order = [
    Rounds(
        Random(
            StimulusA,
            StimulusB,
        ),
        Response,
        n=10,
    ),
]
```

### Nested operators

You can nest operators to create more complex designs:

```python
page_order = [
    Instructions,
    Random(
        Between(VersionA, VersionB),  # Randomly select one version
        Bracket(Control1, Control2),  # Keep these two together
        StandaloneTask,
    ),
    Results,
]
```

Here, participants see three things in random order: one of two versions (selected via `Between`), a two-page control sequence (kept together via `Bracket`), and a standalone task.

## Blocks

Blocks are optional. You only need them when one app takes participants through more than one `Rounds` or `Repeat`.

The problem they solve: if an app runs two loops and both counted rounds the same way, your data would contain two different “round 1”s, and you could not tell which answer belongs to which. A block gives each loop a name. uproot stores that name in `player.block`, so the app, the block, and the round together identify every round.

### Naming blocks

Pass `block=` to `Rounds` or `Repeat`:

```python
page_order = [
    Rounds(Decision, n=2, block="practice"),
    Rounds(Decision, n=10, block="main"),
]
```

Participants see `Decision` twice with `player.block == "practice"` and `player.round` going 1, 2, then ten more times with `player.block == "main"` and `player.round` going from 1 to 10.

Block names must be valid [Python identifiers](https://docs.python.org/3/reference/lexical_analysis.html#identifiers): letters, digits, and underscores, not starting with a digit (e.g., `"main"` or `"part_2"`, but not `"part 2"`). A loop without `block=` has `player.block == None`.

### Returning to a block

Loops with the *same* block name share one counter. A participant who returns to a block continues where they left off:

```python
page_order = [
    Rounds(Step, n=2, block="red"),   # red rounds 1, 2
    Rounds(Step, n=1, block="blue"),  # blue round 1
    Repeat(Step, block="red"),        # red rounds 3, 4, …
]
```

Counters start afresh in every app, so different apps can reuse the same block names.

[:material-github: See the blocks example](https://github.com/mrpg/uproot-examples/tree/master/blocks)

### When uproot asks for blocks

If participants can go through several `Rounds` or `Repeat` in one app and one of them has no block, `uproot run` stops before the server starts and prints an error like this:

```
ValueError: Constraint violation: App 'myapp' can take participants through several Rounds or Repeat, so each of them needs a block, e.g., block="main". Rounds(Decision) has none. Blocks with the same name continue counting player.round, other blocks start at 1.
```

!!! warning "Page orders defined as functions"
    If your `page_order` is a [function](pages.md#the-page_order-list) instead of a list, uproot cannot check it at startup. The server starts normally, and the check runs only when a participant’s page order is built, right after they join. That participant then sees an “Internal Server Error” page, and the error above appears in the server’s terminal output. Test such apps with a participant before you run a session.

The fix is to add `block=` to every outermost `Rounds` and `Repeat` in that app. A few cases do not count as several loops:

- Loops inside `Between` count once, since each participant sees only one alternative. `Between(Rounds(A, n=3), Rounds(B, n=5))` needs no blocks.
- `Rounds` with `n=0` never runs and is ignored.

`Random(Rounds(A, n=3), Rounds(B, n=3))`, on the other hand, runs both loops and therefore needs a block for each.

### Nested loops

A `Rounds` or `Repeat` placed *inside* another one belongs to the outer loop’s block and cannot name its own. `player.round` keeps counting through every iteration at every level, and `player.round_nested` lists the position at each level—`[2, 1]` means “outer round 2, inner round 1.”

### Leaving an app

When a participant moves on to the next app or reaches the end, uproot removes `player.round`, `player.block`, and `player.round_nested`. Reading `player.round` in a later app that has no loop of its own therefore raises an `AttributeError`. To look back at earlier rounds, use [`player.within()`](results.md#using-playerwithin), for example `player.within(app="game", block="main", round=3)`.

## Summary

| Operator | Purpose | Key parameter |
|----------|---------|---------------|
| `Random` | Shuffle pages randomly | Pages as arguments |
| `Bracket` | Group pages as a unit | Pages as arguments |
| `Rounds` | Repeat pages n times | `n` for count; optional [`block`](#blocks) |
| `Repeat` | Repeat until stopped | `player.add_round` to control; optional [`block`](#blocks) |
| `Between` | Select one alternative | Pages/brackets as arguments |
