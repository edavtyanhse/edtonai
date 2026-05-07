# Database Documentation

PostgreSQL data model for EdTon.ai. The schema combines a global AI/cache layer
with user-owned records and generated artifacts.

## ERD

- Source: [erd.puml](erd.puml)
- The diagram uses large PlantUML fonts and grouped blocks so labels stay readable
  in IDE preview/export.

## Model Overview

### Users And Authentication

| Table | Purpose | Important notes |
|---|---|---|
| `users` | Application users | UUID primary key, unique email, active/verified flags. |
| `refresh_tokens` | Refresh sessions | Stores `token_hash`, never the raw refresh token. |
| `email_verifications` | Email verification links | Stores `token_hash`; `token` is nullable legacy compatibility only. |
| `oauth_accounts` | External OAuth identities | Unique `(provider, provider_user_id)` mapped to `users.id`. |

### Global AI Cache Layer

| Table | Purpose | Important notes |
|---|---|---|
| `resume_raw` | De-duplicated raw resume text and parsed resume columns | Global cache keyed by `content_hash`; not a user-owned edited document. |
| `vacancy_raw` | De-duplicated raw vacancy text, optional `source_url`, parsed vacancy columns | Global cache keyed by `content_hash`; URL scraping must stay SSRF-protected. |
| `ai_result` | LLM result cache | Unique `(operation, input_hash)` prevents duplicate AI calls for identical work. |

`analysis_link` was removed. Match de-duplication is handled by
`ai_result(operation, input_hash)`, and user-visible history belongs in
user-owned artifact tables rather than a global resume/vacancy pair link.

### User Ownership And Private Overrides

| Table | Purpose | Important notes |
|---|---|---|
| `user_resume` | User ownership of a `resume_raw` record | `user_id` is UUID FK to `users.id`; unique `(user_id, resume_id)`. |
| `user_vacancy` | User ownership of a `vacancy_raw` record | `user_id` is UUID FK to `users.id`; unique `(user_id, vacancy_id)`. |
| `user_resume.parsed_data_override` | User-specific parsed resume edits | Keeps PATCH edits private and avoids mutating shared `resume_raw`. |
| `user_vacancy.parsed_data_override` | User-specific parsed vacancy edits | Keeps PATCH edits private and avoids mutating shared `vacancy_raw`. |

The raw tables remain useful for de-duplication and AI caching. User edits live
on the owner mapping tables so two users with identical uploaded text cannot
silently overwrite each other's parsed data.

### Generated User Artifacts

| Table | Purpose | Important notes |
|---|---|---|
| `resume_version` | Adapted resume versions | `user_id` is required UUID FK; legacy `NULL` owners are migrated to the inactive archive user. |
| `user_version` | Frontend-friendly history entries | `user_id` is required UUID FK; type is constrained to `adapt` or `ideal`. |
| `ideal_resume` | Generated ideal resume for a vacancy/options hash | Global generated cache keyed by `input_hash`; user access must go through vacancy ownership. |
| `feedback` | Authenticated product feedback | Stores `user_id` where available and `user_hash`; email is nullable legacy-only data. |

`user_version` intentionally duplicates resume/vacancy/result text for easy
history rendering. Because this data can contain PII, future retention and
export/delete policies should treat it as sensitive user content.

## Current Relationships

```text
users
  -> refresh_tokens
  -> email_verifications
  -> oauth_accounts
  -> user_resume -> resume_raw
  -> user_vacancy -> vacancy_raw
  -> resume_version
  -> user_version
  -> feedback

vacancy_raw
  -> ideal_resume
```

## Security And Integrity Rules

- User-bound tables must use `UUID` foreign keys to `users.id`, not string IDs.
- Raw card data must never be added to this schema. Future payments should use
  provider-hosted checkout and store only provider IDs, statuses, hashes and
  audit metadata.
- Refresh and email verification tokens are bearer secrets. Store hashes only.
- `resume_raw` and `vacancy_raw` are shared cache records. User-specific edits
  belong in `user_resume` / `user_vacancy` overrides.
- Match-analysis caching belongs to `ai_result`; do not reintroduce global
  `analysis_link` unless a user-owned history/audit requirement appears.
- Feedback should be attributable without storing email as the primary key.
- Timestamps should use timezone-aware columns.
- Sensitive text tables need future retention/delete policy before commercial
  production.

## Indexes And Constraints

| Table | Constraint / Index | Purpose |
|---|---|---|
| `users.email` | unique | One account per email. |
| `oauth_accounts(provider, provider_user_id)` | unique | Prevent duplicate OAuth identity links. |
| `refresh_tokens.token_hash` | unique index | Safe refresh token lookup/rotation. |
| `email_verifications.token_hash` | unique index | Safe verification token lookup. |
| `resume_raw.content_hash` | unique index | Resume de-duplication. |
| `vacancy_raw.content_hash` | unique index | Vacancy de-duplication. |
| `ai_result(operation, input_hash)` | unique index | LLM cache key. |
| `user_resume(user_id, resume_id)` | unique | Prevent duplicate ownership links. |
| `user_vacancy(user_id, vacancy_id)` | unique | Prevent duplicate ownership links. |
| `user_version.type` | check | Only `adapt` or `ideal`. |
| `feedback.metric_type / score` | checks | CSAT 1-5, NPS 0-10. |

## Migration Notes

Alembic is the source for new schema changes. The historical SQL files in
`backend/db/migrations` document the pre-Alembic baseline and should not be
extended for new work.

Important current Alembic revisions:

- `20260429_0001_baseline_existing_sql.py`: baseline marker for existing DBs.
- `20260502_0002_user_resource_ownership.py`: initial ownership mappings.
- `20260507_0003_harden_user_data_model.py`: UUID owner FKs, private parsed
  overrides, hashed token storage, `analysis_link` removal, feedback privacy.

## Subscription Extension Point

Future billing should attach to `users.id`, not to `resume_raw`, `vacancy_raw` or
`ai_result`.

Recommended future tables:

- `billing_plan`
- `billing_price`
- `plan_entitlement`
- `user_subscription`
- `usage_quota`
- `usage_event`
- `payment_checkout_session`
- `payment_webhook_event`
- `payment_transaction`

Entitlement checks should run in application services before expensive AI
operations and usage should be recorded transactionally with idempotency keys.
