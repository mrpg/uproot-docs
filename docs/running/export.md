# Exporting data

uproot stores every piece of data your experiment collects in an [append-only log](../building/data.md) — nothing is ever overwritten or lost. When you download your data, you don't have to pick and choose: you always get a single ZIP archive (the *data briefcase*) that contains your session's complete data in all key formats, ready for Excel, R, or Python.

This page shows you how to download that ZIP and how to analyze its contents. If you want to automate exports, work with the REST API, or analyze the database directly in Python, see [Advanced data access](export-advanced.md).

## Downloading your data

On a session's page in the admin interface, click **Download data**. You'll see a short form:

- **Latest × Field(s)** *(optional)* — adds an extra format with one row per player per grouping you specify (for example, one row per player per `round`). Leave it unchecked if you're not sure; you can always download again.
- **File type** — **CSV** (opens in Excel and every stats package) or **JSONL** (preserves data types; see [CSV or JSONL?](#csv-or-jsonl) below).
- **Apply reasonable filters** — checked by default; cleans up uproot-internal fields so your data focuses on what your experiment actually collected.

Click **Download** and you'll receive one ZIP file named after the session and the current date, for example `mysession_2026-07-04_1412.zip`.

## What's inside the ZIP

Unpacking the ZIP gives you a single folder named after your session:

```
mysession/
├── README.txt        ← explains the contents, right inside the ZIP
├── SHA256SUMS        ← checksums for verifying your files
├── latest/
│   ├── player.csv
│   ├── group.csv
│   └── session.csv
├── sparse/
│   ├── player.csv
│   ├── group.csv
│   └── session.csv
└── ultralong/
    ├── player.csv
    ├── group.csv
    └── session.csv
```

Each subfolder contains the same data in a different *format* (explained below). Within each format, the data is split into one file per kind of storage:

| File | Contains |
|------|----------|
| `player.csv` | Data stored on players — usually what you want |
| `group.csv` | Data stored on groups (only if your session has groups) |
| `session.csv` | Session-level data |
| `model.csv` | [Custom data models](../advanced/models.md) (only if your apps use them) |

Each file only has columns for fields that actually occur in that kind of storage, so player files aren't cluttered with session-level columns and vice versa.

!!! tip "In a hurry?"
    **`latest/player.csv`** is the file most people want: one row per participant, one column per field, showing each field's final value.

If you checked **Latest × Field(s)**, there is one more folder, named after your grouping variables — for example `latest_by_round/` if you grouped by `round`.

## The three formats

Every briefcase contains the same underlying data at three levels of detail:

### latest — one row per player

One row per storage (e.g., per player), showing the most recent value of every field. This is the most compact format and what you'll typically use for analysis.

If you enabled **Latest × Field(s)**, the extra `latest_by_…/` folder contains one row per player *per combination of your grouping variables* — for example, each participant's state at the end of each round. This is ideal for panel-style analyses.

!!! note
    Grouped snapshots include every field known at that point in time — the grouping variables determine *when* snapshots are taken, not which columns they carry. Fields set before the grouping variable appear in the output as expected.

### sparse — one row per change, one column per field

Each row represents a single change. Every field has its own column, and only the field that changed at that moment is filled in. This produces a wide but mostly empty table. Useful when you want to reconstruct *how* values evolved but still prefer one column per field.

### ultralong — the raw event log

One row per field change, in full detail. Every time a field's value was set, there is a row recording what changed, when, and where in the code. This is the most detailed format and preserves the complete history — use it for temporal analyses, audits, or debugging.

## Understanding the columns

Columns that start with `!` come from uproot itself; they sort to the front and can never clash with your own field names. In `ultralong` files you'll find all of them:

| Column | Description |
|--------|-------------|
| `!storage` | Which storage this row belongs to (e.g., `player/mysession/9wpsj`) |
| `!field` | Field name |
| `!time` | Unix timestamp of the change |
| `!seq` | Sequence number of the change (for exact ordering) |
| `!context` | Code location that made the change |
| `!unavailable` | Whether this row marks a deletion |
| `!data` | The value |

`latest` files just have `!storage`, `!time`, and `!seq` (the time and sequence of the most recent change), followed by one column per field.

The last part of `!storage` is the participant's uproot name — `player/mysession/9wpsj` is participant `9wpsj` in session `mysession`.

## Reasonable filters

The **Apply reasonable filters** option (on by default) cleans up uproot-internal fields:

- Renames `_uproot_group` to `group` (with values like `group/mysession/g1`, matching the `!storage` column of `group.csv` — handy for merging, see below)
- Renames `_uproot_session` to `session`
- Keeps `_uproot_dropout` and `_uproot_settings`
- Removes all other internal `_uproot_*` fields

Turn filters off only if you need to inspect uproot's internal bookkeeping.

## CSV or JSONL?

**CSV** is the safe default: it opens directly in Excel, R, Python, Stata, and everything else. Booleans are written as `TRUE`/`FALSE`, missing values as empty cells, and lists or dictionaries as JSON text within the cell.

**JSONL** ([JSON Lines](https://jsonlines.org/) — one JSON object per line) is worth choosing when your data contains lists, dictionaries, or mixed types. Unlike CSV, it keeps the distinction between numbers, strings, booleans, and nested structures — no more guessing whether `"1"` is a number or a string. Both pandas and R read it with one line of code.

Whichever you choose, the briefcase has the same structure — just with `.jsonl` files instead of `.csv` files.

## Analyzing your data

You don't even have to unpack the ZIP: both R and Python can read individual files straight out of the archive, entirely in memory. The examples below assume you downloaded `mysession_2026-07-04_1412.zip` and that the session is called `mysession` — adjust the names accordingly. (Of course, if you prefer, you can also unpack the ZIP and read the files from disk; the reading code is the same, minus the ZIP part.)

=== "R"

    With base R, `unz()` opens a single file inside a ZIP as a connection — no extraction needed:

    ```r
    zipfile <- "mysession_2026-07-04_1412.zip"

    players <- read.csv(unz(zipfile, "mysession/latest/player.csv"),
                        check.names = FALSE)
    ```

    (`check.names = FALSE` keeps column names like `!storage` intact instead of mangling them to `X.storage`.)

    With **readr/dplyr**, `read_csv()` accepts the same connection and preserves column names by default:

    ```r
    library(readr)

    players <- read_csv(unz(zipfile, "mysession/latest/player.csv"))
    ```

    With **data.table**, let `fread()` pull the file out of the ZIP via the `unzip` command:

    ```r
    library(data.table)

    players <- fread(cmd = paste("unzip -p", zipfile, "mysession/latest/player.csv"))
    ```

    Column names starting with `!` are perfectly legal in R — just wrap them in backticks:

    ```r
    library(dplyr)

    players |>
        select(`!storage`, payoff) |>
        arrange(desc(payoff))
    ```

    **Merging players with their groups.** With filters applied, each player's `group` column matches the `!storage` column of `group.csv`:

    ```r
    library(dplyr)

    players <- read_csv(unz(zipfile, "mysession/latest/player.csv"))
    groups <- read_csv(unz(zipfile, "mysession/latest/group.csv"))

    full <- left_join(players, groups,
                      by = c("group" = "!storage"),
                      suffix = c("", ".group"))
    ```

    Or with data.table:

    ```r
    full <- merge(players, groups,
                  by.x = "group", by.y = "!storage",
                  suffixes = c("", ".group"))
    ```

    **JSONL** briefcases work exactly the same way, with jsonlite:

    ```r
    library(jsonlite)

    players <- stream_in(unz(zipfile, "mysession/latest/player.jsonl"))
    ```

=== "Python"

    Python's built-in `zipfile` module opens a single file inside a ZIP — no extraction needed — and **pandas** reads directly from it:

    ```python
    import zipfile
    import pandas as pd

    with zipfile.ZipFile("mysession_2026-07-04_1412.zip") as zf:
        with zf.open("mysession/latest/player.csv") as f:
            players = pd.read_csv(f)
    ```

    Column names starting with `!` require bracket notation:

    ```python
    players[["!storage", "payoff"]].sort_values("payoff", ascending=False)
    ```

    **Merging players with their groups.** With filters applied, each player's `group` column matches the `!storage` column of `group.csv`:

    ```python
    with zipfile.ZipFile("mysession_2026-07-04_1412.zip") as zf:
        with zf.open("mysession/latest/player.csv") as f:
            players = pd.read_csv(f)
        with zf.open("mysession/latest/group.csv") as f:
            groups = pd.read_csv(f)

    full = players.merge(groups, how="left",
                         left_on="group", right_on="!storage",
                         suffixes=("", "_group"))
    ```

    **JSONL** briefcases need just one extra argument:

    ```python
    with zipfile.ZipFile("mysession_2026-07-04_1412.zip") as zf:
        with zf.open("mysession/latest/player.jsonl") as f:
            players = pd.read_json(f, lines=True)
    ```

## Verifying your download

Every briefcase includes a `SHA256SUMS` file listing the checksum of every other file in the archive. To confirm that nothing was corrupted or modified — for instance, before archiving data for publication — run this inside the unpacked folder:

```bash
cd mysession
sha256sum -c SHA256SUMS
```

(On macOS, use `shasum -a 256 -c SHA256SUMS`.)

## Page times

Page times track when each player entered and left each page — useful for measuring response times. On the **Download data** page, click **Page times** under *Other data* to get a CSV with these columns:

| Column | Description |
|--------|-------------|
| `sname` | Session name |
| `uname` | Player name |
| `show_page` | Page index |
| `page_name` | Page class name |
| `entered` | Unix timestamp when the player entered the page |
| `left` | Unix timestamp when the player left the page |
| `context` | Round/context information |

## Going further

For everything beyond the download button, see [Advanced data access](export-advanced.md):

- Downloading briefcases automatically via the [REST API](../reference/admin-api.md)
- Streaming JSONL exports
- Full database backups with `uproot dump`
- Offline analysis of the database in Python with `uproot.read`
