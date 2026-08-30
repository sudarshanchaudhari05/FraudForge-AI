"""FraudForge AI: Threshold Analysis & Risk Policy Benchmarking Engine.

Performs empirical threshold sweep, business cost trade-off modeling,
probability calibration auditing, and multi-tier policy comparison across:
1. Normal Held-Out Transactions (Dataset A Test)
2. Known Adversarial Transactions (Dataset C)
3. Fresh Unseen Novel Gen-2 Attacks (Dataset D)

Exports comprehensive comparison reports to:
- experiments/risk_policy_evaluation.json
- experiments/risk_policy_evaluation.csv
- experiments/risk_policy_summary.txt
"""

import argparse
import datetime
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, precision_score, recall_score, f1_score, confusion_matrix

from src.detection.predict import FraudDetector
from src.detection.risk_engine import (
    RiskDecisionEngine,
    RiskPolicy,
    RiskThresholds,
    PolicyMode,
    PaymentAction,
    RiskLevel,
)
from src.utils.config import (
    DEFAULT_SEED,
    MODELS_DIR,
    PROCESSED_DATA_DIR,
    EXPERIMENTS_DIR,
)


# =============================================================================
# COST CONFIGURATION
# =============================================================================
# Simulated relative business costs (Defensive research prototype figures)
FALSE_NEGATIVE_COST = 10.0    # Undetected fraud loss
FALSE_POSITIVE_COST = 1.0     # Erroneously blocking legitimate cardholder
STEP_UP_COST = 0.25           # Friction cost of cardholder verification challenge


# =============================================================================
# CALIBRATION AUDIT FUNCTIONS
# =============================================================================

def calculate_expected_calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> Tuple[float, List[Dict[str, Any]]]:
    """Calculate Expected Calibration Error (ECE) and bin reliability stats."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    ece = 0.0
    bin_stats: List[Dict[str, Any]] = []

    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = float(np.mean(in_bin))

        if prop_in_bin > 0:
            accuracy_in_bin = float(np.mean(y_true[in_bin]))
            avg_confidence_in_bin = float(np.mean(y_prob[in_bin]))
            diff = abs(avg_confidence_in_bin - accuracy_in_bin)
            ece += diff * prop_in_bin

            bin_stats.append({
                "bin_range": f"({bin_lower:.2f}, {bin_upper:.2f}]",
                "sample_count": int(np.sum(in_bin)),
                "empirical_fraud_rate": round(accuracy_in_bin, 4),
                "mean_predicted_prob": round(avg_confidence_in_bin, 4),
                "calibration_gap": round(diff, 4),
            })

    return round(float(ece), 4), bin_stats


# =============================================================================
# THRESHOLD ANALYSIS ENGINE
# =============================================================================

class ThresholdAnalysisEngine:
    """Evaluates decision boundaries, cost trade-offs, and policy profiles."""

    def __init__(
        self,
        detector: Optional[FraudDetector] = None,
        output_dir: Optional[Path] = None,
    ):
        self.output_dir = output_dir or EXPERIMENTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.detector = detector
        if self.detector is None:
            model_path = MODELS_DIR / "hardened_zero_day_detector.joblib"
            if not model_path.exists():
                model_path = MODELS_DIR / "baseline_detector.joblib"
            if model_path.exists():
                self.detector = FraudDetector(artifact_path=model_path)
            else:
                raise FileNotFoundError(f"Model artifact not found in {MODELS_DIR}")

    def evaluate_threshold_sweep(
        self,
        df_val: pd.DataFrame,
        thresholds: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """Evaluate performance metrics and cost trade-offs across candidate thresholds."""
        t_list = thresholds or [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.90]
        y_true = df_val["fraud_label"].to_numpy()
        probs = self.detector.predict_proba(df_val)

        results: List[Dict[str, Any]] = []

        for t in t_list:
            preds = (probs >= t).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_true, preds, labels=[0, 1]).ravel()
            total = len(y_true)

            prec = float(precision_score(y_true, preds, zero_division=0))
            rec = float(recall_score(y_true, preds, zero_division=0))
            f1 = float(f1_score(y_true, preds, zero_division=0))
            fpr = float(fp / max(1, tn + fp))

            # Simulated Relative Cost
            cost = (fn * FALSE_NEGATIVE_COST) + (fp * FALSE_POSITIVE_COST)

            results.append({
                "threshold": t,
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "fpr": round(fpr, 4),
                "true_positives": int(tp),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_negatives": int(tn),
                "fraud_caught_pct": round(rec * 100.0, 2),
                "legitimate_blocked_pct": round(fpr * 100.0, 2),
                "simulated_relative_cost": round(cost, 2),
            })

        return results

    def evaluate_policy_on_dataset(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        policy_mode: PolicyMode,
    ) -> Dict[str, Any]:
        """Evaluate a multi-tier RiskPolicy profile on a specific dataset."""
        engine = RiskDecisionEngine(detector=self.detector, policy_mode=policy_mode)
        evaluated_df = engine.evaluate_batch(df)

        y_true = df["fraud_label"].to_numpy()
        probs = evaluated_df["fraud_probability"].to_numpy()
        actions = evaluated_df["action"].to_numpy()

        # Binary equivalent: BLOCK is classified as positive fraud catch
        # STEP_UP_AUTH catches fraud via challenge (assume 90% challenge pass for legit, 95% stop for fraud)
        n_total = len(df)
        n_fraud = int(np.sum(y_true == 1))
        n_legit = int(np.sum(y_true == 0))

        # Distribution of Actions
        allow_mask = (actions == PaymentAction.ALLOW.value)
        monitor_mask = (actions == PaymentAction.MONITOR.value)
        step_up_mask = (actions == PaymentAction.STEP_UP_AUTH.value)
        block_mask = (actions == PaymentAction.BLOCK.value)

        allow_count = int(np.sum(allow_mask))
        monitor_count = int(np.sum(monitor_mask))
        step_up_count = int(np.sum(step_up_mask))
        block_count = int(np.sum(block_mask))

        # Fraud disposition
        fraud_allowed = int(np.sum(allow_mask & (y_true == 1)))
        fraud_monitored = int(np.sum(monitor_mask & (y_true == 1)))
        fraud_stepped_up = int(np.sum(step_up_mask & (y_true == 1)))
        fraud_blocked = int(np.sum(block_mask & (y_true == 1)))

        # Legitimate disposition
        legit_allowed = int(np.sum(allow_mask & (y_true == 0)))
        legit_monitored = int(np.sum(monitor_mask & (y_true == 0)))
        legit_stepped_up = int(np.sum(step_up_mask & (y_true == 0)))
        legit_blocked = int(np.sum(block_mask & (y_true == 0)))

        # In multi-tier policy:
        # Fraud Caught = Blocked + Stepped-up
        # False Negatives (Undetected Fraud) = Fraud Allowed + Fraud Monitored (allowed through)
        # False Alarms = Legitimate Blocked
        # Challenged Customers = Legitimate Stepped-up
        total_fraud_intercepted = fraud_blocked + fraud_stepped_up
        fraud_recall = float(total_fraud_intercepted / max(1, n_fraud))
        direct_block_recall = float(fraud_blocked / max(1, n_fraud))
        false_positives = legit_blocked
        false_negatives = fraud_allowed + fraud_monitored
        fpr = float(legit_blocked / max(1, n_legit))

        # Precision among intercepted/blocked
        total_intercepted = block_count + step_up_count
        precision = float(total_fraud_intercepted / max(1, total_intercepted))
        f1 = float(2 * (precision * fraud_recall) / max(1e-6, precision + fraud_recall))

        # Multi-Action Relative Cost Calculation
        total_cost = (
            (false_negatives * FALSE_NEGATIVE_COST)
            + (false_positives * FALSE_POSITIVE_COST)
            + (step_up_count * STEP_UP_COST)
        )

        return {
            "dataset_name": dataset_name,
            "policy_mode": policy_mode.value,
            "total_samples": n_total,
            "fraud_samples": n_fraud,
            "legitimate_samples": n_legit,
            "metrics": {
                "intercept_recall": round(fraud_recall * 100.0, 2),
                "direct_block_recall": round(direct_block_recall * 100.0, 2),
                "precision": round(precision * 100.0, 2),
                "f1_score": round(f1, 4),
                "false_positive_rate": round(fpr * 100.0, 2),
            },
            "action_distribution": {
                "ALLOW": allow_count,
                "MONITOR": monitor_count,
                "STEP_UP_AUTH": step_up_count,
                "BLOCK": block_count,
            },
            "fraud_breakdown": {
                "fraud_blocked": fraud_blocked,
                "fraud_stepped_up": fraud_stepped_up,
                "fraud_monitored": fraud_monitored,
                "fraud_allowed_missed": fraud_allowed,
                "total_intercepted": total_fraud_intercepted,
            },
            "legitimate_breakdown": {
                "legit_allowed_seamless": legit_allowed,
                "legit_monitored": legit_monitored,
                "legit_challenged_step_up": legit_stepped_up,
                "legit_blocked_fp": legit_blocked,
            },
            "cost_analysis": {
                "false_negatives": false_negatives,
                "false_positives": false_positives,
                "step_up_challenges": step_up_count,
                "simulated_relative_cost": round(total_cost, 2),
            },
        }

    def run_full_evaluation(self) -> Dict[str, Any]:
        """Execute complete threshold sweep, policy comparison, and calibration audit."""
        print("=" * 70)
        print("   FRAUDFORGE AI -- RISK POLICY & THRESHOLD OPTIMIZATION")
        print("=" * 70)

        # 1. Load Datasets
        path_test_a = PROCESSED_DATA_DIR / "test_split.csv"
        path_test_c = PROCESSED_DATA_DIR / "unseen_adversarial_test_c.csv"
        path_test_d = PROCESSED_DATA_DIR / "unseen_novel_test_d.csv"

        if not path_test_a.exists():
            raise FileNotFoundError(f"Dataset A test split not found at {path_test_a}. Run run_experiment.py first.")
        df_a = pd.read_csv(path_test_a)

        # Use 50% of Dataset A test as validation set for threshold tuning
        val_idx = df_a.sample(frac=0.50, random_state=42).index
        df_val = df_a.loc[val_idx].reset_index(drop=True)
        df_eval_a = df_a.drop(val_idx).reset_index(drop=True)

        df_c = pd.read_csv(path_test_c) if path_test_c.exists() else df_eval_a
        df_d = pd.read_csv(path_test_d) if path_test_d.exists() else df_eval_a

        # 2. Threshold Sweep on Validation Set
        print("\n[*] 1. Evaluating Decision Thresholds on Validation Set (Dataset A Val)...")
        sweep_results = self.evaluate_threshold_sweep(df_val)

        # Find best validation threshold by minimum simulated relative cost
        best_thresh_entry = min(sweep_results, key=lambda x: x["simulated_relative_cost"])
        print(f"    [+] Best validation threshold by relative cost: {best_thresh_entry['threshold']} (Cost: {best_thresh_entry['simulated_relative_cost']}, Recall: {best_thresh_entry['recall']*100:.1f}%, FPR: {best_thresh_entry['fpr']*100:.2f}%)")

        # 3. Probability Calibration Check
        print("\n[*] 2. Auditing Hardened Model Probability Calibration...")
        y_val_true = df_val["fraud_label"].to_numpy()
        probs_val = self.detector.predict_proba(df_val)
        brier = float(brier_score_loss(y_val_true, probs_val))
        ece, calib_bins = calculate_expected_calibration_error(y_val_true, probs_val)
        print(f"    [+] Brier Score Loss: {brier:.4f}")
        print(f"    [+] Expected Calibration Error (ECE): {ece:.4f}")

        # 4. Multi-Tier Policy Comparison Across Test Suites
        print("\n[*] 3. Evaluating Multi-Tier Risk Policies vs. Binary ML Baseline...")
        policy_evaluations: List[Dict[str, Any]] = []

        test_suites = [
            ("Dataset A (Normal Held-Out Test)", df_eval_a),
            ("Dataset C (Known Unseen Adversarial)", df_c),
            ("Dataset D (Fresh Novel Gen-2 Unseen)", df_d),
        ]

        for suite_name, df_suite in test_suites:
            # 1. Binary Baseline (Threshold = 0.50)
            binary_engine = RiskPolicy(
                mode=PolicyMode.CUSTOM,
                custom_thresholds=RiskThresholds(low_max=0.50, medium_max=0.50, high_max=0.50),
            )
            # Evaluate Binary via custom policy
            engine_bin = RiskDecisionEngine(detector=self.detector, policy=binary_engine)
            bin_eval_df = engine_bin.evaluate_batch(df_suite)
            y_s_true = df_suite["fraud_label"].to_numpy()
            bin_preds = (bin_eval_df["fraud_probability"].to_numpy() >= 0.50).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_s_true, bin_preds, labels=[0, 1]).ravel()
            bin_cost = (fn * FALSE_NEGATIVE_COST) + (fp * FALSE_POSITIVE_COST)

            binary_summary = {
                "dataset_name": suite_name,
                "policy_mode": "BINARY_BASELINE (0.50)",
                "total_samples": len(df_suite),
                "fraud_samples": int(np.sum(y_s_true == 1)),
                "legitimate_samples": int(np.sum(y_s_true == 0)),
                "metrics": {
                    "intercept_recall": round(float(tp / max(1, tp + fn)) * 100.0, 2),
                    "direct_block_recall": round(float(tp / max(1, tp + fn)) * 100.0, 2),
                    "precision": round(float(tp / max(1, tp + fp)) * 100.0, 2),
                    "f1_score": round(float(f1_score(y_s_true, bin_preds, zero_division=0)), 4),
                    "false_positive_rate": round(float(fp / max(1, tn + fp)) * 100.0, 2),
                },
                "action_distribution": {
                    "ALLOW": int(tn + fn),
                    "MONITOR": 0,
                    "STEP_UP_AUTH": 0,
                    "BLOCK": int(tp + fp),
                },
                "cost_analysis": {
                    "false_negatives": int(fn),
                    "false_positives": int(fp),
                    "step_up_challenges": 0,
                    "simulated_relative_cost": round(bin_cost, 2),
                },
            }
            policy_evaluations.append(binary_summary)

            # 2. Balanced Policy
            bal_res = self.evaluate_policy_on_dataset(df_suite, suite_name, PolicyMode.BALANCED)
            policy_evaluations.append(bal_res)

            # 3. Strict Security Policy
            strict_res = self.evaluate_policy_on_dataset(df_suite, suite_name, PolicyMode.STRICT_SECURITY)
            policy_evaluations.append(strict_res)

        # 5. Export Structured Artifacts
        report_data = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "cost_framework_assumptions": {
                "false_negative_cost": FALSE_NEGATIVE_COST,
                "false_positive_cost": FALSE_POSITIVE_COST,
                "step_up_cost": STEP_UP_COST,
                "note": "Simulated relative research costs; not real Mastercard financial values.",
            },
            "threshold_sweep_validation": sweep_results,
            "best_validation_threshold": best_thresh_entry,
            "probability_calibration_audit": {
                "brier_score_loss": brier,
                "expected_calibration_error": ece,
                "reliability_bins": calib_bins,
            },
            "policy_evaluations": policy_evaluations,
        }

        # JSON Export
        json_path = self.output_dir / "risk_policy_evaluation.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        # CSV Export
        csv_rows = []
        for pe in policy_evaluations:
            row = {
                "dataset_name": pe["dataset_name"],
                "policy_mode": pe["policy_mode"],
                "total_samples": pe["total_samples"],
                "intercept_recall_pct": pe["metrics"]["intercept_recall"],
                "direct_block_recall_pct": pe["metrics"]["direct_block_recall"],
                "precision_pct": pe["metrics"]["precision"],
                "f1_score": pe["metrics"]["f1_score"],
                "fpr_pct": pe["metrics"]["false_positive_rate"],
                "allow_count": pe["action_distribution"]["ALLOW"],
                "monitor_count": pe["action_distribution"]["MONITOR"],
                "step_up_count": pe["action_distribution"]["STEP_UP_AUTH"],
                "block_count": pe["action_distribution"]["BLOCK"],
                "false_negatives": pe["cost_analysis"]["false_negatives"],
                "false_positives": pe["cost_analysis"]["false_positives"],
                "simulated_relative_cost": pe["cost_analysis"]["simulated_relative_cost"],
            }
            csv_rows.append(row)
        csv_path = self.output_dir / "risk_policy_evaluation.csv"
        pd.DataFrame(csv_rows).to_csv(csv_path, index=False)

        # Summary TXT Export
        txt_path = self.output_dir / "risk_policy_summary.txt"
        self._export_summary_text(report_data, txt_path)

        self._print_terminal_summary(report_data)
        print(f"\n[+] JSON Report:  {json_path}")
        print(f"[+] CSV Report:   {csv_path}")
        print(f"[+] Summary File: {txt_path}")

        return report_data

    def _export_summary_text(self, report: Dict[str, Any], output_path: Path) -> None:
        """Format human-readable summary text file."""
        lines = [
            "=" * 75,
            "FRAUDFORGE AI -- RISK-AWARE DECISION ENGINE & POLICY EVALUATION SUMMARY",
            "=" * 75,
            f"Timestamp: {report['timestamp']}",
            "",
            "1. COST FRAMEWORK & POLICY THRESHOLDS",
            f"  - Relative Costs (Simulated): FN Cost = {FALSE_NEGATIVE_COST}, FP Cost = {FALSE_POSITIVE_COST}, Step-Up Cost = {STEP_UP_COST}",
            "  - Balanced Policy Thresholds        : LOW < 0.30 | MEDIUM < 0.60 | HIGH < 0.85 | CRITICAL >= 0.85",
            "  - Strict Security Policy Thresholds : LOW < 0.20 | MEDIUM < 0.45 | HIGH < 0.70 | CRITICAL >= 0.70",
            "",
            "2. VALIDATION THRESHOLD SWEEP & PROBABILITY CALIBRATION",
            f"  - Best Validation Threshold (by Min Cost) : {report['best_validation_threshold']['threshold']} (Simulated Cost: {report['best_validation_threshold']['simulated_relative_cost']})",
            f"  - Brier Score Loss                        : {report['probability_calibration_audit']['brier_score_loss']:.4f}",
            f"  - Expected Calibration Error (ECE)        : {report['probability_calibration_audit']['expected_calibration_error']:.4f}",
            "",
            "3. MULTI-TIER POLICY COMPARISON BY DATASET",
        ]

        for pe in report["policy_evaluations"]:
            m = pe["metrics"]
            act = pe["action_distribution"]
            cost = pe["cost_analysis"]
            lines.extend([
                f"  [{pe['dataset_name']} - {pe['policy_mode']}]",
                f"    • Intercept Recall : {m['intercept_recall']:>5.1f}% | Direct Block Recall: {m['direct_block_recall']:>5.1f}% | FPR: {m['false_positive_rate']:>5.2f}%",
                f"    • Action Breakdown : ALLOW={act['ALLOW']}, MONITOR={act['MONITOR']}, STEP_UP={act['STEP_UP_AUTH']}, BLOCK={act['BLOCK']}",
                f"    • Business Impact  : FN={cost['false_negatives']}, FP={cost['false_positives']} | Relative Decision Cost = {cost['simulated_relative_cost']}",
                "",
            ])

        lines.extend([
            "=" * 75,
            "INSIGHT:",
            '"The ML detector estimates fraud risk. The risk engine converts that score',
            'into practical multi-tier payment actions: allow, monitor, step-up challenge, or block.',
            'Multi-action risk policies substantially lower business loss by resolving ambiguous',
            'medium-to-high risk transactions via authentication challenge rather than direct rejection."',
            "=" * 75,
        ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def _print_terminal_summary(self, report: Dict[str, Any]) -> None:
        """Print clean terminal comparison table."""
        print("\n" + "=" * 80)
        print("                 FRAUDFORGE AI -- RISK POLICY BENCHMARK")
        print("=" * 80)
        print(f"\n{'Dataset / Policy Mode':<42} | {'Intercept Rec':<13} | {'FPR':<7} | {'Step-Up':<8} | {'Block':<7} | {'Cost'}")
        print("-" * 80)

        for pe in report["policy_evaluations"]:
            m = pe["metrics"]
            act = pe["action_distribution"]
            cost = pe["cost_analysis"]
            title = f"{pe['dataset_name'][:22]} ({pe['policy_mode'][:15]})"
            print(
                f"{title:<42} | "
                f"{m['intercept_recall']:>11.1f}% | "
                f"{m['false_positive_rate']:>5.2f}% | "
                f"{act['STEP_UP_AUTH']:>8d} | "
                f"{act['BLOCK']:>7d} | "
                f"{cost['simulated_relative_cost']:>7.1f}"
            )

        print("=" * 80)


def main() -> None:
    """CLI runner for Threshold Analysis and Risk Policy Benchmarking."""
    parser = argparse.ArgumentParser(description="FraudForge AI: Threshold Analysis & Risk Policy Benchmarks")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for reports")
    args = parser.parse_args()

    engine = ThresholdAnalysisEngine(
        output_dir=Path(args.output_dir) if args.output_dir else None
    )
    engine.run_full_evaluation()


if __name__ == "__main__":
    main()
