"""
02_clean.py - Data Cleaning & Validation
Author: Kouamé Ruben
"""

import pandas as pd
import numpy as np
from pathlib import Path

def clean_and_validate():
    # Load
    products = pd.read_csv("data/raw/products_master.csv")
    districts = pd.read_csv("data/raw/districts.csv")
    consumption = pd.read_parquet("data/raw/consumption_monthly.parquet")
    
    # Merge
    df = consumption.merge(products, on="product_id", how="left")
    df = df.merge(districts, on="district_id", how="left")
    df["month"] = pd.to_datetime(df["month"])
    
    # Validation
    errors = []
    if df["consumption"].min() < 0: errors.append("Negative consumption found")
    if df.isnull().any().any(): errors.append(f"Missing values: {df.isnull().sum().sum()}")
    dupes = df.duplicated(subset=["product_id", "district_id", "month"]).sum()
    if dupes > 0: errors.append(f"{dupes} duplicate rows")
    
    if errors:
        print(f"[!]  Validation issues: {errors}")
    else:
        print("[OK] Validation passed - no issues found")
    
    # Feature engineering
    df["year"] = df["month"].dt.year
    df["month_num"] = df["month"].dt.month
    df["quarter"] = df["month"].dt.quarter
    df["fill_rate"] = np.where(df["consumption"] > 0,
                                np.minimum(1, (df["stock_beginning"] + df["orders_received"]) / df["consumption"]),
                                1.0)
    df["days_of_stock"] = np.where(df["consumption"] > 0,
                                    np.round(df["stock_end"] / (df["consumption"] / 30), 1),
                                    np.nan)
    df["consumption_value"] = df["consumption"] * df["unit_cost_fcfa"]
    
    # Save
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    df.to_parquet("data/processed/pharma_enriched.parquet", index=False)
    
    # Aggregations
    district_monthly = df.groupby(["district_id", "name", "pop", "lat", "lon", "month"]).agg(
        total_consumption=("consumption", "sum"),
        total_value=("consumption_value", "sum"),
        avg_fill_rate=("fill_rate", "mean"),
        stockout_count=("stockout", "sum"),
        stockout_rate=("stockout", "mean"),
        n_products=("product_id", "nunique"),
    ).reset_index()
    district_monthly.to_parquet("data/processed/district_monthly.parquet", index=False)
    
    product_monthly = df.groupby(["product_id", "product_name", "category", "criticality", "month"]).agg(
        total_consumption=("consumption", "sum"),
        total_value=("consumption_value", "sum"),
        avg_fill_rate=("fill_rate", "mean"),
        stockout_rate=("stockout", "mean"),
        n_districts_stockout=("stockout", "sum"),
    ).reset_index()
    product_monthly.to_parquet("data/processed/product_monthly.parquet", index=False)
    
    print(f"[OK] Cleaning complete:")
    print(f"   Enriched data:    {len(df):,} rows, {len(df.columns)} columns")
    print(f"   District monthly: {len(district_monthly):,} rows")
    print(f"   Product monthly:  {len(product_monthly):,} rows")

if __name__ == "__main__":
    clean_and_validate()
