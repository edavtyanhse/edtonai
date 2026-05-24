"""Billing data model regression tests."""

from backend.db.base import Base


def test_billing_tables_are_registered():
    expected_tables = {
        "billing_plan",
        "billing_price",
        "plan_entitlement",
        "billing_customer",
        "user_subscription",
        "usage_event",
        "payment_checkout_session",
        "payment_transaction",
        "payment_provider_event",
        "billing_audit_log",
    }

    assert expected_tables.issubset(Base.metadata.tables)


def test_billing_schema_has_no_raw_card_columns():
    prohibited_fragments = {
        "pan",
        "cvv",
        "cvc",
        "card_number",
        "card_cvv",
        "full_card",
    }

    for table_name in (
        "payment_checkout_session",
        "payment_transaction",
        "payment_provider_event",
        "billing_audit_log",
    ):
        column_names = set(Base.metadata.tables[table_name].columns.keys())
        assert column_names.isdisjoint(prohibited_fragments)


def test_billing_schema_has_idempotency_constraints():
    constraints = {
        constraint.name
        for table_name in (
            "billing_customer",
            "user_subscription",
            "usage_event",
            "payment_checkout_session",
            "payment_transaction",
            "payment_provider_event",
            "billing_audit_log",
        )
        for constraint in Base.metadata.tables[table_name].constraints
    }

    assert "uq_billing_customer_provider_customer" in constraints
    assert "uq_user_subscription_provider_subscription" in constraints
    assert "uq_usage_event_user_feature_idempotency" in constraints
    assert "uq_payment_checkout_session_provider_session" in constraints
    assert "uq_payment_transaction_provider_payment" in constraints
    assert "uq_payment_provider_event_provider_event" in constraints


def test_billing_schema_tracks_provider_status_separately():
    payment_columns = set(Base.metadata.tables["payment_transaction"].columns.keys())
    event_columns = set(Base.metadata.tables["payment_provider_event"].columns.keys())

    assert "provider_status" in payment_columns
    assert "provider_status" in event_columns


def test_billing_schema_has_current_subscription_partial_index():
    indexes = {
        index.name
        for index in Base.metadata.tables["user_subscription"].indexes
    }

    assert "uq_user_subscription_one_current_per_user" in indexes
