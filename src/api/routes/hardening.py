"""Zero-Day Adaptive Hardening & Defense Comparison routes."""

import random
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Request
import pandas as pd
import numpy as np

from src.api.schemas import (
    EvolveGen2Request,
    EvolveGen2Response,
    CompareDefenseRequest,
    CompareDefenseResponse,
    DetectorEvaluationStats,
    DefenseImprovementStats,
)
from src.attacks.attack_genome import AttackGenome
from src.attacks.attack_library import AttackArchetype
from src.attacks.novelty_engine import generate_candidate_name
from src.simulation.transaction_generator import TransactionGenerator

router = APIRouter(prefix="/hardening", tags=["Adaptive Hardening & Defense"])


@router.post("/evolve-gen2", response_model=EvolveGen2Response)
def evolve_gen2(req: EvolveGen2Request) -> EvolveGen2Response:
    """Evolve a discovered novel attack into an unseen Generation-2 (V2) variant."""
    try:
        parent_genome = AttackGenome.from_dict(req.parent_genome)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid parent genome: {exc}")

    rng = random.Random(req.seed or 2026)
    evolved_dict = parent_genome.to_dict().copy()
    evolved_genes = []

    # Evolution rules matching ZeroDayHardeningPipeline Generation-2 synthesis
    # 1. Evolve Amount Strategy
    if evolved_dict["amount_strategy"] == "sub_threshold_structuring":
        evolved_dict["amount_strategy"] = "stealth_discounted"
        evolved_genes.append("amount_strategy: sub_threshold_structuring -> stealth_discounted")
    elif evolved_dict["amount_strategy"] == "high_ticket_burst":
        evolved_dict["amount_strategy"] = "micro_charge_testing"
        evolved_genes.append("amount_strategy: high_ticket_burst -> micro_charge_testing")
    else:
        evolved_dict["amount_strategy"] = "sub_threshold_structuring"
        evolved_genes.append(f"amount_strategy: -> sub_threshold_structuring")

    # 2. Evolve Temporal Strategy
    if evolved_dict["temporal_strategy"] == "distributed":
        evolved_dict["temporal_strategy"] = "off_hours_window"
        evolved_genes.append("temporal_strategy: distributed -> off_hours_window")
    elif evolved_dict["temporal_strategy"] == "burst_rapid":
        evolved_dict["temporal_strategy"] = "gradual_escalation"
        evolved_genes.append("temporal_strategy: burst_rapid -> gradual_escalation")

    # 3. Evolve Evasion Strategy if possible
    if evolved_dict["evasion_strategy"] == "trusted_session_behavior":
        evolved_dict["evasion_strategy"] = "trusted_device_masking"
        evolved_genes.append("evasion_strategy: trusted_session_behavior -> trusted_device_masking")

    variant_genome = AttackGenome.from_dict(evolved_dict)
    variant_name = f"{generate_candidate_name(variant_genome)} (Gen-2 Evolved)"
    variant_id = f"{req.candidate_id or 'NSA-001'}-V2"

    return EvolveGen2Response(
        variant_id=variant_id,
        variant_name=variant_name,
        genome=variant_genome.get_genes(),
        parent_id=req.candidate_id or "NSA-001",
        evolved_genes=evolved_genes,
    )


@router.post("/compare-defense", response_model=CompareDefenseResponse)
def compare_defense(req: CompareDefenseRequest, request: Request) -> CompareDefenseResponse:
    """Evaluate an attack scenario against both Baseline and Hardened detectors side-by-side."""
    detector_baseline = getattr(request.app.state, "detector_baseline", None)
    detector_hardened = getattr(request.app.state, "detector_hardened", None)

    if detector_baseline is None or detector_hardened is None:
        from src.utils.config import MODELS_DIR
        from src.detection.predict import FraudDetector
        baseline_path = MODELS_DIR / "baseline_detector.joblib"
        hardened_path = MODELS_DIR / "hardened_zero_day_detector.joblib"
        if not hardened_path.exists():
            hardened_path = MODELS_DIR / "hardened_detector.joblib"

        if detector_baseline is None and baseline_path.exists():
            try:
                detector_baseline = FraudDetector(artifact_path=baseline_path)
                request.app.state.detector_baseline = detector_baseline
            except Exception:
                pass

        if detector_hardened is None and hardened_path.exists():
            try:
                detector_hardened = FraudDetector(artifact_path=hardened_path)
                request.app.state.detector_hardened = detector_hardened
            except Exception:
                pass
        elif detector_hardened is None:
            detector_hardened = detector_baseline
            request.app.state.detector_hardened = detector_hardened

    if detector_baseline is None or detector_hardened is None:
        raise HTTPException(
            status_code=503,
            detail="Required detector models (baseline & hardened) are not loaded in application state.",
        )

    try:
        genome = AttackGenome.from_dict(req.attack_genome)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid attack genome: {exc}")

    sim_params = genome.to_simulation_parameters()
    gen = TransactionGenerator(seed=req.seed or 2026)

    variant_archetype = AttackArchetype(
        attack_id="GEN2-COMPARE",
        name=req.attack_name or "Gen-2 Attack Scenario",
        category="Zero-Day Evolution",
        description="Evolved synthetic attack scenario.",
        severity="CRITICAL",
        novelty_score=0.85,
        detectability_score=0.35,
        behavioral_indicators=[],
        affected_payment_surface=str(sim_params.get("payment_channel", "e-commerce")),
        simulation_parameters=sim_params,
    )

    # Generate synthetic attack transactions
    n_samples = req.sample_count
    txs = []
    for _ in range(n_samples):
        tx = gen.generate_fraud_transaction(archetype=variant_archetype)
        txs.append(tx)

    df_test = pd.DataFrame(txs)

    # 1. Baseline Detector Inference
    probs_base = detector_baseline.predict_proba(df_test)
    preds_base = (probs_base >= 0.50).astype(int)
    base_detected = int(np.sum(preds_base == 1))
    base_missed = int(np.sum(preds_base == 0))
    base_rate = round((base_detected / n_samples) * 100.0, 2)

    # 2. Hardened Detector Inference
    probs_hard = detector_hardened.predict_proba(df_test)
    preds_hard = (probs_hard >= 0.50).astype(int)
    hard_detected = int(np.sum(preds_hard == 1))
    hard_missed = int(np.sum(preds_hard == 0))
    hard_rate = round((hard_detected / n_samples) * 100.0, 2)

    # 3. Delta Metrics
    gen_gain = round(hard_rate - base_rate, 2)
    miss_reduction = base_missed - hard_missed
    fn_reduction_pct = round(
        ((base_missed - hard_missed) / max(base_missed, 1)) * 100.0, 2
    ) if base_missed > 0 else 0.0

    return CompareDefenseResponse(
        scenario_name=req.attack_name or "Novel Attack Scenario",
        total_simulated=n_samples,
        baseline_detector=DetectorEvaluationStats(
            detected=base_detected,
            missed=base_missed,
            detection_rate_pct=base_rate,
        ),
        hardened_detector=DetectorEvaluationStats(
            detected=hard_detected,
            missed=hard_missed,
            detection_rate_pct=hard_rate,
        ),
        defense_improvement=DefenseImprovementStats(
            generalization_gain_pct_points=gen_gain,
            missed_attacks_reduction=miss_reduction,
            false_negative_reduction_pct=fn_reduction_pct,
        ),
    )
