# Deployment

This page covers deploying uproot experiments for production use.

## Self-hosted with nginx (recommended)

The recommended way to run uproot in production is behind an nginx reverse proxy. This setup gives you full control and works well on any VPS or dedicated server. **We strongly recommend that you use a VPS with Debian 13+.** (While uproot itself works flawlessly on Ubuntu, using Ubuntu is in general considered bad practice. uproot also works on OpenBSD.)

!!! tip "New to VPS deployment?"
    If you're setting up a server from scratch, follow the [complete VPS setup guide](vps-setup.md) — it covers everything from getting a VPS to a working HTTPS setup, step by step.

!!! warning "HTTPS required"
    uproot requires HTTPS in production. Many browser features (like the secure cookies needed for accessing the admin area) only work over HTTPS. Use [Let's Encrypt](https://letsencrypt.org/) with `certbot` to get free TLS certificates.

### Running uproot

The simplest approach is a tmux session that persists after you disconnect:

```bash
tmux new -s uproot
uproot run  # or: uv run uproot run
```

Detach with `Ctrl+B` then `D`. Reattach later with `tmux attach -t uproot`.

For a more robust setup that survives reboots automatically, the [VPS setup guide](vps-setup.md#start-uproot-on-boot) shows how to create a systemd user service instead.

uproot listens on port 8000 by default. Use `--port` to change it if needed.

### nginx configuration

Configure nginx as a reverse proxy. The WebSocket upgrade headers are required for real-time features. The following example config (to be added within an existing `http` block) is battle-tested and has been proven to work reliably:

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ""      close;
}

server {
    server_name example.com;  # Adjust this

    listen 443 ssl;
    listen 443 quic;
    listen [::]:443 ssl;
    listen [::]:443 quic;
    http2 on;
    add_header Alt-Svc 'h3=":443"; ma=86400';

    ssl_certificate PATH_TO_fullchain.pem;  # Adjust this
    ssl_certificate_key PATH_TO_privkey.pem;  # Adjust this

    location / {
        proxy_pass http://127.0.0.1:8000;  # Maybe adjust this
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Front-End-Https on;
        proxy_set_header X-Forwarded-Protocol https;
        proxy_set_header X-Forwarded-Ssl on;
        proxy_set_header X-Url-Scheme https;
        proxy_buffering off;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
}
```

### Hosting in a subdirectory

uproot can run in a subdirectory instead of at the root. Set the `UPROOT_SUBDIRECTORY` environment variable and adjust your nginx location block:

```bash
export UPROOT_SUBDIRECTORY=/u/
uproot run  # or: uv run uproot run
```

```nginx
location /u/ {  # ONLY THIS CHANGES
    proxy_pass http://127.0.0.1:8000;  # same as above
    # ... same proxy settings as above ...
}
```

## Fly.io with SQLite

[Fly.io](https://fly.io/) is an excellent platform for deploying uproot experiments. It provides excellent support for long-running WebSocket connections, works seamlessly with uproot's architecture, and uses SQLite for simple, reliable data persistence.

!!! tip "Why Fly.io?"
    - Full support for WebSocket connections and real-time features
    - Works with uproot's default SQLite database (no additional setup needed)
    - Simple pricing with generous free tier
    - Regional deployment for lower latency
    - Native support for persistent volumes

### Prerequisites

1. Create a [Fly.io account](https://fly.io/app/sign-up)
2. Install the [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/):

=== "macOS / Linux"
    ```bash
    curl -L https://fly.io/install.sh | sh
    ```

=== "Windows (PowerShell)"
    ```powershell
    powershell -ExecutionPolicy ByPass -c "iwr https://fly.io/install.ps1 -useb | iex"
    ```

3. Log in to Fly:

```bash
fly auth login
```

### Deploy your experiment

Navigate to your uproot project directory and run:

```bash
fly launch
```

Fly will detect your Python application and guide you through the setup. When prompted:

- Choose an app name or let Fly generate one
- Choose a region close to your participants
- Decline PostgreSQL when asked (uproot uses SQLite by default)
- Decline Redis when asked

This creates a `fly.toml` configuration file. Edit it to ensure the correct settings:

```toml
app = "your-app-name"
primary_region = "iad"  # or your chosen region

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "off"  # Keep WebSocket connections alive
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
```

### Adding persistent storage for SQLite

Create a persistent volume to ensure your SQLite database survives app restarts:

```bash
fly volumes create uproot_data --region iad --size 1
```

Update your `fly.toml` to mount the volume:

```toml
[mounts]
  source = "uproot_data"
  destination = "/data"
```

Then modify your `main.py` to use the persistent storage location:

```python
import os

# Add this near the top of your main.py
if os.getenv("FLY_APP_NAME"):
    # Running on Fly.io, use persistent volume
    os.environ["UPROOT_DB_PATH"] = "/data/uproot.sqlite3"
```

### Deploy

Deploy your application:

```bash
fly deploy
```

After deployment completes, Fly will show your app's URL. Open it in your browser:

```bash
fly open
```

### Setting up the admin account

Since auto-login only works on localhost, you'll need to set a password for the admin account. Edit your `main.py`:

```python
import uproot.deployment as upd

# Replace the ... with a secure password
upd.ADMINS["admin"] = "your-secure-password-here"
```

Then redeploy:

```bash
fly deploy
```

### Monitoring and logs

View your app's logs:

```bash
fly logs
```

Check app status:

```bash
fly status
```

Access the admin interface at `https://your-app-name.fly.dev/admin/`

## Railway

[Railway](https://railway.app/) is another excellent option that auto-detects uproot's `Procfile` and requires minimal configuration. It's particularly good for quick deployments.

### Advantages

- Zero-config deployment (detects `Procfile` automatically)
- Built-in PostgreSQL support if needed
- Simple GitHub integration

### Quick start

1. Sign up at [railway.app](https://railway.app/)
2. Connect your GitHub repository
3. Railway auto-deploys your app
4. Set `UPROOT_ORIGIN` environment variable to your Railway domain

## Heroku

Heroku provides a straightforward way to deploy uproot experiments with PostgreSQL. Note that Heroku requires PostgreSQL and doesn't support persistent SQLite storage.

!!! warning "WebSocket connection instability"
    Heroku's router has a [55-second idle timeout](https://devcenter.heroku.com/articles/request-timeout) for streaming connections including WebSockets. If no data is transmitted for 55 seconds, the connection is terminated. This can cause issues in uproot experiments where participants may be inactive for longer periods (reading instructions, thinking, waiting for others). Consider using Fly.io or Railway for more stable WebSocket support.

### Prerequisites

1. Create a [Heroku account](https://signup.heroku.com/)
2. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
3. Log in to Heroku:

```bash
heroku login
```

### Deploy your experiment

First, edit your `pyproject.toml` to include PostgreSQL support:

```toml
dependencies = [
    "uproot-science[pg] @ git+https://github.com/mrpg/uproot.git@main",
]
```

Create an `app.json` file in your project root:

```json
{
  "name": "Uproot Project",
  "description": "An uproot-based web application for behavioral science experiments",
  "keywords": ["python", "uproot", "experimental-economics", "behavioral-science"],
  "buildpacks": [
    {
      "url": "heroku/python"
    }
  ],
  "formation": {
    "web": {
      "quantity": 1,
      "size": "basic"
    }
  },
  "addons": [
    {
      "plan": "heroku-postgresql:essential-0"
    }
  ],
  "env": {
    "UPROOT_ORIGIN": {
      "description": "The public URL of your app (e.g., https://your-app-name.herokuapp.com). Auto-detected if you enable 'heroku labs:enable runtime-dyno-metadata'. Override for custom domains.",
      "required": false
    }
  }
}
```

Then deploy:

```bash
# Create a new Heroku app
heroku create my-experiment-name

# Enable runtime metadata
heroku labs:enable runtime-dyno-metadata

# Provision PostgreSQL
heroku addons:create heroku-postgresql:essential-0

# Deploy
git push heroku main
```
