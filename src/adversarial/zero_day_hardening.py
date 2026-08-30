"""FraudForge AI: Zero-Day Adaptive Hardening Engine (Phase 6).

Executes the complete Red-Team / Blue-Team loop for Novel Synthetic Attacks:
DISCOVER -> SIMULATE -> ATTACK -> HARDEN -> RE-ATTACK -> MEASURE

1. Discovers novel synthetic attack candidate genomes (Phase 5).
2. Ranks and selects highest-priority novel attacks based on novelty, realism, evasion, and detector blind spots.
3. Simulates Zero-Day training attacks and evaluates the Baseline Detector.
4. Hardens the Blue-Team detector via augmented adversarial retraining.
5. Generates Generation-2 fresh unseen attack variants (Dataset D) to rigorously evaluate generalization.
6. Re-attacks the hardened model across normal, known adversarial, and fresh novel attack suites.
7. Evaluates regression on normal payments, feature importance shifts, and exports structured reports.
"""

import argparse
import datetime
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable
import numpy as np
import pandas as pd

from src.attacks.attack_library import AttackArchetype, get_default_attack_library
from src.attacks.attack_genome import AttackGenome
from src.attacks.novelty_engine import calculate_genome_similarity
from src.attacks.attack_discovery import AttackDiscoveryEngine, NovelAttackCandidate
from src.attacks.attack_mutator import AttackMutator
from src.simulation.transaction_generator import TransactionGenerator
from src.features.feature_engineering import FraudFeaturePipeline, extract_features_and_targets
from src.detection.train import train_baseline_detector, save_detector
from src.detection.predict import FraudDetector
from src.detection.evaluate import evaluate_global_metrics, evaluate_attack_specific_metrics
from src.utils.config import (
    DEFAULT_SEED,
    MODELS_DIR,
    GENERATED_DATA_DIR,
    PROCESSED_DATA_DIR,
    EXPERIMENTS_DIR,
)


class ZeroDayHardeningPipeline:
    """Orchestrates novel attack discovery, zero-day adversarial hardening, and generalization benchmarking."""

    def __init__(
        self,
        baseline_seed: int = 42,
        adversarial_train_seed: int = 101,
        unseen_test_seed: int = 1337,
        novel_discovery_seed: int = 777,
        novel_test_seed: int = 2026,
        output_dir: Optional[Path] = None,
    ):
        self.baseline_seed = baseline_seed
        self.adversarial_train_seed = adversarial_train_seed
        self.unseen_test_seed = unseen_test_seed
        self.novel_discovery_seed = novel_discovery_seed
        self.novel_test_seed = novel_test_seed
        self.output_dir = output_dir or EXPERIMENTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.attack_library = get_default_attack_library()

    def generate_generation_2_variants(
        self,
        training_candidates: List[NovelAttackCandidate],
        discovery_engine: AttackDiscoveryEngine,
        samples_per_variant: int = 200,
    ) -> Tuple[List[NovelAttackCandidate], Dict[str, pd.DataFrame]]:
        """Evolve training candidates into Generation-2 (V2) unseen variants.
        
        Applies a distinct seed and genetic mutation to test transfer/generalization.
        """
        gen2_candidates: List[NovelAttackCandidate] = []
        gen2_datasets: Dict[str, pd.DataFrame] = {}
        generator = TransactionGenerator(seed=self.novel_test_seed)

        for cand in training_candidates:
            # Evolve genome by mutating 1-2 genes using novel test RNG
            mutated_genome, mut_log = discovery_engine.mutate_genome(cand.genome, n_mutations=1)
            gen2_id = f"{cand.candidate_id}-V2"
            gen2_name = f"{cand.candidate_name} (Gen-2 Evolved)"
            mutated_genome.attack_id = gen2_id
            mutated_genome.attack_name = gen2_name

            gen2_cand = NovelAttackCandidate(
                candidate_id=gen2_id,
                candidate_name=gen2_name,
                genome=mutated_genome,
                novelty_score=cand.novelty_score,
                realism_score=cand.realism_score,
                evasion_potential=cand.evasion_potential,
                priority_score=cand.priority_score,
                nearest_known_attack=cand.candidate_id,
                nearest_known_similarity=0.90,
                lineage={
                    "mutation_type": "generation_2_evolution",
                    "parent_candidate": cand.candidate_id,
                    "evolution_mutations": mut_log,
                },
                simulation_parameters=mutated_genome.to_simulation_parameters(),
            )
            gen2_candidates.append(gen2_cand)

            # Synthesize Gen-2 transactions
            cand_archetype = AttackArchetype(
                attack_id=gen2_id,
                name=gen2_name,
                category="Novel Synthetic Attack Gen-2 Variant",
                description=f"Evolved Gen-2 variant of {cand.candidate_id}.",
                severity="CRITICAL",
                novelty_score=cand.novelty_score,
                detectability_score=float(np.round(1.0 - cand.evasion_potential, 2)),
                behavioral_indicators=[f"{k}={v}" for k, v in mutated_genome.get_genes().items()],
                affected_payment_surface=mutated_genome.payment_channel,
                simulation_parameters=gen2_cand.simulation_parameters,
            )

            records: List[Dict[str, Any]] = []
            for _ in range(samples_per_variant):
                tx = generator.generate_fraud_transaction(archetype=cand_archetype)
                records.append(tx)

            gen2_datasets[gen2_id] = pd.DataFrame(records)

        return gen2_candidates, gen2_datasets

    def run_pipeline(
        self,
        n_samples: int = 10000,
        fraud_ratio: float = 0.15,
        mutation_intensity: float = 0.65,
        n_novel_raw: int = 80,
        max_novel_retained: int = 15,
        n_training_candidates: int = 5,
        samples_per_attack: int = 200,
        verbose: bool = True,
        step_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """Execute the full Zero-Day Discovery -> Hardening -> Re-Attack experiment."""

        if verbose:
            print("=" * 80)
            print("   FRAUDFORGE AI -- ZERO-DAY ADAPTIVE HARDENING & RE-ATTACK PIPELINE")
            print("=" * 80)

        # ---------------------------------------------------------------------
        # STEP 1: Baseline Detector & Dataset A Setup
        # ---------------------------------------------------------------------
        if step_callback:
            step_callback(1, "Baseline detector preparation...")
        elif verbose:
            print("\n[*] STEP 1: Setting up Baseline Detector & Dataset A...")

        gen_a = TransactionGenerator(seed=self.baseline_seed)
        df_a = gen_a.generate_dataset(n_samples=n_samples, fraud_ratio=fraud_ratio)

        artifact_baseline, train_df_a, test_df_a = train_baseline_detector(
            df=df_a,
            test_size=0.20,
            seed=self.baseline_seed,
            model_type="xgboost",
        )
        baseline_model_path = MODELS_DIR / "baseline_detector.joblib"
        save_detector(artifact_baseline, baseline_model_path)
        detector_baseline = FraudDetector(artifact=artifact_baseline)

        # Save processed baseline train and test splits
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        train_df_a.to_csv(PROCESSED_DATA_DIR / "train_split.csv", index=False)
        test_df_a.to_csv(PROCESSED_DATA_DIR / "test_split.csv", index=False)

        # Evaluate baseline on normal test set
        y_true_a = test_df_a["fraud_label"].to_numpy()
        y_pred_a_base = detector_baseline.predict(test_df_a)
        y_prob_a_base = detector_baseline.predict_proba(test_df_a)
        baseline_normal_metrics = evaluate_global_metrics(y_true_a, y_pred_a_base, y_prob_a_base)

        if verbose:
            print(f"    [+] Baseline trained on {len(train_df_a):,} samples.")
            print(f"    [+] Baseline Normal F1: {baseline_normal_metrics['f1_score']:.4f} | Recall: {baseline_normal_metrics['recall']:.4f} | FPR: {baseline_normal_metrics['false_positive_rate']*100:.2f}%")

        # ---------------------------------------------------------------------
        # STEP 2: Novel Attack Discovery (Phase 5 Engine)
        # ---------------------------------------------------------------------
        if step_callback:
            step_callback(2, f"Novel attack discovery ({n_novel_raw} raw candidates)...")
        elif verbose:
            print(f"\n[*] STEP 2: Executing Novel Synthetic Attack Discovery (seed={self.novel_discovery_seed})...")

        discovery_engine = AttackDiscoveryEngine(seed=self.novel_discovery_seed)
        raw_candidates = discovery_engine.generate_raw_candidates(n_candidates=n_novel_raw)
        retained_candidates, disc_stats = discovery_engine.filter_and_rank_candidates(
            raw_candidates,
            max_retained=max_novel_retained,
        )

        novel_datasets = discovery_engine.simulate_candidate_transactions(
            retained_candidates,
            samples_per_candidate=samples_per_attack,
            seed=self.novel_discovery_seed + 100,
        )

        # Baseline evaluation on all novel candidates
        evaluated_candidates = discovery_engine.evaluate_against_detector(
            detector_baseline,
            novel_datasets,
            retained_candidates,
        )

        if verbose:
            print(f"    [+] Discovered {len(evaluated_candidates)} novel candidates from {disc_stats['total_generated']} raw genomes.")

        # ---------------------------------------------------------------------
        # STEP 3: Multi-Objective Candidate Selection for Hardening
        # ---------------------------------------------------------------------
        if step_callback:
            step_callback(3, "Selecting high-priority blind spots for hardening...")
        elif verbose:
            print("\n[*] STEP 3: Ranking & Selecting High-Priority Novel Attacks for Hardening...")

        # Multi-objective priority score: Novelty (25%), Realism (25%), Evasion (25%), Blind Spot / Miss Rate (25%)
        for cand in evaluated_candidates:
            miss_factor = (100.0 - cand.detection_rate) / 100.0  # 1.0 = completely undetected
            cand.priority_score = float(np.round(
                (0.25 * cand.novelty_score)
                + (0.25 * cand.realism_score)
                + (0.25 * cand.evasion_potential)
                + (0.25 * miss_factor),
                4
            ))

        # Sort by priority score descending
        evaluated_candidates.sort(key=lambda c: c.priority_score, reverse=True)

        training_candidates = evaluated_candidates[:n_training_candidates]
        non_training_candidates = evaluated_candidates[n_training_candidates:]

        if verbose:
            print(f"    [!] Selected Top {len(training_candidates)} Novel Attack Candidates for Blue-Team Hardening:")
            for cand in training_candidates:
                print(f"        • {cand.candidate_id} [{cand.candidate_name[:38]:<38}]: Baseline Det = {cand.detection_rate:>5.1f}% | Priority = {cand.priority_score:.4f} | {cand.blind_spot_level}")

        # ---------------------------------------------------------------------
        # STEP 4 & 5: Assemble Zero-Day Training Transactions
        # ---------------------------------------------------------------------
        if step_callback:
            step_callback(4, "Synthesizing zero-day training data...")
        elif verbose:
            print("\n[*] STEP 4: Assembling Zero-Day Training Attack Transactions...")

        zero_day_training_dfs: List[pd.DataFrame] = []
        training_baseline_records: Dict[str, Dict[str, Any]] = {}

        for cand in training_candidates:
            df_cand = novel_datasets[cand.candidate_id].copy()
            df_cand["attack_type"] = cand.candidate_name
            df_cand["fraud_label"] = 1
            zero_day_training_dfs.append(df_cand)

            training_baseline_records[cand.candidate_id] = {
                "candidate_id": cand.candidate_id,
                "candidate_name": cand.candidate_name,
                "total_tested": cand.number_tested,
                "baseline_detected": cand.number_detected,
                "baseline_missed": cand.number_missed,
                "baseline_detection_rate": cand.detection_rate,
            }

        zero_day_train_df = pd.concat(zero_day_training_dfs, ignore_index=True)
        if verbose:
            print(f"    [+] Zero-Day Training Dataset: {len(zero_day_train_df):,} samples across {len(training_candidates)} novel attacks.")

        # ---------------------------------------------------------------------
        # STEP 6: Assemble Dataset B & Retrain Hardened Detector
        # ---------------------------------------------------------------------
        if step_callback:
            step_callback(5, "Hardening detector with zero-day + adversarial data...")
        elif verbose:
            print("\n[*] STEP 5: Retraining Hardened Blue-Team Detector on Augmented Data (Dataset A + Dataset B)...")

        # Generate standard known adversarial mutations (Dataset B base)
        gen_b = TransactionGenerator(seed=self.adversarial_train_seed)
        df_b_raw = gen_b.generate_dataset(n_samples=2500, fraud_ratio=0.50)
        df_b_fraud = df_b_raw[df_b_raw["fraud_label"] == 1].copy()
        df_b_legit = df_b_raw[df_b_raw["fraud_label"] == 0].copy()

        # Detector dependencies
        feat_imp_df_base = detector_baseline.get_feature_importances(top_n=15)
        top_feats = feat_imp_df_base.head(6)["feature"].tolist()
        clean_deps = [f for f in ["merchant_risk_score", "device_change", "IP_risk_score", "transaction_velocity_24h", "transaction_velocity_1h", "behavioral_deviation"] if any(f in tf for tf in top_feats)]
        if not clean_deps:
            clean_deps = ["merchant_risk_score", "device_change", "IP_risk_score", "behavioral_deviation"]

        mutator_train = AttackMutator(seed=self.adversarial_train_seed)
        mutated_known_fraud, _ = mutator_train.mutate_dataframe(
            df_fraud=df_b_fraud,
            attack_library=self.attack_library,
            detector_weaknesses=clean_deps,
            mutation_intensity=mutation_intensity,
        )

        # Full Dataset B: Known mutated attacks + Legitimate + Zero-Day Novel attacks
        dataset_b = pd.concat([mutated_known_fraud, df_b_legit, zero_day_train_df], ignore_index=True).sample(
            frac=1.0, random_state=self.adversarial_train_seed
        ).reset_index(drop=True)

        # Augmented training set
        augmented_train_df = pd.concat([train_df_a, dataset_b], ignore_index=True).sample(
            frac=1.0, random_state=self.adversarial_train_seed
        ).reset_index(drop=True)

        X_aug, y_aug, _ = extract_features_and_targets(augmented_train_df)
        hardened_pipeline = FraudFeaturePipeline()
        X_aug_trans = hardened_pipeline.fit_transform(X_aug, y_aug)

        n_neg = int((y_aug == 0).sum())
        n_pos = int((y_aug == 1).sum())
        scale_pos_weight = float(n_neg / max(1, n_pos))

        from xgboost import XGBClassifier
        hardened_model = XGBClassifier(
            n_estimators=180,
            max_depth=6,
            learning_rate=0.07,
            subsample=0.85,
            colsample_bytree=0.85,
            scale_pos_weight=scale_pos_weight,
            random_state=self.adversarial_train_seed,
            eval_metric="logloss",
            n_jobs=-1,
        )
        hardened_model.fit(X_aug_trans, y_aug)

        artifact_hardened = {
            "pipeline": hardened_pipeline,
            "model": hardened_model,
            "model_type": "xgboost_zero_day_hardened",
            "feature_names": hardened_pipeline.get_feature_names_out(),
            "seed": self.adversarial_train_seed,
        }
        hardened_model_path = MODELS_DIR / "hardened_zero_day_detector.joblib"
        save_detector(artifact_hardened, hardened_model_path)
        detector_hardened = FraudDetector(artifact=artifact_hardened)

        if verbose:
            print(f"    [+] Hardened Detector trained on {len(augmented_train_df):,} total samples.")
            print(f"    [+] Saved hardened model to {hardened_model_path}")

        # ---------------------------------------------------------------------
        # STEP 7: Generate Generation-2 Fresh Unseen Variants (Dataset D)
        # ---------------------------------------------------------------------
        if step_callback:
            step_callback(6, "Generating fresh unseen Gen-2 attack variants (Dataset D)...")
        elif verbose:
            print(f"\n[*] STEP 6: Generating Fresh Unseen Gen-2 Variants & Dataset D (seed={self.novel_test_seed})...")

        gen2_candidates, gen2_datasets = self.generate_generation_2_variants(
            training_candidates=training_candidates,
            discovery_engine=discovery_engine,
            samples_per_variant=samples_per_attack,
        )

        # Assemble Dataset D: Gen-2 variants + Fresh Legitimate transactions
        gen_d_legit = TransactionGenerator(seed=self.novel_test_seed).generate_dataset(
            n_samples=1000, fraud_ratio=0.0
        )
        gen2_fraud_dfs = [gen2_datasets[c.candidate_id] for c in gen2_candidates]
        dataset_d_fraud = pd.concat(gen2_fraud_dfs, ignore_index=True)
        dataset_d = pd.concat([dataset_d_fraud, gen_d_legit], ignore_index=True).sample(
            frac=1.0, random_state=self.novel_test_seed
        ).reset_index(drop=True)

        dataset_d_path = PROCESSED_DATA_DIR / "unseen_novel_test_d.csv"
        dataset_d.to_csv(dataset_d_path, index=False)

        # Strict Data Separation Assertions: Ensure Gen-2 attack names are disjoint from training novel attacks
        gen2_ids = set(gen2_datasets.keys())
        train_novel_ids = set(novel_datasets.keys())
        assert gen2_ids.isdisjoint(train_novel_ids), "Leakage Error: Gen-2 Candidate IDs overlap with training candidates"
        assert len(dataset_d) == len(dataset_d_fraud) + len(gen_d_legit), "Schema error in Dataset D assembly"

        if verbose:
            print(f"    [+] Generated Dataset D: {len(dataset_d):,} samples ({len(dataset_d_fraud):,} unseen Gen-2 attacks, {len(gen_d_legit):,} legit).")

        # ---------------------------------------------------------------------
        # STEP 8: Re-Attack & Multi-Suite Side-by-Side Evaluation
        # ---------------------------------------------------------------------
        if step_callback:
            step_callback(7, "Re-attacking hardened detector across all test suites...")
        elif verbose:
            print("\n[*] STEP 7: Re-Attacking Hardened Detector & Measuring Defense Impact...")

        # 1. Normal Test Set A (Defender Regression Check)
        y_pred_a_hard = detector_hardened.predict(test_df_a)
        y_prob_a_hard = detector_hardened.predict_proba(test_df_a)
        hardened_normal_metrics = evaluate_global_metrics(y_true_a, y_pred_a_hard, y_prob_a_hard)

        # 2. Known Adversarial Dataset C
        gen_c = TransactionGenerator(seed=self.unseen_test_seed)
        df_c_raw = gen_c.generate_dataset(n_samples=2000, fraud_ratio=0.15)
        df_c_fraud = df_c_raw[df_c_raw["fraud_label"] == 1].copy()
        df_c_legit = df_c_raw[df_c_raw["fraud_label"] == 0].copy()
        mutator_test = AttackMutator(seed=self.unseen_test_seed)
        mutated_fraud_test, _ = mutator_test.mutate_dataframe(
            df_fraud=df_c_fraud,
            attack_library=self.attack_library,
            detector_weaknesses=clean_deps,
            mutation_intensity=min(1.0, mutation_intensity + 0.10),
        )
        dataset_c = pd.concat([mutated_fraud_test, df_c_legit], ignore_index=True).sample(
            frac=1.0, random_state=self.unseen_test_seed
        ).reset_index(drop=True)
        y_true_c = dataset_c["fraud_label"].to_numpy()
        baseline_c_metrics = evaluate_global_metrics(y_true_c, detector_baseline.predict(dataset_c), detector_baseline.predict_proba(dataset_c))
        hardened_c_metrics = evaluate_global_metrics(y_true_c, detector_hardened.predict(dataset_c), detector_hardened.predict_proba(dataset_c))

        # 3. Novel Training Candidates (Gen-1 Re-Attack)
        training_candidates_results: List[Dict[str, Any]] = []
        for cand in training_candidates:
            df_cand = novel_datasets[cand.candidate_id]
            b_preds = detector_baseline.predict(df_cand)
            h_preds = detector_hardened.predict(df_cand)

            b_caught = int(np.sum(b_preds == 1))
            b_miss = len(df_cand) - b_caught
            b_rate = float(np.round((b_caught / len(df_cand)) * 100.0, 2))

            h_caught = int(np.sum(h_preds == 1))
            h_miss = len(df_cand) - h_caught
            h_rate = float(np.round((h_caught / len(df_cand)) * 100.0, 2))

            delta = float(np.round(h_rate - b_rate, 2))
            miss_red = b_miss - h_miss
            miss_red_pct = float(np.round((miss_red / max(1, b_miss)) * 100.0, 2))

            training_candidates_results.append({
                "candidate_id": cand.candidate_id,
                "candidate_name": cand.candidate_name,
                "candidate_generation": "Gen-1 (Training)",
                "is_training_attack": True,
                "is_test_attack": False,
                "total_samples": len(df_cand),
                "baseline_caught": b_caught,
                "baseline_missed": b_miss,
                "baseline_detection_rate": b_rate,
                "hardened_caught": h_caught,
                "hardened_missed": h_miss,
                "hardened_detection_rate": h_rate,
                "detection_rate_delta": delta,
                "miss_reduction": miss_red,
                "miss_reduction_percentage": miss_red_pct,
                "novelty_score": cand.novelty_score,
                "realism_score": cand.realism_score,
                "evasion_score": cand.evasion_potential,
                "priority_score": cand.priority_score,
                "blind_spot_level": cand.blind_spot_level,
            })

        # 4. Fresh Unseen Gen-2 Variants (Generalization Test on Dataset D)
        gen2_evaluation_results: List[Dict[str, Any]] = []
        total_gen2_tested = 0
        total_gen2_base_missed = 0
        total_gen2_hard_missed = 0
        total_gen2_base_caught = 0
        total_gen2_hard_caught = 0

        for cand in gen2_candidates:
            df_v2 = gen2_datasets[cand.candidate_id]
            b_preds = detector_baseline.predict(df_v2)
            h_preds = detector_hardened.predict(df_v2)

            n_tx = len(df_v2)
            b_caught = int(np.sum(b_preds == 1))
            b_miss = n_tx - b_caught
            b_rate = float(np.round((b_caught / n_tx) * 100.0, 2))

            h_caught = int(np.sum(h_preds == 1))
            h_miss = n_tx - h_caught
            h_rate = float(np.round((h_caught / n_tx) * 100.0, 2))

            delta = float(np.round(h_rate - b_rate, 2))
            miss_red = b_miss - h_miss
            miss_red_pct = float(np.round((miss_red / max(1, b_miss)) * 100.0, 2))

            total_gen2_tested += n_tx
            total_gen2_base_caught += b_caught
            total_gen2_base_missed += b_miss
            total_gen2_hard_caught += h_caught
            total_gen2_hard_missed += h_miss

            gen2_evaluation_results.append({
                "candidate_id": cand.candidate_id,
                "candidate_name": cand.candidate_name,
                "candidate_generation": "Gen-2 (Unseen Variant)",
                "is_training_attack": False,
                "is_test_attack": True,
                "total_samples": n_tx,
                "baseline_caught": b_caught,
                "baseline_missed": b_miss,
                "baseline_detection_rate": b_rate,
                "hardened_caught": h_caught,
                "hardened_missed": h_miss,
                "hardened_detection_rate": h_rate,
                "detection_rate_delta": delta,
                "miss_reduction": miss_red,
                "miss_reduction_percentage": miss_red_pct,
                "novelty_score": cand.novelty_score,
                "realism_score": cand.realism_score,
                "evasion_score": cand.evasion_potential,
                "priority_score": cand.priority_score,
                "blind_spot_level": "UNSEEN GENERALIZATION TEST",
            })

        overall_gen2_base_rate = float(np.round((total_gen2_base_caught / total_gen2_tested) * 100.0, 2))
        overall_gen2_hard_rate = float(np.round((total_gen2_hard_caught / total_gen2_tested) * 100.0, 2))
        generalization_gain = float(np.round(overall_gen2_hard_rate - overall_gen2_base_rate, 2))
        overall_gen2_miss_red = total_gen2_base_missed - total_gen2_hard_missed
        overall_gen2_miss_red_pct = float(np.round((overall_gen2_miss_red / max(1, total_gen2_base_missed)) * 100.0, 2))

        # 5. Feature Importance Comparison
        feat_imp_hard = detector_hardened.get_feature_importances(top_n=15)
        base_imp_dict = dict(zip(feat_imp_df_base["feature"], feat_imp_df_base["importance"]))
        hard_imp_dict = dict(zip(feat_imp_hard["feature"], feat_imp_hard["importance"]))
        
        all_feature_keys = list(set(list(base_imp_dict.keys()) + list(hard_imp_dict.keys())))
        feat_comparison: List[Dict[str, Any]] = []
        for fk in all_feature_keys:
            b_val = base_imp_dict.get(fk, 0.0)
            h_val = hard_imp_dict.get(fk, 0.0)
            feat_comparison.append({
                "feature": fk,
                "baseline_importance": round(float(b_val), 4),
                "hardened_importance": round(float(h_val), 4),
                "importance_delta": round(float(h_val - b_val), 4),
            })
        feat_comparison.sort(key=lambda x: abs(x["importance_delta"]), reverse=True)

        # ---------------------------------------------------------------------
        # STEP 9: Build & Export Artifacts
        # ---------------------------------------------------------------------
        if step_callback:
            step_callback(8, "Exporting zero-day hardening reports...")
        elif verbose:
            print("\n[*] STEP 8: Exporting Experiment Reports & Summaries...")

        report_summary = {
            "experiment_name": "FraudForge AI Phase 6 Zero-Day Adaptive Hardening",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "random_seeds": {
                "baseline_seed": self.baseline_seed,
                "adversarial_train_seed": self.adversarial_train_seed,
                "unseen_test_seed": self.unseen_test_seed,
                "novel_discovery_seed": self.novel_discovery_seed,
                "novel_test_seed": self.novel_test_seed,
            },
            "dataset_sizes": {
                "dataset_a_train": len(train_df_a),
                "dataset_a_test": len(test_df_a),
                "dataset_b_adversarial_train": len(dataset_b),
                "dataset_c_unseen_known_test": len(dataset_c),
                "dataset_d_unseen_novel_test": len(dataset_d),
            },
            "discovery_statistics": disc_stats,
            "training_candidates": [c.to_dict() for c in training_candidates],
            "gen2_test_candidates": [c.to_dict() for c in gen2_candidates],
            "normal_test_regression_metrics": {
                "baseline_detector": baseline_normal_metrics,
                "hardened_detector": hardened_normal_metrics,
                "fpr_cost": float(np.round((hardened_normal_metrics["false_positive_rate"] - baseline_normal_metrics["false_positive_rate"]) * 100.0, 2)),
            },
            "known_adversarial_dataset_c_metrics": {
                "baseline_detector": baseline_c_metrics,
                "hardened_detector": hardened_c_metrics,
            },
            "novel_training_attacks_results": training_candidates_results,
            "generalization_test_results": {
                "overall_baseline_detection_rate": overall_gen2_base_rate,
                "overall_hardened_detection_rate": overall_gen2_hard_rate,
                "generalization_gain_percentage_points": generalization_gain,
                "total_tested": total_gen2_tested,
                "baseline_misses": total_gen2_base_missed,
                "hardened_misses": total_gen2_hard_missed,
                "miss_reduction": overall_gen2_miss_red,
                "miss_reduction_percentage": overall_gen2_miss_red_pct,
                "per_variant_breakdown": gen2_evaluation_results,
            },
            "top_feature_importance_shifts": feat_comparison[:10],
        }

        # 1. JSON Export
        json_report_path = self.output_dir / "zero_day_hardening_report.json"
        with open(json_report_path, "w", encoding="utf-8") as f:
            json.dump(report_summary, f, indent=2)

        # 2. CSV Export
        all_csv_rows = training_candidates_results + gen2_evaluation_results
        csv_report_path = self.output_dir / "zero_day_hardening_report.csv"
        pd.DataFrame(all_csv_rows).to_csv(csv_report_path, index=False)

        # 3. Human-Readable Summary Text Export
        summary_txt_path = self.output_dir / "zero_day_hardening_summary.txt"
        self._export_summary_text(report_summary, summary_txt_path)

        if verbose:
            self._print_terminal_summary(report_summary)
            print(f"\n[+] JSON Report:  {json_report_path}")
            print(f"[+] CSV Report:   {csv_report_path}")
            print(f"[+] Summary File: {summary_txt_path}")

        return report_summary

    def _export_summary_text(self, report: Dict[str, Any], output_path: Path) -> None:
        """Format human-readable text summary of zero-day hardening experiment."""
        gen_res = report["generalization_test_results"]
        reg_res = report["normal_test_regression_metrics"]
        base_norm = reg_res["baseline_detector"]
        hard_norm = reg_res["hardened_detector"]
        train_attacks = report["novel_training_attacks_results"]

        # Find most difficult discovered attack
        sorted_by_base = sorted(train_attacks, key=lambda x: x["baseline_detection_rate"])
        most_difficult = sorted_by_base[0] if sorted_by_base else {}

        lines = [
            "=" * 70,
            "FRAUDFORGE AI",
            "ZERO-DAY ADAPTIVE HARDENING EXPERIMENT",
            "=" * 70,
            f"Timestamp: {report['timestamp']}",
            "",
            "DISCOVERY",
            f"Known attacks: {len(self.attack_library.get_all())}",
            f"Novel candidates generated: {report['discovery_statistics']['total_generated']}",
            f"Novel candidates retained:  {report['discovery_statistics']['retained_candidates']}",
            f"Novel candidates selected for training: {len(train_attacks)}",
            "",
            "RED TEAM RESULT",
            f"Most difficult discovered attack:",
            f"  {most_difficult.get('candidate_id', 'N/A')}: {most_difficult.get('candidate_name', 'N/A')}",
            f"  Baseline detection: {most_difficult.get('baseline_detection_rate', 0.0):.1f}% ({most_difficult.get('baseline_missed', 0)} missed)",
            "",
            "BLUE TEAM HARDENING",
            f"Novel attacks used for training: {', '.join([a['candidate_id'] for a in train_attacks])}",
            "",
            "HARDENED MODEL RESULT (GEN-1 TRAINING ATTACKS)",
        ]

        for a in train_attacks:
            lines.append(
                f"  {a['candidate_id']:<8} [{a['candidate_name'][:32]:<32}]: "
                f"Before: {a['baseline_detection_rate']:>5.1f}% -> After: {a['hardened_detection_rate']:>5.1f}% "
                f"(Delta: {a['detection_rate_delta']:>+5.1f}%, Misses: {a['baseline_missed']} -> {a['hardened_missed']})"
            )

        lines.extend([
            "",
            "GENERALIZATION (FRESH UNSEEN GEN-2 ATTACK VARIANTS)",
            f"Fresh unseen attack variants tested: {gen_res['total_tested']} transactions across {len(gen_res['per_variant_breakdown'])} evolved attacks",
            f"  Baseline Detection Rate : {gen_res['overall_baseline_detection_rate']:.2f}% ({gen_res['baseline_misses']} missed)",
            f"  Hardened Detection Rate : {gen_res['overall_hardened_detection_rate']:.2f}% ({gen_res['hardened_misses']} missed)",
            f"  Generalization Gain     : +{gen_res['generalization_gain_percentage_points']:.2f} percentage points",
            f"  False Negative Reduction: -{gen_res['miss_reduction']} misses ({gen_res['miss_reduction_percentage']:.1f}% reduction)",
            "",
            "NORMAL PAYMENT IMPACT (DEFENDER REGRESSION CHECK)",
            f"  Normal Accuracy : Baseline {base_norm['accuracy']*100:.2f}% -> Hardened {hard_norm['accuracy']*100:.2f}%",
            f"  Normal Precision: Baseline {base_norm['precision']*100:.2f}% -> Hardened {hard_norm['precision']*100:.2f}%",
            f"  Normal Recall   : Baseline {base_norm['recall']*100:.2f}% -> Hardened {hard_norm['recall']*100:.2f}%",
            f"  Normal FPR Cost : Baseline {base_norm['false_positive_rate']*100:.2f}% -> Hardened {hard_norm['false_positive_rate']*100:.2f}% (Delta: {reg_res['fpr_cost']:+.2f}%)",
            "",
            "=" * 70,
            "RESULT",
            "=" * 70,
            '"FraudForge discovered previously unseen synthetic attack patterns, used the detector\'s',
            'blind spots as adversarial training data, and evaluated whether the hardened detector',
            'generalized to fresh attack variants."',
            "=" * 70,
        ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def _print_terminal_summary(self, report: Dict[str, Any]) -> None:
        """Print formatted terminal report."""
        gen_res = report["generalization_test_results"]
        reg_res = report["normal_test_regression_metrics"]
        base_norm = reg_res["baseline_detector"]
        hard_norm = reg_res["hardened_detector"]
        train_attacks = report["novel_training_attacks_results"]

        print("\n" + "=" * 80)
        print("                 FRAUDFORGE AI -- ZERO-DAY DEFENSE BENCHMARK")
        print("=" * 80)
        print("\n1. NOVEL TRAINING CANDIDATES RE-ATTACK (GEN-1):")
        print("-" * 80)
        print(f"{'Candidate ID':<12} | {'Novel Attack Archetype':<38} | {'Baseline':<9} | {'Hardened':<9} | {'Improvement'}")
        print("-" * 80)
        for a in train_attacks:
            name = a["candidate_name"][:36]
            print(f"{a['candidate_id']:<12} | {name:<38} | {a['baseline_detection_rate']:>7.1f}% | {a['hardened_detection_rate']:>7.1f}% | {a['detection_rate_delta']:>+10.1f}%")

        print("\n2. UNSEEN GEN-2 ATTACK GENERALIZATION (DATASET D):")
        print("-" * 80)
        print(f"{'Variant ID':<12} | {'Evolved Attack Variant':<38} | {'Baseline':<9} | {'Hardened':<9} | {'Gen Gain'}")
        print("-" * 80)
        for v in gen_res["per_variant_breakdown"]:
            name = v["candidate_name"][:36]
            print(f"{v['candidate_id']:<12} | {name:<38} | {v['baseline_detection_rate']:>7.1f}% | {v['hardened_detection_rate']:>7.1f}% | {v['detection_rate_delta']:>+10.1f}%")

        print("-" * 80)
        print(f"{'OVERALL UNSEEN NOVEL ATTACK GENERALIZATION':<53} | {gen_res['overall_baseline_detection_rate']:>7.1f}% | {gen_res['overall_hardened_detection_rate']:>7.1f}% | {gen_res['generalization_gain_percentage_points']:>+10.1f}%")
        print(f"Total Missed Attacks (Gen-2 Unseen): Baseline = {gen_res['baseline_misses']} -> Hardened = {gen_res['hardened_misses']} (-{gen_res['miss_reduction']} misses, {gen_res['miss_reduction_percentage']:.1f}% reduction)")

        print("\n3. DEFENDER REGRESSION & PAYMENT IMPACT:")
        print("-" * 80)
        print(f"{'Metric':<30} | {'Baseline Detector':<20} | {'Hardened Detector':<20} | {'Delta'}")
        print("-" * 80)
        print(f"{'Normal F1 Score':<30} | {base_norm['f1_score']:>19.4f} | {hard_norm['f1_score']:>19.4f} | {hard_norm['f1_score'] - base_norm['f1_score']:>+7.4f}")
        print(f"{'Normal Recall':<30} | {base_norm['recall']*100:>18.2f}% | {hard_norm['recall']*100:>18.2f}% | {(hard_norm['recall'] - base_norm['recall'])*100:>+6.2f}%")
        print(f"{'Normal False Positive Rate':<30} | {base_norm['false_positive_rate']*100:>18.2f}% | {hard_norm['false_positive_rate']*100:>18.2f}% | {reg_res['fpr_cost']:>+6.2f}%")
        print("=" * 80)


def main() -> None:
    """CLI runner for Zero-Day Hardening and Re-Attack Experiment."""
    parser = argparse.ArgumentParser(
        description="FraudForge AI: Phase 6 Zero-Day Adaptive Hardening Engine"
    )
    parser.add_argument("--samples", type=int, default=10000, help="Samples for Dataset A (default: 10000)")
    parser.add_argument("--fraud-ratio", type=float, default=0.15, help="Baseline fraud ratio (default: 0.15)")
    parser.add_argument("--mutation-intensity", type=float, default=0.65, help="Mutation intensity (default: 0.65)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Base random seed (default: 42)")
    parser.add_argument("--novel-candidates", type=int, default=80, help="Raw novel candidates to generate (default: 80)")
    parser.add_argument("--transactions-per-attack", type=int, default=200, help="Transactions per candidate (default: 200)")

    args = parser.parse_args()

    pipeline = ZeroDayHardeningPipeline(
        baseline_seed=args.seed,
        adversarial_train_seed=101,
        unseen_test_seed=1337,
        novel_discovery_seed=777,
        novel_test_seed=2026,
    )

    pipeline.run_pipeline(
        n_samples=args.samples,
        fraud_ratio=args.fraud_ratio,
        mutation_intensity=args.mutation_intensity,
        n_novel_raw=args.novel_candidates,
        samples_per_attack=args.transactions_per_attack,
        verbose=True,
    )


if __name__ == "__main__":
    main()
