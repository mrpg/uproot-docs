---
description: Step-by-step tutorial that builds a complete two-player prisoner’s dilemma with pages, forms, groups, and synchronization.
---

# Tutorial: A complete experiment

This tutorial walks you through building a complete prisoner’s dilemma experiment from scratch. By the end, you will understand how uproot pages, forms, groups, and synchronization work together.

## What we are building

Two participants are paired. Each of them privately decides whether to cooperate. Then both see what happened and what they earned. In each cell of this payoff matrix, the first amount goes to you and the second to the other participant:

<style>
    .md-typeset__table td {
        font-variant-numeric: tabular-nums !important;
    }
</style>

| | The other participant cooperates | The other participant does not cooperate |
|--|--|--|
| **You cooperate** | $10 / $10 | &numsp;$0 / $15 |
| **You do not cooperate** | $15 / &numsp;$0 | &numsp;$3 / &numsp;$3 |

Every new uproot project already contains this experiment as a sample app called `prisoners_dilemma`. In this tutorial, you build the same app yourself, step by step, under the name `my_dilemma`.

## 1. Create a project

If you have not done so yet, create a new uproot project (see [Installation](installation.md)):

```console
uv run --with uproot-science uproot setup my_project
cd my_project
```

## 2. Create the app

An uproot experiment consists of one or more apps. Each app is a folder with Python code and HTML templates. Create a new, nearly empty app:

```console
uv run uproot new my_dilemma --minimal
```

This creates a `my_dilemma/` folder with three files:

- `__init__.py` holds the app’s Python code;
- `FirstPage.html` is the template of a placeholder page;
- `simulate.js` lets uproot click through the app for you (see [step 7](#7-test-with-simulated-participants)).

You will not need the placeholder page, so delete `FirstPage.html`.

## 3. Register the config

A config is a named sequence of apps that participants go through. Open `main.py` and add a config for your app below the existing `load_config` line:

```python
load_config(uproot_server, config="my_dilemma", apps=["my_dilemma"])
```

## 4. Write the app

Open `my_dilemma/__init__.py`. Keep the comment at the top of the file: its “Third-party dependencies” lines must stay in every uproot app. Also keep the two `import` lines below it. Delete everything else. You will now add the app’s parts one by one.

### Description and constants

```python
DESCRIPTION = "Prisoner's dilemma"
SUGGESTED_MULTIPLE = 2


class C:
    PAYOFF_MATRIX = {
        # (you cooperate, other cooperates): your payoff
        (True, True): 10,
        (True, False): 0,
        (False, True): 15,
        (False, False): 3,
    }
```

`DESCRIPTION` shows up in the admin interface. `SUGGESTED_MULTIPLE` tells the admin that sessions should have a multiple of 2 players. `C` holds constants that you can use both in Python and in templates.

`PAYOFF_MATRIX` is a Python [dictionary](https://docs.python.org/3/tutorial/datastructures.html#dictionaries). Each key is a pair of decisions: `True` for cooperating and `False` for not cooperating. The first decision is always that of the participant who receives the payoff. For example, `(True, False): 0` means: if you cooperate and the other participant does not, you get 0.

### Instructions

```python
class Instructions(Page):
    pass
```

Each class based on `Page` is a page that participants see. `pass` means that the page needs no Python code: it only shows its template, which you will create in [step 5](#5-create-the-templates).

### Group formation

```python
class GroupPlease(GroupCreatingWait):
    group_size = 2
```

`GroupPlease` is a wait page. When a participant reaches it, they wait until another participant arrives. Then both are grouped together and advance.

### The decision page

```python
class Dilemma(Page):
    fields = dict(
        cooperate=RadioField(
            label="Do you wish to cooperate?",
            choices=[(True, "Yes"), (False, "No")],
        ),
    )
```

The `fields` dictionary defines the form. After submission, the choice is saved as `player.cooperate`: `True` for “Yes” and `False` for “No”.

### Payoffs

```python
class Sync(SynchronizingWait):
    @classmethod
    def all_here(page, group: GroupType) -> None:
        for player in group.players:
            player.payoff = C.PAYOFF_MATRIX[
                player.cooperate,
                player.other_in_group.cooperate,
            ]
```

`Sync` is another wait page: each participant waits here until both members of the group have decided. Then uproot runs `all_here` once for the group. It goes through both players, looks up each one’s payoff in `C.PAYOFF_MATRIX`, and saves it as `player.payoff`. `player.other_in_group` is the other member of a two-person group. Because the payoff is saved on `player`, it also ends up in your [data export](../running/export.md).

`@classmethod` marks `all_here` as a [class method](https://docs.python.org/3/library/functions.html#classmethod). uproot page methods are always written this way, with `page` as their first argument. `group: GroupType` and `-> None` are optional [type hints](https://docs.python.org/3/library/typing.html): they say what goes into and comes out of the method, so that tools can check your code.

### The results page

```python
class Results(Page):
    pass
```

Like `Instructions`, the results page only shows its template.

### Page order

```python
page_order = [
    Instructions,
    GroupPlease,
    Dilemma,
    Sync,
    Results,
]
```

`page_order` lists the pages in the order participants go through them. Participants only see the wait pages `GroupPlease` and `Sync` while they have to wait.

## 5. Create the templates

Every page that participants see needs an HTML template with the same name as its class. Wait pages already have one built in. uproot templates use [Jinja](https://jinja.palletsprojects.com/en/stable/templates/): `{{ ... }}` prints a value, and `{% ... %}` runs logic such as `if` and `for`. Every template can access `player` and `C`.

### Instructions.html

Create `my_dilemma/Instructions.html`:

```html+jinja
{% extends "Base.html" %}

{% block title %}
Instructions
{% endblock title %}


{% block main %}

<p>In this study, you will be paired with another participant.</p>

<p>You will each make one private choice: to cooperate or not to cooperate.</p>

<p>There is no opportunity to communicate with the other participant. Neither of you will learn the other’s choice until both decisions have been submitted. Please make your choice on the next page.</p>

<p>The two decisions jointly determine both your payoff and the other participant’s payoff as follows:</p>

<table class="table">
    <thead>
        <tr>
            <th></th>
            <th>The other participant cooperates</th>
            <th>The other participant does not cooperate</th>
        </tr>
    </thead>
    <tbody>
        {% for you in [True, False] %}
        <tr>
            <th>{{ "You cooperate" if you else "You do not cooperate" }}</th>
            {% for other in [True, False] %}
            <td>
                {{ C.PAYOFF_MATRIX[you, other] | fmtnum(pre="$", places=2) }} for you<br>
                {{ C.PAYOFF_MATRIX[other, you] | fmtnum(pre="$", places=2) }} for the other participant
            </td>
            {% endfor %}
        </tr>
        {% endfor %}
    </tbody>
</table>

{% endblock main %}
```

The table goes through both of your possible decisions (`you`) and both of the other participant’s (`other`). Your payoff is `C.PAYOFF_MATRIX[you, other]`. The other participant’s payoff is `C.PAYOFF_MATRIX[other, you]`, because the first decision is always that of the participant who receives the payoff. The [`fmtnum` filter](../building/results.md#the-fmtnum-filter) prints each amount as dollars with two decimal places, for example `$10.00`.

### Dilemma.html

Create `my_dilemma/Dilemma.html`:

```html+jinja
{% extends "Base.html" %}

{% block title %}
Your decision
{% endblock title %}


{% block main %}

{{ fields() }}

{% endblock main %}
```

`{{ fields() }}` renders all form fields defined on the page.

### Results.html

Create `my_dilemma/Results.html`:

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
<p>The other participant cooperated.</p>
{% else %}
<p>The other participant did not cooperate.</p>
{% endif %}

<p>Your payoff is <b>{{ player.payoff | fmtnum(pre="$", places=2) }}</b>.</p>

{% endblock main %}
```

`player.other_in_group` works in templates, too.

## 6. Run the experiment

Start the server with a ready-to-use room for your config:

```console
uv run uproot start my_dilemma
```

uproot prints a room link. Open it in two browser tabs: each tab joins as a new participant. Both participants read the instructions and then wait on the grouping page until the other arrives. After making their choices, they wait on the sync page until both have decided. Then they see their results.

!!! tip "Sessions for real experiments"
    `uproot start` is made for trying out an experiment. For real experiments, you usually create sessions in the [admin interface](../running/admin.md#creating-sessions) instead.

## 7. Test with simulated participants

Clicking through two tabs gets tedious as your experiment grows. `simulate.js` can click for you. Open `my_dilemma/simulate.js` and replace the `uproot.simulate.on(...)` block below the comment with:

```javascript
uproot.simulate.on("my_dilemma/Instructions", (sim) => {
    sim.submit();
});

uproot.simulate.on("my_dilemma/Dilemma", (sim) => {
    sim.choose("cooperate", sim.random(["True", "False"])).submit();
});
```

The first handler submits the instructions page. The second one picks “Yes” or “No” at random and submits the decision page. Start uproot with `--simulate` to switch them on:

```console
uv run uproot start my_dilemma --simulate
```

Open the room link in two tabs again and watch both participants play by themselves. See [App testing](../running/admin.md#app-testing) for all the helpers that `simulate.js` offers.

## The complete code

Below the comment at the top, `my_dilemma/__init__.py` now reads:

```python
from uproot.fields import *
from uproot.smithereens import *

DESCRIPTION = "Prisoner's dilemma"
SUGGESTED_MULTIPLE = 2


class C:
    PAYOFF_MATRIX = {
        # (you cooperate, other cooperates): your payoff
        (True, True): 10,
        (True, False): 0,
        (False, True): 15,
        (False, False): 3,
    }


class Instructions(Page):
    pass


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
    @classmethod
    def all_here(page, group: GroupType) -> None:
        for player in group.players:
            player.payoff = C.PAYOFF_MATRIX[
                player.cooperate,
                player.other_in_group.cooperate,
            ]


class Results(Page):
    pass


page_order = [
    Instructions,
    GroupPlease,
    Dilemma,
    Sync,
    Results,
]
```

Your app now matches the `prisoners_dilemma` sample app in your project, apart from its name.

[:material-github: See the full prisoners_dilemma example](https://github.com/mrpg/uproot-examples/tree/main/prisoners_dilemma)

## What’s next?

- **[Project structure](project-structure.md):** Understand the files in your project.
- **[Pages and templates](../building/pages.md):** Learn about page lifecycle methods.
- **[Collecting data with forms](../building/forms.md):** Explore all available field types.
- **[Grouping participants](../multiplayer/groups.md):** More on multiplayer experiments.
- **[Variations on this game](https://github.com/mrpg/uproot-examples):** `prisoners_dilemma_repeated`, `prisoners_dilemma_indefinite`, `prisoners_dilemma_chat`, and `prisoners_dilemma_fancy` build on the app you just wrote.
