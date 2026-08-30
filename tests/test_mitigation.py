"""Unit tests for Phase 7 Mitigation Simulator."""

import pytest
from src.detection.mitigation import MitigationSimulator, MitigationStatus
from src.detection.risk_engine import PaymentAction, RiskLevel


def test_mitigation_actions_mapping():
    """Verify all four payment actions map to appropriate mitigation responses."""
    # 1. ALLOW -> APPROVED
    allow_dec = {
        "transaction_id": "TX-001",
        "action": PaymentAction.ALLOW.value,
        "risk_score": 12.5,
        "risk_level": RiskLevel.LOW.value,
        "reason_codes": [],
    }
    resp = MitigationSimulator.execute_mitigation(allow_dec)
    assert resp["status"] == MitigationStatus.APPROVED.value
    assert resp["requires_customer_action"] is False
    assert resp["audit_flag"] is False

    # 2. MONITOR -> APPROVED_MONITORED
    mon_dec = {
        "transaction_id": "TX-002",
        "action": PaymentAction.MONITOR.value,
        "risk_score": 45.0,
        "risk_level": RiskLevel.MEDIUM.value,
        "reason_codes": ["UNUSUAL_AMOUNT"],
    }
    resp = MitigationSimulator.execute_mitigation(mon_dec)
    assert resp["status"] == MitigationStatus.APPROVED_MONITORED.value
    assert resp["requires_customer_action"] is False
    assert resp["audit_flag"] is True

    # 3. STEP_UP_AUTH -> CHALLENGE_REQUIRED
    step_dec = {
        "transaction_id": "TX-003",
        "action": PaymentAction.STEP_UP_AUTH.value,
        "risk_score": 75.0,
        "risk_level": RiskLevel.HIGH.value,
        "reason_codes": ["HIGH_IP_RISK", "DEVICE_CHANGE"],
        "recommended_verification_methods": ["EMV_3DS_V2_CHALLENGE", "SMS_OR_EMAIL_OTP"],
    }
    resp = MitigationSimulator.execute_mitigation(step_dec)
    assert resp["status"] == MitigationStatus.CHALLENGE_REQUIRED.value
    assert resp["challenge_type"] == "EMV_3DS_V2_CHALLENGE"
    assert resp["requires_customer_action"] is True
    assert resp["audit_flag"] is True

    # 4. BLOCK -> REJECTED
    block_dec = {
        "transaction_id": "TX-004",
        "action": PaymentAction.BLOCK.value,
        "risk_score": 96.0,
        "risk_level": RiskLevel.CRITICAL.value,
        "reason_codes": ["HIGH_TRANSACTION_VELOCITY", "FAILED_AUTHENTICATIONS"],
    }
    resp = MitigationSimulator.execute_mitigation(block_dec)
    assert resp["status"] == MitigationStatus.REJECTED.value
    assert resp["requires_customer_action"] is False
    assert resp["audit_flag"] is True
