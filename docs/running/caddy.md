---
description: Run uproot behind Caddy on Debian 13 for automatic HTTPS certificates, HTTP/2, and HTTP/3 over QUIC—an alternative to nginx.
---

# Deploying with Caddy

[Caddy](https://caddyserver.com/docs/) is a web server that can take nginx’s place in front of uproot. It gets and renews its own HTTPS certificates, turns on [HTTP/3](https://developer.mozilla.org/en-US/docs/Glossary/HTTP_3) by default, and needs only three lines of configuration. You do not need Certbot, renewal hooks, or WebSocket settings.

This page assumes that you have read [Deployment](deployment.md) and followed steps 1 to 4 of the [VPS setup guide](vps-setup.md). It replaces the guide’s step 5, “nginx and HTTPS.” Everything below works with Caddy 2.6.2, the version in Debian 13 (“trixie”).

## Install Caddy

Caddy and nginx both need ports 80 and 443, so use one or the other. If you followed the VPS setup guide, leave `nginx certbot python3-certbot-nginx` out of the `apt install` command in [step 3](vps-setup.md#3-install-system-packages). If nginx is already running, stop it and keep it from starting at boot:

```console
uproot@server:~$ sudo systemctl disable --now nginx
```

Then install Caddy and `curl`, which you will use below to check HTTP/3:

```console
uproot@server:~$ sudo apt install caddy curl
```

Debian starts Caddy right away, as a service that runs at boot under its own `caddy` user. Until you configure it, Caddy shows a placeholder page on port 80.

## Prepare the network

Participants’ browsers connect on three ports:

- TCP port 443 for HTTPS over HTTP/1.1 and HTTP/2,
- UDP port 443 for HTTP/3, which runs over [QUIC](https://developer.mozilla.org/en-US/docs/Glossary/QUIC), and
- TCP port 80, which Caddy uses to obtain certificates and to redirect `http://` addresses to `https://`.

If your VPS provider has a firewall in its control panel, allow all three. UDP is easy to forget: if it is blocked, everything still works, but browsers silently fall back to HTTP/2.

Your hostname must already point to the server’s IP address before Caddy can get a certificate. The VPS setup guide explains how to [choose a hostname](vps-setup.md#choose-a-hostname) and check it with `dig`.

## Configure Caddy

Caddy reads its configuration from a file called the *Caddyfile*. Open it:

```console
uproot@server:~$ sudo nano /etc/caddy/Caddyfile
```

Delete everything in it and paste the following, replacing `example.com` with your hostname:

```caddyfile
example.com {
	reverse_proxy 127.0.0.1:8000
}
```

That is the complete configuration. The first line names your site; the second tells Caddy to forward every request to uproot at `127.0.0.1:8000`, the local-only address that the [run script](vps-setup.md#create-a-run-script) starts uproot on. Caddy is a *reverse proxy* here: it talks to participants’ browsers and passes their requests on to uproot.

Check the file for mistakes, then load it:

```console
uproot@server:~$ caddy validate --config /etc/caddy/Caddyfile
uproot@server:~$ sudo systemctl reload caddy
```

Within a few seconds, Caddy obtains a certificate. Open `https://example.com/admin/` to check that uproot answers. If it does not, look at Caddy’s log:

```console
uproot@server:~$ sudo journalctl -u caddy -e
```

Certificate errors there usually mean that the hostname does not point to this server yet, or that a firewall blocks port 80 or 443.

!!! warning "`UPROOT_ORIGIN` must match"
    uproot builds the links it shows you from `UPROOT_ORIGIN`. Set it to the same hostname as in the Caddyfile, with `https://`, as the [run script](vps-setup.md#create-a-run-script) does: `export UPROOT_ORIGIN=https://example.com`.

### What Caddy does for you

With these three lines, Caddy:

- obtains a free certificate from [Let’s Encrypt](https://letsencrypt.org/) (or [ZeroSSL](https://zerossl.com/) if Let’s Encrypt is unavailable) and renews it automatically before it expires,
- redirects `http://` to `https://`,
- speaks HTTP/1.1, HTTP/2, and HTTP/3, and tells browsers about HTTP/3 with an `Alt-Svc` header,
- accepts HTTP/3 over both QUIC version 1 and the newer [QUIC version 2](https://www.rfc-editor.org/rfc/rfc9369.html),
- forwards [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API), which uproot’s [real-time features](../multiplayer/real-time.md) depend on, and
- tells uproot each participant’s IP address and that they connected over HTTPS. Caddy replaces any such information that a browser sends itself, so participants cannot fake their address.

Browsers that cannot use HTTP/3, or networks that block UDP, fall back to HTTP/2 automatically.

To check HTTP/3 from your own computer, open your site in Chrome or Firefox and look at the *Protocol* column in the developer tools’ Network tab: it should show `h3`, possibly only after a reload. Debian 13’s `curl` can also test it from the server:

```console
uproot@server:~$ curl --http3-only -s -o /dev/null -w '%{http_version}\n' https://example.com/admin/login/
3
```

The `3` stands for HTTP/3. If the command fails instead, UDP port 443 is probably blocked.

### Raise the UDP buffer limit

Caddy’s log may contain the line `failed to sufficiently increase receive buffer size`. Debian’s default limit for UDP buffers is too small for fast HTTP/3 transfers. HTTP/3 still works, but large pages and files may load more slowly. Raise the limit to the [value recommended by Caddy’s QUIC library](https://github.com/quic-go/quic-go/wiki/UDP-Buffer-Sizes):

```console
uproot@server:~$ sudo nano /etc/sysctl.d/60-udp-buffers.conf
```

Paste the following:

```ini
net.core.rmem_max = 7500000
net.core.wmem_max = 7500000
```

Apply the setting and restart Caddy:

```console
uproot@server:~$ sudo sysctl --system
uproot@server:~$ sudo systemctl restart caddy
```

The file in `/etc/sysctl.d/` keeps the setting across reboots.

## Changing the configuration

Whenever you edit the Caddyfile, run `caddy validate` and `sudo systemctl reload caddy` again. The certificates and settings stay in place.

!!! warning "Do not reload Caddy during a session"
    A reload closes every open WebSocket connection. uproot reconnects within about a second, but participants briefly see uproot’s “connection lost” notice. Change Caddy’s configuration between sessions.

## Hosting in a subdirectory

To serve uproot at a path like `https://example.com/my-study/`, first set `UPROOT_SUBDIRECTORY` as described in [Hosting in a subdirectory](deployment.md#hosting-in-a-subdirectory). Then forward only that path to uproot:

```caddyfile
example.com {
	redir /my-study /my-study/ 308
	reverse_proxy /my-study/* 127.0.0.1:8000
}
```

Caddy passes the full path, including `/my-study/`, to uproot, which expects it there. The `redir` line sends visitors who leave out the final slash to the right address. The admin interface is then at `https://example.com/my-study/admin/`.

!!! warning "Use `reverse_proxy`, not `handle_path`"
    Caddy’s `handle_path` directive removes the path prefix before forwarding a request. uproot then receives `/admin/` instead of `/my-study/admin/` and answers with `{"detail":"Not Found"}`.

## Logging requests

Caddy writes errors and certificate events to the system journal but, unlike nginx, keeps no log of individual requests. Participants’ IP addresses are personal data, so this is a sensible default for research. If you need a request log, add a `log` line:

```caddyfile
example.com {
	log
	skip_log /ws/*
	reverse_proxy 127.0.0.1:8000
}
```

`skip_log /ws/*` leaves out participants’ WebSocket connections, which would otherwise fill the log. Read the log with `sudo journalctl -u caddy`.

## Advanced: connect through a Unix socket

With the setup above, uproot listens on `127.0.0.1:8000`. Any program on the server can connect to that address directly, bypassing Caddy, and uproot trusts the forwarding information of local connections. On a server that only you use, this is fine. If you want to make sure that only Caddy can reach uproot, connect the two through a [Unix domain socket](https://man7.org/linux/man-pages/man7/unix.7.html), a special file that acts as a local network connection. File permissions then decide who can connect.

First, have the system create a directory for the socket at every boot:

```console
uproot@server:~$ sudo nano /etc/tmpfiles.d/uproot.conf
```

Paste the following:

```text
d /run/uproot 0750 uproot uproot -
```

Create the directory now, and let Caddy into the `uproot` group so that it may open the socket:

```console
uproot@server:~$ sudo systemd-tmpfiles --create /etc/tmpfiles.d/uproot.conf
uproot@server:~$ sudo usermod -aG uproot caddy
```

In your [run script](vps-setup.md#create-a-run-script), replace the last line with:

```bash
exec uproot run --uds /run/uproot/uproot.sock
```

uproot creates the socket so that only its owner and group can use it. `UPROOT_ORIGIN` is required with `--uds`, because uproot cannot work out its public address from a socket. In the Caddyfile, point `reverse_proxy` at the socket:

```caddyfile
example.com {
	reverse_proxy unix//run/uproot/uproot.sock
}
```

Finally, restart both. Caddy needs a full restart, not a reload, to pick up its new group:

```console
uproot@server:~$ systemctl --user restart uproot
uproot@server:~$ sudo systemctl restart caddy
```

If Caddy’s log shows `permission denied` for the socket, check that `id caddy` lists the `uproot` group and that you restarted Caddy.
