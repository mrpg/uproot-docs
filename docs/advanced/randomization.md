# Randomizing pages

Randomize page order using `Random`, `Bracket`, and `Between`.

## Shuffle pages

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

Each participant sees the three tasks in a different random order.

## Keep pages together

Use `Bracket` to randomize groups of pages while keeping each group's internal order:

```python
page_order = [
    Random(
        Bracket(Intro1, Task1),  # These two stay together
        Bracket(Intro2, Task2),  # These two stay together
    ),
]
```

## Between-subjects design

Use `Between` to show each participant only one condition:

```python
page_order = [
    Instructions,
    Between(
        Treatment,
        Control,
    ),
    Survey,
]
```

Each participant sees either `Treatment` or `Control`, never both.

## Learn more

See [SmoothOperators](../building/operators.md#random) for complete documentation including:

- Randomizing entire apps
- Nesting operators
- Tracking which condition was shown

:material-github: [See the randomize_pages example](https://github.com/mrpg/uproot-examples/tree/master/randomize_pages)
