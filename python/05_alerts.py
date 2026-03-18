"""
05_alerts.py — Stockout Risk Alerts & Reorder Recommendations
Author: Kouamé Ruben
"""

import pandas as pd
import numpy as np
from pathlib import Path

def generate_alerts():
    df = pd.read_parquet("data/processed/pharma_enriched.parquet")
    latest_month = df["month"].max()
    latest = df[df["month"] == latest_month].copy()
    
    # Stockout risk scoring
    latest["risk_score"] = (
        (1 - latest["fill_rate"]) * 40 +
        latest["stockout"] * 30 +
        np.where(latest["days_of_stock"] < 15, (15 - latest["days_of_stock"].fillna(0)) * 2, 0)
    ).clip(0, 100).round(0).astype(int)
    
    latest["risk_level"] = pd.cut(latest["risk_score"], bins=[-1, 30, 60, 100],
                                   labels=["Low", "Medium", "High"])
    
    # Reorder recommendations
    latest["recommended_order"] = np.where(
        latest["risk_score"] > 50,
        (latest["consumption"] * 2 - latest["stock_end"]).clip(lower=0).astype(int),
        0
    )
    
    alerts = latest[latest["risk_score"] > 30].sort_values("risk_score", ascending=False)
    alerts_summary = alerts[["product_id", "product_name", "district_id", "name",
                              "criticality", "stock_end", "days_of_stock",
                              "risk_score", "risk_level", "recommended_order"]].copy()
    alerts_summary.columns = ["product_id", "product_name", "district_id", "district_name",
                               "criticality", "current_stock", "days_of_stock",
                               "risk_score", "risk_level", "recommended_order"]
    
    alerts_summary.to_parquet("data/processed/alerts.parquet", index=False)
    
    high = len(alerts_summary[alerts_summary["risk_level"] == "High"])
    medium = len(alerts_summary[alerts_summary["risk_level"] == "Medium"])
    vital = len(alerts_summary[(alerts_summary["risk_level"] == "High") & 
                                (alerts_summary["criticality"] == "Vital")])
    
    print(f"[OK] Alerts generated:")
    print(f"   [!] High risk:   {high:,} product-districts")
    print(f"   [~] Medium risk: {medium:,} product-districts")
    print(f"   [!]  Vital drugs at high risk: {vital}")

if __name__ == "__main__":
    generate_alerts()
