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

:material-github: [See the randomize_pages example](https://github.com/mrpg/uproot-examples/tree/master/randomize_pages)

### Keeping pages together with Bracket

Sometimes you want to randomize the order of *groups* of pages while keeping each group's internal order intact. Use `Bracket` to treat multiple pages as a single unit:

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

:material-github: [See the randomize_apps example](https://github.com/mrpg/uproot-examples/tree/master/randomize_apps)

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

Inside your pages, access `player.round` to know which round you're in (1-indexed):

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

:material-github: [See the rounds example](https://github.com/mrpg/uproot-examples/tree/master/rounds)

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

:material-github: [See the prisoners_dilemma_repeated example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma_repeated)

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
    def before_next(page, player):
        if player.score >= 100:
            player.add_round = False  # Stop repeating, proceed to Results
        else:
            player.add_round = True   # Continue to next repetition
```

Like `Rounds`, `Repeat` automatically tracks `player.round` so you can display progress or use it in your logic.

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

## Summary

| Operator | Purpose | Key parameter |
|----------|---------|---------------|
| `Random` | Shuffle pages randomly | Pages as arguments |
| `Bracket` | Group pages as a unit | Pages as arguments |
| `Rounds` | Repeat pages n times | `n` for count |
| `Repeat` | Repeat until stopped | `player.add_round` to control |
| `Between` | Select one alternative | Pages/brackets as arguments |
