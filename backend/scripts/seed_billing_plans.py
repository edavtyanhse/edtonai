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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@dataclass(frozen=True)
class SeedPrice:
    provider: str
    provider_price_id: str | None
    amount_minor: int
    currency: str
    billing_period: str


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
    prices: tuple[SeedPrice, ...]
    entitlements: tuple[SeedEntitlement, ...]


PLANS: tuple[SeedPlan, ...] = (
    SeedPlan(
        code="free",
        title="Free",
        description="Temporary public access before commercial launch.",
        billing_period="month",
        trial_days=0,
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
            SeedEntitlement(AI_OPERATION_FEATURE, 1_000_000, "month"),
        ),
    ),
    SeedPlan(
        code="basic",
        title="Basic",
        description="Starter subscription placeholder.",
        billing_period="month",
        trial_days=7,
        prices=(
            SeedPrice(
                provider="noop",
                provider_price_id="noop_basic_monthly",
                amount_minor=49000,
                currency="RUB",
                billing_period="month",
            ),
        ),
        entitlements=(
            SeedEntitlement(AI_OPERATION_FEATURE, 100, "month"),
        ),
    ),
    SeedPlan(
        code="pro",
        title="Pro",
        description="Higher usage subscription placeholder.",
        billing_period="month",
        trial_days=7,
        prices=(
            SeedPrice(
                provider="noop",
                provider_price_id="noop_pro_monthly",
                amount_minor=99000,
                currency="RUB",
                billing_period="month",
            ),
        ),
        entitlements=(
            SeedEntitlement(AI_OPERATION_FEATURE, 300, "month"),
        ),
    ),
)


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
    plan.is_active = True
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
        price.is_active = True

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


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        for plan in PLANS:
            await _upsert_plan(session, plan)
        await session.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
