# 📖 Dictionnaire des Données — Pharma Supply Chain Dashboard

## Vue d'ensemble

| Table | Volume | Format | Description |
|-------|--------|--------|-------------|
| `products` | 50 lignes | CSV | Référentiel médicaments essentiels |
| `districts` | 10 lignes | CSV | Districts sanitaires de Côte d'Ivoire |
| `consumption_monthly` | 18 000 lignes | Parquet | Table de faits — consommation mensuelle |
| `pharma_enriched` | 18 000 lignes | Parquet | Données enrichies (colonnes dérivées) |
| `district_monthly` | 360 lignes | Parquet | Agrégation par district-mois |
| `product_monthly` | 1 800 lignes | Parquet | Agrégation par produit-mois |
| `global_kpis` | 1 ligne | Parquet | KPIs globaux du dernier mois |
| `forecast_results` | 20 lignes | Parquet | Résultats prévision ML |
| `alerts` | Variable | Parquet | Alertes de risque de rupture |

---

## 📋 Table `products`

| Colonne | Type | Exemple | Description |
|---------|------|---------|-------------|
| `product_id` | VARCHAR(7) PK | `MED-001` | Identifiant unique du médicament |
| `product_name` | VARCHAR(50) | `Artemether-Lumefantrine 100mg` | Nom + dosage |
| `category` | VARCHAR(30) | `Antipaludique` | Classe thérapeutique |
| `unit_cost_fcfa` | INTEGER | `3500` | Coût unitaire en FCFA |
| `lead_time_days` | INTEGER | `45` | Délai d'approvisionnement (jours) |
| `shelf_life_months` | INTEGER | `24` | Durée de vie (mois) |
| `criticality` | VARCHAR(15) | `Vital` | Classification VEN |

**Valeurs — `category` :** Antipaludique (25%) · Antibiotique (20%) · Analgesique (15%) · Antihypertenseur (12%) · Antidiabetique (10%) · Anti-inflammatoire (8%) · Antiretroviral (5%) · Vitamine (5%)

**Valeurs — `criticality` :** Vital (30%) · Essentiel (50%) · Non-essentiel (20%)

---

## 📋 Table `districts`

| Colonne | Type | Exemple | Description |
|---------|------|---------|-------------|
| `district_id` | VARCHAR(7) PK | `DIST-01` | Identifiant district |
| `name` | VARCHAR(30) | `Abidjan-Nord` | Nom du district sanitaire |
| `pop` | INTEGER | `2500000` | Population |
| `lat` | DECIMAL(6,2) | `5.36` | Latitude |
| `lon` | DECIMAL(6,2) | `-4.00` | Longitude |

**Districts :** Abidjan-Nord (2.5M) · Abidjan-Sud (2.2M) · Bouaké (800K) · Yamoussoukro (400K) · San-Pédro (350K) · Korhogo (300K) · Man (250K) · Daloa (280K) · Gagnoa (220K) · Abengourou (180K)

---

## 📋 Table `consumption_monthly` (table de faits)

**Clé primaire :** `(product_id, district_id, month)`

| Colonne | Type | Exemple | Source | Description |
|---------|------|---------|--------|-------------|
| `product_id` | VARCHAR(7) FK | `MED-001` | products | Réf. produit |
| `district_id` | VARCHAR(7) FK | `DIST-01` | districts | Réf. district |
| `month` | DATE | `2024-06-01` | Généré | 1er jour du mois |
| `consumption` | INTEGER | `1250` | Simulé | Unités consommées |
| `stock_beginning` | INTEGER | `2800` | Simulé | Stock début de mois |
| `orders_received` | INTEGER | `900` | Simulé | Commandes reçues |
| `stock_end` | INTEGER | `2450` | Calculé | `max(0, début + reçu - consommé)` |
| `stockout` | INTEGER 0/1 | `0` | Calculé | `1 si stock_end = 0` |
| `rainfall_mm` | DECIMAL(5,1) | `85.3` | Simulé | Pluviométrie (proxy paludisme) |

---

## 📋 Colonnes dérivées (`pharma_enriched`)

| Colonne | Formule | Description |
|---------|---------|-------------|
| `year` | `year(month)` | Année |
| `month_num` | `month(month)` | Mois (1-12) |
| `quarter` | `quarter(month)` | Trimestre (1-4) |
| `fill_rate` | `min(1, (stock_début + reçu) / consommation)` | Taux de satisfaction [0-1] |
| `days_of_stock` | `stock_end / (consommation / 30)` | Jours de stock restants |
| `consumption_value` | `consumption × unit_cost_fcfa` | Valeur en FCFA |

---

## 📋 Table `forecast_results`

| Colonne | Type | Description |
|---------|------|-------------|
| `product_id` | VARCHAR(7) | Produit prédit |
| `product_name` | VARCHAR(50) | Nom du produit |
| `mape_model` | DECIMAL | MAPE du modèle XGBoost |
| `mape_naive` | DECIMAL | MAPE du baseline naïf |
| `improvement` | DECIMAL | `1 - mape_model/mape_naive` |
| `next_month_forecast` | INTEGER | Prévision mois suivant (unités) |

---

## 📋 Table `alerts`

| Colonne | Type | Description |
|---------|------|-------------|
| `product_id` | VARCHAR(7) | Produit à risque |
| `product_name` | VARCHAR(50) | Nom |
| `district_id` | VARCHAR(7) | District |
| `district_name` | VARCHAR(30) | Nom district |
| `criticality` | VARCHAR(15) | VEN (Vital/Essentiel/Non-essentiel) |
| `current_stock` | INTEGER | Stock actuel |
| `days_of_stock` | DECIMAL | Jours restants |
| `risk_score` | INTEGER [0-100] | Score de risque composite |
| `risk_level` | VARCHAR(6) | Low / Medium / High |
| `recommended_order` | INTEGER | Quantité à commander |

**Formule `risk_score` :** `(1 - fill_rate) × 40 + stockout × 30 + max(0, (15 - days_of_stock) × 2)`

---

## 🔗 Relations

```
products (50) ──1:N──▶ consumption_monthly (18K) ◀──N:1── districts (10)
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
      district_monthly   product_monthly   global_kpis
         (360)              (1800)            (1)
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
            forecast_results          alerts
                (20)              (variable)
```

## 📏 Conventions

| Règle | Exemple |
|-------|---------|
| Nommage colonnes | `snake_case` |
| Dates | 1er jour du mois : `2024-06-01` |
| Monnaie | Suffixe `_fcfa` : `unit_cost_fcfa` |
| Ratios | [0-1] : `fill_rate = 0.87` = 87% |
| Booléens | Integer 0/1 (compatibilité R/Python/SQL) |
| IDs | `PREFIX-NNN` : `MED-001`, `DIST-01` |
| Stockage | Parquet pour traitement, CSV pour échange |
| Valeurs manquantes | `NaN` (Python) / `NA` (R) / `NULL` (SQL) |
