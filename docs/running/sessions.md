# Sessions

Sessions and rooms are the two main concepts for managing how participants access your experiment. A **session** is a running instance of an experiment config, containing players and their data.

Kindly note that [rooms](rooms.md) give you much more control over participant entry.

A session is created from a [config](../getting-started/project-structure.md) and holds all experiment state: players, groups, models, and data. Each session has a unique session name (a short random string by default) and is associated with exactly one config.

## Creating a session directly

From the admin interface, navigate to **Sessions** and create a new session by selecting a config and specifying the number of players. This gives you a session with pre-created player slots that you can distribute manually.

Each pre-created player gets a unique URL of the form:

```
https://your-server.com/p/{session_name}/{player_name}/
```

You can share these URLs with participants individually. This approach works well for small experiments or when you want to assign specific participants to specific slots.

## Session initialization

A session is initialized the first time a player loads their first page. Initialization runs the `new_session` callback in each app (if defined), followed by `new_player` for that player. If you created the session manually with pre-created players, you can also trigger initialization explicitly via the admin API using the `run_new_session` and `run_new_player` endpoints.
