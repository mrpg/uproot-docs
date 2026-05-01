# uproot

**uproot** is a modern, open-source framework for developing and conducting browser-based behavioral experiments. Build studies with hundreds of participants, from simple surveys to complex real-time multiplayer games.

[:material-play-circle: **Try the live demo**](https://demo.uproot.science){ .md-button .md-button--primary }

!!! warning "Work in progress"

    uproot is in pre-alpha. Breaking changes are made with reckless abandon. We are working towards the first alpha (0.0.1) and invite you to join us.

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } __Get started in minutes__

    ---

    Install uproot with a single command and create your first experiment.

    [:octicons-arrow-right-24: Installation](getting-started/installation.md)

-   :material-book-open-variant:{ .lg .middle } __Learn by doing__

    ---

    Follow the tutorial to build a complete prisoner's dilemma experiment.

    [:octicons-arrow-right-24: Tutorial](getting-started/tutorial.md)

-   :material-account-group:{ .lg .middle } __Built for multiplayer__

    ---

    Group participants, synchronize progress, and enable real-time interaction.

    [:octicons-arrow-right-24: Multiplayer experiments](multiplayer/groups.md)

-   :material-folder-open:{ .lg .middle } __Explore examples__

    ---

    Ready-to-use experiments covering common paradigms and techniques.

    [:octicons-arrow-right-24: Example apps](https://github.com/mrpg/uproot-examples)

-   :material-robot-outline:{ .lg .middle } __AI-assisted development__

    ---

    Build experiments faster with Claude Code, Codex, and other agentic coding tools.

    [:octicons-arrow-right-24: Set up AI tooling](getting-started/installation.md#set-up-ai-assisted-development)

</div>

## Why uproot?

- **Real-time multiplayer** — Built-in support for grouping participants, synchronization, and live interactions
- **Flexible data storage** — Append-only log ensures data persistence and supports arbitrary data types
- **Modern stack** — Built on [FastAPI](https://fastapi.tiangolo.com/) for performance and reliability
- **100% open source** — LGPL-licensed with no vendor lock-in

## Quick example

Here's the core logic of a prisoner's dilemma experiment:

```python
from uproot.fields import *
from uproot.smithereens import *

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
    def all_here(page, group):
        for player in group.players:
            other = player.other_in_group

            match player.cooperate, other.cooperate:
                case True, True: player.payoff = 10
                case True, False: player.payoff = 0
                case False, True: player.payoff = 15
                case False, False: player.payoff = 3

class Results(Page):
    pass

page_order = [GroupPlease, Dilemma, Sync, Results]
```

:material-github: [Browse the complete example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma) including HTML templates

## Getting in touch

uproot is developed by [Max R. P. Grossmann](https://max.pm/) and [Holger Gerhardt](https://www.econ.uni-bonn.de/iame/gerhardt).

- **Source code**: [github.com/mrpg/uproot](https://github.com/mrpg/uproot)
- **Examples**: [github.com/mrpg/uproot-examples](https://github.com/mrpg/uproot-examples)
- **Mailing list**: Contact [max@uproot.science](mailto:max@uproot.science) to join
