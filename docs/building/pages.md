# Pages and templates

Pages are the building blocks of uproot experiments. Each page represents a screen that participants see, for instance, instructions, questions, feedback, or results. Pages are defined as Python classes and rendered using HTML or Markdown templates.

## Defining a page

A page is a class that inherits from `Page`:

```python
class Welcome(Page):
    pass
```

This minimal page displays the template `Welcome.html` from your app directory. Every page needs a matching template: `Welcome.html`, or `Welcome.md` if you prefer Markdown (see [Markdown pages](#markdown-pages)).

### The `page_order` list

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

Nested lists are flattened automatically, so you can compose page sequences from reusable building blocks, including SmoothOperators:

```python
def page_order(player):
    warmup = [Instructions, Random(PracticeA, PracticeB)]
    main_task = [Rounds(Decision, Feedback, n=5)]
    return [warmup, main_task, Results]
```

## Templates

Templates define what participants see. Most are HTML files; you can also write [Markdown pages](#markdown-pages). uproot uses [Jinja2](https://jinja.palletsprojects.com/) for templating.

### Template naming and location

By default, uproot looks for a template matching the page class name:

```
my_app/
├── __init__.py      # Contains class Welcome(Page)
└── Welcome.html     # Template for Welcome page (or Welcome.md)
```

To use a custom template path:

```python
class Welcome(Page):
    template = f"{__name__}/Page0.html"
```

Explicit template paths start at the project root, so include the app module name as shown.

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

Available blocks:

| Block | Position |
|-------|----------|
| `title` | Page title (shown in the browser tab and as the heading) |
| `head` | Extra content in `<head>` (CSS, meta tags) |
| `pre_main` | Before the main content, outside the Bootstrap container |
| `main` | Main page content (inside the container) |
| `main_full_width` | After `main`, full viewport width; use this for banners or charts that should break out of the container |
| `main2` | A second container section after `main_full_width` |
| `late` | Extra content at the end of `<body>` (scripts) |

There are also `main2_full_width`, `main3`, `late2`, `footer`, `header_start`, and `header_end` if you need more slots.

### Base template switches

The built-in templates also read a few optional Jinja variables. Set them near the top of a child template when you need to disable part of the default layout:

```html+jinja
{% extends "Base.html" %}
{% set buttons = False %}
{% set disable_connection_lost_modal = True %}
```

| Variable | Default | Effect when set to `True` |
|----------|---------|---------------------------|
| `buttons` | `True` | Set to `False` to hide the default Back/Next buttons |
| `disable_bootstrap` | `False` | Do not load uproot’s bundled Bootstrap CSS and JavaScript |
| `disable_uproot_fonts` | `False` | Do not load uproot’s bundled web fonts |
| `disable_tabular_numbers` | `False` | Do not load the tabular-number font stylesheet |
| `disable_terms` | `False` | Do not load the terms script |
| `disable_auto_start` | `False` | Do not run the default `uproot.init()` and WebSocket startup hook |
| `disable_connection_lost_modal` | `False` | Do not show or enable the connection-lost modal |

For admin templates that extend the built-in admin layout, `disable_navigation = True` hides the admin navigation bar.

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

The `templatevars` method receives `page` (the page class) and `player` (the current participant’s data).

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

[:material-github: See PlayerContext in the prisoners_dilemma example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma) · [bertrand example](https://github.com/mrpg/uproot-examples/tree/master/bertrand)

## Built-in template variables

Every template has access to these variables:

| Variable | Description |
|----------|-------------|
| `player` | The current participant’s data |
| `form` | The form instance (if the page has fields) |
| `page` | The page class |
| `C` | Constants defined in your app’s `C` class |
| `session` | The current session |
| `_("text")` | Translation function for internationalization |

### Accessing player data

```html+jinja
<p>Your name: {{ player.participant_name }}</p>
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

To also use constants in JavaScript (and [Alpine.js](alpinejs.md)), list their names on `C.__export__`:

```python
class C:
    WORD_LENGTH = 5
    DURATION = 120
    __export__ = ["WORD_LENGTH", "DURATION"]
```

uproot copies those values to `window.C`, so `C.WORD_LENGTH` works in scripts. Set `__export__ = ...` (Ellipsis) to export every non-dunder attribute.

[:material-github: See C.__export__ in the encryption_task example](https://github.com/mrpg/uproot-examples/tree/master/encryption_task) · [emoji_sort example](https://github.com/mrpg/uproot-examples/tree/master/emoji_sort)

## Static files

### App-specific static files

Place static files (images, CSS, JavaScript) in an `_static/` folder within your app:

```
my_app/
├── __init__.py
├── Welcome.html
└── _static/
    ├── diagram.png
    └── custom.css
```

Reference them using `appstatic()`:

```html+jinja
<img src="{{ appstatic('diagram.png') }}" alt="Diagram">
<link rel="stylesheet" href="{{ appstatic('custom.css') }}">
```

### Project-wide static files

For files shared across apps, put them in `_static/` at the project root and use `projectstatic()`:

```html+jinja
<script src="{{ projectstatic('shared.js') }}"></script>
```

To inject HTML into every page, add `ProjectHead.html` (inside `<head>`) or `ProjectBody.html` (inside `<body>`) at the project root.

## Markdown pages

If `Welcome.html` is missing, uproot looks for `Welcome.md` instead. Put exactly one level-one heading (`#`) in the file; uproot uses it as the page title and removes it from the main content.

You can still use Jinja. That is, fields, `player`, `C`, and the rest work as usual:

```markdown
# Welcome

Thank you for participating. You start with {{ C.ENDOWMENT }} points.

{{ field(form.consent) }}
```

If the Markdown file name does not match the page class, set its project-root-relative path:

```python
class Welcome(Page):
    template = f"{__name__}/Instructions.md"
```

[:material-github: See the anchoring_markdown example](https://github.com/mrpg/uproot-examples/tree/master/anchoring_markdown)

## Translations

uproot’s built-in interface strings ship in English (`en`), German (`de`), Spanish (`es`), and Japanese (`ja`). Set the default in `main.py`:

```python
upd.LANGUAGE = "de"
```

To choose a language per participant, define `language(player)` in the app. It should return an ISO 639 code:

```python
def language(player):
    return player.session.settings.get("language", "en")
```

In templates, `_("text")` looks up a translation for the current language. Wrap phrases in `{% translate %}...{% endtranslate %}` when you want the same lookup with whitespace collapsed.

To add your own phrases, put YAML files in a directory (one file per language, or one file with all languages) and load them at startup:

```python
import uproot.i18n as i18n

i18n.load("locales/")
```

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

This adds a “Back” button that lets participants revisit and change previous answers.

Set `keep_values = True` to pre-fill the form from values already stored on the player. This is useful when someone returns to a page and should see their previous answers.

!!! note
    Going back re-displays the page but does not undo any data that was
    already saved. Submission hooks like `after_once` do not run again.

## `NoshowPage` for logic-only pages

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

[:material-github: See NoshowPage in the big5 example](https://github.com/mrpg/uproot-examples/tree/master/big5)

## Page lifecycle methods

Pages have several methods that run at different points:

| Method | When it runs |
|--------|--------------|
| `show` | Before displaying; return `False` to skip the page |
| `early` | Earliest hook when entering the page; has the HTTP request |
| `before_always_once` | Once when this page position is reached |
| `before_once` | Once per player, before first display |
| `templatevars` | Before rendering; return template variables |
| `after_once` | Once per player, after first submission |
| `after_always_once` | Once after this page position is submitted |

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
        # Runs after this page position is submitted
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

Access these in your template’s JavaScript:

```html+jinja
<script>
const price = uproot.vars.initial_price;
const maxTrades = uproot.vars.max_trades;
</script>
```

## Complete example

Here is a complete page with context, conditional display, and form handling:

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
    def after_once(page, player):
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

[:material-github: See complete examples in uproot-examples](https://github.com/mrpg/uproot-examples)
