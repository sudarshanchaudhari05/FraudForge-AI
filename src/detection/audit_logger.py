"""FraudForge AI: Production-Style Risk Decision Audit Logger.

Provides append-only structured audit logging for all transaction risk decisions.
Persists in JSON Lines (JSONL) and CSV formats for compliance and telemetry.
Does not log personal identifiable information (PII).
"""

import datetime
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import pandas as pd

from src.utils.config import EXPERIMENTS_DIR


class RiskAuditLogger:
    """Production-grade audit logging for payment risk decisions."""

    DEFAULT_LOG_PATH = EXPERIMENTS_DIR / "risk_audit_log.jsonl"
    DEFAULT_CSV_PATH = EXPERIMENTS_DIR / "risk_audit_log.csv"

    def __init__(
        self,
        log_path: Optional[Path] = None,
        csv_path: Optional[Path] = None,
    ):
        self.log_path = log_path or self.DEFAULT_LOG_PATH
        self.csv_path = csv_path or self.DEFAULT_CSV_PATH
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_decision(
        self,
        decision: Dict[str, Any],
        mitigation_status: Optional[str] = None,
        transaction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Format and append a single decision record to the audit log."""
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        tx_id = transaction_id or str(decision.get("transaction_id", "TX-UNKNOWN"))

        audit_entry = {
            "timestamp": now,
            "transaction_id": tx_id,
            "fraud_probability": float(decision.get("fraud_probability", 0.0)),
            "risk_score": float(decision.get("risk_score", 0.0)),
            "risk_level": str(decision.get("risk_level", "UNKNOWN")),
            "action": str(decision.get("action", "UNKNOWN")),
            "mitigation_status": str(mitigation_status or decision.get("status", "EXECUTED")),
            "reason_codes": decision.get("reason_codes", []),
            "model_version": str(decision.get("model_version", "hardened_zero_day_v1")),
            "policy_version": str(decision.get("policy_version", "balanced_v1")),
        }

        # Append to JSONL
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_entry) + "\n")

        return audit_entry

    def log_batch(
        self,
        decisions_df: pd.DataFrame,
        save_csv: bool = True,
    ) -> int:
        """Log a batch of evaluated transactions to JSONL and optional CSV."""
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        records = decisions_df.to_dict(orient="records")
        entries: List[Dict[str, Any]] = []

        for row in records:
            entry = {
                "timestamp": now,
                "transaction_id": str(row.get("transaction_id", f"TX-{len(entries)+1:06d}")),
                "fraud_probability": float(row.get("fraud_probability", 0.0)),
                "risk_score": float(row.get("risk_score", 0.0)),
                "risk_level": str(row.get("risk_level", "UNKNOWN")),
                "action": str(row.get("action", "UNKNOWN")),
                "mitigation_status": "BATCH_PROCESSED",
                "reason_codes": row.get("reason_codes", []),
                "model_version": str(row.get("model_version", "hardened_zero_day_v1")),
                "policy_version": str(row.get("policy_mode", "balanced").lower() + "_v1"),
            }
            entries.append(entry)

        # Append to JSONL
        with open(self.log_path, "a", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

        # Save or update CSV
        if save_csv:
            df_csv = pd.DataFrame(entries)
            # Flatten reason codes list to string for CSV
            df_csv["reason_codes"] = df_csv["reason_codes"].apply(lambda x: ";".join(x) if isinstance(x, list) else str(x))
            if self.csv_path.exists():
                df_csv.to_csv(self.csv_path, mode="a", header=False, index=False)
            else:
                df_csv.to_csv(self.csv_path, index=False)

        return len(entries)

    def read_logs(self, max_records: Optional[int] = None) -> List[Dict[str, Any]]:
        """Read back logged audit records."""
        if not self.log_path.exists():
            return []

        records: List[Dict[str, Any]] = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line.strip()))

        if max_records is not None:
            return records[-max_records:]
        return records
