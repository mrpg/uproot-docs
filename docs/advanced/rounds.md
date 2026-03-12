# Rounds and repetition

Repeat pages multiple times using `Rounds` or `Repeat`.

## Quick example

```python
page_order = [
    Instructions,
    Rounds(
        Decision,
        Feedback,
        n=5,
    ),
    Results,
]
```

Participants see `Decision` → `Feedback` five times, then `Results`.

Access the current round (1-indexed) with `player.round`:

```html+jinja
<p>Round {{ player.round }} of 5</p>
```

## Repeat until stopped

Use `Repeat` for indefinite repetition controlled by `player.add_round`:

```python
page_order = [
    Repeat(
        Trial,
        Check,
    ),
    Done,
]

class Check(Page):
    @classmethod
    def before_next(page, player):
        if player.score >= 100:
            player.add_round = False  # Stop, go to Done
        else:
            player.add_round = True   # Continue repeating
```

## Learn more

See [SmoothOperators](../building/operators.md#rounds) for complete documentation including:

- Dynamic round counts
- Rounds with multiplayer groups
- Combining rounds with randomization

:material-github: [See the rounds example](https://github.com/mrpg/uproot-examples/tree/master/rounds)
