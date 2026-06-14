"""Seed baseline billing plans without connecting a live payment provider.

Run from repository root:

    backend/.venv/bin/python -m backend.scripts.seed_billing_plans

The script is idempotent and writes only server-controlled plan, price and
entitlement records. It does not create subscriptions, payments, or checkout
sessions.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from backend.core.config import settings
from backend.domain.billing import AI_OPERATION_FEATURE
from backend.models.billing import BillingPlan, BillingPrice, PlanEntitlement
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@dataclass(frozen=True)
class SeedPrice:
    provider: str
    provider_price_id: str | None
    amount_minor: int
    currency: str
    billing_period: str
    is_active: bool = True


@dataclass(frozen=True)
class SeedEntitlement:
    feature_code: str
    limit_value: int | None
    reset_period: str | None


@dataclass(frozen=True)
class SeedPlan:
    code: str
    title: str
    description: str
    billing_period: str
    trial_days: int
    is_active: bool
    prices: tuple[SeedPrice, ...]
    entitlements: tuple[SeedEntitlement, ...]


def _paid_plan(
    code: str,
    title: str,
    billing_period: str,
    amount_minor: int,
) -> SeedPlan:
    """Create a paid subscription period configured from DB."""
    return SeedPlan(
        code=code,
        title=title,
        description="Paid subscription with unlimited AI operations.",
        billing_period=billing_period,
        trial_days=0,
        is_active=True,
        prices=(
            SeedPrice(
                provider="tbank",
                provider_price_id=f"tbank_{code}",
                amount_minor=amount_minor,
                currency="RUB",
                billing_period=billing_period,
            ),
        ),
        entitlements=(
            SeedEntitlement(AI_OPERATION_FEATURE, None, billing_period),
        ),
    )


PLANS: tuple[SeedPlan, ...] = (
    SeedPlan(
        code="free",
        title="Free",
        description="Temporary public access before commercial launch.",
        billing_period="month",
        trial_days=0,
        is_active=True,
        prices=(
            SeedPrice(
                provider="noop",
                provider_price_id="noop_free_monthly",
                amount_minor=0,
                currency="RUB",
                billing_period="month",
            ),
        ),
        entitlements=(
            SeedEntitlement(AI_OPERATION_FEATURE, 5, "month"),
        ),
    ),
    _paid_plan("paid_weekly", "Subscription - weekly", "week", 15000),
    _paid_plan("paid_monthly", "Subscription - monthly", "month", 30000),
    _paid_plan("paid_quarterly", "Subscription - 3 months", "quarter", 60000),
)

OBSOLETE_PLAN_CODES = ("basic", "pro")


async def _upsert_plan(session, seed: SeedPlan) -> None:
    result = await session.execute(
        select(BillingPlan).where(BillingPlan.code == seed.code)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        plan = BillingPlan(code=seed.code)
        session.add(plan)

    plan.title = seed.title
    plan.description = seed.description
    plan.billing_period = seed.billing_period
    plan.trial_days = seed.trial_days
    plan.is_active = seed.is_active
    await session.flush()

    for price_seed in seed.prices:
        price_result = await session.execute(
            select(BillingPrice).where(
                BillingPrice.plan_id == plan.id,
                BillingPrice.provider == price_seed.provider,
                BillingPrice.provider_price_id == price_seed.provider_price_id,
            )
        )
        price = price_result.scalar_one_or_none()
        if price is None:
            price = BillingPrice(
                plan_id=plan.id,
                provider=price_seed.provider,
                provider_price_id=price_seed.provider_price_id,
            )
            session.add(price)
        price.amount_minor = price_seed.amount_minor
        price.currency = price_seed.currency
        price.billing_period = price_seed.billing_period
        price.is_active = price_seed.is_active

    for entitlement_seed in seed.entitlements:
        entitlement_result = await session.execute(
            select(PlanEntitlement).where(
                PlanEntitlement.plan_id == plan.id,
                PlanEntitlement.feature_code == entitlement_seed.feature_code,
            )
        )
        entitlement = entitlement_result.scalar_one_or_none()
        if entitlement is None:
            entitlement = PlanEntitlement(
                plan_id=plan.id,
                feature_code=entitlement_seed.feature_code,
            )
            session.add(entitlement)
        entitlement.limit_value = entitlement_seed.limit_value
        entitlement.reset_period = entitlement_seed.reset_period


async def _deactivate_obsolete_plans(session) -> None:
    result = await session.execute(
        select(BillingPlan).where(BillingPlan.code.in_(OBSOLETE_PLAN_CODES))
    )
    for plan in result.scalars():
        plan.is_active = False
        await session.execute(
            update(BillingPrice)
            .where(BillingPrice.plan_id == plan.id)
            .values(is_active=False)
        )


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        for plan in PLANS:
            await _upsert_plan(session, plan)
        await _deactivate_obsolete_plans(session)
        await session.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
