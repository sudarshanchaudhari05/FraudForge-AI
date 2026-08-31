# FraudForge AI — Run & Demo Guide
## Local Setup, Execution, Testing & Demonstration Runbook

---

## 1. System Requirements & Environment

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python Version**: Python 3.10, 3.11, or 3.12
- **Supported Browsers**: Google Chrome (recommended), Mozilla Firefox, Microsoft Edge, or Safari
- **Network Access**: Local loopback only (`127.0.0.1` / `localhost`) — no external internet connection required for runtime inference

---

## 2. Installation & Setup

### Step 1: Open Terminal in Project Root
```powershell
cd FraudForge-AI
```

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

---

## 3. Starting the Application Services

FraudForge AI uses a decoupled architecture with a Python FastAPI ML backend and a lightweight static frontend server.

### Step 1: Start the Python ML Backend (Terminal 1)
```powershell
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
* **Expected Output**:
  ```text
  INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
  INFO:     Application startup complete.
  ```
* **Verify Backend Health**:
  Open `http://127.0.0.1:8000/api/v1/health` in your browser.  
  Expected JSON: `{"status": "ok", "baseline_model": {"is_loaded": true}, "hardened_model": {"is_loaded": true}}`

### Step 2: Start the Frontend Server (Terminal 2)
Open a second terminal window in the repository root:
```powershell
python -m http.server 3000 --directory frontend
```
* **Expected Output**:
  ```text
  Serving HTTP on :: port 3000 (http://[::]:3000/) ...
  ```

---

## 4. Accessing the Web Interface

Open your browser and navigate to:
```
http://localhost:3000
```

### How to Verify Live Backend Connection
Look at the top-right corner of the header:
- **Green Glowing Dot + Badge**: `LIVE PYTHON ML BACKEND` — Confirms real-time bi-directional communication with the FastAPI ML backend on port 8000.
- **Amber Dot + Badge**: `DEMO SIMULATION MODE` — Indicates the backend is offline. The frontend will seamlessly use client-side deterministic evaluation fallback.

---

## 5. Running the Complete Automated Test Suite

Verify system integrity by executing the full 72-test test suite:
```powershell
pytest -v
```
* **Expected Result**: `72 passed in ~16s` across all API, discovery, genome, detection, feature engineering, and risk policy modules.

---

## 6. Running CLI Experiments

You can also run the full training, discovery, and benchmark experiments directly from the terminal:

### A. Run Full Baseline & Adversarial Retraining Pipeline (Phases 1–3)
```powershell
python run_experiment.py
```

### B. Run Zero-Day Discovery & Gen-2 Generalization Benchmark (Phase 6)
```powershell
python run_experiment.py --zero-day
```

### C. Run Standalone Novel Attack Candidate Generator (Phase 5)
```powershell
python -m src.attacks.attack_discovery --raw-candidates 80 --retained 15 --samples 200
```

---

## 7. Step-by-Step Interactive Demo Walkthrough

### 1. Command Center (`#command-center`)
- View simulated live transaction feeds, threat level gauge, and real-time security audit log.
- Click **"EXPORT LOGS (JSON / CSV)"** to verify compliance logging.

### 2. Attack Lab (`#attack-lab`)
- Select `ATK-012: Stealth Biometric Hash Injection / Virtual Sensor Replay` from the archetype dropdown.
- Review the 10-dimensional genome configuration cards.
- Click **"⚡ TEST ATTACK AGAINST DETECTOR"** to run 100 simulated transactions against the baseline XGBoost detector.
- Observe the **CRITICAL BLIND SPOT** warning (`48.00% Recall` / `52 Misses`).

### 3. Attack Lab → Defense Lab State Bridge
- Click the green button **"SEND TO DEFENSE LAB →"**.
- Notice the UI automatically switches to Defense Lab, populating the target scenario header with `ATK-012` and displaying `CUSTOM ATTACK EVALUATION`.

### 4. Defense Lab Adaptive Hardening (`#defense-lab`)
- Click **"▶ RUN ADAPTIVE HARDENING CYCLE"**.
- Watch the 9-stage pipeline sequentially illuminate from Stage 01 (Attack Ingest) to Stage 09 (Generalization Gain).
- Switch the dropdown to `Unseen Gen-2 Attack Suite (Dataset D Benchmark)` to view the verified **+70.70 pt generalization gain (23.10% → 93.80% recall)**.

### 5. Risk Decision Engine (`#ai-defense`)
- Adjust transaction features (amount, velocity, IP risk) or select a preset template.
- Click **"⚡ SCORE TRANSACTION"** to view the calculated fraud probability, risk score, tier badge, action (`ALLOW`, `MONITOR`, `STEP_UP_AUTH`, `BLOCK`), and transparent reason codes.

### 6. Automated 90-Second Judge Demo
- In the top header or sidebar, click **"90s JUDGE DEMO"**.
- An interactive walkthrough modal guides you through the narrative with automated state transitions.

---

## 8. Troubleshooting & Port Conflict Management

### Port 8000 Already Occupied
If another process is using port 8000:
```powershell
# Find and terminate process on port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

### Port 3000 Already Occupied
```powershell
# Find and terminate process on port 3000
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
```

### Restarting Both Servers
```powershell
# Terminal 1: Backend
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
python -m http.server 3000 --directory frontend
```
