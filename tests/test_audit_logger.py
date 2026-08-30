"""Unit tests for Phase 7 Risk Audit Logger."""

import pytest
from pathlib import Path
import pandas as pd

from src.detection.audit_logger import RiskAuditLogger


def test_audit_logger_single_and_batch_records(tmp_path):
    """Verify single and batch decision audit logging to JSONL and CSV."""
    jsonl_path = tmp_path / "test_audit.jsonl"
    csv_path = tmp_path / "test_audit.csv"
    logger = RiskAuditLogger(log_path=jsonl_path, csv_path=csv_path)

    # 1. Single Decision Logging
    single_dec = {
        "transaction_id": "TX-1001",
        "fraud_probability": 0.94,
        "risk_score": 94.0,
        "risk_level": "CRITICAL",
        "action": "BLOCK",
        "reason_codes": ["HIGH_IP_RISK", "UNUSUAL_AMOUNT"],
        "model_version": "hardened_zero_day_v1",
        "policy_version": "balanced_v1",
    }
    entry = logger.log_decision(single_dec, mitigation_status="REJECTED")

    assert jsonl_path.exists()
    assert entry["transaction_id"] == "TX-1001"
    assert entry["action"] == "BLOCK"

    logs = logger.read_logs()
    assert len(logs) == 1
    assert logs[0]["transaction_id"] == "TX-1001"
    assert logs[0]["reason_codes"] == ["HIGH_IP_RISK", "UNUSUAL_AMOUNT"]

    # 2. Batch Logging
    batch_df = pd.DataFrame([
        {
            "transaction_id": "TX-2001",
            "fraud_probability": 0.15,
            "risk_score": 15.0,
            "risk_level": "LOW",
            "action": "ALLOW",
            "reason_codes": [],
            "policy_mode": "BALANCED",
        },
        {
            "transaction_id": "TX-2002",
            "fraud_probability": 0.75,
            "risk_score": 75.0,
            "risk_level": "HIGH",
            "action": "STEP_UP_AUTH",
            "reason_codes": ["DEVICE_CHANGE"],
            "policy_mode": "BALANCED",
        }
    ])

    logged_count = logger.log_batch(batch_df, save_csv=True)
    assert logged_count == 2
    assert csv_path.exists()

    all_logs = logger.read_logs()
    assert len(all_logs) == 3
    assert all_logs[1]["transaction_id"] == "TX-2001"
    assert all_logs[2]["transaction_id"] == "TX-2002"
