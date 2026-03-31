# Pages and templates

Pages are the building blocks of uproot experiments. Each page represents a screen that participants see—instructions, questions, feedback, or results. Pages are defined as Python classes and rendered using HTML templates.

## Defining a page

A page is a class that inherits from `Page`:

```python
class Welcome(Page):
    pass
```

This minimal page displays the template `Welcome.html` from your app's templates folder. Every page needs a corresponding template file.

### The page_order list

The `page_order` list defines which pages participants see and in what sequence:

```python
page_order = [
    Welcome,
    Instructions,
    Task,
    Results,
]
```

Participants progress through pages in order. You can use [SmoothOperators](../building/operators.md) to randomize, repeat, or conditionally select pages.

`page_order` can also be a callable that takes `player` as a keyword argument, letting you build the sequence dynamically per participant:

```python
def page_order(player):
    pages = [Instructions, Task]
    if player.in_treatment:
        pages.append(TreatmentPage)
    pages.append(Results)
    return pages
```

## Templates

Templates are HTML files that define what participants see. uproot uses [Jinja2](https://jinja.palletsprojects.com/) for templating.

### Template naming and location

By default, uproot looks for a template matching the page class name:

```
my_app/
├── __init__.py      # Contains class Welcome(Page)
└── Welcome.html     # Template for Welcome page
```

To use a custom template path:

```python
class Welcome(Page):
    template = "Page0.html"
```

### Basic template structure

A typical template extends the base layout and defines content:

```html+jinja
{% extends "Base.html" %}


{% block main %}
<h1>Welcome to the experiment</h1>
<p>Thank you for participating.</p>
{% endblock %}
```

The `Base.html` base template provides the form wrapper, navigation buttons, and styling. Your content goes in the `main` block.

### Adding a form

To collect data, include form fields in your template:

```html+jinja
{% extends "Base.html" %}

{% block main %}
<h1>Your decision</h1>

{{ form.amount.label }}
{{ form.amount }}

{% endblock %}
```

See [Collecting data with forms](forms.md) for details on defining form fields.

## Passing data to templates

### The templatevars method

Use the `templatevars` method to pass data from Python to your template:

```python
class Results(Page):
    @classmethod
    def templatevars(page, player):
        return dict(
            earnings=player.payoff,
            partner_choice=player.other_in_group.choice,
        )
```

Then use these variables in your template:

```html+jinja
{% extends "Base.html" %}

{% block main %}
<h1>Results</h1>
<p>You earned {{ earnings }} points.</p>
<p>Your partner chose: {{ partner_choice }}</p>
{% endblock %}
```

The `templatevars` method receives `page` (the page class) and `player` (the current participant's data).

### The PlayerContext class

An alternative, more Pythonic approach is to define a `Context` class in your app that inherits from `PlayerContext`. Its properties become accessible in templates as `player.context.<property>`:

```python
class Context(PlayerContext):
    @property
    def earnings(self):
        return self.player.payoff

    @property
    def partner_choice(self):
        return self.player.other_in_group.choice
```

Access these in templates:

```html+jinja
<p>You earned {{ player.context.earnings }} points.</p>
<p>Your partner chose: {{ player.context.partner_choice }}</p>
```

`PlayerContext` is particularly useful for computed values you want to reuse across multiple pages without writing `templatevars` on each one. The `self.player` attribute gives you access to the current player.

:material-github: [See PlayerContext in the prisoners_dilemma example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma) · [bertrand example](https://github.com/mrpg/uproot-examples/tree/master/bertrand)

## Built-in template variables

Every template has access to these variables:

| Variable | Description |
|----------|-------------|
| `player` | The current participant's data |
| `form` | The form instance (if the page has fields) |
| `page` | The page class |
| `C` | Constants defined in your app's `C` class |
| `session` | The current session |
| `_("text")` | Translation function for internationalization |

### Accessing player data

```html+jinja
<p>Your name: {{ player.name }}</p>
<p>Current round: {{ player.round }}</p>
```

### Using constants

Define constants in your app:

```python
class C:
    ENDOWMENT = 100
    EXCHANGE_RATE = 0.10
```

Use them in templates:

```html+jinja
<p>You start with {{ C.ENDOWMENT }} points.</p>
<p>Each point is worth ${{ C.EXCHANGE_RATE }}.</p>
```

## Static files

### App-specific static files

Place static files (images, CSS, JavaScript) in a `static/` folder within your app:

```
my_app/
├── __init__.py
├── Welcome.html
└── static/
    ├── diagram.png
    └── custom.css
```

Reference them using `appstatic()`:

```html+jinja
<img src="{{ appstatic('diagram.png') }}" alt="Diagram">
<link rel="stylesheet" href="{{ appstatic('custom.css') }}">
```

### Project-wide static files

For files shared across apps, use a project-level static folder and `projectstatic()`.

## Conditional page display

Use the `show` method to conditionally display pages:

```python
class BonusRound(Page):
    @classmethod
    def show(page, player):
        return player.score >= 80  # Only show if score is high enough
```

Pages where `show` returns `False` are skipped automatically.

### Role-based pages

A common pattern for multiplayer experiments:

```python
class ProposerDecision(Page):
    @classmethod
    def show(page, player):
        return player.role == "proposer"

class ResponderDecision(Page):
    @classmethod
    def show(page, player):
        return player.role == "responder"
```

## Allowing back navigation

By default, participants can only move forward. To allow going back:

```python
class Survey(Page):
    allow_back = True
```

This adds a "Back" button that lets participants revisit and change previous answers.

!!! note
    Back navigation only re-displays pages—it doesn't undo any data changes or re-run page logic.

## NoshowPage for logic-only pages

Sometimes you need to run code without displaying anything to participants. Use `NoshowPage`:

```python
class CalculatePayoffs(NoshowPage):
    @classmethod
    def after_always_once(page, player):
        player.payoff = player.correct_answers * 10
```

`NoshowPage` runs its lifecycle methods but never renders a template. Use it for:

- Calculating scores or payoffs
- Initializing player data
- Setting up randomization

:material-github: [See NoshowPage in the big5 example](https://github.com/mrpg/uproot-examples/tree/master/big5)

## Page lifecycle methods

Pages have several methods that run at different points:

| Method | When it runs |
|--------|--------------|
| `show` | Before displaying—return `False` to skip the page |
| `templatevars` | Before rendering—return template variables |
| `before_once` | Once per player, before first display |
| `before_always_once` | Before each display |
| `after_once` | Once per player, after first submission |
| `after_always_once` | After each submission |
| `before_next` | Just before advancing to the next page |

### Example: one-time initialization

```python
class Task(Page):
    @classmethod
    def before_once(page, player):
        # Runs once when the player first sees this page
        player.start_time = time()
```

### Example: cleanup after submission

```python
class Task(Page):
    @classmethod
    def after_always_once(page, player):
        # Runs after each submission
        player.attempts += 1
```

See [Page methods reference](../reference/page-methods.md) for the complete list.

## JavaScript variables

To pass data to JavaScript, use the `jsvars` method:

```python
class TradingGame(Page):
    @classmethod
    def jsvars(page, player):
        return dict(
            initial_price=player.price,
            max_trades=C.MAX_TRADES,
        )
```

Access these in your template's JavaScript:

```html+jinja
<script>
const price = _uproot_js.initial_price;
const maxTrades = _uproot_js.max_trades;
</script>
```

## Complete example

Here's a complete page with context, conditional display, and form handling:

```python
class Offer(Page):
    allow_back = True

    fields = dict(
        amount=IntegerField(
            label="How much do you offer?",
            min=0,
            max=100,
        ),
    )

    @classmethod
    def show(page, player):
        return player.role == "proposer"

    @classmethod
    def templatevars(page, player):
        return dict(
            endowment=C.ENDOWMENT,
            partner=player.other_in_group.name,
        )

    @classmethod
    def before_next(page, player):
        player.offer_made = True
```

```html+jinja
{% extends "Base.html" %}

{% block main %}
<h1>Make an offer</h1>

<p>You have {{ endowment }} points to split with {{ partner }}.</p>

{{ form.amount.label }}
{{ form.amount }}

{% endblock %}
```

:material-github: [See complete examples in uproot-examples](https://github.com/mrpg/uproot-examples)
