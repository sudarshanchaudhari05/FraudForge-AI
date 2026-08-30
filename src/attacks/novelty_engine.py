"""FraudForge AI: Novelty & Fitness Scoring Engine.

Provides compatibility rule validation, weighted genome similarity, novelty scoring,
explainable realism scoring, detector-weakness-informed evasion potential scoring,
candidate prioritization, and automated name generation.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np

from src.attacks.attack_genome import AttackGenome, GENE_KEYS, get_all_known_genomes


# =============================================================================
# GENE WEIGHTS FOR SIMILARITY CALCULATION
# =============================================================================

GENE_WEIGHTS: Dict[str, float] = {
    "behavior": 2.0,
    "evasion_strategy": 2.0,
    "target": 1.5,
    "payment_channel": 1.5,
    "entry_vector": 1.5,
    "amount_strategy": 1.0,
    "identity_strategy": 1.0,
    "temporal_strategy": 0.8,
    "merchant_strategy": 0.8,
    "geographic_strategy": 0.8,
}

TOTAL_GENE_WEIGHT = sum(GENE_WEIGHTS.values())


# =============================================================================
# COMPATIBILITY RULES
# =============================================================================

def check_compatibility(genome: AttackGenome) -> Tuple[bool, List[str]]:
    """Evaluate whether a genome represents a structurally coherent attack combination.

    Returns:
        (is_compatible, list_of_violations)
    """
    violations: List[str] = []
    g = genome.get_genes()

    # Rule 1: Physical POS channels cannot pair with purely headless API exploits without cross-channel behavior
    if g["payment_channel"] in ["pos_chip", "pos_contactless"]:
        if g["entry_vector"] in ["prompt_manipulation", "malicious_tool", "api_exploit", "session_hijacking"]:
            if g["behavior"] != "cross_channel":
                violations.append(
                    f"Physical channel '{g['payment_channel']}' incompatible with headless entry vector '{g['entry_vector']}' without cross_channel behavior."
                )

    # Rule 2: Recurring subscriptions cannot use high-velocity bursts or sub-threshold structuring
    if g["payment_channel"] == "recurring_subscription":
        if g["amount_strategy"] in ["sub_threshold_structuring", "arbitrage_multi_tier", "high_ticket_escalation"]:
            violations.append(
                f"Payment channel '{g['payment_channel']}' incompatible with amount strategy '{g['amount_strategy']}'."
            )
        if g["temporal_strategy"] == "rapid_burst":
            violations.append(f"Payment channel '{g['payment_channel']}' cannot execute rapid_burst temporal cadence.")

    # Rule 3: P2P transfers require compatible merchant strategies (not e-commerce marketplaces)
    if g["payment_channel"] == "p2p_transfer":
        if g["merchant_strategy"] in ["digital_marketplace", "micro_refunds", "luxury_retail"]:
            violations.append(
                f"Payment channel '{g['payment_channel']}' incompatible with merchant strategy '{g['merchant_strategy']}'."
            )

    # Rule 4: Prompt manipulation / Malicious tools require payment agents, checkouts, or delegated agents
    if g["entry_vector"] in ["prompt_manipulation", "malicious_tool"]:
        if g["target"] not in ["payment_agent", "checkout", "account"] and g["identity_strategy"] != "delegated_agent":
            violations.append(
                f"Entry vector '{g['entry_vector']}' requires payment_agent/checkout target or delegated_agent identity."
            )

    # Rule 5: SIM-Swap identity requires carrier_compromise or social_engineering entry
    if g["identity_strategy"] == "swapped_sim":
        if g["entry_vector"] not in ["carrier_compromise", "social_engineering", "credential_abuse"]:
            violations.append(
                f"SIM-swap identity strategy requires carrier_compromise, social_engineering, or credential_abuse."
            )

    # Rule 6: Cart manipulation behavior requires e-commerce / API / checkout surfaces
    if g["behavior"] == "cart_manipulation":
        if g["payment_channel"] not in ["e-commerce", "api_gateway", "mobile_app"]:
            violations.append(
                f"Cart manipulation behavior cannot operate on payment channel '{g['payment_channel']}'."
            )

    # Rule 7: Synthetic identity / Sleeper requires identity/merchant target or synthetic identity strategy
    if g["behavior"] == "identity_fabrication":
        if g["identity_strategy"] not in ["synthetic_sleeper", "fabricated_identity"]:
            violations.append("Identity fabrication behavior requires synthetic_sleeper or fabricated_identity strategy.")

    # Rule 8: Biometric spoofing requires biometric-capable channels
    if g["evasion_strategy"] == "biometric_spoofing":
        if g["payment_channel"] in ["pos_chip", "recurring_subscription"]:
            violations.append(
                f"Biometric spoofing evasion cannot be applied to payment channel '{g['payment_channel']}'."
            )

    # Rule 9: POS chip physical stores do not operate during off-hours (midnight to 5 AM)
    if g["payment_channel"] == "pos_chip" and g["temporal_strategy"] == "off_hours":
        violations.append("Physical POS-chip terminals cannot operate off-hours.")

    return (len(violations) == 0, violations)


# =============================================================================
# SIMILARITY & NOVELTY SCORING
# =============================================================================

def calculate_genome_similarity(g1: AttackGenome, g2: AttackGenome) -> float:
    """Calculate weighted categorical similarity between two AttackGenomes (0.0 to 1.0)."""
    d1 = g1.get_genes()
    d2 = g2.get_genes()

    weighted_match = 0.0
    for key, weight in GENE_WEIGHTS.items():
        if d1.get(key) == d2.get(key):
            weighted_match += weight

    return float(np.round(weighted_match / TOTAL_GENE_WEIGHT, 4))


def calculate_novelty_score(
    candidate: AttackGenome,
    known_genomes: Optional[List[AttackGenome]] = None,
) -> Tuple[float, Optional[AttackGenome], float]:
    """Compute novelty score (0.0 to 1.0) against known archetypes.

    Formula:
        novelty_score = 1.0 - max_similarity_to_any_known_attack

    Returns:
        (novelty_score, nearest_known_genome, max_similarity)
    """
    known = known_genomes or get_all_known_genomes()
    if not known:
        return (1.0, None, 0.0)

    max_sim = 0.0
    nearest: Optional[AttackGenome] = None

    for ref in known:
        sim = calculate_genome_similarity(candidate, ref)
        if sim > max_sim:
            max_sim = sim
            nearest = ref

    novelty = float(np.round(np.clip(1.0 - max_sim, 0.0, 1.0), 4))
    return (novelty, nearest, float(np.round(max_sim, 4)))


# =============================================================================
# REALISM SCORING
# =============================================================================

def calculate_realism_score(genome: AttackGenome) -> float:
    """Calculate an explainable domain realism score (0.0 to 1.0).

    Rewards:
        - Synergistic channel/entry pairs
        - Logical target/behavior groupings
        - Coherent amount and temporal strategies
    Penalizes:
        - Out-of-market channel/merchant combinations
        - Implausible tactical combinations
    """
    is_compat, _ = check_compatibility(genome)
    if not is_compat:
        return 0.20

    score = 0.70  # Baseline realism for any compatible combination
    g = genome.get_genes()

    # 1. Synergistic Channel + Entry Vector
    if (g["payment_channel"] == "mobile_app" and g["entry_vector"] in ["credential_abuse", "deepfake_synthesis", "carrier_compromise"]):
        score += 0.06
    elif (g["payment_channel"] == "api_gateway" and g["entry_vector"] in ["api_exploit", "session_hijacking", "malicious_tool"]):
        score += 0.06
    elif (g["payment_channel"] == "e-commerce" and g["entry_vector"] in ["credential_abuse", "social_engineering"]):
        score += 0.05
    elif (g["payment_channel"] == "pos_contactless" and g["entry_vector"] in ["deepfake_synthesis", "credential_abuse"]):
        score += 0.05

    # 2. Synergistic Target + Behavior
    if (g["target"] == "account" and g["behavior"] in ["low_and_slow", "behavioral_mimicry", "burst_velocity"]):
        score += 0.05
    elif (g["target"] == "payment_agent" and g["behavior"] in ["cart_manipulation", "low_and_slow"]):
        score += 0.06
    elif (g["target"] == "identity" and g["behavior"] == "identity_fabrication"):
        score += 0.06
    elif (g["target"] == "merchant" and g["behavior"] in ["cart_manipulation", "chargeback_cycling"]):
        score += 0.05

    # 3. Synergistic Evasion + Amount/Temporal
    if (g["evasion_strategy"] == "velocity_smoothing" and g["temporal_strategy"] == "even_interval"):
        score += 0.05
    elif (g["evasion_strategy"] == "amount_camouflage" and g["amount_strategy"] in ["normal_looking", "sub_threshold_structuring", "micro_transactions"]):
        score += 0.05
    elif (g["evasion_strategy"] == "trusted_device_masking" and g["identity_strategy"] in ["existing_account", "authorized_victim"]):
        score += 0.05

    # 4. Incongruence Penalties
    if g["payment_channel"] in ["pos_chip", "pos_contactless"] and g["merchant_strategy"] == "high_risk_crypto":
        score -= 0.12  # Crypto exchanges rarely have physical POS terminals
    if g["payment_channel"] == "recurring_subscription" and g["amount_strategy"] == "high_ticket_escalation":
        score -= 0.15

    return float(np.round(np.clip(score, 0.10, 1.0), 4))


# =============================================================================
# EVASION POTENTIAL SCORING
# =============================================================================

def calculate_evasion_potential(genome: AttackGenome) -> float:
    """Score the expected evasion potential against legacy detector models (0.0 to 1.0).

    Directly leverages empirical detector vulnerability weights:
    - Normal-looking amounts bypass amount-based thresholds
    - Velocity smoothing & low-and-slow bypass velocity trips
    - Trusted device masking suppresses device change flags
    - Risk signal suppression / behavioral mimicry blunts deviation scores
    - Residential proxy spoofing blunts geographic deviation flags
    """
    g = genome.get_genes()
    evasion = 0.25  # Base potential

    # 1. Amount Camouflage (Bypasses Amount & Deviation spikes)
    if g["amount_strategy"] in ["normal_looking", "stealth_discounted"]:
        evasion += 0.16
    elif g["amount_strategy"] == "sub_threshold_structuring":
        evasion += 0.12
    elif g["amount_strategy"] == "micro_transactions":
        evasion += 0.10

    # 2. Signal Masking (Bypasses device_change & device_age_days)
    if g["evasion_strategy"] == "trusted_device_masking":
        evasion += 0.18
    elif g["evasion_strategy"] == "trusted_session_behavior":
        evasion += 0.14

    # 3. Velocity Smoothing (Bypasses transaction_velocity_1h & 24h)
    if g["evasion_strategy"] == "velocity_smoothing" or g["behavior"] == "low_and_slow":
        evasion += 0.16
    elif g["temporal_strategy"] == "even_interval":
        evasion += 0.08

    # 4. Behavioral Blending (Bypasses behavioral_deviation & IP_risk_score)
    if g["behavior"] == "behavioral_mimicry" or g["evasion_strategy"] == "risk_signal_suppression":
        evasion += 0.15

    # 5. Geolocation Blending (Bypasses geographic_deviation)
    if g["geographic_strategy"] in ["residential_proxy_spoofed", "domestic_matching"]:
        evasion += 0.12

    # 6. Identity Trust (Self-authorizing / agent credentials)
    if g["identity_strategy"] in ["authorized_victim", "delegated_agent"]:
        evasion += 0.10

    # 7. Channel Blind-Spots
    if g["payment_channel"] in ["pos_contactless", "p2p_transfer", "mobile_app"]:
        evasion += 0.05

    return float(np.round(np.clip(evasion, 0.10, 0.98), 4))


# =============================================================================
# CANDIDATE PRIORITY RANKING
# =============================================================================

def calculate_priority_score(
    novelty_score: float,
    realism_score: float,
    evasion_potential: float,
    w_novelty: float = 0.40,
    w_realism: float = 0.30,
    w_evasion: float = 0.30,
) -> float:
    """Calculate aggregate candidate priority score."""
    priority = (
        (w_novelty * novelty_score)
        + (w_realism * realism_score)
        + (w_evasion * evasion_potential)
    )
    return float(np.round(np.clip(priority, 0.0, 1.0), 4))


# =============================================================================
# HUMAN-READABLE CANDIDATE NAME GENERATOR
# =============================================================================

def generate_candidate_name(genome: AttackGenome) -> str:
    """Generate a clean, professional, descriptive attack name from genome traits."""
    g = genome.get_genes()

    # Prefix based on evasion/behavior
    prefix_map = {
        "trusted_device_masking": "Trusted-Device",
        "velocity_smoothing": "Velocity-Smoothed",
        "amount_camouflage": "Camouflaged",
        "trusted_session_behavior": "Session-Replay",
        "risk_signal_suppression": "Signal-Suppressed",
        "channel_hopping": "Cross-Channel",
        "geolocation_spoofing": "Geo-Spoofed",
        "biometric_spoofing": "Biometric-Injected",
        "mcc_hopping": "MCC-Hopping",
    }
    prefix = prefix_map.get(g["evasion_strategy"], "Adaptive")

    # Core descriptor based on behavior / amount
    core_map = {
        "low_and_slow": "Low-and-Slow",
        "burst_velocity": "Burst",
        "behavioral_mimicry": "Behavioral Mimicry",
        "cross_channel": "Omnichannel",
        "cart_manipulation": "Cart Manipulation",
        "identity_fabrication": "Synthetic Identity",
        "structuring": "Micro-Structuring",
        "chargeback_cycling": "Subscription Layering",
        "arbitrage": "Triangular Arbitrage",
    }
    core = core_map.get(g["behavior"], "Targeted")

    # Subject based on target / identity / entry
    subject_map = {
        "payment_agent": "Agent Exploit",
        "account": "Account Takeover",
        "identity": "Onboarding Bypass",
        "checkout": "Checkout Abuse",
        "payment_authorization": "Push Payment Fraud",
        "merchant": "Merchant Return Arbitrage",
        "customer": "Social Engineering Trap",
    }
    subject = subject_map.get(g["target"], "Payment Exploit")

    # Specific override combinations for maximum readability
    if g["target"] == "payment_agent" and g["entry_vector"] == "prompt_manipulation":
        return f"{prefix} Agent Prompt-Injection Checkout Attack"
    if g["target"] == "payment_agent" and g["entry_vector"] == "malicious_tool":
        return f"{prefix} MCP Tool Micro-Payment Abuse"
    if g["behavior"] == "behavioral_mimicry" and g["evasion_strategy"] == "trusted_device_masking":
        return f"Trusted-Device Behavioral Mimicry {subject}"
    if g["behavior"] == "cross_channel" and g["payment_channel"] in ["pos_contactless", "pos_chip"]:
        return f"Omnichannel POS-to-Web Fast Arbitrage"
    if g["identity_strategy"] == "swapped_sim":
        return f"AI SIM-Swap Automated OTP Exfiltration Variant"

    return f"{prefix} {core} {subject}"
