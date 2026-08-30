"""FraudForge AI: Simulated Mitigation & Payment Response Engine.

Executes simulated payment gateway responses corresponding to Risk Engine actions:
ALLOW -> Approved
MONITOR -> Approved with Telemetry Observation
STEP_UP_AUTH -> Challenge Required (OTP, 3DS, Biometric)
BLOCK -> Transaction Rejected / Held

Note: These are simulated defensive mitigations for prototyping and research.
No live financial transactions or payment network connections are executed.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from src.detection.risk_engine import PaymentAction, RiskLevel


class MitigationStatus(str, Enum):
    """Execution status returned by the payment mitigation simulator."""
    APPROVED = "APPROVED"
    APPROVED_MONITORED = "APPROVED_MONITORED"
    CHALLENGE_REQUIRED = "CHALLENGE_REQUIRED"
    REJECTED = "REJECTED"


@dataclass
class MitigationResponse:
    """Standardized response payload from the mitigation simulator."""
    transaction_id: str
    action: str
    status: MitigationStatus
    risk_score: float
    risk_level: str
    message: str
    challenge_type: Optional[str] = None
    recommended_methods: Optional[List[str]] = None
    reason_codes: Optional[List[str]] = None
    requires_customer_action: bool = False
    audit_flag: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


class MitigationSimulator:
    """Simulates real-world payment authorization and step-up challenge flows."""

    @classmethod
    def execute_mitigation(
        cls,
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Convert a RiskDecision dictionary into a simulated payment gateway response."""
        tx_id = str(decision.get("transaction_id", "TX-UNKNOWN"))
        action_str = str(decision.get("action", PaymentAction.ALLOW.value))
        risk_score = float(decision.get("risk_score", 0.0))
        risk_level = str(decision.get("risk_level", RiskLevel.LOW.value))
        reason_codes = decision.get("reason_codes", [])
        verifications = decision.get("recommended_verification_methods", [])

        if action_str == PaymentAction.ALLOW.value or action_str == PaymentAction.ALLOW:
            resp = MitigationResponse(
                transaction_id=tx_id,
                action=PaymentAction.ALLOW.value,
                status=MitigationStatus.APPROVED,
                risk_score=risk_score,
                risk_level=risk_level,
                message="Transaction approved for immediate authorization.",
                reason_codes=reason_codes,
                requires_customer_action=False,
                audit_flag=False,
            )

        elif action_str == PaymentAction.MONITOR.value or action_str == PaymentAction.MONITOR:
            resp = MitigationResponse(
                transaction_id=tx_id,
                action=PaymentAction.MONITOR.value,
                status=MitigationStatus.APPROVED_MONITORED,
                risk_score=risk_score,
                risk_level=risk_level,
                message="Transaction approved with post-authorization telemetry observation and velocity tracking.",
                reason_codes=reason_codes,
                requires_customer_action=False,
                audit_flag=True,
            )

        elif action_str == PaymentAction.STEP_UP_AUTH.value or action_str == PaymentAction.STEP_UP_AUTH:
            primary_method = verifications[0] if verifications else "EMV_3DS_V2_CHALLENGE"
            resp = MitigationResponse(
                transaction_id=tx_id,
                action=PaymentAction.STEP_UP_AUTH.value,
                status=MitigationStatus.CHALLENGE_REQUIRED,
                risk_score=risk_score,
                risk_level=risk_level,
                message="Additional cardholder verification required before payment capture.",
                challenge_type=primary_method,
                recommended_methods=verifications,
                reason_codes=reason_codes,
                requires_customer_action=True,
                audit_flag=True,
            )

        elif action_str == PaymentAction.BLOCK.value or action_str == PaymentAction.BLOCK:
            resp = MitigationResponse(
                transaction_id=tx_id,
                action=PaymentAction.BLOCK.value,
                status=MitigationStatus.REJECTED,
                risk_score=risk_score,
                risk_level=risk_level,
                message="Transaction blocked due to critical risk score and suspicious indicators.",
                reason_codes=reason_codes,
                requires_customer_action=False,
                audit_flag=True,
            )

        else:
            resp = MitigationResponse(
                transaction_id=tx_id,
                action=action_str,
                status=MitigationStatus.REJECTED,
                risk_score=risk_score,
                risk_level=risk_level,
                message=f"Transaction held under unrecognized action '{action_str}'.",
                reason_codes=reason_codes,
                requires_customer_action=False,
                audit_flag=True,
            )

        return resp.to_dict()
