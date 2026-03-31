# Page methods

All page methods are `@classmethod`s that receive `page` (the page class) and `player` (the current participant) as arguments. They can be sync or async.

## Lifecycle overview

When a participant navigates to a page, methods run in this order:

1. **`show`** — Should the page be displayed?
2. **`early`** — Earliest hook (before any rendering)
3. **`before_always_once`** — Runs once per page display
4. **`before_once`** — Runs once per player, on first visit only
5. **`fields`** — Determine form fields
6. **`templatevars`** / **`jsvars`** — Prepare template and JS data
7. *(Page is rendered and displayed)*
8. *(Participant submits)*
9. **`validate`** — Check submitted data
10. **`may_proceed`** — Gate before advancing
11. **`stealth_fields`** / **`handle_stealth_fields`** — Manual field handling
12. **`after_always_once`** — Runs once after each submission
13. **`after_once`** — Runs once per player, on first submission only
14. **`before_next`** — Last hook before advancing to the next page
15. **`timeout`** / **`timeout_reached`** — Handle page timeouts

## show

Decides whether the page should be displayed. Return `False` to skip the page entirely.

```python
@classmethod
def show(page, player):
    return player.role == "proposer"
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |
| **Returns** | `bool` — `True` to show (default), `False` to skip |

## early

The earliest hook in the page lifecycle. Runs before `before_always_once`. Receives the HTTP request as an additional keyword argument.

```python
@classmethod
def early(page, player, request):
    player.user_agent = request.headers.get("user-agent", "")
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |
| `request` | The Starlette `Request` object |

## before_once

Runs **once per player**, the first time they see this page. Does not run again if the player navigates back and returns.

```python
@classmethod
def before_once(page, player):
    player.start_time = time()
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |

## before_always_once

Runs once each time the page is displayed (including on back navigation). Use this for per-visit initialization.

```python
@classmethod
def before_always_once(page, player):
    player.visit_count = getattr(player, "visit_count", 0) + 1
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |

## fields

Returns the form fields for this page. Can be a dictionary (static) or a method (dynamic).

### Static fields

```python
class Survey(Page):
    fields = dict(
        age=IntegerField(label="Age", min=18, max=100),
    )
```

### Dynamic fields

```python
@classmethod
def fields(page, player):
    max_offer = player.other_in_group.endowment
    return dict(
        offer=IntegerField(label="Your offer", min=0, max=max_offer),
    )
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |
| **Returns** | `dict` mapping field names to field instances |

## templatevars

Returns variables available in the page template.

```python
@classmethod
def templatevars(page, player):
    return dict(
        partner=player.other_in_group,
        total=sum(p.contribution for p in player.group.players),
    )
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |
| **Returns** | `dict` of template variables |

## jsvars

Returns variables available in JavaScript as `_uproot_js`.

```python
@classmethod
def jsvars(page, player):
    return dict(
        initial_price=player.price,
        max_trades=C.MAX_TRADES,
    )
```

Access in JavaScript:

```javascript
const price = _uproot_js.initial_price;
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |
| **Returns** | `dict` of JavaScript variables |

## validate

Custom validation of submitted form data. Called after built-in field validation passes.

```python
@classmethod
def validate(page, player, data):
    if data["give_a"] + data["give_b"] > 100:
        return "Total cannot exceed 100"
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |
| `data` | `dict` of submitted values |
| **Returns** | Error message(s), or nothing if valid |

Return types:

- `str` — Single error displayed at the top of the form
- `list[str]` — Multiple errors displayed at the top
- `dict[str, str | list[str]]` — Per-field errors displayed next to each field

```python
@classmethod
def validate(page, player, data):
    errors = {}
    if data["min_price"] > data["max_price"]:
        errors["min_price"] = "Must be less than max price"
        errors["max_price"] = "Must be greater than min price"
    return errors or None
```

:material-github: [See the input_validation example](https://github.com/mrpg/uproot-examples/tree/master/input_validation)

## may_proceed

Gate that controls whether the player can advance. Return `False` to keep the player on the page.

```python
@classmethod
def may_proceed(page, player):
    from time import time
    return time() >= player.session.detection_period_until
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |
| **Returns** | `bool` — `True` to allow proceeding (default), `False` to block |

## after_once

Runs **once per player**, after the first forward submission. Does not run on back navigation or revisits.

```python
@classmethod
def after_once(page, player):
    player.completed_task = True
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |

## after_always_once

Runs once after each forward submission (including revisits after back navigation).

```python
@classmethod
def after_always_once(page, player):
    player.attempts += 1
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |

!!! note
    `after_once` and `after_always_once` are not available on `GroupCreatingWait` or `SynchronizingWait` pages.

## before_next

Runs just before the player advances to the next page. This is the last hook before navigation.

```python
@classmethod
def before_next(page, player):
    player.offer_made = True
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |

## timeout

Sets a page timeout in seconds. Can be a static value or a method.

### Static timeout

```python
class TimedTask(Page):
    timeout = 60
```

### Dynamic timeout

```python
@classmethod
def timeout(page, player):
    return max(0, player.deadline - time())
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |
| **Returns** | `float` seconds until timeout, or `None` to disable |

## timeout_reached

Called when the page timeout expires, before the page auto-advances.

```python
@classmethod
def timeout_reached(page, player):
    player.timed_out = True
    player.score = 0
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |

## stealth_fields

Specifies which fields should not be saved automatically. Can be a list or a method.

### Static stealth fields

```python
class MyPage(Page):
    stealth_fields = ["code", "iban"]
```

### Dynamic stealth fields

```python
@classmethod
def stealth_fields(page, player):
    return ["response"] if player.condition == "special" else []
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |
| **Returns** | `list[str]` of field names to handle manually |

## handle_stealth_fields

Processes stealth fields. Called after validation. Return error strings to reject the submission.

```python
@classmethod
async def handle_stealth_fields(page, player, data):
    code = data["code"]
    if code != "secret123":
        return "Invalid access code"
    player.verified = True
```

| Parameter | Description |
|-----------|-------------|
| `page` | The page class |
| `player` | The current player |
| `data` | `dict` of stealth field values |
| **Returns** | Error string or list of error strings, or nothing if valid |

:material-github: [See the payment_data example](https://github.com/mrpg/uproot-examples/tree/master/payment_data) · [input_validation example](https://github.com/mrpg/uproot-examples/tree/master/input_validation)

## Page class attributes

| Attribute | Default | Description |
|-----------|---------|-------------|
| `allow_back` | `False` | Show a "Back" button |
| `template` | `{AppName}/{ClassName}.html` | Custom template path |
| `keep_values` | `False` | Re-populate form from player data on re-render |

## Wait page methods

### GroupCreatingWait

| Attribute/Method | Description |
|------------------|-------------|
| `group_size` | Required. Number of players per group |
| `after_grouping(page, group)` | Called once when the group forms |

### SynchronizingWait

| Attribute/Method | Description |
|------------------|-------------|
| `synchronize` | `"group"` (default) or `"session"` |
| `all_here(page, group)` | Called when all group members arrive |
| `all_here(page, session)` | Called when all session members arrive (if `synchronize = "session"`) |
| `wait_for(page, player)` | Override to customize who to wait for |
