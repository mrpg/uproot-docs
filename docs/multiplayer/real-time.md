# Real-time interactions

uproot supports real-time communication between participants through WebSockets. This page covers broadcasting updates to multiple participants. For the basics of live methods (the `@live` decorator and `uproot.invoke`), see [Live methods](../building/live-methods.md).

## Two patterns: return values vs. notifications

There are two ways to send data back to the browser:

1. **Return values** — Data goes back to the caller only
2. **Notifications** — Data is pushed to one or more participants

```python
@live
async def post_offer(page, player, price: float):
    player.my_offer = price

    # Broadcast to everyone (notification)
    notify(player, player.session.players, price, event="NewOffer")

    # Return to the caller only
    return {"posted": price}
```

Use return values for request-response patterns. Use `notify` for broadcasting to multiple participants.

## Broadcasting with notify

`notify` sends data to one or more participants:

```python
# Notify one player
notify(player, other_player, data)

# Notify all players in a group
notify(player, player.group.players, data)

# Notify all players in a session
notify(player, player.session.players, data)

# Notify everyone except the sender
notify(player, player.others_in_group, data)
```

The first argument is the sender (used to determine the current page context). The second is the recipient(s).

### Custom events

Name your notifications with the `event` parameter:

```python
notify(player, player.session.players, market_data, event="MarketUpdate")
```

Listen for specific events in JavaScript:

```javascript
uproot.onCustomEvent("MarketUpdate", (event) => {
    refreshMarketDisplay(event.detail.data);
});
```

### Default event handling

Without a custom event name, data goes to `uproot.receive`:

```python
notify(player, other_player, "Hello!")
```

```javascript
uproot.receive = (data) => {
    console.log(data);  // "Hello!"
};
```

## send_to for server-initiated updates

Use `send_to` when you don't have a sender context (like in background tasks):

```python
from uproot.smithereens import send_to

send_to(player, data)
send_to(session.players, data, event="StatusUpdate")
```

## Example: live text observation

One participant types while another watches in real-time:

```python
class Diary(Page):
    @live
    async def typed(page, player, text: str):
        observer = player.other_in_group
        notify(player, observer, text)
```

```javascript
// Writer
textarea.oninput = () => {
    uproot.invoke("typed", textarea.value);
};

// Observer
uproot.receive = (text) => {
    display.innerText = text;
};
```

:material-github: [See the observed_diary example](https://github.com/mrpg/uproot-examples/tree/master/observed_diary)

## Example: collaborative drawing

Multiple participants drawing on a shared canvas:

```python
class Draw(Page):
    @live
    async def stroke(page, player, points: list, color: str):
        player.session.strokes.append({"points": points, "color": color})

        # Send to others (not the sender)
        notify(player, player.others_in_session, {"points": points, "color": color}, event="NewStroke")
```

```javascript
uproot.onCustomEvent("NewStroke", (event) => {
    drawStroke(event.detail.data.points, event.detail.data.color);
});
```

:material-github: [See the drawing_board example](https://github.com/mrpg/uproot-examples/tree/master/drawing_board)

## Example: real-time market

A trading interface where participants post and accept offers:

```python
class Market(Page):
    @live
    async def post_offer(page, player, price: float):
        player.my_offer = price

        # Broadcast updated market to everyone
        notify(player, player.session.players, list(player.session.offers), event="MarketUpdate")
        return {"posted": price}

    @live
    async def accept_offer(page, player, seller_id: str):
        seller = player.session.players.get(seller_id)
        price = seller.my_offer

        player.bought_at = price
        seller.sold_at = price
        seller.my_offer = None

        # Notify the seller directly
        notify(player, seller, price, event="OfferAccepted")

        # Update market for everyone
        notify(player, player.session.players, list(player.session.offers), event="MarketUpdate")
        return {"bought_at": price}
```

```javascript
uproot.onCustomEvent("MarketUpdate", (event) => {
    renderMarket(event.detail.data);
});

uproot.onCustomEvent("OfferAccepted", (event) => {
    showNotification(`Your offer was accepted at ${event.detail.data}!`);
});
```

:material-github: [See the double_auction example](https://github.com/mrpg/uproot-examples/tree/master/double_auction)

## Summary

| Feature | Use case |
|---------|----------|
| `notify(sender, recipients, data)` | Broadcasting updates to participants |
| `notify(..., event="Name")` | Named events for specific handlers |
| `send_to(recipients, data)` | Server-initiated updates (background tasks) |
| `uproot.onCustomEvent("Name", fn)` | Listening for named events |
| `uproot.receive = fn` | Default handler for unnamed notifications |
| `player.others_in_group` | All group members except sender |
| `player.others_in_session` | All session members except sender |
