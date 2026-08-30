"""FraudForge AI: Production-Style Risk-Aware Decision Engine.

Transforms continuous fraud probabilities and transaction indicators into
actionable, explainable, and multi-tier payment defense decisions:
Fraud Probability -> Risk Level -> Payment Action -> Reason Codes -> Mitigation

Risk Tiers:
- LOW: [0.00, 0.30) -> ALLOW
- MEDIUM: [0.30, 0.60) -> MONITOR
- HIGH: [0.60, 0.85) -> STEP_UP_AUTH
- CRITICAL: [0.85, 1.00] -> BLOCK

This is a simulated defense policy engine for research and prototyping.
"""

from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
import pandas as pd

from src.detection.predict import FraudDetector
from src.utils.config import MODELS_DIR


# =============================================================================
# ENUMS & DATA STRUCTURES
# =============================================================================

class RiskLevel(str, Enum):
    """Categorical risk tiers for payment transactions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PaymentAction(str, Enum):
    """Defensive actions taken by the payment decision engine."""
    ALLOW = "ALLOW"
    MONITOR = "MONITOR"
    STEP_UP_AUTH = "STEP_UP_AUTH"
    BLOCK = "BLOCK"


class PolicyMode(str, Enum):
    """Standard operational profiles for the risk engine."""
    BALANCED = "BALANCED"
    STRICT_SECURITY = "STRICT_SECURITY"
    CUSTOM = "CUSTOM"


@dataclass
class RiskThresholds:
    """Configurable decision boundaries for risk tiers."""
    low_max: float = 0.30       # [0.00, low_max) -> LOW / ALLOW
    medium_max: float = 0.60    # [low_max, medium_max) -> MEDIUM / MONITOR
    high_max: float = 0.85      # [medium_max, high_max) -> HIGH / STEP_UP_AUTH
                                # [high_max, 1.00] -> CRITICAL / BLOCK

    def __post_init__(self):
        if not (0.0 <= self.low_max <= self.medium_max <= self.high_max <= 1.0):
            raise ValueError(
                f"Invalid threshold ordering: low_max={self.low_max}, "
                f"medium_max={self.medium_max}, high_max={self.high_max}. "
                f"Must satisfy 0.0 <= low_max <= medium_max <= high_max <= 1.0"
            )


@dataclass
class RiskReasonCode:
    """Structured, explainable indicator contributing to the risk evaluation."""
    code: str
    feature: str
    value: Any
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskDecision:
    """Complete structured output from the Risk Decision Engine."""
    transaction_id: str
    fraud_probability: float
    risk_score: float  # [0.0, 100.0]
    risk_level: RiskLevel
    action: PaymentAction
    reason_codes: List[str]
    detailed_reasons: List[Dict[str, Any]]
    recommended_verification_methods: List[str]
    policy_mode: str
    policy_version: str
    model_version: str
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["risk_level"] = self.risk_level.value
        d["action"] = self.action.value
        return d


# =============================================================================
# RISK POLICY DEFINITIONS
# =============================================================================

class RiskPolicy:
    """Encapsulates risk decision thresholds and policy mapping."""

    PRESET_THRESHOLDS: Dict[PolicyMode, RiskThresholds] = {
        PolicyMode.BALANCED: RiskThresholds(low_max=0.30, medium_max=0.60, high_max=0.85),
        PolicyMode.STRICT_SECURITY: RiskThresholds(low_max=0.20, medium_max=0.45, high_max=0.70),
    }

    def __init__(
        self,
        mode: Union[PolicyMode, str] = PolicyMode.BALANCED,
        custom_thresholds: Optional[RiskThresholds] = None,
        policy_version: str = "v1.0",
    ):
        if isinstance(mode, str):
            mode = PolicyMode(mode.upper())
        self.mode = mode
        self.policy_version = f"{mode.value.lower()}_{policy_version}"

        if mode == PolicyMode.CUSTOM:
            if custom_thresholds is None:
                raise ValueError("custom_thresholds must be provided when mode is CUSTOM")
            self.thresholds = custom_thresholds
        else:
            self.thresholds = custom_thresholds or self.PRESET_THRESHOLDS[mode]

    def evaluate_probability(self, prob: float) -> Tuple[RiskLevel, PaymentAction]:
        """Map raw probability to RiskLevel and PaymentAction."""
        p = float(np.clip(prob, 0.0, 1.0))

        if p < self.thresholds.low_max:
            return RiskLevel.LOW, PaymentAction.ALLOW
        elif p < self.thresholds.medium_max:
            return RiskLevel.MEDIUM, PaymentAction.MONITOR
        elif p < self.thresholds.high_max:
            return RiskLevel.HIGH, PaymentAction.STEP_UP_AUTH
        else:
            return RiskLevel.CRITICAL, PaymentAction.BLOCK


# =============================================================================
# REASON CODES & EXPLAINABILITY ENGINE
# =============================================================================

class ReasonCodeGenerator:
    """Extracts transparent, feature-grounded reason codes from transaction data."""

    @staticmethod
    def extract_reasons(tx: Dict[str, Any], prob: float) -> List[RiskReasonCode]:
        """Analyze transaction features and extract true matching reason codes."""
        reasons: List[RiskReasonCode] = []

        # 1. Device Change & Age
        device_change = tx.get("device_change", 0)
        device_age = tx.get("device_age_days", 999)
        if device_change == 1 or device_age < 3:
            sev = "CRITICAL" if device_age < 2 and device_change == 1 else "HIGH"
            reasons.append(RiskReasonCode(
                code="DEVICE_CHANGE",
                feature="device_change",
                value={"device_change": device_change, "device_age_days": device_age},
                severity=sev,
                description="New or unrecognized device detected with minimal device tenure.",
            ))

        # 2. Transaction Velocity
        v1h = tx.get("transaction_velocity_1h", 0)
        v24h = tx.get("transaction_velocity_24h", 0)
        if v1h >= 4 or v24h >= 10:
            sev = "CRITICAL" if v1h >= 6 or v24h >= 14 else "HIGH"
            reasons.append(RiskReasonCode(
                code="HIGH_TRANSACTION_VELOCITY",
                feature="transaction_velocity_1h",
                value={"velocity_1h": v1h, "velocity_24h": v24h},
                severity=sev,
                description="Transaction frequency significantly exceeds baseline velocity thresholds.",
            ))

        # 3. Unusual Amount & Deviation
        amt_dev = tx.get("amount_deviation", 0.0)
        amount = tx.get("transaction_amount", 0.0)
        if amt_dev >= 2.5 or amount >= 600.0:
            sev = "HIGH" if amt_dev >= 4.0 or amount >= 1000.0 else "MEDIUM"
            reasons.append(RiskReasonCode(
                code="UNUSUAL_AMOUNT",
                feature="amount_deviation",
                value={"amount": round(float(amount), 2), "amount_deviation": round(float(amt_dev), 2)},
                severity=sev,
                description="Transaction value deviates substantially from cardholder spending history.",
            ))

        # 4. IP Risk Score
        ip_risk = tx.get("IP_risk_score", 0.0)
        if ip_risk >= 0.55:
            sev = "CRITICAL" if ip_risk >= 0.75 else "HIGH"
            reasons.append(RiskReasonCode(
                code="HIGH_IP_RISK",
                feature="IP_risk_score",
                value=round(float(ip_risk), 3),
                severity=sev,
                description="Transaction originating from high-risk, proxy, or suspicious network IP address.",
            ))

        # 5. Merchant Risk Score
        merch_risk = tx.get("merchant_risk_score", 0.0)
        if merch_risk >= 0.55:
            sev = "HIGH" if merch_risk >= 0.70 else "MEDIUM"
            reasons.append(RiskReasonCode(
                code="HIGH_MERCHANT_RISK",
                feature="merchant_risk_score",
                value=round(float(merch_risk), 3),
                severity=sev,
                description="Elevated merchant category dispute or historical chargeback risk.",
            ))

        # 6. Identity Risk Score & Account Age
        id_risk = tx.get("identity_risk_score", 0.0)
        acc_age = tx.get("account_age_days", 999)
        if id_risk >= 0.55 or acc_age < 10:
            sev = "HIGH" if id_risk >= 0.70 or acc_age < 5 else "MEDIUM"
            reasons.append(RiskReasonCode(
                code="HIGH_IDENTITY_RISK",
                feature="identity_risk_score",
                value={"identity_risk_score": round(float(id_risk), 3), "account_age_days": acc_age},
                severity=sev,
                description="Synthetic identity or recently created account profile with high risk score.",
            ))

        # 7. Behavioral Deviation
        beh_dev = tx.get("behavioral_deviation", 0.0)
        if beh_dev >= 0.35:
            sev = "HIGH" if beh_dev >= 0.60 else "MEDIUM"
            reasons.append(RiskReasonCode(
                code="BEHAVIORAL_DEVIATION",
                feature="behavioral_deviation",
                value=round(float(beh_dev), 3),
                severity=sev,
                description="Cardholder interaction timing, navigation, or session pattern is anomalous.",
            ))

        # 8. Geographic Deviation
        geo_dev = tx.get("geographic_deviation", 0)
        if geo_dev == 1:
            reasons.append(RiskReasonCode(
                code="GEOGRAPHIC_DEVIATION",
                feature="geographic_deviation",
                value=1,
                severity="HIGH",
                description="Physical or IP geolocation is inconsistent with cardholder historical location.",
            ))

        # 9. Failed Authentications
        failed_auth = tx.get("failed_authentication_count", 0)
        if failed_auth >= 2:
            sev = "CRITICAL" if failed_auth >= 3 else "HIGH"
            reasons.append(RiskReasonCode(
                code="FAILED_AUTHENTICATIONS",
                feature="failed_authentication_count",
                value=failed_auth,
                severity=sev,
                description="Multiple prior failed authentication or PIN/OTP attempts detected.",
            ))

        # 10. Unusual Transaction Time (Off-Hours)
        hour = tx.get("transaction_hour", 12)
        if hour in [1, 2, 3, 4]:
            reasons.append(RiskReasonCode(
                code="UNUSUAL_TRANSACTION_TIME",
                feature="transaction_hour",
                value=hour,
                severity="LOW",
                description="Transaction executed during anomalous off-hours window (01:00 - 05:00).",
            ))

        # 11. Cross-Channel / Headless Activity
        channel = str(tx.get("payment_channel", "e-commerce"))
        if channel in ["api_gateway", "recurring_subscription"] and (v1h >= 2 or ip_risk >= 0.40):
            reasons.append(RiskReasonCode(
                code="CROSS_CHANNEL_ACTIVITY",
                feature="payment_channel",
                value=channel,
                severity="MEDIUM",
                description=f"Automated, headless, or high-risk payment channel invocation ({channel}).",
            ))

        return reasons

    @staticmethod
    def recommend_verifications(
        action: PaymentAction,
        tx: Dict[str, Any],
        reasons: List[RiskReasonCode],
    ) -> List[str]:
        """Determine appropriate step-up verification methods for challenged transactions."""
        if action != PaymentAction.STEP_UP_AUTH:
            return []

        methods: List[str] = []
        channel = str(tx.get("payment_channel", "e-commerce"))
        has_device_change = any(r.code == "DEVICE_CHANGE" for r in reasons)
        has_geo_dev = any(r.code == "GEOGRAPHIC_DEVIATION" for r in reasons)

        if channel in ["mobile_app", "pos_contactless"]:
            methods.append("BIOMETRIC_PUSH_CONFIRMATION")
        if channel in ["e-commerce", "api_gateway"]:
            methods.append("EMV_3DS_V2_CHALLENGE")
        if has_device_change or has_geo_dev:
            methods.append("TRUSTED_DEVICE_CONFIRMATION")
        methods.append("SMS_OR_EMAIL_OTP")

        # Deduplicate preserving order
        seen = set()
        deduped = []
        for m in methods:
            if m not in seen:
                seen.add(m)
                deduped.append(m)
        return deduped


# =============================================================================
# RISK DECISION ENGINE
# =============================================================================

class RiskDecisionEngine:
    """Production-grade Risk Decision Engine transforming ML probabilities into actions."""

    def __init__(
        self,
        detector: Optional[FraudDetector] = None,
        policy: Optional[RiskPolicy] = None,
        policy_mode: PolicyMode = PolicyMode.BALANCED,
        model_version: str = "hardened_zero_day_v1",
    ):
        self.detector = detector
        if self.detector is None:
            model_path = MODELS_DIR / "hardened_zero_day_detector.joblib"
            if not model_path.exists():
                model_path = MODELS_DIR / "baseline_detector.joblib"
            if model_path.exists():
                self.detector = FraudDetector(artifact_path=model_path)

        self.policy = policy or RiskPolicy(mode=policy_mode)
        self.model_version = model_version
        self.reason_generator = ReasonCodeGenerator()

    def evaluate_probability(
        self,
        fraud_probability: float,
        transaction_context: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> RiskDecision:
        """Score a raw probability directly through the risk decision policy."""
        prob = float(np.clip(fraud_probability, 0.0, 1.0))
        risk_score = float(np.round(prob * 100.0, 1))
        risk_level, action = self.policy.evaluate_probability(prob)

        ctx = transaction_context or {}
        detailed_reasons = self.reason_generator.extract_reasons(ctx, prob)
        reason_codes = [r.code for r in detailed_reasons]
        verifications = self.reason_generator.recommend_verifications(action, ctx, detailed_reasons)

        tx_id = transaction_id or str(ctx.get("transaction_id", f"TX-{abs(hash(prob)) % 1000000:06d}"))

        return RiskDecision(
            transaction_id=tx_id,
            fraud_probability=round(prob, 4),
            risk_score=risk_score,
            risk_level=risk_level,
            action=action,
            reason_codes=reason_codes,
            detailed_reasons=[r.to_dict() for r in detailed_reasons],
            recommended_verification_methods=verifications,
            policy_mode=self.policy.mode.value,
            policy_version=self.policy.policy_version,
            model_version=self.model_version,
        )

    def evaluate_transaction(
        self,
        transaction: Union[Dict[str, Any], pd.Series, pd.DataFrame],
    ) -> Dict[str, Any]:
        """End-to-end evaluation: Feature Pipeline -> ML Detector -> Risk Engine -> Decision."""
        if self.detector is None:
            raise RuntimeError("FraudDetector model is not loaded in RiskDecisionEngine.")

        if isinstance(transaction, pd.Series):
            df_single = pd.DataFrame([transaction.to_dict()])
            tx_dict = transaction.to_dict()
        elif isinstance(transaction, pd.DataFrame):
            df_single = transaction.head(1).copy()
            tx_dict = df_single.iloc[0].to_dict()
        else:
            tx_dict = transaction.copy()
            df_single = pd.DataFrame([tx_dict])

        prob = float(self.detector.predict_proba(df_single)[0])
        decision = self.evaluate_probability(
            fraud_probability=prob,
            transaction_context=tx_dict,
            transaction_id=str(tx_dict.get("transaction_id", "")),
        )
        return decision.to_dict()

    def evaluate_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Batch evaluate a DataFrame of transactions without modifying the original data."""
        if self.detector is None:
            raise RuntimeError("FraudDetector model is not loaded in RiskDecisionEngine.")

        probs = self.detector.predict_proba(df)
        out_df = df.copy()

        risk_scores = np.round(probs * 100.0, 1)
        risk_levels = []
        actions = []
        reason_codes_list = []
        recommendations_list = []

        # Iterate over records to generate explainable reason codes
        records = df.to_dict(orient="records")
        for i, row in enumerate(records):
            p = float(probs[i])
            rl, act = self.policy.evaluate_probability(p)
            reasons = self.reason_generator.extract_reasons(row, p)
            verifs = self.reason_generator.recommend_verifications(act, row, reasons)

            risk_levels.append(rl.value)
            actions.append(act.value)
            reason_codes_list.append([r.code for r in reasons])
            recommendations_list.append(verifs)

        out_df["fraud_probability"] = np.round(probs, 4)
        out_df["risk_score"] = risk_scores
        out_df["risk_level"] = risk_levels
        out_df["action"] = actions
        out_df["reason_codes"] = reason_codes_list
        out_df["recommended_verifications"] = recommendations_list
        out_df["policy_mode"] = self.policy.mode.value

        return out_df


def evaluate_transaction(
    transaction: Union[Dict[str, Any], pd.Series, pd.DataFrame],
    detector: Optional[FraudDetector] = None,
    policy_mode: PolicyMode = PolicyMode.BALANCED,
) -> Dict[str, Any]:
    """Convenience top-level API for scoring a transaction through the risk engine."""
    engine = RiskDecisionEngine(detector=detector, policy_mode=policy_mode)
    return engine.evaluate_transaction(transaction)


if __name__ == "__main__":
    # Quick standalone test demo
    print("=" * 60)
    print(" FRAUDFORGE AI — RISK-AWARE DECISION ENGINE DEMO")
    print("=" * 60)

    sample_tx = {
        "transaction_id": "TX-10482",
        "transaction_amount": 750.0,
        "transaction_hour": 3,
        "account_age_days": 120,
        "device_age_days": 1,
        "device_change": 1,
        "IP_risk_score": 0.82,
        "merchant_risk_score": 0.65,
        "transaction_velocity_1h": 7,
        "transaction_velocity_24h": 15,
        "average_customer_amount": 65.0,
        "amount_deviation": 10.5,
        "geographic_deviation": 1,
        "behavioral_deviation": 0.72,
        "failed_authentication_count": 2,
        "identity_risk_score": 0.45,
        "merchant_category": "digital_goods",
        "payment_channel": "mobile_app",
        "authentication_method": "sms_otp",
        "transaction_country": "US",
        "customer_country": "US",
    }

    try:
        engine = RiskDecisionEngine(policy_mode=PolicyMode.BALANCED)
        decision = engine.evaluate_transaction(sample_tx)

        print(f"\nTransaction ID:     {decision['transaction_id']}")
        print(f"Fraud Probability:  {decision['fraud_probability']}")
        print(f"Risk Score:         {decision['risk_score']} / 100")
        print(f"Risk Level:         {decision['risk_level']}")
        print(f"Defensive Action:   {decision['action']}")
        print(f"\nReason Codes:")
        for r in decision["detailed_reasons"]:
            print(f"  • [{r['severity']}] {r['code']}: {r['description']}")
        print(f"\nRecommended Verifications: {decision['recommended_verification_methods']}")
        print("=" * 60)
    except Exception as exc:
        print(f"Error during demo: {exc}")
