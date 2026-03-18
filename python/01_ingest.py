"""
01_ingest.py — Data Ingestion Layer
Author: Kouamé Ruben
Description: Generates realistic pharmaceutical supply chain data
             simulating multiple source formats (CSV, Excel, Parquet)
"""

import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(2026)

# --- Configuration ---
N_PRODUCTS   = 50
N_DISTRICTS  = 10
N_MONTHS     = 36
START_DATE   = "2023-01-01"

DISTRICTS = {
    "DIST-01": {"name": "Abidjan-Nord",   "pop": 2500000, "lat": 5.36, "lon": -4.00},
    "DIST-02": {"name": "Abidjan-Sud",    "pop": 2200000, "lat": 5.30, "lon": -3.98},
    "DIST-03": {"name": "Bouaké",         "pop": 800000,  "lat": 7.69, "lon": -5.03},
    "DIST-04": {"name": "Yamoussoukro",   "pop": 400000,  "lat": 6.82, "lon": -5.28},
    "DIST-05": {"name": "San-Pédro",      "pop": 350000,  "lat": 4.75, "lon": -6.64},
    "DIST-06": {"name": "Korhogo",        "pop": 300000,  "lat": 9.45, "lon": -5.63},
    "DIST-07": {"name": "Man",            "pop": 250000,  "lat": 7.41, "lon": -7.55},
    "DIST-08": {"name": "Daloa",          "pop": 280000,  "lat": 6.87, "lon": -6.45},
    "DIST-09": {"name": "Gagnoa",         "pop": 220000,  "lat": 6.13, "lon": -5.95},
    "DIST-10": {"name": "Abengourou",     "pop": 180000,  "lat": 6.73, "lon": -3.50},
}

CATEGORIES = [
    ("Antipaludique",     0.25),
    ("Antibiotique",      0.20),
    ("Antihypertenseur",  0.12),
    ("Antidiabetique",    0.10),
    ("Analgesique",       0.15),
    ("Anti-inflammatoire",0.08),
    ("Antiretroviral",    0.05),
    ("Vitamine",          0.05),
]

def generate_products():
    """Generate product master data."""
    prods = []
    cat_names = [c[0] for c in CATEGORIES]
    cat_probs = [c[1] for c in CATEGORIES]
    
    drug_names = ["Paracetamol", "Amoxicilline", "Artemether-Lumefantrine", "Metformine",
                  "Omeprazole", "Ibuprofene", "Ciprofloxacine", "Amlodipine", "Losartan",
                  "Salbutamol", "Cotrimoxazole", "Doxycycline", "Diclofenac", "Atenolol",
                  "Glibenclamide", "Chloroquine", "Quinine", "Erythromycine", "Mebendazole",
                  "Fer-Acide Folique"]
    dosages = ["500mg", "250mg", "100mg", "200mg", "50mg", "1g", "20mg", "5mg"]
    
    for i in range(N_PRODUCTS):
        prods.append({
            "product_id": f"MED-{i+1:03d}",
            "product_name": f"{np.random.choice(drug_names)} {np.random.choice(dosages)}",
            "category": np.random.choice(cat_names, p=cat_probs),
            "unit_cost_fcfa": int(np.random.uniform(500, 15000)),
            "lead_time_days": np.random.randint(14, 91),
            "shelf_life_months": np.random.randint(12, 49),
            "criticality": np.random.choice(["Vital", "Essentiel", "Non-essentiel"], p=[0.3, 0.5, 0.2]),
        })
    return pd.DataFrame(prods)

def generate_consumption(products_df):
    """Generate monthly consumption data by product and district."""
    months = pd.date_range(START_DATE, periods=N_MONTHS, freq="MS")
    
    records = []
    for _, prod in products_df.iterrows():
        for dist_id, dist_info in DISTRICTS.items():
            base = dist_info["pop"] / 1000 * np.random.uniform(0.3, 3.0)
            
            for i, month in enumerate(months):
                # Seasonality: peak during rainy season (June-Sept) for antipaludiques
                if prod["category"] == "Antipaludique":
                    season = 1 + 0.5 * np.sin(2 * np.pi * (month.month - 7) / 12)
                else:
                    season = 1 + 0.15 * np.sin(2 * np.pi * (month.month - 3) / 12)
                
                trend = 1 + 0.004 * i
                noise = max(0.5, np.random.normal(1, 0.15))
                
                # Rainfall proxy (affects malaria drugs)
                rainfall = max(0, 120 * np.sin(2 * np.pi * (month.month - 7) / 12) 
                              + np.random.normal(0, 25))
                
                consumption = max(0, int(base * season * trend * noise))
                
                # Realistic stock levels: sometimes supply < demand => stockouts
                # Small districts and high-season months have more supply issues
                supply_reliability = np.random.uniform(0.3, 1.4)  # Some months supply fails
                if dist_info["pop"] < 300000:  # Rural districts have worse supply
                    supply_reliability *= np.random.uniform(0.6, 1.0)
                if prod["category"] == "Antipaludique" and month.month in [6,7,8,9]:
                    supply_reliability *= np.random.uniform(0.5, 1.0)  # Peak demand, supply can't keep up
                
                stock_begin = max(0, int(consumption * np.random.uniform(0.3, 1.8)))
                received = max(0, int(consumption * supply_reliability))
                stock_end = max(0, stock_begin + received - consumption)
                
                records.append({
                    "product_id": prod["product_id"],
                    "district_id": dist_id,
                    "month": month,
                    "consumption": consumption,
                    "stock_beginning": stock_begin,
                    "orders_received": received,
                    "stock_end": stock_end,
                    "stockout": 1 if stock_end == 0 else 0,
                    "rainfall_mm": round(rainfall, 1),
                })
    
    return pd.DataFrame(records)

def main():
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    
    # Generate
    products = generate_products()
    districts = pd.DataFrame([
        {"district_id": k, **v} for k, v in DISTRICTS.items()
    ])
    consumption = generate_consumption(products)
    
    # Save as multiple formats (simulating real-world sources)
    products.to_csv("data/raw/products_master.csv", index=False)
    districts.to_csv("data/raw/districts.csv", index=False)
    consumption.to_csv("data/raw/consumption_monthly.csv", index=False)
    consumption.to_parquet("data/raw/consumption_monthly.parquet", index=False)
    
    print(f"[OK] Ingestion complete:")
    print(f"   Products:    {len(products):,} items")
    print(f"   Districts:   {len(districts):,} districts")
    print(f"   Consumption: {len(consumption):,} rows")
    print(f"   Stockout rate: {consumption['stockout'].mean():.1%}")
    print(f"   Date range: {consumption['month'].min()} => {consumption['month'].max()}")

if __name__ == "__main__":
    main()
