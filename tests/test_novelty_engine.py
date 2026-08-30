"""Unit tests for Novelty, Realism, Evasion Potential, and Scoring Engine."""

import pytest
from src.attacks.attack_genome import AttackGenome, get_archetype_genome, get_all_known_genomes
from src.attacks.novelty_engine import (
    check_compatibility,
    calculate_genome_similarity,
    calculate_novelty_score,
    calculate_realism_score,
    calculate_evasion_potential,
    calculate_priority_score,
    generate_candidate_name,
)


def test_known_genomes_pass_compatibility():
    """Verify all 28 ground-truth known genomes pass compatibility checks."""
    for genome in get_all_known_genomes():
        is_compat, violations = check_compatibility(genome)
        assert is_compat, f"Known genome {genome.attack_id} failed compatibility: {violations}"


def test_incompatible_genome_rejection():
    """Verify compatibility rules properly reject nonsensical combinations."""
    # 1. POS chip + headless prompt manipulation without cross-channel
    incompat_pos = AttackGenome(
        target="merchant",
        entry_vector="prompt_manipulation",
        behavior="low_and_slow",
        evasion_strategy="amount_camouflage",
        payment_channel="pos_chip",
        amount_strategy="normal_looking",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    )
    is_compat, violations = check_compatibility(incompat_pos)
    assert not is_compat
    assert any("pos_chip" in v for v in violations)

    # 2. Recurring subscription + high ticket escalation
    incompat_sub = AttackGenome(
        target="account",
        entry_vector="credential_abuse",
        behavior="low_and_slow",
        evasion_strategy="velocity_smoothing",
        payment_channel="recurring_subscription",
        amount_strategy="high_ticket_escalation",
        temporal_strategy="distributed",
        identity_strategy="existing_account",
        merchant_strategy="digital_marketplace",
        geographic_strategy="domestic_matching",
    )
    is_compat, violations = check_compatibility(incompat_sub)
    assert not is_compat
    assert any("recurring_subscription" in v for v in violations)


def test_genome_similarity_metrics():
    """Test weighted categorical similarity calculation."""
    g1 = get_archetype_genome("ATK-001")
    g2 = get_archetype_genome("ATK-001")
    assert g1 is not None and g2 is not None

    # Identical genomes must have similarity 1.0
    sim_self = calculate_genome_similarity(g1, g2)
    assert sim_self == 1.0

    # Different genomes have similarity < 1.0
    g3 = get_archetype_genome("ATK-017")
    assert g3 is not None
    sim_diff = calculate_genome_similarity(g1, g3)
    assert 0.0 <= sim_diff < 1.0


def test_novelty_score_bounds_and_behavior():
    """Verify novelty calculation yields 0.0 for known attack and higher for mutated attack."""
    known_genomes = get_all_known_genomes()
    atk1 = get_archetype_genome("ATK-001")
    assert atk1 is not None

    # Duplicate of known attack has novelty 0.0
    novelty, nearest, max_sim = calculate_novelty_score(atk1, known_genomes)
    assert novelty == 0.0
    assert max_sim == 1.0
    assert nearest is not None and nearest.attack_id == "ATK-001"

    # Novel mutated genome has novelty > 0.0
    mutated = AttackGenome(
        target="payment_agent",
        entry_vector="malicious_tool",
        behavior="low_and_slow",
        evasion_strategy="trusted_device_masking",
        payment_channel="p2p_transfer",
        amount_strategy="micro_transactions",
        temporal_strategy="distributed",
        identity_strategy="delegated_agent",
        merchant_strategy="single_target",
        geographic_strategy="domestic_matching",
    )
    novelty_mut, _, max_sim_mut = calculate_novelty_score(mutated, known_genomes)
    assert 0.0 < novelty_mut <= 1.0
    assert 0.0 <= max_sim_mut < 1.0
    assert round(novelty_mut + max_sim_mut, 4) == 1.0


def test_realism_and_evasion_potential_bounds():
    """Verify realism and evasion potential scores fall strictly within [0.0, 1.0]."""
    for genome in get_all_known_genomes():
        realism = calculate_realism_score(genome)
        evasion = calculate_evasion_potential(genome)
        assert 0.0 <= realism <= 1.0
        assert 0.0 <= evasion <= 1.0

    priority = calculate_priority_score(0.80, 0.85, 0.90)
    assert 0.0 <= priority <= 1.0
    assert priority == round(0.40 * 0.80 + 0.30 * 0.85 + 0.30 * 0.90, 4)


def test_candidate_name_generation():
    """Verify automated descriptive name generation."""
    genome = AttackGenome(
        target="payment_agent",
        entry_vector="prompt_manipulation",
        behavior="cart_manipulation",
        evasion_strategy="trusted_device_masking",
        payment_channel="api_gateway",
        amount_strategy="normal_looking",
        temporal_strategy="distributed",
        identity_strategy="delegated_agent",
        merchant_strategy="digital_marketplace",
        geographic_strategy="domestic_matching",
    )
    name = generate_candidate_name(genome)
    assert isinstance(name, str)
    assert len(name) > 10
    assert "Agent" in name or "Prompt" in name or "Trusted-Device" in name
