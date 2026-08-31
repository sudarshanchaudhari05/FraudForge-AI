# FraudForge AI — 90-Second Judge Demo Script
## Practical Stage & Evaluation Guide for Mastercard Innovation Challenge 2026

---

> ### 📌 Presenter Goal
> Deliver a crisp, memorable, high-impact technical demonstration in **strictly under 90 seconds**.  
> The core narrative: **"Attack the detector. Find its blind spot. Harden it on synthetic data. Prove it generalizes to unseen Gen-2 fraud."**

---

## A. 90-Second Master Timeline

```
[00:00 - 00:10] Hook: The AI Fraud Blind-Spot Problem
[00:10 - 00:25] Attack Lab: 10-Dimensional Genome & Synthetic Mutation
[00:25 - 00:40] Test Baseline Detector: Exposing the Blind Spot (48.0% / 23.1% Recall)
[00:40 - 00:60] Defense Lab: Transfer & 9-Stage Adaptive Hardening Cycle
[00:60 - 00:75] Empirical Victory: Baseline vs. Hardened Generalization (+70.70 pts)
[00:75 - 00:85] Risk Decision Engine: Operational Multi-Tier Mitigation
[00:85 - 00:90] Closing Impact: Continuous Self-Hardening Payment Security
```

---

## B. Second-by-Second Execution Guide

### ⏱️ 00:00 – 00:10 | Executive Hook & Problem Statement
* **Where to Look / Click**: Start on the **Command Center** tab (`http://localhost:3000`).
* **Point at**: The top-right badge: `LIVE PYTHON ML BACKEND` (green pulsing dot).
* **Exact Words to Speak**:
  > *"Judges, today's fraud detection models suffer from an asymmetric blind spot: they over-rely on historical flags like device changes and high velocity. When GenAI fraudsters mask these signals, baseline models fail. FraudForge AI solves this by attacking our own detector first, learning from the failure, and hardening the defense before criminals strike."*

---

### ⏱️ 00:10 – 00:25 | Attack Lab & 10-Dimensional Genome
* **Where to Look / Click**: Click **"ATTACK LAB"** in the top navigation bar.
* **Exact Clicks in UI**:
  1. In the **"Select Known Attack Archetype"** dropdown, select `ATK-012: Stealth Biometric Hash Injection / Virtual Sensor Replay`.
  2. Notice how all 10 genome dropdowns update automatically (`target`, `evasion: biometric_spoofing`, `channel: mobile_app`).
* **Point at**: The **Attack Genome Profile** card showing Novelty, Realism, and Evasion scores.
* **Exact Words to Speak**:
  > *"In our Red-Team Attack Lab, we deconstruct attacks into a 10-dimensional behavioral genome. Here, ATK-012 uses biometric spoofing and behavioral mimicry on mobile apps to suppress typical anomaly signals."*

---

### ⏱️ 00:25 – 00:40 | Expose Detector Blind Spot
* **Where to Look / Click**: In Attack Lab, scroll slightly down.
* **Exact Clicks in UI**:
  1. Click **"⚡ TEST ATTACK AGAINST DETECTOR"**.
  2. Wait 1.3 seconds as the progress bar runs feature transformation and baseline XGBoost scoring.
* **Point at**:
  - The rose warning badge: `⚠ UNDETECTED / CRITICAL BLIND SPOT (48% RECALL)`
  - The missed count: `MISSED: 52 / 100`
  - The explanation text: *"The baseline detector over-relied on device_change and failed on this evasion profile."*
* **Exact Words to Speak**:
  > *"We test 100 synthetic transactions against our baseline XGBoost model. The result? A critical blind spot: 52 out of 100 attacks bypass detection with only 48% recall, because the baseline detector over-relied on device changes."*

---

### ⏱️ 00:40 – 00:60 | Defense Lab & Adaptive Hardening
* **Where to Look / Click**: 
* **Exact Clicks in UI**:
  1. Click **"SEND TO DEFENSE LAB →"**.
  2. The UI instantly transitions to **Defense Lab**, populating the target scenario banner with `ATK-012` and its custom genome.
  3. Click **"▶ RUN ADAPTIVE HARDENING CYCLE"**.
* **Point at**: The **9-stage pipeline animation** lighting up in emerald across stages 01 through 09.
* **Exact Words to Speak**:
  > *"We immediately transfer this blind spot to our Blue-Team Defense Lab. With one click, FraudForge mines the false negatives, augments the training dataset, and retrains the XGBoost detector against these adversarial blind spots."*

---

### ⏱️ 00:60 – 00:75 | Baseline vs. Hardened Generalization Victory
* **Where to Look / Click**: In Defense Lab, point at the side-by-side comparison cards.
* **Exact Clicks in UI**:
  1. In the target dropdown, select `Unseen Gen-2 Attack Suite (Dataset D Benchmark)`.
* **Point at**:
  - **Left Card (Baseline Detector)**: `23.10% Recall` (769 Misses).
  - **Right Card (Hardened Detector)**: `93.80% Recall` (Only 62 Misses).
  - **Gain Badge**: `+70.70 pts Generalization Gain` (**91.9% Miss Reduction**).
* **Exact Words to Speak**:
  > *"Here is the empirical breakthrough: when evaluated against completely unseen Generation-2 attack variants, the baseline detector caught only 23.10%. The hardened detector achieves 93.80% recall — a +70.70 percentage point generalization gain with 91.9% fewer missed attacks."*

---

### ⏱️ 00:75 – 00:85 | Risk Decision Engine & Explainable Mitigation
* **Where to Look / Click**: Click **"RISK DECISION ENGINE"** in top navigation.
* **Exact Clicks in UI**:
  1. Click **"⚡ SCORE TRANSACTION"**.
* **Point at**:
  - **Risk Score & Action Badge**: e.g., `ACTION: BLOCK` or `STEP_UP_AUTH`
  - **Reason Codes**: `[HIGH_IP_RISK]`, `[UNUSUAL_AMOUNT]`, `[DEVICE_MASKED]`
* **Exact Words to Speak**:
  > *"Finally, our Risk Decision Engine translates calibrated probabilities into autonomous payment actions — Allow, Monitor, Step-Up Auth, or Block — with transparent, feature-grounded reason codes for instant compliance and auditability."*

---

### ⏱️ 00:85 – 00:90 | Closing Impact Statement
* **Where to Look / Click**: Return to **Command Center** or leave the Risk Engine visible.
* **Exact Words to Speak**:
  > *"FraudForge AI transforms payment security from a reactive post-loss investigation into a continuous, self-hardening defense system for the AI era. Thank you."*

---

## C. Exact Clicks & UI Reference Table

| Step | Time | UI Location | Exact Button / Element | Expected Visual Feedback |
| :---: | :---: | :--- | :--- | :--- |
| **1** | `00:00` | Header | Top Status Badge | Displays `LIVE PYTHON ML BACKEND` (Green dot) |
| **2** | `00:10` | Nav Bar | Tab `"ATTACK LAB"` | Attack Lab workspace opens |
| **3** | `00:15` | Attack Lab | `#attackLabPresetSelect` | Select `ATK-012: Stealth Biometric Hash Injection` |
| **4** | `00:25` | Attack Lab | `"⚡ TEST ATTACK AGAINST DETECTOR"` | Rose badge: `⚠ UNDETECTED (48% RECALL)` |
| **5** | `00:40` | Attack Lab | `"SEND TO DEFENSE LAB →"` | Switches to Defense Lab with `ATK-012` active |
| **6** | `00:45` | Defense Lab | `"▶ RUN ADAPTIVE HARDENING CYCLE"` | 9-stage pipeline illuminates; status turns green |
| **7** | `00:60` | Defense Lab | `#defenseLabScenarioSelect` | Select `Unseen Gen-2 Attack Suite` (`23.1% → 93.8%`) |
| **8** | `00:75` | Nav Bar | Tab `"RISK DECISION ENGINE"` | Risk engine single transaction simulator opens |
| **9** | `00:80` | Risk Engine | `"⚡ SCORE TRANSACTION"` | Risk score, tier badge, and reason codes appear |

---

## D. What NOT to Say (Avoid 90-Second Time Traps)

1. **DO NOT** spend time reading every dropdown gene name or listing all 28 archetypes — name only `ATK-012` or `Voice Clone`.
2. **DO NOT** explain Python virtual environment setup, pip dependencies, or server ports.
3. **DO NOT** get bogged down in mathematical formulas for Gini impurity or XGBoost gradient splits.
4. **DO NOT** make claims about live Mastercard transaction routing or real banking integration — strictly emphasize **synthetic defensive simulation**.
5. **DO NOT** claim the monetary number is actual cash saved — state that it reflects the simulated value of intercepted test transactions.

---

## E. Emergency Fallback Procedures

### Scenario 1: Backend Connection Drops During Demo
* **Symptom**: Badge displays `DEMO SIMULATION MODE` (Amber dot).
* **Procedure**: **Continue presenting without hesitation!** The frontend contains a built-in deterministic client-side ML evaluation fallback. All metrics, blind-spot calculations, and hardening numbers function identically in simulation mode.

### Scenario 2: Browser Becomes Non-Interactive
* **Symptom**: Clicking buttons produces no UI updates.
* **Procedure**: Press `F5` / `Ctrl+R` to refresh the page. The application initializes in under 300ms and immediately re-establishes connection to `http://127.0.0.1:8000`.

### Scenario 3: Port 8000 or 3000 Occupied
* **Procedure**: Open PowerShell and run:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
  Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
  ```
  Then restart backend and frontend.
