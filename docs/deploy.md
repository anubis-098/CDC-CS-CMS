# Ubuntu Server + Docker Compose + Cloudflare Quick Tunnel

Install Docker Engine with the Compose plugin on Ubuntu. No Python or cloudflared installation is needed on the host; Compose runs both in containers.

## First deployment

```bash
git clone https://github.com/anubis-098/CDC-CS-CMS.git
cd CDC-CS-CMS
cp .env.example .env
nano .env
```

Set unique long random values for `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD`. Keep `WEB_BIND_ADDRESS=127.0.0.1` for tunnel-only access. Generate each secret with `openssl rand -hex 32` if desired.

```bash
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
docker compose logs --tail=100 cloudflared
```

Startup order: PostgreSQL health check → database migrations → web health check → Quick Tunnel. Find the generated `https://...trycloudflare.com` address in cloudflared logs.

Edit `.env` using the actual generated hostname:

```dotenv
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,actual-name.trycloudflare.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://actual-name.trycloudflare.com
WEB_BIND_ADDRESS=127.0.0.1
```

Apply the settings only to the web service, keeping the running tunnel and URL:

```bash
docker compose up -d --no-deps --force-recreate web
docker compose ps
```

Open the tunnel HTTPS URL and sign in. Cloudflared runs in the background with Compose and connects directly to `http://web:8000` on the internal Docker network. It does not use localhost inside its own container. No inbound public port is needed for the tunnel.

## Updating

```bash
git pull
docker compose up -d --build
docker compose logs --tail=100 cloudflared
```

If the tunnel restarted and generated a new URL, update both hostname settings again and recreate only web with the command above. Do not use wildcard hosts or disable CSRF.

## Checks and data

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py test
docker compose logs --tail=100 web init cloudflared
```

New installations start with an empty database. Git does not transfer claim records or accounts from another machine. PostgreSQL data persists in the Compose volume. Do not run `docker compose down -v` if you want to keep it.

Quick Tunnel URLs are temporary and intended for testing. For a permanent production address, use a named tunnel. Documentation: https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/
