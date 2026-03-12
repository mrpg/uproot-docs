# Page methods

TODO: Complete reference for all page methods.

Methods to document:

- show(player) — whether to show the page
- templatevars(player) — data for the template
- fields(player) — dynamic form fields
- validate(player) — custom validation
- timeout(player) — page timeout in seconds
- timeout_reached(player) — called on timeout
- may_proceed(player) — whether player can advance
- before_once(player) — runs once before showing
- before_always_once(player) — runs once before (no cache)
- after_once(player) — runs once after submission
- after_always_once(player) — runs once after (no cache)
- jsvars(player) — variables passed to JavaScript

For each method:
- When it's called
- Parameters
- Return value
- Example usage
