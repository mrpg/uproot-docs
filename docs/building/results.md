# Displaying results

Results pages show participants their outcomes, payoffs, and other players' choices. uproot uses Jinja2 templates with full access to Python builtins, enabling calculations and logic directly in your templates.

## Basic results display

Create a Results page and pass data via the `templatevars` method:

```python
class Results(Page):
    @classmethod
    def templatevars(page, player):
        return dict(
            other=player.other_in_group,
        )
```

In the template, access player data and context variables:

```html+jinja
{% extends "Base.html" %}

{% block main %}
<p>You chose to {{ "cooperate" if player.cooperate else "defect" }}.</p>
<p>Your partner chose to {{ "cooperate" if other.cooperate else "defect" }}.</p>
<p>Your payoff is <b>{{ player.payoff }}</b>.</p>
{% endblock main %}
```

:material-github: [See the prisoners_dilemma example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma)

## Accessing other players' data

### Two-player groups

Access the other player via the virtual field `player.other_in_group` directly in templates, or pass it explicitly via `templatevars`:

```python
class Results(Page):
    @classmethod
    def templatevars(page, player):
        return dict(other=player.other_in_group)
```

```html+jinja
<p>Your partner sent {{ other.amount }}.</p>
```

:material-github: [See the trust_game example](https://github.com/mrpg/uproot-examples/tree/master/trust_game) · [ultimatum_game example](https://github.com/mrpg/uproot-examples/tree/master/ultimatum_game)

### Larger groups

Pass a list of other players:

```python
class Results(Page):
    @classmethod
    def templatevars(page, player):
        return dict(others=player.others_in_group)
```

```html+jinja
<p>Other guesses:
{% for other in others %}
    {{ other.guess }}{% if not loop.last %}, {% endif %}
{% endfor %}
</p>
```

:material-github: [See the beauty_contest example](https://github.com/mrpg/uproot-examples/tree/master/beauty_contest) · [minimum_effort_game example](https://github.com/mrpg/uproot-examples/tree/master/minimum_effort_game)

## Formatting numbers

### The `to` filter

Format decimal places with the `| to(n)` filter:

```html+jinja
<p>Your score: {{ player.score | to(1) }}</p>      <!-- 7.3 -->
<p>Amount: ${{ player.amount | to(2) }}</p>        <!-- $12.50 -->
<p>Percentage: {{ player.pct | to(0) }}%</p>       <!-- 85% -->
```

:material-github: [See the big5 example](https://github.com/mrpg/uproot-examples/tree/master/big5) · [focal_point example](https://github.com/mrpg/uproot-examples/tree/master/focal_point)

### The `fmtnum` filter

For currency and units with prefix/suffix:

```html+jinja
{{ player.payoff | fmtnum(pre="$", places=2) }}           <!-- $10.50 -->
{{ player.payoff | fmtnum(post=" EUR", places=2) }}       <!-- 10.50 EUR -->
{{ player.change | fmtnum(pre="$", places=2) }}           <!-- −$5.00 (uses minus sign) -->
```

## Calculations in templates

uproot passes all Python builtins to templates. Perform calculations directly:

```html+jinja
<!-- Arithmetic -->
<p>Total: {{ player.claim + other.claim }}</p>
<p>Tripled amount: {{ sent * 3 }}</p>
<p>Share: {{ player.contribution / total * 100 | to(1) }}%</p>

<!-- Comparisons -->
{% if player.claim + other.claim <= 100 %}
<p>The sum is $100 or less.</p>
{% else %}
<p>The sum exceeds $100.</p>
{% endif %}
```

:material-github: [See the focal_point example](https://github.com/mrpg/uproot-examples/tree/master/focal_point)

### Using Python builtins

Call `sum()`, `max()`, `min()`, `len()`, `range()`, `enumerate()`, `zip()`, and other builtins:

```html+jinja
<!-- Sum contributions -->
<p>Group total: {{ sum(p.contribution for p in others) + player.contribution }}</p>

<!-- Find extremes -->
<p>Highest bid: {{ max(p.bid for p in others) }}</p>

<!-- Enumerate items -->
{% for i, item in enumerate(items) %}
<p>{{ i + 1 }}. {{ item }}</p>
{% endfor %}

<!-- Zip lists together -->
{% for option_a, option_b in zip(options_a, options_b) %}
<tr>
    <td>{{ option_a }}</td>
    <td>{{ option_b }}</td>
</tr>
{% endfor %}
```

:material-github: [See the mpl example](https://github.com/mrpg/uproot-examples/tree/master/mpl)

## Conditional display

### Role-based results

Show different content based on player role:

```html+jinja
{% if player.trustor %}
<p>You sent <b>{{ sent }}</b>, which was tripled to {{ tripled }}.</p>
<p>The other player returned <b>{{ returned }}</b> to you.</p>
{% else %}
<p>The other player sent {{ sent }}, tripled to <b>{{ tripled }}</b>.</p>
<p>You returned <b>{{ returned }}</b>.</p>
{% endif %}
```

:material-github: [See the trust_game example](https://github.com/mrpg/uproot-examples/tree/master/trust_game) · [dictator_game example](https://github.com/mrpg/uproot-examples/tree/master/dictator_game)

### Outcome-based messages

```html+jinja
{% if player.winner %}
<p><b>You won!</b></p>
{% else %}
<p>You did not win this round.</p>
{% endif %}
```

:material-github: [See the beauty_contest example](https://github.com/mrpg/uproot-examples/tree/master/beauty_contest)

## History tables

### Using `player.along()`

For repeated games, iterate through all rounds with `player.along()`:

```html+jinja
<table class="table">
    <thead>
        <tr>
            <th>Round</th>
            <th>Your number</th>
        </tr>
    </thead>
    <tbody>
        {% for round, data in player.along("round") %}
        <tr>
            <td>{{ round }}</td>
            <td>{{ data.number }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

The `along("round")` method returns tuples of `(round_number, player_data_for_that_round)`.

:material-github: [See the rounds example](https://github.com/mrpg/uproot-examples/tree/master/rounds)

### Using `player.within()`

Access a specific round's data with `player.within(round=n)`:

```html+jinja
<table class="table">
    <thead>
        <tr>
            <th>Round</th>
            <th>You</th>
            <th>Partner</th>
        </tr>
    </thead>
    <tbody>
        {% for round in rounds_so_far %}
        <tr>
            <td>{{ round }}</td>
            <td>
                {% if player.within(round=round).cooperate %}
                Cooperated
                {% else %}
                Defected
                {% endif %}
            </td>
            <td>
                {% if other.within(round=round).cooperate %}
                Cooperated
                {% else %}
                Defected
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

Pass `rounds_so_far` from `templatevars`:

```python
class Decision(Page):
    @classmethod
    def templatevars(page, player):
        return dict(
            other=player.other_in_group,
            rounds_so_far=range(1, player.round),
        )
```

:material-github: [See the prisoners_dilemma_repeated example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma_repeated)

## Accessing constants

The `C` class is available in templates:

```python
class C:
    ROUNDS = 5
    ENDOWMENT = 100
```

```html+jinja
<p>Round {{ player.round }} of {{ C.ROUNDS }}</p>
<p>You started with {{ C.ENDOWMENT }} points.</p>
```

## Available filters

| Filter | Purpose | Example |
|--------|---------|---------|
| `to(n)` | Format to n decimal places | `{{ x \| to(2) }}` → `3.14` |
| `fmtnum(pre, post, places)` | Format with prefix/suffix | `{{ x \| fmtnum(pre="$") }}` |
| `tojson` | Convert to JSON | `{{ data \| tojson }}` |
| `repr` | Python repr | `{{ x \| repr }}` |

## Summary

| Feature | Purpose |
|---------|---------|
| `templatevars(page, player)` | Pass variables to template |
| `player.other_in_group` | Get partner in 2-player group |
| `player.others_in_group` | Get all other group members |
| `players(group)` | Get all group members (function form) |
| `player.along("round")` | Iterate all rounds |
| `player.within(round=n)` | Access specific round data |
| `{{ expression }}` | Output values |
| `{% if %}...{% endif %}` | Conditional display |
| `{% for %}...{% endfor %}` | Loops |
| Python builtins | `sum()`, `max()`, `range()`, etc. |
