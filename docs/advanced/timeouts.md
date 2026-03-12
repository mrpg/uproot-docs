# Page timeouts

Timeouts automatically advance participants to the next page after a specified duration. Use them for timed tasks, real-effort experiments, or to keep participants moving through your study.

## Static timeout

Set a fixed timeout in seconds as a class attribute:

```python
class TimedTask(Page):
    timeout = 60  # Auto-advance after 60 seconds
```

When the timeout expires, the page submits automatically with whatever data has been entered.

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

:material-github: [See the timeout_multipage example](https://github.com/mrpg/uproot-examples/tree/master/timeout_multipage)

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

:material-github: [See the sumhunt example](https://github.com/mrpg/uproot-examples/tree/master/sumhunt) · [encryption_task example](https://github.com/mrpg/uproot-examples/tree/master/encryption_task)

## Repositioning the countdown display

uproot automatically shows a countdown timer in `#uproot-timeout`. To move it elsewhere on your page, relocate the `#uproot-time-remaining` element with JavaScript:

```html+jinja
<p>Time remaining: <span id="time-here"></span></p>

<script>
document.getElementById("time-here").appendChild(
    document.getElementById("uproot-time-remaining")
);
document.getElementById("uproot-timeout").remove();
</script>
```

This moves the countdown into your custom container and removes the default wrapper.

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

The `uproot` object exposes timeout state and events for custom interfaces.

### Reading timeout state

```javascript
// Deadline as Unix timestamp (milliseconds)
uproot.timeoutUntil  // e.g., 1706198400000

// Calculate remaining seconds
const remaining = (uproot.timeoutUntil - Date.now()) / 1000;
```

### Timeout events

Two custom events fire on `window`:

```javascript
// Fires once when the timeout is set
window.addEventListener("UprootInternalPageTimeoutSet", () => {
    console.log("Timeout started:", uproot.timeoutUntil);
});

// Fires every second during countdown
window.addEventListener("UprootInternalPageTimeout", () => {
    const remaining = (uproot.timeoutUntil - Date.now()) / 1000;
    updateCustomDisplay(remaining);
});
```

### Visual feedback classes

The default `#uproot-timeout` element automatically changes Bootstrap alert classes based on remaining time:

| Remaining time | Class added |
|----------------|-------------|
| ≥ 60 seconds | `alert-light` |
| < 60 seconds | `alert-warning` |
| < 15 seconds | `alert-danger` |

### Custom countdown display

Combine these APIs for a fully custom countdown:

```html+jinja
<div id="my-timer" class="display-4"></div>

<script>
window.addEventListener("UprootInternalPageTimeout", () => {
    const secs = Math.max(0, Math.floor((uproot.timeoutUntil - Date.now()) / 1000));
    const mins = Math.floor(secs / 60);
    const remainder = secs % 60;
    document.getElementById("my-timer").innerText =
        `${mins}:${remainder.toString().padStart(2, "0")}`;
});

// Hide default display
document.getElementById("uproot-timeout")?.remove();
</script>
```

## Summary

| Feature | Purpose |
|---------|---------|
| `timeout = 60` | Static timeout in seconds |
| `def timeout(page, player)` | Dynamic timeout calculation |
| `def timeout_reached(page, player)` | Callback when timeout expires |
| Return `None` from timeout | Disable timeout for that player |
| `uproot.timeoutUntil` | JavaScript: deadline timestamp |
| `UprootInternalPageTimeoutSet` | JavaScript: event when timeout starts |
| `UprootInternalPageTimeout` | JavaScript: event every second |
