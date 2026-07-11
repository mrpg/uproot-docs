# Why uproot?

If you have ever run a survey or collected data from human participants, you have relied on software to sit between you and your respondents — and you have probably run into its limitations: fragile JavaScript workarounds, "copy survey" as version control, rigid page sequences, and data-reshaping scripts for every single project.

The quality of the tools we use determines the quality of the science we can do. uproot was built on the conviction that your software should never be the weakest part of your study.

**In one paragraph:** uproot never overwrites your data and remembers where every value came from. It reruns identically years later. Participants see beautiful pages that adapt to any device and work with screen readers. Obvious things work without workarounds — refreshing a results page can never pay a bonus twice. It checks everything participants send on the server, where they cannot tamper with it. It handles real-time interaction, flexible page orders, and dropouts out of the box. And it is completely free and open source.

Each claim, explained so you can check it yourself:

## Your data tells its own story

**The advantage in one sentence: uproot never deletes or overwrites your data, and it remembers who changed what, when, and which line of your code did it.**

Most software stores your data like a whiteboard: when a value changes, the old one is erased. uproot stores it like a **lab notebook**: entries are permanent, every entry is dated, and new information is added on a new line. This is called an append-only log.

Concretely, every data change is recorded with three things: a timestamp, the value itself, and the exact place in your study's code that caused the change. If a participant's payoff was set to 10 by a function called `set_payoff()` on line 42, that fact is stored forever, next to the payoff itself. When a reviewer, a co-author, or your future self asks "where does this number come from?" — the data itself answers.

Two practical consequences experimenters will appreciate:

- Repeated rounds do not create dozens of duplicate columns, so you no longer write reshaping scripts before analysis.
- You can reconstruct any participant's complete state at any moment of the study, after the fact.

[:octicons-arrow-right-24: Storing and accessing data](building/data.md)

## Your experiment can be rerun, exactly, years later

**The advantage in one sentence: if you use uproot as intended — with the tool `uv` — anyone with a copy of your project folder can rerun your experiment with exactly the software you used, years later, with one command.**

[Reproducibility](https://en.wikipedia.org/wiki/Reproducibility) is a cornerstone of science, but with most platforms it is out of your hands: the platform updates whenever the vendor decides, and there is no record of what exactly you ran. A Qualtrics survey from 2022 runs on whatever Qualtrics is today.

With uproot, reproducibility is not an extra chore. It falls out of the normal workflow:

1. **Your project folder *is* your experiment.** Pages, logic, texts, and settings all live in one ordinary folder that you can copy, archive, and share.
2. **A file in that folder, `uv.lock`, lists the exact version of every piece of software your project uses** — uproot itself and everything underneath it. Think of it as a receipt for your software environment. It is written automatically; you never edit it.
3. **One command, `uv sync`, reinstalls exactly what is on that receipt.** Not "the current version" — *your* version. On your laptop, on a lab server, or on a replicator's machine in 2031.
4. **Nothing updates behind your back.** Your environment changes only when you explicitly ask for an upgrade. Mid-study, it stays frozen.
5. **No hidden moving parts.** uproot ships all browser assets (fonts, styling, JavaScript libraries) inside the package itself, so your study does not silently depend on external servers that may change or vanish.

Together with the permanent data log above, this covers both halves of a replicable experiment: the *software* that produced your data, and the *complete history* of the data itself.

!!! tip "The one habit that makes it work"

    Keep `uv.lock` together with your project — under version control, in your archive, in your replication package. `uproot setup` initializes a [Git](https://git-scm.com/) repository for you, and `uv.lock` belongs in it. That is the entire discipline required.

## A polished interface that everyone can use — on any device

**The advantage in one sentence: your participants see beautiful, professional pages that work equally well on a laptop, a phone, or a screen reader — and you get all of this without doing any design work.**

Building a good-looking study usually means fiddling with layouts, testing on phones, and hoping nothing breaks. In uproot, you describe *what* you want to ask, and the framework takes care of *how it looks*. A seven-point happiness scale, with labeled endpoints, is this — and nothing more:

```python
happiness = LikertField(
    label="How happy are you today?",
    min=1, max=7,
    label_min="Not at all happy",
    label_max="Very happy",
)
```

On a desktop, this appears as a neat horizontal scale. On a phone, the same scale automatically rearranges itself into a vertical layout that fits the screen — you never design two versions. The same is true for every page uproot produces: the interface is fully responsive, meaning it adapts itself to any screen size.

Harder things stay just as short. A whole Likert *matrix* — several questions sharing one scale, a layout that is notoriously painful elsewhere — is a single line. So are [file uploads](advanced/uploads.md), [sliders, and validated bank-account fields](reference/fields.md). You can see all of them live in the [input elements example](https://github.com/mrpg/uproot-examples/tree/master/input_elements).

And the pages work for *everyone*, because accessibility is built in rather than left as homework:

- Participants using screen readers hear every question, every explanation, and every error message read aloud correctly.
- Participants navigating by keyboard alone can skip past repeated content and operate every input.
- Time limits are announced to screen-reader users, not just shown visually.

(For the technically inclined: uproot's default templates implement this with standard [WAI-ARIA](https://www.w3.org/WAI/standards-guidelines/aria/) markup — labeled inputs, radio groups with accessible names, live announcements, and correctly marked-up dialogs and tables.)

This matters scientifically as well as ethically: participants who use screen readers, keyboards, or five-year-old phones belong in your sample. The visual foundation is [Bootstrap 5](https://getbootstrap.com/), bundled with uproot itself, so pages look consistent and professional out of the box.

[:octicons-arrow-right-24: Form fields](reference/fields.md)

## Obvious things work without workarounds

**The advantage in one sentence: on other platforms, perfectly ordinary needs — "pay this bonus once", "let participants go back", "repeat these pages" — require workarounds; in uproot, the obvious way is the correct way.**

!!! quote "The principle of verisimilitude"

    uproot follows the principle that **if something is hard, it's a bug.**

We call this the principle of *verisimilitude* — and the bug is not yours, it's uproot's. If an ordinary research need is hard to express, the framework is what gets fixed.

A concrete example. On other platforms, a common pattern is to add a €5 bonus when the results page is shown. The hidden flaw: every time the participant refreshes the page, the code runs again — and they receive another €5. Bugs like this have gone undetected for entire studies, and the standard fix is manual bookkeeping that every researcher must remember to write, every time. In uproot, no workaround is needed: its page lifecycle includes methods that are **guaranteed to run exactly once** per participant, no matter how often a page is reloaded. You write the natural code; the framework makes it correct.

The same philosophy runs through everything else on this page: back buttons, randomized blocks, repeated rounds, dropout handling — things a researcher obviously needs — are built in, not bolted on with tricks.

[:octicons-arrow-right-24: Page methods](reference/page-methods.md)

## Participants cannot tamper with your study

**The advantage in one sentence: everything a participant sends is checked on the server, where participants have no access — not in their browser, where they do.**

On platforms whose logic runs in the participant's browser, a tech-savvy participant can open the developer tools and modify any value — payoffs, treatments, answers. There is no way to prevent this, because the checking happens on hardware the participant controls.

In uproot, the server decides what is valid. Every piece of data a participant sends is validated against the types declared in your code before it reaches your logic:

```python
@live
async def bid(page, player, price: float):
    player.bid = price
```

This says: the `bid` action accepts one thing, a number. Anything else — text, malformed data, manipulated requests — is rejected before your study logic ever sees it. You get this protection by writing ordinary Python; no security expertise required.

[:octicons-arrow-right-24: Live methods](building/live-methods.md)

## Real interaction between participants, built in

**The advantage in one sentence: participants can interact live — chat, trade, draw, negotiate — because uproot keeps a permanent connection to every participant's browser.**

Updates appear on participants' screens instantly, without page reloads. This is not a bolted-on extra; it is the foundation the framework is built on. Working examples you can run today include a [double auction](https://github.com/mrpg/uproot-examples/tree/master/double_auction) with live order books, a [collaborative drawing board](https://github.com/mrpg/uproot-examples/tree/master/drawing_board), and [built-in chat](multiplayer/chat.md) with pseudonyms for anonymity.

uproot also notices when a participant disconnects and lets you [decide what happens next](advanced/dropouts.md) — and groups are formed based on who actually shows up, not who signed up.

[:octicons-arrow-right-24: Multiplayer experiments](multiplayer/groups.md)

## Your design is not forced into a fixed pipeline

**The advantage in one sentence: the order of pages is a list your code can change while the study runs — so back buttons, adaptive designs, and randomized blocks are normal, not workarounds.**

On most platforms, participants march through a fixed sequence of pages, forward only. In uproot, the [page order](building/pages.md) can change at runtime: participants can [go back and revise answers](https://github.com/mrpg/uproot-examples/tree/master/revise), pages can appear or disappear based on earlier choices, and common designs are one line:

```python
page_order = [Hello, Random(Page1, Page2), Rounds(Task, Feedback, n=4), Bye]
```

This line shows two pages in random order, then repeats a task-and-feedback block four times. Randomized blocks, between-subjects treatments, and indefinite repetition (for random stopping rules — without deception!) are all built in.

[:octicons-arrow-right-24: SmoothOperators](building/operators.md)

## Full control on the day of your study

**The advantage in one sentence: when a live session hits a problem, you can fix it from the admin interface — per participant, in real time — instead of aborting the session.**

From the admin interface you can advance, revert, reload, or regroup individual participants, message anyone privately, and watch everyone's progress live, filtering and sorting by any data field. If a participant's browser throws an error, uproot captures it automatically, with full context — you find out during the session, not after.

When the study is done, your data exports in [four formats](running/export.md) matched to different analyses — from "one row per participant" to the complete event-by-event history.

[:octicons-arrow-right-24: The admin interface](running/admin.md)

## Built for the AI age

**The advantage in one sentence: you can describe a study in plain language and have an AI coding assistant generate a working uproot version of it.**

Studies are written in [Python](https://www.python.org/) and HTML — the two languages with the broadest ecosystem support, and the ones AI coding assistants handle best. The [uproot skill](https://github.com/mrpg/uproot-skill) gives assistants such as [Claude Code](https://claude.com/claude-code) access to the full documentation and all examples, so "build a [public goods game with punishment](https://github.com/mrpg/uproot-examples/tree/master/pgg_punishment) for 4 players" produces a working study you then review and refine. The same mechanism can convert existing Qualtrics, z-Tree, or oTree studies.

The 65+ examples are also yours in the fullest sense: licensed under [0BSD](https://opensource.org/license/0bsd), meaning you may copy, modify, and use them without restriction or attribution.

:material-github: [Browse the examples](https://github.com/mrpg/uproot-examples)

## Free, open, and yours

**The advantage in one sentence: uproot costs nothing, hides nothing, and locks you into nothing.**

uproot is 100% [Free/Libre Open Source Software](https://www.gnu.org/philosophy/free-sw.html) — you have the [four freedoms](https://www.gnu.org/philosophy/free-sw.html#four-freedoms): to run, study, share, and improve the software, guaranteed by the [LGPL](https://www.gnu.org/licenses/lgpl-3.0.html). There are no license fees, no per-response pricing, and no vendor who can retire a feature you depend on. You can inspect [every line of the code](https://github.com/mrpg/uproot), host it on your own infrastructure (a small server is plenty — the default database is [SQLite](https://sqlite.org/), which requires zero setup), and extend it freely.

## See for yourself

Three commands and you have a running study on your own machine:

[:octicons-arrow-right-24: Installation](getting-started/installation.md)
