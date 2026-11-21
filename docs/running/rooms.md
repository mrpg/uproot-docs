---
description: 'Sessions and rooms: how participants join an experiment, room labels and capacity, configuring default rooms, and saving URL parameters such as study IDs.'
---

# Sessions and rooms

Sessions and rooms are the two concepts for managing how participants access your experiment.

## Sessions

A **session** is a running instance of an experiment config, containing players and their data. Each session has a unique session name (a short random string by default) and is associated with exactly one config.

### Creating a session directly

From the admin interface, navigate to **Sessions** and create a new session by selecting a config and specifying the number of players. This gives you a session with pre-created player slots that you can distribute manually.

Each pre-created player gets a unique URL of the form:

```
https://your-server.com/p/{session_name}/{player_name}/
```

You can share these URLs with participants individually. This approach works well for small experiments or when you want to assign specific participants to specific slots.

### Session initialization

A session is initialized the first time a player loads their first page. Initialization runs the `new_session` callback in each app (if defined), followed by `new_player` in each app for that player. Each callback runs only once; see [Initialization callbacks](../building/data.md#initialization-callbacks). If you created the session manually with pre-created players, you can also trigger initialization explicitly via the [admin API](../reference/admin-api.md), using `POST /admin/api/v1/sessions/{sname}/initialize/` and `POST /admin/api/v1/sessions/{sname}/players/initialize/`.

## Rooms

A **room** is a gateway that controls how participants enter a session. Instead of distributing individual player URLs, you can give all participants the same room URL:

```
https://your-server.com/room/{room_name}/
```

The room handles everything: waiting for the experiment to start, validating credentials, creating player slots, and redirecting participants to their session.

### Creating a room

Navigate to **Rooms** in the admin interface and create a new room. A room has several optional settings:

- **Config**: Which experiment config to run.
- **Labels**: Access codes that restrict who can join.
- **Capacity**: A maximum number of players.
- **Open**: Whether the room is currently accepting participants.

You can also create a room from code in your project’s `main.py` by appending to `DEFAULT_ROOMS`:

```python
import uproot.deployment as upd
from uproot.rooms import room

upd.DEFAULT_ROOMS.append(
    room(
        "my_room",
        config="my_experiment",
        labels=["ALPHA", "BRAVO", "CHARLIE"],
        capacity=20,
        open=True,
    )
)
```

Rooms defined this way are created automatically when the server starts.

### Quick rooms from the command line

During development, creating a room by hand just to test a config is tedious. The [`uproot start`](../reference/cli.md#uproot-start) command does it in one step:

```console
uv run uproot start my_experiment
```

This creates an open room named `quick1` (then `quick2`, and so on), creates a session for the config, starts the server, and prints the room URL. Open the URL in one browser tab per participant. Add `--simulate` to enable [simulated responses](admin.md#app-testing) for the session.

Quick rooms are ordinary rooms: they appear under **Rooms** in the admin, and everything on this page applies to them.

### Room lifecycle

A room acts as a finite-state machine with two main states:

**Waiting (closed)**

The room is in waiting state when any of the following are true:

- `open` is `False`
- The room has neither an associated session nor a config loaded by the server

Participants who visit a waiting room see a “Please wait” page. This page maintains a WebSocket connection to the server so it can advance automatically when the room opens. Participants do not need to refresh.

**Accepting (open)**

When `open` is `True` and the room has an associated session or a loaded config, it is ready to accept participants. Two things happen:

1. If no session exists yet, one is automatically created from the room’s config when the first participant arrives.
2. Participants are added to the session (subject to label and capacity checks).

After joining, participants are redirected to their player URL and begin the experiment.

### Starting a session in a room

From a room’s admin page, you can start a session in two ways:

**Let participants join on their own.** Set the room to open with a config. A session is created automatically when the first participant arrives, and subsequent participants join the same session. This is the most common approach.

**Pre-create a session with players.** Use the “Create session” form on the room’s admin page. Specify a config and the number of players. The session is created with player slots, the room opens, and waiting participants are notified via WebSocket. Pre-created player slots are claimed on a first-come, first-served basis.

When a room becomes ready, waiting browsers receive `RoomStarted` and automatically submit the join form. The server checks readiness again when that form arrives.

### Closing and reopening a room

You can close a room at any time to stop accepting new participants—even while a session is active. Closing a room does **not** affect the running session or its current players; it only prevents new participants from joining.

From the room’s admin page, use the **Close room** button. To resume accepting participants into the same session, use **Reopen room**.

This is useful when:

- You have enough participants and want to prevent latecomers from joining.
- You need to temporarily pause enrollment while checking on the experiment.
- You want to control exactly when new participants can enter.

Via the API, use [`PATCH /admin/api/v1/rooms/{roomname}/open/`](../reference/admin-api.md#patch-adminapiv1roomsroomnameopen) with `{"open": false}` to close or `{"open": true}` to reopen.

#### Closing vs. capacity

Closing a room and setting a capacity are two different mechanisms:

- **Capacity** limits how many players can join. Once the limit is reached, new participants see a “Room full” page. The room remains open and will accept participants again if capacity is freed up or increased.
- **Closing** shuts the door entirely. No new participants can join regardless of available capacity. Participants who visit a closed room see a “Please wait” page.

Use capacity when you want a fixed maximum group size. Use closing when you want manual control over *when* participants can enter, independent of how many have already joined.

### Disassociating and reusing rooms

A room can only have one session at a time. To reuse a room for a new session, first **disassociate** the current session. This unlinks the session from the room and resets the room’s state so new participants can wait again.

Room settings (config, labels, capacity) can only be edited when no session is associated.

### Labels (access codes)

Labels normally restrict room access to a predefined set of participants. Each participant must enter a valid label (access code) to join. You can also require a code without defining the allowed values in advance.

```python
upd.DEFAULT_ROOMS.append(
    room(
        "my_room",
        config="my_experiment",
        labels=["ALPHA", "BRAVO", "CHARLIE"],
    )
)
```

When labels are set:

- Participants see a “Welcome” page with an access code input field.
- The entered label is validated against the room’s label list.
- Invalid labels are rejected with an error message.
- Labels must use only the characters `A-Za-z0-9-._` and be at most 128 characters long.

Pass `labels=[]` (an empty list) to accept **any** non-empty access code, without listing codes in advance.

To load codes from a text file (one label per line; `#` starts a comment), use `from_file`:

```python
from uproot.rooms import room, from_file

upd.DEFAULT_ROOMS.append(
    room("lab", config="my_experiment", labels=from_file("labels.txt"))
)
```

After entering a valid label, participants wait for the room to open (if it is not already open). Once the room opens, they are automatically redirected.

If a participant enters a label that has already been used by another player in the session, they are redirected to that existing player’s URL. This means a participant can rejoin using the same label if they lose their connection.

### Eagerly accepted labels

*If* your room does not require labels, uproot will still eagerly accept labels that are provided using the `?label=` URL parameter. You could use that feature as follows:

```
https://your-server.com/room/{room_name}/?label=MY_LABEL
```

This is useful for physical labs (where `MY_LABEL` may be `01` to `32`, the number of cubicles), and online platforms, such as [Prolific](https://prolific.com/) IDs. For Prolific, a room with `labels=[]` works even better. See [Running on Prolific](prolific.md).

### Labels and capacity

When a non-empty label list is set but no explicit capacity is configured, the room’s effective capacity equals the number of labels. This means each label can be used by exactly one participant. The special `labels=[]` mode has no implicit capacity; set `capacity=` as well if you need a limit.

If you set both labels and an explicit capacity, the capacity value takes precedence. For example, you could have 100 labels but a capacity of 50, meaning only the first 50 valid labels will be accepted.

### Capacity

Capacity sets the maximum number of players that can join a room’s session. When the session is full, new participants see a “Room full” page.

```python
upd.DEFAULT_ROOMS.append(
    room(
        "my_room",
        config="my_experiment",
        capacity=30,
    )
)
```

### How capacity is enforced

A participant can join a room’s session if any of the following conditions are true:

1. **The room is freejoin:** `labels` is `None` or `[]`, and no capacity is set, so participants can join without limit.
2. **The session has room:** The current number of players is below the capacity.
3. **A free slot exists:**: A pre-created player slot that has not been claimed yet. Free slots bypass the capacity check, so pre-created players can always be claimed.

This means capacity primarily controls *growth*: It prevents new player slots from being created beyond the limit. It does not prevent participants from claiming pre-created slots, even if the number of pre-created slots exceeds the capacity.

### Capacity and manual session creation

When you create a session in a room with pre-created players, you can check the **"Set room capacity to number of players"** option. This sets the room’s capacity equal to the number of pre-created players, preventing any additional participants from joining beyond the pre-created slots.

Without that option, the room’s original capacity setting (if any) remains. Pre-created slots can always be claimed, but new slots are only created up to the capacity.

This implies: if you create a session with *n* players, but uncheck “Set room capacity to number of players,” your session can keep growing until the room’s capacity is reached. If the capacity is infinite, the session will be able to grow indefinitely. **Rooms are the only method to create new player slots in a session.**

### Freejoin rooms

A room with the default `labels=None` and no capacity is a **freejoin** room. There is no limit on how many participants can join, and every visitor gets a new player slot in the session. This is useful for large-scale experiments where you want to accept as many participants as possible.

The `labels=[]` mode with no capacity is also unlimited, but each visitor must enter a non-empty code. Reusing a code returns to the player slot that already has that code.

### The room WebSocket

When participants are on the waiting page, the browser opens a WebSocket connection to the server. This connection serves two purposes:

1. **Instant notification**: When the room opens, a `RoomStarted` event is sent over the WebSocket, and the browser automatically submits the join form. Participants do not need to refresh.
2. **Presence tracking**: The server tracks which participants are online in the room’s waiting area. The admin can see this on the room’s admin page.

The WebSocket connection uses a heartbeat mechanism to stay alive. If a participant closes the page, they are marked as offline.

Deleting a room ends its waiting connections with a `RoomDeleted` event. The waiting page shows “This room is no longer available.” Creating another room with the same name starts fresh; participants waiting for the deleted room do not automatically join it.

## Saving URL parameters when participants join

Recruitment platforms often add information to the link they send participants to. A link might end in `?STUDY_ID=S42&SOURCE=newsletter`: these are *URL parameters*, name–value pairs after the `?`, separated by `&`. uproot stores `label` by itself (see [Eagerly accepted labels](#eagerly-accepted-labels)) and ignores all other URL parameters. To keep them, add a function named `entry_data` to your app’s `__init__.py`:

```python
def entry_data(room, request):
    data = {}

    for key in ["STUDY_ID", "SOURCE"]:
        if key in request.query_params:
            data[key] = request.query_params[key]

    return data
```

`request.query_params` holds the URL parameters. The function copies the two parameters you care about, if they are there, into a dictionary and returns it. uproot saves that dictionary as `player.entry_data`. A participant who joins through

```
https://your-server.com/room/my_room/?STUDY_ID=S42&SOURCE=newsletter
```

therefore gets

```python
player.entry_data == {"STUDY_ID": "S42", "SOURCE": "newsletter"}
```

Read a value with `player.entry_data.get("SOURCE")`, which gives `None` if the parameter was missing. A participant whose link had neither parameter gets an empty dictionary, `{}`. So does every participant if no app defines `entry_data`.

`entry_data` is saved like any other player field, so it is part of your [data export](export.md). In CSV files, the dictionary appears as JSON text in a single cell.

### When `entry_data` runs

`entry_data` runs when uproot lets a participant into the session through

- a room link (`/room/…`), or
- the session’s shared link, shown as “Sessionwide URL” under **Player URLs** on the session’s admin page.

It does not run for individual player links (`/p/…`). It also does not run while a participant waits on the access code, “Please wait”, or “Room full” page. The URL parameters stay in the browser’s address bar on those pages, so `entry_data` still receives them once the participant gets in.

[`new_player`](../building/data.md#new_player) runs later, when the participant’s first page loads, so it can already read `player.entry_data`. The one exception: if you initialized pre-created players in advance through the [admin API](../reference/admin-api.md), their `new_player` ran before they joined.

### The two arguments

- `room` is the room the participant joins, as a [`RoomInfo`](../reference/api.md#roominfo) (for example, `room.name`). It is `None` when the participant uses the session’s shared link.
- `request` is the participant’s HTTP request, the message their browser sent to your server. It is a [Starlette `Request`](https://www.starlette.io/requests/). Besides the URL parameters in `request.query_params`, you can read the browser’s headers, for example `request.headers.get("Accept-Language")` for its preferred languages.

### Returning participants

A participant who [comes back with the same label](#labels-access-codes) does not get a new player, but `entry_data` runs again. uproot then updates `player.entry_data` key by key:

- A key that `entry_data` returns gets the new value.
- A key that `entry_data` does not return keeps its old value.

With the example above, a participant who first joins with `?SOURCE=newsletter` and later returns with `?SOURCE=email` ends up with `"SOURCE": "email"`. If they return without any `SOURCE`, they keep `"SOURCE": "newsletter"`. Replaced values are not lost: uproot’s [append-only log](../building/data.md#the-append-only-log) keeps them, and the `ultralong` export lists every value.

### Several apps

If several apps in your config define `entry_data`, uproot calls each of them, in the order of the config, and combines the dictionaries. If two apps return the same key, the value from the later app is saved.

!!! warning "Rules for `entry_data`"
    - Name the arguments exactly `room` and `request`, even if you do not use them. uproot passes them by name.
    - Write `def`, not `async def`. Otherwise, admission fails with `TypeError: myapp.entry_data() must be synchronous` (with your app’s name in place of `myapp`).
    - Always return a dictionary, even an empty one. Otherwise, admission fails with `TypeError: myapp.entry_data() must return a dict`.
    - Return only [values uproot can store](../building/data.md#supported-data-types). URL parameters are strings, which are always fine.
    - Keep it quick. While it runs, the whole server waits, so do not download files or contact other websites from it.

    If `entry_data` fails, the participant sees an error page and is not let in. No player slot is used up. Once you fix the function, the participant can open the same link again.

!!! warning "Participants can change URL parameters"
    Anyone can edit the address bar. Treat URL parameters like answers the participant typed in, not as proof of anything. Never let them decide payments or treatments that participants must not be able to choose.

## Reading room settings from your app

`player.session.room` is the name of the room that the session belongs to, or `None` if the session is not in a room. The name is often enough. For example, if you run the same config in a room called `lab` and in another room for online participants:

```python
def new_player(player):
    player.in_lab = player.session.room == "lab"
```

To read the room’s settings, pass its name to `get_room`:

```python
def new_player(player):
    room = get_room(player.session.room)

    if room is not None:
        player.room_capacity = room.capacity
```

`get_room` returns a [`RoomInfo`](../reference/api.md#roominfo) with the room’s `name`, `config`, `labels`, `capacity`, `open`, and `sname` (the name of the room’s session). It returns `None` if the name is `None` or no room has that name, for example because the room was deleted. Always check for `None`, as above.

A `RoomInfo` is a snapshot. It shows the room as it was when you called `get_room` and does not change afterwards. Call `get_room` again for the current settings. You cannot change a room through it: use the admin interface or the [admin API](../reference/admin-api.md).
