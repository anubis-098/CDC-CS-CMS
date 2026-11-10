# Deploy on another computer

```powershell
git clone https://github.com/anubis-098/CDC-CS-CMS.git
cd CDC-CS-CMS
Copy-Item .env.example .env
```

Set unique `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD` in `.env`, then:

```powershell
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test
```

This starts a new database. Git does not transfer existing users or claim records.

## Cloudflare Quick Tunnel

Install cloudflared on the host and run:

```powershell
cloudflared tunnel --url http://localhost:8085
```

Keep that terminal running. Copy the actual generated hostname into `.env` (replace the example below):

```dotenv
WEB_BIND_ADDRESS=127.0.0.1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,actual-name.trycloudflare.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://actual-name.trycloudflare.com
```

```powershell
docker compose up -d --force-recreate web
```

Open the generated HTTPS URL and sign in. Update both hostname settings whenever the tunnel URL changes. Do not use wildcard hosts or disable CSRF.

Quick Tunnels are temporary testing URLs and stop when cloudflared stops. Reference: https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/
