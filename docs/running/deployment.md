# Deployment

This page explains how to make your experiment accessible over the internet. It assumes you have [installed uproot and created a project](../getting-started/installation.md).

Choose the option that suits you:

1. **[Use Cloudflare](#option-1-use-cloudflare).** If you have a computer with a stable, high-bandwidth internet connection, run uproot there and let Cloudflare connect participants to it. The same approach also works on a VPS.
2. **[Self-host on your own VPS](#option-2-self-host-on-your-own-vps).** A virtual private server (VPS) is a rented computer that you manage remotely. Use nginx and Let’s Encrypt for full control over your web server and HTTPS setup—no third-party service touches participant traffic.
3. **[Use a hosting service](#option-3-use-a-hosting-service).** Deploy to Fly.io, Railway, Render, or Heroku using the instructions below.

## Option 1: Use Cloudflare

[Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/) connects your computer to Cloudflare, which forwards participants’ requests to uproot. Your experiment and database stay on your computer. Cloudflare provides the public [HTTPS](https://developer.mozilla.org/en-US/docs/Glossary/HTTPS) address, which encrypts the browser connection, without requiring you to configure nginx, certificates, or port forwarding on your router.

### Try it for free

[TryCloudflare](https://try.cloudflare.com/) gives you a temporary public address for free, without a Cloudflare account or your own domain name.

First, :material-github: [install `cloudflared` for your operating system](https://github.com/cloudflare/cloudflared#installing-cloudflared) and set an [admin password](admin.md#authentication). In your project directory, [start uproot](../reference/cli.md#uproot-run):

```bash
uv run uproot run
```

In a second terminal on the same computer, run:

```bash
cloudflared tunnel --url http://localhost:8000
```

The command prints a public address such as `https://random-words.trycloudflare.com`. Leave the tunnel running. In your project’s [`.env` file](../getting-started/project-structure.md), add or update this line, replacing the example with the address you received:

```text
UPROOT_ORIGIN=https://random-words.trycloudflare.com
```

This tells uproot which public address to use for links. uproot reads `.env` at startup, so stop it with ++ctrl+c++ in its terminal, then run `uv run uproot run` again to pick up the change. Open the public address followed by `/admin/`, sign in, and create a [session or room](rooms.md). Share the participant links from the admin interface.

Keep both terminals running and prevent the computer from sleeping while anyone is using the experiment. Its internet connection needs sufficient **upload bandwidth**, since your computer sends the experiment’s pages and files to participants. If you restart the Quick Tunnel, update `UPROOT_ORIGIN` with its new address and restart uproot before sharing new links.

!!! note "For testing"
    Cloudflare’s [Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/) are intended for testing and development. They have no uptime guarantee and a limit of 200 simultaneous requests. For collecting research data, use a permanent tunnel as described below.

### Use a permanent address for production

For a stable address such as `https://study.example.com`, follow Cloudflare’s [tunnel setup guide](https://developers.cloudflare.com/tunnel/get-started/). You need a Cloudflare account and a domain name added to it. Give the tunnel a name, choose your public hostname, and point it to `http://localhost:8000`. Update `UPROOT_ORIGIN` to the public HTTPS address and restart uproot.

Permanent tunnels and custom hostnames are available on the free plan. For production use, we recommend a [paid Cloudflare plan](https://www.cloudflare.com/plans/pro/) for additional security features. See [current plans and pricing](https://www.cloudflare.com/plans/) before choosing. Payment is not required simply to name a tunnel or use your own domain.

Cloudflare publishes [GDPR safeguards and a data processing addendum](https://www.cloudflare.com/trust-hub/gdpr/). Because participant traffic passes through Cloudflare, your institution should assess whether the setup meets your study’s data-protection requirements.

!!! tip "Use the same setup on a VPS"
    You can also install uproot and `cloudflared` on a VPS and point a permanent tunnel to `http://localhost:8000` there. Cloudflare handles public HTTPS, saving you the nginx and Let’s Encrypt setup, and your experiment and database live on the VPS so your personal computer can be switched off.

    1. Follow the [VPS setup guide](vps-setup.md) to prepare the server.
    2. [Start uproot on boot](vps-setup.md#start-uproot-on-boot) with a systemd service.
    3. Use Cloudflare’s tunnel setup in place of the nginx and certificate steps.
    4. [Run `cloudflared` as a service](https://developers.cloudflare.com/tunnel/get-started/#create-a-tunnel) so it starts automatically.

## Option 2: Self-host on your own VPS

For full control over your deployment, run uproot behind [nginx](https://nginx.org/en/docs/beginners_guide.html), a web server that forwards requests to uproot as a *reverse proxy*. You manage the server, certificates, and software yourself. This is the most sovereign option: participants connect directly to your VPS, and you choose who provides the infrastructure. **We strongly recommend that you use a VPS with Debian 13+.** (While uproot itself works flawlessly on Ubuntu, using Ubuntu is in general considered bad practice. uproot also works on OpenBSD.)

!!! tip "New to VPS deployment?"
    If you are setting up a server from scratch, follow the [complete VPS setup guide](vps-setup.md). It covers everything from getting a VPS to a working HTTPS setup, step by step.

!!! warning "HTTPS required"
    uproot requires HTTPS in production. Many browser features (like the secure cookies needed for accessing the admin area) only work over HTTPS. Use [Let’s Encrypt](https://letsencrypt.org/) with [Certbot](https://certbot.eff.org/instructions) to get free TLS certificates—the credentials your web server uses to provide HTTPS.

### Running uproot

The simplest approach is a tmux session that persists after you disconnect:

```bash
tmux new -s uproot
uproot run  # or: uv run uproot run
```

Detach with ++ctrl+b++ then ++d++. Reattach later with `tmux attach -t uproot`.

For a more robust setup that survives reboots automatically, the [VPS setup guide](vps-setup.md#start-uproot-on-boot) shows how to create a systemd user service instead.

uproot listens on port 8000 by default. Use `--port` to change it if needed.

### nginx configuration

Configure nginx as a reverse proxy. [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) keep a connection open between the browser and server; the upgrade headers below are required for uproot’s [real-time features](../multiplayer/real-time.md). The following example config (to be added within an existing `http` block) is battle-tested and has been proven to work reliably:

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
        proxy_read_timeout 600s;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
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

If you want to serve uproot at a path like `https://example.com/my-study/` instead of the root, set the `UPROOT_SUBDIRECTORY` environment variable to your chosen path:

```bash
export UPROOT_SUBDIRECTORY=my-study  # use whatever path you want
uproot run
```

Leading and trailing slashes are stripped automatically, so `my-study`, `/my-study`, and `/my-study/` are all equivalent.

When set, uproot prefixes all routes with the subdirectory. Hence, participant pages, the admin interface, static files, and WebSocket connections all work without any further changes to your code or templates.

Then adjust your nginx config to match. Here is a complete example; the only difference from a root deployment is the `location` path:

```nginx
location /my-study/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_read_timeout 600s;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
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
```

The admin interface will be at `https://example.com/my-study/admin/`.

!!! tip "Persistent configuration"
    If you run uproot via a systemd service, set the variable in an environment file or in the service unit’s `Environment=` directive so it persists across restarts.

## Option 3: Use a hosting service

These services run uproot on infrastructure they manage. Choose [Fly.io](#flyio-with-sqlite), [Railway](#railway-with-sqlite), or [Render](#render-with-sqlite) to keep the default SQLite database, or [Heroku](#heroku) with PostgreSQL. Follow the storage instructions for your chosen service so that saved experiment data survives restarts.

### Fly.io with SQLite

[Fly.io](https://fly.io/) supports long-running WebSocket connections and persistent volumes, so you can run uproot with its default SQLite database. Fly charges for the Machines, volumes, and network traffic that you use; check its [current pricing](https://fly.io/docs/about/pricing/) before you deploy.

!!! tip "Why Fly.io?"
    - Full support for WebSocket connections and real-time features
    - Works with uproot’s default SQLite database on a persistent volume
    - Regional deployment for lower latency
    - Native support for persistent volumes

#### Prerequisites

1. Create a [Fly.io account](https://fly.io/app/sign-up)
2. Install the [Fly CLI](https://fly.io/docs/flyctl/install/):

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

#### Deploy your experiment

Navigate to your uproot project directory and run:

```bash
fly launch --no-deploy
```

The `--no-deploy` option is important: it lets you attach persistent storage before uproot starts for the first time. Fly will detect your Python application and guide you through the setup. When prompted:

- Choose an app name or let Fly generate one
- Choose a region close to your participants
- Do not add PostgreSQL or Redis if Fly offers them

This creates a `fly.toml` configuration file. Edit it to ensure the correct settings:

```toml
app = "your-app-name"
primary_region = "iad"  # or your chosen region

[build]
  builder = "paketobuildpacks/builder-jammy-base"

[env]
  PORT = "8080"
  UPROOT_SQLITE3 = "/data/uproot.sqlite3"
  UPROOT_ORIGIN = "https://your-app-name.fly.dev"

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

Replace `your-app-name` and `iad` with the app name and region selected by `fly launch`.
If you later add a custom domain, update `UPROOT_ORIGIN` to that domain.

#### Adding persistent storage for SQLite

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

The `UPROOT_SQLITE3` setting above points uproot at the mounted volume.

!!! warning "Use one Machine"
    A Fly volume is attached to one Machine and is not automatically replicated. Keep this SQLite deployment at one Machine; do not clone the Machine or scale it horizontally.

#### Set the admin password

New uproot projects use `upd.auto_login()` in `main.py`. Set the production password as a Fly secret so that it is not committed to Git:

```bash
fly secrets set UPROOT_ADMIN_PASSWORD='choose-a-long-random-password'
```

If your project does not already contain this line, add it to `main.py`:

```python
upd.ADMINS["admin"] = upd.auto_login()
```

#### Deploy

Deploy your application:

```bash
fly deploy
```

After deployment completes, Fly will show your app’s URL. Open it in your browser:

```bash
fly open
```

#### Monitoring and logs

View your app’s logs:

```bash
fly logs
```

Check app status:

```bash
fly status
```

Access the admin interface at `https://your-app-name.fly.dev/admin/`.

### Railway with SQLite

[Railway](https://railway.com/) can deploy an uproot project directly from GitHub. Its WebSocket connections are [exempt from inactivity timeouts](https://docs.railway.com/networking/public-networking/specs-and-limits), but its ordinary container disk is temporary. You must attach a [volume](https://docs.railway.com/volumes) for the SQLite database.

#### Quick start

1. Sign up at [railway.com](https://railway.com/) and create a project from your GitHub repository.
2. Open the uproot service’s **Settings** tab. Under **Deploy**, set the start command to `uproot run -h 0.0.0.0 -p $PORT`. This is the same command as the generated `Procfile`, but setting it explicitly avoids relying on [deprecated Procfile detection](https://railpack.com/config/procfile/).
3. Add a Railway volume to the service and set its mount path to `/data`.
4. Under **Networking**, select **Generate Domain**.
5. Under **Variables**, add the following values, replacing the example domain and password:

    ```text
    UPROOT_SQLITE3=/data/uproot.sqlite3
    UPROOT_ORIGIN=https://your-service.up.railway.app
    UPROOT_ADMIN_PASSWORD=choose-a-long-random-password
    ```

6. Deploy the staged changes, then open `https://your-service.up.railway.app/admin/`.

The password variable assumes that `main.py` contains `upd.ADMINS["admin"] = upd.auto_login()`, as current uproot projects do. Add that line if you have an older project.

Railway services with a volume [cannot use replicas and have a short period of downtime during a redeploy](https://docs.railway.com/volumes/reference). Do not redeploy while an experiment is running.

### Render with SQLite

[Render](https://render.com/) supports WebSockets without a fixed connection timeout and can attach a persistent disk to a paid web service. Do not use a free web service for a real experiment: free services cannot attach a disk, and their local SQLite files are [lost when the service restarts, redeploys, or spins down](https://render.com/docs/free#local-files-lost-on-redeploy).

#### Quick start

1. Sign up at [render.com](https://render.com/) and select **New > Web Service**.
2. Connect the Git repository that contains your uproot project and choose the **Python 3** runtime.
3. Set the build command to `pip install -r requirements.txt`.
4. Set the start command to `uproot run -h 0.0.0.0 -p $PORT`.
5. Choose a paid instance type. Under **Advanced**, add a persistent disk with the mount path `/var/data`.
6. Add the following environment variables, replacing the example service name and password:

    ```text
    UPROOT_SQLITE3=/var/data/uproot.sqlite3
    UPROOT_ORIGIN=https://your-service-name.onrender.com
    UPROOT_ADMIN_PASSWORD=choose-a-long-random-password
    ```

7. Create the web service. When the first deploy finishes, open `https://your-service-name.onrender.com/admin/`.

The password variable assumes that `main.py` contains `upd.ADMINS["admin"] = upd.auto_login()`, as current uproot projects do. Add that line if you have an older project. Render’s Python runtime uses the project’s `.python-version` file, so the file generated by uproot selects a compatible Python version. If you add a custom domain, update `UPROOT_ORIGIN` to its full `https://` URL.

!!! warning "Persistent-disk limitations"
    A Render persistent disk is available to only one service instance and [disables zero-downtime deploys](https://render.com/docs/disks#disk-limitations-and-considerations). This matches uproot’s single-process live state, but it means each deploy briefly stops the experiment. Keep one instance and do not deploy while participants are active. Render can also replace an instance during platform maintenance, which closes its [WebSocket connections](https://render.com/docs/websocket#faq).

### Heroku

Heroku can run uproot with PostgreSQL. A Heroku dyno’s local disk is temporary, so the default SQLite database is not suitable for production there.

!!! note "WebSocket timeout"
    Heroku supports WebSockets and applies a rolling [55-second idle timeout](https://devcenter.heroku.com/articles/websockets). uproot sends a heartbeat every 9 seconds, so a participant reading or waiting does not leave the connection idle long enough to hit that limit.

!!! warning "Dyno restarts"
    Heroku [restarts dynos at least daily](https://devcenter.heroku.com/articles/dyno-restarts), as well as after deploys and configuration changes. PostgreSQL keeps the saved data, but a restart interrupts active connections and in-process background tasks. Restart or deploy shortly before a scheduled experiment, and do not change the app while participants are active.

#### Prerequisites

1. Create a [Heroku account](https://signup.heroku.com/)
2. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
3. Log in to Heroku:

```bash
heroku login
```

#### Deploy your experiment

First, add PostgreSQL support to the project’s main dependencies:

```bash
uv add 'uproot-science[pg]<1'
```

This updates `pyproject.toml` and `uv.lock`. Current uproot projects also contain a `requirements.txt`, but Heroku’s Python buildpack [requires exactly one package-manager file](https://github.com/heroku/heroku-buildpack-python/blob/main/lib/package_manager.sh). Remove `requirements.txt` from Git so that Heroku uses the lock file:

```bash
git rm requirements.txt
git add pyproject.toml uv.lock
git commit -m "Configure Heroku deployment"
```

The generated `Procfile` already binds uproot to Heroku’s `$PORT`. Make sure `main.py` contains `upd.ADMINS["admin"] = upd.auto_login()`. Then create the app, enable runtime metadata so uproot can discover its public URL, add PostgreSQL, and set the admin password:

```bash
# Create a new Heroku app
heroku create my-experiment-name

# Enable runtime metadata
heroku labs:enable runtime-dyno-metadata

# Provision PostgreSQL
heroku addons:create heroku-postgresql:essential-0
heroku pg:wait

# Store the admin password outside the source code
heroku config:set UPROOT_ADMIN_PASSWORD='choose-a-long-random-password'

# Deploy
git push heroku main

# Keep uproot on exactly one web dyno
heroku ps:scale web=1:basic

# Open the admin interface
heroku open /admin/
```

If your local branch is not named `main`, deploy it with `git push heroku HEAD:main` instead. The PostgreSQL add-on sets `DATABASE_URL`; uproot detects it automatically. If you add a custom domain, set `UPROOT_ORIGIN` to its full `https://` URL with `heroku config:set`.

!!! warning "Do not scale horizontally"
    uproot’s live connection queues and background tasks belong to one server process. Keep exactly one web dyno; adding more web dynos would split participants across processes that do not share that live state.
