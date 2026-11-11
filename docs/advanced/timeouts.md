---
description: Advance participants automatically with static or dynamic page timeouts, handle expiration, span timeouts across pages, and customize the countdown.
---

# Page timeouts

Timeouts automatically advance participants to the next page after a specified duration. Use them for timed tasks, real-effort experiments, or to keep participants moving through your study.

## Static timeout

Set a fixed timeout in seconds as a class attribute:

```python
class TimedTask(Page):
    timeout = 60  # Auto-advance after 60 seconds
```

When the timeout expires, the participant moves on to the next page. uproot saves what they entered if it is valid; see [What happens to entered data](#what-happens-to-entered-data).

## Dynamic timeout

Use a method to calculate the timeout based on player state:

```python
class AdaptiveTask(Page):
    @classmethod
    def timeout(page, player):
        # Faster participants get less time
        base_time = 120
        bonus = player.correct_answers * 5
        return base_time - bonus
```

The method receives `page` and `player` and returns the timeout in seconds. Return `None` to disable the timeout for that player.

## Handling timeout expiration

The `timeout_reached` callback runs when the timeout expires:

```python
class TimedQuiz(Page):
    timeout = 30

    @classmethod
    def timeout_reached(page, player):
        player.timed_out = True
        player.score = 0  # Penalty for not answering in time
```

This callback runs before the page advances. Use it to:

- Record that the participant timed out
- Apply penalties or default values
- Set flags for conditional logic later

### What happens to entered data

When time runs out, the browser submits the page with whatever the participant has entered so far. uproot then:

1. runs `timeout_reached`,
2. checks the submitted data as usual, with built-in validation, [`validate`](../building/forms.md#custom-validation), and [`handle_stealth_fields`](../building/forms.md#stealth-fields),
3. saves the data only if it passes all checks,
4. moves the participant to the next page in any case.

The same happens to any request that arrives after the deadline, also if the participant clicked “Back” at the last moment: they move on, not back.

So a timeout never shows error messages, and it never keeps a participant on the page. If the entered data are incomplete or invalid, **none** of the page’s fields are saved, not even the valid ones. If they are valid, they are saved and overwrite any values that `timeout_reached` set for the same fields.

If the participant’s browser is closed when time runs out, nothing happens until they return. As soon as they load the page again, `timeout_reached` runs and the page advances.

!!! warning "Fields can be missing after a timeout"
    After a timeout, a page’s fields may not exist at all. Reading them later fails with an error such as `AttributeError: Player(*('nvfyk', 'ic9uj')) has no .answer`. Set a default in `timeout_reached`. Answers that were entered in time and are valid replace the default:

    ```python
    class Question(Page):
        timeout = 30
        fields = dict(answer=IntegerField(label="Your estimate"))

        @classmethod
        def timeout_reached(page, player):
            player.timed_out = True
            player.answer = None  # Replaced if a valid answer is submitted
    ```

    Note that `timed_out` is `True` even if the participant’s valid answer was saved at the last moment. To tell the two cases apart, check whether `player.answer` is `None`.

## Timeouts and `may_proceed`

A page with a [`may_proceed`](../reference/page-methods.md#may_proceed) method keeps participants on the page until a condition holds. A timeout overrides this: once the deadline has passed, the page advances even if `may_proceed` returns `False`. This keeps [wait pages](../multiplayer/synchronization.md) from hanging forever when time runs out.

uproot counts a timeout as reached up to one second before the deadline. In that last second, the page only advances if `may_proceed` allows it. So if the next page relies on the deadline having passed, check the deadline in `may_proceed`:

```python
class Negotiate(Page):
    @classmethod
    def timeout(page, player):
        from time import time
        return max(0, player.group.deadline - time())

    @classmethod
    def may_proceed(page, player):
        from time import time
        return player.group.agreed or time() >= player.group.deadline
```

Without `may_proceed`, a participant can reach the next page up to one second before the deadline. To change this tolerance, set `upd.TIMEOUT_TOLERANCE` (in seconds) in `main.py`.

## Timeout spanning multiple pages

For a shared timeout across several pages, store the deadline and calculate remaining time dynamically:

```python
class InitializeTimeout(NoshowPage):
    @classmethod
    def after_always_once(page, player):
        from time import time
        player.deadline = time() + 60  # 60 seconds total
        player.failed = False


class TimedPage(Page):
    @classmethod
    def timeout(page, player):
        from time import time
        return max(0, player.deadline - time())

    @classmethod
    def timeout_reached(page, player):
        if not player.failed:
            player.failed = True


class Task1(TimedPage):
    pass


class Task2(TimedPage):
    pass


class Task3(TimedPage):
    pass


page_order = [
    InitializeTimeout,
    Task1,
    Task2,
    Task3,
    Results,
]
```

All three task pages share the same 60-second deadline. If time runs out on any page, `player.failed` is set.

[:material-github: See the timeout_multipage example](https://github.com/mrpg/uproot-examples/tree/main/timeout_multipage)

## Timeouts with live methods

Timeouts work well with live methods for real-effort tasks:

```python
class Sumhunt(Page):
    timeout = 120  # 2 minutes to solve puzzles

    @live
    async def submit_answer(page, player, answer: int):
        if answer == player.correct_answer:
            player.score += 1
            player.puzzle = generate_new_puzzle()
        return player.puzzle
```

The participant interacts via live methods until the timeout advances them.

[:material-github: See the sumhunt example](https://github.com/mrpg/uproot-examples/tree/main/sumhunt) · [encryption_task example](https://github.com/mrpg/uproot-examples/tree/main/encryption_task)

## Hiding the countdown display

Sometimes participants should not see how much time is left, for example when time pressure is part of your design. To hide the countdown, override the `timeoutbox` block with an empty one in your page’s template:

```html+jinja
{% extends "Base.html" %}

{% block timeoutbox %}{% endblock timeoutbox %}

{% block title %}
Negotiation
{% endblock title %}

{% block main %}
<p>Make your offer.</p>
{% endblock main %}
```

The timeout still applies. Only the display is gone.

## Repositioning the countdown display

By default, uproot shows the countdown above your page content. To show it somewhere else, empty the `timeoutbox` block and place the countdown yourself with one of two template helpers:

- `timeout_box()` renders the complete box, including the text “Remaining time on this page:”, and hides it while no timeout is active.
- `timeout()` renders only the remaining time, for example “1:05 minutes” or “42 seconds”, so you can put it inside your own text.

```html+jinja
{% extends "Base.html" %}

{% block timeoutbox %}{% endblock timeoutbox %}

{% block title %}
Estimation task
{% endblock title %}

{% block main %}
<p>Time left: {{ timeout(class_="fw-bold") }}</p>

{{ fields() }}

{{ timeout_box(class_="alert alert-info") }}
{% endblock main %}
```

Both helpers accept HTML attributes as keyword arguments. Write `class_` (with an underscore) for the `class` attribute, because `class` is a reserved word in Python. You can use the helpers several times on one page; all copies count down together.

The default block also contains a hidden element that announces the remaining time to screen readers when time gets short. If you empty the block and want to keep this, add it to your template:

```html
<div id="uproot-timeout-announcer" class="visually-hidden" aria-live="assertive" aria-atomic="true"></div>
```

[:material-github: See the button_placement example](https://github.com/mrpg/uproot-examples/tree/main/button_placement)

## Checking timeout status in templates

Access the timeout flag in your results template:

```html+jinja
{% if player.timed_out %}
<p>You ran out of time.</p>
{% else %}
<p>You completed the task in time.</p>
{% endif %}
```

## Advanced: JavaScript timeout API

The `uproot` object exposes timeout state and events for custom interfaces. The
countdown uses the monotonic `performance.now()` clock, not a Unix deadline.

### Reading timeout state

`uproot.pageTimeoutRemainingMs()` returns the remaining time in milliseconds (`0` if no timeout is active). The [timeout events](#timeout-events) below also pass the full state as `event.detail`:

```javascript
// { active, level, text, compact }
// active:  whether a timeout is running
// level:   "light", "warning", or "danger" (see below)
// text:    for example "1 minute and 5 seconds"
// compact: for example "1:05 minutes" or "42 seconds"
```

### Timeout events

Two custom events fire on `window`:

```javascript
// Fires once when the timeout is set
window.addEventListener("UprootInternalPageTimeoutSet", (event) => {
    console.log("Timeout started:", event.detail.text);
});

// Fires every second during countdown
window.addEventListener("UprootInternalPageTimeout", (event) => {
    console.log("Remaining:", event.detail.compact);
});
```

### Visual feedback classes

Every countdown box from `timeout_box()`, including the default one, gets a class for the current timeout level:

| Remaining time | Level | Class added |
|----------------|-------|-------------|
| More than 60 seconds | `light` | `uproot-timeout-light` |
| 60 seconds or less | `warning` | `uproot-timeout-warning` |
| 15 seconds or less | `danger` | `uproot-timeout-danger` |

To change the thresholds, set `uproot.pageTimeoutWarningSeconds` and `uproot.pageTimeoutDangerSeconds` in your page’s JavaScript.

### Custom countdown display

Combine these APIs for a fully custom countdown:

```html+jinja
<div id="my-timer" class="display-4"></div>

<script>
window.addEventListener("UprootInternalPageTimeout", (event) => {
    const timer = document.getElementById("my-timer");
    timer.innerText = event.detail.compact;
    timer.classList.toggle("text-danger", event.detail.level === "danger");
});
</script>
```

To hide the default display, override the `timeoutbox` block as shown in [Hiding the countdown display](#hiding-the-countdown-display).

## Summary

| Feature | Purpose |
|---------|---------|
| `timeout = 60` | Static timeout in seconds |
| `def timeout(page, player)` | Dynamic timeout calculation |
| `def timeout_reached(page, player)` | Callback when timeout expires |
| Return `None` from timeout | Disable timeout for that player |
| `{% block timeoutbox %}{% endblock timeoutbox %}` | Hide the countdown display |
| `{{ timeout_box() }}` / `{{ timeout() }}` | Place the countdown box or the bare remaining time |
| `uproot.pageTimeoutRemainingMs()` | JavaScript: remaining time in milliseconds |
| `UprootInternalPageTimeoutSet` | JavaScript: event when timeout starts |
| `UprootInternalPageTimeout` | JavaScript: event every second |
