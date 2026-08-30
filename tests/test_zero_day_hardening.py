"""Unit tests for Phase 6 Zero-Day Adaptive Hardening Engine."""

import pytest
from pathlib import Path
import pandas as pd
import numpy as np

from src.adversarial.zero_day_hardening import ZeroDayHardeningPipeline
from src.attacks.attack_discovery import AttackDiscoveryEngine


@pytest.fixture(scope="module")
def small_zero_day_pipeline(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("zero_day_test_exp")
    pipeline = ZeroDayHardeningPipeline(
        baseline_seed=42,
        adversarial_train_seed=101,
        unseen_test_seed=1337,
        novel_discovery_seed=777,
        novel_test_seed=2026,
        output_dir=out_dir,
    )
    return pipeline, out_dir


def test_zero_day_hardening_pipeline_execution(small_zero_day_pipeline):
    """Test fast end-to-end execution of Zero-Day Hardening on small sample size."""
    pipeline, out_dir = small_zero_day_pipeline

    report = pipeline.run_pipeline(
        n_samples=250,
        fraud_ratio=0.20,
        mutation_intensity=0.50,
        n_novel_raw=20,
        max_novel_retained=4,
        n_training_candidates=2,
        samples_per_attack=40,
        verbose=False,
    )

    # 1. Structure Verification
    assert "experiment_name" in report
    assert "random_seeds" in report
    assert "dataset_sizes" in report
    assert "training_candidates" in report
    assert "gen2_test_candidates" in report
    assert "normal_test_regression_metrics" in report
    assert "generalization_test_results" in report
    assert "novel_training_attacks_results" in report

    # 2. Training Candidates Selection
    train_cands = report["novel_training_attacks_results"]
    assert len(train_cands) == 2
    for cand in train_cands:
        assert cand["is_training_attack"] is True
        assert cand["is_test_attack"] is False
        assert cand["baseline_detection_rate"] >= 0.0
        assert cand["hardened_detection_rate"] >= 0.0
        assert "miss_reduction" in cand
        assert "miss_reduction_percentage" in cand

    # 3. Generalization Test Results
    gen_results = report["generalization_test_results"]
    assert gen_results["total_tested"] == 80  # 2 variants * 40 samples
    assert "generalization_gain_percentage_points" in gen_results
    assert "miss_reduction" in gen_results
    assert "miss_reduction_percentage" in gen_results

    # 4. Strict Data Separation
    train_ids = {c["candidate_id"] for c in report["training_candidates"]}
    gen2_ids = {c["candidate_id"] for c in report["gen2_test_candidates"]}
    assert train_ids.isdisjoint(gen2_ids), "Test candidate IDs must be disjoint from training IDs"

    # 5. Artifact Verification
    assert (out_dir / "zero_day_hardening_report.json").exists()
    assert (out_dir / "zero_day_hardening_report.csv").exists()
    assert (out_dir / "zero_day_hardening_summary.txt").exists()


def test_generation_2_variants_creation(small_zero_day_pipeline):
    """Verify Generation-2 evolution produces valid distinct genomes and datasets."""
    pipeline, _ = small_zero_day_pipeline
    discovery_engine = AttackDiscoveryEngine(seed=777)

    raw = discovery_engine.generate_raw_candidates(n_candidates=10)
    retained, _ = discovery_engine.filter_and_rank_candidates(raw, max_retained=2)

    gen2_cands, gen2_dfs = pipeline.generate_generation_2_variants(
        training_candidates=retained,
        discovery_engine=discovery_engine,
        samples_per_variant=30,
    )

    assert len(gen2_cands) == len(retained)
    assert len(gen2_dfs) == len(retained)

    for cand, (k, df) in zip(gen2_cands, gen2_dfs.items()):
        assert cand.candidate_id.endswith("-V2")
        assert len(df) == 30
        assert df["fraud_label"].all() == 1
        assert (df["transaction_amount"] > 0).all()
