---
description: Context and guidelines for developing EdTon.ai - AI-powered resume analysis platform
---

# EdTon.ai Development Guide

## Project Overview

EdTon.ai is an AI-powered platform for analyzing resumes against job vacancies. It provides match scores, improvement recommendations, and generates tailored motivation letters.

**Tech Stack:**
- **Backend**: FastAPI (Python 3.11+), SQLAlchemy async, Pydantic
- **Frontend**: React 18 + TypeScript, Vite, TailwindCSS
- **Database**: PostgreSQL via Supabase (Transaction Pooler, port 6543)
- **AI**: DeepSeek API (GPT-compatible)
- **Deployment**: Google Cloud Run, Cloud Build CI/CD

## Project Structure

```
c:\Users\User\edtonai\edtonai\
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   └── config.py        # Pydantic Settings (env vars)
│   ├── db/
│   │   ├── session.py       # Async SQLAlchemy engine
│   │   └── models.py        # Database models
│   ├── api/
│   │   └── v1/              # API routes
│   ├── services/
│   │   ├── ai_service.py    # AI provider integration
│   │   └── resume_service.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom hooks
│   │   ├── i18n/            # Internationalization (ru/en)
│   │   └── lib/             # Supabase client, utils
│   ├── nginx.conf           # Production nginx config
│   ├── Dockerfile
│   └── package.json
├── cloudbuild.yaml          # CI/CD configuration
├── backend.env              # Backend env vars for deployment
└── .env                     # Local development env vars
```

## Environment Configuration

### Local Development (.env)
```
POSTGRES_USER=postgres.qwxfmnhkgepyksdkibvw
POSTGRES_PASSWORD=<password>
POSTGRES_HOST=aws-1-us-east-1.pooler.supabase.com
POSTGRES_PORT=6543
POSTGRES_DB=postgres
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=<key>
VITE_SUPABASE_URL=https://qwxfmnhkgepyksdkibvw.supabase.co
VITE_SUPABASE_ANON_KEY=<key>
```

## Running Locally

### Backend
// turbo
```powershell
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
// turbo
```powershell
cd frontend
npm install
npm run dev
```

## Key Technical Details

### Database Connection (Supabase)
- Use **Transaction Pooler** (port 6543), NOT direct connection
- **CRITICAL**: Must set `statement_cache_size=0` in SQLAlchemy:
```python
async_engine = create_async_engine(
    settings.database_url,
    connect_args={"statement_cache_size": 0},  # Required for Supabase pooler
)
```
- Do NOT use `Base.metadata.create_all` in production (DDL not supported via pooler)

### Frontend Nginx Proxy
- Frontend serves at `/api/*` which proxies to backend
- Nginx must rewrite `/api/v1/...` → `/v1/...`:
```nginx
location /api/ {
    rewrite ^/api/(.*)$ /$1 break;
    proxy_pass $backend_upstream;
    proxy_set_header Host $proxy_host;
}
```

### Internationalization (i18n)
- Uses `react-i18next`
- Languages: Russian (default), English
- Translation files: `frontend/src/i18n/locales/`
- **IMPORTANT**: Always check `i18n.ts` initialization when debugging language issues

## Common Tasks

### Add new API endpoint
1. Create route in `backend/api/v1/`
2. Add service logic in `backend/services/`
3. Register router in `backend/api/v1/__init__.py`

### Add new frontend page
1. Create component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Add translations in both `ru.json` and `en.json`

### Database changes
1. Modify models in `backend/db/models.py`
2. Create migration via Supabase dashboard or Alembic
3. Do NOT rely on auto-create (`create_all`) in production

## Deployment

See `/deploy_to_google_cloud` workflow for full deployment instructions.

Quick manual deploy:
```powershell
# Backend
docker build -t us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/backend backend/
docker push us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/backend
gcloud run deploy edtonai-backend --image us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/backend --region us-east1 --env-vars-file backend.env

# Frontend
docker build -t us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/frontend --build-arg VITE_SUPABASE_URL=... --build-arg VITE_SUPABASE_ANON_KEY=... frontend/
docker push us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/frontend
gcloud run deploy edtonai-frontend --image us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/frontend --region us-east1 --update-env-vars "BACKEND_URL=https://edtonai-backend-985259530508.us-east1.run.app"
```

## Service URLs

- **Production Frontend**: https://edtonai-frontend-985259530508.us-east1.run.app
- **Production Backend**: https://edtonai-backend-985259530508.us-east1.run.app
- **Local Frontend**: http://localhost:5173
- **Local Backend**: http://localhost:8000

## Known Issues & Gotchas

1. **Supabase pooler**: Always use `statement_cache_size=0`
2. **PowerShell + gcloud**: Use `--env-vars-file` instead of inline vars
3. **Nginx proxy**: Path rewrite required (`/api/` → `/`)
4. **i18n**: Check `resources` object in `i18n.ts` if translations break
5. **Docker builds**: Frontend needs `--build-arg` for Supabase keys
