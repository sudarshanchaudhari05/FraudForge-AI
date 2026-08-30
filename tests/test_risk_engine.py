"""Unit tests for Phase 7 Risk Decision Engine."""

import pytest
import pandas as pd
import numpy as np

from src.detection.risk_engine import (
    RiskDecisionEngine,
    RiskPolicy,
    RiskThresholds,
    PolicyMode,
    RiskLevel,
    PaymentAction,
    ReasonCodeGenerator,
    evaluate_transaction,
)


def test_threshold_ordering_validation():
    """Verify that invalid threshold bounds raise ValueError."""
    with pytest.raises(ValueError):
        RiskThresholds(low_max=0.8, medium_max=0.4, high_max=0.9)

    with pytest.raises(ValueError):
        RiskThresholds(low_max=-0.1, medium_max=0.5, high_max=0.8)

    valid = RiskThresholds(low_max=0.25, medium_max=0.55, high_max=0.80)
    assert valid.low_max == 0.25


def test_policy_probability_mapping():
    """Verify mapping of raw probabilities to risk levels and actions under Balanced & Strict policies."""
    bal_policy = RiskPolicy(mode=PolicyMode.BALANCED)
    strict_policy = RiskPolicy(mode=PolicyMode.STRICT_SECURITY)

    # Balanced: [0.0-0.30) -> LOW, [0.30-0.60) -> MED, [0.60-0.85) -> HIGH, [0.85-1.0] -> CRIT
    lvl, act = bal_policy.evaluate_probability(0.15)
    assert lvl == RiskLevel.LOW
    assert act == PaymentAction.ALLOW

    lvl, act = bal_policy.evaluate_probability(0.45)
    assert lvl == RiskLevel.MEDIUM
    assert act == PaymentAction.MONITOR

    lvl, act = bal_policy.evaluate_probability(0.70)
    assert lvl == RiskLevel.HIGH
    assert act == PaymentAction.STEP_UP_AUTH

    lvl, act = bal_policy.evaluate_probability(0.92)
    assert lvl == RiskLevel.CRITICAL
    assert act == PaymentAction.BLOCK

    # Strict: [0.0-0.20) -> LOW, [0.20-0.45) -> MED, [0.45-0.70) -> HIGH, [0.70-1.0] -> CRIT
    lvl, act = strict_policy.evaluate_probability(0.22)
    assert lvl == RiskLevel.MEDIUM
    assert act == PaymentAction.MONITOR

    lvl, act = strict_policy.evaluate_probability(0.55)
    assert lvl == RiskLevel.HIGH
    assert act == PaymentAction.STEP_UP_AUTH

    lvl, act = strict_policy.evaluate_probability(0.75)
    assert lvl == RiskLevel.CRITICAL
    assert act == PaymentAction.BLOCK


def test_reason_codes_generation():
    """Verify explainable reason codes trigger correctly only on matching conditions."""
    sample_tx = {
        "transaction_id": "TX-TEST-01",
        "device_change": 1,
        "device_age_days": 1,
        "transaction_velocity_1h": 8,
        "transaction_velocity_24h": 18,
        "amount_deviation": 5.2,
        "transaction_amount": 850.0,
        "IP_risk_score": 0.88,
        "merchant_risk_score": 0.72,
        "identity_risk_score": 0.65,
        "behavioral_deviation": 0.68,
        "geographic_deviation": 1,
        "failed_authentication_count": 3,
        "transaction_hour": 3,
        "payment_channel": "mobile_app",
    }

    reasons = ReasonCodeGenerator.extract_reasons(sample_tx, prob=0.92)
    codes = {r.code for r in reasons}

    assert "DEVICE_CHANGE" in codes
    assert "HIGH_TRANSACTION_VELOCITY" in codes
    assert "UNUSUAL_AMOUNT" in codes
    assert "HIGH_IP_RISK" in codes
    assert "HIGH_MERCHANT_RISK" in codes
    assert "HIGH_IDENTITY_RISK" in codes
    assert "BEHAVIORAL_DEVIATION" in codes
    assert "GEOGRAPHIC_DEVIATION" in codes
    assert "FAILED_AUTHENTICATIONS" in codes
    assert "UNUSUAL_TRANSACTION_TIME" in codes

    # Benign transaction should generate zero or minimal reasons
    benign_tx = {
        "transaction_id": "TX-BENIGN-01",
        "device_change": 0,
        "device_age_days": 180,
        "transaction_velocity_1h": 1,
        "transaction_velocity_24h": 2,
        "amount_deviation": 0.1,
        "transaction_amount": 45.0,
        "IP_risk_score": 0.05,
        "merchant_risk_score": 0.12,
        "identity_risk_score": 0.08,
        "behavioral_deviation": 0.04,
        "geographic_deviation": 0,
        "failed_authentication_count": 0,
        "transaction_hour": 14,
        "payment_channel": "e-commerce",
    }
    benign_reasons = ReasonCodeGenerator.extract_reasons(benign_tx, prob=0.02)
    assert len(benign_reasons) == 0


def test_step_up_recommendations():
    """Verify recommended verification methods for step-up challenges."""
    tx_mobile = {"payment_channel": "mobile_app", "device_change": 1}
    reasons = ReasonCodeGenerator.extract_reasons(tx_mobile, prob=0.70)
    methods = ReasonCodeGenerator.recommend_verifications(PaymentAction.STEP_UP_AUTH, tx_mobile, reasons)

    assert "BIOMETRIC_PUSH_CONFIRMATION" in methods
    assert "TRUSTED_DEVICE_CONFIRMATION" in methods
    assert "SMS_OR_EMAIL_OTP" in methods


def test_risk_decision_engine_single_and_batch_evaluation():
    """Verify single and batch transaction scoring via RiskDecisionEngine."""
    engine = RiskDecisionEngine(policy_mode=PolicyMode.BALANCED)

    # 1. Direct probability evaluation
    decision = engine.evaluate_probability(
        fraud_probability=0.72,
        transaction_context={"transaction_id": "TX-999", "payment_channel": "e-commerce"},
    )
    assert decision.risk_score == 72.0
    assert decision.risk_level == RiskLevel.HIGH
    assert decision.action == PaymentAction.STEP_UP_AUTH
    assert len(decision.recommended_verification_methods) > 0

    # 2. Batch DataFrame Evaluation
    test_df = pd.DataFrame([
        {
            "transaction_id": "TX-01",
            "transaction_amount": 50.0,
            "transaction_hour": 12,
            "account_age_days": 100,
            "device_age_days": 50,
            "device_change": 0,
            "IP_risk_score": 0.10,
            "merchant_risk_score": 0.15,
            "transaction_velocity_1h": 1,
            "transaction_velocity_24h": 2,
            "average_customer_amount": 45.0,
            "amount_deviation": 0.1,
            "geographic_deviation": 0,
            "behavioral_deviation": 0.05,
            "failed_authentication_count": 0,
            "identity_risk_score": 0.10,
            "merchant_category": "groceries",
            "payment_channel": "pos_chip",
            "authentication_method": "pin",
            "transaction_country": "US",
            "customer_country": "US",
            "fraud_label": 0,
        },
        {
            "transaction_id": "TX-02",
            "transaction_amount": 800.0,
            "transaction_hour": 3,
            "account_age_days": 5,
            "device_age_days": 1,
            "device_change": 1,
            "IP_risk_score": 0.90,
            "merchant_risk_score": 0.70,
            "transaction_velocity_1h": 8,
            "transaction_velocity_24h": 16,
            "average_customer_amount": 50.0,
            "amount_deviation": 15.0,
            "geographic_deviation": 1,
            "behavioral_deviation": 0.85,
            "failed_authentication_count": 3,
            "identity_risk_score": 0.80,
            "merchant_category": "digital_goods",
            "payment_channel": "mobile_app",
            "authentication_method": "sms_otp",
            "transaction_country": "US",
            "customer_country": "US",
            "fraud_label": 1,
        }
    ])

    batch_res = engine.evaluate_batch(test_df)
    assert len(batch_res) == 2
    assert "fraud_probability" in batch_res.columns
    assert "risk_score" in batch_res.columns
    assert "risk_level" in batch_res.columns
    assert "action" in batch_res.columns
    assert "reason_codes" in batch_res.columns

    # Original DataFrame must not be mutated
    assert "fraud_probability" not in test_df.columns
