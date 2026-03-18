"""
03_transform.py — KPI Computation & Aggregation
Author: Kouamé Ruben
"""

import pandas as pd
import numpy as np
from pathlib import Path

def compute_kpis():
    df = pd.read_parquet("data/processed/pharma_enriched.parquet")
    
    # Global KPIs
    latest_month = df["month"].max()
    latest = df[df["month"] == latest_month]
    
    kpis = {
        "report_month": str(latest_month)[:7],
        "total_consumption": int(latest["consumption"].sum()),
        "total_value_fcfa": int(latest["consumption_value"].sum()),
        "overall_fill_rate": round(latest["fill_rate"].mean(), 3),
        "overall_stockout_rate": round(latest["stockout"].mean(), 3),
        "products_in_stockout": int(latest.groupby("product_id")["stockout"].max().sum()),
        "districts_affected": int(latest[latest["stockout"] == 1]["district_id"].nunique()),
        "critical_stockouts": int(latest[(latest["stockout"] == 1) & (latest["criticality"] == "Vital")].shape[0]),
    }
    
    # Trend KPIs (month over month)
    prev_month = latest_month - pd.DateOffset(months=1)
    prev = df[df["month"] == prev_month]
    if len(prev) > 0:
        kpis["consumption_mom_change"] = round(
            (latest["consumption"].sum() / prev["consumption"].sum() - 1), 3)
        kpis["stockout_mom_change"] = round(
            latest["stockout"].mean() - prev["stockout"].mean(), 3)
    
    # Save KPIs
    Path("data/processed").mkdir(exist_ok=True)
    pd.DataFrame([kpis]).to_parquet("data/processed/global_kpis.parquet", index=False)
    
    # Category breakdown
    category_kpis = df[df["month"] == latest_month].groupby("category").agg(
        total_consumption=("consumption", "sum"),
        total_value=("consumption_value", "sum"),
        avg_fill_rate=("fill_rate", "mean"),
        stockout_rate=("stockout", "mean"),
        n_products=("product_id", "nunique"),
    ).reset_index().sort_values("total_value", ascending=False)
    category_kpis.to_parquet("data/processed/category_kpis.parquet", index=False)
    
    print(f"[OK] KPIs computed for {kpis['report_month']}:")
    print(f"   Fill rate:     {kpis['overall_fill_rate']:.1%}")
    print(f"   Stockout rate: {kpis['overall_stockout_rate']:.1%}")
    print(f"   Total value:   {kpis['total_value_fcfa']:,} FCFA")

if __name__ == "__main__":
    compute_kpis()
