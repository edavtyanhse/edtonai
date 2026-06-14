"""Billing and subscription endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse

from backend.api.dependencies import (
    get_billing_service,
    get_payment_provider,
    get_payment_webhook_service,
    get_settings,
)
from backend.core.auth import require_auth
from backend.core.config import Settings
from backend.integration.payments.base import (
    PaymentProviderDisabledError,
    PaymentProviderError,
    PaymentProviderUnavailableError,
    PaymentWebhookVerificationError,
)
from backend.schemas import (
    BillingAccountResponse,
    BillingPlanListResponse,
    BillingPlanResponse,
    BillingPriceResponse,
    CheckoutSessionResponse,
    CreateCheckoutSessionRequest,
    CurrentSubscriptionResponse,
    PlanEntitlementResponse,
    UsageFeatureResponse,
)
from backend.services.billing import BillingService, PaymentWebhookService

router = APIRouter(prefix="/billing", tags=["billing"])

WEBHOOK_CONTENT_TYPES = {
    "application/json",
    "application/x-www-form-urlencoded",
}


@router.get("/plans", response_model=BillingPlanListResponse)
async def list_billing_plans(
    service: BillingService = Depends(get_billing_service),
) -> BillingPlanListResponse:
    """List active public plans. Provider-internal IDs are not exposed."""
    plans = await service.list_plans()
    return BillingPlanListResponse(
        items=[
            BillingPlanResponse(
                code=plan.code,
                title=plan.title,
                description=plan.description,
                billing_period=plan.billing_period,
                trial_days=plan.trial_days,
                prices=[
                    BillingPriceResponse(
                        provider=price.provider,
                        amount_minor=price.amount_minor,
                        currency=price.currency,
                        billing_period=price.billing_period,
                    )
                    for price in plan.prices
                ],
                entitlements=[
                    PlanEntitlementResponse(
                        feature_code=entitlement.feature_code,
                        limit_value=entitlement.limit_value,
                        reset_period=entitlement.reset_period,
                    )
                    for entitlement in plan.entitlements
                ],
            )
            for plan in plans
        ]
    )


@router.get("/me", response_model=BillingAccountResponse)
async def get_billing_account(
    user_id: str = Depends(require_auth),
    service: BillingService = Depends(get_billing_service),
) -> BillingAccountResponse:
    """Return current user's billing state and usage summary."""
    account = await service.get_account_state(user_id)
    subscription = account.subscription
    return BillingAccountResponse(
        subscription=CurrentSubscriptionResponse(
            status=subscription.status,
            plan_code=subscription.plan_code,
            trial_end=subscription.trial_end,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
        )
        if subscription
        else None,
        usage=[
            UsageFeatureResponse(
                feature_code=item.feature_code,
                used=item.used,
                limit_value=item.limit_value,
                remaining=item.remaining,
                period_start=item.period_start,
                period_end=item.period_end,
            )
            for item in account.usage
        ],
    )


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    payload: CreateCheckoutSessionRequest,
    user_id: str = Depends(require_auth),
    service: BillingService = Depends(get_billing_service),
) -> CheckoutSessionResponse:
    """Create a hosted checkout session from a server-controlled plan code."""
    try:
        checkout = await service.create_checkout_session(
            user_id,
            payload.plan_code,
            idempotency_key=payload.idempotency_key,
        )
    except PaymentProviderDisabledError as exc:
        raise HTTPException(status_code=503, detail="Payment provider is not ready") from exc
    except PaymentProviderUnavailableError as exc:
        raise HTTPException(status_code=502, detail="Payment provider is unavailable") from exc
    except PaymentProviderError as exc:
        raise HTTPException(status_code=502, detail="Payment provider error") from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Billing plan is not available") from exc
    return CheckoutSessionResponse(
        provider=checkout.provider,
        status=checkout.status,
        payment_url=checkout.payment_url,
    )


@router.post("/webhooks/tbank", response_class=PlainTextResponse)
async def receive_tbank_webhook(
    request: Request,
    payment_provider=Depends(get_payment_provider),
    service: PaymentWebhookService = Depends(get_payment_webhook_service),
    settings: Settings = Depends(get_settings),
) -> PlainTextResponse:
    """Verify and journal T-Bank webhook notifications."""
    _ensure_webhook_content_type(request)
    payload = await _read_limited_body(
        request,
        max_bytes=settings.payment_webhook_max_body_bytes,
    )
    headers = dict(request.headers)
    try:
        event = await payment_provider.verify_webhook(payload, headers)
        await service.process_verified_event(event, signature_verified=True)
    except PaymentWebhookVerificationError as exc:
        raise HTTPException(status_code=400, detail="Invalid payment webhook") from exc
    except PaymentProviderDisabledError as exc:
        raise HTTPException(status_code=503, detail="Payment provider is not ready") from exc
    except PaymentProviderError as exc:
        raise HTTPException(status_code=502, detail="Payment provider error") from exc
    return PlainTextResponse("OK")


def _ensure_webhook_content_type(request: Request) -> None:
    raw_content_type = request.headers.get("content-type", "")
    content_type = raw_content_type.split(";", 1)[0].strip().lower()
    if content_type not in WEBHOOK_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported payment webhook media type")


async def _read_limited_body(request: Request, *, max_bytes: int) -> bytes:
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > max_bytes:
            raise HTTPException(status_code=413, detail="Payment webhook payload is too large")
    return bytes(body)
