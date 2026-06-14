"""Regression tests for billing plan seed configuration."""

from backend.scripts.seed_billing_plans import OBSOLETE_PLAN_CODES, PLANS


def test_paid_subscription_periods_match_commercial_prices():
    plans_by_code = {plan.code: plan for plan in PLANS}

    assert set(plans_by_code) == {
        "free",
        "paid_weekly",
        "paid_monthly",
        "paid_quarterly",
    }
    assert set(OBSOLETE_PLAN_CODES) == {"basic", "pro"}
    assert plans_by_code["free"].entitlements[0].limit_value == 5

    expected_prices = {
        "paid_weekly": 15000,
        "paid_monthly": 30000,
        "paid_quarterly": 60000,
    }
    for code in ("paid_weekly", "paid_monthly", "paid_quarterly"):
        plan = plans_by_code[code]
        assert plan.is_active is True
        assert plan.entitlements[0].limit_value is None
        assert plan.prices[0].provider == "tbank"
        assert plan.prices[0].amount_minor == expected_prices[code]
        assert plan.prices[0].is_active is True
