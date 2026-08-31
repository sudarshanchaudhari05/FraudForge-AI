# FraudForge AI
Attack. Learn. Harden. Repeat.

> **Mastercard Innovation Challenge @ Global Fintech Fest (GFF) 2026**

FraudForge AI is a closed-loop adversarial payment-defense system that proactively attacks its own fraud detector, discovers synthetic blind spots, hardens the model against those weaknesses, and tests whether the defense generalizes to unseen Gen-2 attacks.

---

## Why FraudForge AI is Different

Traditional fraud detection learns mainly from historical fraud registries. When fraudsters use Generative AI and behavioral mimicry to bypass known heuristic flags, static models fail because they have never seen those patterns before.

FraudForge AI flips this paradigm: instead of waiting for real-world fraud losses to occur, it creates adversarial synthetic attacks against its own detector, finds where the detector fails, retrains the model on those blind spots, and then tests whether the defense generalizes to fresh, unseen variants.

```
KNOWN ATTACKS
      ↓
ATTACK GENOME
      ↓
RED TEAM DISCOVERY
      ↓
DETECTOR BLIND SPOT
      ↓
BLUE TEAM HARDENING
      ↓
UNSEEN GEN-2 ATTACK
      ↓
GENERALIZATION TEST
      ↓
RISK-AWARE DECISION
```

---

## Key Results

> **SYNTHETIC DEFENSIVE BENCHMARK RESULTS**  
> All metrics below reflect evaluations conducted on calibrated synthetic payment distributions ($D_{\text{test}}$, $D_{\text{adversarial}}$, $D_{\text{unseen}}$).

| Metric | Result |
|---|---:|
| Known attack archetypes | 28 |
| Attack genome dimensions | 10 |
| Unseen Gen-2 baseline recall | 23.10% |
| Unseen Gen-2 hardened recall | 93.80% |
| Generalization gain | +70.70 percentage points |
| False-negative reduction | 91.9% |
| Automated tests | 72/72 passing |
| Risk-aware policy FPR | 1.06% |
| Simulated policy cost reduction | 37.4% |

---

## System Architecture

FraudForge AI is built as a decoupled, full-stack adversarial machine learning framework:

```
┌────────────────────────────────────────────────────────┐
│             Interactive Frontend Dashboard             │
│                 (http://localhost:3000)                │
└───────────────────────────┬────────────────────────────┘
                            │ REST API (JSON)
                            ▼
┌────────────────────────────────────────────────────────┐
│                  FastAPI Backend Server                │
│                (http://127.0.0.1:8000/api/v1)          │
└───────────────────────────┬────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Risk Engine  │   │Attack Genome &│   │Zero-Day Blue  │
│  & Mitigation │   │Red Discovery  │   │Team Hardening │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│            XGBoost Fraud Detection Classifier          │
│               (Baseline & Hardened Models)             │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│         Synthetic Payment Transaction Generator        │
│          (22 Features, Diurnal & Pareto Tails)         │
└────────────────────────────────────────────────────────┘
```

---

## Main Features

- **Command Center**: Real-time transaction stream, threat telemetry counters, radar charts, and live security audit logs.
- **Attack Lab**: Interactive 10-dimensional genome builder, mutation intensity slider, and live detector testing.
- **Defense Lab**: Side-by-side comparison of baseline vs. hardened detector, 9-stage adaptive pipeline animation, and empirical generalization metrics.
- **Attack Genome Explorer**: Interactive matrix visualizer indexing all 28 cataloged archetypes across 7 categories.
- **Zero-Day Discovery**: Genetic algorithm combining mutation and crossover to search for detector blind spots.
- **Risk Decision Engine**: Multi-tier policy engine mapping probabilities to actionable outcomes (`ALLOW`, `MONITOR`, `STEP_UP_AUTH`, `BLOCK`) with transparent reason codes.
- **90-Second Judge Demo**: Automated guided walkthrough presenting the end-to-end narrative in under 90 seconds.

---

## Repository Structure

```
FraudForge-AI/
├── src/
│   ├── api/                 # FastAPI REST API application & schemas
│   ├── attacks/             # 28 archetypes, 10-D genome & genetic discovery engine
│   ├── detection/           # XGBoost detector, risk engine & threshold optimizer
│   ├── simulation/          # Synthetic transaction generator & distributions
│   ├── features/            # RobustScaler & OneHotEncoder feature pipeline
│   ├── adversarial/         # Zero-day hardening & Gen-2 generalization benchmark
│   └── utils/               # Schema definitions & global configurations
├── frontend/
│   └── index.html           # Single-page interactive security dashboard
├── models/                  # Saved ML detector models (.gitkeep)
├── experiments/             # Verified empirical benchmark outputs (.json, .csv)
├── docs/                    # Walkthrough, Judge Script, Run Guide & Checklist
├── tests/                   # 72 automated pytest test cases (100% passing)
├── requirements.txt         # Project dependencies
├── LICENSE                  # MIT License
└── README.md                # Project documentation
```

---

## Quick Start

### 1. Clone & Install Dependencies
```powershell
git clone https://github.com/sudarshanchaudhari05/FraudForge-AI.git
cd FraudForge-AI

python -m pip install -r requirements.txt
```

### 2. Run Automated Tests
```powershell
pytest -v
```
*(Expected: `72 passed in ~16s`)*

### 3. Start Python ML Backend
```powershell
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
```
*Health Check*: `http://127.0.0.1:8000/api/v1/health`  
*API Documentation (Swagger UI)*: `http://127.0.0.1:8000/docs`

### 4. Start Frontend Server (in a separate terminal)
```powershell
python -m http.server 3000 --directory frontend
```
*Open in Browser*: `http://localhost:3000`

> **Note**: When both services are running, the web UI header will display `LIVE PYTHON ML BACKEND` with a pulsing green indicator.

---

## Judge Demo

For competition judges with limited time, please refer to:
👉 **[90-Second Judge Demo Script](docs/90_Second_Judge_Demo_Script.docx)**

### Exact Demo Flow
```
Command Center
      ↓
  Attack Lab
      ↓
   ATK-012 (Stealth Biometric Injection)
      ↓
 Test Attack (Expose Blind Spot: 48.0% Recall)
      ↓
Send to Defense Lab
      ↓
Adaptive Hardening (9-Stage Pipeline)
      ↓
Unseen Gen-2 Benchmark (23.10% → 93.80% Recall, +70.70 pts Gain)
      ↓
Risk Decision Engine (Autonomous Actions & Reason Codes)
```

---

## Documentation

- 📄 **[Solution Walkthrough](docs/FraudForge_AI_Solution_Walkthrough.docx)**: Deep technical architecture, mathematical formulations, and detailed benchmark results.
- ⏱️ **[90-Second Judge Demo Script](docs/90_Second_Judge_Demo_Script.docx)**: Step-by-step timeline, exact clicks, exact values to point at, and spoken script.
- 🛠️ **[Run & Demo Guide](docs/RUN_AND_DEMO_GUIDE.docx)**: Local execution, port conflict resolution, and CLI experiment execution.
- ✅ **[Final Submission Checklist](docs/FINAL_SUBMISSION_CHECKLIST.docx)**: Complete pre-submission verification and audit checklist.

---

## Important Disclaimer

All transactions, attacks, telemetry features, metrics, and monetary numbers presented in FraudForge AI are **synthetic defensive simulations** created strictly for research, testing, and algorithmic evaluation.

This project does **not** process live cardholder data, does **not** connect to production Mastercard networks, and does **not** represent proprietary Mastercard fraud decisioning systems or confidential risk thresholds.
