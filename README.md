# FraudForge AI — Closed-Loop Adversarial Payment Defense & Zero-Day Hardening Framework

> **Mastercard Innovation Challenge @ Global Fintech Fest (GFF) 2026**  
> *"Attack the detector. Uncover the blind spot. Retrain on synthetic data. Generalize to unseen fraud."*

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.1.0-orange.svg)](https://xgboost.readthedocs.io/)
[![Tests Passing](https://img.shields.io/badge/pytest-72%2F72%20passing-brightgreen)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## ⚠️ Synthetic Defensive Research & Simulation Disclaimer
**FraudForge AI is a synthetic defensive simulation and adversarial machine learning research prototype.**  
- All transaction streams, customer profiles, and behavioral telemetry are synthesized using calibrated statistical distributions (Pareto, log-normal, beta, diurnal curves).
- Attack archetypes and genomes represent defensive testing scenarios to probe detector blind spots.
- Policy thresholds, risk tiers, and simulated cost metrics demonstrate algorithmic concepts and do **not** represent Mastercard's proprietary production rules, live fraud parameters, or global payment routing.

---

## 🛡️ Executive Summary

Modern fraud detection systems suffer from an **asymmetric vulnerability**: while financial institutions train models on historical fraud registries, threat actors use Generative AI, autonomous agents, and polymorphic evasion to craft zero-day vectors. Because legacy classifiers over-rely on historical cues (such as sudden device changes or extreme velocities), sophisticated adversaries bypass detection simply by masking these specific signals.

**FraudForge AI** proactively solves this problem through a closed-loop **Red Team / Blue Team AI Defense Lab**:
1. **Deconstructs** attacks into an orthogonal **10-dimensional Attack Genome** across 28 archetypes.
2. **Discovers** novel synthetic attack variants algorithmically and tests them against the baseline model to expose detector blind spots.
3. **Hardens** the detector via automated adversarial retraining on mined false negatives.
4. **Proves Generalization**: Demonstrates that adversarial retraining transfers to completely unseen Generation-2 attack variants, raising recall from **23.10% to 93.80% (+70.70 percentage points)** with a **91.9% reduction in false negatives** on synthetic benchmarks.
5. **Operationalizes Decisions**: Translates calibrated probabilities into four actionable tiers (**ALLOW**, **MONITOR**, **STEP_UP_AUTH**, **BLOCK**) with transparent, explainable reason codes.

---

## 🧬 Key Innovations

```
      KNOWN ATTACK
           ↓
     ATTACK GENOME (10-Dimensional Space)
           ↓
    SYNTHETIC VARIANT (Mutation & Crossover)
           ↓
    BASELINE DETECTOR (Tested on 100 Transactions)
           ↓
    BLIND SPOT FOUND (e.g. 23.1% / 48.0% Recall)
           ↓
  FALSE NEGATIVES MINED (Feature Rebalancing)
           ↓
  ADVERSARIAL HARDENING (Augmented Retraining)
           ↓
    HARDENED DETECTOR (XGBoost Classifier)
           ↓
    UNSEEN GEN-2 TEST (Dataset D Benchmark)
           ↓
     GENERALIZATION (+70.70 pt Recall Gain)
```

1. **10-Dimensional Attack Genome**: Deconstructs payment fraud into `target`, `entry_vector`, `behavior`, `evasion_strategy`, `payment_channel`, `amount_strategy`, `temporal_strategy`, `identity_strategy`, `merchant_strategy`, and `geographic_strategy`.
2. **Transparent Multi-Objective Scoring**: Ranks discovered candidates by Novelty, Domain Realism, and Detector-Weakness Evasion Potential.
3. **Verified Gen-2 Generalization**: Evaluated on fresh, unseen Generation-2 variants (`seed=2026`) that were never present in training data.
4. **Risk-Aware Decision Engine**: Multi-tier policy reducing simulated business cost by **37.4%** compared to binary classification by challenging rather than declining ambiguous payments.

---

## 📊 Empirical Benchmark Results

| Metric / Scenario | Baseline XGBoost Detector | Hardened XGBoost Detector | Impact / Improvement |
| :--- | :---: | :---: | :---: |
| **Unseen Gen-2 Attack Recall (Dataset D)** | **23.10%** (769 missed) | **93.80%** (62 missed) | **+70.70 pts** (**91.9% fewer misses**) |
| **Gen-1 Adversarial Training Set Recall** | 22.10% | **99.10%** | **+77.00 pts** |
| **Normal Legitimate Payment Recall** | 96.33% | **98.33%** | **+2.00%** |
| **Normal False Positive Rate (FPR)** | **0.94%** | 2.88% | +1.94% (Regulated Calibration) |
| **Probability Calibration (Brier / ECE)** | Brier: 0.0410 | **Brier: 0.0181 \| ECE: 0.0309** | Highly Calibrated |
| **Policy Cost Index (Simulated)** | 38.0 (Binary Threshold) | **23.8 (Balanced Policy)** | **-37.4% Business Loss** |

---

## 📁 Repository Structure

```
FraudForge-AI/
├── src/
│   ├── attacks/                 # Red-Team: Attack Genome & Genetic Discovery Engine
│   │   ├── attack_library.py    # 28 Cataloged Archetypes
│   │   ├── attack_genome.py     # 10-Dimensional Genome Vocabulary
│   │   ├── novelty_engine.py    # Multi-Objective Scoring (Novelty, Realism, Evasion)
│   │   └── attack_discovery.py  # Genetic Evolution & Simulator Testing
│   ├── simulation/              # Synthetic Transaction Generator & Correlated Distributions
│   ├── features/                # RobustScaler, OneHotEncoder & Feature Pipeline
│   ├── detection/               # Blue-Team: XGBoost Detector, Risk Engine & Policy Optimizer
│   │   ├── train.py             # Baseline Training
│   │   ├── predict.py           # Inference Engine
│   │   ├── evaluate.py          # Granular Per-Attack Evaluation
│   │   └── risk_engine.py       # Multi-Tier Actions & Reason Codes
│   ├── adversarial/             # Zero-Day Hardening & Gen-2 Generalization Benchmark
│   ├── api/                     # FastAPI REST API Application & Pydantic Schemas
│   └── utils/                   # Schema Configurations & Global Constants
├── frontend/
│   └── index.html               # Single-Page Interactive Security Dashboard
├── models/                      # Serialized ML Model Artifacts (.joblib)
├── experiments/                 # Verified Empirical Benchmark JSON / CSV Reports
├── docs/                        # Solution Walkthrough, 90s Script, Run Guide & Checklist
└── tests/                       # 72 Passing Automated Pytest Suite
```

---

## 🚀 Quick Start & Reproduction

### 1. Installation
```powershell
# Clone and enter the repository
git clone https://github.com/sudarshanchaudhari05/FraudForge-AI.git
cd FraudForge-AI

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Backend & Frontend Services

**Terminal 1 — Python ML Backend (FastAPI):**
```powershell
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
*Health endpoint*: `http://127.0.0.1:8000/api/v1/health`  
*Swagger docs*: `http://127.0.0.1:8000/docs`

**Terminal 2 — Interactive Frontend Prototype:**
```powershell
python -m http.server 3000 --directory frontend
```
*Frontend URL*: `http://localhost:3000`

---

## 🧪 Running Automated Tests

Run the complete 72-test test suite:
```powershell
pytest -v
```
```text
====================== 72 passed, 25 warnings in 16.28s =======================
```

---

## 🎯 90-Second Demo Highlights

1. **Live Connection**: Header displays `LIVE PYTHON ML BACKEND` with a pulsing green dot.
2. **Attack Lab**: Select `ATK-012` (Stealth Biometric Injection) &rarr; Click **"⚡ TEST ATTACK"** &rarr; Exposes `48.00% Recall` (52 Misses).
3. **State Bridge**: Click **"SEND TO DEFENSE LAB →"** &rarr; Automatically transfers the custom genome to Defense Lab.
4. **Adaptive Hardening**: Click **"▶ RUN ADAPTIVE HARDENING"** &rarr; 9-stage pipeline retrains XGBoost &rarr; Switch to `Unseen Gen-2 Attack Suite` to verify the **+70.70 pt generalization gain (23.1% → 93.8% recall)**.
5. **Risk Engine**: Click **"RISK DECISION ENGINE"** &rarr; Score single transactions with autonomous actions (`ALLOW`, `MONITOR`, `STEP_UP_AUTH`, `BLOCK`) and transparent reason codes.

---

## 📚 Complete Documentation

- 📖 [Solution Walkthrough](docs/FraudForge_AI_Solution_Walkthrough.md): Full technical paper and deep-dive architecture.
- ⏱️ [90-Second Judge Demo Script](docs/90_Second_Judge_Demo_Script.md): Exact timeline, clicks, numbers, and spoken script for competition judging.
- 🛠️ [Run & Demo Guide](docs/RUN_AND_DEMO_GUIDE.md): Local execution, troubleshooting, and port conflict handling.
- ✅ [Final Submission Checklist](docs/FINAL_SUBMISSION_CHECKLIST.md): Pre-submission verification checklist.

---

## ⚖️ License & Credits
Developed for the **Mastercard Innovation Challenge @ Global Fintech Fest 2026**.  
Distributed under the MIT License.
