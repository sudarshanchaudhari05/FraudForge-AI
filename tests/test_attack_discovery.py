"""Unit tests for Novel Synthetic Attack Discovery Engine."""

import json
from pathlib import Path
import pytest
import pandas as pd

from src.attacks.attack_genome import AttackGenome, get_all_known_genomes, get_archetype_genome
from src.attacks.attack_discovery import AttackDiscoveryEngine, NovelAttackCandidate
from src.detection.predict import FraudDetector
from src.utils.config import MODELS_DIR


def test_engine_determinism():
    """Verify that candidate generation is completely reproducible with seed."""
    engine1 = AttackDiscoveryEngine(seed=42)
    engine2 = AttackDiscoveryEngine(seed=42)

    raw1 = engine1.generate_raw_candidates(n_candidates=20)
    raw2 = engine2.generate_raw_candidates(n_candidates=20)

    assert len(raw1) == len(raw2) == 20
    for (g1, l1), (g2, l2) in zip(raw1, raw2):
        assert g1.get_genes() == g2.get_genes()
        assert l1["mutation_type"] == l2["mutation_type"]


def test_mutation_and_crossover_lineage():
    """Verify lineage tracking for mutations and crossovers."""
    engine = AttackDiscoveryEngine(seed=123)
    p1 = get_archetype_genome("ATK-001")
    p2 = get_archetype_genome("ATK-017")
    assert p1 is not None and p2 is not None

    # Mutation
    mutated_child, mut_log = engine.mutate_genome(p1, n_mutations=2)
    assert isinstance(mutated_child, AttackGenome)
    assert len(mut_log) <= 2

    # Crossover
    cross_child, cross_log = engine.crossover_genomes(p1, p2)
    assert isinstance(cross_child, AttackGenome)
    assert len(cross_log) == 10


def test_filtering_and_ranking_pipeline():
    """Test compatibility filtering, duplicate rejection, and priority ranking."""
    engine = AttackDiscoveryEngine(seed=42)
    raw = engine.generate_raw_candidates(n_candidates=50)

    retained, stats = engine.filter_and_rank_candidates(raw, max_retained=10)
    assert len(retained) <= 10
    assert stats["total_generated"] == 50
    assert stats["compatible_candidates"] <= 50
    assert stats["retained_candidates"] == len(retained)

    # Check ID assignment and descending priority order
    for idx, cand in enumerate(retained):
        assert cand.candidate_id == f"NSA-{idx + 1:03d}"
        assert cand.novelty_score >= 0.0
        assert cand.realism_score >= 0.0
        assert cand.evasion_potential >= 0.0
        assert 0.0 <= cand.priority_score <= 1.0
        if idx > 0:
            assert cand.priority_score <= retained[idx - 1].priority_score


def test_simulator_integration_with_candidates():
    """Verify conversion of novel candidate genomes into synthetic transaction DataFrames."""
    engine = AttackDiscoveryEngine(seed=42)
    raw = engine.generate_raw_candidates(n_candidates=10)
    retained, _ = engine.filter_and_rank_candidates(raw, max_retained=3)

    datasets = engine.simulate_candidate_transactions(retained, samples_per_candidate=30, seed=555)
    assert len(datasets) == len(retained)

    for cand in retained:
        df = datasets[cand.candidate_id]
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 30
        assert "fraud_label" in df.columns
        assert (df["fraud_label"] == 1).all()
        assert df["attack_type"].iloc[0] == cand.candidate_name
        assert not df.isnull().any().any()


def test_detector_evaluation_and_blind_spot_discovery(tmp_path: Path):
    """Test evaluation of candidates against detector and blind spot classification."""
    model_path = MODELS_DIR / "baseline_detector.joblib"
    if not model_path.exists():
        pytest.skip("Baseline detector artifact not found.")

    detector = FraudDetector(artifact_path=model_path)
    engine = AttackDiscoveryEngine(seed=42)

    raw = engine.generate_raw_candidates(n_candidates=15)
    retained, _ = engine.filter_and_rank_candidates(raw, max_retained=3)
    datasets = engine.simulate_candidate_transactions(retained, samples_per_candidate=25, seed=777)

    evaluated = engine.evaluate_against_detector(detector, datasets, retained)
    valid_blind_spots = {"CRITICAL BLIND SPOT", "HIGH BLIND SPOT", "MODERATE BLIND SPOT", "LOW PRIORITY"}

    for cand in evaluated:
        assert cand.number_tested == 25
        assert cand.number_detected + cand.number_missed == 25
        assert 0.0 <= cand.detection_rate <= 100.0
        assert cand.blind_spot_level in valid_blind_spots

    # Test artifact export
    json_p, csv_p = engine.export_artifacts(evaluated, output_dir=tmp_path)
    assert json_p.exists()
    assert csv_p.exists()

    with open(json_p, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == len(evaluated)
        assert data[0]["candidate_id"] == evaluated[0].candidate_id

    df_csv = pd.read_csv(csv_p)
    assert len(df_csv) == len(evaluated)
    assert "candidate_id" in df_csv.columns
    assert "blind_spot_level" in df_csv.columns
