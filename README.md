# SSA Alumni — Backend

Django REST API for the SSA Alumni school directory app.

> **Repo:** `ssa-alumni-backend`  
> **Stack:** Django 5 + PostgreSQL (Cloud SQL) + Cloud Run  
> **Auth:** Cloud SQL IAM authentication (passwordless)

---

## Project Structure

```
backend/
├── Dockerfile               # Multi-stage build → Cloud Run
├── requirements.txt
├── manage.py                # DJANGO_SETTINGS_MODULE defaults to dev
├── ssa_alumni/
│   ├── settings/
│   │   ├── base.py          # Shared settings (IAM DB config)
│   │   ├── dev.py           # Local: SQLite, DEBUG=True
│   │   └── prod.py          # Cloud Run: PostgreSQL, HTTPS
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── alumni/                  # Core alumni app
    ├── models.py            # AlumniProfile model
    ├── serializers.py       # DRF serializers
    ├── views.py             # ModelViewSet (CRUD + year filter)
    ├── urls.py              # DefaultRouter
    └── admin.py             # Admin registration
```

## Local Development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
# → http://localhost:8000
# → http://localhost:8000/api/alumni/profiles/
```

## GitHub Actions Deployment (Passwordless)

This project uses **Workload Identity Federation** for secure, passwordless deployments.

### Setup Instructions:
1.  Go to your GitHub repository settings → **Secrets and variables** → **Actions**.
2.  Add the following **Repository Secrets**:
    *   `WIF_PROVIDER`: `projects/685527496529/locations/global/workloadIdentityPools/ssa-alumni-github-pool/providers/ssa-alumni-github-provider`
    *   `WIF_SERVICE_ACCOUNT`: `ssa-alumni-dev-run-sa@ssa-alumni.iam.gserviceaccount.com`

Once these secrets are added, any push to `main` or `master` will automatically build and deploy the backend to Cloud Run.

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/alumni/profiles/` | List all alumni |
| POST | `/api/alumni/profiles/` | Create alumni profile |
| GET | `/api/alumni/profiles/{id}/` | Get one profile |
| PATCH | `/api/alumni/profiles/{id}/` | Update profile |
| DELETE | `/api/alumni/profiles/{id}/` | Delete profile |
| GET | `/api/alumni/profiles/?year=2020` | Filter by graduation year |
