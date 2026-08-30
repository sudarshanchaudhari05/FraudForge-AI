"""Unit tests for Phase 7 Threshold Analysis & Calibration Audit."""

import pytest
from pathlib import Path
import numpy as np
import pandas as pd

from src.detection.threshold_analysis import (
    ThresholdAnalysisEngine,
    calculate_expected_calibration_error,
    FALSE_NEGATIVE_COST,
    FALSE_POSITIVE_COST,
    STEP_UP_COST,
)
from src.detection.risk_engine import PolicyMode


def test_expected_calibration_error_calculation():
    """Verify ECE calculation and bin reliability stats on synthetic probabilities."""
    y_true = np.array([0, 0, 0, 0, 1, 0, 1, 1, 1, 1])
    y_prob = np.array([0.05, 0.10, 0.20, 0.30, 0.55, 0.60, 0.80, 0.85, 0.90, 0.95])

    ece, bins = calculate_expected_calibration_error(y_true, y_prob, n_bins=5)
    assert 0.0 <= ece <= 1.0
    assert len(bins) > 0
    for b in bins:
        assert "bin_range" in b
        assert "calibration_gap" in b
        assert b["sample_count"] > 0


def test_threshold_sweep_and_cost_calculation(tmp_path):
    """Verify threshold sweep on validation dataframe."""
    engine = ThresholdAnalysisEngine(output_dir=tmp_path)

    # Synthetic validation dataset
    val_df = pd.DataFrame([
        {
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
        }
        for _ in range(20)
    ] + [
        {
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
        for _ in range(10)
    ])

    sweep = engine.evaluate_threshold_sweep(val_df, thresholds=[0.30, 0.50, 0.70])
    assert len(sweep) == 3
    for s in sweep:
        assert "threshold" in s
        assert "precision" in s
        assert "recall" in s
        assert "fpr" in s
        assert "simulated_relative_cost" in s
        assert s["simulated_relative_cost"] >= 0.0


def test_policy_dataset_evaluation(tmp_path):
    """Verify multi-tier policy evaluation against synthetic dataset."""
    engine = ThresholdAnalysisEngine(output_dir=tmp_path)

    test_df = pd.DataFrame([
        {
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
        }
        for _ in range(10)
    ] + [
        {
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
        for _ in range(5)
    ])

    eval_res = engine.evaluate_policy_on_dataset(test_df, "Test Synthetic Suite", PolicyMode.BALANCED)
    assert "metrics" in eval_res
    assert "action_distribution" in eval_res
    assert "cost_analysis" in eval_res
    assert eval_res["action_distribution"]["ALLOW"] + eval_res["action_distribution"]["MONITOR"] + eval_res["action_distribution"]["STEP_UP_AUTH"] + eval_res["action_distribution"]["BLOCK"] == 15
