"""
04_forecast.py — ML Demand Forecasting
Author: Kouamé Ruben
Models: XGBoost + simple baseline comparison
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_percentage_error
from pathlib import Path

def create_features(df):
    """Create lag and rolling features for forecasting."""
    df = df.sort_values("month").copy()
    for lag in [1, 2, 3, 6, 12]:
        df[f"lag_{lag}"] = df["total_consumption"].shift(lag)
    for w in [3, 6]:
        df[f"roll_mean_{w}"] = df["total_consumption"].rolling(w).mean().shift(1)
        df[f"roll_std_{w}"] = df["total_consumption"].rolling(w).std().shift(1)
    df["month_num"] = pd.to_datetime(df["month"]).dt.month
    df["quarter"] = pd.to_datetime(df["month"]).dt.quarter
    return df.dropna()

def forecast_products():
    product_monthly = pd.read_parquet("data/processed/product_monthly.parquet")
    
    top_products = (product_monthly.groupby("product_id")["total_consumption"]
                    .sum().nlargest(20).index.tolist())
    
    results = []
    feature_cols = ["lag_1", "lag_2", "lag_3", "lag_6", "lag_12",
                    "roll_mean_3", "roll_mean_6", "roll_std_3", "roll_std_6",
                    "month_num", "quarter"]
    
    for pid in top_products:
        df_p = product_monthly[product_monthly["product_id"] == pid].copy()
        df_p = create_features(df_p)
        
        if len(df_p) < 12:
            continue
        
        train = df_p.iloc[:-6]
        test = df_p.iloc[-6:]
        
        if len(train) < 6 or len(test) == 0:
            continue
        
        model = GradientBoostingRegressor(n_estimators=100, max_depth=4, 
                                           learning_rate=0.1, random_state=42)
        model.fit(train[feature_cols], train["total_consumption"])
        
        pred = model.predict(test[feature_cols])
        naive = test["lag_1"].values
        
        mape_model = mean_absolute_percentage_error(test["total_consumption"], pred)
        mape_naive = mean_absolute_percentage_error(test["total_consumption"], naive)
        
        results.append({
            "product_id": pid,
            "product_name": df_p["product_name"].iloc[0],
            "mape_model": round(mape_model, 3),
            "mape_naive": round(mape_naive, 3),
            "improvement": round(1 - mape_model / max(mape_naive, 0.001), 3),
            "next_month_forecast": int(pred[-1]) if len(pred) > 0 else 0,
        })
    
    results_df = pd.DataFrame(results).sort_values("mape_model")
    results_df.to_parquet("data/processed/forecast_results.parquet", index=False)
    
    avg_mape = results_df["mape_model"].mean()
    avg_improvement = results_df["improvement"].mean()
    
    print(f"[OK] Forecast complete for {len(results_df)} products:")
    print(f"   Avg MAPE (model):   {avg_mape:.1%}")
    print(f"   Avg MAPE (naive):   {results_df['mape_naive'].mean():.1%}")
    print(f"   Avg improvement:    {avg_improvement:.0%}")

if __name__ == "__main__":
    forecast_products()
