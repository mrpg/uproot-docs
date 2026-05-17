# Live methods

Live methods let JavaScript call Python functions in real-time without page reloads. Use them for dynamic interfaces, live validation, background processing, and any interaction that needs immediate server response.

## The @live decorator

Mark a page method with `@live` to make it callable from JavaScript:

```python
class Counter(Page):
    @live
    def increment(page, player):
        player.counter += 1
        return player.counter
```

Live methods:

- Receive `page` and `player` as the first two arguments
- Can accept additional typed parameters
- Can return data back to the caller
- Can be sync or async

:material-github: [See the counter example](https://github.com/mrpg/uproot-examples/tree/master/counter)

## Calling from JavaScript

Use `uproot.invoke()` to call live methods:

```javascript
uproot.invoke("increment").then(count => {
    document.getElementById("counter").innerText = count;
});
```

Pass arguments after the method name:

```javascript
// Single argument
uproot.invoke("set_value", 42);

// Multiple arguments
uproot.invoke("save_response", "question1", "answer");

// With error handling
uproot.invoke("increment")
    .then(result => updateDisplay(result))
    .catch(error => showError("Operation failed"));
```

## Request-response pattern

Return data directly from the live method. The JavaScript Promise resolves with the returned value:

```python
class Quiz(Page):
    @live
    def check_answer(page, player, answer: str):
        correct = answer.lower() == "paris"
        if correct:
            player.score += 1
        return {"correct": correct, "score": player.score}
```

```javascript
uproot.invoke("check_answer", userInput).then(result => {
    if (result.correct) {
        showSuccess("Correct! Score: " + result.score);
    } else {
        showError("Try again");
    }
});
```

## Type validation

Live method parameters are validated using Python type hints:

```python
@live
def place_bid(page, player, amount: float, item_id: int):
    # amount must be a float
    # item_id must be an integer
    player.bid = amount
    return {"placed": amount}
```

Invalid arguments raise an error that rejects the JavaScript Promise. Supported types include:

- `str`, `int`, `float`, `bool`
- `list`, `dict`
- `Optional[T]` for nullable values
- Custom types via Pydantic

## Connection lifecycle

Handle WebSocket connection events in JavaScript:

```javascript
uproot.onReady(() => {
    // WebSocket connected, safe to invoke methods
    uproot.invoke("get_initial_state").then(initDisplay);
});

uproot.onReconnect(() => {
    // Reconnected after disconnect, refresh state
    uproot.invoke("get_current_state").then(refreshDisplay);
});

uproot.onDisconnect(() => {
    // Connection lost, show warning
    showConnectionWarning();
});
```

## Example: dynamic counter

A counter that updates without page reload:

### Python

```python
def new_player(player):
    player.counter = 0


class Counter(Page):
    @live
    def increment(page, player):
        player.counter += 1
        return player.counter

    @live
    def reset(page, player):
        player.counter = 0
        return player.counter
```

### Template

```html+jinja
{% extends "Base.html" %}

{% block main %}
<p>Count: <span id="count">{{ player.counter }}</span></p>
<button onclick="increment()">+1</button>
<button onclick="reset()">Reset</button>

<script>
function increment() {
    uproot.invoke("increment").then(count => {
        document.getElementById("count").innerText = count;
    });
}

function reset() {
    uproot.invoke("reset").then(count => {
        document.getElementById("count").innerText = count;
    });
}
</script>
{% endblock main %}
```

:material-github: [See the counter example](https://github.com/mrpg/uproot-examples/tree/master/counter) · [counter_alpine example](https://github.com/mrpg/uproot-examples/tree/master/counter_alpine) (with Alpine.js)

## Example: live form validation

Validate input as the user types:

```python
class Registration(Page):
    fields = dict(
        username=StringField(label="Username"),
    )

    @live
    def check_username(page, player, username: str):
        # Check if username is available
        taken = username.lower() in ["admin", "root", "system"]
        return {"available": not taken}
```

```javascript
document.getElementById("username").addEventListener("input", (e) => {
    uproot.invoke("check_username", e.target.value).then(result => {
        if (result.available) {
            showValid("Username available");
        } else {
            showError("Username taken");
        }
    });
});
```

## Example: fetching data

Load data dynamically without page reload:

```python
class Dashboard(Page):
    @live
    def get_stats(page, player):
        return {
            "total_responses": player.session.response_count,
            "average_score": player.session.average_score,
        }
```

```javascript
uproot.onReady(() => {
    // Fetch stats when page loads
    uproot.invoke("get_stats").then(stats => {
        document.getElementById("responses").innerText = stats.total_responses;
        document.getElementById("average").innerText = stats.average_score;
    });
});

// Refresh stats periodically
setInterval(() => {
    uproot.invoke("get_stats").then(updateDashboard);
}, 5000);
```

## Async operations

Live methods can be async for I/O operations. Keep reads and writes of `player`,
`player.session`, and other uproot storage outside the part of the method that
awaits whenever you can:

```python
@live
async def process_data(page, player, data: dict):
    # Do slow external work first.
    result = await some_async_function(data)

    # Then update uproot state without another await in between.
    player.processed = result
    return {"status": "complete"}
```

### Advanced concurrency note

Special care must be taken when you want to allow live methods to interleave with
`async`. Specifically:

Live method calls from the same browser page are not a transaction queue. If an
advanced `@live` method reaches an `await`, another live method call for the same
participant may run before the first one resumes. This matters only for methods
whose correctness depends on a check-then-act sequence across an `await`.

Avoid this pattern:

```python
@live
async def submit_once(page, player, payload: dict):
    if player.submitted:
        raise ValueError("Already submitted")

    result = await external_service(payload)

    player.result = result
    player.submitted = True
```

Prefer doing awaited work before entering the state-sensitive section, or keep
the state-sensitive section free of awaits:

```python
@live
async def submit_once(page, player, payload: dict):
    result = await external_service(payload)

    if player.submitted:
        raise ValueError("Already submitted")

    player.result = result
    player.submitted = True
```

For most live methods, including the examples in this guide, this is not a
concern because the method does not await while it is reading or updating uproot
state.

## Example: real-effort task

Live methods are ideal for real-effort tasks where participants interact repeatedly without page reloads:

```python
class Sumhunt(Page):
    timeout = 120

    @live
    def get_matrix(page, player):
        if player.matrix is None:
            player.matrix = generate_matrix(...)
        return player.matrix

    @live
    def propose_solution(page, player, solution: list[int]):
        if sum(solution) == TARGET and all(x in player.matrix for x in solution):
            player.solutions += 1
            player.matrix = generate_matrix(...)  # New puzzle
            return True
        return False
```

```javascript
// Fetch puzzle on page load
uproot.onReady(() => {
    uproot.invoke("get_matrix").then(updateDisplay);
});

// Submit answer and get next puzzle
uproot.invoke("propose_solution", selectedNumbers).then(correct => {
    if (correct) {
        uproot.invoke("get_matrix").then(updateDisplay);
    }
});
```

:material-github: [See the sumhunt example](https://github.com/mrpg/uproot-examples/tree/master/sumhunt)

## Summary

| Feature | Purpose |
|---------|---------|
| `@live` decorator | Make method callable from JavaScript |
| `uproot.invoke("method", args)` | Call live method from JavaScript |
| Return value | Data returned to JavaScript Promise |
| Type hints | Automatic parameter validation |
| `uproot.onReady(fn)` | Run when WebSocket connects |
| `uproot.onReconnect(fn)` | Run after reconnection |
| `uproot.onDisconnect(fn)` | Run when connection lost |

For broadcasting updates to multiple participants, see [Real-time interactions](../multiplayer/real-time.md).
