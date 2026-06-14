#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env}"
CONFIG_FILE="${CLOUDBUILD_CONFIG:-cloudbuild.yaml}"
GCLOUD_BIN="${GCLOUD_BIN:-gcloud}"
if ! command -v "${GCLOUD_BIN}" >/dev/null 2>&1; then
  if [[ -x "/opt/homebrew/share/google-cloud-sdk/bin/gcloud" ]]; then
    GCLOUD_BIN="/opt/homebrew/share/google-cloud-sdk/bin/gcloud"
  else
    echo "gcloud not found. Set GCLOUD_BIN=/path/to/gcloud" >&2
    exit 1
  fi
fi
PROJECT_ID="${GCLOUD_PROJECT:-$("${GCLOUD_BIN}" config get-value project 2>/dev/null)}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Google Cloud project is not set. Run: gcloud config set project <project-id>" >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Env file not found: ${ENV_FILE}" >&2
  exit 1
fi

declare -A ENV_VALUES=()

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "${value}"
}

unquote() {
  local value="$1"
  if [[ "${value}" == \"*\" && "${value}" == *\" ]]; then
    value="${value:1:${#value}-2}"
  elif [[ "${value}" == \'*\' && "${value}" == *\' ]]; then
    value="${value:1:${#value}-2}"
  fi
  printf '%s' "${value}"
}

while IFS= read -r raw_line || [[ -n "${raw_line}" ]]; do
  line="$(trim "${raw_line}")"
  [[ -z "${line}" || "${line}" == \#* ]] && continue
  [[ "${line}" == export\ * ]] && line="${line#export }"
  [[ "${line}" != *=* ]] && continue

  key="$(trim "${line%%=*}")"
  value="$(trim "${line#*=}")"
  value="$(unquote "${value}")"

  [[ -z "${key}" ]] && continue
  ENV_VALUES["${key}"]="${value}"
done < "${ENV_FILE}"

if [[ (! -v "ENV_VALUES[SMTP_FROM_EMAIL]" || -z "${ENV_VALUES[SMTP_FROM_EMAIL]}") && -v "ENV_VALUES[SMTP_USERNAME]" ]]; then
  ENV_VALUES["SMTP_FROM_EMAIL"]="${ENV_VALUES[SMTP_USERNAME]}"
fi

SUBSTITUTION_KEYS=(
  DEPLOY_REGION
  AR_HOSTNAME
  AR_REPO
  BACKEND_SERVICE_NAME
  FRONTEND_SERVICE_NAME
  POSTGRES_USER
  POSTGRES_PASSWORD
  POSTGRES_HOST
  POSTGRES_PORT
  POSTGRES_DB
  AI_PROVIDER
  DEEPSEEK_API_KEY
  DEEPSEEK_BASE_URL
  AI_MODEL
  AI_TIMEOUT_SECONDS
  AI_MAX_RETRIES
  AI_TEMPERATURE
  AI_MAX_TOKENS
  LOG_LEVEL
  APP_ENV
  GROQ_API_KEY
  AI_PROVIDER_PARSING
  AI_PROVIDER_REASONING
  HF_TOKEN
  HF_ENDPOINT_URL
  DB_AUTO_CREATE
  JWT_SECRET_KEY
  JWT_ACCESS_TOKEN_EXPIRE_MINUTES
  JWT_REFRESH_TOKEN_EXPIRE_DAYS
  REFRESH_COOKIE_PATH
  SMTP_HOST
  SMTP_PORT
  SMTP_USERNAME
  SMTP_PASSWORD
  SMTP_FROM_EMAIL
  FRONTEND_URL
  BACKEND_URL
  BACKEND_INTERNAL_URL
  GOOGLE_API_KEY
  GOOGLE_OAUTH_CLIENT_ID
  GOOGLE_OAUTH_CLIENT_SECRET
  YANDEX_OAUTH_CLIENT_ID
  YANDEX_OAUTH_CLIENT_SECRET
  SUPABASE_JWT_SECRET
  MAX_RESUME_CHARS
  MAX_VACANCY_CHARS
  AUTH_RATE_LIMIT_PER_MINUTE
  AI_RATE_LIMIT_PER_MINUTE
  SCRAPER_RATE_LIMIT_PER_MINUTE
  CHECKOUT_RATE_LIMIT_PER_MINUTE
  PAYMENT_WEBHOOK_RATE_LIMIT_PER_MINUTE
  PAYMENT_WEBHOOK_MAX_BODY_BYTES
  TRUSTED_PROXY_IPS
  AI_MONTHLY_FREE_QUOTA
  AI_MONTHLY_TRIAL_QUOTA
  BILLING_TEMPORARY_HIGH_FREE_QUOTA_ENABLED
  SCRAPER_ALLOWED_HOSTS
  SCRAPER_TIMEOUT_SECONDS
  SCRAPER_MAX_HTML_BYTES
  SCRAPER_MAX_REDIRECTS
  HH_API_USER_AGENT
  PAYMENT_PROVIDER
  PAYMENT_WEBHOOK_REPLAY_TOLERANCE_SECONDS
  TBANK_TERMINAL_KEY
  TBANK_PUBLIC_KEY
  TBANK_PASSWORD
  TBANK_WEBHOOK_SECRET
  VITE_SUPABASE_URL
  VITE_SUPABASE_ANON_KEY
  VITE_CLARITY_PROJECT_ID
)

SUBSTITUTIONS=()
for key in "${SUBSTITUTION_KEYS[@]}"; do
  if [[ -v "ENV_VALUES[${key}]" ]]; then
    value="${ENV_VALUES[${key}]}"
    if [[ "${value}" == *"~"* ]]; then
      echo "Value for ${key} contains '~', which is used as a gcloud delimiter." >&2
      exit 1
    fi
    SUBSTITUTIONS+=("_${key}=${value}")
  fi
done

if [[ "${#SUBSTITUTIONS[@]}" -eq 0 ]]; then
  echo "No supported Cloud Build substitutions found in ${ENV_FILE}" >&2
  exit 1
fi

IFS='~'
SUBSTITUTION_ARG="^~^${SUBSTITUTIONS[*]}"
unset IFS

echo "Submitting Cloud Build with ${#SUBSTITUTIONS[@]} substitutions from ${ENV_FILE}"
echo "Secrets are still passed as Cloud Build substitutions; migrate to Secret Manager before production."

if [[ "${DRY_RUN:-}" == "1" ]]; then
  echo "DRY_RUN=1: Cloud Build submission skipped."
  exit 0
fi

"${GCLOUD_BIN}" builds submit \
  --project "${PROJECT_ID}" \
  --config "${CONFIG_FILE}" \
  --substitutions "${SUBSTITUTION_ARG}" \
  .
