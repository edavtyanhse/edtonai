"""Billing and subscription read endpoints."""

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_billing_service
from backend.core.auth import require_auth
from backend.schemas import (
    BillingAccountResponse,
    BillingPlanListResponse,
    BillingPlanResponse,
    BillingPriceResponse,
    CurrentSubscriptionResponse,
    PlanEntitlementResponse,
    UsageFeatureResponse,
)
from backend.services.billing import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


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
