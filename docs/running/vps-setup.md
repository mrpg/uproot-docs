# VPS setup guide

Step-by-step instructions for deploying uproot on a fresh VPS. This guide assumes no prior server administration experience and produces a minimal, production-ready setup.

## 1. Get a VPS

Rent a virtual private server from any major provider — [Hetzner](https://www.hetzner.com/), [DigitalOcean](https://www.digitalocean.com/), or [AWS Lightsail](https://aws.amazon.com/lightsail/) are all good options. uproot is lightweight; the smallest available tier (1 vCPU, 512 MB–1 GB RAM) is sufficient for most experiments.

Choose **Debian** (latest stable) as the operating system. We recommend Debian for reasons we need not elaborate here.

## 2. Secure SSH access

### Generate an SSH key (on your local machine)

If you don't already have an SSH key, create one:

```console
you@local:~$ ssh-keygen -t ed25519
```

Accept the default file location. Your public key is at `~/.ssh/id_ed25519.pub`.

Most VPS providers let you paste your public key during server creation. If you did that, you can SSH in as root immediately:

```console
you@local:~$ ssh root@YOUR_SERVER_IP
```

If you didn't add a key during creation, log in with the password the provider gave you, then install your key:

```console
you@local:~$ ssh-copy-id -i ~/.ssh/id_ed25519.pub root@YOUR_SERVER_IP
```

### Create a non-root user

Don't run experiments as root. Create a normal user and give it sudo access:

```console
root@server:~# adduser uproot
root@server:~# usermod -aG sudo uproot
```

`adduser` asks you to set a password (you'll need it for `sudo` later) and some optional fields you can skip by pressing Enter.

### Set up SSH keys for both users

Your root account already has your SSH key. Copy it to the new user so you can log in as either:

```console
root@server:~# mkdir -p /home/uproot/.ssh
root@server:~# cp /root/.ssh/authorized_keys /home/uproot/.ssh/authorized_keys
root@server:~# chown -R uproot:uproot /home/uproot/.ssh
root@server:~# chmod 700 /home/uproot/.ssh
root@server:~# chmod 600 /home/uproot/.ssh/authorized_keys
```

### Disable password login

Root login is still allowed, but only with SSH keys. This is convenient for emergency administration while still preventing password-based logins.

```console
root@server:~# nano /etc/ssh/sshd_config.d/99-keys-only.conf
```

!!! tip
    In `nano`, save with Ctrl+S and exit with Ctrl+X.

Paste the following:

```ini
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
```

Then test and apply:

```console
root@server:~# sshd -t
root@server:~# systemctl restart ssh
```

!!! warning
    Before closing this session, verify in a **separate terminal** that your key works for **both** users:

    ```console
    you@local:~$ ssh root@YOUR_SERVER_IP
    you@local:~$ ssh uproot@YOUR_SERVER_IP
    ```

    Both must succeed. If either fails, fix it before closing your root session — otherwise you may lock yourself out.

From now on, use `root@server` for system administration and `uproot@server` for managing your experiment.

## 3. Install system packages

Still as root:

```console
root@server:~# apt update && apt install -y python3 python-is-python3 python3-pip python3-venv nginx certbot python3-certbot-nginx tmux unattended-upgrades dnsutils
root@server:~# dpkg-reconfigure -plow unattended-upgrades
```

Select "Yes" when prompted to enable automatic security updates. This ensures critical patches are installed without your intervention.

## 4. Set up your project

From here on, work as the `uproot` user:

```console
you@local:~$ ssh uproot@YOUR_SERVER_IP
```

### Upload your project

In a separate terminal on your local machine, copy your uproot project to the server:

```console
you@local:~$ rsync --delete -Pa my_project uproot@YOUR_SERVER_IP:
```

### Before going to production

Edit `main.py` on the server to set a real admin password:

```python
upd.ADMINS["admin"] = "your-secure-password"
```

### Create a Python environment

```console
uproot@server:~$ python3 -m venv ~/env
uproot@server:~$ source ~/env/bin/activate
(env) uproot@server:~$ cd ~/my_project
(env) uproot@server:~/my_project$ pip install -Ue .
```

Verify it works:

```console
(env) uproot@server:~/my_project$ uproot run -h 127.0.0.1 -p 8000
```

Stop it with Ctrl+C once you see the startup output. The remaining steps don't require the virtual environment.

### Create a run script

```console
uproot@server:~$ nano ~/run.sh
```

Paste the following:

```bash
#!/bin/bash
set -e
cd ~/my_project
source ~/env/bin/activate
pip install -Ue .
export UPROOT_ORIGIN=https://example.com
exec uproot run -h 127.0.0.1 -p 8000
```

Save, exit, then make it executable:

```console
uproot@server:~$ chmod +x ~/run.sh
```

Replace `example.com` with your actual hostname (see [step 5](#choose-a-hostname)).

The script reinstalls your project on every start (picking up any dependency changes) and starts uproot on a local-only port. nginx will handle the public-facing side.

### Start uproot on boot

There are two ways to keep uproot running: a systemd user service (automatic, survives reboots) or tmux (manual, simpler to understand). We recommend systemd, but tmux is a perfectly reasonable alternative — see the [deployment page](deployment.md#running-uproot) for the tmux approach.

#### systemd (recommended)

Create a user-level systemd service so uproot starts automatically when the server boots. First enable lingering, which allows the user's systemd services to run even when the user is not logged in:

```console
uproot@server:~$ sudo loginctl enable-linger uproot
```

Then create the service:

```console
uproot@server:~$ mkdir -p ~/.config/systemd/user
uproot@server:~$ nano ~/.config/systemd/user/uproot.service
```

Paste the following:

```ini
[Unit]
Description=uproot experiment server
After=network.target

[Service]
Type=exec
ExecStart=%h/run.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Enable and start it:

```console
uproot@server:~$ systemctl --user daemon-reload
uproot@server:~$ systemctl --user enable uproot
uproot@server:~$ systemctl --user start uproot
```

Useful commands:

| Command | What it does |
|---------|-------------|
| `systemctl --user status uproot` | Check if uproot is running |
| `systemctl --user restart uproot` | Restart after updating your project |
| `journalctl --user -u uproot -f` | Follow the live log output |
| `systemctl --user stop uproot` | Stop the server |

## 5. nginx and HTTPS

### Choose a hostname

You need a domain name for HTTPS. A custom domain is not required — there are easier options:

- **Provider-assigned hostname** — Some VPS providers let you assign a hostname through their control panel. If your provider offers this and the hostname already resolves to your server's IP, you can use it directly and skip the DNS step below.
- **University subdomain** — Many universities allow researchers to create subdomains (e.g., `experiment.econ.uni-example.de`). Ask your IT department — this is often the easiest and most professional-looking option.
- **Your own domain** — Register one from any registrar if you prefer full control.

If you're using a university subdomain or your own domain, create a DNS **A record** pointing it to your server's IP address. Wait for it to propagate (usually a few minutes, sometimes up to an hour). You can verify with:

```console
uproot@server:~$ dig +short example.com
```

This should return your server's IP.

### Get a TLS certificate

Stop nginx temporarily so certbot can use port 80:

```console
uproot@server:~$ sudo systemctl stop nginx
uproot@server:~$ sudo certbot certonly --standalone -d example.com
```

Follow the prompts. Certbot stores the certificate at `/etc/letsencrypt/live/example.com/`.

### Set up automatic renewal

Certbot installs a systemd timer that attempts renewal twice daily. Since we used standalone mode, nginx needs to briefly stop during renewal. Create hooks for this:

```console
uproot@server:~$ sudo mkdir -p /etc/letsencrypt/renewal-hooks/pre /etc/letsencrypt/renewal-hooks/post
uproot@server:~$ sudo nano /etc/letsencrypt/renewal-hooks/pre/stop-nginx
```

Paste the following:

```bash
#!/bin/bash
systemctl stop nginx
```

Then create the post-renewal hook:

```console
uproot@server:~$ sudo nano /etc/letsencrypt/renewal-hooks/post/start-nginx
```

Paste the following:

```bash
#!/bin/bash
systemctl start nginx
```

Make both hooks executable:

```console
uproot@server:~$ sudo chmod +x /etc/letsencrypt/renewal-hooks/pre/stop-nginx /etc/letsencrypt/renewal-hooks/post/start-nginx
```

Certificates are valid for 90 days. Renewal is attempted automatically roughly every three weeks once a certificate is past the halfway point. Verify the setup with:

```console
uproot@server:~$ sudo certbot renew --dry-run
```

### Configure nginx

Remove the default site and create the uproot configuration:

```console
uproot@server:~$ sudo rm -f /etc/nginx/sites-enabled/default
uproot@server:~$ sudo nano /etc/nginx/sites-available/uproot
```

Paste the following. Replace every occurrence of `example.com` with your hostname:

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ""      close;
}

server {
    listen 80;
    listen [::]:80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

server {
    server_name example.com;

    listen 443 ssl;
    listen 443 quic;
    listen [::]:443 ssl;
    listen [::]:443 quic;
    http2 on;
    add_header Alt-Svc 'h3=":443"; ma=86400';

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
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

Enable the site and start nginx:

```console
uproot@server:~$ sudo ln -sf /etc/nginx/sites-available/uproot /etc/nginx/sites-enabled/uproot
uproot@server:~$ sudo nginx -t && sudo systemctl start nginx
```

`nginx -t` tests the configuration. If it reports errors, double-check that you replaced all occurrences of `example.com` and that the certificate paths exist.

## 6. Go live

If uproot is not already running via the systemd service:

```console
uproot@server:~$ systemctl --user start uproot
```

Your experiment is now live at `https://example.com/admin/`.

### Updating your experiment

Upload the new version from your local machine, then restart:

```console
you@local:~$ rsync --delete -Pa my_project uproot@YOUR_SERVER_IP:
```

```console
uproot@server:~$ systemctl --user restart uproot
```

The run script automatically reinstalls your project and picks up any changes.

### Maintenance

Restart your server regularly (e.g., every few weeks, and always between experiment sessions) to apply kernel updates installed by `unattended-upgrades`. Many security patches only take full effect after a reboot:

```console
uproot@server:~$ sudo reboot
```

uproot starts back up automatically thanks to the systemd service. After reconnecting, verify:

```console
uproot@server:~$ systemctl --user status uproot
```
