# FraudForge AI — Closed-Loop Red Team / Blue Team AI Defense Lab

> **Mastercard Innovation Challenge @ GFF 2026 — AI Defense Lab for Payment Security**  
> *"Attack the detector. Learn from the miss. Build a stronger defense."*

---

## 🛡️ Executive Summary

**FraudForge AI** is an adversarial payment security framework designed to detect, simulate, and defend against emerging **GenAI-powered payment fraud vectors**. Rather than relying on static rules or legacy point-in-time classifiers, FraudForge AI operates a closed-loop **IDENTIFY → GENERATE → DEFEND** cycle:

1. **IDENTIFY**: Curates a library of 28 realistic GenAI fraud archetypes (voice clone APP, deepfake video KYC, autonomous agent injection, behavioral mimicry, smurfing).
2. **GENERATE**: Synthesizes high-fidelity, statistically correlated transaction streams with behavioral telemetry.
3. **DEFEND**: Evaluates blue-team detection performance by individual attack vector, mutates missed attacks via red-team feedback, and hardens the model.

---

## 📁 Repository Structure

```
fraudforge-ai/
├── README.md                           # Project documentation & runbook
├── requirements.txt                    # Core Python dependencies
├── .gitignore                          # Standard Python & data gitignore
│
├── data/
│   ├── raw/                            # Raw data store (.gitkeep)
│   ├── generated/                      # Generated synthetic datasets
│   └── processed/                      # Transformed & normalized feature sets
│
├── src/
│   ├── __init__.py
│   ├── attacks/
│   │   ├── __init__.py
│   │   ├── attack_library.py           # 28 GenAI fraud archetypes catalog & query API
│   │   └── attack_mutator.py           # [Phase 3] Adversarial mutation engine
│   │
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── distributions.py            # Diurnal curves, category parameters, risk priors
│   │   └── transaction_generator.py    # Synthetic payment generator & validator
│   │
│   ├── features/
│   │   ├── __init__.py
│   │   └── feature_engineering.py      # [Phase 2] Preprocessing & feature pipelines
│   │
│   ├── detection/
│   │   ├── __init__.py
│   │   ├── train.py                    # [Phase 2] Baseline XGBoost / RF trainer
│   │   ├── predict.py                  # [Phase 2] Scoring inference engine
│   │   └── evaluate.py                 # [Phase 2] Attack-specific evaluation metrics
│   │
│   ├── adversarial/
│   │   ├── __init__.py
│   │   └── feedback_loop.py            # [Phase 3] Closed-loop retraining pipeline
│   │
│   └── utils/
│       ├── __init__.py
│       └── config.py                   # Global constants, schema definitions & paths
│
├── models/                             # Saved model artifacts (.gitkeep)
├── experiments/                        # Benchmark outputs & run metrics (.gitkeep)
├── notebooks/                          # Exploration & demonstration notebooks (.gitkeep)
└── tests/
    ├── __init__.py
    ├── test_attack_library.py          # Unit tests for attack intelligence catalog
    └── test_transaction_generator.py   # Unit tests for data generator & invariants
```

---

## 🧬 Attack Intelligence Library (28 Archetypes)

The library catalogs 28 distinct GenAI payment fraud vectors organized into 7 functional categories:

| Category | Count | Sample Archetypes |
| :--- | :---: | :--- |
| **AI Social Engineering & Impersonation** | 4 | Voice Clone Executive APP (`ATK-001`), Conversational Phishing Agent (`ATK-002`), Deepfake Family Emergency (`ATK-003`) |
| **Synthetic Identity & Deepfake Onboarding** | 4 | Deepfake Video KYC Bypass (`ATK-005`), Generative Identity Fabrication (`ATK-006`), Diffusion Statement Forgery (`ATK-007`) |
| **Automated ATO & Behavioral Mimicry** | 5 | Keystroke Cadence Mimicry (`ATK-009`), Adaptive Credential Stuffing (`ATK-010`), Stealth Biometric Injection (`ATK-012`) |
| **Evasive & Micro-Transaction Attacks** | 4 | Low-and-Slow Micro-Carding (`ATK-013`), AI Smurfing / Structuring (`ATK-014`), Velocity-Throttled Draining (`ATK-015`) |
| **AI Agent & API Payment Exploits** | 5 | Agent Prompt Hijack (`ATK-017`), Malicious MCP Tool Exploit (`ATK-018`), Risk Scoring Perturbation Evasion (`ATK-021`) |
| **Cross-Channel & Cross-Border Evasion** | 4 | AI Residential Proxy Swarm (`ATK-022`), Triangular Currency Arbitrage (`ATK-023`), POS-to-Web Fast Bypass (`ATK-024`) |
| **E-Commerce & Merchant Exploits** | 2 | AI-Generated RMA Return Fraud (`ATK-026`), Synthetic Subscription Layering (`ATK-027`) |

Each archetype defines:
* `attack_id`, `name`, `category`, `description`, `severity`
* `novelty_score` (0.0–1.0) and `detectability_score` (0.0–1.0)
* `behavioral_indicators` (telemetry and behavioral anomalies)
* `affected_payment_surface` (e-commerce, p2p, mobile_app, pos, api_gateway)
* `simulation_parameters` (precise numerical shifts for amount, velocity, timing, device, and risk priors)

---

## 📊 Dataset Schema & Behavioral Correlated Features

The generated dataset contains **22 features** with realistic statistical distributions and domain invariants:

### Numerical Features (15)
* `transaction_amount`: Transaction amount ($)
* `transaction_hour`: Hour of transaction (0–23, following diurnal curve)
* `account_age_days`: Age of account in days (1–1800)
* `device_age_days`: Age of active device in days (1–account_age_days)
* `device_change`: Binary indicator for newly registered device (0 or 1)
* `IP_risk_score`: IP reputation anomaly score (0.0–1.0)
* `merchant_risk_score`: Category and gateway risk score (0.0–1.0)
* `transaction_velocity_1h`: Transaction count in past 1 hour ($\ge 1$)
* `transaction_velocity_24h`: Transaction count in past 24 hours ($\ge \text{velocity\_1h}$)
* `average_customer_amount`: Historical customer average spending ($)
* `amount_deviation`: Ratio deviation: $\frac{\text{amount} - \text{avg}}{\text{avg}}$
* `geographic_deviation`: Binary cross-border anomaly flag (0 or 1)
* `behavioral_deviation`: Keystroke/navigation biometric anomaly score (0.0–1.0)
* `failed_authentication_count`: Recent failed 2FA/password attempts ($\ge 0$)
* `identity_risk_score`: Synthetic identity / KYC anomaly score (0.0–1.0)

### Categorical Features (5)
* `merchant_category`: `groceries`, `retail`, `dining`, `travel`, `digital_goods`, `gaming`, `luxury`, `crypto_exchange`, `money_transfer`, `utilities`, `electronics`, `marketplace`
* `payment_channel`: `pos_contactless`, `pos_chip`, `e-commerce`, `mobile_app`, `recurring_subscription`, `p2p_transfer`, `api_gateway`
* `authentication_method`: `biometric`, `3ds_v2`, `sms_otp`, `password`, `none`, `hardware_token`, `push_notification`
* `transaction_country`: ISO 2-letter country code
* `customer_country`: Customer primary registration country

### Target & Ground Truth (2)
* `attack_type`: `LEGITIMATE` or specific attack archetype name
* `fraud_label`: `0` (Legitimate) or `1` (Fraudulent)

---

## 🚀 Quick Start & Reproducibility

### 1. Installation
```bash
# Clone the repository and navigate into the root folder
cd fraudforge-ai

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Complete Closed-Loop Experiment (Single Entry Point)
Run the entire **IDENTIFY → GENERATE → DEFEND → ATTACK → LEARN → HARDEN → TEST** pipeline with a single command:
```bash
python run_experiment.py
```
### 3. Run Zero-Day Adaptive Hardening & Re-Attack (Phase 6)
```bash
# Execute end-to-end Zero-Day discovery, blue-team hardening, and Gen-2 generalization re-attack
python run_experiment.py --zero-day
# Or via the standalone module:
python -m src.adversarial.zero_day_hardening --samples 10000 --fraud-ratio 0.15 --novel-candidates 80
```

### 4. Run Novel Synthetic Attack Discovery (Phase 5)
```bash
# Decompose attack genomes, generate novel synthetic candidates, and discover detector blind spots
python -m src.attacks.attack_discovery --raw-candidates 80 --retained 15 --samples 200
```

### 5. Run Robustness Benchmarks & Feature Ablation Experiments
```bash
# Execute model architecture comparisons (XGBoost vs Random Forest) and feature ablation studies
python -m src.detection.benchmarks
```

### 6. Run Automated Test Suite
```bash
pytest -v
```

---

## 🧬 Novel Synthetic Attack Discovery (Phase 5)

> **Clarification & Scope**: *Attack genomes and novel candidates represent synthetic defensive research scenarios designed to proactively test detection boundaries. They do NOT represent real-world zero-day vulnerabilities in payment networks.*

### 1. The Attack Genome Architecture

Rather than treating fraud attacks as monolithic scripts, FraudForge AI decomposes every attack archetype into a 10-dimensional behavioral **Attack Genome**:

```
Attack Genome
├── target              (account, identity, merchant, payment_agent, checkout, payment_authorization, customer)
├── entry_vector        (credential_abuse, prompt_manipulation, deepfake_synthesis, social_engineering, session_hijacking, api_exploit, ...)
├── behavior            (low_and_slow, burst_velocity, behavioral_mimicry, cross_channel, cart_manipulation, identity_fabrication, ...)
├── evasion_strategy    (trusted_device_masking, velocity_smoothing, amount_camouflage, trusted_session_behavior, risk_signal_suppression, ...)
├── payment_channel     (e-commerce, p2p_transfer, mobile_app, api_gateway, pos_chip, pos_contactless, recurring_subscription)
├── amount_strategy     (normal_looking, micro_transactions, high_ticket_escalation, sub_threshold_structuring, stealth_discounted, ...)
├── temporal_strategy   (distributed, off_hours, daytime_peak, rapid_burst, even_interval)
├── identity_strategy   (existing_account, synthetic_sleeper, fabricated_identity, delegated_agent, swapped_sim, authorized_victim)
├── merchant_strategy   (single_target, mcc_rotation, high_risk_crypto, digital_marketplace, micro_refunds, luxury_retail)
└── geographic_strategy (domestic_matching, cross_border_arbitrage, residential_proxy_spoofed)
```

All **28 known archetypes** are indexed into ground-truth genome representations.

### 2. Candidate Generation & Evolution

Novel candidates are synthesized via deterministic genetic operators:
- **Mutation**: Targeted replacement of 1–3 gene traits with compatible alternatives.
- **Crossover**: Combining compatible gene traits from two distinct parent archetypes.
- **Compatibility Validation**: Enforcing 9 domain logic rules (e.g. physical POS channels cannot execute headless API exploits without cross-channel mechanics).
- **Near-Duplicate Filtering**: Weighted gene distance metrics prune candidates too close to known attacks ($>85\%$ similarity) or previously accepted candidates ($>90\%$ similarity).

### 3. Explainable Multi-Objective Scoring

1. **Novelty Score ($0.0 - 1.0$)**:
   $$\text{Novelty} = 1.0 - \max_{k \in \text{Known}} \text{Similarity}(\text{Candidate}, k)$$
2. **Realism Score ($0.0 - 1.0$)**: Rule-based reward for plausible channel/entry synergy, coherent target/behavior pairings, and evasion strategies.
3. **Evasion Potential ($0.0 - 1.0$)**: Derived directly from empirical detector weaknesses (normal-looking amounts, velocity smoothing, trusted-device masking, residential proxy spoofing).
4. **Priority Score ($0.0 - 1.0$)**:
   $$\text{Priority} = 0.40 \times \text{Novelty} + 0.30 \times \text{Realism} + 0.30 \times \text{Evasion Potential}$$

### 4. Simulator Integration & Blind-Spot Discovery

Discovered genomes are automatically compiled into simulation parameters, synthesized into live transaction streams via `TransactionGenerator`, and evaluated against the baseline detector:

| Discovered Candidate | Key Traits | Novelty | Realism | Evasion | Detection Rate | Blind-Spot Severity |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **NSA-001** | Trusted-Device MCP Tool Micro-Payment Abuse | 0.22 | 0.82 | 0.97 | **16.0%** | 🚨 **CRITICAL BLIND SPOT** |
| **NSA-002** | Trusted-Device Burst Account Takeover | 0.28 | 0.86 | 0.76 | **24.0%** | 🚨 **CRITICAL BLIND SPOT** |
| **NSA-006** | Trusted-Device Low-and-Slow Push Payment Fraud | 0.23 | 0.75 | 0.86 | **6.5%** | 🚨 **CRITICAL BLIND SPOT** |
| **NSA-010** | Camouflaged Behavioral Mimicry Push Payment Fraud | 0.29 | 0.75 | 0.73 | **15.5%** | 🚨 **CRITICAL BLIND SPOT** |
| **NSA-012** | Trusted-Device Low-and-Slow Social Engineering Trap | 0.19 | 0.70 | 0.86 | **5.5%** | 🚨 **CRITICAL BLIND SPOT** |

All structured discoveries are exported to `experiments/novel_attack_candidates.json` and `experiments/novel_attack_report.csv`.

---

## 🔬 Robustness & Model Benchmarking (Phase 4 / 4B)

### 1. Synthetic Payment Realism Upgrade (Phase 4B)

We calibrated the synthetic generator distributions to eliminate artificial separation cues:

| Feature | Pre-Realism Separation | Post-Realism Separation | Status |
| :--- | :---: | :---: | :---: |
| **`device_change`** | Legit: 3.75% \| Fraud: 75.75% ($d = 2.172, KS = 0.720$) | Legit: **15.51%** \| Fraud: **52.53%** ($d = 0.849, KS = 0.370$) | ✅ **Realistic Overlap** |
| **`merchant_risk_score`** | Legit: 0.1630 \| Fraud: 0.5166 ($d = 1.858, KS = 0.709$) | Legit: **0.1659** \| Fraud: **0.4431** ($d = 1.355, KS = 0.543$) | ✅ **Moderate Separation** |
| **`transaction_amount`** | Legit: $79.43 \| Fraud: $803.96 ($d = 1.257, KS = 0.596$) | Legit: **$92.47** \| Fraud: **$230.08** ($d = 0.730, KS = 0.307$) | ✅ **Realistic Overlap** |
| **`amount_deviation`** | Legit: 0.2360 \| Fraud: 14.65 ($d = 0.899, KS = 0.655$) | Legit: **0.4807** \| Fraud: **3.4327** ($d = 0.583, KS = 0.317$) | ✅ **Realistic Overlap** |

### 2. Model Architecture Comparison (Realistic Dataset)

Both models evaluated on identical stratified splits (Dataset A normal test & Dataset C unseen adversarial test):

| Model | Normal F1 | Normal Recall | Adversarial Recall (Dataset C) | Adversarial F1 | Adversarial Misses |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **XGBoost (Full Features)** | **0.9554** | **96.33%** | 68.00% | 0.7846 | 96 missed |
| **Random Forest (Full Features)** | 0.9502 | 94.67% | **76.00%** | **0.8352** | **72 missed** |

### 3. Adaptive Red-Team Hardening on Realistic Data

| Metric | Baseline Detector | Hardened Detector | Improvement (Delta) |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 94.40% | **97.05%** | **+2.65%** |
| **Precision** | **92.73%** | 90.85% | -1.88% |
| **Adversarial Recall** | 68.00% | **89.33%** | **+21.33%** |
| **F1 Score** | 0.7846 | **0.9008** | **+0.1162** |
| **ROC-AUC** | 0.9790 | **0.9885** | **+0.0095** |
| **False Positive Rate** | **0.94%** | 1.59% | +0.65% |
| **Missed Attacks (FN)** | 96 missed | **32 missed** | **-64 (-66.7% reduction)** |

---

## 🛡️ Zero-Day Adaptive Hardening & Re-Attack (Phase 6)

> **Core Concept**: *FraudForge discovered previously unseen synthetic attack patterns, used the detector's blind spots as adversarial training data, and evaluated whether the hardened detector generalized to fresh attack variants.*

### 1. Re-Attack on Novel Training Candidates (Gen-1)

| Candidate ID | Discovered Attack Archetype | Baseline Detection | Hardened Detection | Improvement ($\Delta$) |
| :--- | :--- | :---: | :---: | :---: |
| **NSA-001** | Trusted-Device Omnichannel Social Engineering Trap | 10.5% | **97.5%** | **+87.0%** |
| **NSA-003** | Trusted-Device Low-and-Slow Merchant Return Arbitrage | 7.0% | **100.0%** | **+93.0%** |
| **NSA-008** | Biometric-Injected Behavioral Mimicry Account Takeover | 11.5% | **98.0%** | **+86.5%** |
| **NSA-012** | Camouflaged Cart Manipulation Social Engineering Trap | 27.5% | **100.0%** | **+72.5%** |
| **NSA-004** | Signal-Suppressed Low-and-Slow Checkout Exploit | 54.0% | **100.0%** | **+46.0%** |

### 2. Generalization Benchmark on Fresh Unseen Gen-2 Variants (Dataset D)

To prove generalization rather than memorization, fresh Generation-2 evolved variants (`NSA-XXX-V2`) were generated with distinct random seeds (`seed=2026`), mutated sub-genes, and modified distributions that were **never present during training**:

| Evolved Variant ID | Unseen Gen-2 Attack Variant | Baseline Detection | Hardened Detection | Generalization Gain |
| :--- | :--- | :---: | :---: | :---: |
| **NSA-001-V2** | Trusted-Device Omnichannel Social Engineering (Gen-2) | 14.5% | **79.0%** | **+64.5%** |
| **NSA-003-V2** | Trusted-Device Low-and-Slow Return Arbitrage (Gen-2) | 7.0% | **100.0%** | **+93.0%** |
| **NSA-008-V2** | Biometric-Injected Behavioral Mimicry ATO (Gen-2) | 37.0% | **99.0%** | **+62.0%** |
| **NSA-012-V2** | Camouflaged Cart Manipulation Social Trap (Gen-2) | 1.5% | **91.0%** | **+89.5%** |
| **NSA-004-V2** | Signal-Suppressed Low-and-Slow Checkout (Gen-2) | 55.5% | **100.0%** | **+44.5%** |
| **OVERALL** | **Overall Unseen Gen-2 Generalization (Dataset D)** | **23.10%** | **93.80%** | **+70.70 pts** |

* **Total Missed Attacks on Unseen Gen-2**: Reduced from **769 down to 62** (**-707 misses, 91.9% reduction in false negatives**).

### 3. Defender Regression Check (Normal Payments)

| Metric | Baseline Detector | Hardened Detector | Delta |
| :--- | :---: | :---: | :---: |
| **Normal Recall** | 96.33% | **98.33%** | **+2.00%** |
| **Normal F1 Score** | 0.9554 | **0.9161** | -0.0392 |
| **Normal False Positive Rate** | 0.94% | **2.88%** | +1.94% |

All structured zero-day experiment artifacts are exported to `experiments/zero_day_hardening_report.json`, `experiments/zero_day_hardening_report.csv`, and `experiments/zero_day_hardening_summary.txt`.

---

## ⚖️ Risk-Aware Decision Engine & Production-Style Mitigation (Phase 7)

> **Clarification & Scope**: *The ML detector estimates fraud risk. The risk engine converts that score into a practical payment action: allow, monitor, step-up authentication, or block. This is a simulated policy layer for the research prototype and does not represent Mastercard's actual production decision thresholds or proprietary financial cost structures.*

### 1. Decision Architecture: Multi-Tier Risk Tiers & Payment Actions

```
Transaction Features
       │
       ▼
[ Fraud Feature Pipeline ]
       │
       ▼
[ Hardened XGBoost Detector ] ──▶ Fraud Probability (0.00 – 1.00)
                                            │
       ┌────────────────────────────────────┘
       ▼
[ Risk Decision Engine ] ──▶ Risk Score (0 – 100)
       │
       ├── [0.00 – 0.30)  LOW Risk      ──▶ ALLOW         (Seamless capture)
       ├── [0.30 – 0.60)  MEDIUM Risk   ──▶ MONITOR       (Approved + Telemetry observation)
       ├── [0.60 – 0.85)  HIGH Risk     ──▶ STEP_UP_AUTH  (3DS, Biometric Push, OTP)
       └── [0.85 – 1.00]  CRITICAL Risk ──▶ BLOCK         (Direct payment rejection)
```

### 2. Multi-Tier Policy vs. Binary ML Baseline Comparison

| Dataset & Scenario | Decision Policy | Fraud Intercept Recall | Direct Block Recall | False Positive Rate | Step-Up Challenges | Direct Blocks | Simulated Relative Cost |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dataset A (Normal Test)** | Binary ML Baseline (0.50) | 99.3% | 99.3% | 3.31% | 0 | 181 | 38.0 |
| | **BALANCED Policy** | **99.3%** | 80.0% | **1.06%** | 19 | 156 | **23.8 (-37.4%)** |
| | **STRICT_SECURITY Policy** | **99.3%** | 85.0% | **1.54%** | 22 | 165 | **28.5 (-25.0%)** |
| **Dataset C (Known Unseen Adversarial)** | Binary ML Baseline (0.50) | 93.7% | 93.7% | 3.00% | 0 | 332 | 241.0 |
| | **STRICT_SECURITY Policy** | **94.0%** | 84.7% | **1.59%** | 43 | 295 | **217.8 (-9.6%)** |
| **Dataset D (Fresh Gen-2 Unseen Attacks)** | Binary ML Baseline (0.50) | 93.8% | 93.8% | 2.30% | 0 | 961 | 643.0 |
| | **STRICT_SECURITY Policy** | **94.2%** | 68.8% | **1.00%** | 66 | 901 | **606.5 (-5.7%)** |

*(Cost Framework: $\text{FN Cost} = 10.0$, $\text{FP Cost} = 1.0$, $\text{Step-Up Cost} = 0.25$. Demonstrates how multi-action policy reduces friction and lowers business loss by challenging rather than blindly rejecting ambiguous transactions).*

### 3. Probability Calibration & Explainable Reason Codes

* **Brier Score Loss**: `0.0181` | **Expected Calibration Error (ECE)**: `0.0309` (Highly calibrated probabilities).
* **Transparent Reason Codes**: Every decision emits feature-grounded indicators (`DEVICE_CHANGE`, `HIGH_TRANSACTION_VELOCITY`, `HIGH_IP_RISK`, `UNUSUAL_AMOUNT`, `BEHAVIORAL_DEVIATION`, `FAILED_AUTHENTICATIONS`).
* **Audit Trail**: Every decision is logged to structured audit logs (`experiments/risk_audit_log.jsonl` / `csv`).

All policy evaluation artifacts are exported to `experiments/risk_policy_evaluation.json`, `experiments/risk_policy_evaluation.csv`, and `experiments/risk_policy_summary.txt`.

---

## 🗺️ Development Roadmap

- [x] **Phase 1: Repository Foundation & Synthetic Data Pipeline**
  - Attack intelligence library (28 archetypes)
  - Synthetic transaction generator with correlated features
  - Validation engine & automated unit test suite
- [x] **Phase 2: Baseline ML Detector & Attack-Specific Evaluation**
  - Preprocessing and feature engineering pipeline (`FraudFeaturePipeline`)
  - XGBoost baseline classifier trainer (`src/detection/train.py`)
  - Scoring & inference engine (`src/detection/predict.py`)
  - Granular per-attack detection rate & false negative analytics (`src/detection/evaluate.py`)
- [x] **Phase 3: Adaptive Red-Team Loop & Model Hardening**
  - False-negative detection analyzer & feature dependency extractor
  - Targeted, multi-strategy attack mutator (`AttackMutator`)
  - 3-Dataset closed-loop orchestration (`Dataset A`, `Dataset B`, `Dataset C`)
  - Retrained hardened model with 76.5% reduction in adversarial misses (`src/adversarial/feedback_loop.py`)
- [x] **Phase 4 & 4B: Robustness Benchmarks, Data Realism & Full Revalidation**
  - Calibrated synthetic distributions (device change, merchant risk, amount tails)
  - XGBoost vs. Random Forest architectural benchmark
  - Feature ablation studies and automated target leakage audit
  - Retrained and revalidated closed-loop feedback experiment (`experiments/realism_revalidation.json`)
- [x] **Phase 5: Attack Genome & Novel Synthetic Attack Discovery**
  - 10-dimensional Attack Genome schema mapping all 28 existing archetypes
  - Mutation & crossover candidate generation with lineage tracking
  - Domain compatibility validation rules and near-duplicate rejection
  - Transparent Novelty, Realism, and Detector-Weakness Evasion Potential scoring
  - Direct integration with `TransactionGenerator` and baseline detector
  - Blind-spot severity classification and export to `novel_attack_candidates.json` / `novel_attack_report.csv`
- [x] **Phase 6: Zero-Day Adaptive Hardening & Re-Attack Loop**
  - High-priority novel attack selection via transparent multi-objective scoring
  - Augmented zero-day adversarial retraining on Dataset B (`src/adversarial/zero_day_hardening.py`)
  - Generation-2 evolved variant generation (Dataset D) with strict training/test separation
  - Generalization benchmarking proving +70.70 percentage point gain on unseen novel variants
  - Defender regression checks, feature importance shift analytics, and full report generation
- [x] **Phase 7: Risk-Aware Decision Engine & Production-Style Mitigation**
  - Multi-tier Risk Decision Engine (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL` -> `ALLOW`, `MONITOR`, `STEP_UP_AUTH`, `BLOCK`)
  - Explainable, feature-grounded reason code generator with severity levels
  - Step-up authentication recommendation simulator (3DS, Biometric Push, OTP)
  - Comprehensive threshold sweeps, Brier score/ECE calibration auditing, and cost trade-off modeling
  - Production-style structured audit logger (`JSONL` / `CSV`) and batch transaction evaluation APIs