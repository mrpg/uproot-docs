# Sessions and rooms

Sessions and rooms are the two main concepts for managing how participants access your experiment. A **session** is a running instance of an experiment config, containing players and their data. A **room** is a gateway that controls how participants enter a session.

You can create sessions directly from the admin interface, but rooms give you much more control over participant entry.

## Sessions

A session is created from a [config](../getting-started/project-structure.md) and holds all experiment state: players, groups, models, and data. Each session has a unique session name (a short random string by default) and is associated with exactly one config.

### Creating a session directly

From the admin interface, navigate to **Sessions** and create a new session by selecting a config and specifying the number of players. This gives you a session with pre-created player slots that you can distribute manually.

Each pre-created player gets a unique URL of the form:

```
https://your-server.com/p/{session_name}/{player_name}/
```

You can share these URLs with participants individually. This approach works well for small experiments or when you want to assign specific participants to specific slots.

### Session initialization

A session is initialized the first time a player loads their first page. Initialization runs the `new_session` callback in each app (if defined), followed by `new_player` for that player. If you created the session manually with pre-created players, you can also trigger initialization explicitly via the admin API using the `run_new_session` and `run_new_player` endpoints.

## Rooms

A room is a URL that participants visit to enter an experiment. Instead of distributing individual player URLs, you give all participants the same room URL:

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

You can also create a room from code in your project's `main.py` by appending to `DEFAULT_ROOMS`:

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

### Room lifecycle

A room acts as a finite-state machine with two main states:

**Waiting (closed)**

The room is in waiting state when any of the following are true:

- `open` is `False`
- No config is associated with the room
- Both of the above

Participants who visit a waiting room see a "Please wait" page. This page maintains a WebSocket connection to the server so it can advance automatically when the room opens. Participants do not need to refresh.

**Accepting (open)**

When `open` is `True` and a config is set, the room begins accepting participants. Two things happen:

1. If no session exists yet, one is automatically created from the room's config when the first participant arrives.
2. Participants are added to the session (subject to label and capacity checks).

After joining, participants are redirected to their player URL and begin the experiment.

### Starting a session in a room

From a room's admin page, you can start a session in two ways:

**Let participants join on their own.** Set the room to open with a config. A session is created automatically when the first participant arrives, and subsequent participants join the same session. This is the most common approach.

**Pre-create a session with players.** Use the "Create session" form on the room's admin page. Specify a config and the number of players. The session is created with player slots, the room opens, and waiting participants are notified via WebSocket. Pre-created player slots are claimed on a first-come, first-served basis.

When a session is started in a room (either way), the `r.start(roomname)` signal fires, which wakes all WebSocket connections on the waiting page. Participants' browsers automatically submit the join form.

### Disassociating and reusing rooms

A room can only have one session at a time. To reuse a room for a new session, first **disassociate** the current session. This unlinks the session from the room and resets the room's state so new participants can wait again.

Room settings (config, labels, capacity) can only be edited when no session is associated.

## Labels (access codes)

Labels restrict room access to a predefined set of participants. Each participant must enter a valid label (access code) to join.

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

- Participants see a "Welcome" page with an access code input field.
- The entered label is validated against the room's label list.
- Invalid labels are rejected with an error message.
- Labels must use only the characters `A-Za-z0-9-._` and be at most 128 characters long.

After entering a valid label, participants wait for the room to open (if it isn't already). Once the room opens, they are automatically redirected.

If a participant enters a label that has already been used by another player in the session, they are redirected to that existing player's URL. This means a participant can rejoin using the same label if they lose their connection.

### Labels and capacity

When labels are set but no explicit capacity is configured, the room's effective capacity equals the number of labels. This means each label can be used by exactly one participant.

If you set both labels and an explicit capacity, the capacity value takes precedence. For example, you could have 100 labels but a capacity of 50, meaning only the first 50 valid labels will be accepted.

## Capacity

Capacity sets the maximum number of players that can join a room's session. When the session is full, new participants see a "Room full" page.

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

A participant can join a room's session if any of the following conditions are true:

1. **The room is freejoin**: no labels and no capacity are set, so anyone can join without limit.
2. **The session has room**: the current number of players is below the capacity.
3. **A free slot exists**: a pre-created player slot that hasn't been claimed yet. Free slots bypass the capacity check, so pre-created players can always be claimed.

This means capacity primarily controls *growth* — it prevents new player slots from being created beyond the limit. It does not prevent participants from claiming pre-created slots, even if the number of pre-created slots exceeds the capacity.

### Capacity and manual session creation

When you create a session in a room with pre-created players, you can check the **"Set room capacity to number of players"** option. This sets the room's capacity equal to the number of pre-created players, preventing any additional participants from joining beyond the pre-created slots.

Without that option, the room's original capacity setting (if any) remains. Pre-created slots can always be claimed, but new slots are only created up to the capacity.

This implies: if you create a session with *n* players, but uncheck "Set room capacity to number of players", your session can keep growing until the room's capacity is reached. If the capacity is infinite, the session will be able to grow indefinitely. **Rooms are the only method to create new player slots in a session.**

## Freejoin rooms

A room with no labels and no capacity is a **freejoin** room. There is no limit on how many participants can join. Every visitor gets a new player slot in the session. This is useful for large-scale experiments where you want to accept as many participants as possible.

## The room WebSocket

When participants are on the waiting page, the browser opens a WebSocket connection to the server. This connection serves two purposes:

1. **Instant notification**: When the room opens, a `RoomStarted` event is sent over the WebSocket, and the browser automatically submits the join form. Participants don't need to refresh.
2. **Presence tracking**: The server tracks which participants are online in the room's waiting area. The admin can see this on the room's admin page.

The WebSocket connection uses a heartbeat mechanism to stay alive. If a participant closes the page, they are marked as offline.
