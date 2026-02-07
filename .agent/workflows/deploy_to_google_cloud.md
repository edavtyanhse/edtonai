---
description: How to deploy EdTon.ai to Google Cloud Platform (Cloud Run)
---

# Deploy EdTon.ai to Google Cloud Run

This workflow deploys the full-stack EdTon.ai application (FastAPI backend + Vite React frontend) to Google Cloud Run with CI/CD via Cloud Build.

## Prerequisites

- Google Cloud CLI (`gcloud`) authenticated
- Docker Desktop installed and running
- Access to Supabase project (Transaction Pooler connection)
- DeepSeek API key

## Configuration

Project directory: `c:\Users\User\edtonai\edtonai`
Google Cloud Project: `sigma-cairn-486621-b5`
Region: `us-east1`

### Environment Files

**backend.env** (used for Cloud Run deployment):
```
POSTGRES_USER=postgres.qwxfmnhkgepyksdkibvw
POSTGRES_PASSWORD=<supabase_password>
POSTGRES_HOST=aws-1-us-east-1.pooler.supabase.com
POSTGRES_PORT=6543
POSTGRES_DB=postgres
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=<your_api_key>
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat
AI_TIMEOUT_SECONDS=120
AI_MAX_RETRIES=3
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=8192
LOG_LEVEL=INFO
SUPABASE_JWT_SECRET=<your_jwt_secret>
```

## Step 1: Initial Setup

// turbo
```powershell
gcloud config set project sigma-cairn-486621-b5
```

// turbo
```powershell
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

// turbo
```powershell
gcloud auth configure-docker us-east1-docker.pkg.dev --quiet
```

## Step 2: Build and Push Backend

```powershell
docker build -t us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/backend:latest backend/
```

```powershell
docker push us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/backend:latest
```

## Step 3: Deploy Backend

```powershell
gcloud run deploy edtonai-backend --image us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/backend:latest --region us-east1 --platform managed --allow-unauthenticated --port 8000 --env-vars-file backend.env
```

Verify backend health:
// turbo
```powershell
Invoke-RestMethod -Uri https://edtonai-backend-985259530508.us-east1.run.app/health
```

Expected output: `status: ok, database: ok`

## Step 4: Build and Push Frontend

Replace the build args with your actual Supabase credentials:

```powershell
docker build -t us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/frontend:latest --build-arg VITE_SUPABASE_URL=https://qwxfmnhkgepyksdkibvw.supabase.co --build-arg VITE_SUPABASE_ANON_KEY=<your_anon_key> frontend/
```

```powershell
docker push us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/frontend:latest
```

## Step 5: Deploy Frontend

```powershell
gcloud run deploy edtonai-frontend --image us-east1-docker.pkg.dev/sigma-cairn-486621-b5/edtonai-repo/frontend:latest --region us-east1 --platform managed --allow-unauthenticated --port 80 --update-env-vars "BACKEND_URL=https://edtonai-backend-985259530508.us-east1.run.app"
```

Verify frontend API proxy:
// turbo
```powershell
Invoke-RestMethod -Uri https://edtonai-frontend-985259530508.us-east1.run.app/api/v1/health
```

## Step 6: Setup CI/CD with Cloud Build

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers?project=sigma-cairn-486621-b5)
2. Click "Create Trigger"
3. Connect repository: `edavtyanhse/edtonai` (GitHub)
4. Configuration: Cloud Build configuration file (yaml) → `cloudbuild.yaml`
5. Add substitution variables:
   - `_POSTGRES_PASSWORD`: Supabase password
   - `_DEEPSEEK_API_KEY`: DeepSeek API key
   - `_VITE_SUPABASE_URL`: `https://qwxfmnhkgepyksdkibvw.supabase.co`
   - `_VITE_SUPABASE_ANON_KEY`: Supabase anon key
   - `_BACKEND_URL`: `https://edtonai-backend-985259530508.us-east1.run.app`
   - `_SUPABASE_JWT_SECRET`: Supabase JWT secret (Settings → API → JWT Secret)

## Troubleshooting

### Database Connection Error (`statement_cache_size`)
Supabase Transaction Pooler (port 6543) doesn't support prepared statements.  
**Fix**: In `backend/db/session.py`, use `connect_args={"statement_cache_size": 0}`

### 502 Bad Gateway on Frontend API
Nginx forwards `/api/v1/...` but backend expects `/v1/...`.  
**Fix**: In `frontend/nginx.conf`, add rewrite rule:
```nginx
rewrite ^/api/(.*)$ /$1 break;
```

### Environment Variable Corruption (PowerShell)
**Fix**: Use `--env-vars-file backend.env` instead of inline `--set-env-vars`

### Startup Crash (DDL on Transaction Pooler)
**Fix**: Comment out `Base.metadata.create_all` in `backend/main.py`

## Service URLs

- **Backend**: https://edtonai-backend-985259530508.us-east1.run.app
- **Frontend**: https://edtonai-frontend-985259530508.us-east1.run.app
