# uproot

**uproot** is a modern, open-source framework for developing and conducting browser-based behavioral experiments. Build studies with hundreds of participants, from simple surveys to complex real-time multiplayer games.

[:material-play-circle:&#x202F; **Try the live demo**](https://demo.uproot.science){ .fw-500 .my-2 .md-button .md-button--primary }

:material-github: **Source code:** [github.com/mrpg/uproot](https://github.com/mrpg/uproot) <br>
:material-github: **Examples:** [github.com/mrpg/uproot-examples](https://github.com/mrpg/uproot-examples)

!!! warning "Work in progress"

    uproot is in initial development. Breaking changes may occur between releases. The announce&shy;ments shown in the admin interface will tell you when action is needed.

<div class="grid cards mt-4" markdown>

-   :material-download:{ .card-title-icon .lg .middle } __Get started in minutes__

    ---

    Install uproot with a single command and create your first experiment.
    {: .fs-95 .text-opacity-55}

    [:material-arrow-right-circle: Installation](getting-started/installation.md)
    {: .fs-95}

-   :material-book-open-variant:{ .card-title-icon .lg .middle } __Learn by doing__

    ---

    Follow the tutorial to build a complete prisoner’s dilemma experiment.
    {: .fs-95 .text-opacity-55}

    [:material-arrow-right-circle: Tutorial](getting-started/tutorial.md)
    {: .fs-95}

-   :material-account-group:{ .card-title-icon .lg .middle } __Built for multiplayer__

    ---

    Group participants, synchronize progress, and enable real-time interaction.
    {: .fs-95 .text-opacity-55}

    [:material-arrow-right-circle: Multiplayer experiments](multiplayer/groups.md)
    {: .fs-95}

-   :material-folder-open:{ .card-title-icon .lg .middle } __Explore examples__

    ---

    Ready-to-use experiments covering common paradigms and techniques.
    {: .fs-95 .text-opacity-55}

    [:material-arrow-right-circle: Example apps](https://github.com/mrpg/uproot-examples)
    {: .fs-95}

-   :material-robot-outline:{ .card-title-icon .lg .middle } __AI-assisted development__

    ---

    Build experiments faster with Claude Code, Codex, and other agentic coding tools.
    {: .fs-95 .text-opacity-55}

    [:material-arrow-right-circle: Set up AI tooling](getting-started/installation.md#set-up-ai-assisted-development)
    {: .fs-95}

</div>

## Why uproot?

- **Reproducible experiments:** Your project folder plus `uv` recreates the exact software environment of your study, years later.
- **Real-time multiplayer:** Built-in support for grouping participants, synchronization, and live interactions.
- **Flexible data storage:** Append-only log ensures data persistence and supports arbitrary data types.
- **Modern stack:** Built on [FastAPI](https://fastapi.tiangolo.com/) for performance and reliability.
- **100% open source:** LGPL-licensed with no vendor lock-in.

[:material-arrow-right-circle: **The full case for uproot**](why-uproot.md)

## Quick example

Here is the core logic of a prisoner’s dilemma experiment:

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

[:material-github: Browse the complete example](https://github.com/mrpg/uproot-examples/tree/master/prisoners_dilemma) including HTML templates

## Getting in touch

uproot is developed by **[Max Grossmann](https://max.pm/)** and **[Holger Gerhardt](https://www.econ.uni-bonn.de/iame/gerhardt)**. Click [here](legal.md) for more information.
