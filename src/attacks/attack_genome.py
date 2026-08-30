"""FraudForge AI: Attack Genome Engine.

Decomposes payment fraud archetypes into structured, reusable behavioral genes
and provides mapping, serialization, and simulation parameter synthesis.
All representations are strictly defensive and research-oriented.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Tuple
import copy

from src.attacks.attack_library import AttackArchetype, ATTACK_CATALOG, get_default_attack_library


# =============================================================================
# GENOME VOCABULARY
# =============================================================================

GENOME_VOCABULARY: Dict[str, List[str]] = {
    "target": [
        "account",
        "identity",
        "merchant",
        "payment_agent",
        "checkout",
        "payment_authorization",
        "customer",
    ],
    "entry_vector": [
        "credential_abuse",
        "prompt_manipulation",
        "deepfake_synthesis",
        "social_engineering",
        "session_hijacking",
        "api_exploit",
        "carrier_compromise",
        "document_forgery",
        "malicious_tool",
    ],
    "behavior": [
        "low_and_slow",
        "burst_velocity",
        "behavioral_mimicry",
        "cross_channel",
        "cart_manipulation",
        "identity_fabrication",
        "structuring",
        "chargeback_cycling",
        "arbitrage",
    ],
    "evasion_strategy": [
        "trusted_device_masking",
        "velocity_smoothing",
        "amount_camouflage",
        "trusted_session_behavior",
        "risk_signal_suppression",
        "channel_hopping",
        "geolocation_spoofing",
        "biometric_spoofing",
        "mcc_hopping",
    ],
    "payment_channel": [
        "e-commerce",
        "p2p_transfer",
        "mobile_app",
        "api_gateway",
        "pos_chip",
        "pos_contactless",
        "recurring_subscription",
    ],
    "amount_strategy": [
        "normal_looking",
        "micro_transactions",
        "high_ticket_escalation",
        "sub_threshold_structuring",
        "stealth_discounted",
        "arbitrage_multi_tier",
    ],
    "temporal_strategy": [
        "distributed",
        "off_hours",
        "daytime_peak",
        "rapid_burst",
        "even_interval",
    ],
    "identity_strategy": [
        "existing_account",
        "synthetic_sleeper",
        "fabricated_identity",
        "delegated_agent",
        "swapped_sim",
        "authorized_victim",
    ],
    "merchant_strategy": [
        "single_target",
        "mcc_rotation",
        "high_risk_crypto",
        "digital_marketplace",
        "micro_refunds",
        "luxury_retail",
    ],
    "geographic_strategy": [
        "domestic_matching",
        "cross_border_arbitrage",
        "residential_proxy_spoofed",
    ],
}

GENE_KEYS = list(GENOME_VOCABULARY.keys())


@dataclass
class AttackGenome:
    """Structured gene representation of a payment fraud attack."""

    target: str
    entry_vector: str
    behavior: str
    evasion_strategy: str
    payment_channel: str
    amount_strategy: str
    temporal_strategy: str
    identity_strategy: str
    merchant_strategy: str
    geographic_strategy: str

    # Optional metadata preserved alongside genome
    attack_id: Optional[str] = None
    attack_name: Optional[str] = None
    category: Optional[str] = None

    def get_genes(self) -> Dict[str, str]:
        """Return pure gene dictionary without metadata."""
        return {
            "target": self.target,
            "entry_vector": self.entry_vector,
            "behavior": self.behavior,
            "evasion_strategy": self.evasion_strategy,
            "payment_channel": self.payment_channel,
            "amount_strategy": self.amount_strategy,
            "temporal_strategy": self.temporal_strategy,
            "identity_strategy": self.identity_strategy,
            "merchant_strategy": self.merchant_strategy,
            "geographic_strategy": self.geographic_strategy,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize genome and metadata to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttackGenome":
        """Deserialize from dictionary."""
        clean_data = copy.deepcopy(data)
        return cls(**clean_data)

    def to_simulation_parameters(self) -> Dict[str, Any]:
        """Synthesize concrete transaction generator parameters from genome traits."""
        params: Dict[str, Any] = {
            "payment_channel": self.payment_channel,
        }

        # 1. Merchant Category mapping
        merchant_cat_map = {
            "high_risk_crypto": "crypto_exchange",
            "luxury_retail": "luxury",
            "digital_marketplace": "digital_goods",
            "micro_refunds": "marketplace",
            "single_target": "retail",
            "mcc_rotation": "retail",
        }
        if self.merchant_strategy in merchant_cat_map:
            params["merchant_category"] = merchant_cat_map[self.merchant_strategy]

        # 2. Authentication Method Override
        if self.evasion_strategy == "biometric_spoofing":
            params["auth_method_override"] = "biometric"
        elif self.identity_strategy == "swapped_sim":
            params["auth_method_override"] = "sms_otp"
        elif self.identity_strategy == "authorized_victim":
            params["auth_method_override"] = "sms_otp" if self.temporal_strategy == "off_hours" else "biometric"
        elif self.payment_channel in ["api_gateway", "recurring_subscription"]:
            params["auth_method_override"] = "none"

        # 3. Amount Strategy
        if self.amount_strategy == "micro_transactions":
            params["fixed_amount_range"] = (1.0, 12.0)
        elif self.amount_strategy == "sub_threshold_structuring":
            params["fixed_amount_range"] = (850.0, 995.0)
        elif self.amount_strategy == "stealth_discounted":
            params["amount_multiplier"] = (0.15, 0.45)
        elif self.amount_strategy == "high_ticket_escalation":
            params["amount_multiplier"] = (2.4, 5.5)
        elif self.amount_strategy == "arbitrage_multi_tier":
            params["amount_multiplier"] = (2.0, 4.5)
        elif self.amount_strategy == "normal_looking":
            params["amount_multiplier"] = (1.1, 1.85)

        # 4. Temporal Strategy
        if self.temporal_strategy == "off_hours":
            params["hour_distribution"] = "off_hours"
        elif self.temporal_strategy == "daytime_peak":
            params["hour_distribution"] = "daytime"
        elif self.temporal_strategy == "even_interval":
            params["hour_distribution"] = "business_hours"
        else:
            params["hour_distribution"] = "any"

        # 5. Identity & Device Shifts
        if self.identity_strategy in ["synthetic_sleeper", "fabricated_identity"]:
            params["identity_risk_shift"] = 0.50
            params["account_age_max"] = 30
            params["device_change"] = 1
            params["device_age_max"] = 10
        elif self.identity_strategy == "swapped_sim":
            params["device_change"] = 1
            params["device_age_max"] = 2
            params["identity_risk_shift"] = 0.35
        elif self.identity_strategy == "existing_account":
            params["identity_risk_shift"] = 0.10
        elif self.identity_strategy == "delegated_agent":
            params["identity_risk_shift"] = 0.20

        # 6. Evasion & Behavioral Shifts
        if self.evasion_strategy == "trusted_device_masking":
            params["device_change"] = 0
            params["ip_risk_shift"] = 0.18
        elif self.evasion_strategy == "risk_signal_suppression":
            params["ip_risk_shift"] = 0.15
            params["behavioral_dev_shift"] = 0.10
            params["merchant_risk_shift"] = 0.20
        elif self.evasion_strategy == "geolocation_spoofing" or self.geographic_strategy == "residential_proxy_spoofed":
            params["geographic_deviation"] = 0
            params["ip_risk_shift"] = 0.25
        elif self.evasion_strategy == "velocity_smoothing" or self.behavior == "low_and_slow":
            params["velocity_1h_boost"] = 0
            params["velocity_24h_boost"] = 1
            params["behavioral_dev_shift"] = 0.15

        if self.behavior == "behavioral_mimicry":
            params["behavioral_dev_shift"] = 0.12
        elif self.behavior == "burst_velocity" or self.temporal_strategy == "rapid_burst":
            params["velocity_1h_boost"] = params.get("velocity_1h_boost", 3)
            params["velocity_24h_boost"] = params.get("velocity_24h_boost", 6)
        elif self.behavior == "cart_manipulation":
            params["behavioral_dev_shift"] = 0.40

        # 7. Geographic Strategy
        if self.geographic_strategy == "cross_border_arbitrage":
            params["geographic_deviation"] = 1
        elif self.geographic_strategy in ["domestic_matching", "residential_proxy_spoofed"]:
            params["geographic_deviation"] = 0

        # 8. Clean defaults
        params["failed_auth_count"] = 0 if self.evasion_strategy in [
            "trusted_device_masking",
            "trusted_session_behavior",
            "risk_signal_suppression",
        ] else 0

        return params


# =============================================================================
# GROUND-TRUTH MAPPING OF ALL 28 KNOWN ATTACK ARCHETYPES
# =============================================================================

KNOWN_ATTACK_GENOMES: Dict[str, AttackGenome] = {
    "ATK-001": AttackGenome(
        attack_id="ATK-001",
        attack_name="Voice Clone Executive Impersonation (CEO Fraud / APP)",
        category="AI Social Engineering & Impersonation",
        target="payment_authorization",
        entry_vector="deepfake_synthesis",
        behavior="burst_velocity",
        evasion_strategy="trusted_session_behavior",
        payment_channel="p2p_transfer",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="off_hours",
        identity_strategy="authorized_victim",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    ),
    "ATK-002": AttackGenome(
        attack_id="ATK-002",
        attack_name="Conversational Phishing Agent (AI Romance / Trust Scam)",
        category="AI Social Engineering & Impersonation",
        target="customer",
        entry_vector="social_engineering",
        behavior="low_and_slow",
        evasion_strategy="trusted_device_masking",
        payment_channel="p2p_transfer",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="daytime_peak",
        identity_strategy="authorized_victim",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    ),
    "ATK-003": AttackGenome(
        attack_id="ATK-003",
        attack_name="Deepfake Family Emergency Push Payment",
        category="AI Social Engineering & Impersonation",
        target="customer",
        entry_vector="deepfake_synthesis",
        behavior="burst_velocity",
        evasion_strategy="trusted_device_masking",
        payment_channel="mobile_app",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="distributed",
        identity_strategy="authorized_victim",
        merchant_strategy="single_target",
        geographic_strategy="cross_border_arbitrage",
    ),
    "ATK-004": AttackGenome(
        attack_id="ATK-004",
        attack_name="Automated AI Customer Support / Refund Phishing",
        category="AI Social Engineering & Impersonation",
        target="merchant",
        entry_vector="social_engineering",
        behavior="cart_manipulation",
        evasion_strategy="risk_signal_suppression",
        payment_channel="e-commerce",
        amount_strategy="normal_looking",
        temporal_strategy="daytime_peak",
        identity_strategy="existing_account",
        merchant_strategy="digital_marketplace",
        geographic_strategy="domestic_matching",
    ),
    "ATK-005": AttackGenome(
        attack_id="ATK-005",
        attack_name="Deepfake Video KYC Onboarding Bypass",
        category="Synthetic Identity & Deepfake Onboarding",
        target="identity",
        entry_vector="deepfake_synthesis",
        behavior="identity_fabrication",
        evasion_strategy="biometric_spoofing",
        payment_channel="mobile_app",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="distributed",
        identity_strategy="synthetic_sleeper",
        merchant_strategy="high_risk_crypto",
        geographic_strategy="domestic_matching",
    ),
    "ATK-006": AttackGenome(
        attack_id="ATK-006",
        attack_name="Generative Identity Fabrication (Franken-Identity)",
        category="Synthetic Identity & Deepfake Onboarding",
        target="identity",
        entry_vector="deepfake_synthesis",
        behavior="identity_fabrication",
        evasion_strategy="risk_signal_suppression",
        payment_channel="e-commerce",
        amount_strategy="normal_looking",
        temporal_strategy="distributed",
        identity_strategy="fabricated_identity",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    ),
    "ATK-007": AttackGenome(
        attack_id="ATK-007",
        attack_name="Diffusion Document Forgery (Statement Manipulation)",
        category="Synthetic Identity & Deepfake Onboarding",
        target="identity",
        entry_vector="document_forgery",
        behavior="burst_velocity",
        evasion_strategy="risk_signal_suppression",
        payment_channel="api_gateway",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="distributed",
        identity_strategy="fabricated_identity",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    ),
    "ATK-008": AttackGenome(
        attack_id="ATK-008",
        attack_name="Blended Minor Identity Sleeper Fraud",
        category="Synthetic Identity & Deepfake Onboarding",
        target="identity",
        entry_vector="document_forgery",
        behavior="low_and_slow",
        evasion_strategy="trusted_session_behavior",
        payment_channel="pos_chip",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="distributed",
        identity_strategy="synthetic_sleeper",
        merchant_strategy="luxury_retail",
        geographic_strategy="domestic_matching",
    ),
    "ATK-009": AttackGenome(
        attack_id="ATK-009",
        attack_name="Human Typing & Mouse Cadence Behavioral Mimicry",
        category="Automated Account Takeover & Behavioral Mimicry",
        target="account",
        entry_vector="credential_abuse",
        behavior="behavioral_mimicry",
        evasion_strategy="trusted_device_masking",
        payment_channel="e-commerce",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="luxury_retail",
        geographic_strategy="domestic_matching",
    ),
    "ATK-010": AttackGenome(
        attack_id="ATK-010",
        attack_name="LLM-Orchestrated Adaptive Credential Stuffing",
        category="Automated Account Takeover & Behavioral Mimicry",
        target="account",
        entry_vector="credential_abuse",
        behavior="burst_velocity",
        evasion_strategy="channel_hopping",
        payment_channel="e-commerce",
        amount_strategy="normal_looking",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="single_target",
        geographic_strategy="residential_proxy_spoofed",
    ),
    "ATK-011": AttackGenome(
        attack_id="ATK-011",
        attack_name="Autonomous Session Token Harvesting & Replay",
        category="Automated Account Takeover & Behavioral Mimicry",
        target="checkout",
        entry_vector="session_hijacking",
        behavior="burst_velocity",
        evasion_strategy="trusted_session_behavior",
        payment_channel="api_gateway",
        amount_strategy="normal_looking",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="digital_marketplace",
        geographic_strategy="residential_proxy_spoofed",
    ),
    "ATK-012": AttackGenome(
        attack_id="ATK-012",
        attack_name="Stealth Biometric Hash Injection / Virtual Sensor Replay",
        category="Automated Account Takeover & Behavioral Mimicry",
        target="payment_authorization",
        entry_vector="credential_abuse",
        behavior="behavioral_mimicry",
        evasion_strategy="biometric_spoofing",
        payment_channel="mobile_app",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="high_risk_crypto",
        geographic_strategy="domestic_matching",
    ),
    "ATK-013": AttackGenome(
        attack_id="ATK-013",
        attack_name="Low-and-Slow AI Micro-Carding Swarm",
        category="Evasive & Micro-Transaction Attacks",
        target="merchant",
        entry_vector="credential_abuse",
        behavior="low_and_slow",
        evasion_strategy="amount_camouflage",
        payment_channel="e-commerce",
        amount_strategy="micro_transactions",
        temporal_strategy="distributed",
        identity_strategy="fabricated_identity",
        merchant_strategy="mcc_rotation",
        geographic_strategy="domestic_matching",
    ),
    "ATK-014": AttackGenome(
        attack_id="ATK-014",
        attack_name="AI Smurfing & Micro-Structuring Network",
        category="Evasive & Micro-Transaction Attacks",
        target="payment_authorization",
        entry_vector="credential_abuse",
        behavior="structuring",
        evasion_strategy="amount_camouflage",
        payment_channel="p2p_transfer",
        amount_strategy="sub_threshold_structuring",
        temporal_strategy="even_interval",
        identity_strategy="existing_account",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    ),
    "ATK-015": AttackGenome(
        attack_id="ATK-015",
        attack_name="Velocity-Throttled Automated Account Draining",
        category="Evasive & Micro-Transaction Attacks",
        target="account",
        entry_vector="credential_abuse",
        behavior="low_and_slow",
        evasion_strategy="velocity_smoothing",
        payment_channel="e-commerce",
        amount_strategy="normal_looking",
        temporal_strategy="even_interval",
        identity_strategy="existing_account",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    ),
    "ATK-016": AttackGenome(
        attack_id="ATK-016",
        attack_name="Dynamic Merchant Category Hopping Bot",
        category="Evasive & Micro-Transaction Attacks",
        target="merchant",
        entry_vector="credential_abuse",
        behavior="cross_channel",
        evasion_strategy="mcc_hopping",
        payment_channel="e-commerce",
        amount_strategy="normal_looking",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="mcc_rotation",
        geographic_strategy="domestic_matching",
    ),
    "ATK-017": AttackGenome(
        attack_id="ATK-017",
        attack_name="Autonomous Shopping Agent Prompt Hijack",
        category="AI Agent & API Payment Exploits",
        target="payment_agent",
        entry_vector="prompt_manipulation",
        behavior="cart_manipulation",
        evasion_strategy="trusted_session_behavior",
        payment_channel="api_gateway",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="distributed",
        identity_strategy="delegated_agent",
        merchant_strategy="high_risk_crypto",
        geographic_strategy="domestic_matching",
    ),
    "ATK-018": AttackGenome(
        attack_id="ATK-018",
        attack_name="Malicious MCP / Plugin Tool Unauthorized Transaction",
        category="AI Agent & API Payment Exploits",
        target="payment_agent",
        entry_vector="malicious_tool",
        behavior="low_and_slow",
        evasion_strategy="risk_signal_suppression",
        payment_channel="api_gateway",
        amount_strategy="normal_looking",
        temporal_strategy="distributed",
        identity_strategy="delegated_agent",
        merchant_strategy="digital_marketplace",
        geographic_strategy="domestic_matching",
    ),
    "ATK-019": AttackGenome(
        attack_id="ATK-019",
        attack_name="Agentic Webhook Signature Evasion & Race Exploit",
        category="AI Agent & API Payment Exploits",
        target="checkout",
        entry_vector="api_exploit",
        behavior="burst_velocity",
        evasion_strategy="risk_signal_suppression",
        payment_channel="api_gateway",
        amount_strategy="normal_looking",
        temporal_strategy="rapid_burst",
        identity_strategy="delegated_agent",
        merchant_strategy="digital_marketplace",
        geographic_strategy="domestic_matching",
    ),
    "ATK-020": AttackGenome(
        attack_id="ATK-020",
        attack_name="Automated Cart-State Desynchronization & Discount Exploit",
        category="AI Agent & API Payment Exploits",
        target="checkout",
        entry_vector="api_exploit",
        behavior="cart_manipulation",
        evasion_strategy="amount_camouflage",
        payment_channel="e-commerce",
        amount_strategy="stealth_discounted",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    ),
    "ATK-021": AttackGenome(
        attack_id="ATK-021",
        attack_name="Adversarial Perturbation Evasion on Risk Scoring Engine",
        category="AI Agent & API Payment Exploits",
        target="payment_authorization",
        entry_vector="api_exploit",
        behavior="behavioral_mimicry",
        evasion_strategy="risk_signal_suppression",
        payment_channel="e-commerce",
        amount_strategy="normal_looking",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    ),
    "ATK-022": AttackGenome(
        attack_id="ATK-022",
        attack_name="AI-Routed Residential Proxy Swarm Geolocation Spoofing",
        category="Cross-Channel & Cross-Border Evasion",
        target="account",
        entry_vector="credential_abuse",
        behavior="burst_velocity",
        evasion_strategy="geolocation_spoofing",
        payment_channel="e-commerce",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="luxury_retail",
        geographic_strategy="residential_proxy_spoofed",
    ),
    "ATK-023": AttackGenome(
        attack_id="ATK-023",
        attack_name="Multi-Currency Triangular Arbitrage Money Laundering",
        category="Cross-Channel & Cross-Border Evasion",
        target="payment_authorization",
        entry_vector="credential_abuse",
        behavior="arbitrage",
        evasion_strategy="channel_hopping",
        payment_channel="p2p_transfer",
        amount_strategy="arbitrage_multi_tier",
        temporal_strategy="rapid_burst",
        identity_strategy="existing_account",
        merchant_strategy="high_risk_crypto",
        geographic_strategy="cross_border_arbitrage",
    ),
    "ATK-024": AttackGenome(
        attack_id="ATK-024",
        attack_name="Omnichannel Fast Checkout Bypass (POS to Web Arbitrage)",
        category="Cross-Channel & Cross-Border Evasion",
        target="checkout",
        entry_vector="credential_abuse",
        behavior="cross_channel",
        evasion_strategy="channel_hopping",
        payment_channel="pos_contactless",
        amount_strategy="normal_looking",
        temporal_strategy="rapid_burst",
        identity_strategy="existing_account",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    ),
    "ATK-025": AttackGenome(
        attack_id="ATK-025",
        attack_name="Deepfake Live Face Swap on NFC Contactless Terminal",
        category="Cross-Channel & Cross-Border Evasion",
        target="payment_authorization",
        entry_vector="deepfake_synthesis",
        behavior="behavioral_mimicry",
        evasion_strategy="biometric_spoofing",
        payment_channel="pos_contactless",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="luxury_retail",
        geographic_strategy="domestic_matching",
    ),
    "ATK-026": AttackGenome(
        attack_id="ATK-026",
        attack_name="AI-Generated RMA & Fake Tracking Return Fraud",
        category="E-Commerce & Merchant Exploits",
        target="merchant",
        entry_vector="document_forgery",
        behavior="cart_manipulation",
        evasion_strategy="risk_signal_suppression",
        payment_channel="e-commerce",
        amount_strategy="normal_looking",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="digital_marketplace",
        geographic_strategy="domestic_matching",
    ),
    "ATK-027": AttackGenome(
        attack_id="ATK-027",
        attack_name="Synthetic Subscription Layering & Chargeback Cycling",
        category="E-Commerce & Merchant Exploits",
        target="merchant",
        entry_vector="credential_abuse",
        behavior="chargeback_cycling",
        evasion_strategy="amount_camouflage",
        payment_channel="recurring_subscription",
        amount_strategy="micro_transactions",
        temporal_strategy="distributed",
        identity_strategy="fabricated_identity",
        merchant_strategy="digital_marketplace",
        geographic_strategy="domestic_matching",
    ),
    "ATK-028": AttackGenome(
        attack_id="ATK-028",
        attack_name="AI SIM-Swap + Automated OTP Exfiltration",
        category="Automated Account Takeover & Behavioral Mimicry",
        target="account",
        entry_vector="carrier_compromise",
        behavior="burst_velocity",
        evasion_strategy="trusted_device_masking",
        payment_channel="mobile_app",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="rapid_burst",
        identity_strategy="swapped_sim",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    ),
}


def get_archetype_genome(attack_id: str) -> Optional[AttackGenome]:
    """Retrieve the ground-truth AttackGenome for a given known attack_id."""
    return KNOWN_ATTACK_GENOMES.get(attack_id)


def get_all_known_genomes() -> List[AttackGenome]:
    """Return all 28 known attack genomes."""
    return list(KNOWN_ATTACK_GENOMES.values())
