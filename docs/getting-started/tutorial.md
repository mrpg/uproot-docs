# Your first experiment

This tutorial walks you through building a complete prisoner's dilemma experiment from scratch. By the end, you'll understand how uproot pages, forms, groups, and synchronization work together.

## What we're building

A two-player prisoner's dilemma where participants are paired, each choose to cooperate or defect, and then see the outcome. The payoff matrix:

| | Partner cooperates | Partner defects |
|--|--|--|
| **You cooperate** | 10 | 0 |
| **You defect** | 15 | 3 |

## 1. Create a project

If you haven't already, create a new uproot project:

```console
uv run --with 'uproot-science @ git+https://github.com/mrpg/uproot.git@main' uproot setup my_project
cd my_project
```

## 2. Create the app

Create a new app for the experiment:

```console
uv run uproot new prisoners_dilemma
```

This creates a `prisoners_dilemma/` directory with an `__init__.py` and a starter template.

## 3. Register the config

Open `main.py` and add a config that loads your app:

```python
load_config(uproot_server, config="prisoners_dilemma", apps=["prisoners_dilemma"])
```

## 4. Define the app

Replace the contents of `prisoners_dilemma/__init__.py` with:

```python
from uproot.fields import *
from uproot.smithereens import *

DESCRIPTION = "Prisoner's dilemma"
SUGGESTED_MULTIPLE = 2


class C:
    PAYOFF_MATRIX = {
        (True, True): 10,
        (True, False): 0,
        (False, True): 15,
        (False, False): 3,
    }
```

`DESCRIPTION` shows up in the admin interface. `SUGGESTED_MULTIPLE` tells the admin that sessions should have a multiple of 2 players. `C` holds constants accessible in templates.

### Group formation

Add a wait page that pairs participants:

```python
class GroupPlease(GroupCreatingWait):
    group_size = 2
```

When a participant reaches this page, they wait until another participant arrives. Then both are grouped together and advance.

### The decision page

Add a page where participants choose to cooperate or defect:

```python
class Dilemma(Page):
    fields = dict(
        cooperate=RadioField(
            label="Do you wish to cooperate?",
            choices=[(True, "Yes"), (False, "No")],
        ),
    )
```

The `fields` dictionary defines the form. After submission, the choice is stored as `player.cooperate`.

### Synchronization

Add a wait page so both players' decisions are in before showing results:

```python
class Sync(SynchronizingWait):
    pass
```

### The results page

Add an empty results page (the template will handle display):

```python
class Results(Page):
    pass
```

### PlayerContext for computed values

Add a `Context` class to compute payoffs without writing a `templatevars` method:

```python
class Context(PlayerContext):
    @property
    def payoff(self):
        return C.PAYOFF_MATRIX[
            self.player.cooperate,
            self.player.other_in_group.cooperate,
        ]
```

This makes `player.context.payoff` available in templates.

### Page order

Define the sequence:

```python
page_order = [
    GroupPlease,
    Dilemma,
    Sync,
    Results,
]
```

## 5. Create the templates

### Dilemma.html

Create `prisoners_dilemma/Dilemma.html`:

```html+jinja
{% extends "Base.html" %}

{% block title %}
Dilemma
{% endblock title %}

{% block main %}

{{ fields() }}

{% endblock main %}
```

The `{{ fields() }}` call renders all form fields defined on the page.

### Results.html

Create `prisoners_dilemma/Results.html`:

```html+jinja
{% extends "Base.html" %}

{% block title %}
Results
{% endblock title %}

{% block main %}

{% if player.cooperate %}
<p>You cooperated.</p>
{% else %}
<p>You did not cooperate.</p>
{% endif %}

{% if player.other_in_group.cooperate %}
<p>Your partner cooperated.</p>
{% else %}
<p>Your partner did not cooperate.</p>
{% endif %}

<p>Your payoff is <b>{{ player.context.payoff }}</b>.</p>

{% endblock main %}
```

Templates have access to `player`, `C`, and `player.context` automatically.

## 6. Run the experiment

Start the server:

```console
uv run uproot run
```

Open the admin at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) and create a new session:

1. Select the **prisoners_dilemma** config
2. Set **2 players**
3. Click **Create**

Open the two player links in separate browser tabs. Both players will wait at the grouping page until the other arrives. After making their choices and submitting, they wait at the sync page until both have decided. Then they see the results.

## The complete code

```python
from uproot.fields import *
from uproot.smithereens import *

DESCRIPTION = "Prisoner's dilemma"
SUGGESTED_MULTIPLE = 2


class C:
    PAYOFF_MATRIX = {
        (True, True): 10,
        (True, False): 0,
        (False, True): 15,
        (False, False): 3,
    }


class Context(PlayerContext):
    @property
    def payoff(self):
        return C.PAYOFF_MATRIX[
            self.player.cooperate,
            self.player.other_in_group.cooperate,
        ]


class GroupPlease(GroupCreatingWait):
    group_size = 2


class Dilemma(Page):
    fields = dict(
        cooperate=RadioField(
            label="Do you wish to cooperate?",
            choices=[(True, "Yes"), (False, "No")],
        ),
    )


class Sync(SynchronizingWait):
    pass


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

## What's next?

- **[Project structure](project-structure.md)** — Understand the files in your project
- **[Pages and templates](../building/pages.md)** — Learn about page lifecycle methods
- **[Collecting data with forms](../building/forms.md)** — Explore all available field types
- **[Grouping participants](../multiplayer/groups.md)** — More on multiplayer experiments
