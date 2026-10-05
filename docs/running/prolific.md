# Running on Prolific

[Prolific](https://www.prolific.com/) is a platform for recruiting online participants. Prolific sends each participant to a URL you provide, and when they finish, they come back to Prolific with a *completion code* that tells Prolific to pay them. uproot needs very little setup for this: one room, one URL parameter, and one link at the end of your experiment.

This page assumes you have read [Sessions and rooms](rooms.md) and know how to create a session in [the admin interface](admin.md).

## The setup at a glance

1. Create a room with `labels=[]` and no capacity, in the admin interface or in `main.py`.
2. In the admin, create a session in that room with **0 players** and put your completion code in the session settings. This opens the room.
3. Give Prolific the room URL, with the participant’s Prolific ID in `?label=`.
4. End your experiment with a “Finish study” link that sends participants to Prolific with the completion code.

Each step is explained below.

## Step 1: Create the room

You can create the room in the admin interface or in your project’s `main.py`. Both give you the same room.

=== "Admin interface"

    Go to **Rooms** in the admin and create a new room:

    - **Room name:** for example, `my_study`.
    - **Associate with a particular config:** check this and select your config.
    - **Start this config immediately:** leave this unchecked (see below).
    - **Use labels/Access Codes:** check this, but leave the **Labels** box **empty**.
    - **Limit capacity of resulting session:** leave this unchecked.

=== "main.py"

    ```python
    upd.DEFAULT_ROOMS.append(
        room(
            "my_study",
            config="my_experiment",
            labels=[],
            open=False,
        )
    )
    ```

    Rooms defined this way are created automatically when the server starts.

An empty label list (`labels=[]`) means “every participant needs a label, and any non-empty label is accepted.” No capacity is set, so the room has no upper limit. Every participant who arrives gets a new player slot in the session.

The room starts out closed. You open it in Step 2 by creating the session. Until then, anyone who visits the room URL sees a waiting page. If the room were already open, the first visitor would make uproot create a session automatically, without the completion code you are about to enter.

### Why `labels=[]` and not the default

A room with the default `labels=None` would also accept everyone, and it would also store a `?label=` it finds in the URL (see [Eagerly accepted labels](rooms.md#eagerly-accepted-labels)). But `labels=[]` is the better choice for Prolific, for two reasons:

- **Every player gets a Prolific ID.** If the label is missing from the URL (for example, because the participant copied the link by hand), uproot shows a page that asks for an access code instead of letting the participant in anonymously. You never end up with a player you cannot match to a Prolific submission.
- **Participants cannot start twice.** If someone opens the study link again—after closing the tab, after a crash, or on a different device—uproot sees the same label and sends them back to their existing player slot. They continue where they left off instead of starting over in a fresh slot.

Prolific IDs consist only of letters and digits, so they are valid labels (labels may contain `A-Za-z0-9-._`, up to 128 characters).

### Why no capacity

It is tempting to set `capacity` to the number of places in your Prolific study. Do not do that. On Prolific, participants regularly return a study or time out, and Prolific then offers their place to someone new. The returned participant’s player slot still counts toward the room’s capacity, so a capacity equal to your number of places would lock out the replacements. Let Prolific control how many people take part. If you need to stop admissions, [close the room](rooms.md#closing-and-reopening-a-room) instead.

## Step 2: Create a session with 0 players

On the room’s admin page, use the “Create session” form:

- **Number of players:** `0`. Player slots are created as participants arrive, so you do not need any in advance.
- **Settings (JSON):** your completion code, which you copy from your study’s page on Prolific:

    ```json
    {"completion_code": "C1ABC2DE"}
    ```

- **“Set room capacity to number of players”:** leave this **unchecked**.

Creating the session opens the room, so participants can join from now on.

!!! warning "Do not check “Set room capacity to number of players”"
    With 0 players, this option sets the room’s capacity to 0. Every participant then sees a “Room full” page, and nobody can join. If this has already happened, go to the room’s admin page, open **Actions**, uncheck **Limit capacity**, and click **Set**. This removes the limit while the session keeps running. You can do the same via the [admin REST API](../reference/admin-api.md#patch-adminapiv1roomsroomnamecapacity).

Why create the session by hand instead of letting the room create one automatically? Because the admin form lets you enter [session settings](../building/data.md#session-settings). Keeping the completion code in the session settings, rather than in your code, has two advantages: the code never ends up in a public Git repository, and you can run several Prolific studies (each with its own code) from the same project. If you mistype the code, fix it on the session page with **Update settings**.

If you prefer, you can instead give the code as a default via [`load_config(..., settings={"completion_code": "C1ABC2DE"})`](../getting-started/project-structure.md) and let the room create the session automatically when the first participant arrives.

## Step 3: Give Prolific the study URL

In your Prolific study, enter the room URL as the study URL, and choose the option to [record Prolific IDs via URL parameters](https://researcher-help.prolific.com/en/articles/445178-what-survey-experimental-software-is-compatible-with-prolific). Prolific suggests a parameter named `PROLIFIC_PID`. Rename it to `label`:

```
https://your-server.com/room/my_study/?label={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}
```

Prolific replaces `{{%PROLIFIC_PID%}}` with each participant’s ID. uproot reads only `label`. The `STUDY_ID` and `SESSION_ID` parameters are harmless, but uproot does not store them, so you can also drop them. For [bonus payments](#bonus-payments), you can find the corresponding submission ID in Prolific’s demographic export.

Open the URL yourself with a made-up label, such as `?label=TEST1`, to check that everything works before you publish the study. Your test player appears in the session like any other player.

## Step 4: Send participants back to Prolific

[Prolific’s completion URL](https://researcher-help.prolific.com/en/articles/445178-what-survey-experimental-software-is-compatible-with-prolific) has the form `https://app.prolific.com/submissions/complete?cc=YOUR_CODE`. Put a link to it on the last page of your experiment:

```html+jinja
{% extends "Base.html" %}

{% block main %}
<p>Thank you for taking part!</p>

<p>
    <a class="btn btn-primary" href="https://app.prolific.com/submissions/complete?cc={{ session.settings.get('completion_code', 'NOCODE') | urlencode }}">Finish study</a>
</p>
{% endblock main %}

{% set buttons = False %}
```

The participant clicks the link, lands on Prolific, and their submission is marked as complete.

Note `.get('completion_code', 'NOCODE')`: if you forget to set the code, or test the app on its own (via its `~app` config, which has [no settings](../getting-started/project-structure.md)), the page still works. Prolific then receives the code `NOCODE`, which it does not recognize, so you notice the mistake and can review those submissions by hand.

!!! note "Put the link on the last page"
    The participant should click “Finish study” only after uproot has saved all their data. Put the link on a page after your last form, not on a page with form fields, because a link does not submit the form.

## Working with the data

Every player’s Prolific ID is stored as their `label`. When you [export your data](export.md), the `label` column lets you [match your experimental data to Prolific’s demographic data](https://researcher-help.prolific.com/en/articles/445210-matching-data-between-prolific-and-your-external-study-software).

The label check works within one session only. If the same person could take part in two of your studies (for example, a pilot and the main study, each with its own room and session), use [Prolific’s filter that excludes participants of previous studies](https://researcher-help.prolific.com/en/articles/445164-how-can-i-prevent-specific-participants-from-accessing-my-study).

## Advanced: bonus payments and screen-outs

The two recipes below need a bit more code. They are good tasks for a coding agent (such as Claude Code or Codex): describe your experiment and point the agent at this page.

### Bonus payments

[Prolific’s bulk bonus form](https://researcher-help.prolific.com/en/articles/445233-how-do-i-send-bonus-payments) takes one line per submission: its submission ID and bonus amount, separated by a comma. uproot stores the participant ID as `player.label`. You can match it to the submission ID in [Prolific’s demographic export](https://researcher-help.prolific.com/en/articles/445209-exporting-prolific-demographic-data). Suppose your app saves each participant’s bonus as `player.bonus`. A [pipeline](admin.md#pipeline) exports the participant IDs and amounts:

```python
def pipeline(session):
    rows = []

    for player in session.players:
        bonus = player.within(app=__name__).get("bonus")

        if player.label and bonus:
            rows.append(dict(prolific_id=player.label, amount=f"{bonus:.2f}"))

    return rows
```

Run the pipeline from the session page in the admin and download its table. On Prolific, click **Download demographic data** for your study. Match each `prolific_id` in the pipeline output to the **Participant ID** in that download, then take the corresponding **Session ID** (the submission ID). In Prolific’s **Bulk actions** → **Bulk bonus payment**, paste one line per bonus as `<submission ID>,<amount>`, without a header row. Amounts are in your study’s currency.

### Screen-outs

Sometimes participants should leave early, for example because they do not consent or fail an attention check. Prolific lets you define [several completion codes per study](https://researcher-help.prolific.com/en/articles/445170-custom-completion-codes), each with its own action (such as approving the submission, or asking the participant to return it). Put all codes in the session settings:

```json
{"completion_code": "C1ABC2DE", "screenout_code": "C9XYZ8WV"}
```

If your app saves the outcome as `player.passed_attention_check`, pick the right code on the final page:

```html+jinja
{% if player.passed_attention_check %}
    {% set cc = session.settings.get("completion_code", "NOCODE") %}
{% else %}
    {% set cc = session.settings.get("screenout_code", "NOCODE") %}
{% endif %}

<a class="btn btn-primary" href="https://app.prolific.com/submissions/complete?cc={{ cc | urlencode }}">Finish study</a>
```

To send screened-out participants to the final page right away, skip the remaining pages with a [`show`](../building/pages.md) method, or use [`move_to_page`](../reference/api.md#move_to_page) to send them to that page.
