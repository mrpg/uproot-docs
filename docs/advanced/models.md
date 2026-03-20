# Custom data models

Models provide structured, append-only data storage beyond the standard player/group/session fields. Use them for ordered collections of entries like transaction logs, auction bids, or any data that accumulates over time.

!!! note
    The built-in [chat system](../multiplayer/chat.md) is built on top of models. For chat functionality, use the chat API directly.

## Creating a model

Create a model in a session, typically in `new_session`:

```python
from uproot.models import create_model

def new_session(session):
    session.offers = create_model(session)
```

`create_model` returns a `ModelIdentifier` that you store on the session (or group) for later use.

## Defining entry types

Define the structure of your entries using the `Entry` metaclass:

```python
from uproot.models import Entry
from uproot.types import PlayerIdentifier

class Offer(metaclass=Entry):
    player: PlayerIdentifier
    price: float
    quantity: int
```

Entry classes are immutable dataclasses. The `id` field name is reserved.

Fields with types `PlayerIdentifier`, `SessionIdentifier`, `GroupIdentifier`, or `ModelIdentifier` are auto-filled when using `add_entry`.

## Adding entries

Use `add_entry` to add an entry to a model. Identifier fields matching the player's session, group, or player ID are filled automatically:

```python
from uproot.models import add_entry

@live
async def post_offer(page, player, price: float, quantity: int):
    add_entry(player.session.offers, player, Offer, price=price, quantity=quantity)
```

The first argument is the model identifier, the second is the player (used for auto-filling identifier fields), and the third is the entry type. Remaining keyword arguments fill the entry's fields.

Each entry is timestamped and assigned a UUID.

### Raw entries

To add an entry without auto-filling, use `add_raw_entry`:

```python
from uproot.models import add_raw_entry

add_raw_entry(session.log, {"event": "started", "detail": "phase 2"})
```

## Retrieving entries

### All entries

```python
from uproot.models import get_entries

entries = get_entries(session.offers, Offer)
for uuid, timestamp, offer in entries:
    print(f"{offer.player} offered {offer.price} at {timestamp}")
```

`get_entries` returns a list of `(UUID, float, entry)` tuples, ordered by time.

### Filtered entries

```python
from uproot.models import filter_entries

# Filter by field values
cheap_offers = filter_entries(session.offers, Offer, price=10.0)

# Filter by predicate
large_offers = filter_entries(
    session.offers, Offer,
    predicate=lambda o: o.quantity > 100,
)

# Filter by entry UUID
specific = filter_entries(session.offers, Offer, id=some_uuid)
```

### Latest entry

```python
from uproot.models import get_latest_entry

uuid, timestamp, latest = get_latest_entry(session.offers, Offer)
```

### Single field

Read a single field from the model's storage:

```python
from uproot.models import get_field

value = get_field(session.offers, "some_field")
```

## Checking existence

```python
from uproot.models import model_exists

if model_exists(session.offers):
    ...
```

## Example: auction log

A complete example using models to track bids in an auction:

```python
from uproot.models import Entry, create_model, add_entry, get_entries, get_latest_entry
from uproot.types import PlayerIdentifier


class Bid(metaclass=Entry):
    player: PlayerIdentifier
    amount: float


def new_session(session):
    session.auction = create_model(session)


class Auction(Page):
    @live
    async def place_bid(page, player, amount: float):
        add_entry(player.session.auction, player, Bid, amount=amount)

        # Get all bids
        bids = get_entries(player.session.auction, Bid)

        # Return current highest
        if bids:
            _, _, highest = max(bids, key=lambda b: b[2].amount)
            return {"highest": highest.amount, "total_bids": len(bids)}
        return {"highest": 0, "total_bids": 0}
```

## Summary

| Function | Purpose |
|----------|---------|
| `create_model(session)` | Create a new model, returns `ModelIdentifier` |
| `add_entry(mid, player, EntryType, **fields)` | Add entry with auto-filled identifiers |
| `add_raw_entry(mid, entry)` | Add entry without auto-filling |
| `get_entries(mid, EntryType)` | Get all entries as `(UUID, time, entry)` tuples |
| `filter_entries(mid, EntryType, **filters)` | Get filtered entries |
| `get_latest_entry(mid, EntryType)` | Get most recent entry |
| `get_field(mid, field_name)` | Read a field from model storage |
| `model_exists(mid)` | Check if a model exists |
