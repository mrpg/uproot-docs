# Built-in chat

uproot provides a built-in chat system for experiments where participants need to communicate. The chat handles message display, pseudonyms, and real-time updates automatically.

## Creating a chat

Create a chat at the session or group level, typically in the `new_session` callback:

```python
def new_session(session):
    session.chat = chat.create(session)
```

The `chat.create()` function returns a chat identifier that you store on the session for later use.

:material-github: [See the chat example](https://github.com/mrpg/uproot-examples/tree/master/chat)

## Adding players to a chat

Add participants to the chat using `chat.add_player()`. This is typically done when they reach the chat page:

```python
class ChatPage(Page):
    @classmethod
    async def before_once(page, player):
        chat.add_player(player.session.chat, player)
```

The `before_once` method ensures each player is added exactly once, even if they refresh the page.

### Assigning pseudonyms

You can assign pseudonyms to protect participant identity:

```python
chat.add_player(
    player.session.chat,
    player,
    pseudonym=f"Player {player.id}",
)
```

If no pseudonym is provided, an anonymous identifier is generated automatically.

## Displaying the chat

Use the `chat()` template function to render the chat interface:

```html+jinja
{% extends "Base.html" %}

{% block main %}

{{ chat(session.chat) }}

{% endblock main %}
```

The chat widget provides:

- A message display area showing all messages
- An input field for typing messages
- A send button
- Real-time updates when others send messages
- Visual distinction between your messages and others'

## Session-level chat

The simplest chat setup is session-wide, where all participants can see all messages:

```python
def new_session(session):
    session.chat = chat.create(session)


class ChatPage(Page):
    @classmethod
    async def before_once(page, player):
        chat.add_player(
            player.session.chat,
            player,
            pseudonym=f"Player {player.id}",
        )


page_order = [
    ChatPage,
]
```

:material-github: [See the chat example](https://github.com/mrpg/uproot-examples/tree/master/chat)

## Group-level chat

For private communication within groups, create a chat per group in the `after_grouping` callback:

```python
class GroupPlease(GroupCreatingWait):
    group_size = 2

    @classmethod
    def after_grouping(page, group):
        group.chat = chat.create(group.session)

        for player in group.players:
            chat.add_player(group.chat, player)
```

Then display the group's chat:

```html+jinja
{{ chat(player.group.chat) }}
```

## Multiple chats

You can create multiple chat channels for different purposes:

```python
def new_session(session):
    session.general_chat = chat.create(session)
    session.announcements = chat.create(session)  # Admin-only channel
```

Display them on the same page or different pages:

```html+jinja
<h3>General discussion</h3>
{{ chat(session.general_chat) }}

<h3>Announcements</h3>
{{ chat(session.announcements) }}
```

## Reacting to new messages

Use `chat.on_message()` to register a callback that runs whenever a message is sent to a chat. This is useful for bots, automated responses, or recording-keeping logic.

```python
async def on_chat_message(chat, player, message):
    if player is None:
        return  # Message was sent programmatically, not by a participant
    # React to the message here


def new_player(player):
    player.my_chat = chat.create(player.session)
    chat.add_player(player.my_chat, player)
    chat.on_message(player.my_chat, on_chat_message)
```

The callback receives:
- `chat` — the `ModelIdentifier` of the chat
- `player` — the player who sent the message, or `None` if sent programmatically
- `message` — the message text

The callback is persistent: it is automatically restored when the server restarts.

:material-github: [See the chat example with callback](https://github.com/mrpg/uproot-examples/tree/master/chat) · [chat_with_claude example](https://github.com/mrpg/uproot-examples/tree/master/chat_with_claude)

## Chat API reference

### chat.create(session)

Creates a new chat channel.

```python
chat_id = chat.create(session)
```

Returns a `ModelIdentifier` that you store on the session or group.

### chat.add_player(chat, player, pseudonym=None)

Adds a participant to the chat.

```python
chat.add_player(session.chat, player)
chat.add_player(session.chat, player, pseudonym="Alice")
```

### chat.messages(chat)

Returns all messages in the chat.

```python
all_messages = chat.messages(session.chat)
```

### chat.players(chat)

Returns the list of players in the chat.

```python
participants = chat.players(session.chat)
```

### chat.exists(chat)

Checks if a chat exists.

```python
if chat.exists(session.chat):
    ...
```

## Styling the chat

The chat uses Bootstrap classes and can be customized with CSS. The main elements are:

- `.uproot-chat` - Container for the entire chat widget
- `.messages-container` - The scrollable message area
- `.list-unstyled` - The message list

Example custom styling:

```css
.messages-container {
    height: 400px;
    overflow-y: auto;
}

.uproot-chat .btn {
    min-width: 80px;
}
```

## Complete example

Here's a complete session-level chat:

```python
def new_session(session):
    session.chat = chat.create(session)


class ChatHere(Page):
    @classmethod
    async def before_once(page, player):
        chat.add_player(
            player.session.chat,
            player,
            pseudonym=f"Player {player.id}",
        )


page_order = [
    ChatHere,
]
```

Template (`ChatHere.html`):

```html+jinja
{% extends "Base.html" %}

{% block title %}
Chat
{% endblock title %}

{% block main %}

{{ chat(session.chat) }}

{% endblock main %}
```

:material-github: [See the full chat example](https://github.com/mrpg/uproot-examples/tree/master/chat) · [prisoners_dilemma_chat example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma_chat)

## Summary

| Function | Purpose |
|----------|---------|
| `chat.create(session)` | Create a new chat channel |
| `chat.add_player(chat, player, pseudonym=...)` | Add a participant to the chat |
| `chat.on_message(chat, callback)` | Register a callback for new messages |
| `chat(chat_id)` | Template function to render the chat |
| `chat.messages(chat)` | Get all messages |
| `chat.players(chat)` | Get all participants |
